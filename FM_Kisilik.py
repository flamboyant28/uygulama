import streamlit as st

st.set_page_config("FM Kişilik Tespiti", layout="centered")
st.title("🧬 FM Kişilik Tespiti")
st.caption("Gizli özellik değerlerini gir — kişilik profili otomatik hesaplanır.")

# =========================================================
# KİŞİLİK PROFİLLERİ
# =========================================================

PERSONALITY_PROFILES = [
    {
        "name": "⭐ Lider",
        "desc": "Sahada ve soyunma odasında söz sahibi. Zor anlarda takımını toplar, genç oyunculara yol gösterir.",
        "color": "#b8860b",
        "conditions": {"Liderlik": 14, "Baskıya Dayanıklılık": 13, "Önemli Maçlar": 13, "Süreklilik": 15},
        "negative": {},
    },
    {
        "name": "🔥 Hırslı Profesyonel",
        "desc": "Antrenman delisi. Potansiyelini sonuna kadar sıkıştırmak için her şeyi göze alan tip.",
        "color": "#e67e22",
        "conditions": {"Hırs": 15, "Profesyonellik": 14},
        "negative": {},
    },
    {
        "name": "🤝 Takım Oyuncusu",
        "desc": "Bireysel istatistiklerden çok takımın başarısını önemser.",
        "color": "#2ecc71",
        "conditions": {"Sportmenlik": 13, "Aidiyet Duygusu": 13, "Süreklilik": 14},
        "negative": {"Tartışma": 12, "Çirkeflik": 12},
    },
    {
        "name": "💎 Büyük Maç Oyuncusu",
        "desc": "Turnuva finalleri, derbiler... Rakam ne kadar büyük olursa performansı o kadar artar.",
        "color": "#9b59b6",
        "conditions": {"Önemli Maçlar": 15, "Baskıya Dayanıklılık": 13, "Süreklilik": 14},
        "negative": {},
    },
    {
        "name": "🧠 Çalışkan & Disiplinli",
        "desc": "Her antrenmanda yüzde yüz verir. Teknik direktörün güvendiği, soyunma odasının saygı duyduğu isim.",
        "color": "#3498db",
        "conditions": {"Profesyonellik": 15, "Çok Yönlülük": 12},
        "negative": {"Tartışma": 13},
    },
    {
        "name": "🧊 Buzdan Sinirler",
        "desc": "Penaltı vuruşunda nabzı düşen. Kriz anı onun sahnesi.",
        "color": "#00bcd4",
        "conditions": {"Baskıya Dayanıklılık": 16, "Önemli Maçlar": 14},
        "negative": {},
    },
    {
        "name": "🦁 Savaşçı",
        "desc": "Her topu son nefesiyle koşar. İndirimli oynamayı bilmez.",
        "color": "#ff6b35",
        "conditions": {"Huy": 16, "Baskıya Dayanıklılık": 13},
        "negative": {"Çirkeflik": 14},
    },
    {
        "name": "📖 Sakin Profesyonel",
        "desc": "Sessiz sedasız, yıllarca aynı kalitede oynayan istikrar abidesi.",
        "color": "#27ae60",
        "conditions": {"Profesyonellik": 14, "Süreklilik": 16, "Sportmenlik": 13},
        "negative": {"Tartışma": 11, "Hırs": 12},
    },
    {
        "name": "🌟 Tecrübeli Usta",
        "desc": "Genç oyunculara mentor olan, deneyimiyle değer yaratan isim.",
        "color": "#f39c12",
        "conditions": {"Liderlik": 13, "Süreklilik": 15, "Profesyonellik": 13, "Aidiyet Duygusu": 14},
        "negative": {},
    },
    {
        "name": "🎯 Mükemmeliyetçi",
        "desc": "En sert eleştirmeni kendisi. Eksikleri not alır, bir sonraki maça daha iyi hazırlanır.",
        "color": "#8e44ad",
        "conditions": {"Hırs": 15, "Profesyonellik": 16},
        "negative": {"Tartışma": 10},
    },
    {
        "name": "⚡ Karizmatik İsyankâr",
        "desc": "Sahada görkemli, soyunma odasında çalkantılı. Teknik direktörünü tüketir, taraftarı büyüler.",
        "color": "#e74c3c",
        "conditions": {"Hırs": 14, "Tartışma": 13},
        "negative": {"Sportmenlik": 12},
    },
    {
        "name": "🎭 Medya Yıldızı",
        "desc": "Kameralar açılınca performansı artar. Saha dışı gürültü bazen odağını dağıtır.",
        "color": "#e91e63",
        "conditions": {"Hırs": 14, "Çirkeflik": 13},
        "negative": {"Profesyonellik": 13, "Aidiyet Duygusu": 11},
    },
    {
        "name": "💤 Tembel Deha",
        "desc": "Sahaya girdiğinde dedirtir; ama antrenmanda o yeteneğin yarısı kadar efor sarf eder.",
        "color": "#607d8b",
        "conditions": {"Çok Yönlülük": 14},
        "negative": {"Profesyonellik": 10, "Hırs": 11},
    },
    {
        "name": "💔 Motivasyon Yoksunu",
        "desc": "Ateşi çoktan söndü. Sözleşmeyi doldurma modunda.",
        "color": "#546e7a",
        "conditions": {},
        "negative": {"Hırs": 8, "Profesyonellik": 10, "Süreklilik": 10},
    },
    {
        "name": "😤 Sorunlu Karakter",
        "desc": "Teknik direktörün kabusu. Soyunma odasında huzursuzluk yaratır.",
        "color": "#c0392b",
        "conditions": {"Tartışma": 15, "Çirkeflik": 14},
        "negative": {},
    },
    {
        "name": "💣 Zehirli Unsur",
        "desc": "Tek başına soyunma odasının havasını zehirleyebilir.",
        "color": "#b71c1c",
        "conditions": {"Tartışma": 16, "Çirkeflik": 15, "Huy": 15},
        "negative": {"Sportmenlik": 10, "Aidiyet Duygusu": 9},
    },
    {
        "name": "🏥 Sakatlanmaya Meyilli",
        "desc": "Yeteneği tartışılmaz ama sağlığı sürekli sorun çıkarıyor.",
        "color": "#7f8c8d",
        "conditions": {"Sakatlanma Eğilimi": 15},
        "negative": {},
    },
    {
        "name": "🌍 Uyumsuz Gezgin",
        "desc": "Yeni kültüre alışmak için zamana ihtiyacı var. Yabancı ligde başlangıçta zorlanır.",
        "color": "#95a5a6",
        "conditions": {},
        "negative": {"Uyum": 8, "Aidiyet Duygusu": 8},
    },
    # ── YENİ PROFİLLER ────────────────────────────────────────
    {
        "name": "🏟️ Kulüp Adamı",
        "desc": "Tek kulübü var, tek forması var. Transfer tekliflerini reddeder, kulübün bayrağı olarak kalır. Para değil, aidiyet güdüler onu.",
        "color": "#1a6b3c",
        "conditions": {"Aidiyet Duygusu": 16, "Süreklilik": 15, "Sportmenlik": 13},
        "negative": {"Tartışma": 12},
    },
    {
        "name": "🔄 Huzursuz Yıldız",
        "desc": "Sürekli daha büyük kulüp arayışında. Sözleşmesinin son yılında en iyi formunu gösterir. Kalmak için değil, gitmek için oynar.",
        "color": "#c0392b",
        "conditions": {"Hırs": 16},
        "negative": {"Aidiyet Duygusu": 10, "Süreklilik": 10},
    },
    {
        "name": "🌑 Gizli Kahraman",
        "desc": "Kamera önünde değil, soyunma odasında parlar. Sessizce her şeyi omuzlar, övgüyü başkasına bırakır. Teknik direktörün en güvendiği isim.",
        "color": "#2c3e50",
        "conditions": {"Profesyonellik": 16, "Süreklilik": 16, "Sportmenlik": 14},
        "negative": {"Tartışma": 10, "Çirkeflik": 10},
    },
    {
        "name": "💥 Patlak Bomba",
        "desc": "Sakinken tehlikeli, kışkırtılınca kontrol edilemez. Kırmızı kart istatistikleri dehşet verir. Rakip takımlar onu özellikle hedef alır.",
        "color": "#e74c3c",
        "conditions": {"Tartışma": 14, "Huy": 14},
        "negative": {"Sportmenlik": 11, "Profesyonellik": 12},
    },
    {
        "name": "🃏 Karanlık At",
        "desc": "Kimse beklemezken en kritik anlarda ortaya çıkar. Düşük beklentiyi sever, baskı altında gizli bir güç açığa çıkar.",
        "color": "#34495e",
        "conditions": {"Çok Yönlülük": 16, "Baskıya Dayanıklılık": 15},
        "negative": {"Hırs": 11},
    },
    {
        "name": "🌐 Uyum Ustası",
        "desc": "Her ülkeye, her kulübe, her takım arkadaşına hızla uyum sağlar. Yabancı ligde bile ilk haftadan eve döner gibi oynar.",
        "color": "#16a085",
        "conditions": {"Uyum": 17, "Çok Yönlülük": 14, "Sportmenlik": 12},
        "negative": {},
    },
    {
        "name": "⚔️ Rövanş Makinesi",
        "desc": "Eleştirilince daha da güçlenir. Şüphe duyulduğunda en iyi versiyonunu sahaya koyar. Baskıyı yakıta çevirir.",
        "color": "#8e44ad",
        "conditions": {"Önemli Maçlar": 16, "Hırs": 15, "Baskıya Dayanıklılık": 14},
        "negative": {},
    },
    # ── FALLBACK ──────────────────────────────────────────────
    {
        "name": "📋 Standart Profesyonel",
        "desc": "Belirgin bir karakter özelliği öne çıkmıyor. Dengeli, sürprizsiz profil.",
        "color": "#aaaaaa",
        "conditions": {},
        "negative": {},
        "_fallback": True,
    },
]

HIDDEN_ATTRS = [
    "Uyum", "Hırs", "Tartışma", "Aidiyet Duygusu",
    "Baskıya Dayanıklılık", "Profesyonellik",
    "Sportmenlik", "Huy", "Çok Yönlülük",
    "Çirkeflik", "Önemli Maçlar", "Sakatlanma Eğilimi", "Süreklilik",
]


# =========================================================
# TESPİT FONKSİYONU
# =========================================================

def detect_personality(hidden: dict) -> dict:
    scores = []
    for profile in PERSONALITY_PROFILES:
        if profile.get("_fallback"):
            continue
        score = 0
        matched = True
        for attr, threshold in profile["conditions"].items():
            val = hidden.get(attr, 10)
            if val >= threshold:
                score += (val - threshold) * 2
            else:
                matched = False
                break
        if not matched:
            continue
        for attr, threshold in profile.get("negative", {}).items():
            if hidden.get(attr, 10) >= threshold:
                matched = False
                break
        if matched:
            scores.append((profile, score))

    if not scores:
        for p in PERSONALITY_PROFILES:
            if p.get("_fallback"):
                return p
        return PERSONALITY_PROFILES[-1]

    return sorted(scores, key=lambda x: -x[1])[0][0]


# =========================================================
# UI
# =========================================================

st.subheader("🔒 Gizli Özellikler")
st.caption("Her değer 1–20 arasında. Yazınca kişilik otomatik hesaplanır.")

hidden = {}

for i in range(0, len(HIDDEN_ATTRS), 3):
    row_attrs = HIDDEN_ATTRS[i:i+3]
    cols = st.columns(3)
    for j, attr in enumerate(row_attrs):
        with cols[j]:
            hidden[attr] = st.number_input(attr, min_value=1, max_value=20, value=10, step=1, key=f"h_{attr}")

# ── Sonuç ─────────────────────────────────────────────────
st.divider()
profile = detect_personality(hidden)
color   = profile["color"]
name    = profile["name"]
desc    = profile["desc"]

st.markdown(
    f"""
    <div style='
        background:linear-gradient(135deg,#0d1117,#161b22);
        border:1px solid {color}44;
        border-left:4px solid {color};
        border-radius:12px;
        padding:18px 22px;
        margin:8px 0;
    '>
        <div style='font-size:20px;font-weight:800;color:{color};margin-bottom:6px'>{name}</div>
        <div style='font-size:13px;color:#8b949e;font-style:italic'>{desc}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Öne çıkan değerler (13+)
highlights = sorted(
    [(k, v) for k, v in hidden.items() if v >= 13],
    key=lambda x: -x[1]
)

if highlights:
    st.markdown("**Öne çıkan değerler**")
    badge_html = ""
    for attr, val in highlights:
        if val >= 17:   shade = "#3498db"
        elif val >= 14: shade = "#2ecc71"
        else:           shade = "#f1c40f"
        badge_html += (
            f"<span style='background:#21262d;border-radius:10px;"
            f"padding:3px 10px;font-size:12px;color:{shade};"
            f"margin:3px;display:inline-block'>{attr} {val}</span>"
        )
    st.markdown(badge_html, unsafe_allow_html=True)

# Eşleşen tüm profiller (ikinci olasılıklar)
st.divider()
st.caption("Tüm eşleşen profiller (skora göre)")

all_matches = []
for p in PERSONALITY_PROFILES:
    if p.get("_fallback"):
        continue
    score = 0
    matched = True
    for attr, thr in p["conditions"].items():
        val = hidden.get(attr, 10)
        if val >= thr:
            score += (val - thr) * 2
        else:
            matched = False
            break
    if not matched:
        continue
    for attr, thr in (p.get("negative") or {}).items():
        if hidden.get(attr, 10) >= thr:
            matched = False
            break
    if matched:
        all_matches.append((p, score))

all_matches.sort(key=lambda x: -x[1])

if all_matches:
    for p, sc in all_matches:
        st.markdown(
            f"<span style='color:{p['color']};font-size:13px'>{p['name']}</span>"
            f"<span style='color:#555;font-size:12px'> — skor: {sc}</span>",
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        f"<span style='color:#aaa;font-size:13px'>📋 Standart Profesyonel (varsayılan)</span>",
        unsafe_allow_html=True,
    )