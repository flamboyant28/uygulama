import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date
import plotly.express as px

st.set_page_config(page_title='Hisse Portföy & Trading Journal', page_icon='📈', layout='wide')
BASE = Path(__file__).resolve().parent
HISSELER = BASE / 'hisseler.csv'
ISLEMLER = BASE / 'islemler.csv'
MARKET_COLS = ['Tarih','Hisseler','Kod','Hisse Adı','Son','% Fark','Hacim (TL)','Saat']
TRADE_COLS = ['id','Tarih','Hisse','İşlem','Lot','Fiyat','Tutar']


def ensure_files():
    if not HISSELER.exists(): pd.DataFrame(columns=MARKET_COLS).to_csv(HISSELER,index=False,encoding='utf-8-sig')
    if not ISLEMLER.exists(): pd.DataFrame(columns=TRADE_COLS).to_csv(ISLEMLER,index=False,encoding='utf-8-sig')


def read_csv(path, cols):
    if not path.exists(): return pd.DataFrame(columns=cols)
    try: df = pd.read_csv(path, encoding='utf-8-sig')
    except UnicodeDecodeError: df = pd.read_csv(path, encoding='cp1254')
    for c in cols:
        if c not in df.columns: df[c] = ''
    return df[cols]


def num(x):
    if pd.isna(x): return np.nan
    if isinstance(x,(int,float,np.number)): return float(x)
    s=str(x).strip().replace('₺','').replace('TL','').replace('%','').replace(' ','')
    if ',' in s: s=s.replace('.','').replace(',','.')
    elif s.count('.')>1: s=s.replace('.','')
    try: return float(s)
    except: return np.nan


def tl(x):
    if pd.isna(x): return '-'
    return f'{float(x):,.2f}'.replace(',','X').replace('.',',').replace('X','.')+' ₺'


def nfmt(x):
    if pd.isna(x): return '-'
    return f'{float(x):,.2f}'.replace(',','X').replace('.',',').replace('X','.')


def lotfmt(x):
    if pd.isna(x): return '-'
    return f'{int(x):,}'.replace(',','.') if float(x).is_integer() else nfmt(x)


def pct(x):
    if pd.isna(x): return '-'
    return f'{float(x):+.2f}%'.replace('.',',')


def normalize_market(df):
    df=df.copy(); df.columns=[str(c).strip() for c in df.columns]
    aliases={'Hisseler':['Hisseler','Hisse','Hisse Adı','Hisse Adi'],'Son':['Son','Fiyat','Son Fiyat'],'% Fark':['% Fark','Fark','Değişim','Degisim'],'Hacim (TL)':['Hacim (TL)','Hacim','Hacim(TL)'],'Saat':['Saat','Time']}
    ren={}
    for target, names in aliases.items():
        for name in names:
            if name in df.columns: ren[name]=target; break
    df=df.rename(columns=ren)
    missing=[c for c in ['Hisseler','Son','% Fark','Hacim (TL)','Saat'] if c not in df.columns]
    if missing: raise ValueError('Eksik kolon: '+', '.join(missing))
    df=df[['Hisseler','Son','% Fark','Hacim (TL)','Saat']].copy()
    df['Hisseler']=df['Hisseler'].astype(str).str.strip()
    parts=df['Hisseler'].str.extract(r'^\s*([A-Za-z0-9ÇĞİÖŞÜçğıöşü]+)\s+(.*)$')
    df['Kod']=parts[0].fillna(df['Hisseler']).str.upper().str.strip()
    df['Hisse Adı']=parts[1].fillna('').str.strip()
    df['Son']=df['Son'].map(num); df['% Fark']=df['% Fark'].map(num); df['Hacim (TL)']=df['Hacim (TL)'].map(num)
    df['Saat']=df['Saat'].astype(str).str.strip(); df['Tarih']=date.today().isoformat()
    return df[MARKET_COLS]


def load_market():
    d=read_csv(HISSELER,MARKET_COLS)
    if d.empty: return d
    d['Kod']=d['Kod'].astype(str).str.upper().str.strip(); d['Son']=d['Son'].map(num); d['% Fark']=d['% Fark'].map(num); d['Hacim (TL)']=d['Hacim (TL)'].map(num)
    return d


def load_trades():
    d=read_csv(ISLEMLER,TRADE_COLS)
    if d.empty: return d
    d['Tarih']=pd.to_datetime(d['Tarih'],errors='coerce'); d['Hisse']=d['Hisse'].astype(str).str.upper().str.strip(); d['İşlem']=d['İşlem'].astype(str).str.upper().str.strip(); d['Lot']=d['Lot'].map(num); d['Fiyat']=d['Fiyat'].map(num); d['Tutar']=d['Lot']*d['Fiyat']
    return d


def latest_market(m):
    if m.empty:return m
    x=m.copy(); x['_dt']=pd.to_datetime(x['Tarih'].astype(str)+' '+x['Saat'].astype(str),errors='coerce'); return x.sort_values('_dt').drop_duplicates('Kod',keep='last').drop(columns='_dt')


def calc(trades, market):
    if trades.empty:return pd.DataFrame(),pd.DataFrame()
    pos={}; results=[]
    t=trades.copy(); t['_date']=pd.to_datetime(t['Tarih'],errors='coerce'); t=t.sort_values(['_date','id'])
    for _,r in t.iterrows():
        s=r['Hisse']; side=r['İşlem']; q=float(r['Lot'] or 0); p=float(r['Fiyat'] or 0)
        pos.setdefault(s,{'lot':0.0,'cost':0.0})
        oldlot=pos[s]['lot']; oldavg=pos[s]['cost']/oldlot if oldlot else 0
        realized=0
        if side=='AL': pos[s]['lot']+=q; pos[s]['cost']+=q*p
        elif side=='SAT':
            q=min(q,pos[s]['lot']); realized=(p-oldavg)*q; pos[s]['lot']-=q; pos[s]['cost']-=oldavg*q
            if pos[s]['lot']<1e-9: pos[s]={'lot':0.0,'cost':0.0}
        newavg=pos[s]['cost']/pos[s]['lot'] if pos[s]['lot'] else 0
        results.append({'id':r['id'],'Tarih':r['Tarih'],'Hisse':s,'İşlem':side,'Lot':q,'Fiyat':p,'Tutar':q*p,'İşlem Öncesi Lot':oldlot,'İşlem Öncesi Ort. Maliyet':oldavg,'Gerçekleşen K/Z':realized,'İşlem Sonrası Lot':pos[s]['lot'],'İşlem Sonrası Ort. Maliyet':newavg})
    lookup=market.set_index('Kod').to_dict('index') if not market.empty else {}
    rows=[]
    for s,v in pos.items():
        if v['lot']<=0: continue
        mk=lookup.get(s,{ }); price=mk.get('Son',np.nan); value=v['lot']*price if not pd.isna(price) else np.nan
        rows.append({'Hisse':s,'Hisse Adı':mk.get('Hisse Adı',''),'Lot':v['lot'],'Ort. Maliyet':v['cost']/v['lot'],'Son':price,'% Fark':mk.get('% Fark',np.nan),'Maliyet':v['cost'],'Güncel Değer':value,'Açık K/Z':value-v['cost'] if not pd.isna(value) else np.nan})
    pf=pd.DataFrame(rows); rr=pd.DataFrame(results)
    if not pf.empty:
        pf['Lot %']=pf['Lot']/pf['Lot'].sum()*100; total=pf['Güncel Değer'].sum(skipna=True); pf['Değer %']=pf['Güncel Değer']/total*100 if total else 0
    return pf,rr


def display_portfolio(p):
    if p.empty:return p
    return pd.DataFrame({'Hisse':p['Hisse'],'Hisse Adı':p['Hisse Adı'],'Lot':p['Lot'].map(lotfmt),'Ort. Maliyet':p['Ort. Maliyet'].map(tl),'Son':p['Son'].map(tl),'% Fark':p['% Fark'].map(pct),'Maliyet':p['Maliyet'].map(tl),'Güncel Değer':p['Güncel Değer'].map(tl),'Açık K/Z':p['Açık K/Z'].map(tl),'Lot %':p['Lot %'].map(lambda x:f'{x:.2f}%'.replace('.',',')),'Değer %':p['Değer %'].map(lambda x:f'{x:.2f}%'.replace('.',','))})

ensure_files(); market=load_market(); trades=load_trades(); latest=latest_market(market); portfolio,results=calc(trades,latest)

st.title('📈 Hisse Portföy & Trading Journal')
st.caption('İki ayrı CSV: hisseler.csv = piyasa verisi | islemler.csv = kişisel işlemler')

with st.sidebar:
    st.header('⚙️ Veri Yönetimi')
    up=st.file_uploader('Piyasa CSV yükle',type='csv')
    if st.button('📥 Piyasa verisini ekle',use_container_width=True):
        if up is None: st.warning('Önce CSV seç.'); st.stop()
        try:
            try: raw=pd.read_csv(up,encoding='utf-8-sig')
            except UnicodeDecodeError: raw=pd.read_csv(up,encoding='cp1254')
            new=normalize_market(raw); old=load_market(); allm=pd.concat([old,new],ignore_index=True).drop_duplicates(['Tarih','Saat','Kod'],keep='last'); allm.to_csv(HISSELER,index=False,encoding='utf-8-sig'); st.success(f'{len(new)} kayıt işlendi.'); st.rerun()
        except Exception as e: st.error(str(e))
    st.divider(); st.write(f'📄 `{HISSELER.name}`'); st.write(f'📄 `{ISLEMLER.name}`')
    if HISSELER.exists(): st.download_button('⬇️ hisseler.csv',HISSELER.read_bytes(),'hisseler.csv','text/csv',use_container_width=True)
    if ISLEMLER.exists(): st.download_button('⬇️ islemler.csv',ISLEMLER.read_bytes(),'islemler.csv','text/csv',use_container_width=True)

if latest.empty: st.info('Sol menüden örnekteki piyasa CSV dosyanı yükleyerek başlayabilirsin.')

t1,t2,t3,t4=st.tabs(['📊 Dashboard','🔄 İşlemler','💰 Satış Analizi','📁 Piyasa'])
with t1:
    if portfolio.empty: st.info('Açık pozisyon yok. İşlemler sekmesinden AL işlemi gir.')
    else:
        cost=portfolio['Maliyet'].sum(); value=portfolio['Güncel Değer'].sum(skipna=True); openp=portfolio['Açık K/Z'].sum(skipna=True); real=results['Gerçekleşen K/Z'].sum() if not results.empty else 0
        a,b,c,d,e=st.columns(5); a.metric('Toplam Maliyet',tl(cost)); b.metric('Güncel Portföy',tl(value)); c.metric('Açık K/Z',tl(openp)); d.metric('Gerçekleşen K/Z',tl(real)); e.metric('Toplam K/Z',tl(openp+real))
        st.subheader('📋 Portföy'); st.dataframe(display_portfolio(portfolio),use_container_width=True,hide_index=True)
        c1,c2=st.columns(2)
        with c1: st.plotly_chart(px.pie(portfolio,values='Güncel Değer',names='Hisse',hole=.35,title='Portföy Değer Dağılımı'),use_container_width=True)
        with c2: st.plotly_chart(px.pie(portfolio,values='Lot',names='Hisse',hole=.35,title='Lot Dağılımı'),use_container_width=True)
        st.plotly_chart(px.bar(portfolio.sort_values('Açık K/Z'),x='Hisse',y='Açık K/Z',text='Açık K/Z',title='Açık Kâr / Zarar'),use_container_width=True)

with t2:
    st.subheader('➕ İşlem Ekle')
    opts=sorted(latest['Kod'].dropna().unique()) if not latest.empty else []
    c1,c2,c3,c4,c5=st.columns(5)
    symbol=c1.selectbox('Hisse',opts,index=None,placeholder='Hisse ara...') if opts else c1.text_input('Hisse').upper()
    side=c2.selectbox('İşlem',['AL','SAT']); q=c3.number_input('Lot',min_value=.01,value=1.0,step=1.0); price=c4.number_input('Fiyat',min_value=.0001,value=1.0,step=.01,format='%.4f'); dt=c5.date_input('Tarih',date.today())
    if st.button('💾 Kaydet',type='primary'):
        if not symbol: st.error('Hisse seç.'); st.stop()
        if side=='SAT':
            have=float(portfolio.loc[portfolio.Hisse==symbol,'Lot'].iloc[0]) if not portfolio.loc[portfolio.Hisse==symbol].empty else 0
            if q>have: st.error(f'Mevcut lot: {lotfmt(have)}'); st.stop()
        ids=pd.to_numeric(trades['id'],errors='coerce'); new_id=int(ids.max())+1 if ids.notna().any() else 1
        row=pd.DataFrame([{'id':new_id,'Tarih':dt,'Hisse':symbol.upper(),'İşlem':side,'Lot':q,'Fiyat':price,'Tutar':q*price}]); pd.concat([trades,row],ignore_index=True).to_csv(ISLEMLER,index=False,encoding='utf-8-sig'); st.success('İşlem kaydedildi.'); st.rerun()
    st.divider(); st.subheader('📜 İşlem Geçmişi')
    if trades.empty: st.info('İşlem yok.')
    else:
        x=trades.copy(); x['Tarih']=pd.to_datetime(x.Tarih).dt.strftime('%d.%m.%Y'); x['Lot']=x.Lot.map(lotfmt); x['Fiyat']=x.Fiyat.map(tl); x['Tutar']=x.Tutar.map(tl); st.dataframe(x.sort_values('Tarih',ascending=False),use_container_width=True,hide_index=True)
        did=st.number_input('Silinecek ID',min_value=1,step=1)
        if st.button('🗑️ İşlemi sil'):
            if did in trades.id.astype(int).values: trades=trades[trades.id.astype(int)!=int(did)]; trades.to_csv(ISLEMLER,index=False,encoding='utf-8-sig'); st.rerun()
            else: st.warning('ID bulunamadı.')

with t3:
    st.subheader('💰 Gerçekleşen K/Z')
    sales=results[results['İşlem']=='SAT'].copy() if not results.empty else pd.DataFrame()
    if sales.empty: st.info('Henüz satış yok.')
    else:
        a,b,c=st.columns(3); a.metric('Satılan Lot',lotfmt(sales.Lot.sum())); b.metric('Gerçekleşen K/Z',tl(sales['Gerçekleşen K/Z'].sum())); b=0
        win=(sales['Gerçekleşen K/Z']>0).sum(); loss=(sales['Gerçekleşen K/Z']<0).sum(); c.metric('Kârlı / Zararlı',f'{win} / {loss}')
        x=sales.copy(); x['Tarih']=pd.to_datetime(x.Tarih).dt.strftime('%d.%m.%Y')
        for col in ['Lot','İşlem Öncesi Lot','İşlem Sonrası Lot']: x[col]=x[col].map(lotfmt)
        for col in ['Fiyat','Tutar','İşlem Öncesi Ort. Maliyet','Gerçekleşen K/Z','İşlem Sonrası Ort. Maliyet']: x[col]=x[col].map(tl)
        st.dataframe(x,use_container_width=True,hide_index=True)
        st.divider(); st.subheader('🔎 Satış Sonrası Fiyat')
        if not market.empty:
            mh=market.copy(); mh['_d']=pd.to_datetime(mh.Tarih,errors='coerce'); rows=[]
            for _,s in sales.iterrows():
                f=mh[(mh.Kod==s.Hisse)&(mh._d>pd.to_datetime(s.Tarih))].sort_values(['_d','Saat'])
                if not f.empty:
                    z=f.iloc[-1]; p=z.Son
                    rows.append({'Hisse':s.Hisse,'Satış Tarihi':s.Tarih,'Satış Fiyatı':s.Fiyat,'Satılan Lot':s.Lot,'Sonraki Tarih':z._d,'Sonraki Fiyat':p,'Fiyat Farkı':p-s.Fiyat,'Bugün Tutulsaydı':(p-s.Fiyat)*s.Lot})
            if rows:
                y=pd.DataFrame(rows); y['Satış Tarihi']=pd.to_datetime(y['Satış Tarihi']).dt.strftime('%d.%m.%Y'); y['Sonraki Tarih']=pd.to_datetime(y['Sonraki Tarih']).dt.strftime('%d.%m.%Y')
                for col in ['Satış Fiyatı','Sonraki Fiyat','Fiyat Farkı','Bugün Tutulsaydı']: y[col]=y[col].map(tl)
                y['Satılan Lot']=y['Satılan Lot'].map(lotfmt); st.dataframe(y,use_container_width=True,hide_index=True)
            else: st.info('Satış tarihinden sonraki piyasa verisi henüz yok.')

with t4:
    st.subheader('📁 Son Piyasa Verileri')
    if latest.empty: st.info('Veri yok.')
    else:
        x=latest.copy(); x['Son']=x.Son.map(tl); x['% Fark']=x['% Fark'].map(pct); x['Hacim (TL)']=x['Hacim (TL)'].map(tl); st.dataframe(x[['Kod','Hisse Adı','Son','% Fark','Hacim (TL)','Saat']].sort_values('Kod'),use_container_width=True,hide_index=True)
        st.subheader('📈 Fiyat Geçmişi'); opts=sorted(market.Kod.dropna().unique()); s=st.selectbox('Hisse',opts,index=None,placeholder='Hisse ara...')
        if s:
            h=market[market.Kod==s].copy(); h['Zaman']=pd.to_datetime(h.Tarih.astype(str)+' '+h.Saat.astype(str),errors='coerce'); h=h.sort_values('Zaman'); st.plotly_chart(px.line(h,x='Zaman',y='Son',markers=True,title=f'{s} fiyat geçmişi'),use_container_width=True)

st.divider(); st.caption('Yerel CSV yapısı: hisseler.csv piyasa verisi, islemler.csv kişisel işlemler. FIFO kullanılmaz; ağırlıklı ortalama maliyet kullanılır.')
