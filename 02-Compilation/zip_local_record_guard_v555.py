"""Strict ZIP local-record consistency guard for OpenPDF Studio cumulative releases.
Author: Abdelhalim Talbi. Validates raw ZIP metadata without decompressing members.
"""
from __future__ import annotations
import struct
import zlib

_LOCAL_HEADER = struct.Struct("<4s5H3I2H")
_LOCAL_SIGNATURE = b"PK\x03\x04"
_DESCRIPTOR_SIGNATURE = b"PK\x07\x08"
_ZIP64_EXTRA_ID = 0x0001
_UNICODE_PATH_EXTRA_ID = 0x7075
_ZIP32_SENTINEL = 0xFFFFFFFF
_FLAG_ENCRYPTED = 0x0001
_FLAG_STRONG_ENCRYPTION = 0x0040
_FLAG_MASKED_HEADER = 0x2000
_FLAG_DATA_DESCRIPTOR = 0x0008
_EOCD_RECORD = struct.Struct("<4s4H2IH")
_EOCD_SIGNATURE = b"PK\x05\x06"
_ZIP64_LOCATOR = struct.Struct("<4sIQI")
_ZIP64_LOCATOR_SIGNATURE = b"PK\x06\x07"
_ZIP64_EOCD = struct.Struct("<4sQ2H2I4Q")
_ZIP64_EOCD_SIGNATURE = b"PK\x06\x06"
_CENTRAL_DIRECTORY_HEADER = struct.Struct("<4s6H3I5H2I")
_CENTRAL_DIRECTORY_SIGNATURE = b"PK\x01\x02"
_ZIP16_SENTINEL = 0xFFFF


def _error(message: str, name: str) -> ValueError:
    return ValueError(f"{message}: {name}")



def _count_central_directory_records(fp, offset: int, size: int, expected_count: int) -> int:
    """Walk central-record boundaries without reading or decompressing member data."""
    cursor = 0
    count = 0
    while cursor < size:
        remaining = size - cursor
        if remaining < _CENTRAL_DIRECTORY_HEADER.size:
            raise ValueError("Truncated ZIP central-directory entry or trailing bytes")
        fp.seek(offset + cursor)
        raw = fp.read(_CENTRAL_DIRECTORY_HEADER.size)
        if len(raw) != _CENTRAL_DIRECTORY_HEADER.size:
            raise ValueError("Truncated ZIP central-directory entry header")
        fields = _CENTRAL_DIRECTORY_HEADER.unpack(raw)
        if fields[0] != _CENTRAL_DIRECTORY_SIGNATURE:
            raise ValueError("Invalid ZIP central-directory record signature")
        name_length, extra_length, comment_length = fields[10], fields[11], fields[12]
        disk_start = fields[13]
        if disk_start != 0:
            raise ValueError("Multi-disk ZIP entry is not accepted")
        record_length = (_CENTRAL_DIRECTORY_HEADER.size + name_length
                         + extra_length + comment_length)
        if record_length > remaining:
            raise ValueError("ZIP central-directory entry exceeds declared size")
        cursor += record_length
        count += 1
        if count > expected_count:
            raise ValueError("ZIP EOCD entry-count mismatch: central directory contains more entries")
    if cursor != size or count != expected_count:
        raise ValueError("ZIP EOCD entry-count mismatch: central directory record count differs")
    return count


def _validate_eocd_candidate(fp, infos, central_start: int, file_size: int,
                             eocd_offset: int, fields) -> None:
    (signature, disk_number, central_disk, entries_on_disk32, entries_total32,
     central_size32, central_offset32, comment_length) = fields
    if signature != _EOCD_SIGNATURE:
        raise ValueError("Invalid ZIP EOCD signature")
    if eocd_offset + _EOCD_RECORD.size + comment_length != file_size:
        raise ValueError("ZIP EOCD comment length does not reach physical EOF (trailing bytes or malformed comment)")
    if disk_number != 0 or central_disk != 0:
        raise ValueError("Multi-disk ZIP archives are not accepted")

    uses_zip64 = (
        entries_on_disk32 == _ZIP16_SENTINEL
        or entries_total32 == _ZIP16_SENTINEL
        or central_size32 == _ZIP32_SENTINEL
        or central_offset32 == _ZIP32_SENTINEL
    )
    if uses_zip64:
        locator_offset = eocd_offset - _ZIP64_LOCATOR.size
        if locator_offset < 0:
            raise ValueError("Missing ZIP64 EOCD locator")
        fp.seek(locator_offset)
        raw_locator = fp.read(_ZIP64_LOCATOR.size)
        if len(raw_locator) != _ZIP64_LOCATOR.size:
            raise ValueError("Truncated ZIP64 EOCD locator")
        locator_signature, locator_disk, zip64_offset, disk_count = _ZIP64_LOCATOR.unpack(raw_locator)
        if locator_signature != _ZIP64_LOCATOR_SIGNATURE:
            raise ValueError("Missing ZIP64 EOCD locator")
        if locator_disk != 0 or disk_count != 1:
            raise ValueError("Multi-disk ZIP64 archives are not accepted")
        if zip64_offset + _ZIP64_EOCD.size > locator_offset:
            raise ValueError("ZIP64 EOCD offset is outside the allowed record region")
        fp.seek(zip64_offset)
        raw_zip64 = fp.read(_ZIP64_EOCD.size)
        if len(raw_zip64) != _ZIP64_EOCD.size:
            raise ValueError("Truncated ZIP64 EOCD record")
        (zip64_signature, record_size, _made, _needed, zip64_disk, zip64_central_disk,
         entries_on_disk64, entries_total64, central_size64, central_offset64) = _ZIP64_EOCD.unpack(raw_zip64)
        if zip64_signature != _ZIP64_EOCD_SIGNATURE:
            raise ValueError("Invalid ZIP64 EOCD signature")
        # The Python zipfile reader used by this verifier supports the fixed 44-byte
        # ZIP64 end-record body, not optional extensible data sectors.
        if record_size != 44:
            raise ValueError("ZIP64 EOCD extensible data is not supported by the active Python ZIP reader")
        if zip64_offset + 12 + record_size != locator_offset:
            raise ValueError("Unindexed bytes around ZIP64 EOCD record")
        if zip64_disk != 0 or zip64_central_disk != 0:
            raise ValueError("Multi-disk ZIP64 archives are not accepted")
        if entries_on_disk64 != entries_total64:
            raise ValueError("ZIP EOCD entry-count mismatch: ZIP64 disk and total counts differ")
        for raw, sentinel, actual, label in (
            (entries_on_disk32, _ZIP16_SENTINEL, entries_on_disk64, "entries-on-disk"),
            (entries_total32, _ZIP16_SENTINEL, entries_total64, "total entries"),
            (central_size32, _ZIP32_SENTINEL, central_size64, "central-directory size"),
            (central_offset32, _ZIP32_SENTINEL, central_offset64, "central-directory offset"),
        ):
            if raw != sentinel and raw != actual:
                raise ValueError("ZIP EOCD and ZIP64 values disagree: " + label)
        entries_on_disk = entries_on_disk64
        entries_total = entries_total64
        central_size = central_size64
        central_offset = central_offset64
        central_end = zip64_offset
    else:
        entries_on_disk = entries_on_disk32
        entries_total = entries_total32
        central_size = central_size32
        central_offset = central_offset32
        central_end = eocd_offset
        if entries_on_disk != entries_total:
            raise ValueError("ZIP EOCD entry-count mismatch: per-disk and total counts differ")

    if entries_on_disk != entries_total:
        raise ValueError("ZIP EOCD entry-count mismatch: per-disk and total counts differ")
    if central_offset != central_start:
        raise ValueError("ZIP EOCD central-directory offset differs from parsed offset")
    if central_offset + central_size != central_end:
        raise ValueError("Unindexed bytes between ZIP central directory and end record")
    if len(infos) != entries_total:
        raise ValueError(
            "ZIP EOCD entry-count mismatch: end record says %d, parser found %d"
            % (entries_total, len(infos))
        )
    _count_central_directory_records(fp, central_offset, central_size, entries_total)


def _validate_eocd_central_directory(archive, infos, central_start: int, file_size: int) -> None:
    """Validate the exact EOCD record selected by the active ZIP reader.

    Derive its offset from ZipFile.comment instead of scanning every signature in
    the maximum-size comment window. This avoids repeated O(entry-count) walks on
    attacker-controlled signature-like bytes while validating the same EOCD that
    CPython used to parse the archive.
    """
    fp = getattr(archive, "fp", None)
    comment = getattr(archive, "comment", None)
    if fp is None or file_size < _EOCD_RECORD.size:
        raise ValueError("ZIP EOCD record is missing or truncated")
    if not isinstance(comment, bytes) or len(comment) > 0xFFFF:
        raise ValueError("ZIP EOCD comment metadata is invalid")

    eocd_offset = file_size - _EOCD_RECORD.size - len(comment)
    if eocd_offset < 0:
        raise ValueError("ZIP EOCD record is missing or truncated")
    fp.seek(eocd_offset)
    raw = fp.read(_EOCD_RECORD.size)
    if len(raw) != _EOCD_RECORD.size:
        raise ValueError("ZIP EOCD record is missing or truncated")
    fields = _EOCD_RECORD.unpack(raw)
    if fields[0] != _EOCD_SIGNATURE:
        raise ValueError("ZIP EOCD signature differs from the active ZIP reader's parsed comment")

    _validate_eocd_candidate(fp, infos, central_start, file_size, eocd_offset, fields)
    fp.seek(eocd_offset + _EOCD_RECORD.size)
    if fp.read(len(comment)) != comment:
        raise ValueError("ZIP EOCD comment changed during structural validation")


def _parse_extra_fields(extra: bytes, name: str, location: str) -> dict[int, list[bytes]]:
    if not isinstance(extra, bytes):
        raise _error("Invalid ZIP extra-field bytes", name)
    fields: dict[int, list[bytes]] = {}
    offset = 0
    while offset < len(extra):
        if len(extra) - offset < 4:
            raise _error(f"Truncated ZIP {location} extra-field header", name)
        field_id, field_size = struct.unpack_from("<HH", extra, offset)
        offset += 4
        end = offset + field_size
        if end > len(extra):
            raise _error(f"Truncated ZIP {location} extra-field payload", name)
        if field_id in (_ZIP64_EXTRA_ID, _UNICODE_PATH_EXTRA_ID) and field_id in fields:
            raise _error(f"Duplicate ZIP {location} security-sensitive extra field", name)
        fields.setdefault(field_id, []).append(extra[offset:end])
        offset = end
    return fields


def _validate_unicode_path(fields: dict[int, list[bytes]], raw_name: bytes,
                           decoded_name: str, name: str, location: str) -> None:
    values = fields.get(_UNICODE_PATH_EXTRA_ID, [])
    if not values:
        return
    value = values[0]
    if len(value) < 5 or value[0] != 1:
        raise _error(f"Invalid ZIP {location} Unicode Path extra field", name)
    declared_crc = struct.unpack_from("<I", value, 1)[0]
    actual_crc = zlib.crc32(raw_name) & 0xFFFFFFFF
    if declared_crc != actual_crc:
        raise _error(f"ZIP {location} Unicode Path CRC mismatch", name)
    try:
        alternate_name = value[5:].decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise _error(f"Invalid UTF-8 in ZIP {location} Unicode Path", name) from None
    if "\x00" in alternate_name or alternate_name != decoded_name:
        raise _error(f"ZIP {location} Unicode Path alias rejected", name)


def _zip64_local_sizes(fields: dict[int, list[bytes]], name: str,
                       need_uncompressed: bool, need_compressed: bool) -> tuple[int | None, int | None]:
    if not need_uncompressed and not need_compressed:
        return None, None
    values = fields.get(_ZIP64_EXTRA_ID, [])
    if len(values) != 1:
        raise _error("Missing or duplicate ZIP64 local sizes", name)
    data = values[0]
    cursor = 0
    uncompressed = None
    compressed = None
    if need_uncompressed:
        if len(data) - cursor < 8:
            raise _error("Truncated ZIP64 uncompressed size", name)
        uncompressed = struct.unpack_from("<Q", data, cursor)[0]
        cursor += 8
    if need_compressed:
        if len(data) - cursor < 8:
            raise _error("Truncated ZIP64 compressed size", name)
        compressed = struct.unpack_from("<Q", data, cursor)[0]
    return uncompressed, compressed


def _descriptor_end(fp, data_end: int, central_start: int, info, name: str,
                    force_zip64: bool) -> int:
    remaining = central_start - data_end
    if remaining < 12:
        raise _error("Missing or truncated ZIP data descriptor", name)
    fp.seek(data_end)
    raw = fp.read(min(24, remaining))
    widths = (8,) if force_zip64 else (4, 8)
    matches: set[int] = set()
    for width in widths:
        value_bytes = 4 + 2 * width
        for has_signature in (False, True):
            start = 4 if has_signature else 0
            if has_signature and raw[:4] != _DESCRIPTOR_SIGNATURE:
                continue
            total = start + value_bytes
            if len(raw) < total:
                continue
            crc = struct.unpack_from("<I", raw, start)[0]
            if width == 4:
                compressed, uncompressed = struct.unpack_from("<II", raw, start + 4)
            else:
                compressed, uncompressed = struct.unpack_from("<QQ", raw, start + 4)
            if (crc == info.CRC and compressed == info.compress_size
                    and uncompressed == info.file_size):
                matches.add(data_end + total)
    if not matches:
        raise _error("ZIP data descriptor does not match central directory", name)
    if len(matches) != 1:
        raise _error("Ambiguous ZIP data descriptor", name)
    descriptor_end = next(iter(matches))
    if descriptor_end > central_start:
        raise _error("ZIP data descriptor overlaps the central directory", name)
    return descriptor_end


def validate_local_record_layout(archive, infos) -> dict[str, int]:
    """Validate local headers, Unicode aliases, sizes and non-overlapping spans.

    Call after ZipFile parses the central directory but before any read/open of
    member data. Pass every entry, including explicit directories. ZIP local
    spans are checked against the central-directory boundary and each other.
    """
    fp = getattr(archive, "fp", None)
    central_start = getattr(archive, "start_dir", None)
    if fp is None or type(central_start) is not int or central_start < 0:
        raise ValueError("ZIP parser did not expose a valid central-directory boundary")
    try:
        previous_position = fp.tell()
        fp.seek(0, 2)
        file_size = fp.tell()
        if central_start > file_size:
            raise ValueError("ZIP central-directory boundary exceeds file size")
        _validate_eocd_central_directory(archive, infos, central_start, file_size)
        spans: list[tuple[int, int, str]] = []
        offsets: set[int] = set()
        for info in infos:
            name = getattr(info, "filename", "<unknown>")
            original_name = getattr(info, "orig_filename", name)
            if not isinstance(original_name, str) or "\x00" in original_name:
                raise _error("ZIP member name contains NUL", str(original_name))
            if not isinstance(name, str) or original_name != name:
                raise _error("ZIP member name was rewritten by Unicode extra metadata", str(original_name))
            flags = getattr(info, "flag_bits", None)
            method = getattr(info, "compress_type", None)
            compressed_size = getattr(info, "compress_size", None)
            uncompressed_size = getattr(info, "file_size", None)
            crc = getattr(info, "CRC", None)
            offset = getattr(info, "header_offset", None)
            if (type(flags) is not int or type(method) is not int
                    or type(compressed_size) is not int or type(uncompressed_size) is not int
                    or type(crc) is not int or type(offset) is not int
                    or compressed_size < 0 or uncompressed_size < 0
                    or crc < 0 or crc > 0xFFFFFFFF):
                raise _error("Invalid ZIP central-directory metadata", str(name))
            is_directory = bool(getattr(info, "is_dir", lambda: False)())
            if is_directory and (compressed_size != 0 or uncompressed_size != 0 or crc != 0):
                raise _error("ZIP directory entry carries untracked data", str(name))
            if offset < 0 or offset >= central_start:
                raise _error("ZIP local header offset is outside the local-record area", str(name))
            if offset in offsets:
                raise _error("Multiple ZIP entries reference the same local header", str(name))
            offsets.add(offset)
            if flags & (_FLAG_ENCRYPTED | _FLAG_STRONG_ENCRYPTION | _FLAG_MASKED_HEADER):
                raise _error("Encrypted or masked ZIP entries are not accepted", str(name))
            encoding = "utf-8" if flags & 0x0800 else "cp437"
            try:
                central_name_bytes = original_name.encode(encoding, errors="strict")
            except UnicodeEncodeError:
                raise _error("ZIP central filename cannot be represented by its flags", str(name)) from None
            central_extra = getattr(info, "extra", b"")
            central_fields = _parse_extra_fields(central_extra, str(name), "central")
            _validate_unicode_path(central_fields, central_name_bytes, original_name, str(name), "central")

            if offset + _LOCAL_HEADER.size > central_start:
                raise _error("ZIP local header overlaps the central directory", str(name))
            fp.seek(offset)
            header = fp.read(_LOCAL_HEADER.size)
            if len(header) != _LOCAL_HEADER.size:
                raise _error("Truncated ZIP local file header", str(name))
            (signature, _version_needed, local_flags, local_method, _mtime, _mdate,
             local_crc, local_compressed, local_uncompressed, filename_length,
             extra_length) = _LOCAL_HEADER.unpack(header)
            if signature != _LOCAL_SIGNATURE:
                raise _error("Invalid ZIP local file header signature", str(name))
            if local_flags != flags:
                raise _error("ZIP local/central flag mismatch", str(name))
            if local_method != method:
                raise _error("ZIP local/central compression-method mismatch", str(name))
            metadata_start = offset + _LOCAL_HEADER.size
            metadata_end = metadata_start + filename_length + extra_length
            if metadata_end > central_start or metadata_end > file_size:
                raise _error("ZIP local filename/extra fields overlap the central directory", str(name))
            local_metadata = fp.read(filename_length + extra_length)
            if len(local_metadata) != filename_length + extra_length:
                raise _error("Truncated ZIP local filename/extra fields", str(name))
            local_name_bytes = local_metadata[:filename_length]
            local_extra = local_metadata[filename_length:]
            try:
                local_name = local_name_bytes.decode(encoding, errors="strict")
            except UnicodeDecodeError:
                raise _error("Invalid ZIP local filename encoding", str(name)) from None
            if "\x00" in local_name:
                raise _error("ZIP local member name contains NUL", str(name))
            if local_name != original_name or local_name_bytes != central_name_bytes:
                raise _error("ZIP local/central filename mismatch", str(name))
            local_fields = _parse_extra_fields(local_extra, str(name), "local")
            _validate_unicode_path(local_fields, local_name_bytes, local_name, str(name), "local")

            uses_descriptor = bool(local_flags & _FLAG_DATA_DESCRIPTOR)
            local_needs_uncompressed = local_uncompressed == _ZIP32_SENTINEL
            local_needs_compressed = local_compressed == _ZIP32_SENTINEL
            local_zip64_uncompressed, local_zip64_compressed = _zip64_local_sizes(
                local_fields, str(name), local_needs_uncompressed, local_needs_compressed
            )
            if uses_descriptor:
                if local_crc not in (0, crc):
                    raise _error("ZIP local CRC conflicts with data descriptor", str(name))
                if local_uncompressed not in (0, _ZIP32_SENTINEL, uncompressed_size):
                    raise _error("ZIP local uncompressed size conflicts with data descriptor", str(name))
                if local_compressed not in (0, _ZIP32_SENTINEL, compressed_size):
                    raise _error("ZIP local compressed size conflicts with data descriptor", str(name))
                if local_needs_uncompressed and local_zip64_uncompressed not in (0, uncompressed_size):
                    raise _error("ZIP64 local uncompressed size conflicts with data descriptor", str(name))
                if local_needs_compressed and local_zip64_compressed not in (0, compressed_size):
                    raise _error("ZIP64 local compressed size conflicts with data descriptor", str(name))
            else:
                if local_crc != crc:
                    raise _error("ZIP local/central CRC mismatch", str(name))
                local_u = local_zip64_uncompressed if local_needs_uncompressed else local_uncompressed
                local_c = local_zip64_compressed if local_needs_compressed else local_compressed
                if local_u != uncompressed_size or local_c != compressed_size:
                    raise _error("ZIP local/central size mismatch", str(name))

            data_start = metadata_end
            data_end = data_start + compressed_size
            if data_end < data_start or data_end > central_start or data_end > file_size:
                raise _error("ZIP compressed data overlaps the central directory or file boundary", str(name))
            record_end = data_end
            if uses_descriptor:
                force_zip64 = (local_needs_uncompressed or local_needs_compressed
                               or compressed_size >= _ZIP32_SENTINEL or uncompressed_size >= _ZIP32_SENTINEL)
                record_end = _descriptor_end(fp, data_end, central_start, info, str(name), force_zip64)
            if record_end <= offset or record_end > central_start:
                raise _error("ZIP local record has an invalid end offset", str(name))
            spans.append((offset, record_end, str(name)))

        spans.sort(key=lambda item: (item[0], item[1], item[2]))
        cursor = 0
        previous_name = None
        for start, end, name in spans:
            if start < cursor:
                raise ValueError("Overlapping ZIP local records: " + str(previous_name) + " and " + name)
            if start > cursor:
                raise ValueError("Unindexed bytes in ZIP local-record region before: " + name)
            cursor = end
            previous_name = name
        if cursor != central_start:
            raise ValueError("Unindexed bytes before ZIP central directory")
        return {"entries": len(spans), "local_records": len(spans), "overlapping_records": 0}
    finally:
        try:
            fp.seek(previous_position)
        except (UnboundLocalError, OSError, ValueError):
            pass
