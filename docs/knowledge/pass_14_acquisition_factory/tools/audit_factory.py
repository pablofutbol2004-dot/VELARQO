#!/usr/bin/env python3
import csv, sys
from collections import Counter

def truth(v): return str(v or '').strip().lower() in {'1','true','yes','y'}

def pct(a,b): return 0 if not b else round(a*100/b,1)

def main(src):
    with open(src,newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    n=len(rows)
    dup=sum(1 for r in rows if (r.get('current_state') or '')=='DUPLICATE')
    no_domain=sum(1 for r in rows if not r.get('canonical_domain'))
    unresolved=sum(1 for r in rows if (r.get('send_allowed') or '').lower()=='review')
    suppressed=sum(1 for r in rows if truth(r.get('suppressed')))
    valid=sum(1 for r in rows if (r.get('verification_status') or '').lower()=='valid')
    sendable=sum(1 for r in rows if (r.get('send_allowed') or '').lower()=='true' and truth(r.get('icp_pass')) and not truth(r.get('suppressed')) and (r.get('verification_status') or '').lower()=='valid')
    print(f'rows={n}')
    print(f'duplicates={dup} ({pct(dup,n)}%)')
    print(f'no_domain={no_domain} ({pct(no_domain,n)}%)')
    print(f'compliance_review={unresolved} ({pct(unresolved,n)}%)')
    print(f'suppressed={suppressed} ({pct(suppressed,n)}%)')
    print(f'valid_contacts={valid} ({pct(valid,n)}%)')
    print(f'sendable={sendable} ({pct(sendable,n)}%)')

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: audit_factory.py master.csv')
    main(sys.argv[1])
