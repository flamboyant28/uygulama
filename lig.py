import streamlit as st
import json, os

st.set_page_config(page_title="Lig Yöneticisi", page_icon="⚽", layout="wide")

_local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lig_data.json")
DATA_FILE = _local if os.access(os.path.dirname(_local), os.W_OK) else "/tmp/lig_data.json"

# ── Yardımcı ─────────────────────────────────────────────────────────────────
def next_id(fixtures):
    return max((m["id"] for m in fixtures), default=0) + 1

def default_data():
    return {
        "n": 0,
        "teams": [],
        "fixtures": []
    }

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            if "teams" in d and "fixtures" in d:
                if "n" not in d:
                    d["n"] = len(d["teams"])
                return d
        except Exception:
            pass
    return default_data()

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Kayıt hatası: {e}")

# ── İstatistik ────────────────────────────────────────────────────────────────
def compute_table(data):
    teams = data["teams"]
    if not teams:
        return []
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

# ── CSS ───────────────────────────────────────────────────────────────────────
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
  .zona-kd   { border-left:3px solid #e74c3c; }
  .zona-norm { border-left:3px solid transparent; }
  .sira-badge {
    display:inline-block; width:22px; height:22px; line-height:22px;
    border-radius:50%; font-size:11px; font-weight:700; text-align:center;
  }
  .sira-cl  { background:#3498db; color:#fff; }
  .sira-al  { background:#9b59b6; color:#fff; }
  .sira-kl  { background:#1abc9c; color:#fff; }
  .sira-kd  { background:#e74c3c; color:#fff; }
  .sira-norm{ background:#2d3748; color:#a0aec0; }
  .puan { font-weight:700; font-size:14px; color:#000; }
  .mac-kart {
    background:#1a2340; border-radius:10px; padding:14px 18px;
    margin-bottom:8px; border:1px solid #2d3748;
  }
  .mac-baslik { color:#718096; font-size:11px; font-weight:600; margin-bottom:6px; }
  .takim-adi { font-size:14px; font-weight:700; color:#000; text-align:center; }
  .vs { color:#4a5568; font-size:18px; font-weight:700; text-align:center; }
  .metric-card {
    background:#1a2340; border-radius:10px; padding:16px;
    border:1px solid #2d3748; text-align:center; margin-bottom:8px;
  }
  .metric-val { font-size:28px; font-weight:700; color:#fff; }
  .metric-lbl { font-size:12px; color:#718096; margin-top:4px; }
  .sidebar-title { color:#a0aec0; font-size:11px; font-weight:700;
    text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; }
  .ekle-kart {
    background:#1a2340; border-radius:10px; padding:16px;
    border:1px solid #2d3748; margin-bottom:12px;
  }
  div[data-testid="stNumberInput"] input { text-align:center; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data
N = len(data["teams"])

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Lig Ayarları")
    st.markdown("---")

    # Zona ayarları
    st.markdown('<div class="sidebar-title">🏅 Avrupa Zonaları</div>', unsafe_allow_html=True)
    cl_limit = st.number_input("🔵 Şampiyonlar Ligi", min_value=0, max_value=max(N,1), value=min(3, N), step=1, key="cl")
    al_limit = st.number_input("🟣 Avrupa Ligi",       min_value=0, max_value=max(N,1), value=min(5, N), step=1, key="al")
    kl_limit = st.number_input("🟢 Konferans Ligi",    min_value=0, max_value=max(N,1), value=min(7, N), step=1, key="kl")

    st.markdown('<div class="sidebar-title" style="margin-top:10px">🔻 Küme Düşme</div>', unsafe_allow_html=True)
    kd_count = st.number_input("Son kaç takım düşer?", min_value=0, max_value=max(N//2,1), value=min(3, max(N//2,0)), step=1, key="kd")
    kd_start  = N - kd_count + 1

    st.markdown("---")

    # Lig durumu
    played_sb = sum(1 for m in data["fixtures"] if m["played"])
    total_sb  = len(data["fixtures"])
    pct = int(played_sb / total_sb * 100) if total_sb else 0
    st.markdown('<div class="sidebar-title">📊 Lig Durumu</div>', unsafe_allow_html=True)
    st.progress(pct / 100)
    st.markdown(
        f"<div style='color:#718096;font-size:12px;text-align:center'>"
        f"{played_sb} / {total_sb} maç oynandı ({pct}%)</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div style='color:#718096;font-size:12px;text-align:center;margin-top:4px'>"
        f"{N} takım</div>", unsafe_allow_html=True
    )

# ── Başlık ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:16px 0 8px">
  <span style="font-size:32px">⚽</span>
  <h1 style="margin:4px 0;font-size:26px;color:#fff">LİG YÖNETİCİSİ</h1>
  <p style="color:#718096;font-size:13px">{N} Takım · {total_sb} Maç</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Puan Tablosu",
    "⚽ Skor Girişi",
    "📅 Fikstür",
    "➕ Fikstür Oluştur",
    "⚙️ Ayarlar"
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — PUAN TABLOSU
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    table = compute_table(data)

    if not table:
        st.info("Henüz takım yok. **Ayarlar** sekmesinden takım ekle.")
    else:
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
            col.markdown(f'<div class="metric-card"><div class="metric-val">{val}</div>'
                         f'<div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Zona açıklaması
        zona_info = []
        if cl_limit > 0:
            zona_info.append(f'<span><span style="color:#3498db">●</span> 1-{cl_limit} Şampiyonlar Ligi</span>')
        if al_limit > cl_limit:
            zona_info.append(f'<span><span style="color:#9b59b6">●</span> {cl_limit+1}-{al_limit} Avrupa Ligi</span>')
        if kl_limit > al_limit:
            zona_info.append(f'<span><span style="color:#1abc9c">●</span> {al_limit+1}-{kl_limit} Konferans Ligi</span>')
        if kd_count > 0:
            zona_info.append(f'<span><span style="color:#e74c3c">●</span> {kd_start}-{N} Küme Düşme</span>')

        if zona_info:
            st.markdown(
                f'<div style="display:flex;gap:16px;margin-bottom:12px;font-size:12px;'
                f'color:#a0aec0;flex-wrap:wrap">{"".join(zona_info)}</div>',
                unsafe_allow_html=True
            )

        html = '<table class="lig-table"><thead><tr>'
        for h in ["Sıra","Takım","O","G","B","M","AG","YG","AV","Puan","İç O","İç G","İç B","İç M","Son 5"]:
            cls = "left" if h == "Takım" else ""
            html += f'<th class="{cls}">{h}</th>'
        html += "</tr></thead><tbody>"

        for row in table:
            s = row["Sıra"]
            if cl_limit > 0 and s <= cl_limit:
                zona_cls, sira_cls = "zona-cl", "sira-cl"
            elif al_limit > cl_limit and s <= al_limit:
                zona_cls, sira_cls = "zona-al", "sira-al"
            elif kl_limit > al_limit and s <= kl_limit:
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
    if not data["fixtures"]:
        st.info("Henüz maç yok. **Fikstür Oluştur** sekmesinden maç ekle.")
    else:
        all_weeks = sorted(set(m["week"] for m in data["fixtures"]))

        col_l, col_r = st.columns([3, 1])
        col_l.markdown("### Skor Girişi")
        week = col_r.selectbox("Hafta", all_weeks,
                                format_func=lambda w: f"Hafta {w}", key="week_sel")

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
                f'<div class="mac-baslik">MAÇ {m["id"]} · Hafta {m["week"]}</div>',
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
                m["hg"] = hg_new; m["ag"] = ag_new; m["played"] = played_new
                changed = True

        if changed:
            save_data(data)
            st.rerun()

        if st.button("💾 Kaydet", use_container_width=True, type="primary", key="skor_kaydet"):
            save_data(data)
            st.success("Kaydedildi!")

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — FİKSTÜR (görüntüle + sil)
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📅 Fikstür")

    if not data["fixtures"]:
        st.info("Henüz maç yok. **Fikstür Oluştur** sekmesinden maç ekle.")
    else:
        fa, fb, fc = st.columns(3)
        team_f = fa.selectbox("Takım", ["Tümü"] + data["teams"], key="fiks_team")
        hafta_options = ["Tümü"] + sorted(set(m["week"] for m in data["fixtures"]))
        hafta_f = fb.selectbox("Hafta", hafta_options, key="fiks_hafta")
        stat_f  = fc.selectbox("Durum", ["Tümü", "Oynandı", "Oynanmadı"], key="fiks_stat")

        flt = list(data["fixtures"])
        if team_f != "Tümü":
            flt = [m for m in flt if m["home"] == team_f or m["away"] == team_f]
        if hafta_f != "Tümü":
            flt = [m for m in flt if m["week"] == hafta_f]
        if stat_f == "Oynandı":
            flt = [m for m in flt if m["played"]]
        elif stat_f == "Oynanmadı":
            flt = [m for m in flt if not m["played"]]

        st.markdown(f"<p style='color:#718096;font-size:13px'>{len(flt)} maç</p>",
                    unsafe_allow_html=True)

        html2 = '<table class="lig-table"><thead><tr>'
        for h in ["No", "Hafta", "Ev Sahibi", "Skor", "Deplasman", "Durum", "Sil"]:
            cls = "left" if h in ["Ev Sahibi", "Deplasman"] else ""
            html2 += f'<th class="{cls}">{h}</th>'
        html2 += "</tr></thead><tbody>"

        for m in flt:
            if m["played"]:
                skor = f'<b>{m["hg"]} - {m["ag"]}</b>'
                if m["hg"] > m["ag"]:   res_color, res = "#27ae60", "EV SAHİBİ"
                elif m["hg"] < m["ag"]: res_color, res = "#e74c3c", "DEPLASMAN"
                else:                   res_color, res = "#f39c12", "BERABERE"
                durum = f'<span style="color:{res_color};font-size:11px;font-weight:700">{res}</span>'
            else:
                skor  = '<span style="color:#4a5568">vs</span>'
                durum = '<span style="color:#4a5568;font-size:11px">—</span>'

            html2 += (
                f'<tr><td>{m["id"]}</td><td>{m["week"]}</td>'
                f'<td class="left">{m["home"]}</td><td>{skor}</td>'
                f'<td class="left">{m["away"]}</td><td>{durum}</td>'
                f'<td>—</td></tr>'
            )
        html2 += "</tbody></table>"
        st.markdown(html2, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # Maç silme
        with st.expander("🗑️ Maç Sil"):
            mac_ids = [m["id"] for m in data["fixtures"]]
            mac_labels = {
                m["id"]: f"#{m['id']} | H{m['week']} | {m['home']} vs {m['away']}"
                for m in data["fixtures"]
            }
            del_id = st.selectbox("Silinecek maç", mac_ids,
                                   format_func=lambda x: mac_labels[x], key="del_mac")
            if st.button("🗑️ Seçili Maçı Sil", type="secondary", key="del_mac_btn"):
                data["fixtures"] = [m for m in data["fixtures"] if m["id"] != del_id]
                save_data(data)
                st.success("Maç silindi.")
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — FİKSTÜR OLUŞTUR
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### ➕ Fikstür Oluştur")

    if not data["teams"]:
        st.warning("Önce **Ayarlar** sekmesinden takımları ekle.")
    else:
        mod = st.radio("Mod seç", ["Otomatik Round-Robin", "Tek Maç Ekle", "Hafta Oluştur"], horizontal=True)

        st.markdown("---")

        teams = data["teams"]

        # ── MOD 0: Otomatik Round-Robin ───────────────────────────────────
        if mod == "Otomatik Round-Robin":

            n = len(teams)
            if n % 2 != 0:
                st.warning("Round-robin için çift sayıda takım gerekiyor. Ayarlar'dan bir takım daha ekle.", icon="⚠️")
            else:
                total_mac = n * (n - 1)
                total_hafta = (n - 1) * 2
                st.info(f"**{n} takım** → {total_mac} maç · {total_hafta} hafta (çift devreli)", icon="📋")

                mevcut = len(data["fixtures"])
                if mevcut > 0:
                    st.warning(f"Mevcut {mevcut} maç silinecek ve yeni fikstür oluşturulacak!", icon="⚠️")

                if st.button("🔄 Fikstürü Oluştur", type="primary", use_container_width=True, key="rr_btn"):
                    def round_robin(teams):
                        n = len(teams)
                        lst = list(range(n))
                        rounds = []
                        for _ in range(n - 1):
                            pairs = [(lst[i], lst[n - 1 - i]) for i in range(n // 2)]
                            rounds.append(pairs)
                            lst = [lst[0]] + [lst[-1]] + lst[1:-1]
                        return rounds

                    r1 = round_robin(teams)
                    r2 = [[(b, a) for a, b in rnd] for rnd in r1]
                    fixtures = []
                    mid = 1
                    for devre, rounds in enumerate([r1, r2], 1):
                        for w_idx, pairs in enumerate(rounds):
                            week = w_idx + 1 + (n - 1) * (devre - 1)
                            for hi, ai in pairs:
                                fixtures.append({
                                    "id": mid, "week": week, "devre": devre,
                                    "home": teams[hi], "away": teams[ai],
                                    "hg": None, "ag": None, "played": False
                                })
                                mid += 1
                    data["fixtures"] = fixtures
                    save_data(data)
                    st.success(f"✅ {len(fixtures)} maçlık fikstür oluşturuldu!")
                    st.rerun()

        # ── MOD 1: Tek Maç Ekle ───────────────────────────────────────────
        elif mod == "Tek Maç Ekle":
            st.markdown("#### Maç Bilgileri")
            with st.container():
                c1, c2, c3 = st.columns([2, 1, 2])
                home = c1.selectbox("Ev Sahibi", teams, key="add_home")
                away_teams = [t for t in teams if t != home]
                away = c3.selectbox("Deplasman", away_teams, key="add_away")

                hafta_mevcut = sorted(set(m["week"] for m in data["fixtures"]))
                max_hafta = max(hafta_mevcut, default=0)

                c4, c5, c6 = st.columns(3)
                hafta_mod = c4.radio("Hafta", ["Var olan", "Yeni"], horizontal=True, key="hafta_mod")
                if hafta_mod == "Var olan" and hafta_mevcut:
                    hafta = c5.selectbox("Hafta seç", hafta_mevcut, key="add_hafta_sel")
                else:
                    hafta = c5.number_input("Hafta no", min_value=1,
                                             value=max_hafta + 1, step=1, key="add_hafta_new")

                # Skor şimdi girilsin mi?
                skor_simdi = c6.checkbox("Skoru şimdi gir", key="skor_simdi")

                hg_val, ag_val, played_val = 0, 0, False
                if skor_simdi:
                    cs1, cs2, cs3 = st.columns([1,1,1])
                    hg_val = cs1.number_input(f"{home} gol", min_value=0, max_value=30,
                                               value=0, key="add_hg")
                    ag_val = cs3.number_input(f"{away} gol", min_value=0, max_value=30,
                                               value=0, key="add_ag")
                    played_val = True

                if st.button("➕ Maç Ekle", type="primary", use_container_width=True, key="ekle_mac"):
                    if home == away:
                        st.error("Ev sahibi ve deplasman aynı olamaz.")
                    else:
                        yeni = {
                            "id": next_id(data["fixtures"]),
                            "week": int(hafta),
                            "devre": 1,
                            "home": home,
                            "away": away,
                            "hg": hg_val if played_val else None,
                            "ag": ag_val if played_val else None,
                            "played": played_val
                        }
                        data["fixtures"].append(yeni)
                        save_data(data)
                        st.success(f"✅ {home} vs {away} — Hafta {hafta} eklendi!")
                        st.rerun()

        # ── MOD 2: Hafta Oluştur ──────────────────────────────────────────
        elif mod == "Hafta Oluştur":
            st.markdown("#### Hafta Oluştur")
            st.caption("Bir haftanın tüm maçlarını seç, toplu ekle.")

            hafta_mevcut = sorted(set(m["week"] for m in data["fixtures"]))
            max_hafta = max(hafta_mevcut, default=0)

            hc1, hc2 = st.columns(2)
            hafta_mod2 = hc1.radio("Hafta", ["Var olan", "Yeni"], horizontal=True, key="hafta_mod2")
            if hafta_mod2 == "Var olan" and hafta_mevcut:
                hafta_no = hc2.selectbox("Hafta seç", hafta_mevcut, key="hw_sel")
            else:
                hafta_no = hc2.number_input("Hafta no", min_value=1,
                                              value=max_hafta + 1, step=1, key="hw_new")

            # Kaç maç eklenecek
            n_mac = st.number_input("Kaç maç ekleyeceksin?", min_value=1,
                                     max_value=len(teams)//2, value=min(4, len(teams)//2),
                                     step=1, key="n_mac_hafta")

            mac_listesi = []
            valid = True
            for i in range(int(n_mac)):
                st.markdown(f"**Maç {i+1}**")
                mc1, mc2, mc3 = st.columns([2, 1, 2])
                h_opts = teams
                a_opts = teams
                ev  = mc1.selectbox("Ev", h_opts, key=f"hw_h_{i}")
                dep = mc3.selectbox("Dep", a_opts, key=f"hw_a_{i}")
                if ev == dep:
                    mc2.markdown("<br>", unsafe_allow_html=True)
                    st.warning(f"Maç {i+1}: Ev ve deplasman aynı olamaz.", icon="⚠️")
                    valid = False
                mac_listesi.append((ev, dep))

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Haftayı Ekle", type="primary", use_container_width=True, key="ekle_hafta"):
                if not valid:
                    st.error("Lütfen hataları düzelt.")
                else:
                    eklenen = 0
                    for ev, dep in mac_listesi:
                        yeni = {
                            "id": next_id(data["fixtures"]),
                            "week": int(hafta_no),
                            "devre": 1,
                            "home": ev,
                            "away": dep,
                            "hg": None, "ag": None, "played": False
                        }
                        data["fixtures"].append(yeni)
                        eklenen += 1
                    save_data(data)
                    st.success(f"✅ {eklenen} maç — Hafta {hafta_no} olarak eklendi!")
                    st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — AYARLAR
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### ⚙️ Ayarlar")

    # Dosya konumu
    st.markdown("#### 📁 Veri Dosyası")
    if DATA_FILE.startswith("/tmp"):
        st.warning(
            f"**Konum:** `{DATA_FILE}`\n\n"
            "Streamlit Cloud'da `/tmp` kullanılıyor. Restart'ta sıfırlanır. "
            "Düzenli **JSON indir** ile yedek al.", icon="⚠️"
        )
    else:
        st.success(f"**Konum:** `{DATA_FILE}` — Veriler kalıcı.", icon="✅")

    col_dl, col_up = st.columns(2)
    with col_dl:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                json_str = f.read()
            st.download_button("⬇️ JSON İndir", data=json_str,
                                file_name="lig_data.json", mime="application/json",
                                use_container_width=True)
    with col_up:
        uploaded = st.file_uploader("⬆️ JSON Yükle", type="json", label_visibility="collapsed")
        if uploaded:
            try:
                loaded = json.load(uploaded)
                if "teams" in loaded and "fixtures" in loaded:
                    if "n" not in loaded:
                        loaded["n"] = len(loaded["teams"])
                    st.session_state.data = loaded
                    save_data(loaded)
                    st.success("✅ Yüklendi!")
                    st.rerun()
                else:
                    st.error("Geçersiz format.")
            except Exception as e:
                st.error(f"Hata: {e}")

    st.markdown("---")

    # ── Takımlar ──────────────────────────────────────────────────────────
    st.markdown("#### 🏷️ Takım Yönetimi")

    # Yeni takım ekle
    with st.expander("➕ Yeni Takım Ekle", expanded=len(data["teams"]) == 0):
        yeni_takim = st.text_input("Takım adı", key="yeni_takim", max_chars=40)
        if st.button("Ekle", key="takim_ekle_btn", type="primary"):
            yeni_takim = yeni_takim.strip()
            if not yeni_takim:
                st.error("Takım adı boş olamaz.")
            elif yeni_takim in data["teams"]:
                st.error("Bu takım zaten var.")
            else:
                data["teams"].append(yeni_takim)
                data["n"] = len(data["teams"])
                save_data(data)
                st.success(f"✅ {yeni_takim} eklendi!")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Mevcut takımları düzenle
    if data["teams"]:
        st.markdown("**Mevcut Takımlar — İsim Düzenle**")
        st.caption("Değiştir butonuna bas → o takımın tüm maçları da güncellenir.")

        new_names = []
        cols_per_row = 3
        rows_needed = (len(data["teams"]) + cols_per_row - 1) // cols_per_row
        for row_i in range(rows_needed):
            cols = st.columns(cols_per_row)
            for col_i in range(cols_per_row):
                idx = row_i * cols_per_row + col_i
                if idx < len(data["teams"]):
                    val = cols[col_i].text_input(
                        f"{idx+1}.", value=data["teams"][idx],
                        key=f"tname_{idx}", max_chars=40
                    )
                    new_names.append((idx, val.strip()))

        if st.button("💾 İsimleri Kaydet", type="primary", use_container_width=True):
            changed_any = False
            for idx, new_name in new_names:
                if not new_name:
                    st.warning(f"{idx+1}. takım adı boş, atlandı.")
                    continue
                old_name = data["teams"][idx]
                if old_name != new_name:
                    for m in data["fixtures"]:
                        if m["home"] == old_name: m["home"] = new_name
                        if m["away"] == old_name: m["away"] = new_name
                    data["teams"][idx] = new_name
                    changed_any = True
            if changed_any:
                data["n"] = len(data["teams"])
                save_data(data)
                st.success("✅ Güncellendi!")
                st.rerun()
            else:
                st.info("Değişiklik yok.")

        st.markdown("<br>", unsafe_allow_html=True)

        # Takım sil
        with st.expander("🗑️ Takım Sil"):
            st.warning("Takım silinince o takımın tüm maçları da silinir!", icon="⚠️")
            del_team = st.selectbox("Silinecek takım", data["teams"], key="del_team_sel")
            if st.button("🗑️ Takımı Sil", type="secondary", key="del_team_btn"):
                data["fixtures"] = [
                    m for m in data["fixtures"]
                    if m["home"] != del_team and m["away"] != del_team
                ]
                data["teams"].remove(del_team)
                data["n"] = len(data["teams"])
                save_data(data)
                st.success(f"{del_team} silindi.")
                st.rerun()

    st.markdown("---")

    # Sıfırlama
    st.markdown("#### 🗑️ Sıfırlama")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🗑️ Tüm Skorları Sıfırla", use_container_width=True):
            for m in data["fixtures"]:
                m["hg"] = None; m["ag"] = None; m["played"] = False
            save_data(data)
            st.success("Skorlar sıfırlandı.")
            st.rerun()
    with col_r2:
        if st.button("💣 Her Şeyi Sıfırla", use_container_width=True, type="secondary"):
            if st.session_state.get("confirm_reset"):
                st.session_state.data = default_data()
                st.session_state.confirm_reset = False
                save_data(st.session_state.data)
                st.success("Sıfırlandı.")
                st.rerun()
            else:
                st.session_state.confirm_reset = True
                st.warning("⚠️ Emin misin? Tekrar bas.")
