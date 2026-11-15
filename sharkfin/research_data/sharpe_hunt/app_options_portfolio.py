import sys; sys.path.insert(0,'/home/user/SharkFin')
from pathlib import Path
import pandas as pd, numpy as np, math
from sharkfin import swing_options_lab as S
F=Path('/home/user/SharkFin/.lab3')
gr=pd.read_csv('/home/user/SharkFin/sharkfin/research_data/growth_returns.csv',parse_dates=['Date']).set_index('Date')
spy=(1+gr.spy).cumprod(); tb=gr.tbill.fillna(0)
spy200=spy>spy.rolling(200).mean()
tbc=(1+tb).cumprod()
dz=pd.read_csv(F/'out/dz_options.csv',parse_dates=['bought','sold']); br=pd.read_csv(F/'out/br_options.csv',parse_dates=['bought','sold'])
# bias corrections from real-price overlaps
t=pd.read_csv(F/'out/trigger_trades.csv',parse_dates=['bought'])
m=t[t.kind=='dz'].merge(dz,left_on=['sym','bought'],right_on=['sym','bought']).dropna(subset=['long_call','call 1m ATM'])
b=np.polyfit(m['call 1m ATM'],m.long_call,1); print('dz call fit',b)
mp=t[t.kind=='dz'].merge(dz,left_on=['sym','bought'],right_on=['sym','bought']).dropna(subset=['short_put_on_cash'])
put_scale=mp.short_put_on_cash.mean()/mp['put 1m ATM sold'].mean(); print('put scale',put_scale)
dz['call_real_adj']=np.polyval(b,dz['call 1m ATM']); dz['put_real_adj']=dz['put 1m ATM sold']*put_scale
br['call_real_adj']=br['call 8m ATM']*0.52; br['call_model']=br['call 8m ATM']
def ret_over(series_cum,a,b_):
    i=series_cum.index
    a=i[i>=a][0]; b_=i[i<=b_][-1]; return series_cum[b_]/series_cum[a]-1
def overlay(base, trades, col, slots, frac, idle):
    adj=pd.Series(0.0,index=base.index)
    for r in trades.itertuples():
        if r.sold not in adj.index or not np.isfinite(getattr(r,col)): continue
        if idle=='dz': idle_r = ret_over(spy,r.bought,r.sold) if spy200.get(r.bought,False) else ret_over(tbc,r.bought,r.sold)
        else: idle_r = ret_over(tbc,r.bought,r.sold)
        if col.startswith('put'): opt = getattr(r,col)+ret_over(tbc,r.bought,r.sold); new=opt
        else: new=frac*getattr(r,col)+(1-frac)*idle_r
        adj[r.sold]+= (new - r.shares)/slots
    return base+adj
def hedge_series(beta):
    from sharkfin import options_model as M
    from sharkfin.bs import bs_price
    cal=M.calibrate(M.fit_real_smiles(F)); idx=pd.read_pickle(F/'idx.pkl')['Close']
    days=gr.index; spx=idx['^SPX'].reindex(days).ffill(); vix=idx['^VIX'].reindex(days).ffill()
    flag=spx<spx.rolling(200).mean(); h=pd.Series(0.0,index=days)
    for i in range(0,len(days)-21,21):
        if flag.iloc[i] and np.isfinite(vix.iloc[i]):
            S0,S1=spx.iloc[i],spx.iloc[i+21]; K=0.95*S0; T=30/365
            p=float(bs_price(S0,K,T,M.model_iv(cal,'1m',vix.iloc[i]/100,S0,K,T),-1))*1.03
            h.iloc[i+21]+=beta*(max(K-S1,0)-p)/S0
    return h
H=hedge_series(1.0)
def stats(r,lo,hi):
    x=r.loc[lo:hi]; mo=(1+x).resample('ME').prod()-1; rfm=(1+tb.loc[lo:hi]).resample('ME').prod()-1
    eq=(1+x).cumprod(); yrs=len(x)/252
    return dict(CAGR=eq.iloc[-1]**(1/yrs)-1, Sharpe=((mo-rfm).mean()/(mo-rfm).std()*math.sqrt(12)), MaxDD=(eq/eq.cummax()-1).min(), worst_month=mo.min())
P=(pd.Timestamp('2006-01-01'),pd.Timestamp('2021-10-12')); G=(pd.Timestamp('2021-10-13'),pd.Timestamp('2026-11-06'))
rows=[]
def add(name,r):
    a=stats(r,*P); g=stats(r,*G); rows.append({'strategy':name,**{f'pick_{k}':v for k,v in a.items()},**{f'grade_{k}':v for k,v in g.items()}})
d0=gr.dive_zone.fillna(0); b0=gr.tech_breakout_rider.fillna(0)
add('Dive Zone, shares (app)',d0)
add('Dive Zone, sell 1m ATM put instead (real-adjusted)',overlay(d0,dz,'put_real_adj',7,1,'dz'))
add('Dive Zone, 1m calls at 50% of slot (real-adjusted)',overlay(d0,dz,'call_real_adj',7,0.5,'dz'))
add('Dive Zone + S&P-under-200d puts',d0+0.74*H)
add('Breakout, shares (app)',b0)
for f in (0.25,0.5):
    add(f'Breakout, 8m calls at {int(f*100)}% of slot (model x0.52)',overlay(b0,br,'call_real_adj',10,f,'br'))
    add(f'Breakout, 8m calls at {int(f*100)}% of slot (model, unadjusted)',overlay(b0,br,'call_model',10,f,'br'))
bc=overlay(b0,br,'call_real_adj',10,0.25,'br')
add('Breakout 8m calls 25% (adj) + S&P-under-200d puts',bc+1.0*H)
add('Breakout shares + S&P-under-200d puts',b0+1.0*H)
add('50/50 Dive Zone shares + Breakout calls 25% (adj)',0.5*d0+0.5*bc)
add('50/50 above + S&P-under-200d puts',0.5*d0+0.5*bc+0.87*H)
add('SPY buy and hold',gr.spy.fillna(0))
out=pd.DataFrame(rows); out.to_csv(F/'out/app_strategies_options.csv',index=False)
pd.set_option('display.width',250); print(out.round(3).to_string())
