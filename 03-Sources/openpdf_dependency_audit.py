"""Static import + runtime loaded-module audit; never assumes unreachable means unused."""
import ast, json, sys
from pathlib import Path

def static_imports(path):
    tree=ast.parse(Path(path).read_text(encoding="utf-8-sig"), filename=str(path))
    imports=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return sorted(imports)

def audit_directory(folder):
    folder=Path(folder)
    modules={p.stem:p for p in folder.glob("*.py")}
    graph={name:[dep for dep in static_imports(path) if dep in modules] for name,path in modules.items()}
    visited=set();stack=["openpdf_studio"]
    while stack:
        name=stack.pop()
        if name in visited or name not in graph:continue
        visited.add(name);stack.extend(graph[name])
    return {"modules":len(modules),"static_reachable":sorted(visited),"static_unreachable_count":len(modules)-len(visited),"warning":"Static unreachability does not prove dead code; dynamic imports, packaging and tests must be checked."}

def runtime_snapshot(prefix="openpdf"):
    return sorted(name for name in sys.modules if name.startswith(prefix))

if __name__=="__main__":
    folder=Path(__file__).resolve().parent
    print(json.dumps(audit_directory(folder),ensure_ascii=False,indent=2))
