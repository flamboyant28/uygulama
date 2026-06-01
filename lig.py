import streamlit as st
import json, os

st.set_page_config(page_title="Lig Yöneticisi", page_icon="⚽", layout="wide")

DATA_FILE = "lig_data.json"

# ── Fikstür üret ─────────────────────────────────────────────────────────────
def round_robin(teams):
    n = len(teams)
    lst = list(range(n))
    rounds = []
    for _ in range(n - 1):
        pairs = [(lst[i], lst[n - 1 - i]) for i in range(n // 2)]
        rounds.append(pairs)
        lst = [lst[0]] + [lst[-1]] + lst[1:-1]
    return rounds

def generate_fixtures(teams):
    n = len(teams)
    r1 = round_robin(teams)
    r2 = [[(b, a) for a, b in rnd] for rnd in r1]
    fixtures = []
    mid = 0
    for devre, rounds in enumerate([r1, r2], 1):
        for w_idx, pairs in enumerate(rounds):
            week = w_idx + 1 + (n - 1) * (devre - 1)
            for hi, ai in pairs:
                mid += 1
                fixtures.append({
                    "id": mid, "week": week, "devre": devre,
                    "home": teams[hi], "away": teams[ai],
                    "hg": None, "ag": None, "played": False
                })
    return fixtures

def make_teams(n):
    return [f"Takım {i}" for i in range(1, n + 1)]

def default_data(n=16):
    teams = make_teams(n)
    return {"n": n, "teams": teams, "fixtures": generate_fixtures(teams)}

# ── Veri yükle / kaydet ──────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_data()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── İstatistik hesapla ───────────────────────────────────────────────────────
def compute_table(data):
    teams = data["teams"]
    stats = {t: {"O":0,"G":0,"B":0,"M":0,"AG":0,"YG":0,
                 "IC_O":0,"IC_G":0,"IC_B":0,"IC_M":0,"form":[]} for t in teams}
    for m in data["fixtures"]:
        if not m["played"]:
            continue
        h, a = m["home"], m["away"]
        hg, ag = m["hg"], m["ag"]
        if h not in stats or a not in stats:
            continue
        stats[h]["O"] += 1; stats[a]["O"] += 1
        stats[h]["AG"] += hg; stats[h]["YG"] += ag
        stats[a]["AG"] += ag; stats[a]["YG"] += hg
        stats[h]["IC_O"] += 1
        if hg > ag:
            stats[h]["G"] += 1; stats[a]["M"] += 1
            stats[h]["IC_G"] += 1
            stats[h]["form"].append("G"); stats[a]["form"].append("M")
        elif hg < ag:
            stats[a]["G"] += 1; stats[h]["M"] += 1
            stats[h]["IC_M"] += 1
            stats[h]["form"].append("M"); stats[a]["form"].append("G")
        else:
            stats[h]["B"] += 1; stats[a]["B"] += 1
            stats[h]["IC_B"] += 1
            stats[h]["form"].append("B"); stats[a]["form"].append("B")

    rows = []
    for t in teams:
        s = stats[t]
        puan = s["G"] * 3 + s["B"]
        av = s["AG"] - s["YG"]
        rows.append({
            "Takım": t, "O": s["O"], "G": s["G"], "B": s["B"], "M": s["M"],
            "AG": s["AG"], "YG": s["YG"], "AV": av, "Puan": puan,
            "İç O": s["IC_O"], "İç G": s["IC_G"], "İç B": s["IC_B"], "İç M": s["IC_M"],
            "form": s["form"][-5:]
        })
    rows.sort(key=lambda x: (-x["Puan"], -x["AV"], -x["AG"]))
    for i, r in enumerate(rows):
        r["Sıra"] = i + 1
    return rows

def form_html(form5):
    colors = {"G": "#27ae60", "B": "#f39c12", "M": "#e74c3c"}
    badges = "".join(
        f'<span style="background:{colors[f]};color:#fff;border-radius:4px;'
        f'padding:1px 6px;margin:1px;font-size:11px;font-weight:700">{f}</span>'
        for f in form5
    )
    return badges or '<span style="color:#4a5568">—</span>'

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .lig-table { width:100%; border-collapse:collapse; font-size:13px; }
  .lig-table th {
    background:#1a2340; color:#a0aec0; padding:8px 10px;
    text-align:center; border-bottom:2px solid #2d3748;
    font-weight:600; font-size:12px;
  }
  .lig-table th.left { text-align:left; }
  .lig-table td { padding:7px 10px; text-align:center; border-bottom:1px solid #1e2535; }
  .lig-table td.left { text-align:left; font-weight:600; }
  .lig-table tr:hover td { background:#1a2340 !important; }
  .zona-cl   { border-left:3px solid #3498db; }
  .zona-al   { border-left:3px solid #9b59b6; }
  .zona-kl   { border-left:3px solid #1abc9c; }
  .zona-po   { border-left:3px solid #f39c12; }
  .zona-kd   { border-left:3px solid #e74c3c; }
  .zona-norm { border-left:3px solid transparent; }
  .sira-badge {
    display:inline-block; width:22px; height:22px; line-height:22px;
    border-radius:50%; font-size:11px; font-weight:700; text-align:center;
  }
  .sira-cl  { background:#3498db; color:#fff; }
  .sira-al  { background:#9b59b6; color:#fff; }
  .sira-kl  { background:#1abc9c; color:#fff; }
  .sira-po  { background:#f39c12; color:#fff; }
  .sira-kd  { background:#e74c3c; color:#fff; }
  .sira-norm{ background:#2d3748; color:#a0aec0; }
  .puan { font-weight:700; font-size:14px; color:#fff; }
  .mac-kart {
    background:#1a2340; border-radius:10px; padding:14px 18px;
    margin-bottom:10px; border:1px solid #2d3748;
  }
  .mac-baslik { color:#718096; font-size:11px; font-weight:600; margin-bottom:8px; }
  .takim-adi { font-size:14px; font-weight:700; color:#fff; text-align:center; }
  .vs { color:#4a5568; font-size:18px; font-weight:700; text-align:center; }
  .metric-card {
    background:#1a2340; border-radius:10px; padding:16px;
    border:1px solid #2d3748; text-align:center; margin-bottom:8px;
  }
  .metric-val { font-size:28px; font-weight:700; color:#fff; }
  .metric-lbl { font-size:12px; color:#718096; margin-top:4px; }
  .sidebar-section {
    background:#1a2340; border-radius:10px; padding:14px;
    border:1px solid #2d3748; margin-bottom:12px;
  }
  .sidebar-title { color:#a0aec0; font-size:11px; font-weight:700;
    text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; }
  div[data-testid="stNumberInput"] input { text-align:center; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data
N = data["n"]

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Lig Ayarları")
    st.markdown("---")

    # ── Takım sayısı ──────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-title">📋 Takım Sayısı</div>', unsafe_allow_html=True)

    # Çift sayı zorunlu (round-robin için)
    even_options = list(range(4, 33, 2))  # 4, 6, 8 ... 32
    current_idx = even_options.index(N) if N in even_options else even_options.index(16)
    new_n = st.select_slider(
        "Takım sayısı",
        options=even_options,
        value=even_options[current_idx],
        label_visibility="collapsed"
    )

    total_matches = new_n * (new_n - 1)
    total_weeks   = (new_n - 1) * 2
    st.markdown(
        f"<div style='color:#718096;font-size:12px;margin-top:6px'>"
        f"🏟️ {new_n} takım · {total_matches} maç · {total_weeks} hafta"
        f"</div>",
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Ligi sıfırla / yeniden oluştur ───────────────────────────────────
    st.markdown('<div class="sidebar-title">⚠️ Fikstür</div>', unsafe_allow_html=True)

    n_changed = new_n != N
    if n_changed:
        st.warning(f"Takım sayısı {N} → {new_n} olarak değişti. Fikstürü yeniden oluşturmak gerekiyor.")

    col_a, col_b = st.columns(2)
    reset_clicked  = col_a.button("🔄 Yeniden Oluştur", use_container_width=True,
                                   type="primary" if n_changed else "secondary")
    clear_clicked  = col_b.button("🗑️ Skorları Sıfırla", use_container_width=True)

    if reset_clicked:
        new_data = default_data(new_n)
        st.session_state.data = new_data
        save_data(new_data)
        st.success(f"{new_n} takımlı yeni fikstür oluşturuldu!")
        st.rerun()

    if clear_clicked:
        for m in data["fixtures"]:
            m["hg"] = None
            m["ag"] = None
            m["played"] = False
        save_data(data)
        st.success("Tüm skorlar sıfırlandı.")
        st.rerun()

    st.markdown("---")

    # ── Lig özeti ─────────────────────────────────────────────────────────
    played_sb = sum(1 for m in data["fixtures"] if m["played"])
    total_sb  = len(data["fixtures"])
    pct = int(played_sb / total_sb * 100) if total_sb else 0

    st.markdown('<div class="sidebar-title">📊 Lig Durumu</div>', unsafe_allow_html=True)
    st.progress(pct / 100)
    st.markdown(
        f"<div style='color:#718096;font-size:12px;text-align:center'>"
        f"{played_sb} / {total_sb} maç oynandı ({pct}%)"
        f"</div>",
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='color:#4a5568;font-size:11px;text-align:center'>"
        "Çift devreli round-robin<br>Sıralama: Puan → Averaj → AG"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ── Avrupa zonaları ───────────────────────────────────────────────────
    st.markdown('<div class="sidebar-title">🏅 Avrupa Zonaları</div>', unsafe_allow_html=True)
    cl_limit = st.number_input("🔵 Şampiyonlar Ligi (ilk N takım)", min_value=0, max_value=new_n, value=3, step=1, key="cl")
    al_limit = st.number_input("🟣 Avrupa Ligi (ilk N takım)",      min_value=0, max_value=new_n, value=5, step=1, key="al")
    kl_limit = st.number_input("🟢 Konferans Ligi (ilk N takım)",   min_value=0, max_value=new_n, value=7, step=1, key="kl")

    st.markdown('<div class="sidebar-title" style="margin-top:10px">🔻 Küme Düşme</div>', unsafe_allow_html=True)
    kd_count = st.number_input("Son kaç takım düşer?", min_value=0, max_value=new_n // 2, value=3, step=1, key="kd")
    kd_start = new_n - kd_count + 1

# Veriyi güncelle (sidebar'dan sonra)
data = st.session_state.data
N = data["n"]

# ── Başlık ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:16px 0 8px">
  <span style="font-size:32px">⚽</span>
  <h1 style="margin:4px 0;font-size:26px;color:#fff">LİG YÖNETİCİSİ</h1>
  <p style="color:#718096;font-size:13px">{N} Takımlı · Çift Devreli · {len(data['fixtures'])} Maç</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🏆  Puan Tablosu", "⚽  Skor Girişi", "📅  Fikstür"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — PUAN TABLOSU
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    table = compute_table(data)

    played = sum(1 for m in data["fixtures"] if m["played"])
    total  = len(data["fixtures"])
    goals  = sum((m["hg"] or 0) + (m["ag"] or 0) for m in data["fixtures"] if m["played"])
    avg_g  = round(goals / played, 2) if played else 0

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, played, "Oynanan Maç"),
        (c2, total - played, "Kalan Maç"),
        (c3, goals, "Toplam Gol"),
        (c4, avg_g, "Maç Başı Gol"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
          <div class="metric-val">{val}</div>
          <div class="metric-lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Zona eşikleri — sidebar'dan gelir
    st.markdown(f"""
    <div style="display:flex;gap:16px;margin-bottom:12px;font-size:12px;color:#a0aec0;flex-wrap:wrap">
      {"" if cl_limit == 0 else f'<span><span style="color:#3498db">●</span> 1-{cl_limit} Şampiyonlar Ligi</span>'}
      {"" if al_limit <= cl_limit else f'<span><span style="color:#9b59b6">●</span> {cl_limit+1}-{al_limit} Avrupa Ligi</span>'}
      {"" if kl_limit <= al_limit else f'<span><span style="color:#1abc9c">●</span> {al_limit+1}-{kl_limit} Konferans Ligi</span>'}
      {"" if kd_count == 0 else f'<span><span style="color:#e74c3c">●</span> {kd_start}-{N} Küme Düşme</span>'}
    </div>
    """, unsafe_allow_html=True)

    html = '<table class="lig-table"><thead><tr>'
    for h in ["Sıra","Takım","O","G","B","M","AG","YG","AV","Puan","İç O","İç G","İç B","İç M","Son 5"]:
        cls = "left" if h == "Takım" else ""
        html += f'<th class="{cls}">{h}</th>'
    html += "</tr></thead><tbody>"

    for row in table:
        s = row["Sıra"]
        if s <= cl_limit and cl_limit > 0:
            zona_cls, sira_cls = "zona-cl", "sira-cl"
        elif s <= al_limit and al_limit > cl_limit:
            zona_cls, sira_cls = "zona-al", "sira-al"
        elif s <= kl_limit and kl_limit > al_limit:
            zona_cls, sira_cls = "zona-kl", "sira-kl"
        elif kd_count > 0 and s >= kd_start:
            zona_cls, sira_cls = "zona-kd", "sira-kd"
        else:
            zona_cls, sira_cls = "zona-norm", "sira-norm"

        av = row["AV"]
        av_color = "#27ae60" if av > 0 else ("#e74c3c" if av < 0 else "#a0aec0")

        html += (
            f'<tr>'
            f'<td class="{zona_cls}"><span class="sira-badge {sira_cls}">{s}</span></td>'
            f'<td class="left">{row["Takım"]}</td>'
            f'<td>{row["O"]}</td><td>{row["G"]}</td><td>{row["B"]}</td><td>{row["M"]}</td>'
            f'<td>{row["AG"]}</td><td>{row["YG"]}</td>'
            f'<td style="color:{av_color};font-weight:600">{av:+d}</td>'
            f'<td class="puan">{row["Puan"]}</td>'
            f'<td>{row["İç O"]}</td><td>{row["İç G"]}</td><td>{row["İç B"]}</td><td>{row["İç M"]}</td>'
            f'<td>{form_html(row["form"])}</td>'
            f'</tr>'
        )

    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — SKOR GİRİŞİ
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    all_weeks = sorted(set(m["week"] for m in data["fixtures"]))

    col_l, col_r = st.columns([3, 1])
    col_l.markdown("### Skor Girişi")
    week = col_r.selectbox("Hafta", all_weeks,
                            format_func=lambda w: f"Hafta {w}",
                            key="week_sel")

    week_matches = [m for m in data["fixtures"] if m["week"] == week]
    f1, f2 = st.columns(2)
    show_played   = f1.checkbox("Oynanmışları göster", value=True)
    show_unplayed = f2.checkbox("Oynanmamışları göster", value=True)

    filtered = [m for m in week_matches
                if (m["played"] and show_played) or (not m["played"] and show_unplayed)]

    played_w = sum(1 for m in week_matches if m["played"])
    st.markdown(
        f"<p style='color:#718096;font-size:13px'>"
        f"{week}. Hafta · {len(week_matches)} maç · {played_w} oynandı</p>",
        unsafe_allow_html=True
    )

    changed = False
    for m in filtered:
        st.markdown(
            f'<div class="mac-kart">'
            f'<div class="mac-baslik">MAÇ {m["id"]} · {m["devre"]}. Devre</div>',
            unsafe_allow_html=True
        )
        c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
        c1.markdown(f'<div class="takim-adi">{m["home"]}</div>', unsafe_allow_html=True)
        c3.markdown('<div class="vs">—</div>', unsafe_allow_html=True)
        c5.markdown(f'<div class="takim-adi">{m["away"]}</div>', unsafe_allow_html=True)

        hg_new = c2.number_input("", min_value=0, max_value=30,
                                  value=m["hg"] or 0, key=f"hg_{m['id']}",
                                  label_visibility="collapsed")
        ag_new = c4.number_input("", min_value=0, max_value=30,
                                  value=m["ag"] or 0, key=f"ag_{m['id']}",
                                  label_visibility="collapsed")
        played_new = st.checkbox("Oynandı ✓", value=m["played"], key=f"p_{m['id']}")
        st.markdown("</div>", unsafe_allow_html=True)

        if hg_new != m["hg"] or ag_new != m["ag"] or played_new != m["played"]:
            m["hg"] = hg_new
            m["ag"] = ag_new
            m["played"] = played_new
            changed = True

    if changed:
        save_data(data)
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾  Kaydet", use_container_width=True, type="primary"):
        save_data(data)
        st.success("Kaydedildi!")

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — FİKSTÜR
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Fikstür")

    fa, fb, fc = st.columns(3)
    devre_f = fa.selectbox("Devre", [0, 1, 2],
                            format_func=lambda x: "Tümü" if x == 0 else f"{x}. Devre")
    team_f  = fb.selectbox("Takım", ["Tümü"] + data["teams"])
    stat_f  = fc.selectbox("Durum", ["Tümü", "Oynandı", "Oynanmadı"])

    flt = data["fixtures"]
    if devre_f:
        flt = [m for m in flt if m["devre"] == devre_f]
    if team_f != "Tümü":
        flt = [m for m in flt if m["home"] == team_f or m["away"] == team_f]
    if stat_f == "Oynandı":
        flt = [m for m in flt if m["played"]]
    elif stat_f == "Oynanmadı":
        flt = [m for m in flt if not m["played"]]

    st.markdown(
        f"<p style='color:#718096;font-size:13px'>{len(flt)} maç listeleniyor</p>",
        unsafe_allow_html=True
    )

    html2 = '<table class="lig-table"><thead><tr>'
    for h in ["No", "Hafta", "Ev Sahibi", "Skor", "Deplasman", "Devre", "Durum"]:
        cls = "left" if h in ["Ev Sahibi", "Deplasman"] else ""
        html2 += f'<th class="{cls}">{h}</th>'
    html2 += "</tr></thead><tbody>"

    for m in flt:
        if m["played"]:
            skor = f'<b>{m["hg"]} - {m["ag"]}</b>'
            if m["hg"] > m["ag"]:
                res_color, res = "#27ae60", "EV SAHİBİ"
            elif m["hg"] < m["ag"]:
                res_color, res = "#e74c3c", "DEPLASMAN"
            else:
                res_color, res = "#f39c12", "BERABERE"
            durum = f'<span style="color:{res_color};font-size:11px;font-weight:700">{res}</span>'
        else:
            skor  = '<span style="color:#4a5568">vs</span>'
            durum = '<span style="color:#4a5568;font-size:11px">—</span>'

        html2 += (
            f'<tr>'
            f'<td>{m["id"]}</td>'
            f'<td>{m["week"]}</td>'
            f'<td class="left">{m["home"]}</td>'
            f'<td>{skor}</td>'
            f'<td class="left">{m["away"]}</td>'
            f'<td>{m["devre"]}</td>'
            f'<td>{durum}</td>'
            f'</tr>'
        )

    html2 += "</tbody></table>"
    st.markdown(html2, unsafe_allow_html=True)
