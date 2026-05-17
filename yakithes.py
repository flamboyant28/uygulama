import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go
from math import radians, sin, cos, sqrt, atan2
from datetime import time, timedelta, datetime

st.set_page_config(
    page_title="Araç Yol Bilgisayarı",
    page_icon="🚗",
    layout="wide",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.page-title {
    font-size: 2rem; font-weight: 700; color: #1F4E78;
    display: flex; align-items: center; gap: 12px; margin-bottom: 4px;
}
.page-sub { color: #888; font-size: 0.9rem; margin-bottom: 24px; }

.status-ok {
    background: linear-gradient(135deg, #375623, #70AD47);
    color: white; padding: 18px 24px; border-radius: 12px;
    display: flex; align-items: center; gap: 14px;
    font-size: 1.1rem; font-weight: 700;
    box-shadow: 0 4px 12px rgba(55,86,35,.3);
}
.status-fail {
    background: linear-gradient(135deg, #7B0000, #C00000);
    color: white; padding: 18px 24px; border-radius: 12px;
    display: flex; align-items: center; gap: 14px;
    font-size: 1.1rem; font-weight: 700;
    box-shadow: 0 4px 12px rgba(192,0,0,.3);
}
.status-icon { font-size: 2rem; }
.status-detail { font-weight: 400; font-size: 0.9rem; opacity: .85; margin-top: 2px; }

[data-testid="metric-container"] {
    background: white;
    border: 1px solid #E8EDF2;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,.05);
}
[data-testid="metric-container"] > label {
    font-size: 0.72rem !important;
    color: #888 !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: .5px;
}
[data-testid="stMetricValue"] > div {
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    color: #1F4E78 !important;
}
[data-testid="stMetricDelta"] > div {
    font-size: 0.75rem !important;
    color: #999 !important;
}
[data-testid="stMetricDeltaIcon"] { display: none !important; }

.section-header {
    font-size: 1rem; font-weight: 700; color: #1F4E78;
    border-left: 4px solid #1F4E78; padding-left: 10px;
    margin: 28px 0 12px;
}

.route-strip {
    background: #EBF3FB; border-radius: 10px;
    padding: 14px 18px; margin: 8px 0 12px;
    border-left: 4px solid #1F4E78;
}
.route-strip-title {
    font-size: 0.72rem; font-weight: 700; color: #1F4E78;
    text-transform: uppercase; letter-spacing: .6px; margin-bottom: 8px;
}
.route-seg {
    display: flex; align-items: center; gap: 6px;
    font-size: 0.85rem; color: #333; margin: 4px 0;
}
.route-seg-km {
    margin-left: auto; font-weight: 700; color: #1F4E78;
    background: white; padding: 2px 8px; border-radius: 20px;
    font-size: 0.78rem; border: 1px solid #C8DDF0;
}
.route-total {
    border-top: 1px dashed #C8DDF0; margin-top: 8px; padding-top: 8px;
    font-weight: 700; font-size: 0.9rem; color: #1F4E78;
    display: flex; justify-content: space-between;
}

[data-testid="stSidebar"] { background: #F8FAFC; border-right: 1px solid #E2E8F0; }
[data-testid="stSidebar"] label {
    font-size: 0.8rem !important; font-weight: 600 !important; color: #555 !important;
}
</style>
""", unsafe_allow_html=True)

# ── 81 İl / ~970 İlçe koordinat verisi ───────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ilce_data import ILCELER
IL_LIST = sorted(ILCELER.keys())

def ilce_listesi(il):
    return sorted(ILCELER.get(il, {}).keys())

def koordinat(il, ilce):
    return ILCELER[il][ilce]

# ── Mesafe hesabı ─────────────────────────────────────────────────────────────
ROAD_FACTOR = 1.30

def haversine_km(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return round(R * 2 * atan2(sqrt(a), sqrt(1 - a)) * ROAD_FACTOR)

# ── Session state: [(il, ilçe), ...] ─────────────────────────────────────────
if "duraks" not in st.session_state:
    st.session_state.duraks = [("İstanbul", "Kadıköy"), ("Ankara", "Çankaya")]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📍 Güzergah")

    to_remove = None
    for i in range(len(st.session_state.duraks)):
        il, ilce = st.session_state.duraks[i]
        if i == 0:              lbl = "🚩 Kalkış"
        elif i == len(st.session_state.duraks)-1: lbl = "🏁 Varış"
        else:                   lbl = f"📍 {i}. Durak"
        c1, c2 = st.columns([5, 1])
        with c1:
            new_il = st.selectbox(lbl, IL_LIST,
                index=IL_LIST.index(il) if il in IL_LIST else 0,
                key=f"il_{i}")
            ilceler = ilce_listesi(new_il)
            safe_ilce = ilce if (new_il == il and ilce in ilceler) else ilceler[0]
            new_ilce = st.selectbox("", ilceler,
                index=ilceler.index(safe_ilce),
                key=f"ilce_{i}", label_visibility="collapsed")
            st.session_state.duraks[i] = (new_il, new_ilce)
        with c2:
            st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
            if len(st.session_state.duraks) > 2:
                if st.button("✕", key=f"del_{i}", help="Durağı kaldır"):
                    to_remove = i

    if to_remove is not None:
        st.session_state.duraks.pop(to_remove)
        st.rerun()

    col_add, col_clr = st.columns(2)
    with col_add:
        if st.button("＋ Durak Ekle", use_container_width=True):
            ilceler0 = ilce_listesi("Ankara")
            st.session_state.duraks.append(("Ankara", ilceler0[0]))
            st.rerun()
    with col_clr:
        if st.button("↺ Sıfırla", use_container_width=True):
            st.session_state.duraks = [("İstanbul", "Kadıköy"), ("Ankara", "Çankaya")]
            st.rerun()

    # Segmentleri hesapla
    segments = []
    for i in range(len(st.session_state.duraks) - 1):
        a_il, a_ilce = st.session_state.duraks[i]
        b_il, b_ilce = st.session_state.duraks[i + 1]
        km = haversine_km(koordinat(a_il, a_ilce), koordinat(b_il, b_ilce))
        segments.append((f"{a_il}/{a_ilce}", f"{b_il}/{b_ilce}", km))
    total_yol = sum(s[2] for s in segments)

    if segments:
        segs_html = "".join(
            f'<div class="route-seg">🔹 {a} → {b}<span class="route-seg-km">{km} km</span></div>'
            for a, b, km in segments
        )
        st.markdown(f"""
        <div class="route-strip">
            <div class="route-strip-title">Güzergah Özeti</div>
            {segs_html}
            <div class="route-total">
                <span>Toplam mesafe</span><span>{total_yol} km</span>
            </div>
        </div>""", unsafe_allow_html=True)
        st.caption(f"📐 Tahmini mesafe · Yol katsayısı: {ROAD_FACTOR}×")

    yol = max(total_yol, 1)

    st.divider()
    st.markdown("### 🚗 Araç Bilgileri")
    hiz      = st.number_input("Ortalama Hız (km/s)", value=90, min_value=1, max_value=300)
    depo     = st.number_input("Depo Kapasitesi (L)", value=53.0, min_value=1.0, step=0.5, format="%.1f")
    tuketim  = st.number_input("100km Tüketim (L)", value=7.4, min_value=0.1, step=0.1, format="%.1f")
    fiyat    = st.number_input("Benzin Fiyatı (TL/L)", value=64.88, min_value=0.01, step=0.01, format="%.2f")
    cikis    = st.time_input("Çıkış Saati", value=time(8, 0))
    kisi     = st.number_input("Kişi Sayısı", value=1, min_value=1, max_value=20)
    aylik_km = st.number_input("Aylık Ortalama km", value=2000, min_value=0, step=100)

    st.divider()
    st.markdown("### 🔄 Yakıt Karşılaştırması")
    dizel_fiyat   = st.number_input("Dizel Fiyatı (TL/L)", value=67.32, min_value=0.01, step=0.01, format="%.2f")
    dizel_tuketim = st.number_input("Dizel 100km Tüketim (L)", value=6.5, min_value=0.1, step=0.1, format="%.1f")
    lpg_fiyat     = st.number_input("LPG Fiyatı (TL/L)", value=33.29, min_value=0.01, step=0.01, format="%.2f")
    lpg_tuketim   = st.number_input("LPG 100km Tüketim (L)", value=11.0, min_value=0.1, step=0.1, format="%.1f")

    st.divider()
    st.markdown("### ⚡ Elektrikli Araç (EV)")
    ev_fiyat   = st.number_input("Elektrik (TL/kWh)", value=12.0, min_value=0.01, step=0.01, format="%.2f")
    ev_tuketim = st.number_input("EV 100km Tüketim (kWh)", value=20.0, min_value=0.1, step=0.1, format="%.1f")
    ev_batarya = st.number_input("Batarya Kapasitesi (kWh)", value=75.0, min_value=1.0, step=1.0, format="%.1f")

# ── Hesaplamalar ──────────────────────────────────────────────────────────────
km_yakit         = tuketim / 100
km_maliyet       = km_yakit * fiyat
yol_yakiti       = yol * km_yakit
yol_maliyeti     = yol_yakiti * fiyat
tam_depo_menzil  = (depo / tuketim) * 100
tam_depo_maliyet = depo * fiyat
km100_maliyet    = tuketim * fiyat
gerekli_depo     = math.ceil(yol / tam_depo_menzil)
depoda_kalan     = depo - yol_yakiti
gidis_donus      = yol_maliyeti * 2
kisi_basi        = gidis_donus / kisi

sure_saat    = yol / hiz
mola_sayisi  = int(sure_saat / 3)
mola_dakika  = mola_sayisi * 15
molali_sure  = sure_saat + mola_dakika / 60
varis_dt     = datetime.combine(datetime.today(), cikis) + timedelta(hours=molali_sure)
varis_str    = varis_dt.strftime("%H:%M")

def fmt_sure(h_float):
    h = int(h_float)
    m = int(round((h_float - h) * 60))
    if m == 60: h += 1; m = 0
    return f"{h}s {m:02d}dk" if h else f"{m}dk"

sure_str   = fmt_sure(molali_sure)
surus_str  = fmt_sure(sure_saat)
mola_str   = f"{mola_dakika}dk" + (f" ({mola_sayisi} mola)" if mola_sayisi > 0 else " (mola yok)")

aylik_gider  = aylik_km * km_maliyet
yillik_gider = aylik_gider * 12
yakit_yeterli = yol <= tam_depo_menzil

def hesapla(km, fp, tuk):
    miktar = km * tuk / 100
    return miktar * fp, miktar

bnz_m, bnz_y = hesapla(yol, fiyat, tuketim)
diz_m, diz_y = hesapla(yol, dizel_fiyat, dizel_tuketim)
lpg_m, lpg_y = hesapla(yol, lpg_fiyat, lpg_tuketim)
ev_enerji     = yol * ev_tuketim / 100
ev_m          = ev_enerji * ev_fiyat
ev_menzil     = (ev_batarya / ev_tuketim) * 100 if ev_tuketim > 0 else 0
ev_tas        = bnz_m - ev_m
ev_aylik_tas  = (aylik_km * ev_tas / yol) if yol > 0 else 0
ev_yillik_tas = ev_aylik_tas * 12
ev_oran       = bnz_m / ev_m if ev_m > 0 else 0

# ── Sayfa ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🚗 Araç Yol Bilgisayarı</div>', unsafe_allow_html=True)
route_label = " → ".join(f"{il}/{ilce}" for il, ilce in st.session_state.duraks)
st.markdown(f'<div class="page-sub">📍 {route_label} &nbsp;·&nbsp; {total_yol} km</div>', unsafe_allow_html=True)

# Yakıt Durumu
if yakit_yeterli:
    st.markdown(f"""<div class="status-ok">
      <div class="status-icon">✅</div>
      <div><div>YAKIT YETERLİ</div>
      <div class="status-detail">Menzil {tam_depo_menzil:.0f} km · Yol {yol} km · Depoda {depoda_kalan:.1f} L kalır</div>
      </div></div>""", unsafe_allow_html=True)
else:
    st.markdown(f"""<div class="status-fail">
      <div class="status-icon">⛽</div>
      <div><div>YAKIT YETMEZ — {gerekli_depo} depo gerekli</div>
      <div class="status-detail">Menzil {tam_depo_menzil:.0f} km · Yol {yol} km · {abs(depoda_kalan):.1f} L eksik</div>
      </div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Metrik kartları
c1,c2,c3,c4 = st.columns(4)
c1.metric("Yol Maliyeti",    f"{yol_maliyeti:,.0f} ₺", f"{km_maliyet:.2f} ₺/km",    delta_color="off")
c2.metric("Gidiş-Dönüş",    f"{gidis_donus:,.0f} ₺")
c3.metric("Kişi Başı (G/D)", f"{kisi_basi:,.0f} ₺",   f"{kisi} kişi",               delta_color="off")
c4.metric("100km Maliyeti",  f"{km100_maliyet:,.0f} ₺")

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

c5,c6,c7,c8 = st.columns(4)
c5.metric("Tam Depo Menzili",   f"{tam_depo_menzil:.0f} km")
c6.metric("Tam Depo Maliyeti",  f"{tam_depo_maliyet:,.0f} ₺")
c7.metric("Tahmini Varış",      varis_str, f"Çıkış: {cikis.strftime("%H:%M")}", delta_color="off")
c8.metric("Aylık Yakıt Gideri", f"{aylik_gider:,.0f} ₺", f"Yıllık {yillik_gider:,.0f} ₺", delta_color="off")

# ── Süre Bilgileri ──────────────────────────────────────────────────────────
st.markdown('<div class="section-header">⏱ Süre & Varış Bilgileri</div>', unsafe_allow_html=True)

t1, t2, t3, t4 = st.columns(4)
t1.metric("Sürüş Süresi",  surus_str,  f"{yol} km / {hiz} km/s",             delta_color="off")
t2.metric("Mola Süresi",   mola_str,   "Her 3 saatte 1 × 15dk",              delta_color="off")
t3.metric("Toplam Süre",   sure_str,   f"Sürüş + mola",                      delta_color="off")
t4.metric("Tahmini Varış", varis_str,  f"Çıkış: {cikis.strftime('%H:%M')}", delta_color="off")

# Güzergah detay tablosu (çok duraklıysa)
if len(segments) > 1:
    st.markdown('<div class="section-header">📍 Güzergah Detayı</div>', unsafe_allow_html=True)

    def seg_sure(km):
        h = km / hiz
        mol = int(h / 3) * 15
        return fmt_sure(h + mol / 60)

    seg_df = pd.DataFrame(
        [(f"{a} → {b}", f"{km} km", f"{km * km_maliyet:,.0f} ₺",
          fmt_sure(km / hiz), f"{int(km/hiz/2)*15}dk", seg_sure(km))
         for a, b, km in segments],
        columns=["Segment", "Mesafe", "Yakıt Maliyeti", "Sürüş Süresi", "Mola", "Toplam Süre"]
    )
    st.dataframe(seg_df, hide_index=True, use_container_width=True)

# Yakıt karşılaştırması
st.markdown('<div class="section-header">⛽ Yakıt Tipi Karşılaştırması</div>', unsafe_allow_html=True)

def fmt_tas(v):
    if v == 0: return "—"
    return f"{'+'if v>0 else ''}{v:,.0f} ₺"

comp = pd.DataFrame([
    {"Yakıt Tipi":"Benzin",            "Birim Fiyat":f"{fiyat:.2f} ₺/L",      "100km Tüketim":f"{tuketim:.1f} L",      "Yol Yakıt/Enerji":f"{bnz_y:.1f} L",    "Yol Maliyeti (₺)":f"{bnz_m:,.0f}",  "G/D Toplam (₺)":f"{bnz_m*2:,.0f}",  "100km Mal. (₺)":f"{fiyat*tuketim:.2f}",       "Benzinden Tasarruf":"—"},
    {"Yakıt Tipi":"Dizel",             "Birim Fiyat":f"{dizel_fiyat:.2f} ₺/L", "100km Tüketim":f"{dizel_tuketim:.1f} L","Yol Yakıt/Enerji":f"{diz_y:.1f} L",    "Yol Maliyeti (₺)":f"{diz_m:,.0f}",  "G/D Toplam (₺)":f"{diz_m*2:,.0f}",  "100km Mal. (₺)":f"{dizel_fiyat*dizel_tuketim:.2f}", "Benzinden Tasarruf":fmt_tas(bnz_m-diz_m)},
    {"Yakıt Tipi":"LPG",               "Birim Fiyat":f"{lpg_fiyat:.2f} ₺/L",   "100km Tüketim":f"{lpg_tuketim:.1f} L",  "Yol Yakıt/Enerji":f"{lpg_y:.1f} L",    "Yol Maliyeti (₺)":f"{lpg_m:,.0f}",  "G/D Toplam (₺)":f"{lpg_m*2:,.0f}",  "100km Mal. (₺)":f"{lpg_fiyat*lpg_tuketim:.2f}",    "Benzinden Tasarruf":fmt_tas(bnz_m-lpg_m)},
    {"Yakıt Tipi":"⚡ Elektrikli (EV)","Birim Fiyat":f"{ev_fiyat:.2f} ₺/kWh",  "100km Tüketim":f"{ev_tuketim:.1f} kWh", "Yol Yakıt/Enerji":f"{ev_enerji:.1f} kWh","Yol Maliyeti (₺)":f"{ev_m:,.0f}",   "G/D Toplam (₺)":f"{ev_m*2:,.0f}",   "100km Mal. (₺)":f"{ev_fiyat*ev_tuketim:.2f}",      "Benzinden Tasarruf":fmt_tas(bnz_m-ev_m)},
])
st.dataframe(comp, hide_index=True, use_container_width=True)

# Grafik
st.markdown('<div class="section-header">📊 Maliyet Karşılaştırma Grafiği</div>', unsafe_allow_html=True)
fig = go.Figure(go.Bar(
    x=["Benzin","Dizel","LPG","⚡ EV"],
    y=[bnz_m, diz_m, lpg_m, ev_m],
    marker_color=["#ED7D31","#2E75B6","#70AD47","#7030A0"],
    text=[f"{v:,.0f} ₺" for v in [bnz_m, diz_m, lpg_m, ev_m]],
    textposition="outside", textfont=dict(size=13, family="Inter"),
))
fig.add_hline(y=bnz_m, line_dash="dot", line_color="#ED7D31",
              annotation_text=f"Benzin: {bnz_m:,.0f} ₺",
              annotation_position="top right",
              annotation_font=dict(color="#ED7D31", size=11))
fig.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    yaxis=dict(title=dict(text="Yol Maliyeti (₺)", font=dict(size=12)), gridcolor="#F0F0F0"),
    xaxis=dict(tickfont=dict(size=13)),
    margin=dict(t=20, b=20, l=20, r=20), height=320, showlegend=False,
)
st.plotly_chart(fig, use_container_width=True)

# EV tasarruf
st.markdown('<div class="section-header">⚡ Elektrikli Araç — Tasarruf Analizi</div>', unsafe_allow_html=True)
e1,e2,e3,e4 = st.columns(4)
e1.metric("Bu Seyahat Tasarrufu", f"{'+'if ev_tas>=0 else ''}{ev_tas:,.0f} ₺",     "Benzin'e kıyasla",  delta_color="off")
e2.metric("Aylık Tasarruf",       f"{'+'if ev_aylik_tas>=0 else ''}{ev_aylik_tas:,.0f} ₺", f"{aylik_km:,} km/ay", delta_color="off")
e3.metric("Yıllık Tasarruf",      f"{'+'if ev_yillik_tas>=0 else ''}{ev_yillik_tas:,.0f} ₺")
e4.metric("Benzin / EV Oranı",    f"{ev_oran:.2f}×", "EV daha ucuz" if ev_oran>1 else "EV daha pahalı", delta_color="off")

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
e5, e6, _ = st.columns([1,1,2])
ev_yeterli_str = "✅ Şarj yeterli" if yol <= ev_menzil else f"⚡ {math.ceil(yol/ev_menzil)} şarj gerekli"
e5.metric("EV Tam Şarj Menzili", f"{ev_menzil:.0f} km",  f"{ev_batarya:.0f} kWh batarya", delta_color="off")
e6.metric("Bu Yol İçin",         ev_yeterli_str,          f"{yol} km yol",                 delta_color="off")

st.markdown("<br>", unsafe_allow_html=True)
st.caption("📐 Mesafeler koordinat tabanlı tahminidir (haversine × 1.30 yol katsayısı). Gerçek mesafe için navigasyon uygulaması kullanın.")
st.caption("© Yakıt Hesabı | Streamlit + Python | 2026 Enes Özkan")