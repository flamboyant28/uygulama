import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Hava Durumu", page_icon="🌤", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
html,body,[class*="css"]{ font-family:'Outfit',sans-serif; }
.gun-karti{
    background:linear-gradient(135deg,#1e3a5f,#0f2a4a);
    border:1px solid #2a4a6a;border-radius:14px;
    padding:14px 10px;text-align:center;transition:transform .2s;
}
.gun-karti:hover{transform:translateY(-2px);}
.gun-adi{font-size:.78rem;color:#7ab3d4;font-weight:700;}
.gun-ikon{font-size:2rem;margin:6px 0;}
.gun-max{font-size:1.3rem;font-weight:800;color:#ff7043;}
.gun-min{font-size:.95rem;font-weight:500;color:#64b5f6;}
.gun-alt{font-size:.7rem;color:#90caf9;margin-top:4px;}
.anlik-kart{
    background:linear-gradient(135deg,#0d47a1,#1565c0,#1976d2);
    border-radius:20px;padding:24px 28px;color:white;
}
.m-kutu{background:rgba(255,255,255,.15);border-radius:10px;padding:10px 14px;margin-top:10px;}
.m-lbl{font-size:.68rem;opacity:.7;letter-spacing:.06em;text-transform:uppercase;}
.m-val{font-size:1.05rem;font-weight:700;}
</style>
""", unsafe_allow_html=True)

# ── Yardımcı ──────────────────────────────────────────────────────────────────
def safe(val, dec=1):
    """None güvenli round"""
    if val is None: return None
    try: return round(float(val), dec)
    except: return None

def sf(val, dec=1, suffix=""):
    """Gösterim için None güvenli format"""
    v = safe(val, dec)
    if v is None: return "—"
    return f"{v}{suffix}"

HAVA_KODU = {
    0: ("☀️","Açık Gökyüzü"),
    1: ("🌤","Az Bulutlu"),
    2: ("⛅","Parçalı Bulutlu"),
    3: ("☁️","Kapalı"),
    45:("🌫","Sisli"),
    48:("🌫","Buz Sisi"),
    51:("🌦","Hafif Çise"),
    53:("🌦","Orta Çise"),
    55:("🌧","Yoğun Çise"),
    56:("🌨","Hafif Donlu Çise"),
    57:("🌨","Yoğun Donlu Çise"),
    61:("🌧","Hafif Yağmur"),
    63:("🌧","Orta Yağmur"),
    65:("🌧","Şiddetli Yağmur"),
    66:("🌨","Hafif Donlu Yağmur"),
    67:("🌨","Şiddetli Donlu Yağmur"),
    71:("❄️","Hafif Kar"),
    73:("❄️","Kar"),
    75:("❄️","Yoğun Kar"),
    77:("❄️","Kar Taneleri"),
    80:("🌦","Hafif Sağanak"),
    81:("🌦","Orta Sağanak"),
    82:("⛈","Şiddetli Sağanak"),
    85:("🌨","Hafif Kar Sağanağı"),
    86:("🌨","Yoğun Kar Sağanağı"),
    95:("⛈","Gök Gürültülü Fırtına"),
    96:("⛈","Gök Gürültülü Dolu"),
    99:("⛈","Şiddetli Dolu Fırtınası"),
}
def hk(code):
    try: return HAVA_KODU.get(int(float(code)), ("🌡","Bilinmiyor"))
    except: return ("🌡","Bilinmiyor")

SICAKLIK_YORUMU = [
    (-100,-35,"🧊 Donmuş Dünya",     "midnightblue",  "white"),
    (-35, -30,"🥶 Felaket Soğuk",    "navy",           "white"),
    (-30, -27,"❄️ Kutup Soğuğu",     "darkblue",       "white"),
    (-27, -24,"❄️ Sert Buzlanma",    "blue",           "white"),
    (-24, -21,"🧥 Yoğun Üşüme",      "deepskyblue",    "black"),
    (-21, -18,"🧥 Dondurucu Hava",   "lightskyblue",   "black"),
    (-18, -15,"🧤 Eldiven Zorunlu",  "skyblue",        "black"),
    (-15, -12,"🧣 Soğuğa Dikkat",    "dodgerblue",     "white"),
    (-12,  -9,"🌀 Soğuk Rüzgar",     "cadetblue",      "white"),
    ( -9,  -6,"🧊 Hafif Donma",       "lightblue",      "black"),
    ( -6,  -3,"🌫️ Üşütücü Soğuk",   "paleturquoise",  "black"),
    ( -3,   0,"🧊 Soğuk Katlanılır",  "aquamarine",     "black"),
    (  0,   3,"🍃 Ilık-Soğuk Arası", "mediumaquamarine","black"),
    (  3,   6,"🌿 Bahar Serinliği",  "mediumseagreen", "white"),
    (  6,   9,"🌤️ Hafif Serin",      "seagreen",       "white"),
    (  9,  12,"🌞 Ilık Hava",         "green",          "white"),
    ( 12,  15,"🟢 Konforlu (Serin)",  "limegreen",      "black"),
    ( 15,  18,"🟢 Konforlu",          "lawngreen",      "black"),
    ( 18,  21,"🟢 Konforlu (Sıcakça)","chartreuse",     "black"),
    ( 21,  24,"🌼 Sıcakça",           "greenyellow",    "black"),
    ( 24,  27,"🟡 Ilık-Sıcak",        "yellowgreen",    "black"),
    ( 27,  30,"🟡 Sıcak",             "yellow",         "black"),
    ( 30,  33,"🟠 Çok Sıcak",         "gold",           "black"),
    ( 33,  36,"🔥 Bunaltıcı",          "orange",         "black"),
    ( 36,  39,"🔴 Aşırı Sıcak",       "darkorange",     "white"),
    ( 39,  42,"☀️ Ciddi Risk",         "orangered",      "white"),
    ( 42,  45,"☠️ Tehlikeli",          "red",            "white"),
    ( 45,  48,"🌋 Yaşamsal Risk",      "firebrick",      "white"),
    ( 48,  52,"💀 Ölümcül Isı",        "darkred",        "white"),
    ( 52, 100,"🚫 Elverişsiz",         "black",          "white"),
]

RUZGAR_YORUMU = [
    (  0,   1,"🌫️ Rüzgar yok, hava durgun"),
    (  1,   3,"🪁 Hava çok hafif esiyor"),
    (  3,   5,"🌬️ Hafif esinti hissedilir"),
    (  5,   8,"🍃 Serinlik sağlayan rüzgar"),
    (  8,  12,"🌿 Hoş bir esinti"),
    ( 12,  16,"🌬️ Belirgin rüzgar, rahatlatıcı"),
    ( 16,  20,"🍃 Güçlü ama hoş rüzgar"),
    ( 20,  25,"🌬️ Sıcak havayı bastıran rüzgar"),
    ( 25,  30,"🌀 Serinletici kuvvetli rüzgar"),
    ( 30,  35,"🌪️ Sınırda rahatsız edici rüzgar"),
    ( 35,  40,"🌪️ Sert ve rahatsız edici rüzgar"),
    ( 40,  50,"🌪️ Tehlikeli seviyede rüzgar"),
    ( 50,  60,"🌪️ Fırtınamsı etki yaratır"),
    ( 60,  80,"🌪️ Dış ortamda bulunmak zor"),
    ( 80, 100,"🌪️ Uçuşan cisimlere dikkat"),
    (100, 120,"🌪️ Fırtına şiddetinde rüzgar"),
    (120, 150,"🌪️ Kasırga benzeri etki"),
    (150, 200,"🌪️ Aşırı tehlikeli rüzgar!"),
    (200, 300,"🌪️ Yapısal hasar riski!"),
    (300,1000,"💀 Felaket düzeyinde rüzgar!"),
]

def sicaklik_yorum(t):
    try:
        t = float(t)
        for lo,hi,yorum,_bg,_fg in SICAKLIK_YORUMU:
            if lo <= t < hi: return yorum
        return "—"
    except: return "—"

def sicaklik_css(t):
    """DataFrame hücresine uygulanacak CSS string'i döndürür"""
    try:
        t = float(t)
        for lo,hi,_y,bg,fg in SICAKLIK_YORUMU:
            if lo <= t < hi:
                return f"background-color:{bg};color:{fg}"
        return ""
    except: return ""

def ruzgar_yorum(w):
    try:
        w = float(w)
        for lo,hi,yorum in RUZGAR_YORUMU:
            if lo <= w < hi: return yorum
        return "—"
    except: return "—"

RYON = ["K","KKD","KD","DKD","D","DGD","GD","GGD","G","GGB","GB","BGB","B","BKB","KB","KKB"]
def ryon(deg):
    try: return RYON[round(float(deg)/22.5)%16]
    except: return "—"

def uv_yorum(uv):
    try:
        u = float(uv)
        if u < 3:  return "🟢 Düşük"
        if u < 6:  return "🟡 Orta"
        if u < 8:  return "🟠 Yüksek"
        if u < 11: return "🔴 Çok Yüksek"
        return "🟣 Aşırı"
    except: return "—"

def cape_yorum(cape):
    try:
        c = float(cape)
        if c < 300:  return "Kararlı"
        if c < 1000: return "Hafif Kararsız"
        if c < 2500: return "Orta Kararsız"
        return "⛈ Çok Kararsız"
    except: return "—"

# ── API ───────────────────────────────────────────────────────────────────────

# Tüm mevcut saatlik değişkenler
HOURLY_VARS = [
    # Sıcaklık
    "temperature_2m","apparent_temperature",
    "dewpoint_2m","vapor_pressure_deficit",
    # Nem & Yağış
    "relativehumidity_2m",
    "precipitation","rain","showers","snowfall","snow_depth",
    "precipitation_probability",
    # Hava Durumu
    "weathercode","is_day",
    # Basınç & Bulut
    "pressure_msl","surface_pressure",
    "cloudcover","cloudcover_low","cloudcover_mid","cloudcover_high",
    # Görüş
    "visibility",
    # Rüzgar (10m)
    "windspeed_10m","winddirection_10m","windgusts_10m",
    # Rüzgar (üst katmanlar)
    "windspeed_80m","winddirection_80m",
    "windspeed_120m","winddirection_120m",
    "windspeed_180m","winddirection_180m",
    # Işınım
    "shortwave_radiation","direct_radiation",
    "diffuse_radiation","direct_normal_irradiance",
    "uv_index","uv_index_clear_sky",
    # Atmosfer kararlılığı
    "cape","lifted_index","freezinglevel_height",
    # Buharlaşma
    "evapotranspiration","et0_fao_evapotranspiration",
    # Toprak sıcaklığı
    "soil_temperature_0cm","soil_temperature_6cm",
    "soil_temperature_18cm","soil_temperature_54cm",
    # Toprak nemi
    "soil_moisture_0_1cm","soil_moisture_1_3cm",
    "soil_moisture_3_9cm","soil_moisture_9_27cm","soil_moisture_27_81cm",
]

DAILY_VARS = [
    "weathercode",
    "temperature_2m_max","temperature_2m_min",
    "apparent_temperature_max","apparent_temperature_min",
    "precipitation_sum","rain_sum","showers_sum","snowfall_sum",
    "precipitation_hours","precipitation_probability_max",
    "windspeed_10m_max","windgusts_10m_max","winddirection_10m_dominant",
    "shortwave_radiation_sum","uv_index_max","uv_index_clear_sky_max",
    "sunshine_duration","et0_fao_evapotranspiration",
    "sunrise","sunset",
]

@st.cache_data(ttl=3600)
def sehir_ara(q):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
            params={"q":q,"format":"json","limit":5},
            headers={"User-Agent":"hava-v4/1.0"}, timeout=10)
        return r.json()
    except Exception as e:
        st.error(f"Şehir arama hatası: {e}"); return []

@st.cache_data(ttl=1800)
def hava_cek(lat, lon, forecast_days=16):
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude":        lat,
            "longitude":       lon,
            "current_weather": "true",
            "hourly":          ",".join(HOURLY_VARS),
            "daily":           ",".join(DAILY_VARS),
            "timezone":        "auto",
            "forecast_days":   forecast_days,
            "wind_speed_unit": "kmh",
        }, timeout=25)
        d = r.json()
        if "error" in d:
            st.error(f"API hatası: {d.get('reason','Bilinmiyor')}")
            return None
        return d
    except Exception as e:
        st.error(f"Open-Meteo hatası: {e}"); return None

def h_val(h, key, i, dec=1):
    """Saatlik veri güvenli okuma"""
    try:
        v = h.get(key, [])
        return safe(v[i] if i < len(v) else None, dec)
    except: return None

def d_val(d, key, i, dec=1):
    """Günlük veri güvenli okuma"""
    try:
        v = d.get(key, [])
        return safe(v[i] if i < len(v) else None, dec)
    except: return None

# ── Session State ─────────────────────────────────────────────────────────────
for k,v in [("konum1",None),("konum2",None),
             ("tetik1",False),("tetik2",False),
             ("ara1",""),("ara2","")]:
    if k not in st.session_state: st.session_state[k] = v

# ── Başlık & Sidebar ──────────────────────────────────────────────────────────
st.markdown("# 🌤 Hava Durumu Dashboard")
st.caption("Open-Meteo API · Tüm mevcut parametreler · 16 gün / 384 saat")

with st.sidebar:
    st.markdown("### ⚙️ Ayarlar")
    forecast_days = st.slider("Tahmin Günü", 1, 16, 16)
    st.divider()
    st.markdown("**Hızlı Şehirler**")
    for s in ["İstanbul","Ankara","İzmir","Antalya","Trabzon",
              "London","New York","Paris","Tokyo","Dubai","Yakutsk","Reykjavik"]:
        if st.button(s, key=f"hz_{s}", use_container_width=True):
            st.session_state.ara1 = s
            st.session_state.tetik1 = True
            st.session_state.konum1 = None
            st.rerun()

# ── Arama ─────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([3,3,1])
with c1: girdi1 = st.text_input("Şehir 1", value=st.session_state.ara1,
                                 placeholder="İstanbul, Yakutsk...", key="g1")
with c2: girdi2 = st.text_input("Şehir 2 (Karşılaştırma)",
                                 value=st.session_state.ara2,
                                 placeholder="London, Reykjavik...", key="g2")
with c3:
    if st.button("🔍 Ara", type="primary", use_container_width=True):
        if girdi1: st.session_state.ara1=girdi1; st.session_state.tetik1=True; st.session_state.konum1=None
        if girdi2: st.session_state.ara2=girdi2; st.session_state.tetik2=True; st.session_state.konum2=None
        st.rerun()

for ara_k, tetik_k, konum_k in [("ara1","tetik1","konum1"),("ara2","tetik2","konum2")]:
    if st.session_state[tetik_k] and st.session_state[ara_k]:
        with st.spinner(f"{st.session_state[ara_k]} aranıyor..."):
            sonuclar = sehir_ara(st.session_state[ara_k])
        if sonuclar:
            s = sonuclar[0]
            st.session_state[konum_k] = (
                float(s["lat"]), float(s["lon"]),
                s["display_name"].split(",")[0]
            )
        else:
            st.error(f"'{st.session_state[ara_k]}' bulunamadı.")
        st.session_state[tetik_k] = False

if not st.session_state.konum1:
    st.info("👆 Şehir ara veya sol panelden hızlı seçim yap.")
    st.stop()

# ── Veri Çek ──────────────────────────────────────────────────────────────────
lat1, lon1, sehir1 = st.session_state.konum1
with st.spinner(f"{sehir1} verisi alınıyor ({forecast_days} gün)..."):
    v1 = hava_cek(lat1, lon1, forecast_days)
if not v1: st.stop()

h1  = v1["hourly"]
d1  = v1["daily"]
cur = v1["current_weather"]
toplam_saat = len(h1.get("time", []))

v2 = None; sehir2 = ""
if st.session_state.konum2:
    lat2, lon2, sehir2 = st.session_state.konum2
    with st.spinner(f"{sehir2} verisi alınıyor..."):
        v2 = hava_cek(lat2, lon2, forecast_days)

# ── Sekmeler ──────────────────────────────────────────────────────────────────
tab_listesi = ["🌡 Anlık","📅 Günlük","⏰ Temel","💨 Rüzgar",
               "🌱 Toprak","🌪 Atmosfer","📆 16 Günlük","📈 Grafikler"]
if v2: tab_listesi.append("🔄 Karşılaştırma")
tabs = st.tabs(tab_listesi)
(tab_anlik, tab_gunluk, tab_temel, tab_ruzgar,
 tab_toprak, tab_atmos, tab_16gun, tab_grafik) = tabs[:8]
tab_kars = tabs[8] if len(tabs) > 8 else None

# ── Renk fonksiyonları ────────────────────────────────────────────────────────
def rs(val):
    try:
        t = float(val)
        if t < 0:   return "background-color:#bbdefb;color:#0d47a1"
        if t < 10:  return "background-color:#e0f7fa"
        if t < 20:  return "background-color:#e8f5e9"
        if t < 30:  return "background-color:#fff9c4"
        return "background-color:#ffccbc"
    except: return ""

def ry(val):
    try:
        y = float(val)
        if y <= 0:  return ""
        if y < 2:   return "background-color:#e3f2fd"
        if y < 10:  return "background-color:#90caf9"
        return "background-color:#42a5f5;color:white"
    except: return ""

def rn(val):
    try:
        n = float(val)
        if n < 40:  return "background-color:#fff9c4"
        if n < 60:  return "background-color:#e8f5e9"
        if n < 80:  return "background-color:#e3f2fd"
        return "background-color:#bbdefb"
    except: return ""

def rb(val):
    try:
        b = float(val)
        if b < 25:  return ""
        if b < 50:  return "background-color:#f5f5f5"
        if b < 75:  return "background-color:#eeeeee"
        return "background-color:#e0e0e0"
    except: return ""

# Gün filtresi (saatlik sekmeler için ortak)
gunler_lst = sorted(set(t[:10] for t in h1.get("time",[])))
gun_sec_lbls = ["Tümü"] + [
    datetime.strptime(g,"%Y-%m-%d").strftime("%d %B %Y (%A)")
    for g in gunler_lst
]

def gun_filtre(tab_key):
    sec = st.selectbox("📅 Gün filtresi", range(len(gun_sec_lbls)),
                       format_func=lambda i: gun_sec_lbls[i], key=f"gf_{tab_key}")
    if sec == 0:
        return list(range(len(h1["time"])))
    secili = gunler_lst[sec-1]
    return [i for i,t in enumerate(h1["time"]) if t.startswith(secili)]

# ══════════════════════════════════════════════════════════════
# 🌡 ANLIK
# ══════════════════════════════════════════════════════════════
with tab_anlik:
    ikon0, acik0 = hk(cur.get("weathercode"))
    gd = d1.get("sunrise",[""])[0][11:16] if d1.get("sunrise") else "—"
    gb = d1.get("sunset",[""])[0][11:16]  if d1.get("sunset")  else "—"

    ca, cb = st.columns([1.2, 1])
    with ca:
        st.markdown(f"""
        <div class="anlik-kart">
          <div style="font-size:.82rem;opacity:.6">{datetime.now().strftime('%d %B %Y  %H:%M')}</div>
          <div style="font-size:1.3rem;font-weight:700;margin:4px 0">📍 {sehir1}</div>
          <div style="display:flex;align-items:center;gap:20px;margin:14px 0">
            <div style="font-size:3.5rem">{ikon0}</div>
            <div>
              <div style="font-size:4rem;font-weight:800;line-height:1">{sf(cur.get('temperature'),0)}°C</div>
              <div style="opacity:.75;font-style:italic">{acik0}</div>
              <div style="font-size:.82rem;opacity:.85;margin-top:4px">{sicaklik_yorum(cur.get('temperature'))}</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
            <div class="m-kutu"><div class="m-lbl">💨 Rüzgar</div>
              <div class="m-val">{sf(cur.get('windspeed'),0)} km/s {ryon(cur.get('winddirection'))}</div>
              <div style="font-size:.72rem;opacity:.8;margin-top:2px">{ruzgar_yorum(cur.get('windspeed'))}</div></div>
            <div class="m-kutu"><div class="m-lbl">🌡 Max / Min</div>
              <div class="m-val">{sf(d_val(d1,'temperature_2m_max',0),0)}° / {sf(d_val(d1,'temperature_2m_min',0),0)}°</div></div>
            <div class="m-kutu"><div class="m-lbl">💧 Yağış (bugün)</div>
              <div class="m-val">{sf(d_val(d1,'precipitation_sum',0))} mm</div></div>
            <div class="m-kutu"><div class="m-lbl">☀️ UV Max</div>
              <div class="m-val">{uv_yorum(d_val(d1,'uv_index_max',0))}</div></div>
            <div class="m-kutu"><div class="m-lbl">🌅 Gün Doğumu</div>
              <div class="m-val">{gd}</div></div>
            <div class="m-kutu"><div class="m-lbl">🌇 Gün Batımı</div>
              <div class="m-val">{gb}</div></div>
          </div>
        </div>""", unsafe_allow_html=True)

    with cb:
        bugun = d1.get("time",[""])[0]
        idx_b = [i for i,t in enumerate(h1.get("time",[])) if t.startswith(bugun)]
        if idx_b:
            fig_b = go.Figure()
            fig_b.add_trace(go.Scatter(
                x=[h1["time"][i][11:16] for i in idx_b],
                y=[h_val(h1,"temperature_2m",i) for i in idx_b],
                name="Sıcaklık", mode="lines+markers",
                line=dict(color="#ff7043",width=2.5),
                fill="tozeroy", fillcolor="rgba(255,112,67,.08)"))
            fig_b.add_trace(go.Scatter(
                x=[h1["time"][i][11:16] for i in idx_b],
                y=[h_val(h1,"apparent_temperature",i) for i in idx_b],
                name="Hissedilen", line=dict(color="#ffa726",width=2,dash="dot")))
            fig_b.update_layout(title="Bugün Saatlik Sıcaklık", height=240,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0), hovermode="x unified",
                xaxis=dict(showgrid=False,nticks=8),
                yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                legend=dict(orientation="h",y=1.15))
            st.plotly_chart(fig_b, use_container_width=True)

        m1,m2,m3 = st.columns(3)
        mid = idx_b[len(idx_b)//2] if idx_b else 0
        with m1: st.metric("💧 Nem", sf(h_val(h1,"relativehumidity_2m",mid,0),0,"%"))
        with m2: st.metric("🌬 Basınç", sf(h_val(h1,"pressure_msl",mid,0),0," hPa"))
        with m3: st.metric("💨 Gusto", sf(h_val(h1,"windgusts_10m",mid,0),0," km/s"))

# ══════════════════════════════════════════════════════════════
# 📅 GÜNLÜK
# ══════════════════════════════════════════════════════════════
with tab_gunluk:
    st.markdown("### 📅 7 Günlük Tahmin")
    cols7 = st.columns(7)
    for i, col in enumerate(cols7):
        if i >= len(d1.get("time",[])): break
        tarih = datetime.strptime(d1["time"][i],"%Y-%m-%d")
        ikon_g, acik_g = hk(d_val(d1,"weathercode",i,0))
        with col:
            st.markdown(f"""
            <div class="gun-karti">
              <div class="gun-adi">{"Bugün" if i==0 else tarih.strftime("%a")}<br>{tarih.strftime("%d/%m")}</div>
              <div class="gun-ikon">{ikon_g}</div>
              <div class="gun-max">{sf(d_val(d1,'temperature_2m_max',i),0)}°</div>
              <div class="gun-min">{sf(d_val(d1,'temperature_2m_min',i),0)}°</div>
              <div class="gun-alt">💧{sf(d_val(d1,'precipitation_sum',i))}mm
              %{sf(d_val(d1,'precipitation_probability_max',i),0)}</div>
              <div class="gun-alt">💨{sf(d_val(d1,'windspeed_10m_max',i),0)}km/s
              UV:{sf(d_val(d1,'uv_index_max',i),0)}</div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ⏰ TEMEL SAATLİK
# ══════════════════════════════════════════════════════════════
with tab_temel:
    st.markdown("### ⏰ Temel Saatlik Veriler")
    idx = gun_filtre("temel")
    rows = []
    for i in idx:
        dt = datetime.strptime(h1["time"][i],"%Y-%m-%dT%H:%M")
        ikon_s, acik_s = hk(h_val(h1,"weathercode",i,0))
        rows.append({
            "Tarih":        dt.strftime("%d.%m"),
            "Saat":         dt.strftime("%H:%M"),
            "G/G":          "☀️" if h_val(h1,"is_day",i,0) else "🌙",
            "Durum":        f"{ikon_s} {acik_s}",
            "Sıcaklık °C":  h_val(h1,"temperature_2m",i),
            "Sıcaklık Yorum": sicaklik_yorum(h_val(h1,"temperature_2m",i)),
            "Hissedilen":   h_val(h1,"apparent_temperature",i),
            "Hiss. Yorum":  sicaklik_yorum(h_val(h1,"apparent_temperature",i)),
            "Nem %":        h_val(h1,"relativehumidity_2m",i,0),
            "Çiy Noktası":  h_val(h1,"dewpoint_2m",i),
            "Basınç hPa":   h_val(h1,"pressure_msl",i,0),
            "Yüzey Bas.":   h_val(h1,"surface_pressure",i,0),
            "Bulut %":      h_val(h1,"cloudcover",i,0),
            "Bulut Alçak":  h_val(h1,"cloudcover_low",i,0),
            "Bulut Orta":   h_val(h1,"cloudcover_mid",i,0),
            "Bulut Yüksek": h_val(h1,"cloudcover_high",i,0),
            "Görüş km":     h_val(h1,"visibility",i) and round(h_val(h1,"visibility",i)/1000,1),
            "Yağış mm":     h_val(h1,"precipitation",i),
            "Yağmur mm":    h_val(h1,"rain",i),
            "Sağanak mm":   h_val(h1,"showers",i),
            "Kar cm":       h_val(h1,"snowfall",i),
            "Kar Derinlik": h_val(h1,"snow_depth",i),
            "Yağış %":      h_val(h1,"precipitation_probability",i,0),
            "UV":           h_val(h1,"uv_index",i),
            "UV Açık Göky": h_val(h1,"uv_index_clear_sky",i),
        })
    df = pd.DataFrame(rows)
    styled = df.style\
        .map(sicaklik_css, subset=["Sıcaklık °C","Hissedilen","Çiy Noktası"])\
        .map(ry, subset=["Yağış mm","Yağmur mm","Sağanak mm"])\
        .map(rn, subset=["Nem %"])\
        .map(rb, subset=["Bulut %"])\
        .format(precision=1, na_rep="—")
    st.caption(f"{len(rows)} veri noktası · {toplam_saat} saat toplam")
    st.dataframe(styled, use_container_width=True, height=520)

# ══════════════════════════════════════════════════════════════
# 💨 RÜZGAR SAATLİK
# ══════════════════════════════════════════════════════════════
with tab_ruzgar:
    st.markdown("### 💨 Rüzgar Saatlik Veriler (Tüm Yükseklikler)")
    idx = gun_filtre("ruzgar")
    rows = []
    for i in idx:
        dt = datetime.strptime(h1["time"][i],"%Y-%m-%dT%H:%M")
        rows.append({
            "Tarih":        dt.strftime("%d.%m"),
            "Saat":         dt.strftime("%H:%M"),
            "10m km/s":     h_val(h1,"windspeed_10m",i),
            "10m Yorum":    ruzgar_yorum(h_val(h1,"windspeed_10m",i)),
            "10m Yön":      ryon(h_val(h1,"winddirection_10m",i,0)),
            "10m Gusto":    h_val(h1,"windgusts_10m",i),
            "Gusto Yorum":  ruzgar_yorum(h_val(h1,"windgusts_10m",i)),
            "80m km/s":     h_val(h1,"windspeed_80m",i),
            "80m Yön":      ryon(h_val(h1,"winddirection_80m",i,0)),
            "120m km/s":    h_val(h1,"windspeed_120m",i),
            "120m Yön":     ryon(h_val(h1,"winddirection_120m",i,0)),
            "180m km/s":    h_val(h1,"windspeed_180m",i),
            "180m Yön":     ryon(h_val(h1,"winddirection_180m",i,0)),
        })
    df_r = pd.DataFrame(rows)

    def rw(val):
        try:
            w = float(val)
            if w < 10:  return ""
            if w < 30:  return "background-color:#e3f2fd"
            if w < 60:  return "background-color:#90caf9"
            return "background-color:#42a5f5;color:white"
        except: return ""

    styled_r = df_r.style\
        .map(rw, subset=["10m km/s","10m Gusto","80m km/s","120m km/s","180m km/s"])\
        .format(precision=1, na_rep="—")
    st.dataframe(styled_r, use_container_width=True, height=520)

    # Rüzgar profil grafiği (anlık)
    mid_i = idx[len(idx)//2] if idx else 0
    st.markdown("---")
    st.markdown("### Anlık Rüzgar Profili (Yüksekliğe Göre)")
    yukseklikler = [10, 80, 120, 180]
    hizlar = [
        h_val(h1,"windspeed_10m",mid_i) or 0,
        h_val(h1,"windspeed_80m",mid_i) or 0,
        h_val(h1,"windspeed_120m",mid_i) or 0,
        h_val(h1,"windspeed_180m",mid_i) or 0,
    ]
    fig_profil = go.Figure(go.Scatter(
        x=hizlar, y=yukseklikler, mode="lines+markers",
        line=dict(color="#42a5f5",width=3),
        marker=dict(size=10, color="#1a6fff")))
    fig_profil.update_layout(
        title="Rüzgar Hızı (km/s) vs Yükseklik (m)",
        xaxis_title="Hız (km/s)", yaxis_title="Yükseklik (m)",
        height=300, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=35,b=0),
        xaxis=dict(gridcolor="rgba(0,0,0,.05)"),
        yaxis=dict(gridcolor="rgba(0,0,0,.05)"))
    st.plotly_chart(fig_profil, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# 🌱 TOPRAK
# ══════════════════════════════════════════════════════════════
with tab_toprak:
    st.markdown("### 🌱 Toprak Sıcaklığı & Nemi Saatlik")
    idx = gun_filtre("toprak")
    rows = []
    for i in idx:
        dt = datetime.strptime(h1["time"][i],"%Y-%m-%dT%H:%M")
        rows.append({
            "Tarih":       dt.strftime("%d.%m"),
            "Saat":        dt.strftime("%H:%M"),
            "T 0cm °C":    h_val(h1,"soil_temperature_0cm",i),
            "T 6cm °C":    h_val(h1,"soil_temperature_6cm",i),
            "T 18cm °C":   h_val(h1,"soil_temperature_18cm",i),
            "T 54cm °C":   h_val(h1,"soil_temperature_54cm",i),
            "Nem 0-1cm":   h_val(h1,"soil_moisture_0_1cm",i,3),
            "Nem 1-3cm":   h_val(h1,"soil_moisture_1_3cm",i,3),
            "Nem 3-9cm":   h_val(h1,"soil_moisture_3_9cm",i,3),
            "Nem 9-27cm":  h_val(h1,"soil_moisture_9_27cm",i,3),
            "Nem 27-81cm": h_val(h1,"soil_moisture_27_81cm",i,3),
        })
    df_t = pd.DataFrame(rows)
    def rt(val):
        try:
            t=float(val)
            if t<0:  return "background-color:#bbdefb;color:#0d47a1"
            if t<10: return "background-color:#e0f7fa"
            if t<20: return "background-color:#e8f5e9"
            if t<30: return "background-color:#fff9c4"
            return "background-color:#ffccbc"
        except: return ""
    styled_t = df_t.style\
        .map(sicaklik_css, subset=["T 0cm °C","T 6cm °C","T 18cm °C","T 54cm °C"])\
        .format(precision=2, na_rep="—")
    st.dataframe(styled_t, use_container_width=True, height=520)

# ══════════════════════════════════════════════════════════════
# 🌪 ATMOSFERİK
# ══════════════════════════════════════════════════════════════
with tab_atmos:
    st.markdown("### 🌪 Atmosferik & Işınım Saatlik Veriler")
    idx = gun_filtre("atmos")
    rows = []
    for i in idx:
        dt = datetime.strptime(h1["time"][i],"%Y-%m-%dT%H:%M")
        cape_v = h_val(h1,"cape",i,0)
        rows.append({
            "Tarih":         dt.strftime("%d.%m"),
            "Saat":          dt.strftime("%H:%M"),
            "CAPE J/kg":     cape_v,
            "CAPE Yorum":    cape_yorum(cape_v),
            "Lifted Index":  h_val(h1,"lifted_index",i),
            "Donma Yrk m":   h_val(h1,"freezinglevel_height",i,0),
            "Buhar Açığı":   h_val(h1,"vapor_pressure_deficit",i),
            "Buharlaşma":    h_val(h1,"evapotranspiration",i),
            "ET0 mm":        h_val(h1,"et0_fao_evapotranspiration",i),
            "Kısa Dalga":    h_val(h1,"shortwave_radiation",i,0),
            "Direkt Işın.":  h_val(h1,"direct_radiation",i,0),
            "Dağınık Işın.": h_val(h1,"diffuse_radiation",i,0),
            "Direkt Normal": h_val(h1,"direct_normal_irradiance",i,0),
        })
    df_a = pd.DataFrame(rows)

    def rcape(val):
        try:
            c = float(val)
            if c < 300:  return ""
            if c < 1000: return "background-color:#fff9c4"
            if c < 2500: return "background-color:#ffccbc"
            return "background-color:#ef9a9a"
        except: return ""

    styled_a = df_a.style\
        .map(rcape, subset=["CAPE J/kg"])\
        .format(precision=1, na_rep="—")
    st.dataframe(styled_a, use_container_width=True, height=520)

    # CAPE grafiği
    st.markdown("---")
    cape_vals = [h_val(h1,"cape",i,0) or 0 for i in idx]
    saatler_a = [datetime.strptime(h1["time"][i],"%Y-%m-%dT%H:%M").strftime("%d/%m %H:%M") for i in idx]
    fig_cape = go.Figure(go.Bar(x=saatler_a, y=cape_vals,
        marker_color=["#66bb6a" if c<300 else "#ffa726" if c<1000 else
                      "#ef5350" if c<2500 else "#ab47bc" for c in cape_vals]))
    fig_cape.add_hline(y=300,  line_dash="dot", line_color="#ffa726", annotation_text="Hafif Kararsız")
    fig_cape.add_hline(y=1000, line_dash="dot", line_color="#ef5350", annotation_text="Orta Kararsız")
    fig_cape.add_hline(y=2500, line_dash="dot", line_color="#ab47bc", annotation_text="Çok Kararsız")
    fig_cape.update_layout(title="CAPE — Konvektif Enerji (Fırtına Potansiyeli)", height=260,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=35,b=0),
        xaxis=dict(showgrid=False, tickangle=-45, nticks=12),
        yaxis=dict(title="J/kg", gridcolor="rgba(0,0,0,.05)"))
    st.plotly_chart(fig_cape, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# 📆 16 GÜNLÜK TABLO
# ══════════════════════════════════════════════════════════════
with tab_16gun:
    st.markdown(f"### 📆 {forecast_days} Günlük Tahmin Tablosu")
    rows_d = []
    for i in range(len(d1.get("time",[]))):
        tarih = datetime.strptime(d1["time"][i],"%Y-%m-%d")
        ikon_d, acik_d = hk(d_val(d1,"weathercode",i,0))
        gd_i = d1.get("sunrise",[""])[i][11:16] if i < len(d1.get("sunrise",[])) else "—"
        gb_i = d1.get("sunset", [""])[i][11:16] if i < len(d1.get("sunset", [])) else "—"
        sunsec = d_val(d1,"sunshine_duration",i,0)
        rows_d.append({
            "Tarih":        tarih.strftime("%d.%m.%Y"),
            "Gün":          "Bugün" if i==0 else tarih.strftime("%A"),
            "Durum":        f"{ikon_d} {acik_d}",
            "Max °C":       d_val(d1,"temperature_2m_max",i),
            "Min °C":       d_val(d1,"temperature_2m_min",i),
            "Hiss. Max":    d_val(d1,"apparent_temperature_max",i),
            "Hiss. Min":    d_val(d1,"apparent_temperature_min",i),
            "Toplam Yağış": d_val(d1,"precipitation_sum",i),
            "Yağmur mm":    d_val(d1,"rain_sum",i),
            "Sağanak mm":   d_val(d1,"showers_sum",i),
            "Kar mm":       d_val(d1,"snowfall_sum",i),
            "Yağış Saat":   d_val(d1,"precipitation_hours",i,0),
            "Yağış %":      d_val(d1,"precipitation_probability_max",i,0),
            "Rüzgar km/s":  d_val(d1,"windspeed_10m_max",i),
            "Gusto km/s":   d_val(d1,"windgusts_10m_max",i),
            "Rüzgar Yönü":  ryon(d_val(d1,"winddirection_10m_dominant",i,0)),
            "UV Max":       d_val(d1,"uv_index_max",i),
            "UV Açık Göky": d_val(d1,"uv_index_clear_sky_max",i),
            "Güneşlenme s": round(sunsec/3600,1) if sunsec else None,
            "ET0 mm":       d_val(d1,"et0_fao_evapotranspiration",i),
            "Işınım MJ/m²": d_val(d1,"shortwave_radiation_sum",i),
            "Gün Doğumu":   gd_i,
            "Gün Batımı":   gb_i,
        })
    df_gun = pd.DataFrame(rows_d)
    styled_gun = df_gun.style\
        .map(sicaklik_css, subset=["Max °C","Min °C","Hiss. Max","Hiss. Min"])\
        .map(ry, subset=["Toplam Yağış","Yağmur mm","Sağanak mm"])\
        .format(precision=1, na_rep="—")
    st.dataframe(styled_gun, use_container_width=True, height=600)

# ══════════════════════════════════════════════════════════════
# 📈 GRAFİKLER
# ══════════════════════════════════════════════════════════════
with tab_grafik:
    st.markdown("### 📈 Grafikler")
    n    = len(d1.get("time",[]))
    lbls = [datetime.strptime(d1["time"][i],"%Y-%m-%d").strftime("%d %b") for i in range(n)]

    # Sıcaklık
    fig_g1 = go.Figure()
    fig_g1.add_trace(go.Scatter(x=lbls, y=[d_val(d1,"temperature_2m_max",i) for i in range(n)],
        name="Max", line=dict(color="#ff7043",width=2.5),
        fill="tozeroy", fillcolor="rgba(255,112,67,.07)"))
    fig_g1.add_trace(go.Scatter(x=lbls, y=[d_val(d1,"temperature_2m_min",i) for i in range(n)],
        name="Min", line=dict(color="#42a5f5",width=2.5),
        fill="tozeroy", fillcolor="rgba(66,165,245,.07)"))
    fig_g1.add_trace(go.Scatter(x=lbls, y=[d_val(d1,"apparent_temperature_max",i) for i in range(n)],
        name="Hiss. Max", line=dict(color="#ffa726",width=1.5,dash="dot")))
    fig_g1.update_layout(title=f"{forecast_days} Günlük Sıcaklık", height=270,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=35,b=0), hovermode="x unified",
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
        legend=dict(orientation="h",y=1.12))
    st.plotly_chart(fig_g1, use_container_width=True)

    gc1, gc2 = st.columns(2)
    with gc1:
        fig_g2 = go.Figure()
        fig_g2.add_trace(go.Bar(x=lbls,
            y=[d_val(d1,"precipitation_sum",i) or 0 for i in range(n)],
            name="Toplam mm", marker_color="rgba(66,165,245,.8)"))
        fig_g2.add_trace(go.Bar(x=lbls,
            y=[d_val(d1,"snowfall_sum",i) or 0 for i in range(n)],
            name="Kar mm", marker_color="rgba(200,220,255,.9)"))
        fig_g2.add_trace(go.Scatter(x=lbls,
            y=[d_val(d1,"precipitation_probability_max",i) for i in range(n)],
            name="Olas. %", yaxis="y2",
            line=dict(color="#ff8f00",width=2,dash="dot"), mode="lines+markers"))
        fig_g2.update_layout(title="Yağış & Kar", height=260,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0), barmode="stack",
            yaxis=dict(title="mm",gridcolor="rgba(0,0,0,.05)"),
            yaxis2=dict(title="%",overlaying="y",side="right",range=[0,100],showgrid=False),
            legend=dict(orientation="h",y=1.15), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g2, use_container_width=True)

    with gc2:
        fig_g3 = go.Figure()
        fig_g3.add_trace(go.Bar(x=lbls,
            y=[d_val(d1,"windspeed_10m_max",i) or 0 for i in range(n)],
            name="Rüzgar", marker_color="rgba(66,165,245,.8)"))
        fig_g3.add_trace(go.Scatter(x=lbls,
            y=[d_val(d1,"windgusts_10m_max",i) for i in range(n)],
            name="Gusto", line=dict(color="#ef5350",width=2)))
        fig_g3.update_layout(title="Rüzgar & Gusto (km/s)", height=260,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
            legend=dict(orientation="h",y=1.15), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g3, use_container_width=True)

    gc3, gc4 = st.columns(2)
    with gc3:
        uv_vals = [d_val(d1,"uv_index_max",i) or 0 for i in range(n)]
        fig_g4 = go.Figure(go.Bar(x=lbls, y=uv_vals,
            marker_color=["#66bb6a" if u<3 else "#ffa726" if u<6 else
                          "#ef5350" if u<8 else "#ab47bc" for u in uv_vals],
            text=[f"{u:.0f}" for u in uv_vals], textposition="outside"))
        fig_g4.update_layout(title="UV İndeksi", height=230,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g4, use_container_width=True)
        st.caption("🟢<3  🟡3-5  🟠6-7  🔴8-10  🟣11+")

    with gc4:
        sunshine = [round((d_val(d1,"sunshine_duration",i) or 0)/3600,1) for i in range(n)]
        fig_g5 = go.Figure(go.Bar(x=lbls, y=sunshine,
            marker_color="rgba(255,193,7,.85)",
            text=[f"{s:.1f}s" for s in sunshine], textposition="outside"))
        fig_g5.update_layout(title="Güneşlenme Süresi (Saat)", height=230,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g5, use_container_width=True)

    # 384 saatlik trend
    st.markdown("---")
    st.markdown(f"### 📈 {toplam_saat} Saatlik Sıcaklık Trendi")
    fig_tam = go.Figure()
    fig_tam.add_trace(go.Scatter(
        x=h1["time"],
        y=[h_val(h1,"temperature_2m",i) for i in range(toplam_saat)],
        name="Sıcaklık", line=dict(color="#ff7043",width=1.5),
        fill="tozeroy", fillcolor="rgba(255,112,67,.06)"))
    fig_tam.add_trace(go.Scatter(
        x=h1["time"],
        y=[h_val(h1,"apparent_temperature",i) for i in range(toplam_saat)],
        name="Hissedilen", line=dict(color="#ffa726",width=1.5,dash="dot")))
    fig_tam.update_layout(height=280,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=10,b=0), hovermode="x unified",
        xaxis=dict(showgrid=False, nticks=16),
        yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
        legend=dict(orientation="h",y=1.08))
    st.plotly_chart(fig_tam, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# 🔄 KARŞILAŞTIRMA
# ══════════════════════════════════════════════════════════════
if tab_kars and v2:
    with tab_kars:
        d2   = v2["daily"]
        cur2 = v2["current_weather"]
        st.markdown(f"### 🔄 {sehir1} vs {sehir2}")
        k1, k2 = st.columns(2)
        for col, cur_k, d_k, sehir_k in [(k1,cur,d1,sehir1),(k2,cur2,d2,sehir2)]:
            with col:
                ik,ak = hk(cur_k.get("weathercode"))
                st.markdown(f"""
                <div class="anlik-kart" style="padding:18px 22px">
                  <div style="font-weight:700;font-size:1.1rem;margin-bottom:8px">📍 {sehir_k}</div>
                  <div style="font-size:2.5rem;font-weight:800">{ik} {sf(cur_k.get('temperature'),0)}°C</div>
                  <div style="opacity:.75;margin-bottom:10px">{ak}</div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
                    <div class="m-kutu"><div class="m-lbl">💨 Rüzgar</div>
                      <div class="m-val">{sf(cur_k.get('windspeed'),0)} km/s {ryon(cur_k.get('winddirection'))}</div></div>
                    <div class="m-kutu"><div class="m-lbl">🌡 Max/Min</div>
                      <div class="m-val">{sf(d_val(d_k,'temperature_2m_max',0),0)}°/{sf(d_val(d_k,'temperature_2m_min',0),0)}°</div></div>
                  </div>
                </div>""", unsafe_allow_html=True)

        n = min(len(d1.get("time",[])), len(d2.get("time",[])), 7)
        lbls7 = [datetime.strptime(d1["time"][i],"%Y-%m-%d").strftime("%d %b") for i in range(n)]
        fk1, fk2 = st.columns(2)
        with fk1:
            figk = go.Figure()
            figk.add_trace(go.Scatter(x=lbls7,
                y=[d_val(d1,"temperature_2m_max",i) for i in range(n)],
                name=f"{sehir1} Max", line=dict(color="#ff7043",width=2.5)))
            figk.add_trace(go.Scatter(x=lbls7,
                y=[d_val(d2,"temperature_2m_max",i) for i in range(n)],
                name=f"{sehir2} Max", line=dict(color="#ff7043",width=2.5,dash="dot")))
            figk.add_trace(go.Scatter(x=lbls7,
                y=[d_val(d1,"temperature_2m_min",i) for i in range(n)],
                name=f"{sehir1} Min", line=dict(color="#42a5f5",width=2.5)))
            figk.add_trace(go.Scatter(x=lbls7,
                y=[d_val(d2,"temperature_2m_min",i) for i in range(n)],
                name=f"{sehir2} Min", line=dict(color="#42a5f5",width=2.5,dash="dot")))
            figk.update_layout(title="Sıcaklık Karşılaştırma", height=280,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0), hovermode="x unified",
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                legend=dict(orientation="h",y=1.25,font=dict(size=9)))
            st.plotly_chart(figk, use_container_width=True)
        with fk2:
            figky = go.Figure()
            figky.add_trace(go.Bar(x=lbls7,
                y=[d_val(d1,"precipitation_sum",i) or 0 for i in range(n)],
                name=sehir1, marker_color="rgba(66,165,245,.7)"))
            figky.add_trace(go.Bar(x=lbls7,
                y=[d_val(d2,"precipitation_sum",i) or 0 for i in range(n)],
                name=sehir2, marker_color="rgba(239,83,80,.7)"))
            figky.update_layout(title="Yağış Karşılaştırma (mm)", height=280,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0), barmode="group",
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                legend=dict(orientation="h",y=1.15))
            st.plotly_chart(figky, use_container_width=True)

st.divider()
st.caption("🌍 Open-Meteo API · Ücretsiz, açık kaynak · API key gerektirmez · "
           "Tüm mevcut parametreler dahil")
