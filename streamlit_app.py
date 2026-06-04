# =============================================================================
# AMAZON REVIEWS – SENTIMENT DASHBOARD (STREAMLIT)
# Basiert auf 02_dashboard.py – konvertiert für öffentliches Hosting
# Sprachschalter: EN / DE per Klick
# =============================================================================

import streamlit as st
import pandas as pd
import sqlite3
import re
import os
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter

# ── Seite konfigurieren ──────────────────────────────────────────────────────
st.set_page_config(
    page_title = "Amazon Reviews – Sentiment Analytics",
    page_icon  = "📦",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── Sprache initialisieren ───────────────────────────────────────────────────
if "sprache" not in st.session_state:
    st.session_state.sprache = "en"

# Übersetzungen
T = {
    "en": {
        "title":        "Amazon Reviews  Sentiment Analytics",
        "subtitle":     "RoBERTa Transformer · Kaggle Dataset · 21,214 Reviews",
        "tab0":         "Overview",
        "tab1":         "Time Series",
        "tab2":         "Countries",
        "tab3":         "Reviews",
        "filter_sent":  "Sentiment",
        "filter_land":  "Countries",
        "filter_year":  "Year Range",
        "filter_cert":  "Model Certainty",
        "filter_cert_s":"Min. AI confidence in its classification",
        "filter_abw":   "Discrepancies only",
        "kpi_total":    "Total Reviews",
        "kpi_period":   "current period",
        "kpi_rating":   "Avg. Rating",
        "kpi_pos":      "Positive",
        "kpi_neu":      "Neutral",
        "kpi_neg":      "Negative",
        "kpi_abw":      "Discrepancies",
        "kpi_abw_s":    "text ≠ star rating",
        "vs_prior":     "vs prior period",
        # Overview
        "h_dist":       "Sentiment Distribution",
        "s_dist":       "Model output from review text — independent of star ratings",
        "h_vgl":        "Star Rating vs. Text Sentiment",
        "s_vgl":        "How often does the model agree with the star rating?",
        "h_cert":       "Avg. Model Certainty",
        "s_cert":       "How confident was RoBERTa in its classification?",
        "h_trend":      "Monthly Sentiment Trend",
        "s_trend":      "Sentiment evolution across the full dataset period",
        # Time Series
        "h_area":       "Monthly Sentiment Volume",
        "s_area":       "Stacked area chart – absolute review counts per month",
        "h_nj":         "Negative Share by Year",
        "s_nj":         "Annual share of reviews classified as negative",
        "h_rj":         "Avg. Star Rating by Year",
        "s_rj":         "Annual average of reviewer-assigned star ratings",
        # Countries
        "h_choro":      "Negative Sentiment Heatmap",
        "s_choro":      "Share of negative reviews per country — hover for details",
        "h_bubble":     "Review Volume by Location",
        "s_bubble":     "Bubble size = review count · Color = negative share",
        "h_bar15":      "Top 15 Countries — Sentiment Breakdown",
        "s_bar15":      "Absolute review count split by sentiment",
        # Reviews
        "h_words_neg":  "Most Frequent Words — Negative Reviews",
        "h_words_pos":  "Most Frequent Words — Positive Reviews",
        "h_abw":        "Discrepancies — Text Sentiment vs. Star Rating",
        "s_abw":        "Reviews where the AI model's reading contradicts the star rating. High confidence = certain model.",
        "h_browser":    "Review Browser",
        "s_browser":    "Full list of reviews — sortable and filterable",
        "search":       "Search in review text",
        "no_data":      "No data matches the current filter selection.",
        # Table columns
        "col_country":  "Country",
        "col_stars":    "Stars",
        "col_rlabel":   "Rating Label",
        "col_sent":     "Sentiment",
        "col_conf":     "Confidence",
        "col_text":     "Review Text",
        "col_date":     "Date",
        "col_match":    "Match",
        "col_title":    "Title",
        "btn_lang":     "🇩🇪 Deutsch",
        "pos_label":    "Positive",
        "neu_label":    "Neutral",
        "neg_label":    "Negative",
    },
    "de": {
        "title":        "Amazon Bewertungen  Sentiment-Analyse",
        "subtitle":     "RoBERTa Transformer · Kaggle-Datensatz · 21.214 Bewertungen",
        "tab0":         "Übersicht",
        "tab1":         "Zeitverlauf",
        "tab2":         "Länder",
        "tab3":         "Bewertungen",
        "filter_sent":  "Stimmung",
        "filter_land":  "Länder",
        "filter_year":  "Zeitraum",
        "filter_cert":  "Modell-Sicherheit",
        "filter_cert_s":"Wie sicher war die KI bei der Einschätzung?",
        "filter_abw":   "Nur Abweichungen",
        "kpi_total":    "Bewertungen gesamt",
        "kpi_period":   "aktueller Zeitraum",
        "kpi_rating":   "Ø Sternebewertung",
        "kpi_pos":      "Positiv",
        "kpi_neu":      "Neutral",
        "kpi_neg":      "Negativ",
        "kpi_abw":      "Abweichungen",
        "kpi_abw_s":    "Text ≠ Sterne",
        "vs_prior":     "vs. Vorperiode",
        # Overview
        "h_dist":       "Stimmungs-Verteilung",
        "s_dist":       "Modell-Ergebnis aus dem Text – unabhängig von der Sternebewertung",
        "h_vgl":        "Sterne-Rating vs. Text-Stimmung",
        "s_vgl":        "Wie oft stimmt das Modell mit der Sternebewertung überein?",
        "h_cert":       "Ø Modell-Sicherheit",
        "s_cert":       "Wie sicher war das RoBERTa-Modell bei seiner Einschätzung?",
        "h_trend":      "Monatlicher Stimmungs-Trend",
        "s_trend":      "Stimmungsentwicklung über den gesamten Zeitraum",
        # Time Series
        "h_area":       "Monatliches Bewertungsvolumen",
        "s_area":       "Gestapeltes Flächendiagramm – absolute Anzahl Bewertungen pro Monat",
        "h_nj":         "Negativanteil pro Jahr",
        "s_nj":         "Jährlicher Anteil negativer Bewertungen",
        "h_rj":         "Ø Sternebewertung pro Jahr",
        "s_rj":         "Jährlicher Durchschnitt der Sternebewertungen",
        # Countries
        "h_choro":      "Negativanteil nach Land",
        "s_choro":      "Anteil negativer Bewertungen pro Land – Hover für Details",
        "h_bubble":     "Bewertungsvolumen nach Standort",
        "s_bubble":     "Blasengröße = Anzahl Bewertungen · Farbe = Negativanteil",
        "h_bar15":      "Top 15 Länder – Stimmungsaufschlüsselung",
        "s_bar15":      "Absolute Bewertungsanzahl nach Stimmung pro Land",
        # Reviews
        "h_words_neg":  "Häufigste Wörter – Negative Bewertungen",
        "h_words_pos":  "Häufigste Wörter – Positive Bewertungen",
        "h_abw":        "Abweichungen – Text-Stimmung vs. Sterne-Bewertung",
        "s_abw":        "Bewertungen wo das Modell anders urteilt als die Sterne. Hohe Konfidenz = Modell war sicher.",
        "h_browser":    "Bewertungs-Browser",
        "s_browser":    "Alle Bewertungen des aktuellen Filters – sortier- und durchsuchbar",
        "search":       "Suchbegriff im Bewertungstext",
        "no_data":      "Keine Daten für die aktuelle Filterauswahl.",
        # Table columns
        "col_country":  "Land",
        "col_stars":    "Sterne",
        "col_rlabel":   "Sterne-Label",
        "col_sent":     "Stimmung",
        "col_conf":     "Konfidenz",
        "col_text":     "Bewertungstext",
        "col_date":     "Datum",
        "col_match":    "Übereinstimmung",
        "col_title":    "Titel",
        "btn_lang":     "🇬🇧 English",
        "pos_label":    "Positiv",
        "neu_label":    "Neutral",
        "neg_label":    "Negativ",
    }
}

# ── Daten laden ──────────────────────────────────────────────────────────────
@st.cache_data
def lade_daten():
    db_pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "amazon_reviews.db")
    if not os.path.exists(db_pfad):
        st.error("amazon_reviews.db nicht gefunden!")
        st.stop()
    conn = sqlite3.connect(db_pfad)
    df   = pd.read_sql("SELECT * FROM reviews WHERE review_text IS NOT NULL", conn)
    conn.close()

    df["review_datum"] = pd.to_datetime(df["review_datum"], errors="coerce")
    df["jahr"]         = df["review_datum"].dt.year

    LAND_ZU_NAME = {
        "US":"United States","GB":"United Kingdom","CA":"Canada","IN":"India",
        "IE":"Ireland","DK":"Denmark","NL":"Netherlands","AU":"Australia",
        "DE":"Germany","IT":"Italy","FR":"France","SE":"Sweden","ES":"Spain",
        "AE":"United Arab Emirates","PK":"Pakistan","IL":"Israel",
        "NZ":"New Zealand","BE":"Belgium","ZA":"South Africa",
        "PH":"Philippines","SG":"Singapore","RU":"Russia","NO":"Norway",
        "TR":"Turkey","PL":"Poland","PT":"Portugal","UA":"Ukraine",
        "HK":"Hong Kong","CH":"Switzerland","GR":"Greece","JP":"Japan",
        "AT":"Austria","RO":"Romania","NG":"Nigeria","MX":"Mexico",
        "FI":"Finland","EG":"Egypt","CZ":"Czech Republic","ID":"Indonesia",
        "BR":"Brazil","AR":"Argentina","VN":"Vietnam","TH":"Thailand",
        "MT":"Malta","CY":"Cyprus","SA":"Saudi Arabia","RS":"Serbia",
        "MY":"Malaysia","MA":"Morocco","CO":"Colombia","CN":"China",
        "BD":"Bangladesh","JM":"Jamaica","HR":"Croatia","HU":"Hungary",
        "KR":"South Korea","QA":"Qatar","KW":"Kuwait","BH":"Bahrain",
        "TW":"Taiwan","EE":"Estonia","LT":"Lithuania","LV":"Latvia",
        "SK":"Slovakia","SI":"Slovenia","BG":"Bulgaria","GE":"Georgia",
        "AM":"Armenia","AZ":"Azerbaijan","PE":"Peru","CL":"Chile",
        "EC":"Ecuador","VE":"Venezuela","PA":"Panama","CR":"Costa Rica",
        "DO":"Dominican Republic","LU":"Luxembourg","LB":"Lebanon",
        "JO":"Jordan","OM":"Oman","LK":"Sri Lanka","KE":"Kenya",
        "GH":"Ghana","TZ":"Tanzania","ET":"Ethiopia","UG":"Uganda",
        "MU":"Mauritius","BW":"Botswana","MN":"Mongolia","NP":"Nepal",
        "DZ":"Algeria","TN":"Tunisia","IS":"Iceland","JE":"Jersey",
    }
    NAME_ZU_PLOTLY = {v: ("Czechia" if v=="Czech Republic" else v) for v in LAND_ZU_NAME.values()}
    COORDS = {
        "US":(37.09,-95.71),"GB":(55.37,-3.44),"CA":(56.13,-106.35),
        "IN":(20.59,78.96),"IE":(53.41,-8.24),"DK":(56.26,9.50),
        "NL":(52.13,5.29),"AU":(-25.27,133.77),"DE":(51.17,10.45),
        "IT":(41.87,12.57),"FR":(46.23,2.21),"SE":(60.13,18.64),
        "ES":(40.46,-3.75),"AE":(23.42,53.85),"PK":(30.38,69.35),
        "NZ":(-40.90,174.89),"BE":(50.50,4.47),"ZA":(-30.56,22.94),
        "SG":(1.35,103.82),"RU":(61.52,105.32),"NO":(60.47,8.47),
        "TR":(38.96,35.24),"PL":(51.92,19.15),"PT":(39.40,-8.22),
        "CH":(46.82,8.23),"JP":(36.20,138.25),"AT":(47.52,14.55),
        "FI":(61.92,25.75),"MX":(23.63,-102.55),"BR":(-14.24,-51.93),
        "GR":(39.07,21.82),"IL":(31.05,34.85),"CZ":(49.82,15.47),
        "HU":(47.16,19.50),"RO":(45.94,24.97),"MY":(4.21,101.98),
        "PH":(12.88,121.77),"KR":(35.91,127.77),"NG":(9.08,8.68),
        "MA":(31.79,-7.09),"EG":(26.82,30.80),"TH":(15.87,100.99),
        "AR":(-38.42,-63.62),"CO":(4.57,-74.30),"SA":(23.89,45.08),
        "ID":(-0.79,113.92),"VN":(14.06,108.28),"UA":(48.38,31.17),
        "HK":(22.39,114.11),"TW":(23.70,121.00),"RS":(44.02,21.01),
        "CL":(-35.68,-71.54),"PE":(-9.19,-75.02),"KE":(-0.02,37.91),
        "GH":(7.95,-1.02),"BW":(-22.33,24.68),"MU":(-20.35,57.55),
    }

    df["land_name"]   = df["land"].map(LAND_ZU_NAME).fillna(df["land"])
    df["plotly_name"] = df["land_name"].map(NAME_ZU_PLOTLY).fillna(df["land_name"])
    df["land_lat"]    = df["land"].map(lambda x: COORDS.get(x,(None,None))[0])
    df["land_lon"]    = df["land"].map(lambda x: COORDS.get(x,(None,None))[1])
    return df

df = lade_daten()

STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with","is",
    "was","are","were","be","been","have","has","had","do","does","did","will",
    "would","could","should","i","my","me","we","our","you","your","it","its",
    "this","that","they","their","them","he","she","from","by","not","no","so",
    "as","if","what","which","who","how","all","just","more","also","very","can",
    "get","got","when","about","up","out","there","than","then","into","over",
    "after","amazon","order","product","delivery","item","time","use","said",
    "one","still","back","even","never","any","us","re","ve","dont","didnt",
    "cant","ive","really","review","account","customer","service","money",
}

def top_w(texte, n=12):
    alle = []
    for t in texte:
        w = re.findall(r"\b[a-z]{4,}\b", str(t).lower())
        alle.extend([x for x in w if x not in STOPWORDS])
    return Counter(alle).most_common(n)

# Design
BG2 = "white"; BG3 = "#f3f4f6"; BRD = "#e5e7eb"
ACC = "#1e40af"; TXT = "#111827"; TXT2 = "#6b7280"; TXT3 = "#9ca3af"
POS = "#166534"; POS_L = "#f0fdf4"
NEU = "#92400e"; NEU_L = "#fffbeb"
NEG = "#991b1b"; NEG_L = "#fef2f2"
DISC = "#5b21b6"; DISC_L = "#f5f3ff"
LB = dict(paper_bgcolor=BG2, plot_bgcolor=BG2,
          font=dict(color=TXT, family="Inter, Segoe UI, sans-serif", size=11),
          margin=dict(t=20, b=30, l=10, r=10),
          hoverlabel=dict(bgcolor=BG2, font_color=TXT))

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f9fafb; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    div[data-testid="metric-container"] {
        background: white; border: 1px solid #e5e7eb;
        border-radius: 8px; padding: 14px 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    h1 { font-size: 1.5rem !important; font-weight: 800 !important;
         letter-spacing: -0.02em !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        background: transparent; border: 1px solid #e5e7eb;
        border-radius: 6px; padding: 6px 16px;
        font-size: 0.82rem; font-weight: 600; color: #6b7280;
    }
    .stTabs [aria-selected="true"] {
        background: #1e40af !important; color: white !important;
        border-color: #1e40af !important;
    }
    .chart-card {
        background: white; border-radius: 8px; padding: 16px 18px;
        border: 1px solid #e5e7eb; margin-bottom: 14px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .card-title { font-weight: 700; font-size: 0.88rem;
                  color: #111827; margin-bottom: 2px; }
    .card-sub { font-size: 0.73rem; color: #9ca3af;
                margin-bottom: 10px; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar – Filter ──────────────────────────────────────────────────────────
lang = st.session_state.sprache
tx   = T[lang]

with st.sidebar:
    # Sprachschalter
    col_logo, col_btn = st.columns([2, 1])
    with col_logo:
        st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
                 width=100)
    with col_btn:
        st.write("")
        if st.button(tx["btn_lang"], key="lang_btn"):
            st.session_state.sprache = "de" if lang == "en" else "en"
            st.rerun()

    st.markdown("---")

    alle_laender = (df.groupby("land_name")["land_name"]
        .count().sort_values(ascending=False).index.tolist())
    alle_laender = [l for l in alle_laender if pd.notna(l) and str(l) != "nan"]

    st.markdown(f"**{tx['filter_sent']}**")
    if lang == "en":
        sent_opts = {"Positive":"positiv","Neutral":"neutral","Negative":"negativ"}
    else:
        sent_opts = {"Positiv":"positiv","Neutral":"neutral","Negativ":"negativ"}

    filter_sent = st.multiselect("", list(sent_opts.keys()),
                                 default=list(sent_opts.keys()),
                                 label_visibility="collapsed")
    filter_sent_vals = [sent_opts[s] for s in filter_sent]

    st.markdown(f"**{tx['filter_land']}**")
    filter_laender = st.multiselect("", alle_laender,
                                    default=alle_laender[:8],
                                    label_visibility="collapsed")

    st.markdown(f"**{tx['filter_year']}**")
    min_j = int(df["jahr"].min())
    max_j = int(df["jahr"].max())
    jahr_range = st.slider("", min_j, max_j, (2018, max_j),
                           label_visibility="collapsed")

    st.markdown(f"**{tx['filter_cert']}**")
    st.caption(tx["filter_cert_s"])
    min_k = st.slider("Konfidenz", 0.0, 1.0, 0.0, 0.1,
                      label_visibility="collapsed",
                      format="%.0f%%")

    nur_abw = st.checkbox(tx["filter_abw"])
    st.markdown("---")
    st.caption("Aug 2007 – Sep 2024 · RoBERTa")

# ── Filtern ───────────────────────────────────────────────────────────────────
d = df.copy()
if filter_sent_vals: d = d[d["text_sentiment"].isin(filter_sent_vals)]
if filter_laender:   d = d[d["land_name"].isin(filter_laender)]
d = d[d["jahr"].between(jahr_range[0], jahr_range[1])]
d = d[d["text_sentiment_score"] >= min_k]
if nur_abw:          d = d[d["uebereinstimmung"]==0]
n = len(d)

# Vorperiode
cur_len = jahr_range[1] - jahr_range[0]
prev_end = jahr_range[0] - 1
prev_start = prev_end - cur_len
d_vor = df.copy()
if filter_sent_vals: d_vor = d_vor[d_vor["text_sentiment"].isin(filter_sent_vals)]
if filter_laender:   d_vor = d_vor[d_vor["land_name"].isin(filter_laender)]
d_vor = d_vor[d_vor["jahr"].between(prev_start, prev_end)]
n_vor = len(d_vor)

lmap = {"positiv": tx["pos_label"], "neutral": tx["neu_label"], "negativ": tx["neg_label"]}

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"# 📦 {tx['title']}")
st.caption(f"{tx['subtitle']} · {n:,} {('reviews' if lang=='en' else 'Bewertungen')} im aktuellen Filter")

if n == 0:
    st.warning(tx["no_data"])
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
pos_n = int((d["text_sentiment"]=="positiv").sum())
neu_n = int((d["text_sentiment"]=="neutral").sum())
neg_n = int((d["text_sentiment"]=="negativ").sum())
abw_n = int((d["uebereinstimmung"]==0).sum())
avg_k = d["text_sentiment_score"].mean()
avg_r = d["rating"].mean()

pos_v = int((d_vor["text_sentiment"]=="positiv").sum()) if n_vor else None
neg_v = int((d_vor["text_sentiment"]=="negativ").sum()) if n_vor else None

def delta_txt(curr, prev):
    if prev is None or prev == 0: return None
    diff = curr - prev
    s = "+" if diff >= 0 else ""
    return f"{s}{diff:,} {tx['vs_prior']}"

k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric(tx["kpi_total"],   f"{n:,}",       delta_txt(n, n_vor))
k2.metric(tx["kpi_rating"],  f"{avg_r:.2f}")
k3.metric(tx["kpi_pos"],     f"{pos_n:,}",   f"{pos_n/n*100:.1f}%")
k4.metric(tx["kpi_neu"],     f"{neu_n:,}",   f"{neu_n/n*100:.1f}%")
k5.metric(tx["kpi_neg"],     f"{neg_n:,}",   f"{neg_n/n*100:.1f}%")
k6.metric(tx["kpi_abw"],     f"{abw_n:,}",   tx["kpi_abw_s"])

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab0, tab1, tab2, tab3 = st.tabs([
    tx["tab0"], tx["tab1"], tx["tab2"], tx["tab3"]
])

# ═══════════════════════════════════════════════════════
# TAB 0: ÜBERSICHT / OVERVIEW
# ═══════════════════════════════════════════════════════
with tab0:
    cnt = d["text_sentiment"].value_counts().reset_index()
    cnt.columns = ["s","n"]
    cnt["label"] = cnt["s"].map(lmap)

    col1, col2, col3 = st.columns([1.2, 1.2, 0.6])

    with col1:
        st.markdown(f'<div class="card-title">{tx["h_dist"]}</div>'
                    f'<div class="card-sub">{tx["s_dist"]}</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            values=cnt["n"], labels=cnt["label"], hole=0.62,
            marker=dict(
                colors=[{"positiv":"#22c55e","neutral":"#f59e0b","negativ":"#f87171"}.get(x,"#888")
                        for x in cnt["s"]],
                line=dict(color="white", width=3)),
            textinfo="percent+label", textfont=dict(size=11, color=TXT),
            hovertemplate="<b>%{label}</b><br>%{value:,} · %{percent}<extra></extra>"))
        fig.update_layout(**LB, height=280,
            legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
            annotations=[dict(text=f"<b>{n:,}</b>", x=0.5, y=0.5,
                showarrow=False, font=dict(size=18, color=TXT))])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f'<div class="card-title">{tx["h_vgl"]}</div>'
                    f'<div class="card-sub">{tx["s_vgl"]}</div>', unsafe_allow_html=True)
        vgl = d.groupby(["rating","text_sentiment"]).size().reset_index(name="n")
        vgl = vgl.dropna(subset=["rating"])
        vgl["r"] = vgl["rating"].astype(int).astype(str) + " ★"
        vgl["Sentiment"] = vgl["text_sentiment"].map(lmap)
        fig_v = go.Figure()
        for sent, c in [(tx["neg_label"],NEG),(tx["neu_label"],NEU),(tx["pos_label"],POS)]:
            sub = vgl[vgl["Sentiment"]==sent]
            fig_v.add_trace(go.Bar(name=sent, x=sub["r"], y=sub["n"], marker_color=c))
        fig_v.update_layout(**LB, barmode="group", height=280,
            legend=dict(orientation="h", y=1.06, x=1, xanchor="right"),
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor=BRD))
        st.plotly_chart(fig_v, use_container_width=True)

    with col3:
        st.markdown(f'<div class="card-title">{tx["h_cert"]}</div>'
                    f'<div class="card-sub">{tx["s_cert"]}</div>', unsafe_allow_html=True)
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number", value=avg_k*100,
            number={"suffix":"%","font":{"size":28,"color":TXT}},
            gauge={"axis":{"range":[0,100],"tickfont":{"color":TXT2,"size":9}},
                   "bar":{"color":ACC,"thickness":0.5},
                   "bgcolor":BG3,"bordercolor":BRD,
                   "steps":[{"range":[0,60],"color":"#fee2e2"},
                             {"range":[60,80],"color":"#fef9c3"},
                             {"range":[80,100],"color":"#dcfce7"}],
                   "threshold":{"line":{"color":POS,"width":2},"value":80}},
            title={"text":"","font":{"size":11}}))
        fig_g.update_layout(**LB, height=280)
        st.plotly_chart(fig_g, use_container_width=True)

    st.markdown(f'<div class="card-title">{tx["h_trend"]}</div>'
                f'<div class="card-sub">{tx["s_trend"]}</div>', unsafe_allow_html=True)
    zt = d.dropna(subset=["review_datum"]).copy()
    zt["monat"] = zt["review_datum"].dt.to_period("M").astype(str)
    agg = zt.groupby(["monat","text_sentiment"]).size().reset_index(name="n")
    agg["Stimmung"] = agg["text_sentiment"].map(lmap)
    fig_trend = go.Figure()
    fills = {tx["neg_label"]:"rgba(153,27,27,0.15)",
             tx["neu_label"]:"rgba(146,64,14,0.15)",
             tx["pos_label"]:"rgba(22,101,52,0.15)"}
    for sent, c in [(tx["neg_label"],NEG),(tx["neu_label"],NEU),(tx["pos_label"],POS)]:
        sub = agg[agg["Stimmung"]==sent]
        fig_trend.add_trace(go.Scatter(x=sub["monat"], y=sub["n"], name=sent,
            mode="lines", stackgroup="one", line=dict(color=c, width=1.5),
            fillcolor=fills.get(sent,"rgba(0,0,0,0.1)"),
            hovertemplate=f"<b>%{{x}}</b><br>{sent}: %{{y:,}}<extra></extra>"))
    fig_trend.update_layout(**LB, height=200, hovermode="x unified", showlegend=False,
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor=BRD))
    st.plotly_chart(fig_trend, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB 1: ZEITVERLAUF / TIME SERIES
# ═══════════════════════════════════════════════════════
with tab1:
    zt = d.dropna(subset=["review_datum"]).copy()
    zt["monat"] = zt["review_datum"].dt.to_period("M").astype(str)
    agg = zt.groupby(["monat","text_sentiment"]).size().reset_index(name="n")
    agg["Stimmung"] = agg["text_sentiment"].map(lmap)

    st.markdown(f'<div class="card-title">{tx["h_area"]}</div>'
                f'<div class="card-sub">{tx["s_area"]}</div>', unsafe_allow_html=True)
    fig_area = go.Figure()
    for sent, c in [(tx["neg_label"],NEG),(tx["neu_label"],NEU),(tx["pos_label"],POS)]:
        sub = agg[agg["Stimmung"]==sent]
        fig_area.add_trace(go.Scatter(x=sub["monat"], y=sub["n"], name=sent,
            mode="lines", stackgroup="one", line=dict(color=c, width=1.5),
            fillcolor=fills.get(sent,"rgba(0,0,0,0.1)"),
            hovertemplate=f"<b>%{{x}}</b><br>{sent}: %{{y:,}}<extra></extra>"))
    fig_area.update_layout(**LB, height=300, hovermode="x unified",
        legend=dict(orientation="h", y=1.06, x=1, xanchor="right"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=BRD))
    st.plotly_chart(fig_area, use_container_width=True)

    jhr = zt.groupby("jahr").agg(
        total=("text_sentiment","count"),
        neg=("text_sentiment",lambda x:(x=="negativ").sum()),
        avg_r=("rating","mean")).reset_index()
    jhr["neg_pct"] = (jhr["neg"]/jhr["total"]*100).round(1)
    jhr["avg_r"]   = jhr["avg_r"].round(2)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="card-title">{tx["h_nj"]}</div>'
                    f'<div class="card-sub">{tx["s_nj"]}</div>', unsafe_allow_html=True)
        bar_c = [NEG if p>70 else NEU if p>50 else POS for p in jhr["neg_pct"]]
        fig_nj = go.Figure(go.Bar(x=jhr["jahr"], y=jhr["neg_pct"],
            marker_color=bar_c,
            text=jhr["neg_pct"].apply(lambda x: f"{x:.0f}%"),
            textposition="outside", textfont=dict(color=TXT, size=10),
            hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>"))
        fig_nj.update_layout(**LB, height=280,
            yaxis=dict(range=[0,105], ticksuffix="%", showgrid=True, gridcolor=BRD),
            xaxis=dict(showgrid=False))
        st.plotly_chart(fig_nj, use_container_width=True)

    with col2:
        st.markdown(f'<div class="card-title">{tx["h_rj"]}</div>'
                    f'<div class="card-sub">{tx["s_rj"]}</div>', unsafe_allow_html=True)
        fig_rj = go.Figure()
        fig_rj.add_trace(go.Scatter(x=jhr["jahr"], y=jhr["avg_r"],
            mode="lines+markers", line=dict(color=ACC, width=2),
            marker=dict(size=6, color=ACC, line=dict(color="white", width=2)),
            fill="tozeroy", fillcolor="rgba(30,64,175,0.07)",
            hovertemplate="<b>%{x}</b><br>%{y:.2f} ★<extra></extra>"))
        fig_rj.add_hline(y=jhr["avg_r"].mean(), line_dash="dot",
            line_color=TXT3, line_width=1,
            annotation_text=f"Ø {jhr['avg_r'].mean():.2f}",
            annotation_font=dict(color=TXT3, size=10))
        fig_rj.update_layout(**LB, height=280,
            yaxis=dict(range=[1,5.3], tickvals=[1,2,3,4,5],
                       showgrid=True, gridcolor=BRD),
            xaxis=dict(showgrid=False))
        st.plotly_chart(fig_rj, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB 2: LÄNDER / COUNTRIES
# ═══════════════════════════════════════════════════════
with tab2:
    la = d.groupby(["land","land_name","plotly_name","land_lat","land_lon"]).agg(
        count=("land","count"),
        neg_pct=("text_sentiment",lambda x:round((x=="negativ").mean()*100,1)),
        pos_pct=("text_sentiment",lambda x:round((x=="positiv").mean()*100,1)),
        neu_pct=("text_sentiment",lambda x:round((x=="neutral").mean()*100,1)),
        avg_r=("rating",lambda x:round(x.mean(),2)),
        neg=("text_sentiment",lambda x:(x=="negativ").sum()),
        pos=("text_sentiment",lambda x:(x=="positiv").sum()),
        neu=("text_sentiment",lambda x:(x=="neutral").sum()),
    ).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="card-title">{tx["h_choro"]}</div>'
                    f'<div class="card-sub">{tx["s_choro"]}</div>', unsafe_allow_html=True)
        la_map = la[la["count"]>=3].copy()
        pct_label = "% Negative" if lang=="en" else "% Negativ"
        fig_k = go.Figure(go.Choropleth(
            locations=la_map["plotly_name"], locationmode="country names",
            z=la_map["neg_pct"],
            colorscale=[[0,"#bbf7d0"],[0.4,"#fef9c3"],[0.75,"#fecaca"],[1,"#991b1b"]],
            zmin=0, zmax=100, text=la_map["land_name"],
            customdata=la_map[["count","avg_r","pos_pct","neu_pct","neg_pct"]].values,
            hovertemplate=(
                "<b>%{text}</b><br>"
                f"{'Reviews' if lang=='en' else 'Bewertungen'}: %{{customdata[0]:,}}<br>"
                f"{'Avg. Rating' if lang=='en' else 'Ø Sterne'}: %{{customdata[1]:.2f}} ★<br>"
                f"{tx['pos_label']}: %{{customdata[2]:.1f}}%<br>"
                f"{tx['neg_label']}: %{{customdata[4]:.1f}}%<extra></extra>"
            ),
            colorbar=dict(title=dict(text=pct_label, font=dict(size=10,color=TXT2)),
                tickfont=dict(size=9,color=TXT2), thickness=12, len=0.65, ticksuffix="%"),
            marker=dict(line=dict(color="white", width=0.4)),
        ))
        fig_k.update_layout(paper_bgcolor=BG2, plot_bgcolor=BG2,
            font=dict(color=TXT, family="Inter, Segoe UI"),
            margin=dict(t=0,b=0,l=0,r=0), height=380,
            geo=dict(bgcolor=BG2, showframe=False, showcoastlines=True,
                coastlinecolor=BRD, coastlinewidth=0.5, landcolor="#f3f4f6",
                showocean=True, oceancolor="#e0f2fe", showlakes=True,
                lakecolor="#e0f2fe", projection_type="natural earth"))
        st.plotly_chart(fig_k, use_container_width=True)

    with col2:
        st.markdown(f'<div class="card-title">{tx["h_bubble"]}</div>'
                    f'<div class="card-sub">{tx["s_bubble"]}</div>', unsafe_allow_html=True)
        la_b = la[la["land_lat"].notna() & (la["count"]>=3)].copy()
        fig_b2 = go.Figure(go.Scattergeo(
            lat=la_b["land_lat"], lon=la_b["land_lon"],
            text=la_b["land_name"],
            customdata=la_b[["count","neg_pct","avg_r"]].values,
            mode="markers",
            marker=dict(
                size=la_b["count"].apply(lambda x: max(4, min(40, x/80))),
                color=la_b["neg_pct"],
                colorscale=[[0,"#bbf7d0"],[0.5,"#fef9c3"],[1,"#991b1b"]],
                cmin=0, cmax=100, line=dict(color="white",width=0.5), opacity=0.85,
                colorbar=dict(title=dict(text=pct_label,font=dict(size=10,color=TXT2)),
                    tickfont=dict(size=9,color=TXT2),thickness=12,len=0.6,ticksuffix="%"),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                f"{'Reviews' if lang=='en' else 'Bewertungen'}: %{{customdata[0]:,}}<br>"
                f"{tx['neg_label']}: %{{customdata[1]:.1f}}%<br>"
                f"{'Avg. Rating' if lang=='en' else 'Ø Sterne'}: %{{customdata[2]:.2f}} ★"
                "<extra></extra>"
            ),
        ))
        fig_b2.update_layout(paper_bgcolor=BG2, plot_bgcolor=BG2,
            font=dict(color=TXT, family="Inter, Segoe UI"),
            margin=dict(t=0,b=0,l=0,r=0), height=380,
            geo=dict(bgcolor=BG2, showframe=False, showcoastlines=True,
                coastlinecolor=BRD, coastlinewidth=0.5, landcolor="#f3f4f6",
                showocean=True, oceancolor="#e0f2fe", projection_type="natural earth"))
        st.plotly_chart(fig_b2, use_container_width=True)

    st.markdown(f'<div class="card-title">{tx["h_bar15"]}</div>'
                f'<div class="card-sub">{tx["s_bar15"]}</div>', unsafe_allow_html=True)
    top15 = la[la["count"]>=10].nlargest(15,"count")
    fig_bar = go.Figure()
    for sent, lbl, c in [("neg",tx["neg_label"],NEG),("neu",tx["neu_label"],NEU),("pos",tx["pos_label"],POS)]:
        fig_bar.add_trace(go.Bar(name=lbl, x=top15["land_name"],
            y=top15[sent], marker_color=c,
            hovertemplate=f"<b>%{{x}}</b><br>{lbl}: %{{y:,}}<extra></extra>"))
    fig_bar.update_layout(**LB, barmode="stack", height=320,
        legend=dict(orientation="h", y=1.06, x=1, xanchor="right"),
        xaxis=dict(tickangle=-30, showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor=BRD))
    st.plotly_chart(fig_bar, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB 3: BEWERTUNGEN / REVIEWS
# ═══════════════════════════════════════════════════════
with tab3:
    def wfig(sentiment, color, title):
        top = top_w(d[d["text_sentiment"]==sentiment]["review_text"], 12)
        if not top: return go.Figure().update_layout(**LB, height=360)
        wdf = pd.DataFrame(top, columns=["word","n"])
        fig = go.Figure(go.Bar(
            x=wdf["n"], y=wdf["word"], orientation="h",
            marker=dict(color=wdf["n"],
                colorscale=[[0,BG3],[1,color]],
                line=dict(color=BRD, width=0.5)),
            text=wdf["n"], textposition="outside",
            textfont=dict(color=TXT2, size=10),
            hovertemplate="<b>%{y}</b>: %{x:,}<extra></extra>"))
        fig.update_layout(**LB, height=380,
            title=dict(text=title, font=dict(size=12, color=TXT)),
            yaxis=dict(autorange="reversed"),
            xaxis=dict(showgrid=True, gridcolor=BRD))
        return fig

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(wfig("negativ", NEG, tx["h_words_neg"]),
                        use_container_width=True)
    with col2:
        st.plotly_chart(wfig("positiv", POS, tx["h_words_pos"]),
                        use_container_width=True)

    st.markdown(f'<div class="card-title">{tx["h_abw"]}</div>'
                f'<div class="card-sub">{tx["s_abw"]}</div>', unsafe_allow_html=True)
    abw = d[d["uebereinstimmung"]==0].sort_values("text_sentiment_score", ascending=False)
    abw_s = abw[["land_name","rating","rating_sentiment","text_sentiment",
                 "text_sentiment_score","review_text"]].head(100).copy()
    abw_s["rating_sentiment"] = abw_s["rating_sentiment"].map(lmap).fillna(abw_s["rating_sentiment"])
    abw_s["text_sentiment"]   = abw_s["text_sentiment"].map(lmap).fillna(abw_s["text_sentiment"])
    abw_s.columns = [tx["col_country"], tx["col_stars"], tx["col_rlabel"],
                     tx["col_sent"], tx["col_conf"], tx["col_text"]]
    st.dataframe(abw_s, use_container_width=True, height=320)

    st.markdown(f'<div class="card-title">{tx["h_browser"]}</div>'
                f'<div class="card-sub">{tx["s_browser"]}</div>', unsafe_allow_html=True)
    suche = st.text_input(tx["search"], placeholder="e.g. refund, broken, excellent...")
    br = d.copy()
    if suche:
        br = br[br["review_text"].str.contains(suche, case=False, na=False)]
    br_show = br[["review_datum","land_name","rating","text_sentiment",
                  "text_sentiment_score","review_text"]].head(300).copy()
    br_show["text_sentiment"] = br_show["text_sentiment"].map(lmap).fillna(br_show["text_sentiment"])
    br_show.columns = [tx["col_date"], tx["col_country"], tx["col_stars"],
                       tx["col_sent"], tx["col_conf"], tx["col_text"]]
    st.dataframe(br_show, use_container_width=True, height=400)
    st.caption(f"{len(br):,} {'reviews' if lang=='en' else 'Bewertungen'} · max. 300")

st.markdown("---")
st.caption("Amazon Reviews Sentiment Dashboard · RoBERTa Transformer · Streamlit + Plotly")
