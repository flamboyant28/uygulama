import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from math import pow

st.set_page_config(
    page_title="Araç Simülasyonu",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700&family=Outfit:wght@400;600;700&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #0d0f14;
    color: #e8eaf0;
}

section[data-testid="stSidebar"] {
    background: #13161e;
    border-right: 1px solid #1f2330;
}

section[data-testid="stSidebar"] * {
    color: #c8cad8 !important;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    letter-spacing: -0.5px;
}

.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -1px;
    margin-bottom: 0.2rem;
}

.page-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: #555e7a;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 2rem;
}

.card {
    background: #13161e;
    border: 1px solid #1f2330;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}

.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #555e7a;
    margin-bottom: 1rem;
}

.metric-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.metric-box {
    flex: 1;
    min-width: 120px;
    background: #0d0f14;
    border: 1px solid #1f2330;
    border-radius: 10px;
    padding: 0.9rem 1rem;
}

.metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #555e7a;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.3rem;
}

.metric-val {
    font-family: 'Outfit', sans-serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: #ffffff;
    line-height: 1;
}

.metric-unit {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #555e7a;
    margin-top: 0.2rem;
}

.arac1-accent { color: #4fc3f7; }
.arac2-accent { color: #f06292; }

.vs-badge {
    background: #1f2330;
    border-radius: 50%;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 0.75rem;
    color: #555e7a;
    margin: auto;
}

.diff-better {
    color: #66bb6a;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 500;
}

.diff-worse {
    color: #ef5350;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 500;
}

.info-tag {
    display: inline-block;
    background: #1f2330;
    border-radius: 6px;
    padding: 0.25rem 0.6rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #8892aa;
    margin: 0.15rem;
}

.section-divider {
    border: none;
    border-top: 1px solid #1f2330;
    margin: 1.5rem 0;
}

.sidebar-section {
    font-family: 'Syne', sans-serif;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #555e7a !important;
    margin: 1.2rem 0 0.4rem 0;
}

/* Streamlit widget override */
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stSlider {
    background: #0d0f14 !important;
    border-color: #1f2330 !important;
    color: #e8eaf0 !important;
}

div[data-testid="stMetric"] {
    background: #13161e;
    border: 1px solid #1f2330;
    border-radius: 10px;
    padding: 0.8rem 1rem;
}
</style>
""", unsafe_allow_html=True)

# ─── VERİ TANIMLARI ─────────────────────────────────────────────────────────

motor_hacimleri_map = {
    "Motosiklet": [
        (50,   "50cc – Scooter",               6000),
        (125,  "125cc – Moped",                6500),
        (250,  "250cc – Kompakt Motosiklet",   7000),
        (500,  "500cc – Orta Motosiklet",      7500),
        (650,  "650cc – Naked / Roadster",     8000),
        (750,  "750cc – Orta-Büyük",           8200),
        (1000, "1000cc – Süper Spor Moto",     8500),
        (1200, "1200cc – Touring / Cruiser",   7800),
    ],
    "Sedan": [
        (800,  "800cc – Mikro Kompakt",        5500),
        (1000, "1000cc – Hatchback",           5800),
        (1200, "1200cc – Küçük (1.2 TSI/TCe)", 6000),
        (1300, "1300cc – Küçük Sedan",         6000),
        (1400, "1400cc – Alt-Orta",            6100),
        (1500, "1500cc – Kompakt (1.5T)",      6200),
        (1600, "1600cc – Sedan",               6200),
        (1800, "1800cc – Sportif Sedan",       6300),
        (2000, "2000cc – Orta Sınıf",          6500),
        (2500, "2500cc – Üst Orta",            6500),
    ],
    "SUV": [
        (1000, "1000cc – Mini Crossover",      5800),
        (1200, "1200cc – Küçük Crossover",     6000),
        (1400, "1400cc – Kompakt SUV",         6100),
        (1500, "1500cc – Kompakt SUV (1.5T)",  6200),
        (1600, "1600cc – Kompakt SUV",         6200),
        (1800, "1800cc – Orta SUV",            6300),
        (2000, "2000cc – Orta SUV",            6500),
        (2200, "2200cc – Dizel SUV (2.2D)",    4500),
        (2500, "2500cc – SUV / Hafif Ticari",  6500),
        (3000, "3000cc – Büyük SUV",           6700),
        (3500, "3500cc – Büyük SUV+",          6800),
        (4000, "4000cc – Pick-up / Full-size", 7000),
        (5000, "5000cc – Lüks SUV",            7200),
    ],
    "Spor": [
        (1600, "1600cc – Spor",                6200),
        (2000, "2000cc – Spor (2.0T)",         6500),
        (2500, "2500cc – Spor (Boxster 2.5)",  7000),
        (3000, "3000cc – Spor (GT-R 3.0T)",    7200),
        (4000, "4000cc – Spor (911 GT3 4.0)",  8500),
        (4500, "4500cc – Yüksek Performans",   7100),
        (5000, "5000cc – Lüks Spor",           7200),
        (6300, "6300cc – Süper Spor",          7400),
        (7000, "7000cc – Hypercar",            7500),
        (8000, "8000cc – Hypercar+",           7600),
    ],
    "Otobüs":  [
        (7000,  "7000cc – Minibüs / Midibüs",  4800),
        (9000,  "9000cc – Standart Otobüs",    4500),
        (12000, "12000cc – Büyük Otobüs",      4000),
        (15000, "15000cc – Çift Katlı Otobüs", 3800),
    ],
    "Tır": [
        (7000,  "7000cc – Orta Kamyon",        4800),
        (9000,  "9000cc – Hafif Tır",          4500),
        (12000, "12000cc – Standart Tır",      4000),
        (15000, "15000cc – Ağır Tır",          3800),
    ],
    "Kamyon": [
        (5000,  "5000cc – Hafif Ticari",       5000),
        (7000,  "7000cc – Orta Kamyon",        4800),
        (9000,  "9000cc – Ağır Kamyon",        4500),
        (12000, "12000cc – Çok Ağır Kamyon",   4000),
    ],
    "Lokomotif": [
        (12000, "12000cc – Hafif Lokomotif",   3800),
        (16000, "16000cc – Standart Lokomotif",3800),
        (20000, "20000cc – Ağır Lokomotif",    3500),
    ],
    "Gemi": [
        (20000, "20000cc – Küçük Gemi",        3200),
        (25000, "25000cc – Yük Gemisi",        2800),
        (35000, "35000cc – Büyük Yük Gemisi",  2400),
        (50000, "50000cc – Tanker / Konteyner",2000),
    ],
    "Elektrikli Sedan": [(None, "Elektrik Motoru", 6000)],
    "Elektrikli SUV":   [(None, "Elektrik Motoru", 6000)],
    "Elektrikli Spor":  [(None, "Elektrik Motoru", 7000)],
}

arac_tipleri_cfg = {
    "Sedan":            {"lastik": 2.0, "diff": 3.9},
    "SUV":              {"lastik": 2.2, "diff": 4.1},
    "Spor":             {"lastik": 1.9, "diff": 3.5},
    "Otobüs":           {"lastik": 3.2, "diff": 5.2},
    "Tır":              {"lastik": 3.5, "diff": 5.8},
    "Kamyon":           {"lastik": 3.3, "diff": 5.4},
    "Motosiklet":       {"lastik": 0.6, "diff": 3.0},
    "Gemi":             {"lastik": 5.0, "diff": 10.0},
    "Lokomotif":        {"lastik": 5.5, "diff": 9.5},
    "Elektrikli Sedan": {"lastik": 2.0, "diff": 3.9},
    "Elektrikli SUV":   {"lastik": 2.2, "diff": 4.1},
    "Elektrikli Spor":  {"lastik": 1.9, "diff": 3.5},
}

sanziman_oranlari = {
    "tek_vites": {1: 1.0},
    "2_vites":   {1:1.5, 2:1.0},
    "3_vites":   {1:2.0, 2:1.5, 3:1.0},
    "4_vites":   {1:2.5, 2:2.0, 3:1.5, 4:1.0},
    "6_vites":   {1:3.5, 2:2.2, 3:1.5, 4:1.1, 5:0.85, 6:0.65},
    "7_vites":   {1:3.7, 2:2.3, 3:1.6, 4:1.1, 5:0.85, 6:0.70, 7:0.60},
    "8_vites":   {1:4.0, 2:2.5, 3:1.7, 4:1.2, 5:0.90, 6:0.75, 7:0.62, 8:0.55},
    "12_vites":  {1:12.0,2:9.8,3:8.2,4:6.7,5:5.4,6:4.2,7:3.3,8:2.6,9:2.0,10:1.6,11:1.2,12:1.0},
    "16_vites":  {1:14.0,2:12.0,3:10.0,4:8.5,5:7.0,6:6.0,7:5.0,8:4.2,9:3.5,10:2.8,11:2.2,12:1.8,13:1.5,14:1.2,15:1.0,16:0.85},
}

arac_sanziman_map = {
    "Motosiklet":       ["2_vites","3_vites","4_vites"],
    "Sedan":            ["6_vites","7_vites","8_vites"],
    "SUV":              ["6_vites","7_vites","8_vites"],
    "Spor":             ["6_vites","7_vites","8_vites"],
    "Elektrikli Sedan": ["tek_vites"],
    "Elektrikli SUV":   ["tek_vites"],
    "Elektrikli Spor":  ["tek_vites"],
    "Otobüs":           ["12_vites","16_vites"],
    "Tır":              ["12_vites","16_vites"],
    "Kamyon":           ["12_vites","16_vites"],
    "Gemi":             [],
    "Lokomotif":        [],
}

arac_motor_tur_map = {
    "Sedan":            ["Benzin","Dizel","Hibrit","LPG"],
    "SUV":              ["Benzin","Dizel","Hibrit","LPG"],
    "Spor":             ["Benzin","Dizel","Hibrit","LPG"],
    "Motosiklet":       ["Benzin","LPG"],
    "Otobüs":           ["Benzin","Dizel","LPG"],
    "Tır":              ["Benzin","Dizel","LPG"],
    "Kamyon":           ["Benzin","Dizel","LPG"],
    "Gemi":             ["HFO"],
    "Lokomotif":        ["Dizel","HFO"],
    "Elektrikli Sedan": ["Elektrik"],
    "Elektrikli SUV":   ["Elektrik"],
    "Elektrikli Spor":  ["Elektrik"],
}

TÜKETIM_BİRİM = {
    "Benzin":"L/100km","Dizel":"L/100km","Hibrit":"L/100km",
    "LPG":"L/100km","HFO":"L/100km","Elektrik":"kWh/100km"
}

# ─── HESAPLAMA FONKSİYONLARI ────────────────────────────────────────────────

def tahmin_beygir(cc, mt):
    if cc is None: return None
    if mt in ("Benzin","LPG"): return round(cc/10+30)
    elif mt == "Hibrit":       return round(cc/9+40)
    elif mt == "Dizel":        return round(cc/14+25)
    elif mt == "HFO":          return round(cc/8+50)
    return round(cc/15+40)

def tahmin_tork(cc, mt):
    if cc is None: return None
    if mt == "Dizel":          return round(cc/10+80)
    elif mt == "Hibrit":       return round(cc/12+70)
    elif mt in ("Benzin","LPG"): return round(cc/14+60)
    elif mt == "HFO":          return round(cc/6+100)
    return round(cc/15+50)

def tahmin_aero(arac):
    return {"Sedan":0.28,"SUV":0.34,"Spor":0.25,"Motosiklet":0.38,
            "Otobüs":0.60,"Tır":0.65,"Kamyon":0.63,"Gemi":0.80,
            "Lokomotif":0.75,"Elektrikli Sedan":0.26,
            "Elektrikli SUV":0.30,"Elektrikli Spor":0.23}.get(arac, 0.40)

def hesapla_tuketim(mt, arac, cc, hiz, oran, sz, max_rpm, tip):
    try:
        n_v = 1 if sz in ("tek_vites","tek") else int(sz.split("_")[0])
    except Exception:
        n_v = 6

    rpm = hiz * oran * tip["diff"] * 1000 / (tip["lastik"] * 60)

    if arac.startswith("Elektrikli"):
        base = {"Elektrikli Sedan":14.0,"Elektrikli SUV":17.0,"Elektrikli Spor":20.0}.get(arac,15.0)
        k    = {"Elektrikli Sedan":0.0003,"Elektrikli SUV":0.0004,"Elektrikli Spor":0.0005}.get(arac,0.0003)
        t = base + k * pow(max(hiz-60,0), 2)
        return rpm, max(0.0, round(t,2))

    cc_v = cc if cc else 1500
    ce = max(-1.5, min(15.0, (cc_v-1600)/1000))

    if arac == "Sedan":
        base = 6.0+ce*0.5
        k = (0.0008+0.0001*ce)*(1+0.003*(hiz-90))/max(oran**0.6,0.1)
    elif arac == "SUV":
        base = 8.0+ce*0.6
        k = (0.0010+0.00015*ce)*(1+0.003*(hiz-90))/max(oran**0.6,0.1)
    elif arac == "Spor":
        base = 9.0+ce*0.7
        k = (0.0012+0.0002*ce)*(1+0.003*(hiz-90))/max(oran**0.6,0.1)
    elif arac in ("Otobüs","Tır","Kamyon"):
        base = 20.0+ce*1.2+0.006*hiz
        k = 0.005*(1+0.0035*(hiz-40))*(1+ce*0.3)/max(oran**0.6,0.1)
    elif arac == "Lokomotif":
        base = 150.0+ce*2.0
        k = 0.0075*(1+ce*0.25)
    elif arac == "Motosiklet":
        base = 4.0+ce*0.3
        k = 0.0007+0.00005*ce
    else:
        base = 7.0+ce*0.5
        k = 0.001*(1+0.002*ce)

    if mt == "Dizel":        base*=0.88; k*=0.88
    elif mt == "Hibrit":     base*=0.78; k*=0.82
    elif mt == "LPG":        base*=1.10; k*=1.10
    elif mt == "HFO":        base*=1.30; k*=1.20

    if n_v <= 4:   base*=1.04; k*=1.04
    elif n_v >= 8: base*=0.97; k*=0.97

    if mt == "Hibrit":
        if hiz <= 40:   t = base*0.55
        elif hiz <= 70:
            blend=(hiz-40)/30.0
            t = base*(0.55+blend*0.45)
        else: t = base+k*pow(hiz-90,2)*pow(rpm/max_rpm,1.1)
    else:
        t = base+k*pow(hiz-90,2)*pow(rpm/max_rpm,1.1)

    return rpm, max(0.0, round(t,2))

def gemi_hesapla(hiz):
    rpm = 150+hiz*0.8
    tuk = round((180+hiz*1.2)/hiz*100, 2)
    return rpm, tuk

def hesapla_arac_data(cfg, fiyatlar):
    arac   = cfg["arac"]
    mt     = cfg["motor_turu"]
    cc     = cfg["cc"]
    max_rpm= cfg["max_rpm"]
    sz     = cfg["sanziman"]
    vites  = cfg["vites"]
    tip    = arac_tipleri_cfg[arac]

    if sz in sanziman_oranlari:
        oran = sanziman_oranlari[sz].get(vites, 1.0)
    else:
        oran = 1.0

    hiz_list = list(range(10, 510, 10)) if arac != "Gemi" else list(range(10,50,5))
    rows = []
    for hiz in hiz_list:
        if arac == "Gemi":
            rpm, tuk = gemi_hesapla(hiz)
        else:
            rpm, tuk = hesapla_tuketim(mt, arac, cc, hiz, oran, sz, max_rpm, tip)
        fiyat = fiyatlar.get(mt, 48.72)
        mal   = round(tuk*fiyat, 2)
        rows.append({"Hız": hiz, "RPM": round(rpm), "Tüketim": tuk, "Maliyet": mal})

    return pd.DataFrame(rows)

# ─── SIDEBAR ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="page-title" style="font-size:1.4rem;">⚙️ Ayarlar</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Yakıt Fiyatları (TL)</div>', unsafe_allow_html=True)
    fiyatlar = {}
    f_cols = st.columns(2)
    with f_cols[0]:
        fiyatlar["Benzin"]   = st.number_input("Benzin",   value=63.57, step=0.01, format="%.2f")
        fiyatlar["Dizel"]    = st.number_input("Dizel",    value=71.59, step=0.01, format="%.2f")
        fiyatlar["LPG"]      = st.number_input("LPG",      value=36.35, step=0.01, format="%.2f")
    with f_cols[1]:
        fiyatlar["Hibrit"]   = st.number_input("Hibrit",   value=63.57, step=0.01, format="%.2f")
        fiyatlar["Elektrik"] = st.number_input("Elektrik", value=11.00, step=0.01, format="%.2f")
        fiyatlar["HFO"]      = st.number_input("HFO",      value=45.54, step=0.01, format="%.2f")

    st.markdown('<div class="sidebar-section">Grafik Seçenekleri</div>', unsafe_allow_html=True)
    grafik_turu = st.radio("Göster", ["Tüketim (100km)", "Maliyet (TL/100km)", "RPM"], index=0)
    hiz_aralik  = st.slider("Hız Aralığı (km/s)", 10, 500, (10, 500), step=5)

    st.markdown('<div class="sidebar-section">KM Maliyet Hesabı</div>', unsafe_allow_html=True)
    hedef_km = st.number_input("Referans KM", value=100, min_value=1, max_value=10000)

    st.markdown('<div class="sidebar-section">Yolculuk Hesabı</div>', unsafe_allow_html=True)
    yolculuk_km = st.number_input("Yolculuk KM", value=500, min_value=1, max_value=100000,
                                   help="Planladigin yolculugun toplam mesafesi")

# ─── ARAÇ SEÇİM FORMU ───────────────────────────────────────────────────────

def arac_secim_panel(prefix, renk_class, emoji):
    arac_listesi = list(arac_tipleri_cfg.keys())
    arac = st.selectbox(f"{emoji} Araç Tipi", arac_listesi, key=f"{prefix}_arac")

    cc_list = motor_hacimleri_map.get(arac, [(1600,"1600cc",6200)])
    cc_labels = [item[1] for item in cc_list]
    cc_idx = st.selectbox("Motor Hacmi", range(len(cc_labels)),
                          format_func=lambda i: cc_labels[i], key=f"{prefix}_cc")
    cc_val, _, max_rpm = cc_list[cc_idx]

    mt_list = arac_motor_tur_map.get(arac, ["Benzin"])
    mt = st.selectbox("Motor Türü", mt_list, key=f"{prefix}_mt")

    sz_list = arac_sanziman_map.get(arac, [])
    if sz_list:
        sz = st.selectbox("Şanzıman", sz_list, key=f"{prefix}_sz")
        vites_opts = list(sanziman_oranlari[sz].keys())
        vites = st.selectbox("Vites", vites_opts,
                             index=len(vites_opts)-1, key=f"{prefix}_vites")
        oran = sanziman_oranlari[sz][vites]
    else:
        sz = "tek_vites"; vites = 1; oran = 1.0
        st.info("Sabit şanzıman")

    return {
        "arac": arac, "cc": cc_val, "max_rpm": max_rpm,
        "motor_turu": mt, "sanziman": sz, "vites": vites, "oran": oran
    }

# ─── ANA BAŞLIK ─────────────────────────────────────────────────────────────

st.markdown('<div class="page-title">🚗 Araç Simülasyonu</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Yakıt Tüketimi & Maliyet Karşılaştırması</div>', unsafe_allow_html=True)

# ─── İKİ ARAÇ SEÇİMİ ────────────────────────────────────────────────────────

col_a, col_vs, col_b = st.columns([5, 1, 5])

with col_a:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:700;color:#4fc3f7;margin-bottom:0.6rem;">🔵 ARAÇ 1</div>', unsafe_allow_html=True)
    with st.container():
        cfg1 = arac_secim_panel("a1", "arac1-accent", "")

with col_vs:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown('<div class="vs-badge">VS</div>', unsafe_allow_html=True)

with col_b:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:700;color:#f06292;margin-bottom:0.6rem;">🔴 ARAÇ 2</div>', unsafe_allow_html=True)
    with st.container():
        cfg2 = arac_secim_panel("a2", "arac2-accent", "")

# ─── HESAPLA ────────────────────────────────────────────────────────────────

df1 = hesapla_arac_data(cfg1, fiyatlar)
df2 = hesapla_arac_data(cfg2, fiyatlar)

# Hız aralığı filtrele
df1f = df1[(df1["Hız"] >= hiz_aralik[0]) & (df1["Hız"] <= hiz_aralik[1])]
df2f = df2[(df2["Hız"] >= hiz_aralik[0]) & (df2["Hız"] <= hiz_aralik[1])]

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ─── METRİK KARTI ────────────────────────────────────────────────────────────

def ortalama(df, col):
    return round(df[col].mean(), 2) if len(df) > 0 else 0

tuk1 = ortalama(df1f, "Tüketim")
tuk2 = ortalama(df2f, "Tüketim")
mal1 = ortalama(df1f, "Maliyet")
mal2 = ortalama(df2f, "Maliyet")
rpm1 = ortalama(df1f, "RPM")
rpm2 = ortalama(df2f, "RPM")
mt1  = cfg1["motor_turu"]
mt2  = cfg2["motor_turu"]
birim1 = TÜKETIM_BİRİM.get(mt1, "L/100km")
birim2 = TÜKETIM_BİRİM.get(mt2, "L/100km")

hp1   = tahmin_beygir(cfg1["cc"], mt1)
hp2   = tahmin_beygir(cfg2["cc"], mt2)
tork1 = tahmin_tork(cfg1["cc"], mt1)
tork2 = tahmin_tork(cfg2["cc"], mt2)
aero1 = tahmin_aero(cfg1["arac"])
aero2 = tahmin_aero(cfg2["arac"])

km_tuk1 = round(tuk1/100 * hedef_km, 2)
km_tuk2 = round(tuk2/100 * hedef_km, 2)
km_mal1 = round(mal1/100 * hedef_km, 2)
km_mal2 = round(mal2/100 * hedef_km, 2)

def diff_label(v1, v2, ters=False):
    if v2 == 0: return ""
    pct = round((v1-v2)/v2*100, 1)
    if pct == 0: return '<span style="color:#8892aa;font-size:0.72rem;">eşit</span>'
    cls = "diff-better" if (pct < 0 and not ters) else "diff-worse"
    arrow = "▼" if pct < 0 else "▲"
    return f'<span class="{cls}">{arrow} %{abs(pct)}</span>'

st.markdown("### 📊 Anlık Karşılaştırma")

mal1km = round(mal1 / 100, 3)
mal2km = round(mal2 / 100, 3)

m_cols = st.columns(6)
metrics = [
    ("Ort. Tüketim",  f"{tuk1}", birim1,      f"{tuk2}", birim2,      tuk1,      tuk2,      False),
    ("Ort. Maliyet",  f"{mal1}", "TL/100km",  f"{mal2}", "TL/100km",  mal1,      mal2,      False),
    ("1 KM Maliyet",  f"{mal1km}", "TL/km",   f"{mal2km}", "TL/km",   mal1km,    mal2km,    False),
    ("Beygir Gücü",   f"{hp1 or '?'}", "hp",  f"{hp2 or '?'}", "hp",  hp1 or 0, hp2 or 0,  True),
    ("Tork",          f"{tork1 or '?'}", "Nm", f"{tork2 or '?'}", "Nm",tork1 or 0,tork2 or 0,True),
    ("Aero (Cd)",     f"{aero1}", "",          f"{aero2}", "",          aero1,     aero2,     False),
]

for col, (label, v1, u1, v2, u2, n1, n2, ters) in zip(m_cols, metrics):
    with col:
        d1 = diff_label(n1, n2, ters=ters)
        d2 = diff_label(n2, n1, ters=ters)
        st.markdown(f"""
        <div class="card" style="min-height:160px;">
            <div class="card-title">{label}</div>
            <div style="color:#4fc3f7;font-family:'Outfit',sans-serif;font-size:1.2rem;font-weight:600;">{v1} <span style="font-size:0.65rem;color:#555e7a;">{u1}</span></div>
            <div style="margin:0.2rem 0 0.5rem 0;">{d1}</div>
            <div style="border-top:1px solid #1f2330;padding-top:0.5rem;margin-top:0.3rem;">
            <div style="color:#f06292;font-family:'Outfit',sans-serif;font-size:1.2rem;font-weight:600;">{v2} <span style="font-size:0.65rem;color:#555e7a;">{u2}</span></div>
            <div style="margin-top:0.2rem;">{d2}</div></div>
        </div>
        """, unsafe_allow_html=True)

# ─── KM MALİYET KARŞILAŞTIRMASI ─────────────────────────────────────────────

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(f"### 🗺️ {hedef_km} KM İçin Maliyet")

km_cols = st.columns(4)
km_data = [
    ("🔵 Araç 1 Tüketim", f"{km_tuk1}", birim1.replace("/100km",""), "#4fc3f7"),
    ("🔵 Araç 1 Maliyet",  f"{km_mal1:,.0f}", "TL", "#4fc3f7"),
    ("🔴 Araç 2 Tüketim", f"{km_tuk2}", birim2.replace("/100km",""), "#f06292"),
    ("🔴 Araç 2 Maliyet",  f"{km_mal2:,.0f}", "TL", "#f06292"),
]
for col, (label, val, unit, renk) in zip(km_cols, km_data):
    with col:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">{label}</div>
            <div style="color:{renk};font-family:'Outfit',sans-serif;font-size:1.8rem;font-weight:700;line-height:1;">{val}</div>
            <div style="font-family:DM Mono,monospace;font-size:0.7rem;color:#555e7a;margin-top:0.3rem;">{unit}</div>
        </div>""", unsafe_allow_html=True)

# Tasarruf
tasarruf_mal = round(abs(km_mal1 - km_mal2), 2)
kazanan = "🔵 Araç 1" if km_mal1 < km_mal2 else ("🔴 Araç 2" if km_mal2 < km_mal1 else "Eşit")
renk_k  = "#4fc3f7" if km_mal1 < km_mal2 else "#f06292"
if km_mal1 != km_mal2:
    st.markdown(f"""
    <div class="card" style="text-align:center;margin-top:0.5rem;">
        <span style="font-family:DM Mono,monospace;font-size:0.75rem;color:#555e7a;">TASARRUF EDİLEN →</span>
        <span style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:700;color:{renk_k};margin:0 1rem;">{tasarruf_mal:,.0f} TL</span>
        <span style="font-family:DM Mono,monospace;font-size:0.75rem;color:#555e7a;">{hedef_km} km'de {kazanan} lehine</span>
    </div>""", unsafe_allow_html=True)

# ─── YOLCULUK KM HESABI ──────────────────────────────────────────────────────

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(f"### ✈️ Yolculuk Hesabı — {yolculuk_km:,} KM")

yol_tuk1 = round(tuk1 / 100 * yolculuk_km, 2)
yol_tuk2 = round(tuk2 / 100 * yolculuk_km, 2)
yol_mal1 = round(mal1 / 100 * yolculuk_km, 2)
yol_mal2 = round(mal2 / 100 * yolculuk_km, 2)
yol_tas  = round(abs(yol_mal1 - yol_mal2), 2)
yol_kaz  = "🔵 Araç 1" if yol_mal1 < yol_mal2 else ("🔴 Araç 2" if yol_mal2 < yol_mal1 else "Eşit")
yol_renk = "#4fc3f7" if yol_mal1 < yol_mal2 else "#f06292"

yol_cols = st.columns(5)
yol_data = [
    ("🔵 Araç 1\nTüketim",        f"{yol_tuk1:,.1f}", birim1.replace("/100km",""), "#4fc3f7"),
    ("🔵 Araç 1\nMaliyet",        f"{yol_mal1:,.0f}", "TL",                        "#4fc3f7"),
    ("🔴 Araç 2\nTüketim",        f"{yol_tuk2:,.1f}", birim2.replace("/100km",""), "#f06292"),
    ("🔴 Araç 2\nMaliyet",        f"{yol_mal2:,.0f}", "TL",                        "#f06292"),
    ("⚖️ Maliyet Farkı",           f"{yol_tas:,.0f}",  f"TL · {yol_kaz} lehine",   yol_renk),
]

for col, (label, val, unit, renk) in zip(yol_cols, yol_data):
    with col:
        label_html = label.replace("\n", "<br>")
        st.markdown(f"""
        <div class="card" style="text-align:center;">
            <div class="card-title" style="text-align:center;">{label_html}</div>
            <div style="color:{renk};font-family:'Outfit',sans-serif;font-size:1.6rem;font-weight:700;line-height:1;">{val}</div>
            <div style="font-family:DM Mono,monospace;font-size:0.65rem;color:#555e7a;margin-top:0.4rem;">{unit}</div>
        </div>""", unsafe_allow_html=True)

# Seçilen KM tablosu (her hıza göre)
with st.expander(f"📋 Hıza Göre {yolculuk_km:,} KM Detay Tablosu"):
    try:
        tbl1 = df1f[["Hız","Tüketim","Maliyet"]].copy()
        tbl1["Yolculuk Tüketim"]  = (tbl1["Tüketim"] / 100 * yolculuk_km).round(2)
        tbl1["Yolculuk Maliyet"]  = (tbl1["Maliyet"] / 100 * yolculuk_km).round(0).astype(int)
        tbl1 = tbl1.rename(columns={"Tüketim": f"Tük/100km ({birim1})", "Maliyet": "Mal/100km (TL)"})

        tbl2 = df2f[["Hız","Tüketim","Maliyet"]].copy()
        tbl2["Yolculuk Tüketim"]  = (tbl2["Tüketim"] / 100 * yolculuk_km).round(2)
        tbl2["Yolculuk Maliyet"]  = (tbl2["Maliyet"] / 100 * yolculuk_km).round(0).astype(int)
        tbl2 = tbl2.rename(columns={"Tüketim": f"Tük/100km ({birim2})", "Maliyet": "Mal/100km (TL)",
                                     "Yolculuk Tüketim": "Yolculuk Tüketim ", "Yolculuk Maliyet": "Yolculuk Maliyet "})

        merged_yol = pd.merge(
            tbl1, tbl2, on="Hız", suffixes=(" [A1]", " [A2]")
        )
        merged_yol["Maliyet Farkı (TL)"] = (merged_yol["Yolculuk Maliyet [A1]"] - merged_yol["Yolculuk Maliyet  [A2]"]).abs()
        merged_yol["Daha Ucuz"] = merged_yol.apply(
            lambda r: "🔵 Araç 1" if r["Yolculuk Maliyet [A1]"] < r["Yolculuk Maliyet  [A2]"]
            else ("🔴 Araç 2" if r["Yolculuk Maliyet  [A2]"] < r["Yolculuk Maliyet [A1]"] else "Eşit"), axis=1
        )
        st.dataframe(merged_yol, use_container_width=True, hide_index=True)
    except Exception:
        tc1, tc2 = st.columns(2)
        with tc1:
            st.caption("🔵 Araç 1")
            st.dataframe(tbl1, use_container_width=True, hide_index=True)
        with tc2:
            st.caption("🔴 Araç 2")
            st.dataframe(tbl2, use_container_width=True, hide_index=True)

# ─── GRAFIK ─────────────────────────────────────────────────────────────────

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("### 📈 Hız – Performans Grafiği")

if grafik_turu == "Tüketim (100km)":
    y_col = "Tüketim"
    y_lbl = "Tüketim"
elif grafik_turu == "Maliyet (TL/100km)":
    y_col = "Maliyet"
    y_lbl = "Maliyet (TL)"
else:
    y_col = "RPM"
    y_lbl = "RPM"

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df1f["Hız"], y=df1f[y_col],
    name=f"Araç 1 – {cfg1['arac']} {cfg1['motor_turu']}",
    line=dict(color="#4fc3f7", width=2.5),
    mode="lines+markers",
    marker=dict(size=5, color="#4fc3f7"),
    fill="tozeroy",
    fillcolor="rgba(79,195,247,0.06)"
))

fig.add_trace(go.Scatter(
    x=df2f["Hız"], y=df2f[y_col],
    name=f"Araç 2 – {cfg2['arac']} {cfg2['motor_turu']}",
    line=dict(color="#f06292", width=2.5),
    mode="lines+markers",
    marker=dict(size=5, color="#f06292"),
    fill="tozeroy",
    fillcolor="rgba(240,98,146,0.06)"
))

fig.update_layout(
    paper_bgcolor="#0d0f14",
    plot_bgcolor="#13161e",
    font=dict(family="DM Sans", color="#8892aa"),
    xaxis=dict(
        title="Hız (km/s)",
        gridcolor="#1f2330",
        zerolinecolor="#1f2330",
        title_font=dict(color="#555e7a"),
    ),
    yaxis=dict(
        title=y_lbl,
        gridcolor="#1f2330",
        zerolinecolor="#1f2330",
        title_font=dict(color="#555e7a"),
    ),
    legend=dict(
        bgcolor="#13161e",
        bordercolor="#1f2330",
        borderwidth=1,
        font=dict(size=12)
    ),
    height=420,
    margin=dict(l=20, r=20, t=20, b=20),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# ─── DETAY TABLOSU ──────────────────────────────────────────────────────────

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("### 🗂️ Detaylı Veri Tablosu")

tab1, tab2, tab3 = st.tabs(["🔵 Araç 1", "🔴 Araç 2", "⚖️ Karşılaştırma"])

with tab1:
    st.markdown(f"""
    <div style="font-family:DM Mono,monospace;font-size:0.72rem;color:#555e7a;margin-bottom:0.8rem;">
    {cfg1['arac']} · {cfg1['motor_turu']} · {cfg1['cc'] or 'Elektrik'}cc · {cfg1['sanziman']} · Vites {cfg1['vites']}
    </div>""", unsafe_allow_html=True)
    st.dataframe(
        df1f.rename(columns={"Tüketim": f"Tüketim ({birim1})", "Maliyet": "Maliyet (TL/100km)"}),
        use_container_width=True, hide_index=True
    )

with tab2:
    st.markdown(f"""
    <div style="font-family:DM Mono,monospace;font-size:0.72rem;color:#555e7a;margin-bottom:0.8rem;">
    {cfg2['arac']} · {cfg2['motor_turu']} · {cfg2['cc'] or 'Elektrik'}cc · {cfg2['sanziman']} · Vites {cfg2['vites']}
    </div>""", unsafe_allow_html=True)
    st.dataframe(
        df2f.rename(columns={"Tüketim": f"Tüketim ({birim2})", "Maliyet": "Maliyet (TL/100km)"}),
        use_container_width=True, hide_index=True
    )

with tab3:
    try:
        merge = df1f[["Hız","Tüketim","Maliyet"]].copy()
        merge.columns = ["Hız", "Tüketim_A1", "Maliyet_A1"]
        m2 = df2f[["Hız","Tüketim","Maliyet"]].copy()
        m2.columns = ["Hız","Tüketim_A2","Maliyet_A2"]
        merged = pd.merge(merge, m2, on="Hız", how="inner")
        merged["Tüketim Farkı"]  = (merged["Tüketim_A1"] - merged["Tüketim_A2"]).round(2)
        merged["Maliyet Farkı"]  = (merged["Maliyet_A1"] - merged["Maliyet_A2"]).round(2)
        merged["Daha Verimli"]   = merged.apply(
            lambda r: "🔵 Araç 1" if r["Tüketim_A1"] < r["Tüketim_A2"]
            else ("🔴 Araç 2" if r["Tüketim_A2"] < r["Tüketim_A1"] else "Eşit"), axis=1)
        st.dataframe(merged, use_container_width=True, hide_index=True)
    except Exception as e:
        st.info("Hız aralıkları örtüşmüyor, karşılaştırma yapılamıyor.")

# ─── ARAÇ BİLGİ KARTLARI ────────────────────────────────────────────────────

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("### 🔧 Teknik Özellikler")

inf1, inf2 = st.columns(2)

def bilgi_karti(cfg, hp, tork, aero, renk, prefix):
    elektrik = cfg["arac"].startswith("Elektrikli")
    batarya  = "8-10 yıl" if elektrik else "—"
    dolum    = ("0.5-1 saat" if "Spor" in cfg["arac"] else
                "1.5-2 saat" if "SUV" in cfg["arac"] else "1-1.5 saat") if elektrik else "—"
    return f"""
    <div class="card">
        <div class="card-title" style="color:{renk};">{prefix}</div>
        <div style="display:flex;flex-wrap:wrap;gap:0.4rem;margin-bottom:0.8rem;">
            <span class="info-tag">{cfg['arac']}</span>
            <span class="info-tag">{cfg['motor_turu']}</span>
            <span class="info-tag">{cfg['cc'] or 'Elektrik'}cc</span>
            <span class="info-tag">{cfg['sanziman']}</span>
            <span class="info-tag">Vites {cfg['vites']}</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">
            <div class="metric-box">
                <div class="metric-label">Beygir</div>
                <div class="metric-val" style="color:{renk};">{hp or '?'}</div>
                <div class="metric-unit">hp</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Tork</div>
                <div class="metric-val" style="color:{renk};">{tork or '?'}</div>
                <div class="metric-unit">Nm</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Aero Kd</div>
                <div class="metric-val" style="color:{renk};">{aero}</div>
                <div class="metric-unit">Cd</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Batarya</div>
                <div class="metric-val" style="font-size:1rem;color:{renk};">{batarya}</div>
                <div class="metric-unit">ömür · {dolum}</div>
            </div>
        </div>
    </div>"""

with inf1:
    st.markdown(bilgi_karti(cfg1, hp1, tork1, aero1, "#4fc3f7", "🔵 ARAÇ 1"), unsafe_allow_html=True)
with inf2:
    st.markdown(bilgi_karti(cfg2, hp2, tork2, aero2, "#f06292", "🔴 ARAÇ 2"), unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;font-family:DM Mono,monospace;font-size:0.65rem;color:#2a2f3e;margin-top:2rem;">
Araç Simülasyonu · Değerler tahmin modellerine dayanmaktadır
</div>""", unsafe_allow_html=True)