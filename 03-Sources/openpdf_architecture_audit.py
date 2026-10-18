"""Deterministic static dependency audit, no deletion decisions."""
import ast
import json
from pathlib import Path

def audit(source_dir):
    source_dir = Path(source_dir)
    modules = {p.stem:p for p in source_dir.glob("*.py")}
    imports = {}
    parse_errors = {}
    for name, path in sorted(modules.items()):
        try:
            tree=ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            parse_errors[name]=str(exc)
            continue
        found=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:
                found.add(node.module.split(".")[0])
        imports[name]=sorted(found & modules.keys())
    reachable=set()
    pending=["openpdf_studio"]
    while pending:
        name=pending.pop()
        if name in reachable: continue
        reachable.add(name)
        pending.extend(imports.get(name, []))
    return {"entrypoint":"openpdf_studio", "modules":len(modules), "reachable_static":sorted(reachable), "reachable_count":len(reachable), "parse_errors":parse_errors, "caution":"Static imports exclude dynamic imports, scripts, plugins and tests; unreachable is not proof of dead code."}

if __name__=="__main__":
    print(json.dumps(audit(Path(__file__).parent), indent=2, ensure_ascii=False))
