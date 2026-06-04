import streamlit as st
import pandas as pd
import sqlite3
import re
import os
import plotly.graph_objects as go
from collections import Counter

st.set_page_config(
    page_title="Amazon Reviews – Sentiment Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS: exakt wie das Dash-Dashboard ───────────────────────────────────────
st.markdown("""
<style>
    /* Hintergrund */
    .main, .stApp { background-color: #f9fafb !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* Header */
    .dash-header {
        background: white;
        border-bottom: 1px solid #e5e7eb;
        padding: 0 36px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 54px;
        position: sticky;
        top: 0;
        z-index: 999;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        margin-bottom: 0;
    }
    .dash-logo { height: 20px; filter: brightness(0); opacity: 0.85; }
    .dash-title { font-size: 0.97rem; font-weight: 400; color: #6b7280; }
    .dash-subtitle { font-size: 0.67rem; color: #9ca3af; }
    .dash-info { text-align: right; font-size: 0.72rem; }
    .dash-info-bold { font-weight: 600; color: #111827; }

    /* Filter Bar */
    .filter-bar {
        background: white;
        border-bottom: 1px solid #e5e7eb;
        padding: 10px 36px;
        margin-bottom: 0;
    }

    /* Content */
    .dash-content { padding: 20px 36px; }

    /* KPI Karten */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(6,1fr);
        gap: 12px;
        margin-bottom: 18px;
    }
    .kpi-card {
        background: white;
        border-radius: 8px;
        padding: 18px 20px;
        border: 1px solid #e5e7eb;
        border-left-width: 3px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .kpi-value {
        font-size: 1.9rem; font-weight: 800;
        line-height: 1.1; letter-spacing: -0.02em;
    }
    .kpi-sub { font-size: 0.75rem; opacity: 0.7; margin-top: 1px; }
    .kpi-label {
        font-size: 0.65rem; color: #6b7280;
        text-transform: uppercase; letter-spacing: 0.08em;
        margin-top: 8px; font-weight: 600;
    }
    .kpi-delta { font-size: 0.68rem; color: #9ca3af; margin-top: 4px; }

    /* Chart Karten */
    .chart-card {
        background: white;
        border-radius: 8px;
        padding: 20px 22px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 14px;
    }
    .chart-title {
        font-weight: 700; color: #111827;
        font-size: 0.88rem; margin-bottom: 2px;
    }
    .chart-sub {
        font-size: 0.73rem; color: #9ca3af;
        margin-bottom: 12px; line-height: 1.5;
    }

    /* Tabs wie Dash Buttons */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px; background: transparent;
        border-bottom: none;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 7px 16px;
        font-size: 0.8rem; font-weight: 600;
        color: #6b7280;
    }
    .stTabs [aria-selected="true"] {
        background: #1e40af !important;
        color: white !important;
        border-color: #1e40af !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e5e7eb;
    }

    /* Metrics ausblenden (eigene KPIs) */
    div[data-testid="metric-container"] { display: none; }

    /* Streamlit padding weg */
    div[data-testid="stVerticalBlock"] { gap: 0rem; }
    .element-container { margin-bottom: 0; }
</style>
""", unsafe_allow_html=True)

# ── Sprachzustand ────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"

LMAP = {
    "en": {"pos":"Positive","neu":"Neutral","neg":"Negative"},
    "de": {"pos":"Positiv", "neu":"Neutral", "neg":"Negativ"},
}

# ── Daten laden ──────────────────────────────────────────────────────────────
@st.cache_data
def lade_daten():
    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "amazon_reviews.db")
    if not os.path.exists(db):
        st.error("amazon_reviews.db nicht gefunden!")
        st.stop()
    conn = sqlite3.connect(db)
    df = pd.read_sql("SELECT * FROM reviews WHERE review_text IS NOT NULL", conn)
    conn.close()
    df["review_datum"] = pd.to_datetime(df["review_datum"], errors="coerce")
    df["jahr"] = df["review_datum"].dt.year
    NAMES = {
        "US":"United States","GB":"United Kingdom","CA":"Canada","IN":"India",
        "IE":"Ireland","DK":"Denmark","NL":"Netherlands","AU":"Australia",
        "DE":"Germany","IT":"Italy","FR":"France","SE":"Sweden","ES":"Spain",
        "AE":"United Arab Emirates","PK":"Pakistan","NZ":"New Zealand",
        "BE":"Belgium","ZA":"South Africa","PH":"Philippines","SG":"Singapore",
        "RU":"Russia","NO":"Norway","TR":"Turkey","PL":"Poland","PT":"Portugal",
        "UA":"Ukraine","HK":"Hong Kong","CH":"Switzerland","GR":"Greece",
        "JP":"Japan","AT":"Austria","RO":"Romania","NG":"Nigeria","MX":"Mexico",
        "FI":"Finland","EG":"Egypt","CZ":"Czech Republic","ID":"Indonesia",
        "BR":"Brazil","AR":"Argentina","VN":"Vietnam","TH":"Thailand",
        "SA":"Saudi Arabia","MY":"Malaysia","MA":"Morocco","CO":"Colombia",
        "KR":"South Korea","IL":"Israel","HU":"Hungary","HR":"Croatia",
        "BD":"Bangladesh","LK":"Sri Lanka","KE":"Kenya","GH":"Ghana",
    }
    PLOTLY = {v:("Czechia" if v=="Czech Republic" else v) for v in NAMES.values()}
    COORDS = {
        "US":(37.09,-95.71),"GB":(55.37,-3.44),"CA":(56.13,-106.35),
        "IN":(20.59,78.96),"IE":(53.41,-8.24),"DK":(56.26,9.50),
        "NL":(52.13,5.29),"AU":(-25.27,133.77),"DE":(51.17,10.45),
        "IT":(41.87,12.57),"FR":(46.23,2.21),"SE":(60.13,18.64),
        "ES":(40.46,-3.75),"AE":(23.42,53.85),"NZ":(-40.90,174.89),
        "BE":(50.50,4.47),"ZA":(-30.56,22.94),"SG":(1.35,103.82),
        "RU":(61.52,105.32),"NO":(60.47,8.47),"TR":(38.96,35.24),
        "PL":(51.92,19.15),"PT":(39.40,-8.22),"CH":(46.82,8.23),
        "JP":(36.20,138.25),"AT":(47.52,14.55),"FI":(61.92,25.75),
        "MX":(23.63,-102.55),"BR":(-14.24,-51.93),"GR":(39.07,21.82),
        "IL":(31.05,34.85),"MY":(4.21,101.98),"KR":(35.91,127.77),
        "NG":(9.08,8.68),"MA":(31.79,-7.09),"EG":(26.82,30.80),
        "AR":(-38.42,-63.62),"CO":(4.57,-74.30),"SA":(23.89,45.08),
        "UA":(48.38,31.17),"HK":(22.39,114.11),"VN":(14.06,108.28),
        "TH":(15.87,100.99),"ID":(-0.79,113.92),
    }
    df["land_name"]   = df["land"].map(NAMES).fillna(df["land"])
    df["plotly_name"] = df["land_name"].map(PLOTLY).fillna(df["land_name"])
    df["land_lat"]    = df["land"].map(lambda x: COORDS.get(x,(None,None))[0])
    df["land_lon"]    = df["land"].map(lambda x: COORDS.get(x,(None,None))[1])
    return df

df = lade_daten()

STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with","is",
    "was","are","were","be","been","have","has","had","do","does","did","will",
    "would","could","should","i","my","me","we","our","you","your","it","its",
    "this","that","they","their","them","from","by","not","no","so","as","if",
    "what","which","who","how","all","just","more","also","very","can","get",
    "got","when","about","up","out","there","than","then","into","over","after",
    "amazon","order","product","delivery","item","time","use","said","one",
    "still","back","even","never","any","us","dont","didnt","cant","ive",
    "really","review","account","customer","service","money","email",
}

def top_w(texte, n=12):
    alle = []
    for t in texte:
        w = re.findall(r"\b[a-z]{4,}\b", str(t).lower())
        alle.extend([x for x in w if x not in STOPWORDS])
    return Counter(alle).most_common(n)

# Design
ACC="#1e40af"; TXT="#111827"; TXT2="#6b7280"; TXT3="#9ca3af"
BG2="white";   BG3="#f3f4f6"; BRD="#e5e7eb"
POS="#166534"; NEU="#92400e"; NEG="#991b1b"; DISC="#5b21b6"
LB = dict(paper_bgcolor=BG2,plot_bgcolor=BG2,
          font=dict(color=TXT,family="Inter, Segoe UI, sans-serif",size=11),
          margin=dict(t=20,b=30,l=10,r=10),
          hoverlabel=dict(bgcolor=BG2,font_color=TXT))

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    col1, col2 = st.columns([3,1])
    with col1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=90)
    with col2:
        st.write("")
        lang = st.session_state.lang
        btn_txt = "🇩🇪 DE" if lang=="en" else "🇬🇧 EN"
        if st.button(btn_txt, key="langbtn"):
            st.session_state.lang = "de" if lang=="en" else "en"
            st.rerun()

    lang = st.session_state.lang
    lmap = LMAP[lang]
    st.markdown("---")

    alle_laender = (df.groupby("land_name")["land_name"]
        .count().sort_values(ascending=False).index.tolist())

    lbl_sent = "SENTIMENT" if lang=="en" else "STIMMUNG"
    lbl_land = "COUNTRIES" if lang=="en" else "LÄNDER"
    lbl_year = "YEAR RANGE" if lang=="en" else "ZEITRAUM"
    lbl_cert = "MODEL CERTAINTY" if lang=="en" else "MODELL-SICHERHEIT"
    lbl_abw  = "Discrepancies only" if lang=="en" else "Nur Abweichungen"

    st.markdown(f"**{lbl_sent}**")
    if lang=="en":
        sopts = {"Positive":"positiv","Neutral":"neutral","Negative":"negativ"}
    else:
        sopts = {"Positiv":"positiv","Neutral":"neutral","Negativ":"negativ"}
    filt_s = st.multiselect("",list(sopts.keys()),default=list(sopts.keys()),
                            label_visibility="collapsed")
    filt_sv = [sopts[s] for s in filt_s]

    st.markdown(f"**{lbl_land}**")
    filt_l = st.multiselect("",alle_laender,default=alle_laender[:8],
                            label_visibility="collapsed")

    st.markdown(f"**{lbl_year}**")
    min_j,max_j = int(df["jahr"].min()),int(df["jahr"].max())
    yr = st.slider("",min_j,max_j,(2018,max_j),label_visibility="collapsed")

    st.markdown(f"**{lbl_cert}**")
    if lang=="en": st.caption("Min. AI confidence in its classification")
    else:          st.caption("Wie sicher war die KI?")
    min_k = st.slider("Konfidenz",0.0,1.0,0.0,0.1,label_visibility="collapsed")

    nur_abw = st.checkbox(lbl_abw)
    st.markdown("---")
    st.caption("Aug 2007 – Sep 2024 · RoBERTa · Kaggle")

# ── Filter anwenden ──────────────────────────────────────────────────────────
d = df.copy()
if filt_sv: d = d[d["text_sentiment"].isin(filt_sv)]
if filt_l:  d = d[d["land_name"].isin(filt_l)]
d = d[d["jahr"].between(yr[0],yr[1])]
d = d[d["text_sentiment_score"] >= min_k]
if nur_abw: d = d[d["uebereinstimmung"]==0]
n = len(d)

d_vor = df.copy()
if filt_sv: d_vor = d_vor[d_vor["text_sentiment"].isin(filt_sv)]
if filt_l:  d_vor = d_vor[d_vor["land_name"].isin(filt_l)]
d_vor = d_vor[d_vor["jahr"].between(yr[0]-(yr[1]-yr[0]+1), yr[0]-1)]
n_vor = len(d_vor)

lm = {"positiv":lmap["pos"],"neutral":lmap["neu"],"negativ":lmap["neg"]}

if n == 0:
    st.warning("No data." if lang=="en" else "Keine Daten.")
    st.stop()

pos_n=int((d["text_sentiment"]=="positiv").sum())
neu_n=int((d["text_sentiment"]=="neutral").sum())
neg_n=int((d["text_sentiment"]=="negativ").sum())
abw_n=int((d["uebereinstimmung"]==0).sum())
avg_k=d["text_sentiment_score"].mean()
avg_r=d["rating"].mean()

pos_v=int((d_vor["text_sentiment"]=="positiv").sum()) if n_vor else None
neg_v=int((d_vor["text_sentiment"]=="negativ").sum()) if n_vor else None
def dlt(c,p):
    if not p or p==0: return ""
    d=c-p; s="+" if d>=0 else ""
    return f"<div class='kpi-delta'>{s}{d:,} ({s}{d/p*100:.1f}%) {'vs prior' if lang=='en' else 'vs. Vorperiode'}</div>"

# ── Header ────────────────────────────────────────────────────────────────────
rev_txt = f"{n:,} reviews" if lang=="en" else f"{n:,} Bewertungen"
ttl = "Reviews  Sentiment Analytics" if lang=="en" else "Bewertungen  Sentiment-Analyse"
st.markdown(f"""
<div class="dash-header">
  <div style="display:flex;align-items:center;gap:10px">
    <div style="width:3px;height:28px;background:{ACC};border-radius:2px"></div>
    <img class="dash-logo"
         src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg">
    <div>
      <div style="font-weight:700;font-size:0.97rem;color:{TXT}">{ttl}</div>
      <div class="dash-subtitle">RoBERTa Transformer · Kaggle Dataset</div>
    </div>
  </div>
  <div class="dash-info">
    <div class="dash-info-bold">{rev_txt}</div>
    <div style="color:{TXT3}">Aug 2007 – Sep 2024</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Karten ────────────────────────────────────────────────────────────────
kpi_items = [
    (f"{n:,}",    "Total Reviews" if lang=="en" else "Bewertungen",
     "current period" if lang=="en" else "aktueller Zeitraum", ACC, "#eff6ff", dlt(n,n_vor)),
    (f"{avg_r:.2f}", "Avg. Rating" if lang=="en" else "Ø Sternebewertung",
     "out of 5.0", TXT, BG3, ""),
    (f"{pos_n:,}", "Positive" if lang=="en" else "Positiv",
     f"{pos_n/n*100:.1f}%", POS, "#f0fdf4", dlt(pos_n,pos_v)),
    (f"{neu_n:,}", "Neutral",
     f"{neu_n/n*100:.1f}%", NEU, "#fffbeb", ""),
    (f"{neg_n:,}", "Negative" if lang=="en" else "Negativ",
     f"{neg_n/n*100:.1f}%", NEG, "#fef2f2", dlt(neg_n,neg_v)),
    (f"{abw_n:,}", "Discrepancies" if lang=="en" else "Abweichungen",
     "text ≠ star rating" if lang=="en" else "Text ≠ Sterne", DISC, "#f5f3ff", ""),
]

kpi_html = '<div class="kpi-grid">'
for val,lbl,sub,color,bg,delta in kpi_items:
    kpi_html += f"""
    <div class="kpi-card" style="border-left-color:{color};background:{bg}">
        <div class="kpi-value" style="color:{color}">{val}</div>
        <div class="kpi-sub" style="color:{color}">{sub}</div>
        <div class="kpi-label">{lbl}</div>
        {delta}
    </div>"""
kpi_html += "</div>"

st.markdown('<div class="dash-content">', unsafe_allow_html=True)
st.markdown(kpi_html, unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
if lang=="en":
    tab_names = ["Overview","Time Series","Countries","Reviews"]
else:
    tab_names = ["Übersicht","Zeitverlauf","Länder","Bewertungen"]

tab0,tab1,tab2,tab3 = st.tabs(tab_names)

fill_colors = {
    lm["neg"]:"rgba(153,27,27,0.15)",
    lm["neu"]:"rgba(146,64,14,0.15)",
    lm["pos"]:"rgba(22,101,52,0.15)",
}

def card(title, subtitle, fig):
    st.markdown(f'<div class="chart-card"><div class="chart-title">{title}</div>'
                f'<div class="chart-sub">{subtitle}</div></div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

# ══════════════════════════════════════════════════
# TAB 0: OVERVIEW / ÜBERSICHT
# ══════════════════════════════════════════════════
with tab0:
    cnt = d["text_sentiment"].value_counts().reset_index()
    cnt.columns=["s","n"]; cnt["label"]=cnt["s"].map(lm)
    fig_pie=go.Figure(go.Pie(
        values=cnt["n"],labels=cnt["label"],hole=0.62,
        marker=dict(colors=[{"positiv":"#22c55e","neutral":"#f59e0b","negativ":"#f87171"}.get(x,"#888") for x in cnt["s"]],
                    line=dict(color="white",width=3)),
        textinfo="percent+label",textfont=dict(size=11,color=TXT),
        hovertemplate="<b>%{label}</b><br>%{value:,} · %{percent}<extra></extra>"))
    fig_pie.update_layout(**LB,height=280,
        legend=dict(orientation="h",y=-0.12,x=0.5,xanchor="center"),
        annotations=[dict(text=f"<b>{n:,}</b>",x=0.5,y=0.5,showarrow=False,
            font=dict(size=18,color=TXT))])

    vgl=d.groupby(["rating","text_sentiment"]).size().reset_index(name="n")
    vgl=vgl.dropna(subset=["rating"])
    vgl["r"]=vgl["rating"].astype(int).astype(str)+" ★"
    vgl["S"]=vgl["text_sentiment"].map(lm)
    fig_vgl=go.Figure()
    for s,c in [(lm["neg"],NEG),(lm["neu"],NEU),(lm["pos"],POS)]:
        sub=vgl[vgl["S"]==s]
        fig_vgl.add_trace(go.Bar(name=s,x=sub["r"],y=sub["n"],marker_color=c))
    fig_vgl.update_layout(**LB,barmode="group",height=280,
        legend=dict(orientation="h",y=1.06,x=1,xanchor="right"),
        xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor=BRD))

    fig_g=go.Figure(go.Indicator(
        mode="gauge+number",value=avg_k*100,
        number={"suffix":"%","font":{"size":28,"color":TXT}},
        gauge={"axis":{"range":[0,100],"tickfont":{"color":TXT2,"size":9}},
               "bar":{"color":ACC,"thickness":0.5},
               "bgcolor":BG3,"bordercolor":BRD,
               "steps":[{"range":[0,60],"color":"#fee2e2"},
                        {"range":[60,80],"color":"#fef9c3"},
                        {"range":[80,100],"color":"#dcfce7"}],
               "threshold":{"line":{"color":POS,"width":2},"value":80}},
        title={"text":"Avg. Model Certainty" if lang=="en" else "Ø Modell-Sicherheit",
               "font":{"color":TXT2,"size":11}}))
    fig_g.update_layout(**LB,height=280)

    zt=d.dropna(subset=["review_datum"]).copy()
    zt["monat"]=zt["review_datum"].dt.to_period("M").astype(str)
    agg=zt.groupby(["monat","text_sentiment"]).size().reset_index(name="n")
    agg["S"]=agg["text_sentiment"].map(lm)
    fig_tr=go.Figure()
    for s,c in [(lm["neg"],NEG),(lm["neu"],NEU),(lm["pos"],POS)]:
        sub=agg[agg["S"]==s]
        fig_tr.add_trace(go.Scatter(x=sub["monat"],y=sub["n"],name=s,mode="lines",
            stackgroup="one",line=dict(color=c,width=1.5),
            fillcolor=fill_colors.get(s,"rgba(0,0,0,0.1)")))
    fig_tr.update_layout(**LB,height=200,hovermode="x unified",showlegend=False,
        xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor=BRD))

    c1,c2,c3=st.columns([1.2,1.2,0.6])
    h_sd="Sentiment Distribution" if lang=="en" else "Stimmungs-Verteilung"
    s_sd="Model output from review text — independent of star ratings" if lang=="en" else "Modell-Ergebnis aus dem Text – unabhängig von der Sternebewertung"
    h_vg="Star Rating vs. Text Sentiment" if lang=="en" else "Sterne-Rating vs. Text-Stimmung"
    s_vg="How often does the model agree with the star rating?" if lang=="en" else "Wie oft stimmt das Modell mit der Sternebewertung überein?"
    h_ce="Avg. Model Certainty" if lang=="en" else "Ø Modell-Sicherheit"
    s_ce="How confident was RoBERTa?" if lang=="en" else "Wie sicher war das RoBERTa-Modell?"

    with c1:
        st.markdown(f'<div class="chart-card"><div class="chart-title">{h_sd}</div><div class="chart-sub">{s_sd}</div></div>',unsafe_allow_html=True)
        st.plotly_chart(fig_pie,use_container_width=True,config={"displayModeBar":False})
    with c2:
        st.markdown(f'<div class="chart-card"><div class="chart-title">{h_vg}</div><div class="chart-sub">{s_vg}</div></div>',unsafe_allow_html=True)
        st.plotly_chart(fig_vgl,use_container_width=True,config={"displayModeBar":False})
    with c3:
        st.markdown(f'<div class="chart-card"><div class="chart-title">{h_ce}</div><div class="chart-sub">{s_ce}</div></div>',unsafe_allow_html=True)
        st.plotly_chart(fig_g,use_container_width=True,config={"displayModeBar":False})

    h_tr="Monthly Sentiment Trend" if lang=="en" else "Monatlicher Stimmungs-Trend"
    s_tr="Sentiment evolution across the full dataset period" if lang=="en" else "Stimmungsentwicklung über den gesamten Zeitraum"
    st.markdown(f'<div class="chart-card"><div class="chart-title">{h_tr}</div><div class="chart-sub">{s_tr}</div></div>',unsafe_allow_html=True)
    st.plotly_chart(fig_tr,use_container_width=True,config={"displayModeBar":False})

# ══════════════════════════════════════════════════
# TAB 1: TIME SERIES / ZEITVERLAUF
# ══════════════════════════════════════════════════
with tab1:
    zt=d.dropna(subset=["review_datum"]).copy()
    zt["monat"]=zt["review_datum"].dt.to_period("M").astype(str)
    agg=zt.groupby(["monat","text_sentiment"]).size().reset_index(name="n")
    agg["S"]=agg["text_sentiment"].map(lm)
    fig_area=go.Figure()
    for s,c in [(lm["neg"],NEG),(lm["neu"],NEU),(lm["pos"],POS)]:
        sub=agg[agg["S"]==s]
        fig_area.add_trace(go.Scatter(x=sub["monat"],y=sub["n"],name=s,mode="lines",
            stackgroup="one",line=dict(color=c,width=1.5),
            fillcolor=fill_colors.get(s,"rgba(0,0,0,0.1)")))
    fig_area.update_layout(**LB,height=300,hovermode="x unified",
        legend=dict(orientation="h",y=1.06,x=1,xanchor="right"),
        xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor=BRD))

    jhr=zt.groupby("jahr").agg(total=("text_sentiment","count"),
        neg=("text_sentiment",lambda x:(x=="negativ").sum()),
        avg_r=("rating","mean")).reset_index()
    jhr["neg_pct"]=(jhr["neg"]/jhr["total"]*100).round(1)
    jhr["avg_r"]=jhr["avg_r"].round(2)
    bar_c=[NEG if p>70 else NEU if p>50 else POS for p in jhr["neg_pct"]]
    fig_nj=go.Figure(go.Bar(x=jhr["jahr"],y=jhr["neg_pct"],marker_color=bar_c,
        text=jhr["neg_pct"].apply(lambda x:f"{x:.0f}%"),
        textposition="outside",textfont=dict(color=TXT,size=10)))
    fig_nj.update_layout(**LB,height=280,
        yaxis=dict(range=[0,105],ticksuffix="%",showgrid=True,gridcolor=BRD),
        xaxis=dict(showgrid=False))

    fig_rj=go.Figure()
    fig_rj.add_trace(go.Scatter(x=jhr["jahr"],y=jhr["avg_r"],mode="lines+markers",
        line=dict(color=ACC,width=2),marker=dict(size=6,color=ACC,line=dict(color="white",width=2)),
        fill="tozeroy",fillcolor="rgba(30,64,175,0.07)"))
    fig_rj.add_hline(y=jhr["avg_r"].mean(),line_dash="dot",line_color=TXT3,line_width=1,
        annotation_text=f"Ø {jhr['avg_r'].mean():.2f}",annotation_font=dict(color=TXT3,size=10))
    fig_rj.update_layout(**LB,height=280,
        yaxis=dict(range=[1,5.3],tickvals=[1,2,3,4,5],showgrid=True,gridcolor=BRD),
        xaxis=dict(showgrid=False))

    h_a="Monthly Sentiment Volume" if lang=="en" else "Monatliches Bewertungsvolumen"
    s_a="Stacked area chart showing absolute review counts by sentiment per month" if lang=="en" else "Absolute Anzahl Bewertungen nach Stimmung pro Monat"
    h_n="Negative Sentiment Share by Year" if lang=="en" else "Negativanteil pro Jahr"
    s_n="Annual share of reviews classified as negative" if lang=="en" else "Jährlicher Anteil negativer Bewertungen"
    h_r="Average Star Rating by Year" if lang=="en" else "Ø Sternebewertung pro Jahr"
    s_r="Annual average star rating" if lang=="en" else "Jährlicher Durchschnitt der Sternebewertungen"

    st.markdown(f'<div class="chart-card"><div class="chart-title">{h_a}</div><div class="chart-sub">{s_a}</div></div>',unsafe_allow_html=True)
    st.plotly_chart(fig_area,use_container_width=True,config={"displayModeBar":False})
    c1,c2=st.columns(2)
    with c1:
        st.markdown(f'<div class="chart-card"><div class="chart-title">{h_n}</div><div class="chart-sub">{s_n}</div></div>',unsafe_allow_html=True)
        st.plotly_chart(fig_nj,use_container_width=True,config={"displayModeBar":False})
    with c2:
        st.markdown(f'<div class="chart-card"><div class="chart-title">{h_r}</div><div class="chart-sub">{s_r}</div></div>',unsafe_allow_html=True)
        st.plotly_chart(fig_rj,use_container_width=True,config={"displayModeBar":False})

# ══════════════════════════════════════════════════
# TAB 2: COUNTRIES / LÄNDER
# ══════════════════════════════════════════════════
with tab2:
    la=d.groupby(["land","land_name","plotly_name","land_lat","land_lon"]).agg(
        count=("land","count"),
        neg_pct=("text_sentiment",lambda x:round((x=="negativ").mean()*100,1)),
        pos_pct=("text_sentiment",lambda x:round((x=="positiv").mean()*100,1)),
        neu_pct=("text_sentiment",lambda x:round((x=="neutral").mean()*100,1)),
        avg_r=("rating",lambda x:round(x.mean(),2)),
        neg=("text_sentiment",lambda x:(x=="negativ").sum()),
        pos=("text_sentiment",lambda x:(x=="positiv").sum()),
        neu=("text_sentiment",lambda x:(x=="neutral").sum()),
    ).reset_index()

    pct_lbl="% Negative" if lang=="en" else "% Negativ"
    la_map=la[la["count"]>=3].copy()
    fig_k=go.Figure(go.Choropleth(
        locations=la_map["plotly_name"],locationmode="country names",
        z=la_map["neg_pct"],
        colorscale=[[0,"#bbf7d0"],[0.4,"#fef9c3"],[0.75,"#fecaca"],[1,"#991b1b"]],
        zmin=0,zmax=100,text=la_map["land_name"],
        customdata=la_map[["count","avg_r","pos_pct","neu_pct","neg_pct"]].values,
        hovertemplate=f"<b>%{{text}}</b><br>{'Reviews' if lang=='en' else 'Bewertungen'}: %{{customdata[0]:,}}<br>Ø ★: %{{customdata[1]:.2f}}<br>{lm['neg']}: %{{customdata[4]:.1f}}%<extra></extra>",
        colorbar=dict(title=dict(text=pct_lbl,font=dict(size=10,color=TXT2)),
            tickfont=dict(size=9,color=TXT2),thickness=12,len=0.65,ticksuffix="%"),
        marker=dict(line=dict(color="white",width=0.4))))
    fig_k.update_layout(paper_bgcolor=BG2,plot_bgcolor=BG2,
        font=dict(color=TXT,family="Inter, Segoe UI"),
        margin=dict(t=0,b=0,l=0,r=0),height=400,
        geo=dict(bgcolor=BG2,showframe=False,showcoastlines=True,
            coastlinecolor=BRD,coastlinewidth=0.5,landcolor="#f3f4f6",
            showocean=True,oceancolor="#e0f2fe",showlakes=True,
            lakecolor="#e0f2fe",projection_type="natural earth"))

    la_b=la[la["land_lat"].notna()&(la["count"]>=3)].copy()
    fig_b=go.Figure(go.Scattergeo(
        lat=la_b["land_lat"],lon=la_b["land_lon"],text=la_b["land_name"],
        customdata=la_b[["count","neg_pct","avg_r"]].values,mode="markers",
        marker=dict(size=la_b["count"].apply(lambda x:max(4,min(40,x/80))),
            color=la_b["neg_pct"],
            colorscale=[[0,"#bbf7d0"],[0.5,"#fef9c3"],[1,"#991b1b"]],
            cmin=0,cmax=100,line=dict(color="white",width=0.5),opacity=0.85,
            colorbar=dict(title=dict(text=pct_lbl,font=dict(size=10,color=TXT2)),
                tickfont=dict(size=9,color=TXT2),thickness=12,len=0.6,ticksuffix="%")),
        hovertemplate=f"<b>%{{text}}</b><br>{'Reviews' if lang=='en' else 'Bewertungen'}: %{{customdata[0]:,}}<br>{lm['neg']}: %{{customdata[1]:.1f}}%<extra></extra>"))
    fig_b.update_layout(paper_bgcolor=BG2,plot_bgcolor=BG2,
        font=dict(color=TXT,family="Inter, Segoe UI"),
        margin=dict(t=0,b=0,l=0,r=0),height=380,
        geo=dict(bgcolor=BG2,showframe=False,showcoastlines=True,
            coastlinecolor=BRD,landcolor="#f3f4f6",showocean=True,
            oceancolor="#e0f2fe",projection_type="natural earth"))

    top15=la[la["count"]>=10].nlargest(15,"count")
    fig_bar=go.Figure()
    for s,lbl,c in [("neg",lm["neg"],NEG),("neu",lm["neu"],NEU),("pos",lm["pos"],POS)]:
        fig_bar.add_trace(go.Bar(name=lbl,x=top15["land_name"],y=top15[s],marker_color=c))
    fig_bar.update_layout(**LB,barmode="stack",height=320,
        legend=dict(orientation="h",y=1.06,x=1,xanchor="right"),
        xaxis=dict(tickangle=-30,showgrid=False,tickfont=dict(size=9)),
        yaxis=dict(showgrid=True,gridcolor=BRD))

    h_ch="Negative Sentiment Heatmap" if lang=="en" else "Negativanteil nach Land"
    s_ch="Share of negative reviews per country — hover for details" if lang=="en" else "Anteil negativer Bewertungen – Hover für Details"
    h_bu="Review Volume by Location" if lang=="en" else "Bewertungsvolumen nach Standort"
    s_bu="Bubble size = number of reviews · Color = negative share" if lang=="en" else "Blasengröße = Anzahl Bewertungen · Farbe = Negativanteil"
    h_b15="Top 15 Countries — Sentiment Breakdown" if lang=="en" else "Top 15 Länder – Stimmungsaufschlüsselung"
    s_b15="Absolute review count split by sentiment" if lang=="en" else "Absolute Bewertungsanzahl nach Stimmung"

    c1,c2=st.columns(2)
    with c1:
        st.markdown(f'<div class="chart-card"><div class="chart-title">{h_ch}</div><div class="chart-sub">{s_ch}</div></div>',unsafe_allow_html=True)
        st.plotly_chart(fig_k,use_container_width=True,config={"displayModeBar":False})
    with c2:
        st.markdown(f'<div class="chart-card"><div class="chart-title">{h_bu}</div><div class="chart-sub">{s_bu}</div></div>',unsafe_allow_html=True)
        st.plotly_chart(fig_b,use_container_width=True,config={"displayModeBar":False})
    st.markdown(f'<div class="chart-card"><div class="chart-title">{h_b15}</div><div class="chart-sub">{s_b15}</div></div>',unsafe_allow_html=True)
    st.plotly_chart(fig_bar,use_container_width=True,config={"displayModeBar":False})

# ══════════════════════════════════════════════════
# TAB 3: REVIEWS / BEWERTUNGEN
# ══════════════════════════════════════════════════
with tab3:
    def wfig(sentiment,color,title):
        top=top_w(d[d["text_sentiment"]==sentiment]["review_text"],12)
        if not top: return go.Figure().update_layout(**LB,height=360)
        wdf=pd.DataFrame(top,columns=["word","n"])
        fig=go.Figure(go.Bar(x=wdf["n"],y=wdf["word"],orientation="h",
            marker=dict(color=wdf["n"],colorscale=[[0,BG3],[1,color]],
                line=dict(color=BRD,width=0.5)),
            text=wdf["n"],textposition="outside",textfont=dict(color=TXT2,size=10)))
        fig.update_layout(**LB,height=400,
            title=dict(text=title,font=dict(size=12,color=TXT)),
            yaxis=dict(autorange="reversed"),xaxis=dict(showgrid=True,gridcolor=BRD))
        return fig

    h_wn="Most Frequent Words — Negative Reviews" if lang=="en" else "Häufigste Wörter – Negative Bewertungen"
    h_wp="Most Frequent Words — Positive Reviews" if lang=="en" else "Häufigste Wörter – Positive Bewertungen"
    c1,c2=st.columns(2)
    with c1:
        st.markdown(f'<div class="chart-card"></div>',unsafe_allow_html=True)
        st.plotly_chart(wfig("negativ",NEG,h_wn),use_container_width=True,config={"displayModeBar":False})
    with c2:
        st.markdown(f'<div class="chart-card"></div>',unsafe_allow_html=True)
        st.plotly_chart(wfig("positiv",POS,h_wp),use_container_width=True,config={"displayModeBar":False})

    abw=d[d["uebereinstimmung"]==0].sort_values("text_sentiment_score",ascending=False)
    abw_s=abw[["land_name","rating","rating_sentiment","text_sentiment",
               "text_sentiment_score","review_text"]].head(100).copy()
    abw_s["rating_sentiment"]=abw_s["rating_sentiment"].map(lm).fillna(abw_s["rating_sentiment"])
    abw_s["text_sentiment"]=abw_s["text_sentiment"].map(lm).fillna(abw_s["text_sentiment"])
    if lang=="en":
        abw_s.columns=["Country","Stars","Rating Label","Sentiment","Confidence","Review Text"]
        h_aw="Discrepancies — Text Sentiment vs. Star Rating"
        s_aw="Reviews where the AI model contradicts the star rating. High confidence = certain model."
        h_br="Review Browser"; s_br="Full list — sortable and filterable"
        s_label="Search in review text"
    else:
        abw_s.columns=["Land","Sterne","Sterne-Label","Stimmung","Konfidenz","Bewertungstext"]
        h_aw="Abweichungen – Text-Stimmung vs. Sterne-Bewertung"
        s_aw="Bewertungen wo das Modell anders urteilt als die Sterne. Hohe Konfidenz = Modell war sicher."
        h_br="Bewertungs-Browser"; s_br="Alle Bewertungen – sortier- und durchsuchbar"
        s_label="Suchbegriff im Bewertungstext"

    st.markdown(f'<div class="chart-card"><div class="chart-title">{h_aw}</div><div class="chart-sub">{s_aw}</div></div>',unsafe_allow_html=True)
    st.dataframe(abw_s,use_container_width=True,height=320)

    st.markdown(f'<div class="chart-card"><div class="chart-title">{h_br}</div><div class="chart-sub">{s_br}</div></div>',unsafe_allow_html=True)
    suche=st.text_input(s_label,placeholder="e.g. refund, broken...")
    br=d.copy()
    if suche: br=br[br["review_text"].str.contains(suche,case=False,na=False)]
    br_s=br[["review_datum","land_name","rating","text_sentiment",
             "text_sentiment_score","review_text"]].head(300).copy()
    br_s["text_sentiment"]=br_s["text_sentiment"].map(lm).fillna(br_s["text_sentiment"])
    if lang=="en":
        br_s.columns=["Date","Country","Stars","Sentiment","Confidence","Review Text"]
    else:
        br_s.columns=["Datum","Land","Sterne","Stimmung","Konfidenz","Bewertungstext"]
    st.dataframe(br_s,use_container_width=True,height=400)
    rev_lbl="reviews" if lang=="en" else "Bewertungen"
    st.caption(f"{len(br):,} {rev_lbl} · max. 300")

st.markdown("</div>",unsafe_allow_html=True)
