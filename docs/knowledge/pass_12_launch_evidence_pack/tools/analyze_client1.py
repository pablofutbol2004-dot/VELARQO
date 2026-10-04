#!/usr/bin/env python3
import pandas as pd, json, sys, math
from pathlib import Path

p=Path(sys.argv[1] if len(sys.argv)>1 else 'pilot/outcome_reconciliation.csv')
outdir=Path(sys.argv[2] if len(sys.argv)>2 else 'pilot/analysis')
outdir.mkdir(parents=True,exist_ok=True)
df=pd.read_csv(p)
if df.empty:
    raise SystemExit('No reconciled rows yet.')

def b(col):
    if col not in df: return pd.Series(False,index=df.index)
    x=df[col]
    if x.dtype==bool: return x.fillna(False)
    return x.fillna('').astype(str).str.lower().isin(['1','true','yes','y'])

def rate(num,den): return None if den==0 else num/den
N=len(df)
metrics={'rows':N}
for col in ['delivered','replied','positive_interest','qualified','booked','attended','requote','won','billable_result','billing_disputed']:
    metrics[col]=int(b(col).sum())
metrics['delivery_rate']=rate(metrics['delivered'],N)
for col in ['replied','positive_interest','qualified','booked','won']:
    metrics[col+'_per_delivered']=rate(metrics[col],metrics['delivered'])
metrics['attendance_rate']=rate(metrics['attended'],metrics['booked'])
metrics['requote_per_attended']=rate(metrics['requote'],metrics['attended'])
metrics['won_per_attended']=rate(metrics['won'],metrics['attended'])
for col in ['won_value_gbp','cash_collected_gbp','manual_minutes_total']:
    if col in df:
        metrics[col+'_sum']=float(pd.to_numeric(df[col],errors='coerce').fillna(0).sum())
metrics['cash_per_delivered']=rate(metrics.get('cash_collected_gbp_sum',0),metrics['delivered'])
metrics['manual_minutes_per_100_delivered']=rate(metrics.get('manual_minutes_total_sum',0)*100,metrics['delivered'])

# treatment vs holdout if present
if 'pilot_assignment' in df:
    comp=[]
    for grp,g in df.groupby(df['pilot_assignment'].fillna('UNKNOWN')):
        row={'group':grp,'n':len(g)}
        for col in ['booked','attended','won']:
            s=b(col).loc[g.index].sum(); row[col]=int(s); row[col+'_rate']=rate(int(s),len(g))
        comp.append(row)
    metrics['assignment_comparison']=comp
    t=next((x for x in comp if str(x['group']).lower() in ['treatment','test','send']),None)
    h=next((x for x in comp if str(x['group']).lower() in ['holdout','control']),None)
    if t and h:
        metrics['incremental_lift']={k:(t[k+'_rate']-h[k+'_rate'] if t[k+'_rate'] is not None and h[k+'_rate'] is not None else None) for k in ['booked','attended','won']}

# cohorts
if 'quote_age_days' in df:
    age=pd.to_numeric(df['quote_age_days'],errors='coerce')
    bins=[-1,90,180,365,730,10**9]; labels=['0-90','91-180','181-365','366-730','731+']
    cohorts=pd.cut(age,bins=bins,labels=labels)
    cres=[]
    for grp,g in df.groupby(cohorts,observed=False):
        if len(g)==0: continue
        row={'cohort':str(grp),'n':len(g)}
        for col in ['booked','attended','won']:
            s=b(col).loc[g.index].sum(); row[col]=int(s); row[col+'_rate']=rate(int(s),len(g))
        cres.append(row)
    metrics['quote_age_cohorts']=cres

(outdir/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
lines=['# Client 1 analysis','']
for k,v in metrics.items():
    if isinstance(v,(dict,list)): continue
    lines.append(f'- **{k}:** {v}')
if metrics.get('assignment_comparison'):
    lines += ['', '## Treatment / holdout']
    for x in metrics['assignment_comparison']: lines.append('- '+json.dumps(x))
if metrics.get('incremental_lift'):
    lines += ['', '## Incremental lift', json.dumps(metrics['incremental_lift'],indent=2)]
if metrics.get('quote_age_cohorts'):
    lines += ['', '## Quote-age cohorts']
    for x in metrics['quote_age_cohorts']: lines.append('- '+json.dumps(x))
(outdir/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(outdir)
