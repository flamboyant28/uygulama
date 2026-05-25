import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import re
import pandas as pd
import plotly.express as px
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="Loto Kombinasyon Üretici", page_icon="🍀", layout="wide")

st.markdown("""
<style>
.ball-row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin:3px 0; }
.ball { width:42px; height:42px; border-radius:50%; display:flex; align-items:center;
        justify-content:center; font-weight:700; font-size:14px; color:#fff; flex-shrink:0; }
.sep  { font-size:20px; color:#bbb; margin:0 2px; }
.row-label { font-size:12px; color:#888; margin-bottom:1px; font-weight:500; }
.info-note { font-size:11px; color:#aaa; font-style:italic; margin-top:6px; }
</style>
""", unsafe_allow_html=True)

# ─── Arşivler (JSON'dan oku) ─────────────────────────────────────────────────
import json as _json, os as _os
from datetime import datetime as _dt

def _arsiv_yukle(dosya, sistem_filtre=None):
    """JSON arşivini yükle, isteğe göre sistem filtrele."""
    if _os.path.exists(dosya):
        with open(dosya, encoding="utf-8") as _f:
            rows = _json.load(_f)
    else:
        rows = []
    if sistem_filtre:
        rows = [r for r in rows if r.get("sistem") == sistem_filtre]
    rows.sort(key=lambda r: _dt.strptime(r["tarih"], "%d/%m/%Y"), reverse=True)
    for r in rows:
        r["tarih_str"] = r["tarih"]
        r["hafta"]     = r["sira"]
    return rows

ON_NUMARA_ARSIV   = _arsiv_yukle("on_numara_arsiv.json")
SAYISAL_ARSIV     = _arsiv_yukle("sayisal_loto_arsiv.json")
SUPER_ARSIV       = _arsiv_yukle("super_loto_arsiv.json")
SANS_TOPU_ARSIV   = _arsiv_yukle("sans_topu_arsiv.json")

# Her oyunun arşivini config'e bağla
OYUN_ARSIVLERI = {
    "Sayisal-Loto": SAYISAL_ARSIV,
    "Super-Loto":   SUPER_ARSIV,
    "Sans-Topu":    SANS_TOPU_ARSIV,
    "On-Numara":    ON_NUMARA_ARSIV,
}

# ─── Yedek istatistik verisi ──────────────────────────────────────────────────
YEDEK = {
    "Sayisal-Loto": {
        "sicak": [(45,82),(87,80),(71,79),(62,73),(60,73),(89,72),(18,72),(56,71),(38,71),(88,70),
                  (23,69),(69,69),(13,69),(12,67),(5,67),(64,67),(1,67),(8,67),(63,66),(80,66),
                  (46,66),(41,66),(77,66),(6,65),(47,65),(48,64),(66,64),(7,64),(50,63),(40,63)],
        "soguk": [(54,67),(85,59),(51,44),(73,40),(15,39),(49,38),(21,33),(22,33),(65,32),(58,32),
                  (44,31),(57,28),(32,27),(46,27),(77,27),(61,26),(86,25),(71,24),(20,23),(67,23)],
    },
    "Super-Loto": {
        "sicak": [(44,22),(41,20),(7,18),(9,18),(3,17),(21,17),(55,17),(32,16),(36,16),(6,15),
                  (16,15),(19,15),(37,15),(47,14),(52,14),(14,13),(23,13),(34,13),(38,13),(51,13)],
        "soguk": [(13,49),(58,37),(10,34),(15,33),(4,31),(53,25),(18,23),(59,21),(40,19),(24,19),
                  (45,18),(30,16),(20,15),(26,15),(17,14),(28,14),(49,13),(60,13),(22,12),(27,12)],
    },
    "Sans-Topu": {
        "sicak": [(5,99),(2,98),(22,98),(18,96),(6,96),(14,95),(29,94),(7,94),(8,93),(26,91),
                  (25,91),(12,90),(21,90),(33,90),(32,89),(23,89),(34,89),(15,88),(1,87),(3,86)],
        "soguk": [(31,18),(10,15),(4,14),(17,12),(30,11),(3,10),(28,9),(13,8),(19,8),(1,7),
                  (20,7),(27,7),(9,6),(16,6),(24,6),(11,5),(2,4),(5,4),(8,4),(22,4)],
        "bonus_sicak": [(2,38),(8,36),(11,35),(6,34),(14,34),(1,33),(4,33),(7,32),(13,31),(3,30)],
        "bonus_soguk": [(12,8),(5,7),(10,7),(3,6),(9,6),(14,5),(1,4),(4,4),(6,4),(7,4)],
    },
    "On-Numara": {
        "sicak": [(77,195),(16,193),(2,189),(4,188),(50,187),(53,184),(12,183),(27,183),(28,179),
                  (60,177),(65,177),(52,177),(57,176),(73,175),(79,175),(48,174),(55,173),(40,173),
                  (6,173),(47,171),(31,171),(13,170),(71,168),(11,168),(18,168),(15,167),(37,167),
                  (34,167),(58,166),(32,166)],
        "soguk": [(22,18),(4,18),(30,14),(57,11),(41,11),(26,10),(34,9),(55,8),(36,8),(51,7),
                  (67,7),(7,7),(47,7),(49,6),(25,6),(23,6),(28,5),(46,5),(11,5),(20,5)],
    },
}

OYUNLAR = {
    "🎯 Sayısal Loto": {"slug":"Sayisal-Loto","havuz":90,"secim":6,"bonus":False,"renk":"#1a4fa0","aciklama":"1–90 arası 6 sayı","olasilik":"1 / 622.614.630"},
    "⭐ Süper Loto":   {"slug":"Super-Loto",  "havuz":60,"secim":6,"bonus":False,"renk":"#7d3c98","aciklama":"1–60 arası 6 sayı","olasilik":"1 / 50.063.860"},
    "🔵 Şans Topu":   {"slug":"Sans-Topu",   "havuz":34,"secim":5,"bonus":True, "bonus_havuz":14,"bonus_renk":"#e6a817","renk":"#16a085","aciklama":"1–34 arası 5 sayı + Şans Topu (1–14)","olasilik":"1 / 3.895.584"},
    "🔴 On Numara":   {"slug":"On-Numara",   "havuz":80,"secim":10,"bonus":False,"renk":"#c0392b","aciklama":"1–80 arası 10 sayı (22 çekilir)","olasilik":"1 / 2.545.786"},
}

# ─── Scraper ──────────────────────────────────────────────────────────────────
def parse_numred(url):
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for img in soup.find_all("img", src=re.compile(r"img/num/\d+\.png|NumRed/\d+\.png")):
            m = re.search(r"/(\d+)\.png", img["src"])
            if not m:
                continue
            num = int(m.group(1))
            td = img.find_parent("td")
            if td:
                sib = td.find_next_sibling("td")
                if sib:
                    vm = re.search(r"\d+", sib.get_text())
                    if vm:
                        results.append((num, int(vm.group())))
        return results
    except:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def veri_yukle(slug):
    base = "https://www.lotokurdu.com"
    slug_map = {
        "Sayisal-Loto": ("Sayisal-Loto-En-Cok-Cikan-Sayilar","Sayisal-Loto-En-Uzun-Zamandir-Cikmayan-Sayilar"),
        "Super-Loto":   ("Super-Loto-En-Cok-Cikan-Sayilar","Super-Loto-En-Uzun-Zamandir-Cikmayan-Sayilar"),
        "Sans-Topu":    ("Sans-Topu-En-Cok-Cikan-Sayilar","Sans-Topu-En-Uzun-Zamandir-Cikmayan-Sayilar"),
        "On-Numara":    ("On-Numara-En-Cok-Cikan-Sayilar","On-Numara-En-Uzun-Zamandir-Cikmayan-Sayilar"),
    }
    s1, s2 = slug_map.get(slug, ("",""))
    sicak = parse_numred(f"{base}/{s1}")
    soguk = parse_numred(f"{base}/{s2}")
    yedek = YEDEK.get(slug, {})
    kaynak = "lotokurdu.com" if sicak else "yedek veri"
    if not sicak: sicak = yedek.get("sicak", [])
    if not soguk: soguk = yedek.get("soguk", [])
    return sicak, soguk, yedek.get("bonus_sicak",[]), yedek.get("bonus_soguk",[]), kaynak

# ─── Son çekilişlere dayalı mod ───────────────────────────────────────────────
def son_cekilis_adaylar(arsiv, n_cekilis, aday_sayisi=30):
    """Son N çekilişe göre frekans hesapla ve 30 aday belirle."""
    son_n = arsiv[:n_cekilis]
    tum = []
    for row in son_n:
        tum.extend(row["sayilar"])
    freq = Counter(tum)
    # En çok çıkan aday_sayisi kadar sayı
    adaylar_sirali = [num for num, _ in freq.most_common(aday_sayisi)]
    return adaylar_sirali, freq

def son_cekilis_bonus(arsiv, n_cekilis, alt_mod, bonus_havuz=14):
    """Son N çekilişe göre şans topu (bonus) üret."""
    son_n = arsiv[:n_cekilis]
    bonus_freq = Counter()
    for row in son_n:
        if row.get("bonus"):
            bonus_freq[row["bonus"]] += 1
    tum = list(range(1, bonus_havuz + 1))
    if alt_mod == "🔥 Sıcak" and bonus_freq:
        sirali = sorted(tum, key=lambda x: bonus_freq.get(x, 0), reverse=True)
        return random.choice(sirali[:5])
    elif alt_mod == "❄️ Soğuk" and bonus_freq:
        sirali = sorted(tum, key=lambda x: bonus_freq.get(x, 0))
        return random.choice(sirali[:5])
    return random.randint(1, bonus_havuz)

def son_cekilis_mod(arsiv, n_cekilis, alt_mod="🎲 Rastgele", secim=10, aday_sayisi=30):
    """30 aday belirle, alt moda göre 10 seç."""
    adaylar_sirali, freq = son_cekilis_adaylar(arsiv, n_cekilis, aday_sayisi)

    if len(adaylar_sirali) < secim:
        adaylar_sirali += [x for x in range(1, 81) if x not in adaylar_sirali]

    aday_set = adaylar_sirali[:aday_sayisi]

    if alt_mod == "🎲 Rastgele":
        secilen = random.sample(aday_set, min(secim, len(aday_set)))

    elif alt_mod == "🔥 Sıcak":
        # 30 içinde en çok çıkan 10
        sirali = sorted(aday_set, key=lambda x: freq.get(x, 0), reverse=True)
        havuz = sirali[:max(secim * 2, 15)]
        secilen = random.sample(havuz, min(secim, len(havuz)))

    elif alt_mod == "❄️ Soğuk":
        # 30 içinde en az çıkan 10
        sirali = sorted(aday_set, key=lambda x: freq.get(x, 0))
        havuz = sirali[:max(secim * 2, 15)]
        secilen = random.sample(havuz, min(secim, len(havuz)))

    elif alt_mod == "🎭 Karma":
        # Yarısı sıcak yarısı soğuk
        sirali_sicak = sorted(aday_set, key=lambda x: freq.get(x, 0), reverse=True)
        sirali_soguk = sorted(aday_set, key=lambda x: freq.get(x, 0))
        yarim = secim // 2
        diger = secim - yarim
        s_havuz = sirali_sicak[:max(yarim * 2, 10)]
        g_havuz = [x for x in sirali_soguk[:max(diger * 2, 10)] if x not in s_havuz]
        if len(g_havuz) < diger:
            g_havuz += [x for x in aday_set if x not in s_havuz and x not in g_havuz]
        secilen = (random.sample(s_havuz, min(yarim, len(s_havuz))) +
                   random.sample(g_havuz, min(diger, len(g_havuz))))
    else:
        secilen = random.sample(aday_set, min(secim, len(aday_set)))

    return sorted(secilen), freq, aday_set

# ─── Kombinasyon üretici ──────────────────────────────────────────────────────
def uret(mod, havuz, secim, sicak, soguk):
    sn = [x for x,_ in sicak if 1<=x<=havuz]
    gn = [x for x,_ in soguk if 1<=x<=havuz]
    if mod == "Rastgele" or (not sn and not gn):
        return sorted(random.sample(range(1,havuz+1), secim))
    elif mod == "🔥 Sıcak":
        aday = sn[:max(secim*3,18)]
        if len(aday)<secim: aday += [x for x in range(1,havuz+1) if x not in aday]
        return sorted(random.sample(aday[:max(secim*2,14)], min(secim,len(aday))))
    elif mod == "❄️ Soğuk":
        aday = gn[:max(secim*3,18)]
        if len(aday)<secim: aday += [x for x in range(1,havuz+1) if x not in aday]
        return sorted(random.sample(aday[:max(secim*2,14)], min(secim,len(aday))))
    elif mod == "🎲 Karma":
        yarim=secim//2; diger=secim-yarim
        sa=sn[:20]; ga=[x for x in gn[:20] if x not in sa]
        if len(sa)<yarim: sa+=[x for x in range(1,havuz+1) if x not in sa]
        if len(ga)<diger: ga+=[x for x in range(1,havuz+1) if x not in ga and x not in sa]
        sec=(random.sample(sa[:max(yarim*2,10)],min(yarim,len(sa)))+
             random.sample(ga[:max(diger*2,10)],min(diger,len(ga))))
        return sorted(sec)
    return sorted(random.sample(range(1,havuz+1), secim))

def uret_bonus(mod, bh, bs, bg):
    if mod=="🔥 Sıcak" and bs:
        a=[x for x,_ in bs if 1<=x<=bh]; return random.choice(a[:6]) if a else random.randint(1,bh)
    elif mod=="❄️ Soğuk" and bg:
        a=[x for x,_ in bg if 1<=x<=bh]; return random.choice(a[:6]) if a else random.randint(1,bh)
    return random.randint(1,bh)

def mod_rengi(mod, varsayilan):
    return {"🔥 Sıcak":"#c0392b","❄️ Soğuk":"#16a085","🎲 Karma":"#7d3c98",
            "📅 Son Çekilişlere Dayalı":"#d35400"}.get(mod, varsayilan)

def toplar_html(nums, renk, bonus=None, bonus_renk="#e6a817"):
    html='<div class="ball-row">'
    for n in nums:
        html+=f'<div class="ball" style="background:{renk}">{n}</div>'
    if bonus is not None:
        html+=f'<div class="sep">+</div><div class="ball" style="background:{bonus_renk}">{bonus}</div>'
    html+='</div>'
    return html

def goster_grafik(data, baslik, renk, y_label):
    if not data: return
    df=pd.DataFrame(data,columns=["Sayı",y_label]).sort_values("Sayı")
    fig=px.bar(df,x="Sayı",y=y_label,title=baslik,color_discrete_sequence=[renk],height=250)
    fig.update_layout(margin=dict(t=36,b=10,l=10,r=10),plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",xaxis_title="",yaxis_title="")
    st.plotly_chart(fig,use_container_width=True)

def goster_top_listesi(data, renk, suffix, n=10):
    top=data[:n]
    if not top: return
    cols=st.columns(len(top))
    for col,(num,val) in zip(cols,top):
        col.markdown(f'<div style="text-align:center"><div class="ball" style="background:{renk};margin:0 auto 4px">{num}</div><div style="font-size:11px;color:#888">{val}{suffix}</div></div>',unsafe_allow_html=True)


# ─── Kolon Analizi ────────────────────────────────────────────────────────────
KOLON_OYUN_CFG = {
    "🎯 Sayısal Loto": {
        "slug": "Sayisal-Loto", "havuz_yeni": 90, "havuz_eski": 49,
        "secim": 6, "arsiv_key": "SAYISAL_ARSIV", "bonus": False,
    },
    "⭐ Süper Loto": {
        "slug": "Super-Loto", "havuz_yeni": 60, "havuz_eski": 54,
        "secim": 6, "arsiv_key": "SUPER_ARSIV", "bonus": False,
    },
    "🔵 Şans Topu": {
        "slug": "Sans-Topu", "havuz_yeni": 34, "havuz_eski": 34,
        "secim": 5, "arsiv_key": "SANS_TOPU_ARSIV", "bonus": False,
    },
    "🔴 On Numara": {
        "slug": "On-Numara", "havuz_yeni": 80, "havuz_eski": 80,
        "secim": 10, "arsiv_key": "ON_NUMARA_ARSIV", "bonus": False,
    },
}

KOLON_ARSIV_MAP = {
    "SAYISAL_ARSIV": lambda: SAYISAL_ARSIV,
    "SUPER_ARSIV":   lambda: SUPER_ARSIV,
    "SANS_TOPU_ARSIV": lambda: SANS_TOPU_ARSIV,
    "ON_NUMARA_ARSIV": lambda: ON_NUMARA_ARSIV,
}

def sayi_gridi_html(secilen: list, havuz: int) -> str:
    html = '<div style="display:flex;flex-wrap:wrap;gap:5px;margin:10px 0">'
    for n in range(1, havuz + 1):
        if n in secilen:
            stil = "background:#8e44ad;color:#fff;font-weight:700;border:2px solid #6c3483"
        else:
            stil = "background:#f0f0f0;color:#555;border:1px solid #ddd"
        html += (f'<div style="width:34px;height:34px;border-radius:50%;' +
                 f'{stil};display:flex;align-items:center;justify-content:center;' +
                 f'font-size:11px;cursor:default">{n:02d}</div>')
    html += '</div>'
    return html

def kolon_sonuc_tablosu(arsiv: list, secilen: list, secilen_bonus: int = None) -> str:
    secilen_set = set(secilen)
    bildi_sayac = Counter()
    satirlar = []
    for row in arsiv:
        cekilen = row["sayilar"]
        eslesen = secilen_set & set(cekilen)
        bildi = len(eslesen)
        # Bonus kontrolü
        bonus_eslesti = False
        if secilen_bonus and row.get("bonus"):
            bonus_eslesti = (secilen_bonus == row["bonus"])
        anahtar = (bildi, 1 if bonus_eslesti else 0) if secilen_bonus else bildi
        bildi_sayac[anahtar] += 1
        satirlar.append((row["tarih"], cekilen, eslesen, bildi,
                         row.get("bonus"), bonus_eslesti))

    # Özet kartlar
    ozet = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin:12px 0">'
    for anahtar in sorted(bildi_sayac.keys(), reverse=True):
        if secilen_bonus:
            ana_b, bon_b = anahtar
            etiket = f"{ana_b}+{bon_b} Bildi"
        else:
            ana_b = anahtar; etiket = f"{ana_b} Bildi"
        if   ana_b == 0 and (not secilen_bonus or bon_b == 0): renk = "#888"
        elif ana_b >= len(secilen):    renk = "#c0392b"
        elif ana_b >= len(secilen)-2:  renk = "#e67e22"
        elif ana_b >= len(secilen)-4:  renk = "#8e44ad"
        else: renk = "#555"
        ozet += (f'<div style="text-align:center;padding:8px 14px;border-radius:10px;' +
                 f'background:#f8f8f8;border:1px solid #eee">' +
                 f'<div style="font-size:18px;font-weight:700;color:{renk}">{etiket}</div>' +
                 f'<div style="font-size:12px;color:#888">{bildi_sayac[anahtar]} Kez</div></div>')
    ozet += '</div>'

    n_col = max(len(r["sayilar"]) for r in arsiv) if arsiv else 6
    has_bonus_col = secilen_bonus is not None

    tablo = """<style>
    .kt{width:100%;border-collapse:collapse;font-size:12px;}
    .kt th{background:#2c3e50;color:#fff;padding:5px 3px;text-align:center;}
    .kt td{padding:2px 2px;text-align:center;border-bottom:1px solid #f0f0f0;}
    .kt tr:hover td{background:#fafafa;}
    .tn{display:inline-flex;width:22px;height:22px;border-radius:50%;
        background:#e74c3c;color:#fff;align-items:center;justify-content:center;
        font-size:10px;font-weight:600;margin:1px;}
    .te{display:inline-flex;width:22px;height:22px;border-radius:50%;
        background:#8e44ad;color:#fff;align-items:center;justify-content:center;
        font-size:10px;font-weight:700;margin:1px;}
    .bb{padding:2px 7px;border-radius:10px;font-weight:600;font-size:11px;}
    </style>
    <table class="kt"><thead><tr><th>Tarih</th>"""
    for i in range(1, n_col+1):
        tablo += f'<th>{i}</th>'
    if has_bonus_col:
        tablo += '<th style="background:#b7860a">+</th>'
    tablo += '<th>Sonuç</th></tr></thead><tbody>'

    for tarih, cekilen, eslesen, bildi, row_bonus, bonus_eslesti in satirlar:
        max_b = len(secilen_set)
        if   bildi >= max_b and (not secilen_bonus or bonus_eslesti): bg = 'style="background:#fde8e8"'
        elif bildi >= max_b:     bg = 'style="background:#fde8e8"'
        elif bildi >= max_b-2:   bg = 'style="background:#fef3e2"'
        elif bildi >= max_b-4:   bg = 'style="background:#f3e8fd"'
        else: bg = ""

        if secilen_bonus:
            bon_str = f"+{1 if bonus_eslesti else 0}"
            etiket = f"{bildi}{bon_str}"
            if bildi == max_b and bonus_eslesti:  bc = "#c0392b"
            elif bildi >= max_b-1:                bc = "#e67e22"
            elif bildi >= max_b-3:                bc = "#8e44ad"
            elif bildi == 0 and not bonus_eslesti: bc = "#888"
            else: bc = "#bdc3c7"
            badge = f'<span class="bb" style="background:{bc};color:#fff">{etiket} Bildi</span>'
        else:
            if   bildi == 0:         badge = '<span class="bb" style="background:#eee;color:#888">0 Bildi</span>'
            elif bildi >= max_b:     badge = f'<span class="bb" style="background:#c0392b;color:#fff">{bildi} Bildi</span>'
            elif bildi >= max_b-2:   badge = f'<span class="bb" style="background:#e67e22;color:#fff">{bildi} Bildi</span>'
            elif bildi >= max_b-4:   badge = f'<span class="bb" style="background:#8e44ad;color:#fff">{bildi} Bildi</span>'
            else:                    badge = f'<span class="bb" style="background:#bdc3c7;color:#555">{bildi} Bildi</span>'

        tablo += f'<tr {bg}><td><b>{tarih}</b></td>'
        for n in sorted(cekilen):
            cls = "te" if n in eslesen else "tn"
            tablo += f'<td><span class="{cls}">{n}</span></td>'
        for _ in range(n_col - len(cekilen)):
            tablo += '<td></td>'
        # Bonus sütunu
        if secilen_bonus is not None and row_bonus:
            bon_cls = "te" if bonus_eslesti else "tn"
            tablo += f'<td><span class="{bon_cls}" style="background:{"#e6a817" if bonus_eslesti else "#aaa"}">{row_bonus}</span></td>'
        tablo += f'<td>{badge}</td></tr>'
    tablo += '</tbody></table>'
    return ozet + tablo

def kolon_analizi_sayfasi():
    # Oyun seçici
    oyun_adi = st.radio(
        "Oyun seçin:",
        list(KOLON_OYUN_CFG.keys()),
        horizontal=True,
        key="kolon_oyun_sec",
        index=list(KOLON_OYUN_CFG.keys()).index(
            st.session_state.get("kolon_oyun_adi", "🔴 On Numara")
        )
    )
    cfg_k = KOLON_OYUN_CFG[oyun_adi]
    arsiv_full = KOLON_ARSIV_MAP[cfg_k["arsiv_key"]]()

    # Sistem filtresi (Sayısal ve Süper için)
    col_s, col_m = st.columns([2, 3])
    with col_s:
        if cfg_k["slug"] in ["Sayisal-Loto", "Super-Loto"]:
            sistem = st.radio("Sistem:", ["Tümü","Yeni","Eski"],
                              horizontal=True, key=f"kolon_sistem_{cfg_k['slug']}")
            if sistem == "Yeni":
                arsiv = [r for r in arsiv_full if r.get("sistem")=="yeni"]
                havuz = cfg_k["havuz_yeni"]
            elif sistem == "Eski":
                arsiv = [r for r in arsiv_full if r.get("sistem")=="eski"]
                havuz = cfg_k["havuz_eski"]
            else:
                arsiv = arsiv_full
                havuz = cfg_k["havuz_yeni"]
        else:
            arsiv = arsiv_full
            havuz = cfg_k["havuz_yeni"]

    with col_m:
        st.caption(
            f"**{oyun_adi}** — 1–{havuz} arası {cfg_k['secim']} sayı  |  "
            f"Arşiv: **{len(arsiv)}** çekiliş"
        )

    if st.session_state.get("kolon_gonderildi"):
        st.success("✅ Kombinasyon aktarıldı!")
        st.session_state["kolon_gonderildi"] = False

    st.divider()

    # Sayı seçimi
    min_sec = cfg_k["secim"]
    max_sec = min(cfg_k["secim"] + 5, havuz)

    c1, c2 = st.columns([4, 1])
    with c1:
        default_sec = st.session_state.get("kolon_secim", [])
        default_sec = [n for n in default_sec if 1 <= n <= havuz]
        secilen = st.multiselect(
            f"Sayılarınızı seçin ({min_sec}–{max_sec} arası):",
            options=list(range(1, havuz + 1)),
            default=default_sec,
            format_func=lambda x: f"{x:02d}",
            max_selections=max_sec,
            key=f"kolon_secim_{oyun_adi}",
            placeholder="Sayı seçin..."
        )
    with c2:
        st.write("")
        st.metric("Seçilen", f"{len(secilen)} / {max_sec}")

    # Şans Topu: bonus seçici (1-14)
    secilen_bonus = None
    if cfg_k["slug"] == "Sans-Topu":
        st.markdown("**Şans Topu (opsiyonel):**")
        default_bon = st.session_state.get("kolon_secim_bonus")
        c_bon, c_bon2 = st.columns([3, 1])
        with c_bon:
            bon_opts = [None] + list(range(1, 15))
            bon_labels = {None: "Seçme", **{i: f"{i:02d}" for i in range(1, 15)}}
            secilen_bonus = st.selectbox(
                "Şans Topu seçin (1–14):",
                options=bon_opts,
                index=bon_opts.index(default_bon) if default_bon in bon_opts else 0,
                format_func=lambda x: bon_labels.get(x, str(x)),
                key=f"kolon_bonus_{oyun_adi}"
            )
        with c_bon2:
            if secilen_bonus:
                st.markdown(
                    f'<div style="margin-top:28px">' +
                    f'<div class="ball" style="background:#e6a817;width:42px;height:42px;font-size:16px;margin:auto">{secilen_bonus}</div>' +
                    f'</div>',
                    unsafe_allow_html=True)

    # Görsel grid
    st.markdown(sayi_gridi_html(secilen, havuz), unsafe_allow_html=True)

    if len(secilen) < min_sec:
        st.info(f"En az {min_sec} sayı seçmelisiniz. ({len(secilen)} seçili)")
        return

    # Yıl filtresi + test butonu
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        if arsiv:
            yillar = sorted(set(int(r["tarih"].split("/")[2]) for r in arsiv))
            yil_aralik = st.select_slider(
                "Yıl aralığı",
                options=yillar,
                value=(yillar[0], yillar[-1]),
                key=f"kolon_yil_{oyun_adi}"
            )
        else:
            yil_aralik = (2000, 2026)
    with col_f2:
        st.write("")
        test_btn = st.button("🔍 Kolon Test", type="primary",
                             use_container_width=True, key=f"kolon_test_{oyun_adi}")

    if test_btn:
        if not arsiv:
            st.error("Arşiv yüklenemedi.")
            return
        filtre = [r for r in arsiv
                  if yil_aralik[0] <= int(r["tarih"].split("/")[2]) <= yil_aralik[1]]
        filtre = sorted(filtre, key=lambda r: r["sira"], reverse=True)
        st.markdown(f"**{len(filtre)}** çekiliş analiz edildi ({yil_aralik[0]}–{yil_aralik[1]})")
        st.markdown(kolon_sonuc_tablosu(filtre, secilen, secilen_bonus), unsafe_allow_html=True)


def oyun_sekmesi(cfg):
    slug=cfg["slug"]; havuz=cfg["havuz"]; secim=cfg["secim"]
    bonus=cfg["bonus"]; bonus_havuz=cfg.get("bonus_havuz",14)
    bonus_renk=cfg.get("bonus_renk","#e6a817"); renk=cfg["renk"]
    on_numara = slug == "On-Numara"
    arsiv = OYUN_ARSIVLERI.get(slug, [])
    has_arsiv = len(arsiv) > 0

    with st.spinner("Veriler yükleniyor..."):
        sicak,soguk,b_sicak,b_soguk,kaynak = veri_yukle(slug)

    # Metrikler
    m1,m2,m3,m4=st.columns(4)
    m1.metric("Havuz",f"1–{havuz}")
    m2.metric("Seçim",f"{secim} sayı"+(" + şans topu" if bonus else ""))
    m3.metric("Büyük ikramiye",cfg["olasilik"])
    m4.metric("Veri kaynağı",kaynak)
    if kaynak=="yedek veri":
        st.warning("⚠️ lotokurdu.com'a bağlanılamadı — yedek istatistik verisi kullanılıyor.")
    st.divider()

    # Modlar
    modlar=["Rastgele","🔥 Sıcak","❄️ Soğuk","🎲 Karma"]
    if has_arsiv:
        modlar.append("📅 Son Çekilişlere Dayalı")

    c1,c2,c3=st.columns([3,1,1])
    with c1:
        mod=st.radio("Kombinasyon modu",modlar,horizontal=True,key=f"mod_{slug}")
    with c2:
        kolon=st.number_input("Kolon sayısı",1,20,5,key=f"kolon_{slug}")
    with c3:
        st.write(""); st.write("")
        uret_btn=st.button("🎯 Üret",key=f"uret_{slug}",use_container_width=True,type="primary")

    # Son çekilişlere dayalı slider
    n_cekilis = 5
    if has_arsiv and mod == "📅 Son Çekilişlere Dayalı":
        max_val = len(arsiv)
        n_cekilis = st.slider(
            f"Kaç son çekiliş baz alınsın? (Toplam {max_val} çekiliş mevcut)",
            min_value=3, max_value=min(max_val, max_val), value=5, step=1,
            key=f"slider_son_cekilis_{slug}"
        )
        # Sistem filtresi (Sayısal Loto ve Süper Loto için)
        if slug in ["Sayisal-Loto", "Super-Loto"]:
            sistem_sec = st.radio(
                "Hangi sistem?", ["Tümü", "Yeni sistem", "Eski sistem"],
                horizontal=True, key=f"sistem_{slug}"
            )
            if sistem_sec == "Yeni sistem":
                arsiv_filtered = [r for r in arsiv if r.get("sistem") == "yeni"]
            elif sistem_sec == "Eski sistem":
                arsiv_filtered = [r for r in arsiv if r.get("sistem") == "eski"]
            else:
                arsiv_filtered = arsiv
        else:
            arsiv_filtered = arsiv
        son_n_rows = arsiv_filtered[:n_cekilis]
        tarihler = f"{son_n_rows[-1]['tarih_str']} – {son_n_rows[0]['tarih_str']}" if son_n_rows else "—"
        st.caption(f"📅 Baz alınan dönem: **{tarihler}** ({n_cekilis} çekiliş)")

    # Son Çekilişlere Dayalı alt mod
    alt_mod = "🎲 Rastgele"
    if has_arsiv and mod == "📅 Son Çekilişlere Dayalı":
        alt_mod = st.radio(
            "30 aday içinden seçim stratejisi",
            ["🎲 Rastgele", "🔥 Sıcak", "❄️ Soğuk", "🎭 Karma"],
            horizontal=True,
            key=f"alt_mod_son_cekilis_{slug}",
            help="Önce son N çekilişten 30 aday belirlenir, sonra bu strateji uygulanır."
        )

    ALT_MOD_ACIK = {
        "🎲 Rastgele": "30 aday içinden tamamen rastgele 10 sayı seçilir.",
        "🔥 Sıcak":    "30 aday içinde son N çekilişte en çok çıkan 10 sayı seçilir.",
        "❄️ Soğuk":    "30 aday içinde son N çekilişte en az çıkan 10 sayı seçilir.",
        "🎭 Karma":    "30 aday içinden 5 sıcak + 5 soğuk karma seçim yapılır.",
    }
    MOD_ACIK={
        "Rastgele":"Tüm sayılar eşit olasılıkla — tamamen şansa bırak.",
        "🔥 Sıcak":"Tüm zamanların en sık çıkan sayılarından oluşturulur.",
        "❄️ Soğuk":"En uzun süredir çıkmayan sayılardan oluşturulur.",
        "🎲 Karma":"Yarısı sıcak, yarısı soğuk sayılardan karma seçim.",
        "📅 Son Çekilişlere Dayalı":f"Son {n_cekilis} çekilişten 30 aday belirlenir → {ALT_MOD_ACIK.get(alt_mod,'')}",
    }
    st.caption(f"ℹ️ {MOD_ACIK.get(mod,'')}") 
    st.divider()

    # Üret
    if uret_btn:
        st.subheader("🎰 Kombinasyonlar")
        top_renk=mod_rengi(mod,renk)

        if has_arsiv and mod=="📅 Son Çekilişlere Dayalı":
            _, freq, aday_set = son_cekilis_mod(arsiv_filtered, n_cekilis, alt_mod, secim, 30)
            for i in range(kolon):
                nums, _, aday_set = son_cekilis_mod(arsiv_filtered, n_cekilis, alt_mod, secim, 30)
                bon = None
                if bonus:
                    bon = son_cekilis_bonus(arsiv_filtered, n_cekilis, alt_mod, bonus_havuz)
                c_top, c_btn = st.columns([5, 1])
                with c_top:
                    st.markdown(f'<div class="row-label">Kolon {i+1}</div>',unsafe_allow_html=True)
                    st.markdown(toplar_html(nums, top_renk, bon, bonus_renk),unsafe_allow_html=True)
                with c_btn:
                    st.write("")
                    if st.button("🔍", key=f"kolon_gonder_son_{i}", help="Kolon Analizine Gönder"):
                        st.session_state["kolon_secim"] = nums
                        st.session_state["kolon_secim_bonus"] = bon
                        st.session_state["kolon_gonderildi"] = True
                        st.rerun()

            # 30 aday göster
            st.divider()
            adaylar_sirali, freq = son_cekilis_adaylar(arsiv_filtered, n_cekilis, 30)
            adaylar = sorted(adaylar_sirali)
            st.caption(f"**30 Aday Sayı** (son {n_cekilis} çekilişe göre) — koyu = daha çok çıktı:")
            aday_html = '<div class="ball-row">'
            max_freq = max(freq.get(n,1) for n in adaylar)
            min_freq = min(freq.get(n,1) for n in adaylar)
            for n in adaylar:
                f = freq.get(n, 1)
                # Frekansa göre opaklık: çok çıkan daha koyu
                oran = (f - min_freq) / max((max_freq - min_freq), 1)
                r_val = int(208 - oran * 100)
                g_val = int(53  - oran * 30)
                b_val = int(26  - oran * 10)
                bg = f"rgb({r_val},{g_val},{b_val})"
                isaretli = "★" if n in aday_set else ""
                aday_html += (f'<div style="text-align:center;margin:2px">' +
                              f'<div class="ball" style="background:{bg};width:36px;height:36px;font-size:12px">{n}</div>' +
                              f'<div style="font-size:9px;color:#888">{f}×</div>' +
                              f'</div>')
            aday_html += '</div>'
            st.markdown(aday_html, unsafe_allow_html=True)
        else:
            for i in range(kolon):
                nums=uret(mod,havuz,secim,sicak,soguk)
                bon=uret_bonus(mod,bonus_havuz,b_sicak,b_soguk) if bonus else None
                if on_numara:
                    c_top, c_btn = st.columns([5, 1])
                    with c_top:
                        st.markdown(f'<div class="row-label">Kolon {i+1}</div>',unsafe_allow_html=True)
                        st.markdown(toplar_html(nums,top_renk,bon,bonus_renk),unsafe_allow_html=True)
                    with c_btn:
                        st.write("")
                        if st.button("🔍", key=f"kolon_gonder_{i}", help="Kolon Analizine Gönder"):
                            st.session_state["kolon_secim"] = nums
                            st.session_state["kolon_secim_bonus"] = bon
                            st.session_state["kolon_oyun_adi"] = [k for k,v in KOLON_OYUN_CFG.items() if v["slug"]==slug][0]
                            st.session_state["kolon_gonderildi"] = True
                            st.rerun()
                else:
                    st.markdown(f'<div class="row-label">Kolon {i+1}</div>',unsafe_allow_html=True)
                    st.markdown(toplar_html(nums,top_renk,bon,bonus_renk),unsafe_allow_html=True)

        st.divider()
        st.success("Hayırlısı olsun! 🍀")
        st.markdown('<p class="info-note">Not: İstatistik bazlı seçim matematiksel kazanma olasılığını değiştirmez.</p>',unsafe_allow_html=True)

    # İstatistikler
    with st.expander("📊 İstatistikleri Göster / Gizle",expanded=False):
        if on_numara:
            t1,t2,t3=st.tabs(["🔥 En Çok Çıkanlar","❄️ En Uzun Çıkmayanlar","📅 Arşiv Özeti"])
        else:
            t1,t2=st.tabs(["🔥 En Çok Çıkanlar","❄️ En Uzun Çıkmayanlar"])
            t3=None

        with t1:
            goster_top_listesi(sicak,renk,"×",n=12)
            goster_grafik(sicak,"Çıkma Sayısı",renk,"Çıkma")
        with t2:
            goster_top_listesi(soguk,"#16a085"," çekiliş",n=12)
            goster_grafik(soguk,"Çıkmama Süresi (çekiliş)","#16a085","Çekiliş")

        if t3 and on_numara:
            with t3:
                tum=[]
                for row in ON_NUMARA_ARSIV: tum.extend(row["sayilar"])
                freq=Counter(tum)
                st.caption(f"Arşivdeki {len(ON_NUMARA_ARSIV)} çekilişe göre frekans analizi")
                data=sorted(freq.items())
                goster_grafik(data,"Tüm Arşivde Çıkma Sayısı",renk,"Çıkma")

        if bonus and b_sicak:
            st.divider()
            st.markdown("**🌟 Şans Topu İstatistikleri**")
            bc1,bc2=st.columns(2)
            with bc1:
                st.caption("En çok çıkan şans topları")
                goster_top_listesi(b_sicak,bonus_renk,"×",n=7)
            with bc2:
                st.caption("En uzun çıkmayan şans topları")
                goster_top_listesi(b_soguk,"#888"," çekiliş",n=7)

    if st.button("🔄 Veriyi Yenile",key=f"yenile_{slug}"):
        st.cache_data.clear(); st.rerun()

# ─── Ana sayfa ────────────────────────────────────────────────────────────────
st.title("🍀 Loto Kombinasyon Üretici")
st.caption(
    f"Sayısal Loto: {len(SAYISAL_ARSIV)} çekiliş  |  "
    f"Süper Loto: {len(SUPER_ARSIV)} çekiliş  |  "
    f"Şans Topu: {len(SANS_TOPU_ARSIV)} çekiliş  |  "
    f"On Numara: {len(ON_NUMARA_ARSIV)} çekiliş"
)

tab1,tab2,tab3,tab4,tab5=st.tabs(list(OYUNLAR.keys()) + ["🔍 Kolon Analizi"])
for tab,(isim,cfg) in zip([tab1,tab2,tab3,tab4],OYUNLAR.items()):
    with tab:
        oyun_sekmesi(cfg)
with tab5:
    kolon_analizi_sayfasi()

st.divider()
st.caption(f"Son yükleme: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
