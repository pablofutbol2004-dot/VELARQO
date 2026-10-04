#!/usr/bin/env python3
import csv, sys
PASS={'pass','passed','done','yes','true','closed'}
def main(path):
    with open(path,newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    blockers=[r for r in rows if (r.get('status') or '').strip().lower() not in PASS]
    critical=[r for r in blockers if (r.get('severity') or '').lower()=='critical']
    print(f'checks={len(rows)} passed={len(rows)-len(blockers)} blockers={len(blockers)} critical_blockers={len(critical)}')
    if blockers:
        for r in blockers: print(f"BLOCK {r.get('check_id')}: [{r.get('severity')}] {r.get('check_name')}")
        raise SystemExit(2)
    print('FACTORY READY')
if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: check_factory_gate.py factory_gate.csv')
    main(sys.argv[1])
