import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import io, math

# ── Sayfa Ayarları ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finansal Karar Destek Sistemi",
    page_icon="💰",
    layout="wide"
)

# ── Session State ─────────────────────────────────────────────────────────────
if 'kayitli_senaryolar' not in st.session_state:
    st.session_state.kayitli_senaryolar = []
if 'coklu_mevduat' not in st.session_state:
    st.session_state.coklu_mevduat = []
if 'son_mevduat_df' not in st.session_state:
    st.session_state.son_mevduat_df = None
if 'son_kredi_df' not in st.session_state:
    st.session_state.son_kredi_df = None
if 'son_taksit' not in st.session_state:
    st.session_state.son_taksit = 0.0

# ── Yardımcı Fonksiyonlar ─────────────────────────────────────────────────────
def tl(x):
    return f"₺{x:,.2f}".replace(",", ".")

def is_is_gunu(tarih):
    return tarih.weekday() < 5

def vade_sonu_tarihi_hesapla(gun_sayisi):
    bugun = date.today()
    teorik = bugun + timedelta(days=gun_sayisi)
    duz = teorik
    while not is_is_gunu(duz):
        duz += timedelta(days=1)
    return bugun, teorik, duz

def taksit_ayi_hesapla(baslangic, ay_no):
    yil = baslangic.year
    ay  = baslangic.month + ay_no
    if ay > 12:
        yil += (ay - 1) // 12
        ay   = ((ay - 1) % 12) + 1
    return date(yil, ay, 1).strftime("%Y %B")

def aylik_taksit_hesapla(kredi, aylik_faiz, vade):
    r, n = aylik_faiz / 100, vade
    if r == 0:
        return kredi / n
    return kredi * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

def mevduat_hesapla(anapara, faiz, gun, stopaj):
    yillik  = anapara * (faiz / 100)
    gunluk  = yillik / 365
    brut    = gunluk * gun
    stopaj_ = brut * (stopaj / 100)
    net     = brut - stopaj_
    return gunluk, brut, stopaj_, net

def reel_getiri_hesapla(net_getiri, anapara, enflasyon_yillik, gun):
    """Fisher denklemiyle reel getiri"""
    enf_kayip = anapara * (enflasyon_yillik / 100) * (gun / 365)
    return net_getiri - enf_kayip

# ── Excel Export ──────────────────────────────────────────────────────────────
def df_to_excel(dfs: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        for sheet, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet[:31], index=False)
    return buf.getvalue()

# ── PDF Export ────────────────────────────────────────────────────────────────
def df_to_pdf(df: pd.DataFrame, baslik: str) -> bytes:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=30, rightMargin=30,
                            topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(baslik, styles['Title']))
    elements.append(Spacer(1, 12))

    cols = list(df.columns)
    data = [cols] + df.astype(str).values.tolist()

    col_count = len(cols)
    col_w = (landscape(A4)[0] - 60) / col_count

    t = Table(data, colWidths=[col_w]*col_count, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
        ('FONTSIZE',      (0,0), (-1,0), 7),
        ('FONTSIZE',      (0,1), (-1,-1), 6.5),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('GRID',          (0,0), (-1,-1), 0.3, colors.HexColor('#cccccc')),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t)
    doc.build(elements)
    return buf.getvalue()

# ── Başlık ────────────────────────────────────────────────────────────────────
st.title("💰 Finansal Karar Destek Sistemi")
st.caption("Mevduat • Kredi • Hedef Hesap • Döviz • Analiz • Export")

# ── Sekmeler ──────────────────────────────────────────────────────────────────
tab_mev, tab_kredi, tab_hedef, tab_doviz, tab_analiz, tab_export = st.tabs([
    "📈 Mevduat",
    "🏦 Kredi",
    "🎯 Hedef Hesap",
    "💱 Döviz Karşılaştırması",
    "🔄 Kredi + Mevduat Analizi",
    "📤 Dışa Aktar",
])

# ═══════════════════════════════════════════════════════════════════════════════
# 📈 MEVDUAT
# ═══════════════════════════════════════════════════════════════════════════════
with tab_mev:
    st.header("📈 Mevduat Faiz Karar Destek Sistemi")

    c1, c2, c3, c4 = st.columns(4)
    with c1: anapara     = st.number_input("Anapara (TL)", value=200_000.0, step=100_000.0, key="anapara_tl_1")
    with c2: gun_sayisi  = st.number_input("Vade (Gün)",   value=32,        min_value=1, step=1, key="vade_gün_1")
    with c3: stopaj_orani= st.number_input("Stopaj (%)",   value=7.5,       step=0.1, key="stopaj_pct_1")
    with c4: enflasyon   = st.number_input("Yıllık Enflasyon (%)", value=65.0, step=1.0, # key eksik - bu satır devam ediyor
                                           help="Reel getiri hesabı için kullanılır")

    baslangic, teorik_bitis, duz_bitis = vade_sonu_tarihi_hesapla(gun_sayisi)
    st.info(f"📅 **Başlangıç:** {baslangic.strftime('%d %B %Y')} · "
            f"📆 **Teorik Vade Sonu:** {teorik_bitis.strftime('%d %B %Y')} · "
            f"🏦 **İş Gününe Kaydırılmış:** **{duz_bitis.strftime('%d %B %Y')}**")

    st.subheader("📌 Faiz Senaryoları")
    s1, s2, s3 = st.columns(3)
    with s1: faiz_a = st.slider("Senaryo A (%)", 0.0, 100.0, 35.0, 0.1)
    with s2: faiz_b = st.slider("Senaryo B (%)", 0.0, 100.0, 40.0, 0.1)
    with s3: faiz_c = st.slider("Senaryo C (%)", 0.0, 100.0, 50.0, 0.1)

    senaryolar = {"Senaryo A": faiz_a, "Senaryo B": faiz_b, "Senaryo C": faiz_c}
    rows, grafik = [], []

    for ad, faiz in senaryolar.items():
        gunluk, brut, stopaj_, net = mevduat_hesapla(anapara, faiz, gun_sayisi, stopaj_orani)
        reel = reel_getiri_hesapla(net, anapara, enflasyon, gun_sayisi)
        rows.append({
            "Senaryo": ad, "Faiz (%)": faiz, "Gün": gun_sayisi,
            "Günlük Faiz": tl(gunluk), "Brüt Getiri": tl(brut),
            "Stopaj": tl(stopaj_), "Net Getiri": tl(net),
            "Reel Getiri": tl(reel),
            "Reel +/-": "✅" if reel > 0 else "❌",
            "Vade Sonu Toplam": tl(anapara + net),
        })
        for g in range(1, gun_sayisi + 1):
            _, _, _, net_g = mevduat_hesapla(anapara, faiz, g, stopaj_orani)
            reel_g = reel_getiri_hesapla(net_g, anapara, enflasyon, g)
            grafik.append({"Gün": g, "Net Getiri": net_g, "Reel Getiri": reel_g, "Senaryo": ad})

    st.subheader("📊 Mevduat Senaryo Karşılaştırması")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    grafik_df = pd.DataFrame(grafik)
    fig_net = px.line(grafik_df, x="Gün", y="Net Getiri", color="Senaryo",
                      title="Gün Gün Birikimli Net Getiri", markers=False)
    fig_net.update_layout(yaxis_tickformat=",")
    fig_net.update_traces(hovertemplate="Gün: %{x}<br>Net Getiri: ₺%{y:,.2f}")
    st.plotly_chart(fig_net, use_container_width=True)

    # Reel getiri grafiği
    fig_reel = px.line(grafik_df, x="Gün", y="Reel Getiri", color="Senaryo",
                       title=f"Reel Getiri (Enflasyon {enflasyon:.1f}% düşüldükten sonra)",
                       markers=False)
    fig_reel.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Başabaş")
    fig_reel.update_layout(yaxis_tickformat=",")
    st.plotly_chart(fig_reel, use_container_width=True)

    # ── 24 Aylık Projeksiyon ──────────────────────────────────────────────────
    st.subheader("📅 48 Aylık Mevduat Projeksiyonu (Bileşik)")
    proj_senaryo = st.selectbox("Projeksiyon için senaryo seç",
                                list(senaryolar.keys()), key="proj_sel")
    proj_faiz = senaryolar[proj_senaryo]

    aylik_rows = []
    mevcut_ap = anapara
    for ay in range(1, 49):
        _, _, stopaj_t, net_g = mevduat_hesapla(mevcut_ap, proj_faiz, 32, stopaj_orani)
        brut_g = mevcut_ap * (proj_faiz / 100) * (32 / 365)
        reel_g = reel_getiri_hesapla(net_g, mevcut_ap, enflasyon, 32)
        aylik_rows.append({
            "Ay": ay,
            "Anapara": tl(mevcut_ap),
            "Brüt Getiri": tl(brut_g),
            "Stopaj": tl(stopaj_t),
            "Net Gelir": tl(net_g),
            "Reel Gelir": tl(reel_g),
            "Vade Sonu Toplam": tl(mevcut_ap + net_g),
        })
        mevcut_ap += net_g

    df_24ay = pd.DataFrame(aylik_rows)
    st.session_state.son_mevduat_df = df_24ay.copy()
    st.dataframe(df_24ay, use_container_width=True)

    # ── Senaryo Kaydetme ──────────────────────────────────────────────────────
    st.subheader("💾 Senaryo Kaydet")
    senaryo_ad = st.text_input("Senaryo adı", placeholder="örn: Garanti %40 32gün")
    if st.button("💾 Seçili Senaryoyu Kaydet") and senaryo_ad:
        faiz_sec = senaryolar[proj_senaryo]
        _, brut_s, stop_s, net_s = mevduat_hesapla(anapara, faiz_sec, gun_sayisi, stopaj_orani)
        reel_s = reel_getiri_hesapla(net_s, anapara, enflasyon, gun_sayisi)
        st.session_state.kayitli_senaryolar.append({
            "Ad": senaryo_ad, "Anapara": tl(anapara), "Faiz (%)": faiz_sec,
            "Gün": gun_sayisi, "Net Getiri": tl(net_s), "Reel Getiri": tl(reel_s),
            "Vade Sonu Toplam": tl(anapara + net_s), "Tarih": date.today().strftime("%d.%m.%Y"),
        })
        st.success(f"'{senaryo_ad}' kaydedildi!")

    if st.session_state.kayitli_senaryolar:
        st.subheader("📋 Kayıtlı Senaryolar")
        df_kyd = pd.DataFrame(st.session_state.kayitli_senaryolar)
        st.dataframe(df_kyd, use_container_width=True)
        if st.button("🗑 Tüm Kayıtlı Senaryoları Sil"):
            st.session_state.kayitli_senaryolar = []
            st.rerun()

    # ── Çoklu Mevduat ─────────────────────────────────────────────────────────
    with st.expander("➕ Birden Fazla Mevduat Takibi"):
        st.caption("Aynı anda birden fazla mevduatı karşılaştır")
        cm1, cm2, cm3, cm4 = st.columns(4)
        with cm1: cm_ap   = st.number_input("Anapara", value=100_000.0, step=50_000.0, key="cm_ap")
        with cm2: cm_faiz = st.number_input("Faiz (%)", value=40.0, step=0.5, key="cm_faiz")
        with cm3: cm_gun  = st.number_input("Vade (Gün)", value=32, min_value=1, step=1, key="cm_gun")
        with cm4: cm_ad   = st.text_input("Açıklama", placeholder="Garanti Bankası", key="cm_ad")

        if st.button("➕ Mevduatı Listeye Ekle"):
            _, brut_m, stop_m, net_m = mevduat_hesapla(cm_ap, cm_faiz, cm_gun, stopaj_orani)
            reel_m = reel_getiri_hesapla(net_m, cm_ap, enflasyon, cm_gun)
            st.session_state.coklu_mevduat.append({
                "Açıklama": cm_ad or f"Mevduat {len(st.session_state.coklu_mevduat)+1}",
                "Anapara": tl(cm_ap), "Faiz (%)": cm_faiz, "Gün": cm_gun,
                "Net Getiri": tl(net_m), "Reel Getiri": tl(reel_m),
                "Vade Sonu": tl(cm_ap + net_m),
            })
            st.rerun()

        if st.session_state.coklu_mevduat:
            df_cm = pd.DataFrame(st.session_state.coklu_mevduat)
            st.dataframe(df_cm, use_container_width=True)
            c_t1, c_t2 = st.columns(2)
            with c_t1:
                if st.button("🗑 Listeyi Temizle"):
                    st.session_state.coklu_mevduat = []
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# 🏦 KREDİ
# ═══════════════════════════════════════════════════════════════════════════════
with tab_kredi:
    st.header("🏦 Kredi Karar Destek Sistemi")

    kredi_turleri = {
        "Konut Kredisi":   {"faiz": 1.85, "kkdf": 0.0,  "bsmv": 0.0},
        "Taşıt Kredisi":   {"faiz": 2.50, "kkdf": 0.15, "bsmv": 0.15},
        "İhtiyaç Kredisi": {"faiz": 3.50, "kkdf": 0.15, "bsmv": 0.15},
    }

    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1: kredi_tutari         = st.number_input("Kredi Tutarı (TL)", value=200_000.0, step=10_000.0, key="kredi_tutarı_1")
    with kc2: vade                 = st.slider("Vade (Ay)", 3, 120, 20)
    with kc3: kredi_turu           = st.selectbox("Kredi Türü", kredi_turleri.keys())
    with kc4: kredi_bas_tarihi     = st.date_input("Başlangıç Tarihi", value=date.today())

    aylik_faiz  = st.number_input("Aylık Faiz (%)", value=kredi_turleri[kredi_turu]["faiz"], step=0.01, key="aylık_faiz_p_1")
    kkdf_orani  = kredi_turleri[kredi_turu]["kkdf"]
    bsmv_orani  = kredi_turleri[kredi_turu]["bsmv"]
    efektif     = aylik_faiz * (1 + kkdf_orani + bsmv_orani)

    hesaplanan_taksit = aylik_taksit_hesapla(kredi_tutari, efektif, vade)
    st.info(f"📌 Hesaplanan Aylık Taksit: **{tl(hesaplanan_taksit)}**")

    advanced = st.checkbox("🔧 Manuel taksit")
    # Manuel değilse hesaplanan taksiti kullan (widget değeri değil)
    if advanced:
        taksit = st.number_input("Aylık Taksit", value=hesaplanan_taksit,
                                  key="aylık_taksit_1")
    else:
        st.number_input("Aylık Taksit", value=hesaplanan_taksit,
                        disabled=True, key="aylık_taksit_1")
        taksit = hesaplanan_taksit  # Her zaman hesaplanan değeri kullan

    a1, a2 = st.columns(2)
    with a1: ara_odeme_ayi   = st.number_input("Ara Ödeme Ayı (0=yok)", 0, vade, 0, key="ara_ödeme_ay_1")
    with a2: ara_odeme_tutar = st.number_input("Ara Ödeme Tutarı", value=0.0, step=50_000.0, key="ara_ödeme_tu_1")

    # Amortisman tablosu oluştur
    rows_k, kalan = [], kredi_tutari
    hata_msg = None
    for ay in range(1, vade + 1):
        faiz_k    = round(kalan * (aylik_faiz / 100), 2)
        kkdf_k    = round(faiz_k * kkdf_orani, 2)
        bsmv_k    = round(faiz_k * bsmv_orani, 2)
        faiz_top  = round(faiz_k + kkdf_k + bsmv_k, 2)
        donem_ay  = taksit_ayi_hesapla(kredi_bas_tarihi, ay)
        anapara_k = round(taksit - faiz_top, 2)
        if anapara_k <= 0:
            hata_msg = (f"⚠️ Taksit faizi karşılamıyor. "
                        f"Aylık faiz: {tl(faiz_top)}, Taksit: {tl(taksit)}. "
                        f"Taksit en az {tl(faiz_top + 1)} olmalı.")
            break
        ara = ara_odeme_tutar if ay == ara_odeme_ayi else 0.0
        kalan = max(0, round(kalan - anapara_k - ara, 2))
        rows_k.append({
            "Dönem": ay, "Dönem (Ay)": donem_ay,
            "Taksit": taksit, "Anapara": anapara_k,
            "Faiz": faiz_k, "KKDF": kkdf_k, "BSMV": bsmv_k,
            "Faiz+KKDF+BSMV": faiz_top, "Ara Ödeme": ara,
            "Kalan Anapara": kalan,
            "Ödenen Taksit": round(ay * taksit, 2),
            "Ödenen %": round(ay * taksit / (taksit * vade) * 100, 1),
        })
        if kalan == 0:
            break

    if hata_msg or not rows_k:
        st.error(hata_msg or "⚠️ Amortisman tablosu oluşturulamadı.")
        st.stop()

    df_kredi = pd.DataFrame(rows_k)
    st.session_state.son_kredi_df  = df_kredi.copy()
    st.session_state.son_taksit    = taksit

    # Özet metrikler
    toplam_taksit = taksit * len(df_kredi)
    toplam_faiz_k = df_kredi["Faiz"].sum()
    toplam_kkdf   = df_kredi["KKDF"].sum()
    toplam_bsmv   = df_kredi["BSMV"].sum()
    toplam_fvk    = df_kredi["Faiz+KKDF+BSMV"].sum()

    st.markdown("### 📊 Kredi Özeti")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Toplam Taksit",  tl(toplam_taksit))
        st.metric("Toplam Anapara", tl(kredi_tutari))
        st.metric("Toplam Faiz",    tl(toplam_faiz_k))
    with m2:
        st.metric("Toplam KKDF",    tl(toplam_kkdf))
        st.metric("Toplam BSMV",    tl(toplam_bsmv))
        st.metric("F+KKDF+BSMV",   tl(toplam_fvk))
    with m3:
        st.metric("Maliyet Oranı",  f"%{toplam_fvk/kredi_tutari*100:.1f}")
        st.metric("Aylık Taksit",   tl(taksit))

    # Waterfall grafiği
    st.subheader("🌊 Kredi Maliyet Dağılımı (Şelale Grafiği)")
    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute","relative","relative","relative","total"],
        x=["Kredi Tutarı","Faiz","KKDF","BSMV","Toplam Geri Ödeme"],
        y=[kredi_tutari, toplam_faiz_k, toplam_kkdf, toplam_bsmv, 0],
        text=[tl(kredi_tutari), tl(toplam_faiz_k), tl(toplam_kkdf), tl(toplam_bsmv), tl(toplam_taksit)],
        textposition="outside",
        connector={"line":{"color":"rgb(63,63,63)"}},
        increasing={"marker":{"color":"#ef5350"}},
        decreasing={"marker":{"color":"#66bb6a"}},
        totals={"marker":{"color":"#1a6fff"}},
    ))
    fig_wf.update_layout(title="Kredi Toplam Maliyet Dağılımı",
                         yaxis_title="Tutar (₺)", yaxis_tickformat=",")
    st.plotly_chart(fig_wf, use_container_width=True)

    # Kalan anapara grafiği
    fig_kalan = px.area(df_kredi, x="Dönem", y="Kalan Anapara",
                        title="Kalan Anapara (Ay Ay)")
    fig_kalan.update_layout(yaxis_tickformat=",")
    st.plotly_chart(fig_kalan, use_container_width=True)

    # Anapara vs Faiz bar grafiği
    fig_av = px.bar(df_kredi, x="Dönem", y=["Anapara","Faiz","KKDF","BSMV"],
                    title="Her Taksitte Anapara / Faiz / Vergi Dağılımı",
                    barmode="stack")
    fig_av.update_layout(yaxis_tickformat=",")
    st.plotly_chart(fig_av, use_container_width=True)

    # Amortisman tablosu
    st.subheader("📋 Amortisman Tablosu")
    df_kredi_g = df_kredi.copy()
    for col in ["Taksit","Anapara","Faiz","KKDF","BSMV","Faiz+KKDF+BSMV",
                "Ara Ödeme","Kalan Anapara","Ödenen Taksit"]:
        df_kredi_g[col] = df_kredi_g[col].apply(tl)
    st.dataframe(df_kredi_g, use_container_width=True)

    # ── Erken Kapatma Senaryosu ───────────────────────────────────────────────
    st.subheader("🔚 Erken Kapatma Senaryosu")
    st.caption("Krediyi belirli bir ayda erken kapatsanız ne olurdu?")

    erken_ay = st.slider("Erken Kapatma Ayı", 1, len(df_kredi), min(12, len(df_kredi)))
    erken_row = df_kredi[df_kredi["Dönem"] == erken_ay]

    if not erken_row.empty:
        kalan_anapara_erken = erken_row["Kalan Anapara"].values[0]
        odenen_toplam_faiz  = df_kredi[df_kredi["Dönem"] <= erken_ay]["Faiz+KKDF+BSMV"].sum()
        kalan_faiz_normal   = df_kredi[df_kredi["Dönem"] > erken_ay]["Faiz+KKDF+BSMV"].sum()
        toplam_erken_odeme  = erken_ay * taksit + kalan_anapara_erken

        ek1, ek2, ek3 = st.columns(3)
        with ek1:
            st.metric(f"{erken_ay}. ayda kalan anapara", tl(kalan_anapara_erken))
            st.metric("O ana kadar ödenen F+K+B", tl(odenen_toplam_faiz))
        with ek2:
            st.metric("Erken kapatma toplam ödemesi", tl(toplam_erken_odeme))
            st.metric("Normal durumda toplam ödeme", tl(toplam_taksit))
        with ek3:
            tasarruf = toplam_taksit - toplam_erken_odeme
            st.metric("Faiz Tasarrufu", tl(kalan_faiz_normal),
                      delta=f"₺{kalan_faiz_normal:,.0f} tasarruf")
            st.metric("Erken kapatsanız kazancınız", tl(tasarruf))

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 HEDEF HESAP
# ═══════════════════════════════════════════════════════════════════════════════
with tab_hedef:
    st.header("🎯 Hedef Bazlı Hesap")
    st.caption("Hedefinize göre ters hesaplama yapın")

    mod = st.radio("Hesaplama modu", [
        "💰 Ne kadar yatırmalıyım?",
        "📅 Kaç gün/ay gerekir?",
        "📊 Hangi faiz lazım?",
    ], horizontal=True)

    st.divider()

    if mod == "💰 Ne kadar yatırmalıyım?":
        h1, h2, h3, h4 = st.columns(4)
        with h1: hedef_tutar  = st.number_input("Hedef Tutar (TL)", value=250_000.0, step=10_000.0, key="hedef_tutar__1")
        with h2: h_faiz       = st.number_input("Yıllık Faiz (%)", value=40.0, step=0.5, key="yıllık_faiz__1")
        with h3: h_gun        = st.number_input("Vade (Gün)", value=32, min_value=1, step=1, key="vade_gün_2")
        with h4: h_stopaj     = st.number_input("Stopaj (%)", value=7.5, step=0.1, key="h_stop")
        h_enf = st.number_input("Enflasyon (%)", value=65.0, step=1.0, key="h_enf")

        net_oran = (h_faiz/100) * (h_gun/365) * (1 - h_stopaj/100)
        gereken_anapara = hedef_tutar / (1 + net_oran)
        net_g = gereken_anapara * net_oran
        reel_g = reel_getiri_hesapla(net_g, gereken_anapara, h_enf, h_gun)

        st.success(f"**{h_gun} günde {tl(hedef_tutar)} için yatırmanız gereken anapara: {tl(gereken_anapara)}**")
        r1, r2, r3 = st.columns(3)
        with r1: st.metric("Gereken Anapara",  tl(gereken_anapara))
        with r2: st.metric("Net Getiri",        tl(net_g))
        with r3: st.metric("Reel Getiri",       tl(reel_g), delta="enflasyon düşüldü")

    elif mod == "📅 Kaç gün/ay gerekir?":
        h1, h2, h3, h4 = st.columns(4)
        with h1: h_ap         = st.number_input("Anapara (TL)", value=200_000.0, step=10_000.0, key="h_ap2")
        with h2: hedef_tutar2 = st.number_input("Hedef Tutar (TL)", value=250_000.0, step=10_000.0, key="h_ht2")
        with h3: h_faiz2      = st.number_input("Yıllık Faiz (%)", value=40.0, step=0.5, key="h_f2")
        with h4: h_stopaj2    = st.number_input("Stopaj (%)", value=7.5, step=0.1, key="h_s2")

        hedef_net = hedef_tutar2 - h_ap
        gunluk_net = h_ap * (h_faiz2/100) / 365 * (1 - h_stopaj2/100)
        if gunluk_net > 0:
            gereken_gun = math.ceil(hedef_net / gunluk_net)
            gereken_ay  = math.ceil(gereken_gun / 30)
            vade_tarihi = date.today() + timedelta(days=gereken_gun)

            st.success(f"**{tl(hedef_tutar2)} hedefinize ulaşmak için: {gereken_gun} gün ({gereken_ay} ay)**")
            r1, r2, r3 = st.columns(3)
            with r1: st.metric("Gereken Gün",  f"{gereken_gun} gün")
            with r2: st.metric("Gereken Ay",   f"~{gereken_ay} ay")
            with r3: st.metric("Tahmini Tarih", vade_tarihi.strftime("%d.%m.%Y"))

            # Bileşik büyüme grafiği
            biles_rows = []
            mevcut = h_ap
            for ay in range(1, gereken_ay + 2):
                _, _, _, net_ay = mevduat_hesapla(mevcut, h_faiz2, 32, h_stopaj2)
                mevcut += net_ay
                biles_rows.append({"Ay": ay, "Birikim": mevcut})
                if mevcut >= hedef_tutar2:
                    break
            df_biles = pd.DataFrame(biles_rows)
            fig_biles = px.line(df_biles, x="Ay", y="Birikim",
                                title="Bileşik Büyüme ile Hedefe Ulaşım")
            fig_biles.add_hline(y=hedef_tutar2, line_dash="dash",
                                line_color="green", annotation_text="Hedef")
            fig_biles.update_layout(yaxis_tickformat=",")
            st.plotly_chart(fig_biles, use_container_width=True)
        else:
            st.error("Günlük faiz 0 veya negatif, lütfen parametreleri kontrol edin.")

    elif mod == "📊 Hangi faiz lazım?":
        h1, h2, h3, h4 = st.columns(4)
        with h1: h_ap3        = st.number_input("Anapara (TL)", value=200_000.0, step=10_000.0, key="h_ap3")
        with h2: hedef_tutar3 = st.number_input("Hedef Tutar (TL)", value=250_000.0, step=10_000.0, key="h_ht3")
        with h3: h_gun3       = st.number_input("Vade (Gün)", value=32, min_value=1, step=1, key="h_g3")
        with h4: h_stopaj3    = st.number_input("Stopaj (%)", value=7.5, step=0.1, key="h_s3")

        hedef_net3    = hedef_tutar3 - h_ap3
        net_oran_gerk = hedef_net3 / h_ap3
        brut_oran     = net_oran_gerk / (1 - h_stopaj3/100)
        yillik_faiz_g = brut_oran / (h_gun3/365) * 100

        if yillik_faiz_g > 0:
            st.success(f"**{h_gun3} günde {tl(hedef_tutar3)} için gereken yıllık faiz: %{yillik_faiz_g:.2f}**")
            r1, r2, r3 = st.columns(3)
            with r1: st.metric("Gereken Yıllık Faiz", f"%{yillik_faiz_g:.2f}")
            with r2: st.metric("Hedef Net Getiri",    tl(hedef_net3))
            with r3: st.metric("Net Getiri Oranı",    f"%{net_oran_gerk*100:.2f}")
        else:
            st.warning("Hedefiniz anapara ile aynı veya düşük, faiz gerekmez.")

# ═══════════════════════════════════════════════════════════════════════════════
# 💱 DÖVİZ KARŞILAŞTIRMASI
# ═══════════════════════════════════════════════════════════════════════════════
with tab_doviz:
    st.header("💱 Döviz Karşılaştırması")
    st.caption("Aynı parayı TL, USD veya EUR mevduata yatırsaydınız ne olurdu?")

    dc1, dc2 = st.columns(2)
    with dc1:
        d_tl_tutar  = st.number_input("TL Tutarı", value=200_000.0, step=10_000.0, key="tl_tutarı_1")
        d_gun       = st.number_input("Vade (Gün)", value=32, min_value=1, step=1, key="d_gun")
        d_stopaj    = st.number_input("Stopaj (%)", value=7.5, step=0.1, key="d_stop")
        d_enf       = st.number_input("Enflasyon (%)", value=65.0, step=1.0, key="d_enf")
    with dc2:
        d_tl_faiz   = st.number_input("TL Mevduat Faizi (%)", value=40.0, step=0.5, key="tl_mevduat_f_1")
        d_usd_faiz  = st.number_input("USD Mevduat Faizi (% yıllık)", value=5.0, step=0.25, key="usd_mevduat__1")
        d_eur_faiz  = st.number_input("EUR Mevduat Faizi (% yıllık)", value=3.5, step=0.25, key="eur_mevduat__1")

    st.subheader("📌 Mevcut Döviz Kurları")
    ku1, ku2, ku3 = st.columns(3)
    with ku1: kur_usd_buy = st.number_input("USD/TL Alış (bugün)", value=32.50, step=0.10, key="usd_tl_alış__1")
    with ku2: kur_usd_sell= st.number_input("USD/TL Satış (bugün)", value=32.70, step=0.10, key="usd_tl_satış_1")
    with ku3: kur_eur     = st.number_input("EUR/TL (bugün)", value=35.20, step=0.10, key="eur_tl_bugün_1")

    st.subheader("📈 Vade Sonu Kur Senaryoları")
    ks1, ks2, ks3 = st.columns(3)
    with ks1: kur_usd_vade_a = st.number_input("USD/TL — İyimser", value=30.0, step=0.50, key="usd_tl_—_i̇y_1")
    with ks2: kur_usd_vade_b = st.number_input("USD/TL — Baz",     value=33.5, step=0.50, key="usd_tl_—_baz_1")
    with ks3: kur_usd_vade_c = st.number_input("USD/TL — Kötümser",value=37.0, step=0.50, key="usd_tl_—_köt_1")

    # TL mevduat
    _, brut_tl, stop_tl, net_tl = mevduat_hesapla(d_tl_tutar, d_tl_faiz, d_gun, d_stopaj)
    reel_tl = reel_getiri_hesapla(net_tl, d_tl_tutar, d_enf, d_gun)
    toplam_tl = d_tl_tutar + net_tl

    # USD mevduat
    usd_miktar = d_tl_tutar / kur_usd_sell
    usd_faiz_gunluk = usd_miktar * (d_usd_faiz/100) * (d_gun/365)

    # EUR mevduat
    eur_miktar = d_tl_tutar / kur_eur
    eur_faiz_gunluk = eur_miktar * (d_eur_faiz/100) * (d_gun/365)

    rows_doviz = []
    for senaryo, kur_son in [("İyimser", kur_usd_vade_a),
                               ("Baz",      kur_usd_vade_b),
                               ("Kötümser", kur_usd_vade_c)]:
        usd_toplam_tl = (usd_miktar + usd_faiz_gunluk) * kur_son
        eur_toplam_tl = (eur_miktar + eur_faiz_gunluk) * kur_son  # EUR için USD kuru yaklaşık

        rows_doviz.append({
            "Kur Senaryosu": senaryo,
            "TL Mevduat Sonu": tl(toplam_tl),
            "TL Net Getiri": tl(net_tl),
            "USD Sonu (TL'ye çevrilmiş)": tl(usd_toplam_tl),
            "USD Kâr/Zarar (TL)": tl(usd_toplam_tl - d_tl_tutar),
            "En İyi Seçenek": (
                "✅ TL" if toplam_tl >= usd_toplam_tl else "✅ USD"
            ),
        })

    df_doviz = pd.DataFrame(rows_doviz)
    st.dataframe(df_doviz, use_container_width=True)

    # Görsel karşılaştırma
    fig_d = go.Figure()
    fig_d.add_trace(go.Bar(name="TL Mevduat",
                            x=["İyimser","Baz","Kötümser"],
                            y=[toplam_tl]*3,
                            marker_color="#1a6fff"))
    usd_sonlar = [
        (usd_miktar + usd_faiz_gunluk) * kur for kur in
        [kur_usd_vade_a, kur_usd_vade_b, kur_usd_vade_c]
    ]
    fig_d.add_trace(go.Bar(name="USD Mevduat (TL'ye çevrilmiş)",
                            x=["İyimser","Baz","Kötümser"],
                            y=usd_sonlar,
                            marker_color="#f97316"))
    fig_d.update_layout(title="TL vs USD Mevduat — Kur Senaryoları",
                         yaxis_tickformat=",", barmode="group")
    st.plotly_chart(fig_d, use_container_width=True)

    st.info(f"""
💡 **Özet:**
- TL Mevduat: {tl(d_tl_tutar)} → {tl(toplam_tl)} (net getiri: {tl(net_tl)})
- USD alındı: {usd_miktar:.2f} USD @ {kur_usd_sell} TL
- Baz senaryoda USD sonu: {tl(usd_sonlar[1])}
- Reel TL getiri (enflasyon düşüldü): {tl(reel_tl)}
""")

# ═══════════════════════════════════════════════════════════════════════════════
# 🔄 KREDİ + MEVDUAT ANALİZİ
# ═══════════════════════════════════════════════════════════════════════════════
with tab_analiz:
    st.header("🔄 Kredi + Mevduat Birlikte Analiz")
    st.markdown("""
Bu ekran **Mevduat** ve **Kredi** sekmelerindeki verileri otomatik kullanır.
> **"Kredi öderken, mevduattaki para daha mı hızlı büyüyor?"**
""")

    df_24_son = st.session_state.son_mevduat_df
    df_kredi_son = st.session_state.son_kredi_df
    son_taksit = st.session_state.son_taksit

    if df_24_son is None:
        st.warning("⚠️ Önce **Mevduat** sekmesinde hesaplama yapın.")
    elif df_kredi_son is None:
        st.warning("⚠️ Önce **Kredi** sekmesinde hesaplama yapın.")
    else:
        max_donem = min(len(df_kredi_son), len(df_24_son))
        analiz_rows = []

        for ay in range(1, max_donem + 1):
            # Mevduat sekmesindeki son projeksiyon verisi (Net Gelir sütunu TL formatında)
            # Sayısal değere dönüştür
            net_gelir_str = df_24_son.loc[ay-1, "Net Gelir"]
            net_gelir_num = float(net_gelir_str.replace("₺","").replace(".","").replace(",","."))
            net_durum = net_gelir_num - son_taksit
            analiz_rows.append({
                "Dönem": ay,
                "Mevduat Net Gelir": net_gelir_num,
                "Aylık Taksit": son_taksit,
                "Net Durum": net_durum,
            })

        df_analiz = pd.DataFrame(analiz_rows)
        df_analiz["Kümülatif Net"] = df_analiz["Net Durum"].cumsum()

        df_analiz_g = df_analiz.copy()
        for col in ["Mevduat Net Gelir","Aylık Taksit","Net Durum","Kümülatif Net"]:
            df_analiz_g[col] = df_analiz_g[col].apply(tl)
        st.dataframe(df_analiz_g, use_container_width=True)

        # Grafik
        fig_analiz = px.bar(df_analiz, x="Dönem", y="Net Durum",
                             title="Ay Ay Net Durum (Mevduat Geliri − Kredi Taksiti)",
                             color="Net Durum",
                             color_continuous_scale=["#ef5350","#66bb6a"])
        fig_analiz.add_hline(y=0, line_dash="dash", line_color="#333333")
        fig_analiz.update_layout(yaxis_tickformat=",")
        st.plotly_chart(fig_analiz, use_container_width=True)

        fig_kum = px.line(df_analiz, x="Dönem", y="Kümülatif Net",
                           title="Kümülatif Net Durum")
        fig_kum.add_hline(y=0, line_dash="dash", line_color="red")
        fig_kum.update_layout(yaxis_tickformat=",")
        st.plotly_chart(fig_kum, use_container_width=True)

        son_net = df_analiz["Net Durum"].iloc[-1]
        kum_net = df_analiz["Kümülatif Net"].iloc[-1]
        if son_net > 0:
            st.success(f"✅ Son ayda mevduat, taksitten {tl(son_net)} fazla getiri sağlıyor.")
        else:
            st.error(f"❌ Son ayda kredi taksiti, mevduat getirisini {tl(abs(son_net))} aşıyor.")

        if kum_net > 0:
            st.success(f"📈 Toplam sürede kümülatif net: **{tl(kum_net)} pozitif**")
        else:
            st.error(f"📉 Toplam sürede kümülatif net: **{tl(abs(kum_net))} negatif**")

# ═══════════════════════════════════════════════════════════════════════════════
# 📤 DIŞA AKTAR
# ═══════════════════════════════════════════════════════════════════════════════
with tab_export:
    st.header("📤 Dışa Aktar")
    st.caption("Tablolarınızı Excel veya PDF olarak indirin")

    df_kredi_exp = st.session_state.son_kredi_df
    df_mev_exp   = st.session_state.son_mevduat_df

    if df_kredi_exp is None and df_mev_exp is None:
        st.info("Dışa aktarılacak veri yok. Önce Mevduat ve/veya Kredi sekmelerinde hesaplama yapın.")
    else:
        exp_sec = st.multiselect("Hangi tabloları dahil etmek istiyorsunuz?",
                                  options=["Mevduat Projeksiyonu","Kredi Amortismanı",
                                           "Kayıtlı Senaryolar","Çoklu Mevduat"],
                                  default=["Mevduat Projeksiyonu","Kredi Amortismanı"])

        dfs_for_export = {}
        if "Mevduat Projeksiyonu" in exp_sec and df_mev_exp is not None:
            dfs_for_export["Mevduat Projeksiyonu"] = df_mev_exp
        if "Kredi Amortismanı" in exp_sec and df_kredi_exp is not None:
            df_k_raw = df_kredi_exp.copy()
            for col in ["Taksit","Anapara","Faiz","KKDF","BSMV","Faiz+KKDF+BSMV",
                        "Ara Ödeme","Kalan Anapara","Ödenen Taksit"]:
                if col in df_k_raw.columns:
                    df_k_raw[col] = df_k_raw[col].apply(tl)
            dfs_for_export["Kredi Amortismanı"] = df_k_raw
        if "Kayıtlı Senaryolar" in exp_sec and st.session_state.kayitli_senaryolar:
            dfs_for_export["Kayıtlı Senaryolar"] = pd.DataFrame(st.session_state.kayitli_senaryolar)
        if "Çoklu Mevduat" in exp_sec and st.session_state.coklu_mevduat:
            dfs_for_export["Çoklu Mevduat"] = pd.DataFrame(st.session_state.coklu_mevduat)

        if dfs_for_export:
            col_exc, col_pdf = st.columns(2)
            with col_exc:
                excel_bytes = df_to_excel(dfs_for_export)
                st.download_button(
                    label="📊 Excel İndir (.xlsx)",
                    data=excel_bytes,
                    file_name=f"finansal_analiz_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            with col_pdf:
                for sheet_name, df_p in dfs_for_export.items():
                    pdf_bytes = df_to_pdf(df_p, sheet_name)
                    st.download_button(
                        label=f"📄 {sheet_name} — PDF İndir",
                        data=pdf_bytes,
                        file_name=f"{sheet_name.lower().replace(' ','_')}_{date.today()}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{sheet_name}",
                    )
        else:
            st.warning("Seçilen tablolarda veri bulunamadı.")

# ── Alt Bilgi ─────────────────────────────────────────────────────────────────
st.divider()
st.caption("© Finansal Karar Destek Sistemi v2 | Streamlit + Python | Enes Özkan 2026")
