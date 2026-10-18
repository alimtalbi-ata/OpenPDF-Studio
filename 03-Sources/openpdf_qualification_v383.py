"""V38.3 actual application operations qualification (synthetic PDF inputs)."""
import json,sys
from openpdf_functional_qualification import run_suite
def main():
    report=run_suite();report['version']='38.3';report['scope']='Canonical run_operation; no Windows GUI claims'
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['passed']==report['total'] else 1
if __name__=='__main__':sys.exit(main())
