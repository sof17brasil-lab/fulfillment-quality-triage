"""Step 3. Independent re-check.

Recomputes the headline numbers straight from the raw CSV files with pandas.
It shares no code with the SQL, so if both agree, a bug would have to exist
twice, written two different ways, to go unnoticed.

    python scripts/verify_pandas.py            # reads data/raw
    python scripts/verify_pandas.py path/to/csvs

Writes out/pandas_recheck.json. scripts/check_reproduction.py compares it
with the SQL results.
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
d = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "data" / "raw")
dt = ['order_purchase_timestamp','order_delivered_carrier_date','order_delivered_customer_date','order_estimated_delivery_date']
o = pd.read_csv(f'{d}/olist_orders_dataset.csv', parse_dates=dt)
it = pd.read_csv(f'{d}/olist_order_items_dataset.csv', parse_dates=['shipping_limit_date'])
cu = pd.read_csv(f'{d}/olist_customers_dataset.csv', dtype=str)
rv = pd.read_csv(f'{d}/olist_order_reviews_dataset.csv', parse_dates=['review_answer_timestamp'])
se = pd.read_csv(f'{d}/olist_sellers_dataset.csv', dtype=str)
R = {}
R['raw_rows'] = dict(orders=len(o), items=len(it), customers=len(cu), reviews=len(rv), sellers=len(se))
# true first-order date per seller, from the FULL unfiltered history (the
# raw data starts Sep 2016, before this project's 86-week window)
seller_first_order = it[['order_id', 'seller_id']].merge(
    o[['order_id', 'order_purchase_timestamp']], on='order_id'
).groupby('seller_id').order_purchase_timestamp.min()
o = o[(o.order_purchase_timestamp >= '2017-01-02') & (o.order_purchase_timestamp < '2018-08-27')].copy()
o = o.merge(cu[['customer_id','customer_unique_id','customer_state']], on='customer_id', how='left')
lim = it.groupby('order_id').shipping_limit_date.max().rename('lim')
o = o.merge(lim, on='order_id', how='left')
last = rv.sort_values(['order_id','review_answer_timestamp','review_id'], ascending=[True,False,True]).drop_duplicates('order_id')
o = o.merge(last[['order_id','review_score']], on='order_id', how='left')
deadline = o.order_estimated_delivery_date + pd.Timedelta(days=1)
deliv = (o.order_status == 'delivered') & o.order_delivered_customer_date.notna()
late = deliv & (o.order_delivered_customer_date >= deadline)
canc = o.order_status.isin(['canceled','unavailable'])
o['outcome'] = np.select([canc, late, deliv], ['cancelled','delivered_late','delivered_on_time'], 'stalled')
o['late'] = late; o['deliv'] = deliv
has_h = o.order_delivered_carrier_date.notna() & o.lim.notna()
late_h = has_h & (o.order_delivered_carrier_date > o.lim)
R['orders'] = len(o)
R['outcomes'] = o.outcome.value_counts().to_dict()
R['late_pct_of_delivered'] = round(100*late.sum()/deliv.sum(), 2)
R['late_handoff'] = dict(n=int(late_h.sum()), base=int(has_h.sum()), pct=round(100*late_h.sum()/has_h.sum(), 2))
# customer impact
g = o.groupby('outcome').review_score
R['review'] = {k: dict(avg=round(v.mean(),2), low_pct=round(100*(v<=2).sum()/v.notna().sum(),1), reviewed=int(v.notna().sum())) for k, v in g}
# late cause
past = (o.order_delivered_customer_date - deadline).dt.total_seconds()//60/60.0
hdel = (o.order_delivered_carrier_date - o.lim).dt.total_seconds()//60/60.0
cause = np.select([~late, ~has_h, late_h & (hdel >= past), late_h], ['', 'unknown', 'seller_handoff', 'shared'], 'carrier_or_promise')
R['late_cause'] = pd.Series(cause)[late.values].value_counts().to_dict()
# periods
p = np.select([(o.order_purchase_timestamp >= '2017-11-20') & (o.order_purchase_timestamp < '2017-12-11'),
               (o.order_purchase_timestamp >= '2018-02-12') & (o.order_purchase_timestamp < '2018-03-19')],
              ['Black Friday 2017','Feb-Mar 2018'], 'Normal weeks')
o['period'] = p; o['cause'] = cause; o['late_h'] = late_h; o['has_h'] = has_h
R['periods'] = {k: dict(orders=len(v), late=int(v.late.sum()), late_pct=round(100*v.late.sum()/v.deliv.sum(),1),
                        late_handoff_pct=round(100*v.late_h.sum()/v.has_h.sum(),1),
                        on_time_handoff_share_of_late=round(100*(v.cause=='carrier_or_promise').sum()/((v.late)&(v.cause!='unknown')).sum(),1))
                for k, v in o.groupby('period')}
rj = o[(o.customer_state=='RJ')]
R['RJ'] = {k: round(100*v.late.sum()/v.deliv.sum(),1) for k, v in rj.groupby('period')}
# promise
dd = o[deliv]
R['promise'] = dict(promised_p50=round(((deadline[deliv]-dd.order_purchase_timestamp).dt.total_seconds()/86400).median(),1),
                    actual_p50=round(((dd.order_delivered_customer_date-dd.order_purchase_timestamp).dt.total_seconds()/86400).median(),1),
                    early7_pct=round(100*((deadline[deliv]-dd.order_delivered_customer_date).dt.total_seconds() >= 7*86400).mean(),1))
# sellers
os_ = it[['order_id','seller_id']].drop_duplicates().merge(
    o[['order_id','late_h','has_h','cause','review_score','late','deliv']], on='order_id')
s = os_.groupby('seller_id').agg(h=('has_h','sum'), lh=('late_h','sum'),
                                  seller_caused_late=('cause', lambda x: (x=='seller_handoff').sum()))
s = s[s.h >= 50]; plat = late_h.sum()/has_h.sum(); z = 1.96
ph = s.lh/s.h
wl = (ph + z*z/(2*s.h) - z*np.sqrt((ph*(1-ph) + z*z/(4*s.h))/s.h))/(1+z*z/s.h)
fl = wl > plat
R['sellers'] = dict(scored=len(s), flagged=int(fl.sum()), flagged_share_orders=round(100*s.h[fl].sum()/s.h.sum(),1),
                    flagged_share_late_handoffs=round(100*s.lh[fl].sum()/s.lh.sum(),1), scored_orders=int(s.h.sum()))

# initiative sizing: seller handoff program
sf = s[fl].copy()
sf['excess_frac'] = np.where(sf.lh > 0, np.maximum(sf.lh - sf.h * plat, 0) / sf.lh, 0.0)
seller_avoidable = (sf.excess_frac * sf.seller_caused_late).sum()
sf_mask = os_.seller_id.isin(sf.index) & (os_.cause == 'seller_handoff')
sf_low_review_rate = (os_.loc[sf_mask, 'review_score'] <= 2).sum() / os_.loc[sf_mask, 'review_score'].notna().sum()
R['initiative_seller'] = dict(late_orders_avoided=round(seller_avoidable),
                              low_reviews_avoided=round(seller_avoidable * sf_low_review_rate))

# initiative sizing: episode response and lane-level promise, re-sized to
# only count what was actually actionable. Black Friday can be planned for
# ahead of time (counted in full); Feb-Mar 2018 could not, so only orders
# purchased after the real detection delay (the dataset's own median
# promise length) count.
o['days_late'] = (o.order_delivered_customer_date.dt.normalize() - o.order_estimated_delivery_date).dt.days
promised_days_all = (deadline - o.order_purchase_timestamp).dt.total_seconds() / 86400
median_promised_days = promised_days_all.median()
feb_mar_detected_at = pd.Timestamp('2018-02-12') + pd.Timedelta(days=round(median_promised_days))


def episode_part(mask):
    late = o[mask & o.late]
    return dict(late_orders_avoided=int((late.days_late <= 7).sum()),
                late_orders_avoided_3d_cap=int((late.days_late <= 3).sum()),
                low_reviews_avoided=int(((late.days_late <= 7) & (late.review_score <= 2)).sum()))


def total_parts(a, b):
    return {k: a[k] + b[k] for k in a}


bf_mask = (o.order_purchase_timestamp >= '2017-11-20') & (o.order_purchase_timestamp < '2017-12-11')
fm_mask = (o.order_purchase_timestamp >= '2018-02-12') & (o.order_purchase_timestamp < '2018-03-19')
fm_actionable_mask = fm_mask & (o.order_purchase_timestamp >= feb_mar_detected_at)

bf_part = episode_part(bf_mask)
fm_part = episode_part(fm_actionable_mask)
R['initiative_episode'] = dict(black_friday=bf_part, feb_mar=fm_part, total=total_parts(bf_part, fm_part))


def top_states_before(cutoff):
    before = o[o.order_purchase_timestamp < cutoff]
    g = before.groupby('customer_state').agg(delivered=('deliv', 'sum'), late=('late', 'sum'))
    g = g[g.delivered >= 300]
    g['late_rate'] = g.late / g.delivered
    return g.sort_values('late_rate', ascending=False).head(5).index.tolist()


top_bf = top_states_before('2017-11-20')
top_fm = top_states_before('2018-02-12')
bf_lane_part = episode_part(bf_mask & o.customer_state.isin(top_bf))
fm_lane_part = episode_part(fm_actionable_mask & o.customer_state.isin(top_fm))
R['initiative_lane'] = dict(black_friday=bf_lane_part, feb_mar=fm_lane_part,
                            total=total_parts(bf_lane_part, fm_lane_part),
                            top_states_black_friday=top_bf, top_states_feb_mar=top_fm)

# launch scorecard: do new sellers have a rough first month?
new_sellers = seller_first_order[seller_first_order >= '2017-03-01'].index
os2 = it[['order_id', 'seller_id']].drop_duplicates().merge(
    o[['order_id', 'order_purchase_timestamp', 'outcome']], on='order_id')
os2 = os2[os2.seller_id.isin(new_sellers)].copy()
os2['first_order_at'] = os2.seller_id.map(seller_first_order)
os2['seller_age_days'] = (os2.order_purchase_timestamp.dt.normalize() - os2.first_order_at.dt.normalize()).dt.days
os2['tenure_bucket'] = np.select([os2.seller_age_days < 30, os2.seller_age_days < 90],
                                  ['First 30 days', 'Days 31 to 90'], 'After day 90')
os2['cancelled'] = os2.outcome == 'cancelled'

first_look = os2.groupby('tenure_bucket').agg(orders=('cancelled', 'size'), cancelled=('cancelled', 'sum'))
R['launch'] = {'first_look': {k: dict(orders=int(v.orders), cancelled=int(v.cancelled),
                                       cancel_pct=round(100 * v.cancelled / v.orders, 2))
                               for k, v in first_look.iterrows()}}

os2['purchase_month'] = os2.order_purchase_timestamp.dt.to_period('M').dt.to_timestamp()
strata = os2[os2.tenure_bucket.isin(['First 30 days', 'After day 90'])].groupby(
    ['purchase_month', 'tenure_bucket']).agg(orders=('cancelled', 'size'), cancelled=('cancelled', 'sum')).reset_index()
new_m = strata[strata.tenure_bucket == 'First 30 days'].set_index('purchase_month')
vet_m = strata[strata.tenure_bucket == 'After day 90'].set_index('purchase_month')
vet_m = vet_m[vet_m.orders >= 30]
common = new_m.index.intersection(vet_m.index)
new_m, vet_m = new_m.loc[common], vet_m.loc[common]
new_orders = int(new_m.orders.sum())
new_cancelled = int(new_m.cancelled.sum())
veteran_orders = int(vet_m.orders.sum())
veteran_cancelled = int(vet_m.cancelled.sum())
veteran_matched_rate = (new_m.orders * (vet_m.cancelled / vet_m.orders)).sum() / new_orders
R['launch']['controlled'] = dict(
    new_seller_orders=new_orders,
    new_seller_cancelled=new_cancelled,
    new_seller_cancel_pct=round(100 * new_cancelled / new_orders, 2),
    veteran_orders_in_matched_months=veteran_orders,
    veteran_cancelled_in_matched_months=veteran_cancelled,
    veteran_matched_cancel_pct=round(100 * veteran_matched_rate, 2))

# early warning: share of parcels in transit >10 days, at each week's end
o['purchase_week'] = (o.order_purchase_timestamp
                       - pd.to_timedelta(o.order_purchase_timestamp.dt.weekday, unit='D')).dt.normalize()
by_week = {}
for wk in sorted(o.purchase_week.unique()):
    week_end = wk + pd.Timedelta(days=6)
    mask = (o.order_delivered_carrier_date.notna() & (o.order_delivered_carrier_date <= week_end)
            & (o.order_delivered_customer_date.isna() | (o.order_delivered_customer_date > week_end)))
    in_transit = int(mask.sum())
    if in_transit == 0:
        continue
    days_in_transit = (week_end - o.loc[mask, 'order_delivered_carrier_date'].dt.normalize()).dt.days
    in_transit_10plus = int((days_in_transit > 10).sum())
    by_week[wk.strftime('%Y-%m-%d')] = round(100 * in_transit_10plus / in_transit, 2)
R['early_warning'] = dict(
    black_friday_week_before_pct=by_week.get('2017-11-13'),
    feb_mar_week_before_pct=by_week.get('2018-02-05'))

# repeat purchase after first delivered order
o = o.sort_values(['customer_unique_id','order_purchase_timestamp','order_id'])
first = o.drop_duplicates('customer_unique_id')
first = first[first.deliv][['customer_unique_id','order_delivered_customer_date','late']].rename(columns={'order_delivered_customer_date':'d0'})
m = o[['customer_unique_id','order_purchase_timestamp']].merge(first, on='customer_unique_id')
end = pd.Timestamp('2018-08-27')
for days in (180, 90):
    hit = m[(m.order_purchase_timestamp > m.d0) & (m.order_purchase_timestamp <= m.d0 + pd.Timedelta(days=days))].customer_unique_id.unique()
    el = first[first.d0 + pd.Timedelta(days=days) <= end]
    rep = el.customer_unique_id.isin(hit)
    R[f'repeat_{days}'] = {('late' if k else 'on_time'): dict(customers=int(len(v)), repeaters=int(rep[v.index].sum()),
                           pct=round(100*rep[v.index].mean(),2)) for k, v in el.groupby('late')}
R['customers'] = int(o.customer_unique_id.nunique())
R['repeat_any_pct'] = round(100*(o.groupby('customer_unique_id').size() > 1).mean(), 2)

# ---- cancellation trend (query 15) ----
cut = o.order_purchase_timestamp.median()
half = np.where(o.order_purchase_timestamp < cut, 'First half', 'Second half')
# read cancellation off o itself: the bare `canc` Series still carries the
# pre-sort row order, and o was re-sorted for the repeat-purchase test above
is_canc = o.outcome.eq('cancelled').to_numpy()
R['cancel_trend'] = {}
for name in ('First half', 'Second half'):
    m = half == name
    R['cancel_trend'][name] = dict(orders=int(m.sum()), cancelled=int(is_canc[m].sum()),
                                   cancel_pct=round(100*is_canc[m].sum()/m.sum(), 2))
bym = o.assign(c=is_canc).groupby(o.order_purchase_timestamp.dt.to_period('M'))
agg = bym.agg(orders=('c','size'), cancelled=('c','sum'))
agg = agg[agg.orders >= 500]
agg['pct'] = (100*agg.cancelled/agg.orders).round(2)
worst = agg.sort_values('pct', ascending=False).iloc[0]
R['cancel_trend']['worst_month'] = dict(month=str(agg.sort_values('pct', ascending=False).index[0]),
                                        orders=int(worst.orders), cancel_pct=float(worst.pct))

# ---- order timeline (query 16) ----
# DuckDB's datediff('minute', ...) counts whole minutes, so floor before scaling
mins = lambda a, b: (b - a).dt.total_seconds() // 60
o['seller_leg']  = mins(o.order_purchase_timestamp, o.order_delivered_carrier_date) / 1440.0
o['carrier_leg'] = mins(o.order_delivered_carrier_date, o.order_delivered_customer_date) / 1440.0
o['total_days']  = mins(o.order_purchase_timestamp, o.order_delivered_customer_date) / 1440.0
o['promise_days'] = mins(o.order_purchase_timestamp, deadline) / 1440.0
o['days_early'] = mins(o.order_delivered_customer_date, deadline) / 1440.0
R['timeline'] = {}
for name, v in o.groupby('period'):
    d = v[v.deliv]
    R['timeline'][name] = dict(
        delivered=int(v.deliv.sum()),
        seller_leg_p50=round(d.seller_leg.median(), 1),
        carrier_leg_p50=round(d.carrier_leg.median(), 1),
        total_p50=round(d.total_days.median(), 1),
        promised_p50=round(v.promise_days.median(), 1),
        carrier_leg_p90=round(d.carrier_leg.quantile(0.9), 1))
for name in ('Black Friday 2017', 'Feb-Mar 2018'):
    R['timeline'][name]['seller_leg_vs_normal'] = round(
        R['timeline'][name]['seller_leg_p50'] - R['timeline']['Normal weeks']['seller_leg_p50'], 1)
    R['timeline'][name]['carrier_leg_vs_normal'] = round(
        R['timeline'][name]['carrier_leg_p50'] - R['timeline']['Normal weeks']['carrier_leg_p50'], 1)

# ---- escalation (query 17) ----
# same rule as the SQL: of the flagged sellers, the one whose late handoffs
# caused the most late deliveries, ties broken by seller_id
top = s[fl].reset_index().sort_values(
    ['seller_caused_late','seller_id'], ascending=[False,True]).iloc[0]['seller_id']
e = os_[os_.seller_id == top]
e_h = int(e.has_h.sum()); e_rev = int(e.review_score.notna().sum())
R['escalation_seller'] = dict(
    seller=top[:8], scored_orders=e_h, late_handoffs=int(e.late_h.sum()),
    late_handoff_pct=round(100*e.late_h.sum()/e_h, 1),
    late_deliveries=int(e.late.sum()),
    late_delivery_pct=round(100*e.late.sum()/e_h, 1),
    seller_caused_late=int((e.cause == 'seller_handoff').sum()),
    shared_late=int((e.cause == 'shared').sum()),
    reviewed=e_rev,
    low_review_pct=round(100*(e.review_score <= 2).sum()/e_rev, 1))


# Does a late handoff cost reviews even when the parcel still arrives on
# time? Restricted to on-time deliveries, so lateness cannot explain it.
def handoff_review_split(frame, late_col, rev_col):
    out = {}
    for flag, name in ((False, 'on_time_handoff'), (True, 'late_handoff')):
        v = frame[frame[late_col] == flag]
        rev = v[rev_col].notna().sum()
        out[name] = dict(on_time_deliveries=int(len(v)), reviewed=int(rev),
                         avg_review=round(v[rev_col].mean(), 2),
                         low_reviews=int((v[rev_col] <= 2).sum()),
                         low_review_pct=round(100*(v[rev_col] <= 2).sum()/rev, 1))
    return out


R['handoff_reviews_platform'] = handoff_review_split(
    o[o.deliv & ~o.late & o.has_h], 'late_h', 'review_score')
R['handoff_reviews_seller'] = handoff_review_split(
    e[e.deliv & ~e.late & e.has_h], 'late_h', 'review_score')

# the likely mechanism: on-time orders that were handed over late still
# reach the customer later, and closer to the deadline
_ot = o[o.deliv & ~o.late & o.has_h]
R['handoff_wait'] = {
    name: dict(total_days_p50=round(_ot[_ot.late_h == flag].total_days.median(), 1),
               days_early_p50=round(_ot[_ot.late_h == flag].days_early.median(), 1))
    for flag, name in ((False, 'on_time_handoff'), (True, 'late_handoff'))}

rj = o[o.customer_state == 'RJ']
R['escalation_rj'] = {}
for name, v in rj.groupby('period'):
    d = v[v.deliv]
    R['escalation_rj'][name] = dict(
        delivered=int(v.deliv.sum()), late=int(v.late.sum()),
        late_pct=round(100*v.late.sum()/v.deliv.sum(), 1),
        late_handoff_pct=round(100*v.late_h.sum()/v.has_h.sum(), 1),
        seller_leg_p50=round(d.seller_leg.median(), 1),
        carrier_leg_p50=round(d.carrier_leg.median(), 1))
_n = R['escalation_rj']['Normal weeks']; _e = R['escalation_rj']['Feb-Mar 2018']
R['escalation_rj']['excess_late_orders'] = round(
    _e['late'] - _e['delivered'] * (_n['late'] / _n['delivered']))

# ---- episode late rate against normal weeks, in percentage points ----
# recomputed from the unrounded rates, exactly as the SQL does, so a
# rounding difference would show up as a mismatch rather than be hidden
def _late_rate(mask):
    v = o[mask]
    return 100.0 * v.late.sum() / v.deliv.sum()


_normal = _late_rate(o.period == 'Normal weeks')
R['late_vs_normal'] = {
    name: dict(late_pct=round(_late_rate(o.period == name), 1),
               normal_late_pct=round(_normal, 1),
               late_pct_vs_normal=round(_late_rate(o.period == name) - _normal, 1))
    for name in ('Black Friday 2017', 'Feb-Mar 2018')}

_rj = o[o.customer_state == 'RJ']
_rj_normal = 100.0 * _rj[_rj.period == 'Normal weeks'].late.sum() / _rj[_rj.period == 'Normal weeks'].deliv.sum()
_rj_ep = 100.0 * _rj[_rj.period == 'Feb-Mar 2018'].late.sum() / _rj[_rj.period == 'Feb-Mar 2018'].deliv.sum()
R['rj_vs_normal'] = dict(episode_late_pct=round(_rj_ep, 1),
                         normal_late_pct=round(_rj_normal, 1),
                         late_pct_vs_normal=round(_rj_ep - _rj_normal, 1))
(ROOT / "out").mkdir(exist_ok=True)
(ROOT / "out" / "pandas_recheck.json").write_text(json.dumps(R, indent=1, default=int))
print(json.dumps(R, indent=1, default=int))
