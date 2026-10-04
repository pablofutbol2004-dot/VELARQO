#!/usr/bin/env python3
import csv, re, sys, urllib.parse, uuid

def domain(v):
    v=(v or '').strip().lower()
    if not v: return ''
    if '://' not in v: v='https://'+v
    try:
        h=urllib.parse.urlparse(v).hostname or ''
    except Exception:
        h=''
    h=h.lower()
    return h[4:] if h.startswith('www.') else h

def norm_name(v):
    v=(v or '').lower()
    v=re.sub(r'\b(limited|ltd|plc|llp)\b','',v)
    return re.sub(r'[^a-z0-9]+',' ',v).strip()

def main(src,dst):
    with open(src,newline='',encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    seen_num={}; seen_domain={}; out=[]
    for r in rows:
        num=(r.get('company_number') or '').strip().upper()
        dom=domain(r.get('website_url') or r.get('canonical_domain') or '')
        key=None; reason=''
        if num and num in seen_num: key=seen_num[num]; reason='company_number'
        elif dom and dom in seen_domain: key=seen_domain[dom]; reason='domain'
        if key:
            r['duplicate_of']=key; r['merge_reason']=reason; r['current_state']='DUPLICATE'
        else:
            cid=r.get('company_id') or str(uuid.uuid4())
            r['company_id']=cid; r['canonical_domain']=dom; r['normalized_name']=norm_name(r.get('legal_name') or r.get('trading_name') or '')
            r['duplicate_of']=''; r['merge_reason']=''
            if num: seen_num[num]=cid
            if dom: seen_domain[dom]=cid
        out.append(r)
    fields=[]
    for r in out:
        for k in r:
            if k not in fields: fields.append(k)
    with open(dst,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out)
    print(f'rows={len(out)} duplicates={sum(1 for r in out if r.get("current_state")=="DUPLICATE")}')

if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: normalize_companies.py input.csv output.csv')
    main(sys.argv[1],sys.argv[2])
