"""Reject active or externally linked OOXML content in release documentation.

OpenPDF Studio V49.5. Author: Abdelhalim Talbi.
This is a bounded static preflight, not malware detection or a signature.
"""
from __future__ import annotations

from io import BytesIO
import re
import xml.etree.ElementTree as ET
import zipfile

from openpdf_release_guard_v494 import validate_docx_bytes

MAX_RELATIONSHIP_XML = 1024 * 1024
MAX_TOTAL_RELATIONSHIP_XML = 4 * 1024 * 1024
RELATIONSHIP_TAG = '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'
ACTIVE_PART_NAMES = ('vbaproject.bin', 'vbadata.xml', 'macrosheets/', 'activex/',
                     'embeddings/', 'oleobject', 'customui/', 'webextensions/')
ACTIVE_CONTENT_TYPES = ('macroenabled', 'vba', 'activex', 'oleobject', 'attachedtemplate')


def validate_release_docx(data: bytes) -> dict:
    """Require an inert DOCX: no external relationships, macros or embedded objects.

    All nested ZIP budgets and CRCs are checked by the V49.4 preflight first.
    Only the small OOXML relationship and content-type parts are parsed here.
    """
    summary = validate_docx_bytes(data)
    relationships = 0
    total_xml = 0
    with zipfile.ZipFile(BytesIO(data)) as archive:
        names = archive.namelist()
        for name in names:
            lower = name.casefold()
            if any(part in lower for part in ACTIVE_PART_NAMES):
                raise ValueError('Active or embedded OOXML content is forbidden: ' + name)
            if lower.endswith(('.exe', '.dll', '.js', '.vbs', '.ps1')):
                raise ValueError('Executable OOXML attachment is forbidden: ' + name)
            if not (lower.endswith('.rels') or lower == '[content_types].xml'):
                continue
            info = archive.getinfo(name)
            if info.file_size > MAX_RELATIONSHIP_XML:
                raise ValueError('OOXML relationship XML exceeds budget')
            total_xml += info.file_size
            if total_xml > MAX_TOTAL_RELATIONSHIP_XML:
                raise ValueError('OOXML relationship XML total exceeds budget')
            raw = archive.read(info)
            if re.search(br'<!\s*(?:DOCTYPE|ENTITY)\b', raw, re.IGNORECASE):
                raise ValueError('DTD and entity declarations are forbidden in OOXML')
            try:
                root = ET.fromstring(raw)
            except ET.ParseError as exc:
                raise ValueError('Malformed OOXML relationship/content-type XML') from exc
            if lower == '[content_types].xml':
                for item in root.iter():
                    if any(term in item.attrib.get('ContentType', '').casefold()
                           for term in ACTIVE_CONTENT_TYPES):
                        raise ValueError('Macro-enabled or active OOXML content type')
                continue
            if root.tag != RELATIONSHIP_TAG.rsplit('}', 1)[0] + '}Relationships':
                raise ValueError('Invalid OOXML relationship root namespace')
            for child in root:
                if child.tag != RELATIONSHIP_TAG:
                    raise ValueError('Unexpected OOXML relationship element')
            for item in root.iter(RELATIONSHIP_TAG):
                relationships += 1
                target = item.attrib.get('Target', '')
                mode = item.attrib.get('TargetMode', 'Internal')
                if (mode.casefold() != 'internal' or not target or
                        re.match(r'^[a-z][a-z0-9+.-]*:', target, re.IGNORECASE) or
                        target.startswith(('/', '\\')) or '\\' in target):
                    raise ValueError('External or unsafe OOXML relationship')
    return {**summary, 'relationships_checked': relationships,
            'active_content_rejected': True, 'external_links_rejected': True}
