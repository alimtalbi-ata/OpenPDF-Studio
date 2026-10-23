"""Fail-closed comparison of PDF optional-content (layer) configuration.

OpenPDF Studio V45.5. Author: Abdelhalim Talbi.

This checks declared OCGs and visibility configurations before a compressed PDF
is published. It does not prove byte-identical optional-content streams or
preservation of every OCMD policy; existing render and structure gates remain
necessary. Xref numbers are deliberately normalized because rewrites renumber
PDF objects.
"""


def snapshot_optional_content(doc):
    """Return an xref-independent snapshot of OCG names and visibility state.

    Ambiguous duplicate layer names are rejected rather than allowing a rewrite
    to swap identities invisibly. Unknown layer references are rejected.
    """
    ocgs = doc.get_ocgs()
    if not ocgs:
        # Fail closed if a malformed PDF declares layer configs without OCGs.
        if doc.get_layer() or doc.get_layers() or doc.layer_ui_configs():
            raise RuntimeError('Configuration de calques PDF incohérente')
        return ((), (), (), ())

    xref_to_name = {}
    names = set()
    definitions = []
    for xref, info in ocgs.items():
        if not isinstance(info, dict) or not isinstance(info.get('name'), str):
            raise RuntimeError('Définition de calque PDF non prise en charge')
        name = info['name']
        if not name or name in names:
            raise RuntimeError('Noms de calques PDF ambigus : compression refusée')
        names.add(name)
        xref_to_name[xref] = name
        intent = info.get('intent', ())
        if isinstance(intent, str):
            intent = [intent]
        if not isinstance(intent, (tuple, list)) or any(not isinstance(v, str) for v in intent):
            raise RuntimeError('Intention de calque PDF non prise en charge')
        usage = info.get('usage')
        if usage is not None and not isinstance(usage, str):
            raise RuntimeError('Usage de calque PDF non pris en charge')
        definitions.append((name, tuple(sorted(intent)), usage, bool(info.get('on'))))

    def normalize(config):
        if config is None:
            return ()
        if not isinstance(config, dict):
            raise RuntimeError('Configuration de calques PDF non prise en charge')
        result = []
        for key, value in config.items():
            if key in ('on', 'off', 'locked'):
                if not isinstance(value, (list, tuple)):
                    raise RuntimeError('Références de calques PDF invalides')
                try:
                    named = tuple(sorted(xref_to_name[v] for v in value))
                except (KeyError, TypeError) as exc:
                    raise RuntimeError('Référence de calque PDF inconnue') from exc
                result.append((key, named))
            elif key == 'rbgroups':
                if not isinstance(value, (list, tuple)):
                    raise RuntimeError('Groupes de calques PDF invalides')
                try:
                    groups = tuple(sorted(tuple(sorted(xref_to_name[v] for v in group))
                                          for group in value))
                except (KeyError, TypeError) as exc:
                    raise RuntimeError('Groupe de calques PDF inconnu') from exc
                result.append((key, groups))
            else:
                # Never silently ignore an unknown visibility policy.
                raise RuntimeError(f'Option de calques PDF non prise en charge : {key}')
        return tuple(sorted(result))

    configurations = []
    for layer in doc.get_layers():
        if not isinstance(layer, dict) or type(layer.get('number')) is not int:
            raise RuntimeError('Configuration nommée de calques PDF invalide')
        configurations.append((layer.get('name'), layer.get('creator'),
                               normalize(doc.get_layer(layer['number']))))
    ui = []
    for item in doc.layer_ui_configs():
        if not isinstance(item, dict):
            raise RuntimeError('Interface de calques PDF non prise en charge')
        ui.append(tuple(sorted(item.items())))
    return (tuple(sorted(definitions)), normalize(doc.get_layer()),
            tuple(sorted(configurations, key=repr)), tuple(ui))


def validate_ocg_preserved(source, candidate):
    """Reject altered PDF layers even when rendered pixels/text are unchanged."""
    import fitz
    with fitz.open(str(source)) as original, fitz.open(str(candidate)) as output:
        if original.needs_pass or output.needs_pass:
            raise ValueError('PDF protégé : calques non vérifiables')
        if original.page_count != output.page_count:
            raise RuntimeError('Nombre de pages PDF modifié : sortie rejetée')
        before = snapshot_optional_content(original)
        after = snapshot_optional_content(output)
        if before != after:
            raise RuntimeError('Calques/visibilité PDF modifiés : sortie rejetée')
        return {'pages_verified': original.page_count,
                'layers_verified': len(before[0])}
