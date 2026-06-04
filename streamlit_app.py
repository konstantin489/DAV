# =============================================================================
# AMAZON REVIEWS – SENTIMENT DASHBOARD (STREAMLIT)
# Öffentlich erreichbar über Streamlit Community Cloud
#
# LOKAL STARTEN:
#   pip install streamlit plotly pandas
#   streamlit run streamlit_app.py
#
# ÖFFENTLICH (kostenlos):
#   → Anleitung am Ende dieser Datei
# =============================================================================

import streamlit as st
import pandas as pd
import sqlite3
import re
import os
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter

# ── Seiten-Konfiguration ────────────────────────────────────────────────────
st.set_page_config(
    page_title = "Amazon Bewertungen – Sentiment",
    page_icon  = "📦",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .block-container { padding-top: 1.5rem; }
    h1 { font-size: 1.6rem !important; font-weight: 800 !important; }
    h2 { font-size: 1.1rem !important; font-weight: 700 !important;
         color: #1d4ed8 !important; }
    .metric-card {
        background: white; border-radius: 8px; padding: 16px 18px;
        border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="metric-container"] {
        background: white; border: 1px solid #e2e8f0;
        border-radius: 8px; padding: 14px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

# ── Daten laden (gecacht) ───────────────────────────────────────────────────
@st.cache_data
def lade_daten():
    # Datenbank im selben Ordner suchen
    db_pfad = os.path.join(os.path.dirname(__file__), "amazon_reviews.db")
    if not os.path.exists(db_pfad):
        st.error("amazon_reviews.db nicht gefunden! "
                 "Lege die Datei in denselben Ordner wie streamlit_app.py")
        st.stop()
    conn = sqlite3.connect(db_pfad)
    df   = pd.read_sql("SELECT * FROM reviews WHERE review_text IS NOT NULL", conn)
    conn.close()
    df["review_datum"] = pd.to_datetime(df["review_datum"], errors="coerce")
    df["jahr"]         = df["review_datum"].dt.year

    LAND_NAMEN = {
        "US":"USA","GB":"Großbritannien","CA":"Kanada","IN":"Indien",
        "IE":"Irland","DK":"Dänemark","NL":"Niederlande","AU":"Australien",
        "DE":"Deutschland","IT":"Italien","FR":"Frankreich","SE":"Schweden",
        "ES":"Spanien","AE":"Ver. Arab. Emirate","SG":"Singapur",
        "NO":"Norwegen","AT":"Österreich","BE":"Belgien","CH":"Schweiz",
        "PL":"Polen","PT":"Portugal","JP":"Japan","FI":"Finnland",
        "MX":"Mexiko","BR":"Brasilien","GR":"Griechenland","NZ":"Neuseeland",
        "ZA":"Südafrika","RU":"Russland","TR":"Türkei","PH":"Philippinen",
        "MY":"Malaysia","KR":"Südkorea","IL":"Israel","NG":"Nigeria",
        "PK":"Pakistan","SA":"Saudi-Arabien","EG":"Ägypten","MA":"Marokko",
        "TH":"Thailand","AR":"Argentinien","CO":"Kolumbien",
    }
    COORDS = {
        "US":(37.09,-95.71),"GB":(55.37,-3.44),"CA":(56.13,-106.35),
        "IN":(20.59,78.96),"IE":(53.41,-8.24),"DK":(56.26,9.50),
        "NL":(52.13,5.29),"AU":(-25.27,133.77),"DE":(51.17,10.45),
        "IT":(41.87,12.57),"FR":(46.23,2.21),"SE":(60.13,18.64),
        "ES":(40.46,-3.75),"AE":(23.42,53.85),"SG":(1.35,103.82),
        "NO":(60.47,8.47),"AT":(47.52,14.55),"BE":(50.50,4.47),
        "CH":(46.82,8.23),"PL":(51.92,19.15),"PT":(39.40,-8.22),
        "JP":(36.20,138.25),"FI":(61.92,25.75),"MX":(23.63,-102.55),
        "BR":(-14.24,-51.93),"GR":(39.07,21.82),"NZ":(-40.90,174.89),
        "ZA":(-30.56,22.94),"RU":(61.52,105.32),"TR":(38.96,35.24),
        "PH":(12.88,121.77),"MY":(4.21,101.98),"KR":(35.91,127.77),
        "IL":(31.05,34.85),"NG":(9.08,8.68),"PK":(30.38,69.35),
        "SA":(23.89,45.08),"EG":(26.82,30.80),"MA":(31.79,-7.09),
        "TH":(15.87,100.99),"AR":(-38.42,-63.62),"CO":(4.57,-74.30),
    }
    df["land_name"] = df["land"].map(LAND_NAMEN).fillna(df["land"])
    df["land_lat"]  = df["land"].map(lambda x: COORDS.get(x,(None,None))[0])
    df["land_lon"]  = df["land"].map(lambda x: COORDS.get(x,(None,None))[1])
    return df

df = lade_daten()

LMAP   = {"positiv":"Positiv","neutral":"Neutral","negativ":"Negativ"}
FARBEN = {"Positiv":"#16a34a","Neutral":"#d97706","Negativ":"#dc2626"}
FILL   = {"Negativ":"rgba(153,27,27,0.2)",
          "Neutral":"rgba(146,64,14,0.2)",
          "Positiv":"rgba(22,101,52,0.2)"}
LB = dict(paper_bgcolor="white", plot_bgcolor="white",
          font=dict(color="#111827", family="Segoe UI, sans-serif", size=11),
          margin=dict(t=20,b=30,l=10,r=10))

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

# ── Sidebar / Filter ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📦 Amazon Reviews")
    st.caption("Sentiment-Analyse · RoBERTa Transformer")
    st.markdown("---")

    st.markdown("**Stimmung**")
    filter_sentiment = st.multiselect(
        label="",
        options=["positiv","neutral","negativ"],
        default=["positiv","neutral","negativ"],
        format_func=lambda x: LMAP[x],
        label_visibility="collapsed",
    )

    alle_laender = (df.groupby("land_name")["land_name"]
        .count().sort_values(ascending=False).index.tolist())
    st.markdown("**Länder**")
    filter_laender = st.multiselect(
        label="",
        options=alle_laender,
        default=alle_laender[:8],
        label_visibility="collapsed",
    )

    st.markdown("**Zeitraum**")
    min_j = int(df["jahr"].min())
    max_j = int(df["jahr"].max())
    jahr_range = st.slider("", min_j, max_j, (2018, max_j),
                           label_visibility="collapsed")

    st.markdown("**Modell-Sicherheit**")
    st.caption("Wie sicher war die KI bei der Einschätzung?")
    min_k = st.slider("Min. Konfidenz", 0.0, 1.0, 0.0, 0.05,
                      label_visibility="collapsed")

    nur_abw = st.checkbox("Nur Abweichungen (Text ≠ Sterne)")

    st.markdown("---")
    st.caption("21.214 Bewertungen · Aug. 2007 – Sep. 2024")

# ── Filtern ──────────────────────────────────────────────────────────────────
d = df.copy()
if filter_sentiment: d = d[d["text_sentiment"].isin(filter_sentiment)]
if filter_laender:   d = d[d["land_name"].isin(filter_laender)]
d = d[d["jahr"].between(jahr_range[0], jahr_range[1])]
d = d[d["text_sentiment_score"] >= min_k]
if nur_abw:          d = d[d["uebereinstimmung"]==0]

n     = len(d)
pos_n = int((d["text_sentiment"]=="positiv").sum())
neu_n = int((d["text_sentiment"]=="neutral").sum())
neg_n = int((d["text_sentiment"]=="negativ").sum())
abw_n = int((d["uebereinstimmung"]==0).sum())
avg_k = d["text_sentiment_score"].mean()
avg_r = d["rating"].mean()

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("# 📦 Amazon Bewertungen – Sentiment-Analyse")
st.caption("RoBERTa Transformer-Modell · Kaggle-Datensatz · "
           f"{n:,} Bewertungen im aktuellen Filter")
st.markdown("---")

# ── KPI-Karten ───────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("Bewertungen",   f"{n:,}")
k2.metric("Ø Sterne",      f"{avg_r:.2f}")
k3.metric("Positiv",       f"{pos_n:,}", f"{pos_n/n*100:.1f}%" if n else "")
k4.metric("Neutral",       f"{neu_n:,}", f"{neu_n/n*100:.1f}%" if n else "")
k5.metric("Negativ",       f"{neg_n:,}", f"{neg_n/n*100:.1f}%" if n else "")
k6.metric("Abweichungen",  f"{abw_n:,}", "Text ≠ Sterne")

st.markdown("---")

# ── TABS ─────────────────────────────────────────────────────────────────────
tab0, tab1, tab2, tab3 = st.tabs([
    "Übersicht", "Zeitverlauf", "Länder", "Bewertungen"
])

# ═══════════════════════════════════════════════════════
# TAB 0: ÜBERSICHT
# ═══════════════════════════════════════════════════════
with tab0:
    col1, col2 = st.columns([1.3, 0.7])

    with col1:
        st.markdown("## Stimmungs-Verteilung")
        st.caption("Ergebnis des KI-Modells – basiert auf Textinhalt, nicht Sternen")
        cnt = d["text_sentiment"].value_counts().reset_index()
        cnt.columns = ["s","n"]
        cnt["label"] = cnt["s"].map(LMAP)
        fig = go.Figure(go.Pie(
            values=cnt["n"], labels=cnt["label"], hole=0.58,
            marker=dict(
                colors=[{"positiv":"#22c55e","neutral":"#f59e0b",
                         "negativ":"#f87171"}.get(x,"#888") for x in cnt["s"]],
                line=dict(color="white",width=3)),
            textinfo="percent+label",
            textfont=dict(size=12,color="#111827"),
        ))
        fig.update_layout(**LB, height=300,
            annotations=[dict(text=f"<b>{n:,}</b>",x=0.5,y=0.5,
                showarrow=False,font=dict(size=18,color="#111827"))])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("## Modell-Sicherheit")
        st.caption("Ø Konfidenz des RoBERTa-Modells")
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number", value=avg_k*100,
            number={"suffix":"%","font":{"size":28,"color":"#111827"}},
            gauge={"axis":{"range":[0,100]},
                   "bar":{"color":"#1d4ed8","thickness":0.5},
                   "bgcolor":"#f1f5f9","bordercolor":"#e2e8f0",
                   "steps":[{"range":[0,60],"color":"#fee2e2"},
                             {"range":[60,80],"color":"#fef9c3"},
                             {"range":[80,100],"color":"#dcfce7"}]},
            title={"text":"","font":{"size":12}}))
        fig_g.update_layout(**LB, height=300)
        st.plotly_chart(fig_g, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("## Sterne vs. Text-Stimmung")
        st.caption("Wie oft stimmt das Modell mit den Sternen überein?")
        vgl = d.groupby(["rating","text_sentiment"]).size().reset_index(name="n")
        vgl = vgl.dropna(subset=["rating"])
        vgl["rating"] = vgl["rating"].astype(int).astype(str)+" ★"
        vgl["Stimmung"] = vgl["text_sentiment"].map(LMAP)
        fig_v = go.Figure()
        for sent,c in [("Negativ","#dc2626"),("Neutral","#d97706"),("Positiv","#16a34a")]:
            sub = vgl[vgl["Stimmung"]==sent]
            fig_v.add_trace(go.Bar(name=sent,x=sub["rating"],y=sub["n"],marker_color=c))
        fig_v.update_layout(**LB,barmode="group",height=300,
            legend=dict(orientation="h",y=1.05),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
        st.plotly_chart(fig_v, use_container_width=True)

    with col4:
        st.markdown("## Abweichungen nach Land")
        st.caption("Länder mit höchstem Text-Rating-Widerspruch")
        abw_l = d[d["uebereinstimmung"]==0].groupby("land_name").size().reset_index(name="abw")
        tot_l = d.groupby("land_name").size().reset_index(name="total")
        abw_l = abw_l.merge(tot_l, on="land_name")
        abw_l["pct"] = (abw_l["abw"]/abw_l["total"]*100).round(1)
        abw_l = abw_l[abw_l["total"]>=20].nlargest(10,"pct")
        fig_a = px.bar(abw_l,x="pct",y="land_name",orientation="h",
            color="pct",
            color_continuous_scale=[[0,"#dcfce7"],[0.5,"#fef9c3"],[1,"#fee2e2"]],
            text=abw_l["pct"].apply(lambda x:f"{x:.1f}%"))
        fig_a.update_traces(textposition="outside",textfont=dict(color="#111827"))
        fig_a.update_layout(**LB,height=300,coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
            xaxis=dict(showgrid=True,gridcolor="#f1f5f9",ticksuffix="%"))
        st.plotly_chart(fig_a, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB 1: ZEITVERLAUF
# ═══════════════════════════════════════════════════════
with tab1:
    zt = d.dropna(subset=["review_datum"]).copy()
    zt["monat"] = zt["review_datum"].dt.to_period("M").astype(str)
    agg = zt.groupby(["monat","text_sentiment"]).size().reset_index(name="n")
    agg["Stimmung"] = agg["text_sentiment"].map(LMAP)

    st.markdown("## Monatliche Stimmungsentwicklung")
    st.caption("Gestapeltes Flächendiagramm – absolute Anzahl Bewertungen pro Monat")
    fig_area = go.Figure()
    for sent,c in [("Negativ","#dc2626"),("Neutral","#d97706"),("Positiv","#16a34a")]:
        sub = agg[agg["Stimmung"]==sent]
        fig_area.add_trace(go.Scatter(
            x=sub["monat"],y=sub["n"],name=sent,mode="lines",
            stackgroup="one",line=dict(color=c,width=1.5),
            fillcolor=FILL[sent]))
    fig_area.update_layout(**LB,height=320,hovermode="x unified",
        legend=dict(orientation="h",y=1.05),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True,gridcolor="#f1f5f9",title="Bewertungen"))
    st.plotly_chart(fig_area, use_container_width=True)

    col1, col2 = st.columns(2)
    jhr = zt.groupby("jahr").agg(
        total=("text_sentiment","count"),
        neg=("text_sentiment",lambda x:(x=="negativ").sum()),
        avg_r=("rating","mean")).reset_index()
    jhr["neg_pct"] = (jhr["neg"]/jhr["total"]*100).round(1)
    jhr["avg_r"]   = jhr["avg_r"].round(2)

    with col1:
        st.markdown("## Negativanteil pro Jahr")
        bar_c=["#dc2626" if p>70 else "#d97706" if p>50 else "#16a34a"
               for p in jhr["neg_pct"]]
        fig_nj = go.Figure(go.Bar(x=jhr["jahr"],y=jhr["neg_pct"],
            marker_color=bar_c,
            text=jhr["neg_pct"].apply(lambda x:f"{x:.0f}%"),
            textposition="outside",textfont=dict(color="#111827",size=10)))
        fig_nj.update_layout(**LB,height=300,
            yaxis=dict(range=[0,105],ticksuffix="%",
                       showgrid=True,gridcolor="#f1f5f9"),
            xaxis=dict(showgrid=False))
        st.plotly_chart(fig_nj, use_container_width=True)

    with col2:
        st.markdown("## Ø Sternebewertung pro Jahr")
        fig_rj = go.Figure()
        fig_rj.add_trace(go.Scatter(x=jhr["jahr"],y=jhr["avg_r"],
            mode="lines+markers",line=dict(color="#1d4ed8",width=2),
            marker=dict(size=6,color="#1d4ed8",line=dict(color="white",width=2)),
            fill="tozeroy",fillcolor="rgba(29,78,216,0.07)"))
        fig_rj.add_hline(y=jhr["avg_r"].mean(),line_dash="dot",
            line_color="#9ca3af",line_width=1,
            annotation_text=f"Ø {jhr['avg_r'].mean():.2f}",
            annotation_font=dict(color="#9ca3af",size=10))
        fig_rj.update_layout(**LB,height=300,
            yaxis=dict(range=[1,5.3],tickvals=[1,2,3,4,5],
                       showgrid=True,gridcolor="#f1f5f9"),
            xaxis=dict(showgrid=False))
        st.plotly_chart(fig_rj, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB 2: LÄNDER
# ═══════════════════════════════════════════════════════
with tab2:
    la = d.groupby(["land","land_name","land_lat","land_lon"]).agg(
        anzahl=("land","count"),
        neg_pct=("text_sentiment",lambda x:round((x=="negativ").mean()*100,1)),
        pos_pct=("text_sentiment",lambda x:round((x=="positiv").mean()*100,1)),
        neu_pct=("text_sentiment",lambda x:round((x=="neutral").mean()*100,1)),
        avg_r=("rating",lambda x:round(x.mean(),2)),
        neg=("text_sentiment",lambda x:(x=="negativ").sum()),
        pos=("text_sentiment",lambda x:(x=="positiv").sum()),
        neu=("text_sentiment",lambda x:(x=="neutral").sum()),
    ).reset_index()

    NAME_PLOTLY = {
        "USA":"United States","Großbritannien":"United Kingdom",
        "Kanada":"Canada","Indien":"India","Irland":"Ireland",
        "Dänemark":"Denmark","Niederlande":"Netherlands",
        "Australien":"Australia","Deutschland":"Germany",
        "Italien":"Italy","Frankreich":"France","Schweden":"Sweden",
        "Spanien":"Spain","Österreich":"Austria","Belgien":"Belgium",
        "Schweiz":"Switzerland","Norwegen":"Norway","Finnland":"Finland",
        "Polen":"Poland","Portugal":"Portugal","Japan":"Japan",
        "Mexiko":"Mexico","Brasilien":"Brazil","Südafrika":"South Africa",
        "Singapur":"Singapore","Russland":"Russia","Türkei":"Turkey",
        "Griechenland":"Greece","Neuseeland":"New Zealand",
        "Philippinen":"Philippines","Malaysia":"Malaysia",
        "Südkorea":"South Korea","Israel":"Israel","Nigeria":"Nigeria",
        "Pakistan":"Pakistan","Saudi-Arabien":"Saudi Arabia",
        "Ägypten":"Egypt","Marokko":"Morocco","Thailand":"Thailand",
        "Argentinien":"Argentina","Kolumbien":"Colombia",
        "Ver. Arab. Emirate":"United Arab Emirates",
    }

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## Negativanteil nach Land (Weltkarte)")
        st.caption("Grün = wenig negativ · Rot = viel negativ · Hover für Details")
        la_map = la[la["anzahl"]>=3].copy()
        la_map["plotly_name"] = la_map["land_name"].map(NAME_PLOTLY).fillna(la_map["land_name"])
        fig_k = go.Figure(go.Choropleth(
            locations=la_map["plotly_name"],
            locationmode="country names",
            z=la_map["neg_pct"],
            colorscale=[[0,"#bbf7d0"],[0.4,"#fef9c3"],[0.75,"#fecaca"],[1,"#991b1b"]],
            zmin=0,zmax=100,
            text=la_map["land_name"],
            customdata=la_map[["anzahl","avg_r","pos_pct","neg_pct"]].values,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Bewertungen: %{customdata[0]:,}<br>"
                "Ø Sterne: %{customdata[1]:.2f}<br>"
                "Positiv: %{customdata[2]:.1f}%<br>"
                "Negativ: %{customdata[3]:.1f}%<extra></extra>"
            ),
            colorbar=dict(title=dict(text="% Negativ",
                font=dict(size=10)),thickness=12,len=0.65,ticksuffix="%"),
            marker=dict(line=dict(color="white",width=0.4)),
        ))
        fig_k.update_layout(paper_bgcolor="white",plot_bgcolor="white",
            font=dict(color="#111827",family="Segoe UI"),
            margin=dict(t=0,b=0,l=0,r=0),height=380,
            geo=dict(bgcolor="white",showframe=False,showcoastlines=True,
                coastlinecolor="#e2e8f0",landcolor="#f3f4f6",
                showocean=True,oceancolor="#e0f2fe",projection_type="natural earth"))
        st.plotly_chart(fig_k, use_container_width=True)

    with col2:
        st.markdown("## Bewertungsvolumen (Bubble-Map)")
        st.caption("Blasengröße = Anzahl Bewertungen · Farbe = Negativanteil")
        la_b = la[la["land_lat"].notna() & (la["anzahl"]>=3)]
        fig_b = go.Figure(go.Scattergeo(
            lat=la_b["land_lat"],lon=la_b["land_lon"],
            text=la_b["land_name"],
            customdata=la_b[["anzahl","neg_pct","avg_r"]].values,
            mode="markers",
            marker=dict(
                size=la_b["anzahl"].apply(lambda x:max(4,min(40,x/80))),
                color=la_b["neg_pct"],
                colorscale=[[0,"#bbf7d0"],[0.5,"#fef9c3"],[1,"#991b1b"]],
                cmin=0,cmax=100,line=dict(color="white",width=0.5),opacity=0.85,
                colorbar=dict(title=dict(text="% Negativ",font=dict(size=10)),
                    thickness=12,len=0.6,ticksuffix="%"),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Bewertungen: %{customdata[0]:,}<br>"
                "Negativ: %{customdata[1]:.1f}%<br>"
                "Ø Sterne: %{customdata[2]:.2f}<extra></extra>"
            ),
        ))
        fig_b.update_layout(paper_bgcolor="white",plot_bgcolor="white",
            font=dict(color="#111827",family="Segoe UI"),
            margin=dict(t=0,b=0,l=0,r=0),height=380,
            geo=dict(bgcolor="white",showframe=False,showcoastlines=True,
                coastlinecolor="#e2e8f0",landcolor="#f3f4f6",
                showocean=True,oceancolor="#e0f2fe",projection_type="natural earth"))
        st.plotly_chart(fig_b, use_container_width=True)

    col3, col4 = st.columns([1.3, 0.7])
    with col3:
        st.markdown("## Top 15 Länder – Stimmungsaufschlüsselung")
        top15 = la[la["anzahl"]>=10].nlargest(15,"anzahl")
        fig_bar = go.Figure()
        for sent,lbl,c in [("neg","Negativ","#dc2626"),
                            ("neu","Neutral","#d97706"),
                            ("pos","Positiv","#16a34a")]:
            fig_bar.add_trace(go.Bar(name=lbl,x=top15["land_name"],
                y=top15[sent],marker_color=c))
        fig_bar.update_layout(**LB,barmode="stack",height=340,
            legend=dict(orientation="h",y=1.05),
            xaxis=dict(tickangle=-30,showgrid=False,tickfont=dict(size=9)),
            yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col4:
        st.markdown("## Ø Sterne vs. Negativanteil")
        sc = la[la["anzahl"]>=15]
        fig_sc = go.Figure(go.Scatter(
            x=sc["avg_r"],y=sc["neg_pct"],mode="markers+text",
            text=sc["land_name"],textposition="top center",
            textfont=dict(size=8,color="#6b7280"),
            marker=dict(size=sc["anzahl"].apply(lambda x:max(6,min(30,x/60))),
                color=sc["neg_pct"],
                colorscale=[[0,"#16a34a"],[0.5,"#d97706"],[1,"#dc2626"]],
                cmin=0,cmax=100,line=dict(color="white",width=1),opacity=0.8),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Ø Sterne: %{x:.2f}<br>"
                "Negativ: %{y:.1f}%<extra></extra>"
            ),
        ))
        fig_sc.add_vline(x=sc["avg_r"].mean(),line_dash="dot",
            line_color="#9ca3af",line_width=1)
        fig_sc.add_hline(y=sc["neg_pct"].mean(),line_dash="dot",
            line_color="#9ca3af",line_width=1)
        fig_sc.update_layout(**LB,height=340,coloraxis_showscale=False,
            xaxis=dict(title="Ø Sternebewertung",range=[1,5.2],
                       showgrid=True,gridcolor="#f1f5f9"),
            yaxis=dict(title="Negativanteil (%)",
                       showgrid=True,gridcolor="#f1f5f9",ticksuffix="%"))
        st.plotly_chart(fig_sc, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB 3: BEWERTUNGEN
# ═══════════════════════════════════════════════════════
with tab3:
    col1, col2 = st.columns(2)

    def wfig(sentiment, farbe, titel):
        top = top_w(d[d["text_sentiment"]==sentiment]["review_text"], 12)
        if not top: return go.Figure().update_layout(**LB,height=360)
        wdf = pd.DataFrame(top,columns=["wort","n"])
        fig = go.Figure(go.Bar(
            x=wdf["n"],y=wdf["wort"],orientation="h",
            marker=dict(color=wdf["n"],
                colorscale=[[0,"#f3f4f6"],[1,farbe]],
                line=dict(color="#e2e8f0",width=0.5)),
            text=wdf["n"],textposition="outside",
            textfont=dict(color="#6b7280",size=10),
        ))
        fig.update_layout(**LB,height=400,
            title=dict(text=titel,font=dict(size=12,color="#111827")),
            yaxis=dict(autorange="reversed"),
            xaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
        return fig

    with col1:
        st.plotly_chart(wfig("negativ","#dc2626","Häufigste Wörter – Negative Bewertungen"),
                        use_container_width=True)
    with col2:
        st.plotly_chart(wfig("positiv","#16a34a","Häufigste Wörter – Positive Bewertungen"),
                        use_container_width=True)

    st.markdown("## Abweichungen: Text-Stimmung ≠ Sterne-Bewertung")
    st.caption("Fälle wo die KI anders urteilt als die Sterne – "
               "sortiert nach Modell-Sicherheit")
    abw = d[d["uebereinstimmung"]==0].sort_values("text_sentiment_score",ascending=False)
    abw_s = abw[["land_name","rating","rating_sentiment","text_sentiment",
                 "text_sentiment_score","review_text"]].head(100).copy()
    abw_s["rating_sentiment"] = abw_s["rating_sentiment"].map(LMAP).fillna(abw_s["rating_sentiment"])
    abw_s["text_sentiment"]   = abw_s["text_sentiment"].map(LMAP).fillna(abw_s["text_sentiment"])
    abw_s.columns = ["Land","Sterne","Sterne-Label","Text-Stimmung",
                     "Konfidenz","Bewertungstext"]
    st.dataframe(abw_s, use_container_width=True, height=350)

    st.markdown("## Bewertungs-Browser")
    suche = st.text_input("Suchbegriff im Bewertungstext", placeholder="z.B. refund, delivery, broken...")
    br = d.copy()
    if suche:
        br = br[br["review_text"].str.contains(suche, case=False, na=False)]
    br_show = br[["review_datum","land_name","rating","text_sentiment",
                  "text_sentiment_score","review_titel","review_text"]].head(300).copy()
    br_show["text_sentiment"] = br_show["text_sentiment"].map(LMAP).fillna(br_show["text_sentiment"])
    br_show.columns = ["Datum","Land","Sterne","Stimmung","Konfidenz","Titel","Bewertungstext"]
    st.dataframe(br_show, use_container_width=True, height=400)
    st.caption(f"{len(br):,} Bewertungen gefunden · Zeige erste 300")

# ══ Footer ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.caption("Amazon Reviews Sentiment Dashboard · "
           "RoBERTa (cardiffnlp/twitter-roberta-base-sentiment-latest) · "
           "Kaggle-Datensatz · Plotly + Streamlit")
