import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import math

st.set_page_config(page_title="Hava Durumu", page_icon="🌤", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
html,body,[class*="css"]{ font-family:'Outfit',sans-serif; }

.gun-karti {
    background:linear-gradient(135deg,#1e3a5f,#0f2a4a);
    border:1px solid #2a4a6a; border-radius:14px;
    padding:14px 10px; text-align:center;
    transition:transform .2s;
}
.gun-karti:hover{transform:translateY(-2px);}
.gun-adi{font-size:.78rem;color:#7ab3d4;font-weight:700;letter-spacing:.05em;}
.gun-ikon{font-size:2rem;margin:6px 0;}
.gun-max{font-size:1.3rem;font-weight:800;color:#ff7043;}
.gun-min{font-size:.95rem;font-weight:500;color:#64b5f6;}
.gun-alt{font-size:.7rem;color:#90caf9;margin-top:4px;}

.anlik-kart{
    background:linear-gradient(135deg,#0d47a1,#1565c0,#1976d2);
    border-radius:20px; padding:24px 28px; color:white;
}
.metrik-kutu{
    background:rgba(255,255,255,.15);
    border-radius:10px; padding:10px 14px; margin-top:10px;
}
.metrik-lbl{font-size:.68rem;opacity:.7;letter-spacing:.06em;text-transform:uppercase;}
.metrik-val{font-size:1.05rem;font-weight:700;}
</style>
""", unsafe_allow_html=True)

# ── Yardımcı ─────────────────────────────────────────────────────────────────
HAVA_KODU = {
    0:("☀️","Açık"), 1:("🌤","Az Bulutlu"), 2:("⛅","Parçalı Bulutlu"),
    3:("☁️","Bulutlu"), 45:("🌫","Sisli"), 48:("🌫","Yoğun Sis"),
    51:("🌦","Hafif Çisenti"), 53:("🌦","Çisenti"), 55:("🌧","Yoğun Çisenti"),
    61:("🌧","Hafif Yağmur"), 63:("🌧","Yağmur"), 65:("🌧","Yoğun Yağmur"),
    71:("🌨","Hafif Kar"), 73:("❄️","Kar"), 75:("❄️","Yoğun Kar"),
    80:("🌦","Sağanak"), 81:("⛈","Kuvvetli Sağanak"), 82:("⛈","Çok Kuvvetli Sağanak"),
    85:("🌨","Kar Sağanağı"), 95:("⛈","Fırtına"), 96:("⛈","Dolu ile Fırtına"), 99:("⛈","Yoğun Dolu"),
}

def hk(code):
    return HAVA_KODU.get(code, ("🌡","Bilinmiyor"))

def ryon(deg):
    dirs = ["K","KKD","KD","DKD","D","DGD","GD","GGD","G","GGB","GB","BGB","B","BKB","KB","KKB"]
    return dirs[round(deg/22.5) % 16]

def uv_yorum(uv):
    if uv < 3:   return "🟢 Düşük"
    if uv < 6:   return "🟡 Orta"
    if uv < 8:   return "🟠 Yüksek"
    if uv < 11:  return "🔴 Çok Yüksek"
    return "🟣 Aşırı"

def renk_sicaklik(t):
    if t < 0:    return "#90caf9"
    if t < 10:   return "#80cbc4"
    if t < 20:   return "#a5d6a7"
    if t < 30:   return "#ffcc80"
    return "#ef9a9a"

def renk_yagis(mm):
    if mm == 0:  return ""
    if mm < 2:   return "background-color:#e3f2fd"
    if mm < 10:  return "background-color:#bbdefb"
    return "background-color:#90caf9"

# ── API ───────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def sehir_ara(q):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
            params={"q":q,"format":"json","limit":5},
            headers={"User-Agent":"hava-v2/1.0"}, timeout=10)
        return r.json()
    except: return []

@st.cache_data(ttl=1800)
def hava_cek(lat, lon):
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current_weather": "true",
            "hourly": ",".join([
                "temperature_2m","apparent_temperature","relativehumidity_2m",
                "dewpoint_2m","precipitation","precipitation_probability",
                "snowfall","snow_depth","weathercode","pressure_msl",
                "surface_pressure","cloudcover","cloudcover_low","cloudcover_mid",
                "cloudcover_high","visibility","windspeed_10m","winddirection_10m",
                "windgusts_10m","uv_index","is_day",
            ]),
            "daily": ",".join([
                "weathercode","temperature_2m_max","temperature_2m_min",
                "apparent_temperature_max","apparent_temperature_min",
                "precipitation_sum","precipitation_hours","precipitation_probability_max",
                "windspeed_10m_max","windgusts_10m_max","winddirection_10m_dominant",
                "shortwave_radiation_sum","uv_index_max","sunrise","sunset",
                "snowfall_sum","rain_sum",
            ]),
            "timezone": "auto",
            "forecast_days": 16,
            "wind_speed_unit": "kmh",
        }, timeout=15)
        return r.json()
    except Exception as e:
        st.error(f"API hatası: {e}"); return None

# ── Session state ─────────────────────────────────────────────────────────────
for k,v in [("konum1",None),("konum2",None),("ara1",""),("ara2",""),
             ("tetik1",False),("tetik2",False)]:
    if k not in st.session_state: st.session_state[k] = v

# ── Başlık ────────────────────────────────────────────────────────────────────
st.markdown("# 🌤 Hava Durumu Dashboard")

# ── Şehir Arama ──────────────────────────────────────────────────────────────
with st.expander("🔍 Şehir Seç", expanded=st.session_state.konum1 is None):
    c1,c2,c3 = st.columns([3,3,1])
    with c1:
        girdi1 = st.text_input("Şehir 1",placeholder="İstanbul, Ankara...",key="g1")
    with c2:
        girdi2 = st.text_input("Şehir 2 (Karşılaştırma için opsiyonel)",
                               placeholder="London, Berlin...", key="g2")
    with c3:
        ara_btn = st.button("🔍 Ara", type="primary", use_container_width=True)

    # Hızlı seçim
    hizli = ["İstanbul","Ankara","İzmir","Antalya","Bursa","London","New York","Paris","Tokyo","Dubai"]
    st.markdown("**Hızlı:**")
    hcols = st.columns(len(hizli))
    for i,s in enumerate(hizli):
        with hcols[i]:
            if st.button(s, key=f"hz_{s}", use_container_width=True):
                st.session_state.ara1 = s
                st.session_state.tetik1 = True
                st.rerun()

    if ara_btn:
        if girdi1: st.session_state.ara1 = girdi1; st.session_state.tetik1 = True
        if girdi2: st.session_state.ara2 = girdi2; st.session_state.tetik2 = True
        st.rerun()

# Koordinat çöz
for idx, (ara_key, tetik_key, konum_key) in enumerate([
    ("ara1","tetik1","konum1"), ("ara2","tetik2","konum2")
]):
    if st.session_state[tetik_key] and st.session_state[ara_key]:
        with st.spinner(f"Aranıyor: {st.session_state[ara_key]}..."):
            sonuclar = sehir_ara(st.session_state[ara_key])
        if sonuclar:
            s = sonuclar[0]
            st.session_state[konum_key] = (
                float(s["lat"]), float(s["lon"]),
                s["display_name"].split(",")[0]
            )
        st.session_state[tetik_key] = False

if not st.session_state.konum1:
    st.info("👆 Yukarıdan bir şehir ara veya hızlı seçim yap.")
    st.stop()

# ── Veri Çek ─────────────────────────────────────────────────────────────────
lat1, lon1, sehir1 = st.session_state.konum1
with st.spinner("Hava verisi alınıyor..."):
    v1 = hava_cek(lat1, lon1)
if not v1: st.stop()

v2 = None
if st.session_state.konum2:
    lat2, lon2, sehir2 = st.session_state.konum2
    with st.spinner(f"{sehir2} verisi alınıyor..."):
        v2 = hava_cek(lat2, lon2)

# ── Sekmeler ──────────────────────────────────────────────────────────────────
tabs = st.tabs(["🌡 Anlık","📅 7 Günlük","⏰ Saatlik Tablo","📆 16 Günlük Tablo","📈 Grafikler"])
if v2:
    tabs = st.tabs(["🌡 Anlık","📅 7 Günlük","⏰ Saatlik Tablo",
                    "📆 16 Günlük Tablo","📈 Grafikler","🔄 Karşılaştırma"])

tab_anlik, tab_7gun, tab_saatlik, tab_16gun, tab_grafik = tabs[:5]
tab_kars = tabs[5] if len(tabs) > 5 else None

# ════════════════════════════════════════════════════════════
# 🌡 ANLIK
# ════════════════════════════════════════════════════════════
with tab_anlik:
    cur  = v1["current_weather"]
    d    = v1["daily"]
    ikon,acik = hk(cur["weathercode"])

    col_anlik, col_bugun = st.columns([1.2, 1])
    with col_anlik:
        st.markdown(f"""
        <div class="anlik-kart">
          <div style="font-size:.85rem;opacity:.65">{datetime.now().strftime('%d %B %Y  %H:%M')}</div>
          <div style="font-size:1.3rem;font-weight:700;margin:4px 0">📍 {sehir1}</div>
          <div style="display:flex;align-items:center;gap:20px;margin:12px 0">
            <div style="font-size:3.5rem">{ikon}</div>
            <div>
              <div style="font-size:4rem;font-weight:800;line-height:1">{cur['temperature']:.0f}°C</div>
              <div style="opacity:.75;font-style:italic">{acik}</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
            <div class="metrik-kutu">
              <div class="metrik-lbl">💨 Rüzgar</div>
              <div class="metrik-val">{cur['windspeed']:.0f} km/s {ryon(cur['winddirection'])}</div>
            </div>
            <div class="metrik-kutu">
              <div class="metrik-lbl">☀️ UV</div>
              <div class="metrik-val">{uv_yorum(d['uv_index_max'][0])}</div>
            </div>
            <div class="metrik-kutu">
              <div class="metrik-lbl">🌅 Gün Doğumu</div>
              <div class="metrik-val">{d['sunrise'][0][11:16]}</div>
            </div>
            <div class="metrik-kutu">
              <div class="metrik-lbl">🌡 Max / Min</div>
              <div class="metrik-val">{d['temperature_2m_max'][0]:.0f}° / {d['temperature_2m_min'][0]:.0f}°</div>
            </div>
            <div class="metrik-kutu">
              <div class="metrik-lbl">💧 Yağış</div>
              <div class="metrik-val">{d['precipitation_sum'][0]:.1f} mm</div>
            </div>
            <div class="metrik-kutu">
              <div class="metrik-lbl">🌇 Gün Batımı</div>
              <div class="metrik-val">{d['sunset'][0][11:16]}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_bugun:
        st.markdown("### Bugün Saatlik (Sıcaklık)")
        h = v1["hourly"]
        bugun = d["time"][0]
        idx_bugun = [i for i,t in enumerate(h["time"]) if t.startswith(bugun)]
        saatler = [h["time"][i][11:16] for i in idx_bugun]
        sicak   = [h["temperature_2m"][i] for i in idx_bugun]
        nem     = [h["relativehumidity_2m"][i] for i in idx_bugun]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=saatler, y=sicak, mode="lines+markers",
            line=dict(color="#ff7043",width=2.5), fill="tozeroy",
            fillcolor="rgba(255,112,67,.1)", name="°C"))
        fig.update_layout(height=220, margin=dict(l=0,r=0,t=10,b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
            xaxis=dict(showgrid=False, tickangle=-45, nticks=8))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Nem (Bugün)")
        fig2 = go.Figure(go.Bar(x=saatler, y=nem,
            marker_color=[f"rgb(66,{130+int(n/100*80)},245)" for n in nem]))
        fig2.update_layout(height=180, margin=dict(l=0,r=0,t=5,b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[0,100],gridcolor="rgba(0,0,0,.05)"),
            xaxis=dict(showgrid=False, tickangle=-45, nticks=8))
        st.plotly_chart(fig2, use_container_width=True)

# ════════════════════════════════════════════════════════════
# 📅 7 GÜNLÜK
# ════════════════════════════════════════════════════════════
with tab_7gun:
    st.markdown("### 📅 7 Günlük Tahmin")
    d = v1["daily"]
    cols7 = st.columns(7)
    for i,col in enumerate(cols7):
        tarih = datetime.strptime(d["time"][i],"%Y-%m-%d")
        gun   = "Bugün" if i==0 else tarih.strftime("%a")
        ikon,acik = hk(d["weathercode"][i])
        with col:
            st.markdown(f"""
            <div class="gun-karti">
              <div class="gun-adi">{gun}<br>{tarih.strftime('%d/%m')}</div>
              <div class="gun-ikon">{ikon}</div>
              <div class="gun-max">{d['temperature_2m_max'][i]:.0f}°</div>
              <div class="gun-min">{d['temperature_2m_min'][i]:.0f}°</div>
              <div class="gun-alt">💧{d['precipitation_sum'][i]:.1f}mm
              %{d['precipitation_probability_max'][i]:.0f}</div>
              <div class="gun-alt">💨{d['windspeed_10m_max'][i]:.0f}km/s</div>
            </div>""", unsafe_allow_html=True)

    # 7 günlük sıcaklık grafiği
    st.markdown("---")
    tarih_lbls = [datetime.strptime(d["time"][i],"%Y-%m-%d").strftime("%d %b") for i in range(7)]
    fig_7 = go.Figure()
    fig_7.add_trace(go.Scatter(x=tarih_lbls, y=d["temperature_2m_max"][:7],
        name="Max °C", mode="lines+markers", line=dict(color="#ff7043",width=3),
        fill="tozeroy", fillcolor="rgba(255,112,67,.08)"))
    fig_7.add_trace(go.Scatter(x=tarih_lbls, y=d["temperature_2m_min"][:7],
        name="Min °C", mode="lines+markers", line=dict(color="#42a5f5",width=3),
        fill="tozeroy", fillcolor="rgba(66,165,245,.08)"))
    fig_7.add_trace(go.Bar(x=tarih_lbls, y=d["precipitation_sum"][:7],
        name="Yağış mm", yaxis="y2", marker_color="rgba(100,180,255,.6)"))
    fig_7.update_layout(
        title="7 Günlük Sıcaklık & Yağış",
        yaxis=dict(title="°C", gridcolor="rgba(0,0,0,.05)"),
        yaxis2=dict(title="mm", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h",y=1.1),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=40,b=0), hovermode="x unified",
        xaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig_7, use_container_width=True)

# ════════════════════════════════════════════════════════════
# ⏰ SAATLİK TABLO
# ════════════════════════════════════════════════════════════
with tab_saatlik:
    st.markdown("### ⏰ Saatlik Detaylı Veri Tablosu")

    h = v1["hourly"]
    d = v1["daily"]

    # Gün seçimi
    gunler = [datetime.strptime(t,"%Y-%m-%d").strftime("%d %B %Y (%A)")
              for t in v1["daily"]["time"][:7]]
    secili_gun_idx = st.selectbox("📅 Gün seç", range(7),
                                   format_func=lambda i: gunler[i])
    secili_gun = v1["daily"]["time"][secili_gun_idx]

    idx_list = [i for i,t in enumerate(h["time"]) if t.startswith(secili_gun)]

    rows = []
    for i in idx_list:
        ikon,acik = hk(h["weathercode"][i])
        rows.append({
            "Saat":          h["time"][i][11:16],
            "Durum":         f"{ikon} {acik}",
            "Sıcaklık (°C)": h["temperature_2m"][i],
            "Hissedilen":    h["apparent_temperature"][i],
            "Nem (%)":       h["relativehumidity_2m"][i],
            "Çiy Noktası":   h["dewpoint_2m"][i],
            "Basınç (hPa)":  h["pressure_msl"][i],
            "Bulut (%)":     h["cloudcover"][i],
            "Görüş (km)":    round(h["visibility"][i]/1000,1) if h["visibility"][i] else 0,
            "Yağış (mm)":    h["precipitation"][i],
            "Yağış Olas (%)":h["precipitation_probability"][i],
            "Kar (cm)":      h["snowfall"][i],
            "Rüzgar km/s":   h["windspeed_10m"][i],
            "Rüzgar Yönü":   ryon(h["winddirection_10m"][i]),
            "Gusto km/s":    h["windgusts_10m"][i],
            "UV":            h["uv_index"][i],
        })

    df_saat = pd.DataFrame(rows)

    def renk_sicak(val):
        try:
            t = float(val)
            if t < 0:   return "background-color:#bbdefb;color:#0d47a1"
            if t < 10:  return "background-color:#e0f7fa;color:#006064"
            if t < 20:  return "background-color:#e8f5e9;color:#1b5e20"
            if t < 30:  return "background-color:#fff9c4;color:#f57f17"
            return "background-color:#ffccbc;color:#bf360c"
        except: return ""

    def renk_nem(val):
        try:
            n = float(val)
            if n < 40:  return "background-color:#fff9c4"
            if n < 60:  return "background-color:#e8f5e9"
            if n < 80:  return "background-color:#e3f2fd"
            return "background-color:#bbdefb"
        except: return ""

    def renk_yagis2(val):
        try:
            y = float(val)
            if y == 0:  return ""
            if y < 2:   return "background-color:#e3f2fd"
            if y < 10:  return "background-color:#90caf9"
            return "background-color:#42a5f5;color:white"
        except: return ""

    styled = df_saat.style\
        .applymap(renk_sicak,  subset=["Sıcaklık (°C)","Hissedilen"])\
        .applymap(renk_nem,    subset=["Nem (%)"])\
        .applymap(renk_yagis2, subset=["Yağış (mm)"])\
        .format(precision=1)

    st.dataframe(styled, use_container_width=True, height=500)

    # Saatlik grafik
    st.markdown("---")
    sg1, sg2 = st.columns(2)
    with sg1:
        fig_sh = go.Figure()
        fig_sh.add_trace(go.Scatter(
            x=df_saat["Saat"], y=df_saat["Sıcaklık (°C)"],
            name="Sıcaklık", line=dict(color="#ff7043",width=2.5),
            fill="tozeroy", fillcolor="rgba(255,112,67,.08)"))
        fig_sh.add_trace(go.Scatter(
            x=df_saat["Saat"], y=df_saat["Hissedilen"],
            name="Hissedilen", line=dict(color="#ffa726",width=2,dash="dot")))
        fig_sh.update_layout(title="Saatlik Sıcaklık",height=240,
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            xaxis=dict(showgrid=False,tickangle=-45),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
            legend=dict(orientation="h",y=1.15))
        st.plotly_chart(fig_sh, use_container_width=True)

    with sg2:
        fig_ruz = go.Figure()
        fig_ruz.add_trace(go.Bar(
            x=df_saat["Saat"], y=df_saat["Rüzgar km/s"],
            name="Rüzgar", marker_color="#42a5f5"))
        fig_ruz.add_trace(go.Scatter(
            x=df_saat["Saat"], y=df_saat["Gusto km/s"],
            name="Gusto", line=dict(color="#ef5350",width=2,dash="dot")))
        fig_ruz.update_layout(title="Rüzgar & Gusto",height=240,
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            xaxis=dict(showgrid=False,tickangle=-45),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
            legend=dict(orientation="h",y=1.15))
        st.plotly_chart(fig_ruz, use_container_width=True)

    sg3, sg4 = st.columns(2)
    with sg3:
        fig_bs = go.Figure(go.Scatter(
            x=df_saat["Saat"], y=df_saat["Basınç (hPa)"],
            line=dict(color="#7e57c2",width=2.5),
            fill="tozeroy", fillcolor="rgba(126,87,194,.08)"))
        fig_bs.update_layout(title="Basınç (hPa)",height=220,
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            xaxis=dict(showgrid=False,tickangle=-45),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"))
        st.plotly_chart(fig_bs, use_container_width=True)

    with sg4:
        fig_bl = go.Figure()
        fig_bl.add_trace(go.Bar(
            x=df_saat["Saat"], y=df_saat["Bulut (%)"],
            marker_color="rgba(120,144,156,.7)", name="Bulut"))
        fig_bl.add_trace(go.Scatter(
            x=df_saat["Saat"], y=df_saat["Nem (%)"],
            name="Nem", line=dict(color="#26c6da",width=2), yaxis="y"))
        fig_bl.update_layout(title="Bulut & Nem (%)",height=220,
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            xaxis=dict(showgrid=False,tickangle=-45),
            yaxis=dict(range=[0,100],gridcolor="rgba(0,0,0,.05)"),
            legend=dict(orientation="h",y=1.15))
        st.plotly_chart(fig_bl, use_container_width=True)

# ════════════════════════════════════════════════════════════
# 📆 16 GÜNLÜK TABLO
# ════════════════════════════════════════════════════════════
with tab_16gun:
    st.markdown("### 📆 16 Günlük Tahmin Tablosu")
    d = v1["daily"]
    n = len(d["time"])

    gun_rows = []
    for i in range(n):
        tarih  = datetime.strptime(d["time"][i],"%Y-%m-%d")
        ikon,acik = hk(d["weathercode"][i])
        gun_rows.append({
            "Tarih":         tarih.strftime("%d.%m.%Y"),
            "Gün":           "Bugün" if i==0 else tarih.strftime("%A"),
            "Durum":         f"{ikon} {acik}",
            "Max (°C)":      d["temperature_2m_max"][i],
            "Min (°C)":      d["temperature_2m_min"][i],
            "Hiss. Max":     d["apparent_temperature_max"][i],
            "Hiss. Min":     d["apparent_temperature_min"][i],
            "Yağış (mm)":    d["precipitation_sum"][i],
            "Yağış Saat":    d["precipitation_hours"][i],
            "Yağış Olas (%)":d["precipitation_probability_max"][i],
            "Kar (mm)":      d["snowfall_sum"][i],
            "Rüzgar km/s":   d["windspeed_10m_max"][i],
            "Gusto km/s":    d["windgusts_10m_max"][i],
            "Rüzgar Yönü":   ryon(d["winddirection_10m_dominant"][i]),
            "UV Max":        d["uv_index_max"][i],
            "Gün Doğumu":    d["sunrise"][i][11:16],
            "Gün Batımı":    d["sunset"][i][11:16],
        })

    df_gun = pd.DataFrame(gun_rows)

    def renk_max(val):
        try:
            t=float(val)
            if t<0:   return "background-color:#bbdefb;color:#0d47a1"
            if t<10:  return "background-color:#e0f7fa"
            if t<20:  return "background-color:#e8f5e9"
            if t<30:  return "background-color:#fff9c4"
            return "background-color:#ffccbc"
        except: return ""

    styled_gun = df_gun.style\
        .applymap(renk_max, subset=["Max (°C)","Min (°C)","Hiss. Max","Hiss. Min"])\
        .applymap(renk_yagis2 if True else lambda x:x, subset=["Yağış (mm)"])\
        .format(precision=1)

    st.dataframe(styled_gun, use_container_width=True, height=580)

# ════════════════════════════════════════════════════════════
# 📈 GRAFİKLER
# ════════════════════════════════════════════════════════════
with tab_grafik:
    st.markdown("### 📈 Detaylı Grafikler")

    d  = v1["daily"]
    h  = v1["hourly"]
    n  = len(d["time"])
    lbls = [datetime.strptime(d["time"][i],"%Y-%m-%d").strftime("%d %b") for i in range(n)]

    # 16 günlük sıcaklık
    fig_g1 = go.Figure()
    fig_g1.add_trace(go.Scatter(x=lbls, y=d["temperature_2m_max"],
        name="Max", line=dict(color="#ff7043",width=2.5),
        fill="tozeroy", fillcolor="rgba(255,112,67,.07)"))
    fig_g1.add_trace(go.Scatter(x=lbls, y=d["temperature_2m_min"],
        name="Min", line=dict(color="#42a5f5",width=2.5),
        fill="tozeroy", fillcolor="rgba(66,165,245,.07)"))
    fig_g1.add_trace(go.Scatter(x=lbls, y=d["apparent_temperature_max"],
        name="Hiss. Max", line=dict(color="#ffa726",width=1.5,dash="dot")))
    fig_g1.update_layout(title="16 Günlük Sıcaklık",height=280,
        plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=35,b=0),hovermode="x unified",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
        legend=dict(orientation="h",y=1.12))
    st.plotly_chart(fig_g1, use_container_width=True)

    gc1, gc2 = st.columns(2)
    with gc1:
        # Yağış
        fig_g2 = go.Figure()
        fig_g2.add_trace(go.Bar(x=lbls, y=d["precipitation_sum"],
            name="Yağış mm", marker_color=[
                "#42a5f5" if y<5 else "#1565c0" if y<15 else "#0d47a1"
                for y in d["precipitation_sum"]],
            text=[f"{y:.1f}" for y in d["precipitation_sum"]],
            textposition="outside"))
        fig_g2.add_trace(go.Scatter(x=lbls, y=d["precipitation_probability_max"],
            name="Olas. %", yaxis="y2",
            line=dict(color="#ff8f00",width=2,dash="dot"), mode="lines+markers"))
        fig_g2.update_layout(title="Yağış & Olasılık",height=280,
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            yaxis=dict(title="mm",gridcolor="rgba(0,0,0,.05)"),
            yaxis2=dict(title="%",overlaying="y",side="right",range=[0,100],showgrid=False),
            legend=dict(orientation="h",y=1.15),xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g2, use_container_width=True)

    with gc2:
        # Rüzgar
        fig_g3 = go.Figure()
        fig_g3.add_trace(go.Bar(x=lbls, y=d["windspeed_10m_max"],
            name="Rüzgar", marker_color="rgba(66,165,245,.8)"))
        fig_g3.add_trace(go.Scatter(x=lbls, y=d["windgusts_10m_max"],
            name="Gusto", line=dict(color="#ef5350",width=2)))
        fig_g3.update_layout(title="Rüzgar & Gusto (km/s)",height=280,
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
            legend=dict(orientation="h",y=1.15),xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g3, use_container_width=True)

    # UV & Işınım
    gc3, gc4 = st.columns(2)
    with gc3:
        uv_renk = ["#66bb6a" if u<3 else "#ffa726" if u<6 else
                   "#ef5350" if u<8 else "#ab47bc" for u in d["uv_index_max"]]
        fig_g4 = go.Figure(go.Bar(x=lbls, y=d["uv_index_max"],
            marker_color=uv_renk,
            text=[f"{u:.0f}" for u in d["uv_index_max"]],
            textposition="outside"))
        fig_g4.update_layout(title="UV İndeksi",height=240,
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
            xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g4, use_container_width=True)
        st.caption("🟢<3  🟡3-5  🟠6-7  🔴8-10  🟣11+")

    with gc4:
        fig_g5 = go.Figure(go.Bar(x=lbls, y=d["shortwave_radiation_sum"],
            marker_color="rgba(255,193,7,.8)",
            text=[f"{r:.0f}" for r in d["shortwave_radiation_sum"]],
            textposition="outside"))
        fig_g5.update_layout(title="Güneş Işınımı (MJ/m²)",height=240,
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
            xaxis=dict(showgrid=False))
        st.plotly_chart(fig_g5, use_container_width=True)

# ════════════════════════════════════════════════════════════
# 🔄 KARŞILAŞTIRMA
# ════════════════════════════════════════════════════════════
if tab_kars and v2:
    with tab_kars:
        st.markdown(f"### 🔄 {sehir1} vs {sehir2}")

        d1 = v1["daily"]; d2 = v2["daily"]
        n  = min(len(d1["time"]), len(d2["time"]), 7)
        lbls7 = [datetime.strptime(d1["time"][i],"%Y-%m-%d").strftime("%d %b") for i in range(n)]

        kc1, kc2 = st.columns(2)
        # Sıcaklık karşılaştırma
        with kc1:
            fig_k1 = go.Figure()
            fig_k1.add_trace(go.Scatter(x=lbls7, y=d1["temperature_2m_max"][:n],
                name=f"{sehir1} Max", line=dict(color="#ff7043",width=2.5)))
            fig_k1.add_trace(go.Scatter(x=lbls7, y=d2["temperature_2m_max"][:n],
                name=f"{sehir2} Max", line=dict(color="#ff7043",width=2.5,dash="dot")))
            fig_k1.add_trace(go.Scatter(x=lbls7, y=d1["temperature_2m_min"][:n],
                name=f"{sehir1} Min", line=dict(color="#42a5f5",width=2.5)))
            fig_k1.add_trace(go.Scatter(x=lbls7, y=d2["temperature_2m_min"][:n],
                name=f"{sehir2} Min", line=dict(color="#42a5f5",width=2.5,dash="dot")))
            fig_k1.update_layout(title="Sıcaklık Karşılaştırma",height=300,
                plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0),hovermode="x unified",
                xaxis=dict(showgrid=False),yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                legend=dict(orientation="h",y=1.25,font=dict(size=10)))
            st.plotly_chart(fig_k1, use_container_width=True)

        with kc2:
            fig_k2 = go.Figure()
            fig_k2.add_trace(go.Bar(x=lbls7, y=d1["precipitation_sum"][:n],
                name=sehir1, marker_color="rgba(66,165,245,.7)"))
            fig_k2.add_trace(go.Bar(x=lbls7, y=d2["precipitation_sum"][:n],
                name=sehir2, marker_color="rgba(239,83,80,.7)"))
            fig_k2.update_layout(title="Yağış Karşılaştırma (mm)",height=300,
                plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0),barmode="group",
                xaxis=dict(showgrid=False),yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                legend=dict(orientation="h",y=1.15))
            st.plotly_chart(fig_k2, use_container_width=True)

        # Özet tablo
        st.markdown("### 📊 7 Günlük Özet Karşılaştırma")
        ozet = []
        for i in range(n):
            ozet.append({
                "Tarih": datetime.strptime(d1["time"][i],"%Y-%m-%d").strftime("%d %b"),
                f"{sehir1} Max": f"{d1['temperature_2m_max'][i]:.0f}°C",
                f"{sehir2} Max": f"{d2['temperature_2m_max'][i]:.0f}°C",
                f"{sehir1} Yağış": f"{d1['precipitation_sum'][i]:.1f}mm",
                f"{sehir2} Yağış": f"{d2['precipitation_sum'][i]:.1f}mm",
                f"{sehir1} Rüzgar": f"{d1['windspeed_10m_max'][i]:.0f}km/s",
                f"{sehir2} Rüzgar": f"{d2['windspeed_10m_max'][i]:.0f}km/s",
            })
        st.dataframe(pd.DataFrame(ozet), use_container_width=True)

# ── Alt bilgi ──────────────────────────────────────────────────────────────────
st.divider()
st.caption("🌍 Veri: Open-Meteo API (ücretsiz, kayıt gerektirmez) • "
           "Nominatim/OpenStreetMap • Her 30dk güncellenir")
