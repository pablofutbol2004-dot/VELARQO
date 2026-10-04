#!/usr/bin/env python3
import csv, sys, collections
TRUTH={'1','true','yes','y'}
def b(v): return str(v or '').strip().lower() in TRUTH

def div(a,bv): return (a/bv) if bv else None

def pct(x): return 'n/a' if x is None else f'{x:.1%}'

def main(path):
    with open(path,encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    n=len(rows)
    metrics={k:sum(b(r.get(k)) for r in rows) for k in ['attempted','delivered','bounced','call_booked','call_held','qualified','export_requested','export_received','pilot_interest','pilot_agreed']}
    replies=collections.Counter((r.get('reply_class') or 'none').strip().lower() for r in rows)
    print(f'Prospects: {n}')
    for k,v in metrics.items(): print(f'{k}: {v}')
    print('reply_classes:', dict(replies))
    print('delivery_rate:', pct(div(metrics['delivered'], metrics['attempted'])))
    print('positive_reply_rate_delivered:', pct(div(replies.get('positive',0), metrics['delivered'])))
    print('held_call_rate_delivered:', pct(div(metrics['call_held'], metrics['delivered'])))
    print('export_rate_held:', pct(div(metrics['export_received'], metrics['call_held'])))
    print('pilot_agreement_rate_held:', pct(div(metrics['pilot_agreed'], metrics['call_held'])))
    byv=collections.defaultdict(list)
    for r in rows: byv[r.get('variant') or 'unknown'].append(r)
    print('\nBy variant:')
    for v,rs in sorted(byv.items()):
        d=sum(b(r.get('delivered')) for r in rs); pos=sum((r.get('reply_class') or '').strip().lower()=='positive' for r in rs); held=sum(b(r.get('call_held')) for r in rs); ex=sum(b(r.get('export_received')) for r in rs)
        print(f'{v}: n={len(rs)} delivered={d} positive={pos} held={held} exports={ex}')
if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: summarize_outreach.py outreach_log.csv')
    main(sys.argv[1])
