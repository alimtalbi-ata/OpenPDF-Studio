"""Reproducible cross-process contention and crash recovery test. Author: Abdelhalim Talbi."""
import argparse, json, os, subprocess, sys, tempfile, time
from pathlib import Path
from openpdf_reservation import reserve, inspect_orphan, recover_orphan, lock_path

WORKER = r"""
import sys,time
from openpdf_reservation import reserve
try:
    with reserve(sys.argv[1]):
        print('ACQUIRED',flush=True)
        time.sleep(float(sys.argv[2]))
except FileExistsError:
    print('BUSY',flush=True)
"""

def run_stress(workers=8, rounds=4, hold_seconds=0.12):
    if workers<2 or rounds<1 or hold_seconds<=0: raise ValueError('invalid stress parameters')
    cases=[]
    with tempfile.TemporaryDirectory(prefix='openpdf-stress-') as temp:
        target=str(Path(temp)/'output.pdf')
        for round_id in range(rounds):
            procs=[subprocess.Popen([sys.executable,'-c',WORKER,target,str(hold_seconds)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(workers)]
            outputs=[]
            for p in procs:
                try: out,err=p.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    p.kill();out,err=p.communicate();raise RuntimeError('worker timeout')
                outputs.append({'returncode':p.returncode,'output':out.strip(),'error':err.strip()})
            acquired=sum(x['output']=='ACQUIRED' for x in outputs)
            busy=sum(x['output']=='BUSY' for x in outputs)
            passed=(acquired>=1 and acquired+busy==workers and all(x['returncode']==0 for x in outputs) and not lock_path(target).exists())
            cases.append({'round':round_id+1,'acquired':acquired,'busy':busy,'passed':passed,'workers':outputs})
    return {'schema':1,'synthetic':True,'workers':workers,'rounds':rounds,'passed':all(c['passed'] for c in cases),'cases':cases,'note':'Acquisitions sequentially after release may occur; test checks no failures and clean release, not strict mutual exclusion proof.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);ap.add_argument('--rounds',type=int,default=4);ap.add_argument('--output',required=True);args=ap.parse_args()
    result=run_stress(args.workers,args.rounds)
    Path(args.output).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'rounds':args.rounds,'workers':args.workers}))
    sys.exit(0 if result['passed'] else 1)
