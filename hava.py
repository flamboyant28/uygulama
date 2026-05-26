import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

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
.gun-adi{font-size:.78rem;color:#7ab3d4;font-weight:700;letter-spacing:.05em;}
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
HAVA_KODU = {
    0:("☀️","Açık"), 1:("🌤","Az Bulutlu"), 2:("⛅","Parçalı Bulutlu"),
    3:("☁️","Bulutlu"), 45:("🌫","Sisli"), 48:("🌫","Yoğun Sis"),
    51:("🌦","Hafif Çisenti"), 53:("🌦","Çisenti"), 55:("🌧","Yoğun Çisenti"),
    61:("🌧","Hafif Yağmur"), 63:("🌧","Yağmur"), 65:("🌧","Yoğun Yağmur"),
    71:("🌨","Hafif Kar"), 73:("❄️","Kar"), 75:("❄️","Yoğun Kar"),
    80:("🌦","Sağanak"), 81:("⛈","Kuvvetli Sağanak"), 82:("⛈","Çok Kuvvetli"),
    85:("🌨","Kar Sağanağı"), 95:("⛈","Fırtına"), 96:("⛈","Dolu+Fırtına"), 99:("⛈","Yoğun Dolu"),
}
def hk(code): return HAVA_KODU.get(int(code) if code else 0, ("🌡","Bilinmiyor"))

RYON = ["K","KKD","KD","DKD","D","DGD","GD","GGD","G","GGB","GB","BGB","B","BKB","KB","KKB"]
def ryon(deg): return RYON[round(float(deg)/22.5)%16] if deg is not None else "—"

def uv_yorum(uv):
    if uv is None: return "—"
    uv = float(uv)
    if uv < 3:  return "🟢 Düşük"
    if uv < 6:  return "🟡 Orta"
    if uv < 8:  return "🟠 Yüksek"
    if uv < 11: return "🔴 Çok Yüksek"
    return "🟣 Aşırı"

# ── API ───────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def sehir_ara(q):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
            params={"q":q,"format":"json","limit":5},
            headers={"User-Agent":"hava-v3/1.0"}, timeout=10)
        return r.json()
    except Exception as e:
        st.error(f"Şehir arama hatası: {e}"); return []

@st.cache_data(ttl=1800)
def hava_cek(lat, lon, forecast_days=16):
    """Open-Meteo: saatlik + günlük, forecast_days=16 → 384 saatlik veri"""
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude":  lat,
            "longitude": lon,
            "current_weather": "true",
            "hourly": ",".join([
                "temperature_2m","apparent_temperature",
                "relativehumidity_2m","dewpoint_2m",
                "precipitation","precipitation_probability","snowfall","snow_depth",
                "weathercode","pressure_msl","surface_pressure",
                "cloudcover","cloudcover_low","cloudcover_mid","cloudcover_high",
                "visibility","windspeed_10m","winddirection_10m","windgusts_10m",
                "uv_index","is_day","shortwave_radiation",
            ]),
            "daily": ",".join([
                "weathercode","temperature_2m_max","temperature_2m_min",
                "apparent_temperature_max","apparent_temperature_min",
                "precipitation_sum","precipitation_hours","precipitation_probability_max",
                "windspeed_10m_max","windgusts_10m_max","winddirection_10m_dominant",
                "shortwave_radiation_sum","uv_index_max",
                "sunrise","sunset","rain_sum","snowfall_sum",
            ]),
            "timezone":       "auto",
            "forecast_days":  forecast_days,
            "wind_speed_unit":"kmh",
        }, timeout=20)
        return r.json()
    except Exception as e:
        st.error(f"Open-Meteo hatası: {e}"); return None

# ── Session State ─────────────────────────────────────────────────────────────
for k,v in [("konum1",None),("konum2",None),
             ("tetik1",False),("tetik2",False),
             ("ara1",""),("ara2","")]:
    if k not in st.session_state: st.session_state[k] = v

# ── Başlık ────────────────────────────────────────────────────────────────────
st.markdown("# 🌤 Hava Durumu Dashboard")
st.caption("Open-Meteo API · Ücretsiz · API key gerektirmez · 16 gün / 384 saat")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Ayarlar")
    forecast_days = st.slider("Tahmin Günü", 1, 16, 16,
        help="Maksimum 16 gün = 384 saatlik veri")
    st.divider()
    st.markdown("**Hızlı Şehirler**")
    hizli = ["İstanbul","Ankara","İzmir","Antalya","Bursa","Trabzon",
             "London","New York","Paris","Tokyo","Dubai","Berlin"]
    for s in hizli:
        if st.button(s, key=f"hz_{s}", use_container_width=True):
            st.session_state.ara1 = s
            st.session_state.tetik1 = True
            st.session_state.konum1 = None
            st.rerun()
    st.divider()
    st.caption("Veri: [Open-Meteo](https://open-meteo.com) · "
               "Şehir: [Nominatim/OSM](https://nominatim.openstreetmap.org)")

# ── Arama ─────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([3,3,1])
with c1:
    girdi1 = st.text_input("Şehir 1", placeholder="İstanbul, Ankara...",
                            value=st.session_state.ara1, key="g1")
with c2:
    girdi2 = st.text_input("Şehir 2 (Karşılaştırma — opsiyonel)",
                            placeholder="London, Berlin...",
                            value=st.session_state.ara2, key="g2")
with c3:
    if st.button("🔍 Ara", type="primary", use_container_width=True):
        if girdi1:
            st.session_state.ara1=girdi1; st.session_state.tetik1=True
            st.session_state.konum1=None
        if girdi2:
            st.session_state.ara2=girdi2; st.session_state.tetik2=True
            st.session_state.konum2=None
        st.rerun()

for ara_k, tetik_k, konum_k in [("ara1","tetik1","konum1"),("ara2","tetik2","konum2")]:
    if st.session_state[tetik_k] and st.session_state[ara_k]:
        with st.spinner(f"{st.session_state[ara_k]} aranıyor..."):
            sonuclar = sehir_ara(st.session_state[ara_k])
        if sonuclar:
            s = sonuclar[0]
            ad = s.get("display_name","").split(",")[0]
            st.session_state[konum_k] = (float(s["lat"]),float(s["lon"]),ad)
        else:
            st.error(f"'{st.session_state[ara_k]}' bulunamadı.")
        st.session_state[tetik_k] = False

if not st.session_state.konum1:
    st.info("👆 Şehir ara veya sol panelden hızlı seçim yap.")
    st.stop()

# ── Veri Çek ──────────────────────────────────────────────────────────────────
lat1,lon1,sehir1 = st.session_state.konum1
with st.spinner(f"{sehir1} hava verisi alınıyor..."):
    v1 = hava_cek(lat1, lon1, forecast_days)
if not v1: st.stop()

v2 = None; sehir2 = ""
if st.session_state.konum2:
    lat2,lon2,sehir2 = st.session_state.konum2
    with st.spinner(f"{sehir2} verisi alınıyor..."):
        v2 = hava_cek(lat2, lon2, forecast_days)

h1 = v1["hourly"]; d1 = v1["daily"]; cur = v1["current_weather"]
toplam_saat = len(h1["time"])

# ── Sekmeler ──────────────────────────────────────────────────────────────────
tab_listesi = ["🌡 Anlık","📅 Günlük","⏰ Saatlik Tablo","📆 16 Günlük Tablo","📈 Grafikler"]
if v2: tab_listesi.append("🔄 Karşılaştırma")
tabs = st.tabs(tab_listesi)
tab_anlik, tab_gunluk, tab_saatlik, tab_16gun, tab_grafik = tabs[:5]
tab_kars = tabs[5] if len(tabs)>5 else None

# ══════════════════════════════════════════════════════════════
# 🌡 ANLIK
# ══════════════════════════════════════════════════════════════
with tab_anlik:
    ikon0, acik0 = hk(cur["weathercode"])
    gd = d1["sunrise"][0][11:16]
    gb = d1["sunset"][0][11:16]

    ca, cb = st.columns([1.2,1])
    with ca:
        st.markdown(f"""
        <div class="anlik-kart">
          <div style="font-size:.82rem;opacity:.6">{datetime.now().strftime('%d %B %Y  %H:%M')}</div>
          <div style="font-size:1.3rem;font-weight:700;margin:4px 0">📍 {sehir1}</div>
          <div style="display:flex;align-items:center;gap:20px;margin:14px 0">
            <div style="font-size:3.5rem">{ikon0}</div>
            <div>
              <div style="font-size:4rem;font-weight:800;line-height:1">{cur['temperature']:.0f}°C</div>
              <div style="opacity:.75;font-style:italic">{acik0}</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
            <div class="m-kutu"><div class="m-lbl">💨 Rüzgar</div>
              <div class="m-val">{cur['windspeed']:.0f} km/s {ryon(cur['winddirection'])}</div></div>
            <div class="m-kutu"><div class="m-lbl">🌡 Max / Min</div>
              <div class="m-val">{d1['temperature_2m_max'][0]:.0f}° / {d1['temperature_2m_min'][0]:.0f}°</div></div>
            <div class="m-kutu"><div class="m-lbl">💧 Yağış</div>
              <div class="m-val">{d1['precipitation_sum'][0]:.1f} mm</div></div>
            <div class="m-kutu"><div class="m-lbl">☀️ UV İndeks</div>
              <div class="m-val">{uv_yorum(d1['uv_index_max'][0])}</div></div>
            <div class="m-kutu"><div class="m-lbl">🌅 Gün Doğumu</div>
              <div class="m-val">{gd}</div></div>
            <div class="m-kutu"><div class="m-lbl">🌇 Gün Batımı</div>
              <div class="m-val">{gb}</div></div>
          </div>
        </div>""", unsafe_allow_html=True)

    with cb:
        # Bugünün saatlik sıcaklık grafiği
        bugun = d1["time"][0]
        idx_b = [i for i,t in enumerate(h1["time"]) if t.startswith(bugun)]
        fig_b = go.Figure()
        fig_b.add_trace(go.Scatter(
            x=[h1["time"][i][11:16] for i in idx_b],
            y=[h1["temperature_2m"][i] for i in idx_b],
            mode="lines+markers", name="Sıcaklık",
            line=dict(color="#ff7043",width=2.5),
            fill="tozeroy", fillcolor="rgba(255,112,67,.08)"))
        fig_b.add_trace(go.Scatter(
            x=[h1["time"][i][11:16] for i in idx_b],
            y=[h1["apparent_temperature"][i] for i in idx_b],
            mode="lines", name="Hissedilen",
            line=dict(color="#ffa726",width=2,dash="dot")))
        fig_b.update_layout(title="Bugün Saatlik Sıcaklık", height=230,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0), hovermode="x unified",
            xaxis=dict(showgrid=False, nticks=8),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
            legend=dict(orientation="h",y=1.15))
        st.plotly_chart(fig_b, use_container_width=True)

        # Bugünün detay metrikleri
        m1,m2,m3 = st.columns(3)
        with m1:
            nem_b  = h1["relativehumidity_2m"][idx_b[len(idx_b)//2]] if idx_b else 0
            st.metric("💧 Nem", f"%{nem_b}")
        with m2:
            bas_b  = h1["pressure_msl"][idx_b[len(idx_b)//2]] if idx_b else 0
            st.metric("🌬 Basınç", f"{bas_b:.0f} hPa")
        with m3:
            gus_b  = h1["windgusts_10m"][idx_b[len(idx_b)//2]] if idx_b else 0
            st.metric("💨 Gusto", f"{gus_b:.0f} km/s")

# ══════════════════════════════════════════════════════════════
# 📅 GÜNLÜK (7 kartlı)
# ══════════════════════════════════════════════════════════════
with tab_gunluk:
    st.markdown("### 📅 7 Günlük Tahmin")
    cols7 = st.columns(7)
    for i,col in enumerate(cols7):
        tarih = datetime.strptime(d1["time"][i],"%Y-%m-%d")
        ikon_g, acik_g = hk(d1["weathercode"][i])
        with col:
            st.markdown(f"""
            <div class="gun-karti">
              <div class="gun-adi">{"Bugün" if i==0 else tarih.strftime("%a")}<br>{tarih.strftime("%d/%m")}</div>
              <div class="gun-ikon">{ikon_g}</div>
              <div class="gun-max">{d1['temperature_2m_max'][i]:.0f}°</div>
              <div class="gun-min">{d1['temperature_2m_min'][i]:.0f}°</div>
              <div class="gun-alt">💧{d1['precipitation_sum'][i]:.1f}mm
              %{d1['precipitation_probability_max'][i]:.0f}</div>
              <div class="gun-alt">💨{d1['windspeed_10m_max'][i]:.0f}km/s
              UV:{d1['uv_index_max'][i]:.0f}</div>
            </div>""", unsafe_allow_html=True)

    # 7 günlük grafik
    st.markdown("---")
    lbls7 = [datetime.strptime(d1["time"][i],"%Y-%m-%d").strftime("%d %b") for i in range(7)]
    fig7 = go.Figure()
    fig7.add_trace(go.Scatter(x=lbls7, y=d1["temperature_2m_max"][:7],
        name="Max", line=dict(color="#ff7043",width=3),
        fill="tozeroy", fillcolor="rgba(255,112,67,.07)"))
    fig7.add_trace(go.Scatter(x=lbls7, y=d1["temperature_2m_min"][:7],
        name="Min", line=dict(color="#42a5f5",width=3),
        fill="tozeroy", fillcolor="rgba(66,165,245,.07)"))
    fig7.add_trace(go.Bar(x=lbls7, y=d1["precipitation_sum"][:7],
        name="Yağış mm", yaxis="y2", marker_color="rgba(100,180,255,.6)"))
    fig7.update_layout(title="7 Günlük Sıcaklık & Yağış", height=280,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=35,b=0), hovermode="x unified",
        yaxis=dict(title="°C",gridcolor="rgba(0,0,0,.05)"),
        yaxis2=dict(title="mm",overlaying="y",side="right",showgrid=False),
        legend=dict(orientation="h",y=1.12), xaxis=dict(showgrid=False))
    st.plotly_chart(fig7, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# ⏰ SAATLİK TABLO
# ══════════════════════════════════════════════════════════════
with tab_saatlik:
    st.markdown("### ⏰ Saatlik Veri Tablosu")
    st.success(f"✅ Open-Meteo · **{toplam_saat} saat** ({forecast_days} gün × 24 saat)")

    # Gün filtresi
    gunler_lst = sorted(set(t[:10] for t in h1["time"]))
    gun_sec_lbls = ["Tümü"] + [
        datetime.strptime(g,"%Y-%m-%d").strftime("%d %B %Y (%A)")
        for g in gunler_lst
    ]
    gun_sec = st.selectbox("📅 Gün filtresi", range(len(gun_sec_lbls)),
                           format_func=lambda i: gun_sec_lbls[i])

    if gun_sec == 0:
        idx_filtre = range(len(h1["time"]))
    else:
        secili_gun = gunler_lst[gun_sec-1]
        idx_filtre = [i for i,t in enumerate(h1["time"]) if t.startswith(secili_gun)]

    rows = []
    for i in idx_filtre:
        dt = datetime.strptime(h1["time"][i], "%Y-%m-%dT%H:%M")
        ikon_s, acik_s = hk(h1["weathercode"][i])
        rows.append({
            "Tarih":        dt.strftime("%d.%m"),
            "Saat":         dt.strftime("%H:%M"),
            "Gün/Gece":     "☀️" if h1["is_day"][i] else "🌙",
            "Durum":        f"{ikon_s} {acik_s}",
            "Sıcaklık °C":  h1["temperature_2m"][i],
            "Hissedilen":   h1["apparent_temperature"][i],
            "Nem %":        h1["relativehumidity_2m"][i],
            "Çiy Noktası":  round(h1["dewpoint_2m"][i],1),
            "Basınç hPa":   h1["pressure_msl"][i],
            "Bulut %":      h1["cloudcover"][i],
            "Bulut Alçak":  h1["cloudcover_low"][i],
            "Bulut Orta":   h1["cloudcover_mid"][i],
            "Bulut Yüksek": h1["cloudcover_high"][i],
            "Görüş km":     round(h1["visibility"][i]/1000,1) if h1["visibility"][i] else 0,
            "Yağış mm":     h1["precipitation"][i],
            "Yağış %":      h1["precipitation_probability"][i],
            "Kar cm":       h1["snowfall"][i],
            "Rüzgar km/s":  h1["windspeed_10m"][i],
            "Rüzgar Yönü":  ryon(h1["winddirection_10m"][i]),
            "Gusto km/s":   h1["windgusts_10m"][i],
            "UV":           round(h1["uv_index"][i],1),
            "Işınım W/m²":  round(h1["shortwave_radiation"][i],0),
        })

    df_saat = pd.DataFrame(rows)
    st.caption(f"Gösterilen: {len(rows)} veri noktası")

    # Renk fonksiyonları
    def rs(val):
        try:
            t=float(val)
            if t<0:  return "background-color:#bbdefb;color:#0d47a1"
            if t<10: return "background-color:#e0f7fa"
            if t<20: return "background-color:#e8f5e9"
            if t<30: return "background-color:#fff9c4"
            return "background-color:#ffccbc"
        except: return ""

    def ry(val):
        try:
            y=float(val)
            if y==0: return ""
            if y<2:  return "background-color:#e3f2fd"
            if y<10: return "background-color:#90caf9"
            return "background-color:#42a5f5;color:white"
        except: return ""

    def rn(val):
        try:
            n=float(val)
            if n<40: return "background-color:#fff9c4"
            if n<60: return "background-color:#e8f5e9"
            if n<80: return "background-color:#e3f2fd"
            return "background-color:#bbdefb"
        except: return ""

    def rb(val):
        try:
            b=float(val)
            if b<25:  return ""
            if b<50:  return "background-color:#f5f5f5"
            if b<75:  return "background-color:#eeeeee"
            return "background-color:#e0e0e0"
        except: return ""

    styled_s = df_saat.style\
        .map(rs, subset=["Sıcaklık °C","Hissedilen"])\
        .map(ry, subset=["Yağış mm"])\
        .map(rn, subset=["Nem %"])\
        .map(rb, subset=["Bulut %"])\
        .format(precision=1)

    st.dataframe(styled_s, use_container_width=True, height=520)

    # Seçili gün grafiği
    if gun_sec > 0 and len(rows) > 0:
        st.markdown("---")
        sg1, sg2 = st.columns(2)
        saatler = [r["Saat"] for r in rows]
        with sg1:
            fig_sg = go.Figure()
            fig_sg.add_trace(go.Scatter(x=saatler, y=[r["Sıcaklık °C"] for r in rows],
                name="Sıcaklık", line=dict(color="#ff7043",width=2.5),
                fill="tozeroy", fillcolor="rgba(255,112,67,.08)"))
            fig_sg.add_trace(go.Scatter(x=saatler, y=[r["Hissedilen"] for r in rows],
                name="Hissedilen", line=dict(color="#ffa726",width=2,dash="dot")))
            fig_sg.update_layout(title="Sıcaklık", height=220,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0),
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                legend=dict(orientation="h",y=1.2))
            st.plotly_chart(fig_sg, use_container_width=True)
        with sg2:
            fig_rg = go.Figure()
            fig_rg.add_trace(go.Bar(x=saatler, y=[r["Rüzgar km/s"] for r in rows],
                name="Rüzgar", marker_color="rgba(66,165,245,.75)"))
            fig_rg.add_trace(go.Scatter(x=saatler, y=[r["Gusto km/s"] for r in rows],
                name="Gusto", line=dict(color="#ef5350",width=2)))
            fig_rg.update_layout(title="Rüzgar & Gusto (km/s)", height=220,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0),
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                legend=dict(orientation="h",y=1.2))
            st.plotly_chart(fig_rg, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# 📆 16 GÜNLÜK TABLO
# ══════════════════════════════════════════════════════════════
with tab_16gun:
    st.markdown(f"### 📆 {forecast_days} Günlük Tahmin Tablosu")
    n = len(d1["time"])
    rows_d = []
    for i in range(n):
        tarih = datetime.strptime(d1["time"][i],"%Y-%m-%d")
        ikon_d, acik_d = hk(d1["weathercode"][i])
        rows_d.append({
            "Tarih":        tarih.strftime("%d.%m.%Y"),
            "Gün":          "Bugün" if i==0 else tarih.strftime("%A"),
            "Durum":        f"{ikon_d} {acik_d}",
            "Max °C":       d1["temperature_2m_max"][i],
            "Min °C":       d1["temperature_2m_min"][i],
            "Hiss. Max":    d1["apparent_temperature_max"][i],
            "Hiss. Min":    d1["apparent_temperature_min"][i],
            "Yağış mm":     d1["precipitation_sum"][i],
            "Yağış Saat":   d1["precipitation_hours"][i],
            "Yağış %":      d1["precipitation_probability_max"][i],
            "Kar mm":       d1["snowfall_sum"][i],
            "Yağmur mm":    d1["rain_sum"][i],
            "Rüzgar km/s":  d1["windspeed_10m_max"][i],
            "Gusto km/s":   d1["windgusts_10m_max"][i],
            "Rüzgar Yönü":  ryon(d1["winddirection_10m_dominant"][i]),
            "UV Max":       d1["uv_index_max"][i],
            "Işınım MJ/m²": d1["shortwave_radiation_sum"][i],
            "Gün Doğumu":   d1["sunrise"][i][11:16],
            "Gün Batımı":   d1["sunset"][i][11:16],
        })

    df_gun = pd.DataFrame(rows_d)

    def rm(val):
        try:
            t=float(val)
            if t<0:  return "background-color:#bbdefb;color:#0d47a1"
            if t<10: return "background-color:#e0f7fa"
            if t<20: return "background-color:#e8f5e9"
            if t<30: return "background-color:#fff9c4"
            return "background-color:#ffccbc"
        except: return ""

    styled_g = df_gun.style\
        .map(rm, subset=["Max °C","Min °C","Hiss. Max","Hiss. Min"])\
        .map(ry, subset=["Yağış mm"])\
        .format(precision=1)

    st.dataframe(styled_g, use_container_width=True, height=600)

# ══════════════════════════════════════════════════════════════
# 📈 GRAFİKLER
# ══════════════════════════════════════════════════════════════
with tab_grafik:
    st.markdown("### 📈 Grafikler")

    n    = len(d1["time"])
    lbls = [datetime.strptime(d1["time"][i],"%Y-%m-%d").strftime("%d %b") for i in range(n)]

    # 16 günlük sıcaklık
    fig_g1 = go.Figure()
    fig_g1.add_trace(go.Scatter(x=lbls, y=d1["temperature_2m_max"],
        name="Max", line=dict(color="#ff7043",width=2.5),
        fill="tozeroy", fillcolor="rgba(255,112,67,.07)"))
    fig_g1.add_trace(go.Scatter(x=lbls, y=d1["temperature_2m_min"],
        name="Min", line=dict(color="#42a5f5",width=2.5),
        fill="tozeroy", fillcolor="rgba(66,165,245,.07)"))
    fig_g1.add_trace(go.Scatter(x=lbls, y=d1["apparent_temperature_max"],
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
        fig_g2.add_trace(go.Bar(x=lbls, y=d1["precipitation_sum"],
            name="Yağış mm",
            marker_color=["#42a5f5" if y<5 else "#1565c0" if y<15 else "#0d47a1"
                          for y in d1["precipitation_sum"]],
            text=[f"{y:.1f}" for y in d1["precipitation_sum"]],
            textposition="outside"))
        fig_g2.add_trace(go.Scatter(x=lbls, y=d1["precipitation_probability_max"],
            name="Olas. %", yaxis="y2",
            line=dict(color="#ff8f00",width=2,dash="dot"), mode="lines+markers"))
        fig_g2.update_layout(title="Yağış & Olasılık", height=260,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            yaxis=dict(title="mm",gridcolor="rgba(0,0,0,.05)"),
            yaxis2=dict(title="%",overlaying="y",side="right",range=[0,100],showgrid=False),
            legend=dict(orientation="h",y=1.15), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g2, use_container_width=True)

    with gc2:
        fig_g3 = go.Figure()
        fig_g3.add_trace(go.Bar(x=lbls, y=d1["windspeed_10m_max"],
            name="Rüzgar", marker_color="rgba(66,165,245,.8)"))
        fig_g3.add_trace(go.Scatter(x=lbls, y=d1["windgusts_10m_max"],
            name="Gusto", line=dict(color="#ef5350",width=2)))
        fig_g3.update_layout(title="Rüzgar & Gusto (km/s)", height=260,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
            legend=dict(orientation="h",y=1.15), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g3, use_container_width=True)

    gc3, gc4 = st.columns(2)
    with gc3:
        uv_renk = ["#66bb6a" if u<3 else "#ffa726" if u<6 else
                   "#ef5350" if u<8 else "#ab47bc" for u in d1["uv_index_max"]]
        fig_g4 = go.Figure(go.Bar(x=lbls, y=d1["uv_index_max"],
            marker_color=uv_renk,
            text=[f"{u:.0f}" for u in d1["uv_index_max"]],
            textposition="outside"))
        fig_g4.update_layout(title="UV İndeksi", height=230,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g4, use_container_width=True)
        st.caption("🟢<3  🟡3-5  🟠6-7  🔴8-10  🟣11+")

    with gc4:
        fig_g5 = go.Figure(go.Bar(x=lbls, y=d1["shortwave_radiation_sum"],
            marker_color="rgba(255,193,7,.8)",
            text=[f"{r:.0f}" for r in d1["shortwave_radiation_sum"]],
            textposition="outside"))
        fig_g5.update_layout(title="Güneş Işınımı (MJ/m²)", height=230,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g5, use_container_width=True)

    # 384 saatlik sıcaklık trendi
    st.markdown("---")
    st.markdown(f"### 📈 {toplam_saat} Saatlik Sıcaklık Trendi")
    fig_tam = go.Figure()
    fig_tam.add_trace(go.Scatter(
        x=h1["time"], y=h1["temperature_2m"],
        name="Sıcaklık", line=dict(color="#ff7043",width=1.5),
        fill="tozeroy", fillcolor="rgba(255,112,67,.06)"))
    fig_tam.add_trace(go.Scatter(
        x=h1["time"], y=h1["apparent_temperature"],
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
        st.markdown(f"### 🔄 {sehir1} vs {sehir2}")
        d2 = v2["daily"]
        cur2 = v2["current_weather"]

        k1, k2 = st.columns(2)
        for col, cur_k, sehir_k in [(k1,cur,sehir1),(k2,cur2,sehir2)]:
            with col:
                ik,ak = hk(cur_k["weathercode"])
                st.markdown(f"""
                <div class="anlik-kart" style="padding:18px 22px">
                  <div style="font-weight:700;font-size:1.1rem;margin-bottom:8px">📍 {sehir_k}</div>
                  <div style="font-size:2.5rem;font-weight:800">{ik} {cur_k['temperature']:.0f}°C</div>
                  <div style="opacity:.75;margin-bottom:10px">{ak}</div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
                    <div class="m-kutu"><div class="m-lbl">💨 Rüzgar</div>
                      <div class="m-val">{cur_k['windspeed']:.0f} km/s</div></div>
                    <div class="m-kutu"><div class="m-lbl">🌡 Max/Min</div>
                      <div class="m-val">{v1['daily']['temperature_2m_max'][0] if sehir_k==sehir1 else d2['temperature_2m_max'][0]:.0f}°/{v1['daily']['temperature_2m_min'][0] if sehir_k==sehir1 else d2['temperature_2m_min'][0]:.0f}°</div></div>
                  </div>
                </div>""", unsafe_allow_html=True)

        n = min(len(d1["time"]),len(d2["time"]),7)
        lbls7 = [datetime.strptime(d1["time"][i],"%Y-%m-%d").strftime("%d %b") for i in range(n)]

        fk1, fk2 = st.columns(2)
        with fk1:
            figk = go.Figure()
            figk.add_trace(go.Scatter(x=lbls7, y=d1["temperature_2m_max"][:n],
                name=f"{sehir1} Max", line=dict(color="#ff7043",width=2.5)))
            figk.add_trace(go.Scatter(x=lbls7, y=d2["temperature_2m_max"][:n],
                name=f"{sehir2} Max", line=dict(color="#ff7043",width=2.5,dash="dot")))
            figk.add_trace(go.Scatter(x=lbls7, y=d1["temperature_2m_min"][:n],
                name=f"{sehir1} Min", line=dict(color="#42a5f5",width=2.5)))
            figk.add_trace(go.Scatter(x=lbls7, y=d2["temperature_2m_min"][:n],
                name=f"{sehir2} Min", line=dict(color="#42a5f5",width=2.5,dash="dot")))
            figk.update_layout(title="Sıcaklık Karşılaştırma", height=280,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0), hovermode="x unified",
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                legend=dict(orientation="h",y=1.25,font=dict(size=9)))
            st.plotly_chart(figk, use_container_width=True)

        with fk2:
            figky = go.Figure()
            figky.add_trace(go.Bar(x=lbls7, y=d1["precipitation_sum"][:n],
                name=sehir1, marker_color="rgba(66,165,245,.7)"))
            figky.add_trace(go.Bar(x=lbls7, y=d2["precipitation_sum"][:n],
                name=sehir2, marker_color="rgba(239,83,80,.7)"))
            figky.update_layout(title="Yağış Karşılaştırma (mm)", height=280,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0), barmode="group",
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                legend=dict(orientation="h",y=1.15))
            st.plotly_chart(figky, use_container_width=True)

st.divider()
st.caption("🌍 Open-Meteo API · Ücretsiz, açık kaynak · openweathermap'tan farklı olarak API key gerektirmez")
