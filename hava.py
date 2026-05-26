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
OW_IKONLAR = {
    "01d":"☀️","01n":"🌙","02d":"🌤","02n":"🌤",
    "03d":"⛅","03n":"⛅","04d":"☁️","04n":"☁️",
    "09d":"🌧","09n":"🌧","10d":"🌦","10n":"🌦",
    "11d":"⛈","11n":"⛈","13d":"❄️","13n":"❄️",
    "50d":"🌫","50n":"🌫",
}
def ikon(code): return OW_IKONLAR.get(code, "🌡")

RYON = ["K","KKD","KD","DKD","D","DGD","GD","GGD","G","GGB","GB","BGB","B","BKB","KB","KKB"]
def ryon(deg): return RYON[round(deg/22.5)%16]

def uv_yorum(uv):
    if uv is None: return "—"
    if uv < 3:  return "🟢 Düşük"
    if uv < 6:  return "🟡 Orta"
    if uv < 8:  return "🟠 Yüksek"
    if uv < 11: return "🔴 Çok Yüksek"
    return "🟣 Aşırı"

def hiz_yon(speed, deg): return f"{speed:.0f} km/s {ryon(deg)}"

# ── API ───────────────────────────────────────────────────────────────────────
BASE = "https://api.openweathermap.org"

@st.cache_data(ttl=3600)
def sehir_ara(q, key):
    try:
        r = requests.get(f"{BASE}/geo/1.0/direct",
            params={"q":q,"limit":5,"appid":key}, timeout=10)
        return r.json()
    except Exception as e:
        st.error(f"Geocoding hatası: {e}"); return []

@st.cache_data(ttl=1800)
def anlik_hava(lat, lon, key):
    try:
        r = requests.get(f"{BASE}/data/2.5/weather",
            params={"lat":lat,"lon":lon,"appid":key,
                    "units":"metric","lang":"tr"}, timeout=10)
        return r.json()
    except Exception as e:
        st.error(f"Anlık veri hatası: {e}"); return None

@st.cache_data(ttl=1800)
def tahmin_3saatlik(lat, lon, key):
    """5 günlük / 3 saatlik tahmin (ücretsiz)"""
    try:
        r = requests.get(f"{BASE}/data/2.5/forecast",
            params={"lat":lat,"lon":lon,"appid":key,
                    "units":"metric","lang":"tr","cnt":40}, timeout=10)
        return r.json()
    except Exception as e:
        st.error(f"Tahmin hatası: {e}"); return None

@st.cache_data(ttl=1800)
def onecall(lat, lon, key):
    """One Call API 3.0 — saatlik + 8 günlük (abonelik gerekebilir)"""
    try:
        r = requests.get(f"{BASE}/data/3.0/onecall",
            params={"lat":lat,"lon":lon,"appid":key,
                    "units":"metric","lang":"tr",
                    "exclude":"minutely,alerts"}, timeout=10)
        d = r.json()
        return d if "daily" in d else None
    except:
        return None

def gunluk_ozet(forecast_json):
    """3 saatlik veriyi günlük özetlere dönüştür"""
    if not forecast_json or "list" not in forecast_json:
        return []
    gunler = {}
    for item in forecast_json["list"]:
        gun = item["dt_txt"][:10]
        t   = item["main"]["temp"]
        if gun not in gunler:
            gunler[gun] = {
                "max": t, "min": t,
                "icon": item["weather"][0]["icon"],
                "desc": item["weather"][0]["description"],
                "yagis": item.get("rain",{}).get("3h",0) + item.get("snow",{}).get("3h",0),
                "nem": item["main"]["humidity"],
                "ruzgar": item["wind"]["speed"]*3.6,
                "samples": 1,
            }
        else:
            gunler[gun]["max"]    = max(gunler[gun]["max"], t)
            gunler[gun]["min"]    = min(gunler[gun]["min"], t)
            gunler[gun]["yagis"] += item.get("rain",{}).get("3h",0) + item.get("snow",{}).get("3h",0)
            gunler[gun]["nem"]   += item["main"]["humidity"]
            gunler[gun]["ruzgar"]+= item["wind"]["speed"]*3.6
            gunler[gun]["samples"]+= 1
    # Ortalama
    for g in gunler.values():
        g["nem"]    = round(g["nem"]    / g["samples"])
        g["ruzgar"] = round(g["ruzgar"] / g["samples"], 1)
    return [(gun, val) for gun, val in gunler.items()]

# ── Session state ──────────────────────────────────────────────────────────────
for k,v in [("konum1",None),("konum2",None),("tetik1",False),("tetik2",False),
             ("ara1",""),("ara2","")]:
    if k not in st.session_state: st.session_state[k] = v

# ── Başlık & API Key ──────────────────────────────────────────────────────────
st.markdown("# 🌤 Hava Durumu Dashboard")

with st.sidebar:
    st.markdown("### ⚙️ Ayarlar")
    api_key = st.text_input("🔑 OpenWeather API Key",
                             type="password", placeholder="xxxxxxxxxxxxx")
    st.caption("Ücretsiz key: openweathermap.org/api")
    st.divider()
    st.markdown("**Hızlı Şehirler**")
    hizli = ["İstanbul","Ankara","İzmir","Antalya",
             "Bursa","London","New York","Paris","Tokyo","Dubai"]
    for s in hizli:
        if st.button(s, key=f"hz_{s}", use_container_width=True):
            st.session_state.ara1 = s
            st.session_state.tetik1 = True
            st.rerun()

if not api_key:
    st.info("👈 Sol panelden OpenWeather API key'ini gir.")
    st.stop()

# ── Arama ──────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([3,3,1])
with c1:
    girdi1 = st.text_input("Şehir 1", placeholder="İstanbul, Ankara...",
                            value=st.session_state.ara1, key="g1")
with c2:
    girdi2 = st.text_input("Şehir 2 (Karşılaştırma — opsiyonel)",
                            placeholder="London, Berlin...",
                            value=st.session_state.ara2, key="g2")
with c3:
    ara_btn = st.button("🔍 Ara", type="primary", use_container_width=True)

if ara_btn:
    if girdi1: st.session_state.ara1=girdi1; st.session_state.tetik1=True; st.session_state.konum1=None
    if girdi2: st.session_state.ara2=girdi2; st.session_state.tetik2=True; st.session_state.konum2=None
    st.rerun()

# Koordinat çöz
for ara_k, tetik_k, konum_k in [("ara1","tetik1","konum1"),("ara2","tetik2","konum2")]:
    if st.session_state[tetik_k] and st.session_state[ara_k]:
        with st.spinner(f"{st.session_state[ara_k]} aranıyor..."):
            sonuclar = sehir_ara(st.session_state[ara_k], api_key)
        if sonuclar:
            s = sonuclar[0]
            ad = s.get("local_names",{}).get("tr") or s.get("name","")
            ulke = s.get("country","")
            st.session_state[konum_k] = (float(s["lat"]),float(s["lon"]),f"{ad}, {ulke}")
        else:
            st.error(f"'{st.session_state[ara_k]}' bulunamadı.")
        st.session_state[tetik_k] = False

if not st.session_state.konum1:
    st.info("👆 Şehir ara veya sol panelden hızlı seçim yap.")
    st.stop()

# ── Veri Çek ──────────────────────────────────────────────────────────────────
lat1,lon1,sehir1 = st.session_state.konum1

with st.spinner("Veri alınıyor..."):
    anlik1   = anlik_hava(lat1, lon1, api_key)
    tahmin1  = tahmin_3saatlik(lat1, lon1, api_key)
    oc1      = onecall(lat1, lon1, api_key)   # None olabilir

if not anlik1: st.stop()

v2_anlik = v2_tahmin = v2_oc = None
sehir2 = ""
if st.session_state.konum2:
    lat2,lon2,sehir2 = st.session_state.konum2
    with st.spinner(f"{sehir2} verisi alınıyor..."):
        v2_anlik  = anlik_hava(lat2, lon2, api_key)
        v2_tahmin = tahmin_3saatlik(lat2, lon2, api_key)
        v2_oc     = onecall(lat2, lon2, api_key)

gunluk1  = gunluk_ozet(tahmin1)
gunluk2  = gunluk_ozet(v2_tahmin) if v2_tahmin else []

# ── Sekmeler ──────────────────────────────────────────────────────────────────
tab_listesi = ["🌡 Anlık","📅 Günlük Tahmin","⏰ Saatlik Tablo","📈 Grafikler"]
if sehir2: tab_listesi.append("🔄 Karşılaştırma")
tabs = st.tabs(tab_listesi)
tab_anlik, tab_gunluk, tab_saatlik, tab_grafik = tabs[:4]
tab_kars = tabs[4] if len(tabs) > 4 else None

# ══════════════════════════════════════════════════════════════
# 🌡 ANLIK
# ══════════════════════════════════════════════════════════════
with tab_anlik:
    w = anlik1
    ic = ikon(w["weather"][0]["icon"])
    ac = w["weather"][0]["description"].capitalize()
    gd = datetime.fromtimestamp(w["sys"]["sunrise"]).strftime("%H:%M")
    gb = datetime.fromtimestamp(w["sys"]["sunset"]).strftime("%H:%M")

    col_a, col_b = st.columns([1.2, 1])
    with col_a:
        st.markdown(f"""
        <div class="anlik-kart">
          <div style="font-size:.85rem;opacity:.65">{datetime.now().strftime('%d %B %Y  %H:%M')}</div>
          <div style="font-size:1.3rem;font-weight:700;margin:4px 0">📍 {sehir1}</div>
          <div style="display:flex;align-items:center;gap:20px;margin:14px 0">
            <div style="font-size:3.5rem">{ic}</div>
            <div>
              <div style="font-size:4rem;font-weight:800;line-height:1">{w['main']['temp']:.0f}°C</div>
              <div style="opacity:.75;font-style:italic">{ac}</div>
              <div style="font-size:.85rem;opacity:.7">Hissedilen {w['main']['feels_like']:.0f}°C</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
            <div class="m-kutu">
              <div class="m-lbl">💨 Rüzgar</div>
              <div class="m-val">{w['wind']['speed']*3.6:.0f} km/s {ryon(w['wind'].get('deg',0))}</div>
            </div>
            <div class="m-kutu">
              <div class="m-lbl">💧 Nem</div>
              <div class="m-val">%{w['main']['humidity']}</div>
            </div>
            <div class="m-kutu">
              <div class="m-lbl">🌡 Max / Min</div>
              <div class="m-val">{w['main']['temp_max']:.0f}° / {w['main']['temp_min']:.0f}°</div>
            </div>
            <div class="m-kutu">
              <div class="m-lbl">🌬 Basınç</div>
              <div class="m-val">{w['main']['pressure']} hPa</div>
            </div>
            <div class="m-kutu">
              <div class="m-lbl">👁 Görüş</div>
              <div class="m-val">{w.get('visibility',0)//1000} km</div>
            </div>
            <div class="m-kutu">
              <div class="m-lbl">🌅 Gün D/B</div>
              <div class="m-val">{gd} / {gb}</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    with col_b:
        # One Call varsa UV ve günlük detay
        if oc1 and "current" in oc1:
            cur = oc1["current"]
            st.markdown("### Ek Detaylar (One Call)")
            m1,m2 = st.columns(2)
            with m1:
                st.metric("☀️ UV İndeksi",    uv_yorum(cur.get("uvi")))
                st.metric("☁️ Bulut",          f"%{cur.get('clouds',0)}")
                st.metric("💧 Çiy Noktası",    f"{cur.get('dew_point',0):.1f}°C")
            with m2:
                st.metric("👁 Görüş",          f"{cur.get('visibility',0)//1000} km")
                st.metric("💨 Gusto",          f"{cur.get('wind_gust',0)*3.6:.0f} km/s")
                st.metric("🌧 Son 1s Yağış",  f"{cur.get('rain',{}).get('1h',0):.1f} mm")
        else:
            st.info("One Call API verisi yok (ücretsiz planlarda kısıtlı olabilir). "
                    "Temel veriler anlık sekmede görünüyor.")

        # Son 24 saatin saatlik tahmini (3h forecast'tan)
        if tahmin1 and "list" in tahmin1:
            st.markdown("### Yakın Tahmin (3 Saatlik)")
            items = tahmin1["list"][:8]
            df_kisa = pd.DataFrame({
                "Saat":    [datetime.fromtimestamp(x["dt"]).strftime("%H:%M") for x in items],
                "°C":      [round(x["main"]["temp"],1) for x in items],
                "Durum":   [f"{ikon(x['weather'][0]['icon'])} {x['weather'][0]['description']}" for x in items],
                "Nem %":   [x["main"]["humidity"] for x in items],
                "Yağış mm":[round(x.get("rain",{}).get("3h",0)+x.get("snow",{}).get("3h",0),1) for x in items],
            })
            st.dataframe(df_kisa, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# 📅 GÜNLÜK TAHMİN
# ══════════════════════════════════════════════════════════════
with tab_gunluk:
    st.markdown("### 📅 Günlük Tahmin")

    # One Call varsa 8 günlük, yoksa 3h özetinden
    if oc1 and "daily" in oc1:
        st.success("✅ One Call API — 8 günlük tahmin")
        daily = oc1["daily"]
        n = len(daily)
        cols = st.columns(min(n, 7))
        for i, col in enumerate(cols):
            d  = daily[i]
            dt = datetime.fromtimestamp(d["dt"])
            ic = ikon(d["weather"][0]["icon"])
            ac = d["weather"][0]["description"]
            with col:
                st.markdown(f"""
                <div class="gun-karti">
                  <div class="gun-adi">{"Bugün" if i==0 else dt.strftime("%a")}<br>{dt.strftime("%d/%m")}</div>
                  <div class="gun-ikon">{ic}</div>
                  <div class="gun-max">{d['temp']['max']:.0f}°</div>
                  <div class="gun-min">{d['temp']['min']:.0f}°</div>
                  <div class="gun-alt">💧{d.get('rain',0)+d.get('snow',0):.1f}mm  {d.get('pop',0)*100:.0f}%</div>
                  <div class="gun-alt">💨{d['wind_speed']*3.6:.0f}km/s  UV:{d.get('uvi',0):.0f}</div>
                </div>""", unsafe_allow_html=True)

        # 8 günlük tablo
        st.markdown("---")
        rows = []
        for d in daily:
            dt = datetime.fromtimestamp(d["dt"])
            ic = ikon(d["weather"][0]["icon"])
            rows.append({
                "Tarih":       dt.strftime("%d.%m.%Y"),
                "Gün":         dt.strftime("%A"),
                "Durum":       f"{ic} {d['weather'][0]['description']}",
                "Max (°C)":    d["temp"]["max"],
                "Min (°C)":    d["temp"]["min"],
                "Hiss. Max":   d["feels_like"]["day"],
                "Hiss. Gece":  d["feels_like"]["night"],
                "Yağış mm":    round(d.get("rain",0)+d.get("snow",0),1),
                "Yağış %":     round(d.get("pop",0)*100),
                "Nem %":       d["humidity"],
                "Rüzgar":      f"{d['wind_speed']*3.6:.0f} km/s {ryon(d.get('wind_deg',0))}",
                "Gusto":       f"{d.get('wind_gust',0)*3.6:.0f} km/s",
                "UV":          d.get("uvi",0),
                "Gün D.":      datetime.fromtimestamp(d["sunrise"]).strftime("%H:%M"),
                "Gün B.":      datetime.fromtimestamp(d["sunset"]).strftime("%H:%M"),
            })
        df_daily = pd.DataFrame(rows)

        def renk_max(val):
            try:
                t = float(val)
                if t<0:  return "background-color:#bbdefb;color:#0d47a1"
                if t<10: return "background-color:#e0f7fa"
                if t<20: return "background-color:#e8f5e9"
                if t<30: return "background-color:#fff9c4"
                return "background-color:#ffccbc"
            except: return ""

        styled_d = df_daily.style.map(renk_max, subset=["Max (°C)","Min (°C)"])
        st.dataframe(styled_d, use_container_width=True, hide_index=True)

    else:
        st.info("ℹ️ One Call API yok — 3 saatlik veriden günlük özet gösteriliyor (5 gün)")
        cols = st.columns(min(len(gunluk1), 5))
        for i, (tarih, d) in enumerate(gunluk1[:5]):
            dt = datetime.strptime(tarih,"%Y-%m-%d")
            ic = ikon(d["icon"])
            with cols[i]:
                st.markdown(f"""
                <div class="gun-karti">
                  <div class="gun-adi">{"Bugün" if i==0 else dt.strftime("%a")}<br>{dt.strftime("%d/%m")}</div>
                  <div class="gun-ikon">{ic}</div>
                  <div class="gun-max">{d['max']:.0f}°</div>
                  <div class="gun-min">{d['min']:.0f}°</div>
                  <div class="gun-alt">💧{d['yagis']:.1f}mm</div>
                  <div class="gun-alt">💨{d['ruzgar']:.0f}km/s</div>
                </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ⏰ SAATLİK TABLO
# ══════════════════════════════════════════════════════════════
with tab_saatlik:
    st.markdown("### ⏰ Saatlik Veri Tablosu")

    kaynak = "One Call API (saatlik)" if oc1 and "hourly" in oc1 else "3 Saatlik Tahmin"
    st.caption(f"Kaynak: {kaynak}")

    if oc1 and "hourly" in oc1:
        items = oc1["hourly"][:48]
        rows = []
        for x in items:
            dt = datetime.fromtimestamp(x["dt"])
            rows.append({
                "Tarih":        dt.strftime("%d.%m"),
                "Saat":         dt.strftime("%H:%M"),
                "Durum":        f"{ikon(x['weather'][0]['icon'])} {x['weather'][0]['description']}",
                "Sıcaklık":     x["temp"],
                "Hissedilen":   x["feels_like"],
                "Nem %":        x["humidity"],
                "Çiy Noktası":  x.get("dew_point",0),
                "Basınç hPa":   x["pressure"],
                "Bulut %":      x["clouds"],
                "Görüş km":     round(x.get("visibility",10000)/1000,1),
                "Rüzgar km/s":  round(x["wind_speed"]*3.6,1),
                "Yön":          ryon(x.get("wind_deg",0)),
                "Gusto km/s":   round(x.get("wind_gust",0)*3.6,1),
                "Yağış mm":     round(x.get("rain",{}).get("1h",0)+x.get("snow",{}).get("1h",0),2),
                "Yağış %":      round(x.get("pop",0)*100),
                "UV":           x.get("uvi",0),
            })
    else:
        items = tahmin1["list"] if tahmin1 and "list" in tahmin1 else []
        rows = []
        for x in items:
            dt = datetime.fromtimestamp(x["dt"])
            rows.append({
                "Tarih":        dt.strftime("%d.%m"),
                "Saat":         dt.strftime("%H:%M"),
                "Durum":        f"{ikon(x['weather'][0]['icon'])} {x['weather'][0]['description']}",
                "Sıcaklık":     x["main"]["temp"],
                "Hissedilen":   x["main"]["feels_like"],
                "Nem %":        x["main"]["humidity"],
                "Çiy Noktası":  "—",
                "Basınç hPa":   x["main"]["pressure"],
                "Bulut %":      x["clouds"]["all"],
                "Görüş km":     round(x.get("visibility",10000)/1000,1),
                "Rüzgar km/s":  round(x["wind"]["speed"]*3.6,1),
                "Yön":          ryon(x["wind"].get("deg",0)),
                "Gusto km/s":   round(x["wind"].get("gust",0)*3.6,1),
                "Yağış mm":     round(x.get("rain",{}).get("3h",0)+x.get("snow",{}).get("3h",0),2),
                "Yağış %":      round(x.get("pop",0)*100),
                "UV":           "—",
            })

    df_saat = pd.DataFrame(rows)

    def rs(val):  # renk sıcaklık
        try:
            t=float(val)
            if t<0:  return "background-color:#bbdefb;color:#0d47a1"
            if t<10: return "background-color:#e0f7fa"
            if t<20: return "background-color:#e8f5e9"
            if t<30: return "background-color:#fff9c4"
            return "background-color:#ffccbc"
        except: return ""

    def ry(val):  # renk yağış
        try:
            y=float(val)
            if y==0: return ""
            if y<2:  return "background-color:#e3f2fd"
            if y<10: return "background-color:#90caf9"
            return "background-color:#42a5f5;color:white"
        except: return ""

    def rn(val):  # renk nem
        try:
            n=float(val)
            if n<40: return "background-color:#fff9c4"
            if n<60: return "background-color:#e8f5e9"
            if n<80: return "background-color:#e3f2fd"
            return "background-color:#bbdefb"
        except: return ""

    styled_s = df_saat.style\
        .map(rs, subset=["Sıcaklık","Hissedilen"])\
        .map(ry, subset=["Yağış mm"])\
        .map(rn, subset=["Nem %"])\
        .format(precision=1)

    st.dataframe(styled_s, use_container_width=True, height=500)

# ══════════════════════════════════════════════════════════════
# 📈 GRAFİKLER
# ══════════════════════════════════════════════════════════════
with tab_grafik:
    st.markdown("### 📈 Grafikler")

    if tahmin1 and "list" in tahmin1:
        items = tahmin1["list"]
        zamanlar = [datetime.fromtimestamp(x["dt"]).strftime("%d/%m %H:%M") for x in items]
        sicaklik = [x["main"]["temp"]    for x in items]
        hissed   = [x["main"]["feels_like"] for x in items]
        nem      = [x["main"]["humidity"] for x in items]
        basınc   = [x["main"]["pressure"] for x in items]
        ruzgar   = [x["wind"]["speed"]*3.6 for x in items]
        gusto    = [x["wind"].get("gust",0)*3.6 for x in items]
        yagis    = [x.get("rain",{}).get("3h",0)+x.get("snow",{}).get("3h",0) for x in items]
        bulut    = [x["clouds"]["all"]   for x in items]

        # Sıcaklık
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=zamanlar, y=sicaklik, name="Sıcaklık",
            line=dict(color="#ff7043",width=2.5), fill="tozeroy",
            fillcolor="rgba(255,112,67,.08)"))
        fig1.add_trace(go.Scatter(x=zamanlar, y=hissed, name="Hissedilen",
            line=dict(color="#ffa726",width=2,dash="dot")))
        fig1.update_layout(title="Sıcaklık & Hissedilen (5 Gün)",height=260,
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=35,b=0),hovermode="x unified",
            xaxis=dict(showgrid=False,tickangle=-45,nticks=10),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
            legend=dict(orientation="h",y=1.15))
        st.plotly_chart(fig1, use_container_width=True)

        gc1, gc2 = st.columns(2)
        with gc1:
            # Yağış
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=zamanlar, y=yagis, name="Yağış mm",
                marker_color="rgba(66,165,245,.75)"))
            fig2.update_layout(title="Yağış (3 Saatlik)",height=240,
                plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0),
                xaxis=dict(showgrid=False,tickangle=-45,nticks=10),
                yaxis=dict(gridcolor="rgba(0,0,0,.05)"))
            st.plotly_chart(fig2, use_container_width=True)

        with gc2:
            # Rüzgar
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(x=zamanlar, y=ruzgar, name="Rüzgar",
                marker_color="rgba(66,165,245,.7)"))
            fig3.add_trace(go.Scatter(x=zamanlar, y=gusto, name="Gusto",
                line=dict(color="#ef5350",width=2)))
            fig3.update_layout(title="Rüzgar & Gusto (km/s)",height=240,
                plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0),
                xaxis=dict(showgrid=False,tickangle=-45,nticks=10),
                yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                legend=dict(orientation="h",y=1.15))
            st.plotly_chart(fig3, use_container_width=True)

        gc3, gc4 = st.columns(2)
        with gc3:
            # Basınç
            fig4 = go.Figure(go.Scatter(x=zamanlar, y=basınc,
                line=dict(color="#7e57c2",width=2.5),
                fill="tozeroy", fillcolor="rgba(126,87,194,.08)"))
            fig4.update_layout(title="Basınç (hPa)",height=220,
                plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0),
                xaxis=dict(showgrid=False,tickangle=-45,nticks=10),
                yaxis=dict(gridcolor="rgba(0,0,0,.05)"))
            st.plotly_chart(fig4, use_container_width=True)

        with gc4:
            # Nem & Bulut
            fig5 = go.Figure()
            fig5.add_trace(go.Scatter(x=zamanlar, y=nem,
                name="Nem %", line=dict(color="#26c6da",width=2),
                fill="tozeroy", fillcolor="rgba(38,198,218,.06)"))
            fig5.add_trace(go.Scatter(x=zamanlar, y=bulut,
                name="Bulut %", line=dict(color="#90a4ae",width=2,dash="dot")))
            fig5.update_layout(title="Nem & Bulut (%)",height=220,
                plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=35,b=0),
                xaxis=dict(showgrid=False,tickangle=-45,nticks=10),
                yaxis=dict(range=[0,100],gridcolor="rgba(0,0,0,.05)"),
                legend=dict(orientation="h",y=1.15))
            st.plotly_chart(fig5, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# 🔄 KARŞILAŞTIRMA
# ══════════════════════════════════════════════════════════════
if tab_kars and v2_anlik:
    with tab_kars:
        st.markdown(f"### 🔄 {sehir1} vs {sehir2}")

        k1, k2 = st.columns(2)
        for col, anlik, sehir in [(k1,anlik1,sehir1),(k2,v2_anlik,sehir2)]:
            with col:
                ic = ikon(anlik["weather"][0]["icon"])
                st.markdown(f"""
                <div class="anlik-kart" style="padding:18px 22px">
                  <div style="font-weight:700;font-size:1.1rem;margin-bottom:8px">📍 {sehir}</div>
                  <div style="font-size:2.5rem;font-weight:800">{ic} {anlik['main']['temp']:.0f}°C</div>
                  <div style="opacity:.75;margin-bottom:10px">{anlik['weather'][0]['description'].capitalize()}</div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
                    <div class="m-kutu"><div class="m-lbl">Hissedilen</div><div class="m-val">{anlik['main']['feels_like']:.0f}°C</div></div>
                    <div class="m-kutu"><div class="m-lbl">Nem</div><div class="m-val">%{anlik['main']['humidity']}</div></div>
                    <div class="m-kutu"><div class="m-lbl">Rüzgar</div><div class="m-val">{anlik['wind']['speed']*3.6:.0f} km/s</div></div>
                    <div class="m-kutu"><div class="m-lbl">Basınç</div><div class="m-val">{anlik['main']['pressure']} hPa</div></div>
                  </div>
                </div>""", unsafe_allow_html=True)

        # 5 günlük karşılaştırma grafikleri
        if gunluk1 and gunluk2:
            st.markdown("---")
            n = min(len(gunluk1), len(gunluk2), 5)
            lbls = [datetime.strptime(g[0],"%Y-%m-%d").strftime("%d %b") for g in gunluk1[:n]]

            fg1, fg2 = st.columns(2)
            with fg1:
                figk1 = go.Figure()
                figk1.add_trace(go.Scatter(x=lbls,
                    y=[g[1]["max"] for g in gunluk1[:n]],
                    name=f"{sehir1} Max", line=dict(color="#ff7043",width=2.5)))
                figk1.add_trace(go.Scatter(x=lbls,
                    y=[g[1]["max"] for g in gunluk2[:n]],
                    name=f"{sehir2} Max", line=dict(color="#ff7043",width=2.5,dash="dot")))
                figk1.add_trace(go.Scatter(x=lbls,
                    y=[g[1]["min"] for g in gunluk1[:n]],
                    name=f"{sehir1} Min", line=dict(color="#42a5f5",width=2.5)))
                figk1.add_trace(go.Scatter(x=lbls,
                    y=[g[1]["min"] for g in gunluk2[:n]],
                    name=f"{sehir2} Min", line=dict(color="#42a5f5",width=2.5,dash="dot")))
                figk1.update_layout(title="Sıcaklık Karşılaştırma",height=280,
                    plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0,r=0,t=35,b=0),hovermode="x unified",
                    xaxis=dict(showgrid=False),yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                    legend=dict(orientation="h",y=1.2,font=dict(size=10)))
                st.plotly_chart(figk1, use_container_width=True)

            with fg2:
                figk2 = go.Figure()
                figk2.add_trace(go.Bar(x=lbls,
                    y=[g[1]["yagis"] for g in gunluk1[:n]],
                    name=sehir1, marker_color="rgba(66,165,245,.7)"))
                figk2.add_trace(go.Bar(x=lbls,
                    y=[g[1]["yagis"] for g in gunluk2[:n]],
                    name=sehir2, marker_color="rgba(239,83,80,.7)"))
                figk2.update_layout(title="Yağış Karşılaştırma (mm)",height=280,
                    plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0,r=0,t=35,b=0),barmode="group",
                    xaxis=dict(showgrid=False),yaxis=dict(gridcolor="rgba(0,0,0,.05)"),
                    legend=dict(orientation="h",y=1.15))
                st.plotly_chart(figk2, use_container_width=True)

st.divider()
st.caption("🌍 OpenWeather API • Free tier: anlık + 5 günlük/3s • One Call 3.0: 8 günlük/saatlik")
