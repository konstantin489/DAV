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
)

st.markdown("""
<style>
.main { background-color: #f9fafb; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
div[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background: transparent;
    padding: 7px 18px;
    font-size: 0.82rem;
    font-weight: 600;
    color: #6b7280;
}
.stTabs [aria-selected="true"] {
    background: #1e40af !important;
    color: white !important;
    border-color: #1e40af !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none; }
section[data-testid="stSidebar"] { background: white; }
</style>
""", unsafe_allow_html=True)

# ── Sprache ──────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"

# ── Daten ────────────────────────────────────────────────────────────────────
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
        "KR":"South Korea","IL":"Israel","HU":"Hungary","BD":"Bangladesh",
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

ACC="#1e40af"; TXT="#111827"; TXT2="#6b7280"; TXT3="#9ca3af"
BG2="white"; BG3="#f3f4f6"; BRD="#e5e7eb"
POS="#166534"; NEU="#92400e"; NEG="#991b1b"; DISC="#5b21b6"
LB = dict(paper_bgcolor=BG2, plot_bgcolor=BG2,
          font=dict(color=TXT, family="Segoe UI, sans-serif", size=11),
          margin=dict(t=20,b=30,l=10,r=10))

FILL_NEG = "rgba(153,27,27,0.15)"
FILL_NEU = "rgba(146,64,14,0.15)"
FILL_POS = "rgba(22,101,52,0.15)"

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    col_logo, col_btn = st.columns([2,1])
    with col_logo:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
            width=90)
    with col_btn:
        lang = st.session_state.lang
        if st.button("🇩🇪 DE" if lang=="en" else "🇬🇧 EN"):
            st.session_state.lang = "de" if lang=="en" else "en"
            st.rerun()

    lang = st.session_state.lang
    st.markdown("---")

    alle_laender = (df.groupby("land_name")["land_name"]
        .count().sort_values(ascending=False).index.tolist())

    if lang == "en":
        pos_lbl, neu_lbl, neg_lbl = "Positive", "Neutral", "Negative"
        st.markdown("**Sentiment**")
        sopts = {"Positive":"positiv","Neutral":"neutral","Negative":"negativ"}
        st.markdown("**Countries**")
        st.markdown("**Year Range**")
        st.markdown("**Model Certainty**")
        st.caption("Min. AI confidence in its classification")
        abw_lbl = "Discrepancies only"
    else:
        pos_lbl, neu_lbl, neg_lbl = "Positiv", "Neutral", "Negativ"
        st.markdown("**Stimmung**")
        sopts = {"Positiv":"positiv","Neutral":"neutral","Negativ":"negativ"}
        st.markdown("**Länder**")
        st.markdown("**Zeitraum**")
        st.markdown("**Modell-Sicherheit**")
        st.caption("Wie sicher war die KI?")
        abw_lbl = "Nur Abweichungen"

    filt_s_labels = st.multiselect(
        "", list(sopts.keys()), default=list(sopts.keys()),
        label_visibility="collapsed", key="fs")
    filt_sv = [sopts[s] for s in filt_s_labels]

    filt_l = st.multiselect(
        "", alle_laender, default=alle_laender[:8],
        label_visibility="collapsed", key="fl")

    min_j, max_j = int(df["jahr"].min()), int(df["jahr"].max())
    yr = st.slider("", min_j, max_j, (2018, max_j),
                   label_visibility="collapsed", key="yr")

    min_k = st.slider("", 0.0, 1.0, 0.0, 0.1,
                      label_visibility="collapsed", key="mk")

    nur_abw = st.checkbox(abw_lbl)
    st.markdown("---")
    st.caption("Aug 2007 – Sep 2024 · RoBERTa · Kaggle")

# ── Filter ───────────────────────────────────────────────────────────────────
d = df.copy()
if filt_sv: d = d[d["text_sentiment"].isin(filt_sv)]
if filt_l:  d = d[d["land_name"].isin(filt_l)]
d = d[d["jahr"].between(yr[0], yr[1])]
d = d[d["text_sentiment_score"] >= min_k]
if nur_abw: d = d[d["uebereinstimmung"]==0]
n = len(d)

# Vorperiode
span = yr[1] - yr[0] + 1
d_vor = df.copy()
if filt_sv: d_vor = d_vor[d_vor["text_sentiment"].isin(filt_sv)]
if filt_l:  d_vor = d_vor[d_vor["land_name"].isin(filt_l)]
d_vor = d_vor[d_vor["jahr"].between(yr[0]-span, yr[0]-1)]
n_vor = len(d_vor)

# Sentiment-Labels
lm = {"positiv": pos_lbl, "neutral": neu_lbl, "negativ": neg_lbl}

if n == 0:
    st.warning("No data for this filter." if lang=="en" else "Keine Daten für diesen Filter.")
    st.stop()

pos_n = int((d["text_sentiment"]=="positiv").sum())
neu_n = int((d["text_sentiment"]=="neutral").sum())
neg_n = int((d["text_sentiment"]=="negativ").sum())
abw_n = int((d["uebereinstimmung"]==0).sum())
avg_k = d["text_sentiment_score"].mean()
avg_r = d["rating"].mean()

pos_v = int((d_vor["text_sentiment"]=="positiv").sum()) if n_vor else None
neg_v = int((d_vor["text_sentiment"]=="negativ").sum()) if n_vor else None

def dlt(c, p):
    if not p or p == 0: return None
    diff = c - p
    s = "+" if diff >= 0 else ""
    return f"{s}{diff:,} ({s}{diff/p*100:.1f}%) {'vs prior' if lang=='en' else 'vs. Vorperiode'}"

# ── Header ────────────────────────────────────────────────────────────────────
ttl = "Reviews  Sentiment Analytics" if lang=="en" else "Bewertungen  Sentiment-Analyse"
rev_n = f"{n:,} {'reviews' if lang=='en' else 'Bewertungen'}"
st.markdown(f"## 📦 Amazon {ttl}")
st.caption(f"RoBERTa Transformer · Kaggle Dataset · {rev_n}")
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5,k6 = st.columns(6)
kpi_args = [
    (k1, f"{n:,}",       "Total Reviews" if lang=="en" else "Bewertungen",       dlt(n, n_vor)),
    (k2, f"{avg_r:.2f}", "Avg. Rating"   if lang=="en" else "Ø Sternebewertung", None),
    (k3, f"{pos_n:,}",   pos_lbl,                                                f"{pos_n/n*100:.1f}%"),
    (k4, f"{neu_n:,}",   neu_lbl,                                                f"{neu_n/n*100:.1f}%"),
    (k5, f"{neg_n:,}",   neg_lbl,                                                f"{neg_n/n*100:.1f}%"),
    (k6, f"{abw_n:,}",   "Discrepancies" if lang=="en" else "Abweichungen",     "text ≠ stars" if lang=="en" else "Text ≠ Sterne"),
]
for col, val, lbl, delta in kpi_args:
    col.metric(lbl, val, delta)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
if lang == "en":
    tabs = st.tabs(["Overview","Time Series","Countries","Reviews"])
else:
    tabs = st.tabs(["Übersicht","Zeitverlauf","Länder","Bewertungen"])

tab0, tab1, tab2, tab3 = tabs

# ══════════════════════════════════════════════════════════
# TAB 0: OVERVIEW
# ══════════════════════════════════════════════════════════
with tab0:
    cnt = d["text_sentiment"].value_counts().reset_index()
    cnt.columns = ["s","n"]
    cnt["label"] = cnt["s"].map(lm)

    fig_pie = go.Figure(go.Pie(
        values=cnt["n"], labels=cnt["label"], hole=0.62,
        marker=dict(
            colors=[{"positiv":"#22c55e","neutral":"#f59e0b",
                     "negativ":"#f87171"}.get(x,"#888") for x in cnt["s"]],
            line=dict(color="white", width=3)),
        textinfo="percent+label", textfont=dict(size=11,color=TXT),
        hovertemplate="<b>%{label}</b><br>%{value:,} · %{percent}<extra></extra>"))
    fig_pie.update_layout(**LB, height=300,
        legend=dict(orientation="h",y=-0.12,x=0.5,xanchor="center"),
        annotations=[dict(text=f"<b>{n:,}</b>",x=0.5,y=0.5,
            showarrow=False,font=dict(size=18,color=TXT))])

    vgl = d.groupby(["rating","text_sentiment"]).size().reset_index(name="n")
    vgl = vgl.dropna(subset=["rating"])
    vgl["r"] = vgl["rating"].astype(int).astype(str)+" ★"
    vgl["S"] = vgl["text_sentiment"].map(lm)
    fig_vgl = go.Figure()
    for s,c in [(neg_lbl,NEG),(neu_lbl,NEU),(pos_lbl,POS)]:
        sub = vgl[vgl["S"]==s]
        fig_vgl.add_trace(go.Bar(name=s, x=sub["r"], y=sub["n"], marker_color=c,
            hovertemplate=f"<b>%{{x}}</b><br>{s}: %{{y:,}}<extra></extra>"))
    fig_vgl.update_layout(**LB, barmode="group", height=300,
        legend=dict(orientation="h",y=1.06,x=1,xanchor="right"),
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True,gridcolor=BRD))

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
        title={"text":"Avg. Model Certainty" if lang=="en" else "Ø Modell-Sicherheit",
               "font":{"color":TXT2,"size":11}}))
    fig_g.update_layout(**LB, height=300)

    zt = d.dropna(subset=["review_datum"]).copy()
    zt["monat"] = zt["review_datum"].dt.to_period("M").astype(str)
    agg = zt.groupby(["monat","text_sentiment"]).size().reset_index(name="n")
    agg["S"] = agg["text_sentiment"].map(lm)
    fig_tr = go.Figure()
    fills = {pos_lbl:FILL_POS, neu_lbl:FILL_NEU, neg_lbl:FILL_NEG}
    for s,c in [(neg_lbl,NEG),(neu_lbl,NEU),(pos_lbl,POS)]:
        sub = agg[agg["S"]==s]
        fig_tr.add_trace(go.Scatter(x=sub["monat"],y=sub["n"],name=s,
            mode="lines",stackgroup="one",line=dict(color=c,width=1.5),
            fillcolor=fills.get(s,FILL_NEG)))
    fig_tr.update_layout(**LB, height=220, hovermode="x unified", showlegend=False,
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True,gridcolor=BRD))

    h_sd = "Sentiment Distribution" if lang=="en" else "Stimmungs-Verteilung"
    h_vg = "Star Rating vs. Text Sentiment" if lang=="en" else "Sterne vs. Text-Stimmung"
    h_ce = "Model Certainty" if lang=="en" else "Modell-Sicherheit"
    h_tr = "Monthly Sentiment Trend" if lang=="en" else "Monatlicher Stimmungs-Trend"

    c1,c2,c3 = st.columns([1.2,1.2,0.6])
    with c1:
        st.subheader(h_sd)
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar":False})
    with c2:
        st.subheader(h_vg)
        st.plotly_chart(fig_vgl, use_container_width=True, config={"displayModeBar":False})
    with c3:
        st.subheader(h_ce)
        st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar":False})

    st.subheader(h_tr)
    st.plotly_chart(fig_tr, use_container_width=True, config={"displayModeBar":False})

# ══════════════════════════════════════════════════════════
# TAB 1: TIME SERIES
# ══════════════════════════════════════════════════════════
with tab1:
    zt = d.dropna(subset=["review_datum"]).copy()
    zt["monat"] = zt["review_datum"].dt.to_period("M").astype(str)
    agg = zt.groupby(["monat","text_sentiment"]).size().reset_index(name="n")
    agg["S"] = agg["text_sentiment"].map(lm)
    fills = {pos_lbl:FILL_POS, neu_lbl:FILL_NEU, neg_lbl:FILL_NEG}

    fig_area = go.Figure()
    for s,c in [(neg_lbl,NEG),(neu_lbl,NEU),(pos_lbl,POS)]:
        sub = agg[agg["S"]==s]
        fig_area.add_trace(go.Scatter(x=sub["monat"],y=sub["n"],name=s,
            mode="lines",stackgroup="one",line=dict(color=c,width=1.5),
            fillcolor=fills.get(s,FILL_NEG)))
    fig_area.update_layout(**LB, height=300, hovermode="x unified",
        legend=dict(orientation="h",y=1.06,x=1,xanchor="right"),
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True,gridcolor=BRD))

    jhr = zt.groupby("jahr").agg(
        total=("text_sentiment","count"),
        neg=("text_sentiment",lambda x:(x=="negativ").sum()),
        avg_r=("rating","mean")).reset_index()
    jhr["neg_pct"] = (jhr["neg"]/jhr["total"]*100).round(1)
    jhr["avg_r"]   = jhr["avg_r"].round(2)

    bar_c = [NEG if p>70 else NEU if p>50 else POS for p in jhr["neg_pct"]]
    fig_nj = go.Figure(go.Bar(x=jhr["jahr"], y=jhr["neg_pct"], marker_color=bar_c,
        text=jhr["neg_pct"].apply(lambda x:f"{x:.0f}%"),
        textposition="outside", textfont=dict(color=TXT,size=10)))
    fig_nj.update_layout(**LB, height=280,
        yaxis=dict(range=[0,105],ticksuffix="%",showgrid=True,gridcolor=BRD),
        xaxis=dict(showgrid=False))

    fig_rj = go.Figure()
    fig_rj.add_trace(go.Scatter(x=jhr["jahr"],y=jhr["avg_r"],mode="lines+markers",
        line=dict(color=ACC,width=2),
        marker=dict(size=6,color=ACC,line=dict(color="white",width=2)),
        fill="tozeroy",fillcolor="rgba(30,64,175,0.07)"))
    fig_rj.add_hline(y=jhr["avg_r"].mean(),line_dash="dot",
        line_color=TXT3,line_width=1,
        annotation_text=f"Ø {jhr['avg_r'].mean():.2f}",
        annotation_font=dict(color=TXT3,size=10))
    fig_rj.update_layout(**LB, height=280,
        yaxis=dict(range=[1,5.3],tickvals=[1,2,3,4,5],
                   showgrid=True,gridcolor=BRD),
        xaxis=dict(showgrid=False))

    h_a = "Monthly Sentiment Volume" if lang=="en" else "Monatliches Bewertungsvolumen"
    h_n = "Negative Share by Year" if lang=="en" else "Negativanteil pro Jahr"
    h_r = "Avg. Star Rating by Year" if lang=="en" else "Ø Sternebewertung pro Jahr"

    st.subheader(h_a)
    st.plotly_chart(fig_area, use_container_width=True, config={"displayModeBar":False})
    c1,c2 = st.columns(2)
    with c1:
        st.subheader(h_n)
        st.plotly_chart(fig_nj, use_container_width=True, config={"displayModeBar":False})
    with c2:
        st.subheader(h_r)
        st.plotly_chart(fig_rj, use_container_width=True, config={"displayModeBar":False})

# ══════════════════════════════════════════════════════════
# TAB 2: COUNTRIES
# ══════════════════════════════════════════════════════════
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

    pct_lbl = "% Negative" if lang=="en" else "% Negativ"
    rv_lbl  = "Reviews" if lang=="en" else "Bewertungen"

    la_map = la[la["count"]>=3].copy()
    fig_k = go.Figure(go.Choropleth(
        locations=la_map["plotly_name"], locationmode="country names",
        z=la_map["neg_pct"],
        colorscale=[[0,"#bbf7d0"],[0.4,"#fef9c3"],[0.75,"#fecaca"],[1,"#991b1b"]],
        zmin=0, zmax=100, text=la_map["land_name"],
        customdata=la_map[["count","avg_r","pos_pct","neg_pct"]].values,
        hovertemplate=(
            "<b>%{text}</b><br>"
            f"{rv_lbl}: %{{customdata[0]:,}}<br>"
            f"Ø ★: %{{customdata[1]:.2f}}<br>"
            f"{neg_lbl}: %{{customdata[3]:.1f}}%<extra></extra>"),
        colorbar=dict(title=dict(text=pct_lbl,font=dict(size=10,color=TXT2)),
            tickfont=dict(size=9,color=TXT2),thickness=12,len=0.65,ticksuffix="%"),
        marker=dict(line=dict(color="white",width=0.4))))
    fig_k.update_layout(paper_bgcolor=BG2,plot_bgcolor=BG2,
        font=dict(color=TXT,family="Segoe UI"),
        margin=dict(t=0,b=0,l=0,r=0),height=400,
        geo=dict(bgcolor=BG2,showframe=False,showcoastlines=True,
            coastlinecolor=BRD,coastlinewidth=0.5,landcolor="#f3f4f6",
            showocean=True,oceancolor="#e0f2fe",showlakes=True,
            lakecolor="#e0f2fe",projection_type="natural earth"))

    la_b = la[la["land_lat"].notna()&(la["count"]>=3)].copy()
    fig_b = go.Figure(go.Scattergeo(
        lat=la_b["land_lat"],lon=la_b["land_lon"],text=la_b["land_name"],
        customdata=la_b[["count","neg_pct","avg_r"]].values,mode="markers",
        marker=dict(
            size=la_b["count"].apply(lambda x:max(4,min(40,x/80))),
            color=la_b["neg_pct"],
            colorscale=[[0,"#bbf7d0"],[0.5,"#fef9c3"],[1,"#991b1b"]],
            cmin=0,cmax=100,line=dict(color="white",width=0.5),opacity=0.85,
            colorbar=dict(title=dict(text=pct_lbl,font=dict(size=10,color=TXT2)),
                tickfont=dict(size=9,color=TXT2),thickness=12,len=0.6,ticksuffix="%")),
        hovertemplate=(
            "<b>%{text}</b><br>"
            f"{rv_lbl}: %{{customdata[0]:,}}<br>"
            f"{neg_lbl}: %{{customdata[1]:.1f}}%<extra></extra>")))
    fig_b.update_layout(paper_bgcolor=BG2,plot_bgcolor=BG2,
        font=dict(color=TXT,family="Segoe UI"),
        margin=dict(t=0,b=0,l=0,r=0),height=380,
        geo=dict(bgcolor=BG2,showframe=False,showcoastlines=True,
            coastlinecolor=BRD,landcolor="#f3f4f6",showocean=True,
            oceancolor="#e0f2fe",projection_type="natural earth"))

    top15 = la[la["count"]>=10].nlargest(15,"count")
    fig_bar = go.Figure()
    for s,lbl,c in [("neg",neg_lbl,NEG),("neu",neu_lbl,NEU),("pos",pos_lbl,POS)]:
        fig_bar.add_trace(go.Bar(name=lbl,x=top15["land_name"],y=top15[s],
            marker_color=c))
    fig_bar.update_layout(**LB,barmode="stack",height=320,
        legend=dict(orientation="h",y=1.06,x=1,xanchor="right"),
        xaxis=dict(tickangle=-30,showgrid=False,tickfont=dict(size=9)),
        yaxis=dict(showgrid=True,gridcolor=BRD))

    h_ch = "Negative Sentiment Heatmap" if lang=="en" else "Negativanteil nach Land"
    h_bu = "Review Volume by Location" if lang=="en" else "Bewertungsvolumen nach Standort"
    h_b15 = "Top 15 Countries — Sentiment Breakdown" if lang=="en" else "Top 15 Länder – Stimmungsaufschlüsselung"

    c1,c2 = st.columns(2)
    with c1:
        st.subheader(h_ch)
        st.plotly_chart(fig_k, use_container_width=True, config={"displayModeBar":False})
    with c2:
        st.subheader(h_bu)
        st.plotly_chart(fig_b, use_container_width=True, config={"displayModeBar":False})
    st.subheader(h_b15)
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar":False})

# ══════════════════════════════════════════════════════════
# TAB 3: REVIEWS
# ══════════════════════════════════════════════════════════
with tab3:
    def wfig(sentiment, color, title):
        top = top_w(d[d["text_sentiment"]==sentiment]["review_text"], 12)
        if not top: return go.Figure().update_layout(**LB,height=360)
        wdf = pd.DataFrame(top, columns=["word","n"])
        fig = go.Figure(go.Bar(
            x=wdf["n"], y=wdf["word"], orientation="h",
            marker=dict(color=wdf["n"],colorscale=[[0,BG3],[1,color]],
                line=dict(color=BRD,width=0.5)),
            text=wdf["n"], textposition="outside",
            textfont=dict(color=TXT2,size=10),
            hovertemplate="<b>%{y}</b>: %{x:,}<extra></extra>"))
        fig.update_layout(**LB, height=400,
            title=dict(text=title,font=dict(size=12,color=TXT)),
            yaxis=dict(autorange="reversed"),
            xaxis=dict(showgrid=True,gridcolor=BRD))
        return fig

    h_wn = "Most Frequent Words — Negative Reviews" if lang=="en" else "Häufigste Wörter – Negative Bewertungen"
    h_wp = "Most Frequent Words — Positive Reviews" if lang=="en" else "Häufigste Wörter – Positive Bewertungen"
    h_aw = "Discrepancies — Text Sentiment vs. Star Rating" if lang=="en" else "Abweichungen – Text-Stimmung vs. Sterne-Bewertung"
    h_br = "Review Browser" if lang=="en" else "Bewertungs-Browser"
    s_lbl = "Search in review text" if lang=="en" else "Suchbegriff im Bewertungstext"

    c1,c2 = st.columns(2)
    with c1:
        st.plotly_chart(wfig("negativ",NEG,h_wn), use_container_width=True,
                        config={"displayModeBar":False})
    with c2:
        st.plotly_chart(wfig("positiv",POS,h_wp), use_container_width=True,
                        config={"displayModeBar":False})

    st.subheader(h_aw)
    if lang=="en":
        st.caption("Reviews where the AI model contradicts the star rating — sorted by confidence")
    else:
        st.caption("Bewertungen wo das Modell anders urteilt als die Sterne – sortiert nach Konfidenz")

    abw = d[d["uebereinstimmung"]==0].sort_values("text_sentiment_score",ascending=False)
    abw_s = abw[["land_name","rating","rating_sentiment","text_sentiment",
                 "text_sentiment_score","review_text"]].head(100).copy()
    abw_s["rating_sentiment"] = abw_s["rating_sentiment"].map(lm).fillna(abw_s["rating_sentiment"])
    abw_s["text_sentiment"]   = abw_s["text_sentiment"].map(lm).fillna(abw_s["text_sentiment"])
    if lang=="en":
        abw_s.columns = ["Country","Stars","Rating Label","Sentiment","Confidence","Review Text"]
    else:
        abw_s.columns = ["Land","Sterne","Sterne-Label","Stimmung","Konfidenz","Bewertungstext"]
    st.dataframe(abw_s, use_container_width=True, height=320)

    st.subheader(h_br)
    suche = st.text_input(s_lbl, placeholder="e.g. refund, broken, excellent...")
    br = d.copy()
    if suche:
        br = br[br["review_text"].str.contains(suche, case=False, na=False)]
    br_s = br[["review_datum","land_name","rating","text_sentiment",
               "text_sentiment_score","review_text"]].head(300).copy()
    br_s["text_sentiment"] = br_s["text_sentiment"].map(lm).fillna(br_s["text_sentiment"])
    if lang=="en":
        br_s.columns = ["Date","Country","Stars","Sentiment","Confidence","Review Text"]
    else:
        br_s.columns = ["Datum","Land","Sterne","Stimmung","Konfidenz","Bewertungstext"]
    st.dataframe(br_s, use_container_width=True, height=400)
    st.caption(f"{len(br):,} {'reviews' if lang=='en' else 'Bewertungen'} · max. 300")

st.divider()
st.caption("Amazon Reviews Sentiment Dashboard · RoBERTa · Streamlit + Plotly")
