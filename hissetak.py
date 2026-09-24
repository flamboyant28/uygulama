from pathlib import Path

code = r'''
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# AYARLAR
# ============================================================
st.set_page_config(
    page_title="Hisse Portföy & Trading Journal",
    page_icon="📈",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
MARKET_FILE = BASE_DIR / "hisseler.csv"
TRADES_FILE = BASE_DIR / "islemler.csv"

MARKET_COLUMNS = [
    "Tarih", "Hisseler", "Kod", "Hisse Adı",
    "Son", "% Fark", "Hacim (TL)", "Saat"
]

TRADE_COLUMNS = [
    "id", "Tarih", "Hisse", "İşlem", "Lot", "Fiyat", "Tutar"
]


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================
def ensure_files():
    if not MARKET_FILE.exists():
        pd.DataFrame(columns=MARKET_COLUMNS).to_csv(
            MARKET_FILE, index=False, encoding="utf-8-sig"
        )

    if not TRADES_FILE.exists():
        pd.DataFrame(columns=TRADE_COLUMNS).to_csv(
            TRADES_FILE, index=False, encoding="utf-8-sig"
        )


def read_csv_safe(path, columns):
    if not path.exists():
        return pd.DataFrame(columns=columns)

    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="cp1254")

    if df.empty:
        return pd.DataFrame(columns=columns)

    return df


def tr_number(value):
    """Türkçe sayı formatını float'a çevirir."""
    if pd.isna(value):
        return np.nan

    if isinstance(value, (int, float, np.number)):
        return float(value)

    s = str(value).strip()
    if not s:
        return np.nan

    s = s.replace("₺", "").replace("TL", "").replace("%", "")
    s = s.replace(" ", "")

    # 39.925.922,68 -> 39925922.68
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        # 39.925.922 gibi bir sayıysa binlik noktaları kaldır.
        if s.count(".") > 1:
            s = s.replace(".", "")

    try:
        return float(s)
    except ValueError:
        return np.nan


def format_tl(value):
    if pd.isna(value):
        return "-"
    value = float(value)
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " ₺"


def format_number(value):
    if pd.isna(value):
        return "-"
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_lot(value):
    if pd.isna(value):
        return "-"
    if abs(float(value) - round(float(value))) < 1e-9:
        return f"{int(round(float(value))):,}".replace(",", ".")
    return format_number(value)


def format_pct(value):
    if pd.isna(value):
        return "-"
    return f"{float(value):+.2f}%".replace(".", ",")


def normalize_market_csv(uploaded_df):
    """
    Kaynaktan gelen CSV'nin örnek formatını normalize eder:
    Hisseler | Son | % Fark | Hacim (TL) | Saat

    Hisseler alanından kod ve şirket adı ayrılır.
    Her içe aktarmada tarih otomatik eklenir.
    """
    df = uploaded_df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Türkçe kaynakta olabilecek kolon isimleri
    aliases = {
        "Hisseler": ["Hisseler", "Hisse", "Hisse Adı", "Hisse Adi"],
        "Son": ["Son", "Fiyat", "Son Fiyat"],
        "% Fark": ["% Fark", "Fark", "Değişim", "Degisim", "%Degisim"],
        "Hacim (TL)": ["Hacim (TL)", "Hacim", "Hacim(TL)"],
        "Saat": ["Saat", "Time"]
    }

    renamed = {}
    for target, candidates in aliases.items():
        for c in candidates:
            if c in df.columns:
                renamed[c] = target
                break

    df = df.rename(columns=renamed)

    required = ["Hisseler", "Son", "% Fark", "Hacim (TL)", "Saat"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            "CSV içinde şu kolonlar bulunamadı: "
            + ", ".join(missing)
        )

    df = df[required].copy()

    # Kod + isim ayır
    df["Hisseler"] = df["Hisseler"].astype(str).str.strip()

    split = df["Hisseler"].str.extract(
        r"^\s*([A-Za-z0-9ÇĞİÖŞÜçğıöşü]+)\s+(.*)$"
    )

    df["Kod"] = split[0].fillna(df["Hisseler"]).str.upper().str.strip()
    df["Hisse Adı"] = split[1].fillna("").str.strip()

    df["Son"] = df["Son"].apply(tr_number)
    df["% Fark"] = df["% Fark"].apply(tr_number)
    df["Hacim (TL)"] = df["Hacim (TL)"].apply(tr_number)
    df["Saat"] = df["Saat"].astype(str).str.strip()

    df["Tarih"] = date.today().isoformat()

    return df[MARKET_COLUMNS]


def load_market():
    df = read_csv_safe(MARKET_FILE, MARKET_COLUMNS)

    if df.empty:
        return pd.DataFrame(columns=MARKET_COLUMNS)

    # Eski dosya yeni yapıya geçiş
    if "Kod" not in df.columns:
        if "Hisseler" in df.columns:
            split = df["Hisseler"].astype(str).str.extract(
                r"^\s*([A-Za-z0-9ÇĞİÖŞÜçğıöşü]+)\s+(.*)$"
            )
            df["Kod"] = split[0].fillna(df["Hisseler"]).str.upper()
            df["Hisse Adı"] = split[1].fillna("")
        else:
            df["Kod"] = ""
            df["Hisse Adı"] = ""

    for col in MARKET_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df["Kod"] = df["Kod"].astype(str).str.upper().str.strip()
    df["Son"] = df["Son"].apply(tr_number)
    df["% Fark"] = df["% Fark"].apply(tr_number)
    df["Hacim (TL)"] = df["Hacim (TL)"].apply(tr_number)

    return df[MARKET_COLUMNS]


def load_trades():
    df = read_csv_safe(TRADES_FILE, TRADE_COLUMNS)

    if df.empty:
        return pd.DataFrame(columns=TRADE_COLUMNS)

    for col in TRADE_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df["Tarih"] = pd.to_datetime(
        df["Tarih"], errors="coerce"
    ).dt.date

    df["Hisse"] = df["Hisse"].astype(str).str.upper().str.strip()
    df["İşlem"] = df["İşlem"].astype(str).str.upper().str.strip()
    df["Lot"] = df["Lot"].apply(tr_number)
    df["Fiyat"] = df["Fiyat"].apply(tr_number)
    df["Tutar"] = df["Lot"] * df["Fiyat"]

    return df[TRADE_COLUMNS]


def save_trades(df):
    out = df.copy()
    out["Tarih"] = pd.to_datetime(out["Tarih"]).dt.strftime("%Y-%m-%d")
    out.to_csv(TRADES_FILE, index=False, encoding="utf-8-sig")


def save_market(df):
    df.to_csv(MARKET_FILE, index=False, encoding="utf-8-sig")


def get_latest_market(market_df):
    if market_df.empty:
        return pd.DataFrame(columns=MARKET_COLUMNS)

    m = market_df.copy()
    m["Tarih"] = pd.to_datetime(m["Tarih"], errors="coerce")
    m["Saat_dt"] = pd.to_datetime(
        m["Tarih"].dt.strftime("%Y-%m-%d") + " " +
        m["Saat"].astype(str),
        errors="coerce"
    )

    m = m.sort_values("Saat_dt").drop_duplicates(
        subset=["Kod"], keep="last"
    )

    return m.drop(columns=["Saat_dt"])


def calculate_portfolio(trades, latest_market):
    """
    Ağırlıklı ortalama maliyet yöntemi.

    AL:
        lot artar
        maliyet = mevcut maliyet + alış tutarı

    SAT:
        gerçekleşen K/Z = (satış fiyatı - mevcut ortalama maliyet) * satılan lot
        kalan maliyet = eski maliyet - ortalama maliyet * satılan lot
    """
    if trades.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame()
        )

    t = trades.copy()
    t["Tarih"] = pd.to_datetime(t["Tarih"], errors="coerce")
    t = t.sort_values(["Hisse", "Tarih", "id"])

    positions = {}
    trade_results = []
    snapshots = []

    for _, row in t.iterrows():
        symbol = str(row["Hisse"]).upper()
        side = str(row["İşlem"]).upper()
        lot = float(row["Lot"]) if not pd.isna(row["Lot"]) else 0
        price = float(row["Fiyat"]) if not pd.isna(row["Fiyat"]) else 0

        if symbol not in positions:
            positions[symbol] = {
                "lot": 0.0,
                "cost": 0.0
            }

        pos = positions[symbol]

        before_lot = pos["lot"]
        before_cost = pos["cost"]
        before_avg = (
            before_cost / before_lot
            if before_lot > 0 else 0
        )

        realized = 0.0

        if side == "AL":
            pos["lot"] += lot
            pos["cost"] += lot * price

        elif side == "SAT":
            if lot > pos["lot"] + 1e-9:
                # Hatalı satışın hesabı bozmasını engelle
                lot = pos["lot"]

            realized = (price - before_avg) * lot
            pos["lot"] -= lot
            pos["cost"] -= before_avg * lot

            if abs(pos["lot"]) < 1e-9:
                pos["lot"] = 0
                pos["cost"] = 0

        after_avg = (
            pos["cost"] / pos["lot"]
            if pos["lot"] > 0 else 0
        )

        trade_results.append({
            "id": row["id"],
            "Tarih": row["Tarih"],
            "Hisse": symbol,
            "İşlem": side,
            "Lot": lot,
            "Fiyat": price,
            "Tutar": lot * price,
            "İşlem Öncesi Lot": before_lot,
            "İşlem Öncesi Ort. Maliyet": before_avg,
            "Gerçekleşen K/Z": realized,
            "İşlem Sonrası Lot": pos["lot"],
            "İşlem Sonrası Ort. Maliyet": after_avg
        })

        snapshots.append({
            "Tarih": row["Tarih"],
            "Hisse": symbol,
            "İşlem": side,
            "Lot": lot,
            "İşlem Sonrası Lot": pos["lot"]
        })

    portfolio = []

    market_lookup = {}
    if not latest_market.empty:
        market_lookup = latest_market.set_index("Kod").to_dict("index")

    for symbol, pos in positions.items():
        lot = pos["lot"]
        cost = pos["cost"]

        if lot <= 0:
            continue

        avg = cost / lot

        market = market_lookup.get(symbol, {})
        current_price = market.get("Son", np.nan)
        daily_change = market.get("% Fark", np.nan)
        company_name = market.get("Hisse Adı", "")

        current_value = (
            lot * current_price
            if not pd.isna(current_price) else np.nan
        )

        open_pnl = (
            current_value - cost
            if not pd.isna(current_value) else np.nan
        )

        portfolio.append({
            "Hisse": symbol,
            "Hisse Adı": company_name,
            "Lot": lot,
            "Ort. Maliyet": avg,
            "Son": current_price,
            "% Fark": daily_change,
            "Maliyet": cost,
            "Güncel Değer": current_value,
            "Açık K/Z": open_pnl
        })

    portfolio_df = pd.DataFrame(portfolio)

    if not portfolio_df.empty:
        total_value = portfolio_df["Güncel Değer"].sum(
            skipna=True
        )
        total_lot = portfolio_df["Lot"].sum()

        portfolio_df["Lot %"] = (
            portfolio_df["Lot"] / total_lot * 100
            if total_lot > 0 else 0
        )

        if total_value > 0:
            portfolio_df["Değer %"] = (
                portfolio_df["Güncel Değer"] /
                total_value * 100
            )
        else:
            portfolio_df["Değer %"] = 0

    trade_results_df = pd.DataFrame(trade_results)
    snapshots_df = pd.DataFrame(snapshots)

    return portfolio_df, trade_results_df, snapshots_df


def make_display_portfolio(df):
    if df.empty:
        return df

    x = df.copy()

    return pd.DataFrame({
        "Hisse": x["Hisse"],
        "Hisse Adı": x["Hisse Adı"],
        "Lot": x["Lot"].apply(format_lot),
        "Ort. Maliyet": x["Ort. Maliyet"].apply(format_tl),
        "Son": x["Son"].apply(format_tl),
        "% Fark": x["% Fark"].apply(format_pct),
        "Maliyet": x["Maliyet"].apply(format_tl),
        "Güncel Değer": x["Güncel Değer"].apply(format_tl),
        "Açık K/Z": x["Açık K/Z"].apply(format_tl),
        "Lot %": x["Lot %"].apply(lambda v: f"{v:.2f}%".replace(".", ",")),
        "Değer %": x["Değer %"].apply(lambda v: f"{v:.2f}%".replace(".", ","))
    })


# ============================================================
# BAŞLANGIÇ
# ============================================================
ensure_files()

market_df = load_market()
trades_df = load_trades()

latest_market = get_latest_market(market_df)

portfolio_df, trade_results_df, snapshots_df = calculate_portfolio(
    trades_df,
    latest_market
)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("⚙️ Veri Yönetimi")

    st.caption(
        "Piyasa verisi ve kendi işlemlerin ayrı CSV dosyalarında tutulur."
    )

    st.write(f"📄 Hisse verisi: `{MARKET_FILE.name}`")
    st.write(f"📄 İşlemler: `{TRADES_FILE.name}`")

    st.divider()

    st.subheader("📥 Piyasa CSV Güncelle")

    uploaded_market = st.file_uploader(
        "Kaynaktan aldığın CSV'yi seç",
        type=["csv"],
        key="market_upload"
    )

    if st.button("📥 Piyasa Verisini Ekle", use_container_width=True):
        if uploaded_market is None:
            st.warning("Önce piyasa CSV dosyasını seç.")
        else:
            try:
                raw = pd.read_csv(
                    uploaded_market,
                    encoding="utf-8-sig"
                )
            except UnicodeDecodeError:
                raw = pd.read_csv(
                    uploaded_market,
                    encoding="cp1254"
                )

            try:
                new_market = normalize_market_csv(raw)

                # Aynı gün/saat/kod tekrar yüklenirse duplicate oluşmasın.
                old = load_market()

                combined = pd.concat(
                    [old, new_market],
                    ignore_index=True
                )

                combined = combined.drop_duplicates(
                    subset=["Tarih", "Saat", "Kod"],
                    keep="last"
                )

                save_market(combined)

                st.success(
                    f"{len(new_market)} hisse eklendi/güncellendi."
                )
                st.rerun()

            except Exception as e:
                st.error(f"CSV okunamadı: {e}")

    st.divider()

    st.subheader("📤 Veri Yedekleme")

    with open(TRADES_FILE, "rb") as f:
        st.download_button(
            "İşlem CSV'sini indir",
            f,
            file_name="islemler_yedek.csv",
            mime="text/csv",
            use_container_width=True
        )

    if MARKET_FILE.exists():
        with open(MARKET_FILE, "rb") as f:
            st.download_button(
                "Hisse CSV'sini indir",
                f,
                file_name="hisseler_yedek.csv",
                mime="text/csv",
                use_container_width=True
            )


# ============================================================
# BAŞLIK
# ============================================================
st.title("📈 Hisse Portföy & Trading Journal")
st.caption(
    "CSV tabanlı • Ağırlıklı ortalama maliyet • Satış analizi • "
    "Portföy dağılımı • Offline"
)

if latest_market.empty:
    st.info(
        "Başlamak için sol menüden kaynaktan aldığın piyasa CSV'sini yükle."
    )


# ============================================================
# TABS
# ============================================================
tab_dashboard, tab_islemler, tab_satis, tab_piyasa = st.tabs([
    "📊 Dashboard",
    "🔄 İşlemler",
    "💰 Satış Analizi",
    "📁 Piyasa Verisi"
])


# ============================================================
# DASHBOARD
# ============================================================
with tab_dashboard:

    if portfolio_df.empty:
        st.info("Henüz açık pozisyon bulunmuyor.")
    else:
        total_cost = portfolio_df["Maliyet"].sum()
        total_value = portfolio_df["Güncel Değer"].sum(
            skipna=True
        )
        open_pnl = portfolio_df["Açık K/Z"].sum(
            skipna=True
        )

        realized_pnl = (
            trade_results_df["Gerçekleşen K/Z"].sum()
            if not trade_results_df.empty else 0
        )

        total_pnl = open_pnl + realized_pnl

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "💰 Toplam Maliyet",
            format_tl(total_cost)
        )

        c2.metric(
            "📊 Güncel Portföy",
            format_tl(total_value)
        )

        c3.metric(
            "📈 Açık K/Z",
            format_tl(open_pnl)
        )

        c4.metric(
            "💵 Gerçekleşen K/Z",
            format_tl(realized_pnl)
        )

        c5.metric(
            "🏆 Toplam K/Z",
            format_tl(total_pnl)
        )

        st.divider()

        st.subheader("📊 Mevcut Portföy")

        st.dataframe(
            make_display_portfolio(portfolio_df),
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # PORTFÖY GRAFİKLERİ
        # ----------------------------------------------------
        col1, col2 = st.columns(2)

        with col1:
            fig = px.pie(
                portfolio_df,
                values="Güncel Değer",
                names="Hisse",
                title="Portföy Değer Dağılımı",
                hole=0.35
            )
            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with col2:
            fig2 = px.pie(
                portfolio_df,
                values="Lot",
                names="Hisse",
                title="Lot Dağılımı",
                hole=0.35
            )
            st.plotly_chart(
                fig2,
                use_container_width=True
            )

        # ----------------------------------------------------
        # K/Z GRAFİĞİ
        # ----------------------------------------------------
        st.subheader("📈 Hisse Bazlı Açık K/Z")

        pnl_chart = portfolio_df.sort_values(
            "Açık K/Z",
            ascending=False
        )

        fig3 = px.bar(
            pnl_chart,
            x="Hisse",
            y="Açık K/Z",
            text="Açık K/Z",
            title="Açık Kâr / Zarar"
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

        # ----------------------------------------------------
        # PORTFÖY AĞIRLIĞI
        # ----------------------------------------------------
        st.subheader("⚖️ Portföy Ağırlıkları")

        weight_df = portfolio_df[
            ["Hisse", "Lot %", "Değer %"]
        ].copy()

        weight_df["Lot %"] = weight_df["Lot %"].round(2)
        weight_df["Değer %"] = weight_df["Değer %"].round(2)

        st.dataframe(
            weight_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# İŞLEMLER
# ============================================================
with tab_islemler:

    st.subheader("➕ Yeni İşlem")

    symbol_options = []

    if not latest_market.empty:
        symbol_options = sorted(
            latest_market["Kod"].dropna().unique().tolist()
        )

    col1, col2, col3, col4, col5 = st.columns(5)

    if symbol_options:
        symbol = col1.selectbox(
            "Hisse",
            symbol_options,
            index=None,
            placeholder="Hisse ara..."
        )
    else:
        symbol = col1.text_input(
            "Hisse kodu",
            placeholder="THYAO"
        ).upper()

    side = col2.selectbox(
        "İşlem",
        ["AL", "SAT"]
    )

    lot = col3.number_input(
        "Lot",
        min_value=0.01,
        step=1.0,
        value=1.0
    )

    price = col4.number_input(
        "Fiyat",
        min_value=0.0,
        step=0.01,
        format="%.4f"
    )

    trade_date = col5.date_input(
        "Tarih",
        value=date.today()
    )

    if st.button(
        "💾 İşlemi Kaydet",
        type="primary"
    ):
        if not symbol:
            st.error("Hisse seçmelisin.")
        elif lot <= 0:
            st.error("Lot 0'dan büyük olmalı.")
        elif price <= 0:
            st.error("Fiyat 0'dan büyük olmalı.")
        else:
            # SAT kontrolü
            if side == "SAT" and not portfolio_df.empty:
                current = portfolio_df.loc[
                    portfolio_df["Hisse"] == symbol,
                    "Lot"
                ]

                current_lot = (
                    float(current.iloc[0])
                    if not current.empty else 0
                )

                if lot > current_lot + 1e-9:
                    st.error(
                        f"{symbol} için mevcut lot: "
                        f"{format_lot(current_lot)}. "
                        f"{format_lot(lot)} lot satamazsın."
                    )
                    st.stop()

            current_ids = pd.to_numeric(
                trades_df["id"],
                errors="coerce"
            )

            next_id = (
                int(current_ids.max()) + 1
                if current_ids.notna().any()
                else 1
            )

            new_row = pd.DataFrame([{
                "id": next_id,
                "Tarih": trade_date,
                "Hisse": symbol.upper(),
                "İşlem": side,
                "Lot": lot,
                "Fiyat": price,
                "Tutar": lot * price
            }])

            trades_df = pd.concat(
                [trades_df, new_row],
                ignore_index=True
            )

            save_trades(trades_df)

            st.success(
                f"{symbol} {side} işlemi kaydedildi."
            )
            st.rerun()

    st.divider()

    st.subheader("📜 İşlem Geçmişi")

    if trades_df.empty:
        st.info("Henüz işlem yok.")
    else:
        display_trades = trades_df.copy()
        display_trades["Tarih"] = pd.to_datetime(
            display_trades["Tarih"]
        ).dt.strftime("%d.%m.%Y")

        display_trades["Lot"] = display_trades["Lot"].apply(
            format_lot
        )
        display_trades["Fiyat"] = display_trades["Fiyat"].apply(
            format_tl
        )
        display_trades["Tutar"] = display_trades["Tutar"].apply(
            format_tl
        )

        st.dataframe(
            display_trades.sort_values(
                "Tarih",
                ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader("🗑️ İşlem Sil")

    if not trades_df.empty:
        delete_id = st.number_input(
            "Silinecek işlem ID",
            min_value=1,
            step=1
        )

        if st.button(
            "🗑️ İşlemi Sil",
            type="secondary"
        ):
            if delete_id in trades_df["id"].astype(int).values:
                trades_df = trades_df[
                    trades_df["id"].astype(int) != int(delete_id)
                ]

                save_trades(trades_df)

                st.success(
                    f"{delete_id} numaralı işlem silindi."
                )
                st.rerun()
            else:
                st.warning("Bu ID ile işlem bulunamadı.")


# ============================================================
# SATIŞ ANALİZİ
# ============================================================
with tab_satis:

    st.subheader("💰 Satış ve Gerçekleşen K/Z Analizi")

    if trade_results_df.empty:
        st.info("Henüz işlem bulunmuyor.")
    else:
        sales = trade_results_df[
            trade_results_df["İşlem"] == "SAT"
        ].copy()

        if sales.empty:
            st.info("Henüz satış işlemi bulunmuyor.")
        else:
            realized_total = sales["Gerçekleşen K/Z"].sum()
            sold_lot = sales["Lot"].sum()

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Satılan Toplam Lot",
                format_lot(sold_lot)
            )

            c2.metric(
                "Gerçekleşen K/Z",
                format_tl(realized_total)
            )

            win_sales = (sales["Gerçekleşen K/Z"] > 0).sum()
            loss_sales = (sales["Gerçekleşen K/Z"] < 0).sum()

            c3.metric(
                "Kârlı / Zararlı Satış",
                f"{win_sales} / {loss_sales}"
            )

            st.divider()

            display_sales = sales.copy()

            display_sales["Tarih"] = pd.to_datetime(
                display_sales["Tarih"]
            ).dt.strftime("%d.%m.%Y")

            for col in [
                "Lot",
                "İşlem Öncesi Lot",
                "İşlem Sonrası Lot"
            ]:
                display_sales[col] = display_sales[col].apply(
                    format_lot
                )

            for col in [
                "Fiyat",
                "Tutar",
                "İşlem Öncesi Ort. Maliyet",
                "Gerçekleşen K/Z",
                "İşlem Sonrası Ort. Maliyet"
            ]:
                display_sales[col] = display_sales[col].apply(
                    format_tl
                )

            st.dataframe(
                display_sales[
                    [
                        "id",
                        "Tarih",
                        "Hisse",
                        "Lot",
                        "Fiyat",
                        "Tutar",
                        "İşlem Öncesi Lot",
                        "İşlem Öncesi Ort. Maliyet",
                        "Gerçekleşen K/Z",
                        "İşlem Sonrası Lot",
                        "İşlem Sonrası Ort. Maliyet"
                    ]
                ].sort_values(
                    "Tarih",
                    ascending=False
                ),
                use_container_width=True,
                hide_index=True
            )

            # ------------------------------------------------
            # SATIŞ SONRASI FİYAT TAKİBİ
            # ------------------------------------------------
            st.divider()
            st.subheader("🔎 Satış Sonrası Fiyat Takibi")

            st.caption(
                "Bu bölüm, hisseler.csv içine daha sonraki piyasa "
                "verileri eklendikçe satıştan sonraki fiyat hareketini gösterir."
            )

            market_history = market_df.copy()

            if not market_history.empty:
                market_history["Tarih_dt"] = pd.to_datetime(
                    market_history["Tarih"],
                    errors="coerce"
                )

            post_rows = []

            for _, sale in sales.iterrows():
                sale_date = pd.to_datetime(
                    sale["Tarih"]
                )

                symbol = sale["Hisse"]
                sell_price = sale["Fiyat"]
                sold_lot = sale["Lot"]

                future = market_history[
                    (market_history["Kod"] == symbol) &
                    (market_history["Tarih_dt"] > sale_date)
                ].copy()

                if future.empty:
                    continue

                future = future.sort_values(
                    ["Tarih_dt", "Saat"]
                )

                for _, market_row in future.iterrows():
                    future_price = market_row["Son"]

                    if pd.isna(future_price):
                        continue

                    price_diff = future_price - sell_price
                    hypothetical = price_diff * sold_lot

                    post_rows.append({
                        "Satış ID": sale["id"],
                        "Hisse": symbol,
                        "Satış Tarihi": sale_date,
                        "Satış Fiyatı": sell_price,
                        "Satılan Lot": sold_lot,
                        "İzlenen Tarih": market_row["Tarih_dt"],
                        "İzlenen Saat": market_row["Saat"],
                        "Sonraki Fiyat": future_price,
                        "Fiyat Farkı": price_diff,
                        "Satılan Lot Bugün Tutulsaydı": hypothetical
                    })

            if post_rows:
                post_df = pd.DataFrame(post_rows)

                # Her satış için en son piyasa kaydı
                latest_post = (
                    post_df.sort_values(
                        ["Satış ID", "İzlenen Tarih", "İzlenen Saat"]
                    )
                    .groupby("Satış ID", as_index=False)
                    .tail(1)
                )

                display_post = latest_post.copy()

                display_post["Satış Tarihi"] = pd.to_datetime(
                    display_post["Satış Tarihi"]
                ).dt.strftime("%d.%m.%Y")

                display_post["İzlenen Tarih"] = pd.to_datetime(
                    display_post["İzlenen Tarih"]
                ).dt.strftime("%d.%m.%Y")

                display_post["Satış Fiyatı"] = display_post[
                    "Satış Fiyatı"
                ].apply(format_tl)

                display_post["Sonraki Fiyat"] = display_post[
                    "Sonraki Fiyat"
                ].apply(format_tl)

                display_post["Fiyat Farkı"] = display_post[
                    "Fiyat Farkı"
                ].apply(format_tl)

                display_post[
                    "Satılan Lot Bugün Tutulsaydı"
                ] = display_post[
                    "Satılan Lot Bugün Tutulsaydı"
                ].apply(format_tl)

                st.dataframe(
                    display_post[
                        [
                            "Satış ID",
                            "Hisse",
                            "Satış Tarihi",
                            "Satış Fiyatı",
                            "Satılan Lot",
                            "İzlenen Tarih",
                            "İzlenen Saat",
                            "Sonraki Fiyat",
                            "Fiyat Farkı",
                            "Satılan Lot Bugün Tutulsaydı"
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(
                    "Satışlardan sonraki dönemlere ait piyasa verisi "
                    "henüz hisseler.csv içinde yok."
                )


# ============================================================
# PİYASA VERİSİ
# ============================================================
with tab_piyasa:

    st.subheader("📁 Piyasa Hisse Verileri")

    if market_df.empty:
        st.info("Henüz piyasa CSV'si yüklenmedi.")
    else:
        st.write(
            f"Toplam piyasa kaydı: **{len(market_df):,}**".replace(",", ".")
        )

        st.write(
            f"Takip edilen farklı hisse: "
            f"**{market_df['Kod'].nunique():,}**".replace(",", ".")
        )

        latest_display = latest_market.copy()

        latest_display["Son"] = latest_display["Son"].apply(
            format_tl
        )
        latest_display["% Fark"] = latest_display["% Fark"].apply(
            format_pct
        )
        latest_display["Hacim (TL)"] = latest_display[
            "Hacim (TL)"
        ].apply(format_tl)

        st.dataframe(
            latest_display[
                [
                    "Kod",
                    "Hisse Adı",
                    "Son",
                    "% Fark",
                    "Hacim (TL)",
                    "Saat"
                ]
            ].sort_values("Kod"),
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("📈 Piyasa Fiyat Geçmişi")

        history_symbols = sorted(
            market_df["Kod"].dropna().unique().tolist()
        )

        selected_history = st.selectbox(
            "Hisse seç",
            history_symbols,
            index=None,
            placeholder="Hisse ara..."
        )

        if selected_history:
            hist = market_df[
                market_df["Kod"] == selected_history
            ].copy()

            hist["Tarih_dt"] = pd.to_datetime(
                hist["Tarih"],
                errors="coerce"
            )

            hist["Zaman"] = pd.to_datetime(
                hist["Tarih_dt"].dt.strftime("%Y-%m-%d") +
                " " + hist["Saat"].astype(str),
                errors="coerce"
            )

            hist = hist.sort_values("Zaman")

            fig = px.line(
                hist,
                x="Zaman",
                y="Son",
                markers=True,
                title=f"{selected_history} Fiyat Geçmişi"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


# ============================================================
# ALT BİLGİ
# ============================================================
st.divider()

st.caption(
    "Veriler yerel CSV dosyalarında tutulur. "
    "Piyasa CSV'si dış kaynaktan alınan fiyat verisidir; "
    "işlemler ayrı CSV'de saklanır."
)
'''

#path = Path("/mnt/data/hissetak.py")
#path.write_text(code, encoding="utf-8")

# Başlangıç CSV dosyalarını da oluştur.
market = pd.DataFrame(columns=[
    "Tarih", "Hisseler", "Kod", "Hisse Adı",
    "Son", "% Fark", "Hacim (TL)", "Saat"
])
trades = pd.DataFrame(columns=[
    "id", "Tarih", "Hisse", "İşlem", "Lot", "Fiyat", "Tutar"
])

market.to_csv("/mnt/data/hisseler.csv", index=False, encoding="utf-8-sig")
trades.to_csv("/mnt/data/islemler.csv", index=False, encoding="utf-8-sig")

print(path)
print("/mnt/data/hisseler.csv")
print("/mnt/data/islemler.csv")
