# =============================================================================
# SCRIPT 02 – AMAZON REVIEWS SENTIMENT DASHBOARD
# F5 drücken → Browser → http://127.0.0.1:8050
# =============================================================================
import subprocess, sys, os

def finde_conda():
    basis = sys.executable
    for _ in range(6):
        basis = os.path.dirname(basis)
        for k in [os.path.join(basis,"conda.exe"),
                  os.path.join(basis,"Scripts","conda.exe"),
                  os.path.join(basis,"bin","conda")]:
            if os.path.exists(k): return k
    return None

def installiere(p):
    c = finde_conda()
    if c:
        r = subprocess.run([c,"install","-c","conda-forge",p,"-y","--quiet"],capture_output=True)
        if r.returncode==0: return "conda"
    r = subprocess.run([sys.executable,"-m","pip","install",p,"--quiet"],capture_output=True)
    return "pip" if r.returncode==0 else None

print("Checking packages...")
for p in ["pandas","dash","plotly"]:
    try: __import__(p); print(f"  OK: {p}")
    except ImportError:
        print(f"  Installing {p}...")
        m = installiere(p)
        print(f"  OK via {m}" if m else f"  ERROR: {p}")
print("Ready.\n")

# =============================================================================
DB_PFAD = r"C:\Users\johan\OneDrive\Desktop\DAV\amazon_reviews.db"
# =============================================================================

import pandas as pd, sqlite3, re
from collections import Counter
from datetime import date
from dash import Dash, dcc, html, Input, Output, dash_table, callback_context
import plotly.graph_objects as go
import plotly.express as px

print("Loading data...")
conn = sqlite3.connect(DB_PFAD)
df   = pd.read_sql("SELECT * FROM reviews WHERE review_text IS NOT NULL", conn)
conn.close()
df["review_datum"] = pd.to_datetime(df["review_datum"], errors="coerce")
df["jahr"]         = df["review_datum"].dt.year
df["monat_num"]    = df["review_datum"].dt.to_period("M")
print(f"{len(df):,} reviews loaded.\n")

# Country mappings
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
    "DO":"Dominican Republic","PR":"Puerto Rico","LU":"Luxembourg",
    "LB":"Lebanon","JO":"Jordan","OM":"Oman","LK":"Sri Lanka",
    "TT":"Trinidad and Tobago","KE":"Kenya","GH":"Ghana","CM":"Cameroon",
    "TZ":"Tanzania","ET":"Ethiopia","UG":"Uganda","MU":"Mauritius",
    "BW":"Botswana","BB":"Barbados","MN":"Mongolia","NP":"Nepal",
    "MM":"Myanmar","KH":"Cambodia","DZ":"Algeria","TN":"Tunisia",
    "JE":"Jersey","GG":"Guernsey","IM":"Isle of Man","IS":"Iceland",
}

# Plotly v6 needs full country names for choropleth
NAME_ZU_PLOTLY = {
    "United States":"United States","United Kingdom":"United Kingdom",
    "Canada":"Canada","India":"India","Ireland":"Ireland","Denmark":"Denmark",
    "Netherlands":"Netherlands","Australia":"Australia","Germany":"Germany",
    "Italy":"Italy","France":"France","Sweden":"Sweden","Spain":"Spain",
    "United Arab Emirates":"United Arab Emirates","Pakistan":"Pakistan",
    "Israel":"Israel","New Zealand":"New Zealand","Belgium":"Belgium",
    "South Africa":"South Africa","Philippines":"Philippines","Singapore":"Singapore",
    "Russia":"Russia","Norway":"Norway","Turkey":"Turkey","Poland":"Poland",
    "Portugal":"Portugal","Ukraine":"Ukraine","Hong Kong":"Hong Kong",
    "Switzerland":"Switzerland","Greece":"Greece","Japan":"Japan",
    "Austria":"Austria","Romania":"Romania","Nigeria":"Nigeria","Mexico":"Mexico",
    "Finland":"Finland","Egypt":"Egypt","Czech Republic":"Czechia",
    "Indonesia":"Indonesia","Brazil":"Brazil","Argentina":"Argentina",
    "Vietnam":"Vietnam","Thailand":"Thailand","Saudi Arabia":"Saudi Arabia",
    "Serbia":"Serbia","Malaysia":"Malaysia","Morocco":"Morocco",
    "Colombia":"Colombia","China":"China","Bangladesh":"Bangladesh",
    "Jamaica":"Jamaica","Croatia":"Croatia","Hungary":"Hungary",
    "South Korea":"South Korea","Qatar":"Qatar","Kuwait":"Kuwait",
    "Bahrain":"Bahrain","Taiwan":"Taiwan","Estonia":"Estonia",
    "Lithuania":"Lithuania","Latvia":"Latvia","Slovakia":"Slovakia",
    "Slovenia":"Slovenia","Bulgaria":"Bulgaria","Georgia":"Georgia",
    "Armenia":"Armenia","Azerbaijan":"Azerbaijan","Peru":"Peru",
    "Chile":"Chile","Ecuador":"Ecuador","Venezuela":"Venezuela",
    "Panama":"Panama","Costa Rica":"Costa Rica",
    "Dominican Republic":"Dominican Republic",
    "Luxembourg":"Luxembourg","Lebanon":"Lebanon","Jordan":"Jordan",
    "Oman":"Oman","Sri Lanka":"Sri Lanka","Kenya":"Kenya","Ghana":"Ghana",
    "Cameroon":"Cameroon","Tanzania":"Tanzania","Ethiopia":"Ethiopia",
    "Uganda":"Uganda","Mauritius":"Mauritius","Botswana":"Botswana",
    "Mongolia":"Mongolia","Nepal":"Nepal","Algeria":"Algeria","Tunisia":"Tunisia",
}

COORDS = {
    "US":(37.09,-95.71),"GB":(55.37,-3.44),"CA":(56.13,-106.35),
    "IN":(20.59,78.96),"IE":(53.41,-8.24),"DK":(56.26,9.50),
    "NL":(52.13,5.29),"AU":(-25.27,133.77),"DE":(51.17,10.45),
    "IT":(41.87,12.57),"FR":(46.23,2.21),"SE":(60.13,18.64),
    "ES":(40.46,-3.75),"AE":(23.42,53.85),"PK":(30.38,69.35),
    "IL":(31.05,34.85),"NZ":(-40.90,174.89),"BE":(50.50,4.47),
    "ZA":(-30.56,22.94),"PH":(12.88,121.77),"SG":(1.35,103.82),
    "RU":(61.52,105.32),"NO":(60.47,8.47),"TR":(38.96,35.24),
    "PL":(51.92,19.15),"PT":(39.40,-8.22),"UA":(48.38,31.17),
    "HK":(22.39,114.11),"CH":(46.82,8.23),"GR":(39.07,21.82),
    "JP":(36.20,138.25),"AT":(47.52,14.55),"RO":(45.94,24.97),
    "NG":(9.08,8.68),"MX":(23.63,-102.55),"FI":(61.92,25.75),
    "EG":(26.82,30.80),"CZ":(49.82,15.47),"ID":(-0.79,113.92),
    "BR":(-14.24,-51.93),"AR":(-38.42,-63.62),"VN":(14.06,108.28),
    "TH":(15.87,100.99),"SA":(23.89,45.08),"RS":(44.02,21.01),
    "MY":(4.21,101.98),"MA":(31.79,-7.09),"CO":(4.57,-74.30),
    "CN":(35.86,104.20),"BD":(23.68,90.35),"JM":(18.11,-77.30),
    "HR":(45.10,15.20),"HU":(47.16,19.50),"KR":(35.91,127.77),
    "QA":(25.35,51.18),"KW":(29.31,47.48),"BH":(26.03,50.55),
    "TW":(23.70,121.00),"EE":(58.60,25.01),"LT":(55.17,23.88),
    "LV":(56.88,24.60),"SK":(48.67,19.70),"SI":(46.15,14.99),
    "BG":(42.73,25.49),"GE":(42.31,43.36),"AM":(40.07,45.04),
    "AZ":(40.14,47.58),"PE":(-9.19,-75.02),"CL":(-35.68,-71.54),
    "EC":(-1.83,-78.18),"VE":(6.42,-66.59),"PA":(8.54,-80.78),
    "CR":(9.75,-83.75),"DO":(18.74,-70.16),"LU":(49.82,6.13),
    "LB":(33.85,35.86),"JO":(30.59,36.24),"OM":(21.51,55.92),
    "LK":(7.87,80.77),"KE":(-0.02,37.91),"GH":(7.95,-1.02),
    "CM":(3.85,11.50),"TZ":(-6.37,34.89),"ET":(9.15,40.49),
    "UG":(1.37,32.29),"MU":(-20.35,57.55),"BW":(-22.33,24.68),
    "MN":(46.86,103.85),"NP":(28.39,84.12),"DZ":(28.03,1.66),
    "TN":(33.89,9.54),"MT":(35.94,14.37),"CY":(35.13,33.43),
    "IS":(64.96,-19.02),
}

df["land_name"]    = df["land"].map(LAND_ZU_NAME).fillna(df["land"])
df["land_lat"]     = df["land"].map(lambda x: COORDS.get(x,(None,None))[0])
df["land_lon"]     = df["land"].map(lambda x: COORDS.get(x,(None,None))[1])
df["plotly_name"]  = df["land_name"].map(NAME_ZU_PLOTLY).fillna(df["land_name"])

alle_laender = (df.groupby("land_name")["land_name"]
    .count().sort_values(ascending=False).index.tolist())
alle_laender = [l for l in alle_laender if pd.notna(l) and str(l)!="nan"]

MIN_DATUM = df["review_datum"].min().date()
MAX_DATUM = df["review_datum"].max().date()

STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with","is","was",
    "are","were","be","been","have","has","had","do","does","did","will","would",
    "could","should","i","my","me","we","our","you","your","it","its","this","that",
    "they","their","them","he","she","from","by","not","no","so","as","if","what",
    "which","who","how","all","just","more","also","very","can","get","got","when",
    "about","up","out","there","than","then","into","over","after","amazon","order",
    "product","delivery","item","time","use","said","one","still","back","even",
    "never","any","us","re","ve","don","didn","wasnt","isnt","cant","ive","really",
    "review","account","customer","service","money","email","sent","told","those",
}

def top_w(texte, n=15):
    alle = []
    for t in texte:
        w = re.findall(r"\b[a-z]{4,}\b", str(t).lower())
        alle.extend([x for x in w if x not in STOPWORDS])
    return Counter(alle).most_common(n)

def filtere(sentiments, laender, datum_von, datum_bis, certainty, nur_abw):
    d = df.copy()
    if sentiments:  d = d[d["text_sentiment"].isin(sentiments)]
    if laender:     d = d[d["land_name"].isin(laender)]
    if datum_von:   d = d[d["review_datum"] >= pd.Timestamp(datum_von)]
    if datum_bis:   d = d[d["review_datum"] <= pd.Timestamp(datum_bis)]
    d = d[d["text_sentiment_score"] >= certainty]
    if nur_abw and "ja" in nur_abw:
        d = d[d["uebereinstimmung"]==0]
    return d

def vorperiode(datum_von, datum_bis):
    """Berechnet die gleich lange Vorperiode."""
    if not datum_von or not datum_bis:
        return None, None
    v = pd.Timestamp(datum_von)
    b = pd.Timestamp(datum_bis)
    delta = b - v
    return (v - delta - pd.Timedelta(days=1)).date(), (v - pd.Timedelta(days=1)).date()

# ── Design ─────────────────────────────────────────────────────────────────
BG    = "#f9fafb"
BG2   = "#ffffff"
BG3   = "#f3f4f6"
BRD   = "#e5e7eb"
ACC   = "#1e40af"
ACC_L = "#eff6ff"
TXT   = "#111827"
TXT2  = "#6b7280"
TXT3  = "#9ca3af"
POS   = "#166534"; POS_L = "#f0fdf4"
NEU   = "#92400e"; NEU_L = "#fffbeb"
NEG   = "#991b1b"; NEG_L = "#fef2f2"
DISC  = "#5b21b6"; DISC_L= "#f5f3ff"

LB = dict(
    paper_bgcolor=BG2, plot_bgcolor=BG2,
    font=dict(color=TXT, family="Inter, Segoe UI, sans-serif", size=11),
    margin=dict(t=20, b=36, l=16, r=16),
    hoverlabel=dict(bgcolor=BG2, font_color=TXT, bordercolor=BRD),
)

CARD = {"backgroundColor":BG2,"borderRadius":"8px","padding":"20px 22px",
        "border":f"1px solid {BRD}","boxShadow":"0 1px 3px rgba(0,0,0,0.04)"}
HDR  = {"fontWeight":"700","color":TXT,"marginBottom":"2px","fontSize":"0.88rem",
        "letterSpacing":"-0.01em"}
SUB  = {"fontSize":"0.73rem","color":TXT3,"marginBottom":"12px","lineHeight":"1.5"}

TBL = dict(
    style_table={"overflowX":"auto","border":f"1px solid {BRD}",
                 "borderRadius":"6px","overflow":"hidden"},
    style_cell={"backgroundColor":BG2,"color":TXT,"border":f"1px solid {BRD}",
                "padding":"8px 13px","fontSize":"0.8rem","textAlign":"left",
                "maxWidth":"260px","overflow":"hidden","textOverflow":"ellipsis",
                "fontFamily":"Inter, Segoe UI, sans-serif"},
    style_header={"backgroundColor":BG3,"color":TXT2,"fontWeight":"600",
                  "border":f"1px solid {BRD}","fontSize":"0.72rem",
                  "textTransform":"uppercase","letterSpacing":"0.07em",
                  "padding":"9px 13px"},
    style_data_conditional=[
        {"if":{"filter_query":'{Sentiment} = L["pos"]'},"color":POS,"fontWeight":"600"},
        {"if":{"filter_query":'{Sentiment} = L["neg"]'},"color":NEG,"fontWeight":"600"},
        {"if":{"filter_query":'{Sentiment} = L["neu"]'}, "color":NEU,"fontWeight":"600"},
        {"if":{"row_index":"odd"},"backgroundColor":BG3},
    ],
    sort_action="native", filter_action="native", page_size=12,
)

BTN_ON  = {"backgroundColor":ACC,"color":"#fff","border":"none","borderRadius":"6px",
           "padding":"7px 16px","cursor":"pointer","fontSize":"0.8rem","fontWeight":"600"}
BTN_OFF = {"backgroundColor":"transparent","color":TXT2,"border":f"1px solid {BRD}",
           "borderRadius":"6px","padding":"7px 16px","cursor":"pointer",
           "fontSize":"0.8rem","fontWeight":"600"}

CHART_C = {L["pos"]:"#16a34a",L["neu"]:"#d97706",L["neg"]:"#dc2626"}

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Sentiment Analytics"

app.layout = html.Div(
    style={"backgroundColor":BG,"minHeight":"100vh",
           "fontFamily":"Inter, Segoe UI, sans-serif","color":TXT},
    children=[

    # ── HEADER ──────────────────────────────────────────────────────────────
    html.Div(style={
        "backgroundColor":BG2,"borderBottom":f"1px solid {BRD}",
        "padding":"0 36px","display":"flex","alignItems":"center",
        "justifyContent":"space-between","height":"54px",
        "position":"sticky","top":"0","zIndex":"200",
        "boxShadow":"0 1px 2px rgba(0,0,0,0.05)"
    }, children=[
        html.Div(style={"display":"flex","alignItems":"center","gap":"20px"}, children=[
            html.Div(style={"display":"flex","alignItems":"center","gap":"10px"}, children=[
                html.Div(style={"width":"3px","height":"28px",
                                "backgroundColor":ACC,"borderRadius":"2px"}),
                html.Div(style={"display":"flex","alignItems":"center","gap":"10px"}, children=[
                    html.Img(
                        src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
                        style={"height":"22px","filter":"brightness(0)","opacity":"0.85"}
                    ),
                    html.Div([
                        html.Span("Reviews",
                            style={"fontWeight":"700","fontSize":"0.97rem","color":TXT}),
                        html.Span(" Sentiment Analytics",
                            style={"fontWeight":"400","fontSize":"0.97rem","color":TXT2}),
                        html.Div("RoBERTa Transformer · Kaggle Dataset",
                            style={"fontSize":"0.67rem","color":TXT3,
                                   "letterSpacing":"0.03em","marginTop":"1px"}),
                    ]),
                ]),
            ]),
        ]),
        html.Div(style={"display":"flex","alignItems":"center","gap":"8px"}, children=[
            html.Div(id="nav-buttons", style={"display":"flex","gap":"4px"},
                children=[
                    html.Button("Overview",    id="btn-0",n_clicks=0,style=BTN_ON),
                    html.Button("Time Series", id="btn-1",n_clicks=0,style=BTN_OFF),
                    html.Button("Countries",   id="btn-2",n_clicks=0,style=BTN_OFF),
                    html.Button("Reviews",     id="btn-3",n_clicks=0,style=BTN_OFF),
                ]),
            html.Div(style={"width":"1px","height":"22px",
                            "backgroundColor":BRD,"margin":"0 4px"}),
            html.Button("🇩🇪 DE", id="btn-lang", n_clicks=0,
                style={"backgroundColor":"transparent","color":TXT2,
                       "border":f"1px solid {BRD}","borderRadius":"6px",
                       "padding":"5px 12px","cursor":"pointer",
                       "fontSize":"0.78rem","fontWeight":"600"}),
        ]),
        html.Div(style={"textAlign":"right","fontSize":"0.72rem"}, children=[
            html.Div("21,214 reviews", style={"fontWeight":"600","color":TXT}),
            html.Div("Aug 2007 – Sep 2024", style={"color":TXT3}),
        ]),
    ]),

    # ── FILTER BAR ──────────────────────────────────────────────────────────
    html.Div(style={
        "backgroundColor":BG2,"borderBottom":f"1px solid {BRD}",
        "padding":"10px 36px"
    }, children=[
        html.Div(style={
            "display":"grid",
            "gridTemplateColumns":"1fr 1fr 1fr 1fr 1fr",
            "gap":"16px",
            "alignItems":"end",
        }, children=[

            # SENTIMENT
            html.Div([
                html.Label("SENTIMENT",
                    style={"fontSize":"0.65rem","color":TXT3,"fontWeight":"700",
                           "letterSpacing":"0.09em","display":"block","marginBottom":"4px"}),
                html.Div(style={"overflow":"hidden","height":"36px","position":"relative"}, children=[
                    dcc.Dropdown(id="f-s",
                        options=[{"label":L["pos"],"value":"positiv"},
                                 {"label":L["neu"],  "value":"neutral"},
                                 {"label":L["neg"],  "value":"negativ"}],
                        value=["positiv","neutral","negativ"],
                        multi=True, clearable=False,
                        style={"fontSize":"0.82rem","width":"100%"}),
                ]),
            ]),

            # COUNTRIES
            html.Div([
                html.Label("COUNTRIES",
                    style={"fontSize":"0.65rem","color":TXT3,"fontWeight":"700",
                           "letterSpacing":"0.09em","display":"block","marginBottom":"4px"}),
                html.Div(style={"overflow":"hidden","height":"36px","position":"relative"}, children=[
                    dcc.Dropdown(id="f-l",
                        options=[{"label":l,"value":l} for l in alle_laender],
                        value=alle_laender[:8], multi=True,
                        style={"fontSize":"0.82rem","width":"100%"},
                        placeholder="Select countries..."),
                ]),
            ]),

            # DATE RANGE
            html.Div([
                html.Label("DATE RANGE",
                    style={"fontSize":"0.65rem","color":TXT3,"fontWeight":"700",
                           "letterSpacing":"0.09em","display":"block","marginBottom":"4px"}),
                dcc.DatePickerRange(
                    id="f-datum",
                    min_date_allowed=MIN_DATUM,
                    max_date_allowed=MAX_DATUM,
                    start_date=date(2020,1,1),
                    end_date=MAX_DATUM,
                    display_format="DD MMM YYYY",
                    style={"fontSize":"0.82rem","width":"100%"},
                ),
            ]),

            # MODEL CERTAINTY
            html.Div([
                html.Label("MODEL CERTAINTY",
                    style={"fontSize":"0.65rem","color":TXT3,"fontWeight":"700",
                           "letterSpacing":"0.09em","display":"block","marginBottom":"4px"}),
                html.Div("Min. AI confidence in classification",
                    style={"fontSize":"0.68rem","color":TXT3,"marginBottom":"6px"}),
                dcc.Slider(id="f-k", min=0, max=1, step=0.1, value=0,
                    marks={0:"Any",0.6:"60%",0.8:"80%",1:"100%"},
                    tooltip={"placement":"bottom","always_visible":False}),
            ]),

            # VIEW
            html.Div([
                html.Label("VIEW",
                    style={"fontSize":"0.65rem","color":TXT3,"fontWeight":"700",
                           "letterSpacing":"0.09em","display":"block","marginBottom":"4px"}),
                dcc.Checklist(id="f-a",
                    options=[{"label":"  Discrepancies only","value":"ja"}],
                    value=[], style={"fontSize":"0.82rem","color":TXT,"paddingTop":"8px"}),
            ]),
        ]),
    ]),

    dcc.Store(id="aktiver-tab", data=0),
    dcc.Store(id="lang", data="en"),
    html.Div(id="inhalt", style={"padding":"20px 36px"}),
])


# Übersetzungen
LANG = {
    "en": {
        "tabs":    ["Overview","Time Series","Countries","Reviews"],
        "pos":L["pos"],"neu":L["neu"],"neg":L["neg"],
        "cert":L["cert"],
        "total":L["total"],"period":L["period"],
        "rating":L["rating"],"disc":L["disc"],"disc_s":L["disc_s"],
        "sent_dist":L["sent_dist"],
        "sent_dist_s":L["sent_dist_s"],
        "vgl_h":L["vgl_h"],
        "vgl_s":L["vgl_s"],
        "cert_s":L["cert_s"],
        "trend_h":L["trend_h"],
        "trend_s":L["trend_s"],
        "area_h":L["area_h"],
        "area_s":L["area_s"],
        "nj_h":L["nj_h"],
        "nj_s":L["nj_s"],
        "rj_h":L["rj_h"],
        "rj_s":L["rj_s"],
        "choro_h":L["choro_h"],
        "choro_s":L["choro_s"],
        "bubble_h":L["bubble_h"],
        "bubble_s":L["bubble_s"],
        "bar_h":L["bar_h"],
        "bar_s":L["bar_s"],
        "words_neg":L["words_neg"],
        "words_pos":L["words_pos"],
        "disc_h":L["disc_h"],
        "disc_txt":"Reviews where the AI model\'s reading contradicts the star rating. High confidence = certain model.",
        "browser_h":L["browser_h"],
        "browser_s":L["browser_s"],
        "btn_lang":"🇩🇪 DE","no_data":L["no_data"],
        "vs_prior":L["vs_prior"],"reviews_n":"reviews","period_avg":"Period avg",
    },
    "de": {
        "tabs":    ["Übersicht","Zeitverlauf","Länder","Bewertungen"],
        "pos":"Positiv","neu":L["neu"],"neg":"Negativ",
        "cert":"Ø Modell-Sicherheit",
        "total":"Bewertungen gesamt","period":"aktueller Zeitraum",
        "rating":"Ø Sternebewertung","disc":"Abweichungen","disc_s":"Text ≠ Sterne",
        "sent_dist":"Stimmungs-Verteilung",
        "sent_dist_s":"Modell-Ergebnis aus dem Text – unabhängig von der Sternebewertung",
        "vgl_h":"Sterne-Rating vs. Text-Stimmung",
        "vgl_s":"Wie oft stimmt das Modell mit der Sternebewertung überein?",
        "cert_s":"Wie sicher war das RoBERTa-Modell bei seiner Einschätzung?",
        "trend_h":"Monatlicher Stimmungs-Trend",
        "trend_s":"Stimmungsentwicklung über den gesamten Zeitraum",
        "area_h":"Monatliches Bewertungsvolumen",
        "area_s":"Gestapeltes Flächendiagramm – absolute Anzahl Bewertungen pro Monat",
        "nj_h":"Negativanteil pro Jahr",
        "nj_s":"Jährlicher Anteil negativer Bewertungen laut Modell",
        "rj_h":"Ø Sternebewertung pro Jahr",
        "rj_s":"Jährlicher Durchschnitt der vergebenen Sternebewertungen",
        "choro_h":"Negativanteil nach Land",
        "choro_s":"Anteil negativer Bewertungen pro Land – Hover für Details",
        "bubble_h":"Bewertungsvolumen nach Standort",
        "bubble_s":"Blasengröße = Anzahl Bewertungen · Farbe = Negativanteil",
        "bar_h":"Top 15 Länder – Stimmungsaufschlüsselung",
        "bar_s":"Absolute Bewertungsanzahl nach Stimmung pro Land",
        "words_neg":"Häufigste Wörter – Negative Bewertungen",
        "words_pos":"Häufigste Wörter – Positive Bewertungen",
        "disc_h":"Abweichungen – Text-Stimmung vs. Sterne-Bewertung",
        "disc_txt":"Bewertungen wo das Modell anders urteilt als die Sterne. Hohe Konfidenz = Modell war sicher.",
        "browser_h":"Bewertungs-Browser",
        "browser_s":"Alle Bewertungen des aktuellen Filters – sortier- und durchsuchbar",
        "btn_lang":"🇬🇧 EN","no_data":"Keine Daten für die aktuelle Filterauswahl.",
        "vs_prior":"vs. Vorperiode","reviews_n":"Bewertungen","period_avg":"Zeitraum-Ø",
        "col_country":"Land","col_stars":"Sterne","col_rlabel":"Sterne-Label",
        "col_sent":"Stimmung","col_conf":"Konfidenz","col_text":"Bewertungstext",
        "col_date":"Datum","col_match":"Übereinstimmung","col_title":"Titel",
    },
}

@app.callback(
    Output("lang","data"),
    Output("btn-lang","children"),
    Output("btn-lang","style"),
    Input("btn-lang","n_clicks"),
    prevent_initial_call=True,
)
def toggle_lang(n):
    lang = "de" if (n or 0) % 2 == 1 else "en"
    aktiv = lang == "de"
    stil = {"backgroundColor": ACC if aktiv else "transparent",
            "color": "#fff" if aktiv else TXT2,
            "border": f"1px solid {ACC if aktiv else BRD}",
            "borderRadius":"6px","padding":"5px 12px",
            "cursor":"pointer","fontSize":"0.78rem","fontWeight":"600"}
    return lang, LANG[lang]["btn_lang"], stil

# ── Tab switching ────────────────────────────────────────────────────────────
@app.callback(
    Output("aktiver-tab","data"),
    Output("btn-0","style"),Output("btn-1","style"),
    Output("btn-2","style"),Output("btn-3","style"),
    Output("btn-0","children"),Output("btn-1","children"),
    Output("btn-2","children"),Output("btn-3","children"),
    Input("btn-0","n_clicks"),Input("btn-1","n_clicks"),
    Input("btn-2","n_clicks"),Input("btn-3","n_clicks"),
    Input("lang","data"),
)
def switch_tab(n0,n1,n2,n3,lang):
    tl = LANG.get(lang or "en","en")["tabs"]
    ctx = callback_context
    tab = 0
    if ctx.triggered and ctx.triggered[0]["value"]:
        pid = ctx.triggered[0]["prop_id"]
        if "btn-lang" not in pid and "lang" not in pid:
            tab = int(pid.split("-")[1].split(".")[0])
    tl = LANG.get(lang or "en",LANG["en"])["tabs"]
    return tab, *(BTN_ON if i==tab else BTN_OFF for i in range(4)), *tl,

# ── Main render ──────────────────────────────────────────────────────────────
@app.callback(
    Output("inhalt","children"),
    Input("aktiver-tab","data"),
    Input("f-s","value"),Input("f-l","value"),
    Input("f-datum","start_date"),Input("f-datum","end_date"),
    Input("f-k","value"),Input("f-a","value"),
    Input("lang","data"),
)
def render(tab,s,l,d_von,d_bis,k,a,lang):
    L = LANG.get(lang or "en", LANG["en"])
    d    = filtere(s,l,d_von,d_bis,k,a)
    n    = len(d)
    vvon, vbis = vorperiode(d_von,d_bis)
    d_vor= filtere(s,l,vvon,vbis,k,a) if vvon else pd.DataFrame()
    n_vor= len(d_vor)

    if n == 0:
        return html.Div(L["no_data"],
            style={"color":TXT3,"padding":"60px","textAlign":"center",
                   "fontSize":"0.9rem"})

    pos_n = (d["text_sentiment"]=="positiv").sum()
    neu_n = (d["text_sentiment"]=="neutral").sum()
    neg_n = (d["text_sentiment"]=="negativ").sum()
    abw_n = (d["uebereinstimmung"]==0).sum()
    avg_k = d["text_sentiment_score"].mean()
    avg_r = d["rating"].mean()

    pos_v = (d_vor["text_sentiment"]=="positiv").sum() if n_vor else None
    neg_v = (d_vor["text_sentiment"]=="negativ").sum() if n_vor else None
    n_v   = len(d_vor) if n_vor else None

    def delta_str(curr, prev, pct=False):
        if prev is None or prev==0: return None
        diff = curr - prev
        pct_d = diff/prev*100
        sign = "+" if diff>=0 else ""
        if pct:
            return f"{sign}{pct_d:.1f}% vs prior period"
        return f"{sign}{diff:,} ({sign}{pct_d:.1f}%) vs prior"

    def kpi(val, label, sub, color, bg, delta=None):
        return html.Div(style={
            "backgroundColor":bg,"borderRadius":"8px","padding":"18px 20px",
            "border":f"1px solid {BRD}","borderLeft":f"3px solid {color}",
        }, children=[
            html.Div(val, style={"fontSize":"1.9rem","fontWeight":"800",
                                  "color":color,"lineHeight":"1.1",
                                  "letterSpacing":"-0.02em"}),
            html.Div(sub, style={"fontSize":"0.75rem","color":color,
                                  "opacity":"0.7","marginTop":"1px"}) if sub else html.Span(),
            html.Div(label, style={"fontSize":"0.65rem","color":TXT2,
                                    "textTransform":"uppercase","letterSpacing":"0.08em",
                                    "marginTop":"8px","fontWeight":"600"}),
            html.Div(delta, style={"fontSize":"0.68rem","color":TXT3,
                                    "marginTop":"4px"}) if delta else html.Span(),
        ])

    kpis = html.Div(style={"display":"grid","gridTemplateColumns":"repeat(6,1fr)",
                            "gap":"12px","marginBottom":"18px"}, children=[
        kpi(f"{n:,}",    L["total"],    L["period"],    ACC,  ACC_L,
            delta_str(n,n_v)),
        kpi(f"{avg_r:.2f}",L["rating"],   "out of 5.0",        TXT,  BG3),
        kpi(f"{pos_n:,}",L["pos"],         f"{pos_n/n*100:.1f}%",POS,POS_L,
            delta_str(pos_n,pos_v)),
        kpi(f"{neu_n:,}",L["neu"],          f"{neu_n/n*100:.1f}%",NEU,NEU_L),
        kpi(f"{neg_n:,}",L["neg"],         f"{neg_n/n*100:.1f}%",NEG,NEG_L,
            delta_str(neg_n,neg_v)),
        kpi(f"{abw_n:,}",L["disc"],
            L["disc_s"],             DISC, DISC_L),
    ])

    # ── TAB 0: OVERVIEW ─────────────────────────────────────────────────────
    if tab == 0:
        cnt = d["text_sentiment"].value_counts().reset_index()
        cnt.columns = ["s","n"]
        lmap = {"positiv":L["pos"],"neutral":L["neu"],"negativ":L["neg"]}
        cnt["label"] = cnt["s"].map(lmap)

        fig_pie = go.Figure(go.Pie(
            values=cnt["n"], labels=cnt["label"], hole=0.62,
            marker=dict(colors=[{"positiv":"#22c55e","neutral":"#f59e0b","negativ":"#f87171"}.get(x,"#888") for x in cnt["s"]],
                        line=dict(color=BG2,width=3)),
            textinfo="percent+label",
            textfont=dict(size=11,color=TXT),
            hovertemplate="<b>%{label}</b><br>%{value:,} · %{percent}<extra></extra>"))
        fig_pie.update_layout(**LB, height=280,
            legend=dict(orientation="h",y=-0.12,x=0.5,xanchor="center"),
            annotations=[dict(text=f"<b>{n:,}</b>",x=0.5,y=0.5,
                showarrow=False,font=dict(size=18,color=TXT))])

        vgl = d.groupby(["rating","text_sentiment"]).size().reset_index(name="n")
        vgl["r"] = vgl["rating"].astype(str)+" ★"
        vgl[L.get("col_sent","Sentiment")] = vgl["text_sentiment"].map(lmap)
        fig_vgl = go.Figure()
        for sent,c in [(L["neg"],NEG),(L["neu"],NEU),(L["pos"],POS)]:
            sub = vgl[vgl[L.get("col_sent","Sentiment")]==sent]
            fig_vgl.add_trace(go.Bar(name=sent,x=sub["r"],y=sub["n"],
                marker_color=c,
                hovertemplate=f"<b>%{{x}}</b><br>{sent}: %{{y:,}}<extra></extra>"))
        fig_vgl.update_layout(**LB,height=280,barmode="group",
            legend=dict(orientation="h",y=1.06,x=1,xanchor="right"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True,gridcolor=BRD,gridwidth=1))

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_k*100,
            number={"suffix":"%","font":{"size":28,"color":TXT}},
            gauge={"axis":{"range":[0,100],"tickfont":{"color":TXT2,"size":9}},
                   "bar":{"color":ACC,"thickness":0.5},
                   "bgcolor":BG3,"bordercolor":BRD,"borderwidth":1,
                   "steps":[{"range":[0,60],"color":"#fee2e2"},
                             {"range":[60,80],"color":"#fef9c3"},
                             {"range":[80,100],"color":"#dcfce7"}],
                   "threshold":{"line":{"color":POS,"width":2},"value":80}},
            title={"text":L["cert"],"font":{"color":TXT2,"size":11}}))
        fig_gauge.update_layout(**LB,height=280)

        zt = d.dropna(subset=["review_datum"]).copy()
        zt["monat"] = zt["review_datum"].dt.to_period("M").astype(str)
        agg = zt.groupby(["monat","text_sentiment"]).size().reset_index(name="n")
        agg[L.get("col_sent","Sentiment")] = agg["text_sentiment"].map(lmap)
        fig_trend = px.line(agg,x="monat",y="n",color=L.get("col_sent","Sentiment"),
            color_discrete_map={L["pos"]:POS,L["neu"]:NEU,L["neg"]:NEG},
            labels={"monat":"","n":"Reviews"})
        fig_trend.update_traces(line_width=1.8)
        fig_trend.update_layout(**LB,height=200,
            hovermode="x unified",showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True,gridcolor=BRD))

        return html.Div([kpis,
            html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr 0.7fr",
                            "gap":"14px","marginBottom":"14px"}, children=[
                html.Div(style=CARD,children=[
                    html.P(L["sent_dist"],style=HDR),
                    html.P(L["sent_dist_s"],style=SUB),
                    dcc.Graph(figure=fig_pie,config={"displayModeBar":False}),
                ]),
                html.Div(style=CARD,children=[
                    html.P(L["vgl_h"],style=HDR),
                    html.P(L["vgl_s"],style=SUB),
                    dcc.Graph(figure=fig_vgl,config={"displayModeBar":False}),
                ]),
                html.Div(style=CARD,children=[
                    html.P("Model Certainty",style=HDR),
                    html.P(L["cert_s"],style=SUB),
                    dcc.Graph(figure=fig_gauge,config={"displayModeBar":False}),
                ]),
            ]),
            html.Div(style=CARD,children=[
                html.P(L["trend_h"],style=HDR),
                html.P(L["trend_s"],style=SUB),
                dcc.Graph(figure=fig_trend,config={"displayModeBar":False}),
            ]),
        ])

    # ── TAB 1: TIME SERIES ───────────────────────────────────────────────────
    elif tab == 1:
        zt = d.dropna(subset=["review_datum"]).copy()
        zt["monat"] = zt["review_datum"].dt.to_period("M").astype(str)
        lmap = {"positiv":L["pos"],"neutral":L["neu"],"negativ":L["neg"]}

        agg = zt.groupby(["monat","text_sentiment"]).size().reset_index(name="n")
        agg[L.get("col_sent","Sentiment")] = agg["text_sentiment"].map(lmap)
        fig_area = go.Figure()
        for sent,c in [(L["neg"],NEG),(L["neu"],NEU),(L["pos"],POS)]:
            sub = agg[agg[L.get("col_sent","Sentiment")]==sent]
            fig_area.add_trace(go.Scatter(x=sub["monat"],y=sub["n"],
                name=sent,mode="lines",stackgroup="one",
                line=dict(color=c,width=1.5),
                fillcolor={L["neg"]:"rgba(153,27,27,0.15)",L["neu"]:"rgba(146,64,14,0.15)",L["pos"]:"rgba(22,101,52,0.15)"}.get(sent,"rgba(0,0,0,0.1)"),
                hovertemplate=f"<b>%{{x}}</b><br>{sent}: %{{y:,}}<extra></extra>"))
        fig_area.update_layout(**LB,height=320,hovermode="x unified",
            legend=dict(orientation="h",y=1.06,x=1,xanchor="right"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True,gridcolor=BRD))

        jhr = zt.groupby("jahr").agg(
            total=("text_sentiment","count"),
            neg=("text_sentiment",lambda x:(x=="negativ").sum()),
            avg_r=("rating","mean"),
        ).reset_index()
        jhr["neg_pct"] = (jhr["neg"]/jhr["total"]*100).round(1)
        jhr["avg_r"]   = jhr["avg_r"].round(2)

        bar_c = [NEG if p>70 else NEU if p>50 else POS for p in jhr["neg_pct"]]
        fig_nj = go.Figure(go.Bar(x=jhr["jahr"],y=jhr["neg_pct"],
            marker_color=bar_c,
            text=jhr["neg_pct"].apply(lambda x:f"{x:.0f}%"),
            textposition="outside",textfont=dict(color=TXT,size=10),
            hovertemplate="<b>%{x}</b><br>Negative: %{y:.1f}%<extra></extra>"))
        fig_nj.update_layout(**LB,height=280,
            yaxis=dict(range=[0,105],ticksuffix="%",showgrid=True,gridcolor=BRD),
            xaxis=dict(showgrid=False))

        fig_rj = go.Figure()
        fig_rj.add_trace(go.Scatter(x=jhr["jahr"],y=jhr["avg_r"],
            mode="lines+markers",
            line=dict(color=ACC,width=2),
            marker=dict(size=6,color=ACC,line=dict(color=BG2,width=2)),
            fill="tozeroy",fillcolor="rgba(30,64,175,0.07)",
            hovertemplate="<b>%{x}</b><br>Avg. Rating: %{y:.2f}<extra></extra>"))
        fig_rj.add_hline(y=jhr["avg_r"].mean(),line_dash="dot",
            line_color=TXT3,line_width=1,
            annotation_text=f"Period avg: {jhr['avg_r'].mean():.2f}",
            annotation_font=dict(color=TXT3,size=10))
        fig_rj.update_layout(**LB,height=280,
            yaxis=dict(range=[1,5.3],tickvals=[1,2,3,4,5],
                       showgrid=True,gridcolor=BRD),
            xaxis=dict(showgrid=False))

        return html.Div([kpis,
            html.Div(style={**CARD,"marginBottom":"14px"},children=[
                html.P(L["area_h"],style=HDR),
                html.P(L["area_s"],style=SUB),
                dcc.Graph(figure=fig_area,config={"displayModeBar":False}),
            ]),
            html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"14px"},children=[
                html.Div(style=CARD,children=[
                    html.P(L["nj_h"],style=HDR),
                    html.P(L["nj_s"],style=SUB),
                    dcc.Graph(figure=fig_nj,config={"displayModeBar":False}),
                ]),
                html.Div(style=CARD,children=[
                    html.P(L["rj_h"],style=HDR),
                    html.P(L["rj_s"],style=SUB),
                    dcc.Graph(figure=fig_rj,config={"displayModeBar":False}),
                ]),
            ]),
        ])

    # ── TAB 2: COUNTRIES ─────────────────────────────────────────────────────
    elif tab == 2:
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

        if len(la)==0:
            return html.Div("No country data available.",
                style={"padding":"40px","textAlign":"center","color":TXT3})

        # Choropleth – country names mode (Plotly 6 compatible)
        la_map = la[la["count"]>=3].copy()
        fig_choro = go.Figure(go.Choropleth(
            locations=la_map["plotly_name"],
            locationmode="country names",
            z=la_map["neg_pct"],
            colorscale=[[0,"#bbf7d0"],[0.4,"#fef9c3"],[0.75,"#fecaca"],[1,"#991b1b"]],
            zmin=0, zmax=100,
            text=la_map["land_name"],
            customdata=la_map[["count","avg_r","pos_pct","neu_pct","neg_pct"]].values,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Reviews: %{customdata[0]:,}<br>"
                "Avg. Rating: %{customdata[1]:.2f} ★<br>"
                "Positive: %{customdata[2]:.1f}%<br>"
                "Neutral: %{customdata[3]:.1f}%<br>"
                "Negative: %{customdata[4]:.1f}%"
                "<extra></extra>"
            ),
            colorbar=dict(
                title=dict(text="% Negative",font=dict(size=10,color=TXT2)),
                tickfont=dict(size=9,color=TXT2),
                thickness=12,len=0.65,
                ticksuffix="%",x=1.01,
            ),
            marker=dict(line=dict(color=BG2,width=0.4)),
        ))
        fig_choro.update_layout(
            paper_bgcolor=BG2,plot_bgcolor=BG2,
            font=dict(color=TXT,family="Inter, Segoe UI"),
            margin=dict(t=0,b=0,l=0,r=0),height=400,
            geo=dict(
                bgcolor=BG2,showframe=False,
                showcoastlines=True,coastlinecolor=BRD,coastlinewidth=0.5,
                landcolor="#f3f4f6",showocean=True,oceancolor="#e0f2fe",
                showlakes=True,lakecolor="#e0f2fe",
                projection_type="natural earth",
            ),
        )

        # Bubble map – review volume by location
        la_bubble = la[la["land_lat"].notna() & (la["count"]>=3)].copy()
        fig_bubble = go.Figure(go.Scattergeo(
            lat=la_bubble["land_lat"],
            lon=la_bubble["land_lon"],
            text=la_bubble["land_name"],
            customdata=la_bubble[["count","neg_pct","avg_r"]].values,
            mode="markers",
            marker=dict(
                size=la_bubble["count"].apply(lambda x: max(4, min(40, x/80))),
                color=la_bubble["neg_pct"],
                colorscale=[[0,"#bbf7d0"],[0.5,"#fef9c3"],[1,"#991b1b"]],
                cmin=0,cmax=100,
                line=dict(color=BG2,width=0.5),
                opacity=0.85,
                colorbar=dict(
                    title=dict(text="% Negative",font=dict(size=10,color=TXT2)),
                    tickfont=dict(size=9,color=TXT2),
                    thickness=12,len=0.6,
                    ticksuffix="%",x=1.01,
                ),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Reviews: %{customdata[0]:,}<br>"
                "Negative: %{customdata[1]:.1f}%<br>"
                "Avg. Rating: %{customdata[2]:.2f} ★"
                "<extra></extra>"
            ),
        ))
        fig_bubble.update_layout(
            paper_bgcolor=BG2,plot_bgcolor=BG2,
            font=dict(color=TXT,family="Inter, Segoe UI"),
            margin=dict(t=0,b=0,l=0,r=0),height=380,
            geo=dict(
                bgcolor=BG2,showframe=False,
                showcoastlines=True,coastlinecolor=BRD,coastlinewidth=0.5,
                landcolor="#f3f4f6",showocean=True,oceancolor="#e0f2fe",
                showlakes=False,projection_type="natural earth",
            ),
        )

        # Stacked bar top 15
        top15 = la[la["count"]>=10].nlargest(15,"count")
        fig_b = go.Figure()
        for sent,lbl,c in [("neg",L["neg"],NEG),("neu",L["neu"],NEU),("pos",L["pos"],POS)]:
            fig_b.add_trace(go.Bar(name=lbl,x=top15["land_name"],
                y=top15[sent],marker_color=c,
                hovertemplate=f"<b>%{{x}}</b><br>{lbl}: %{{y:,}}<extra></extra>"))
        fig_b.update_layout(**LB,barmode="stack",height=320,
            legend=dict(orientation="h",y=1.06,x=1,xanchor="right"),
            xaxis=dict(tickangle=-30,showgrid=False,tickfont=dict(size=9)),
            yaxis=dict(showgrid=True,gridcolor=BRD))

        return html.Div([kpis,
            html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr",
                            "gap":"14px","marginBottom":"14px"}, children=[
                html.Div(style=CARD,children=[
                    html.P(L["choro_h"],style=HDR),
                    html.P(L["choro_s"],style=SUB),
                    dcc.Graph(figure=fig_choro,config={"displayModeBar":False}),
                ]),
                html.Div(style=CARD,children=[
                    html.P(L["bubble_h"],style=HDR),
                    html.P(L["bubble_s"],style=SUB),
                    dcc.Graph(figure=fig_bubble,config={"displayModeBar":False}),
                ]),
            ]),
            html.Div(style={"display":"grid","gridTemplateColumns":"1.3fr 0.7fr",
                            "gap":"14px"}, children=[
                html.Div(style=CARD,children=[
                    html.P(L["bar_h"],style=HDR),
                    html.P(L["bar_s"],style=SUB),
                    dcc.Graph(figure=fig_b,config={"displayModeBar":False}),
                ]),

            ]),
        ])

    # ── TAB 3: REVIEWS ───────────────────────────────────────────────────────
    elif tab == 3:
        lmap = {"positiv":L["pos"],"neutral":L["neu"],"negativ":L["neg"]}

        def wfig(sentiment, color, title):
            top = top_w(d[d["text_sentiment"]==sentiment]["review_text"],15)
            if not top: return go.Figure().update_layout(**LB,height=380)
            wdf = pd.DataFrame(top,columns=["word","n"])
            fig = go.Figure(go.Bar(
                x=wdf["n"],y=wdf["word"],orientation="h",
                marker=dict(color=wdf["n"],
                    colorscale=[[0,BG3],[1,color]],
                    line=dict(color=BRD,width=0.5)),
                text=wdf["n"],textposition="outside",
                textfont=dict(color=TXT2,size=10),
                hovertemplate="<b>%{y}</b>: %{x:,}<extra></extra>"))
            fig.update_layout(**LB,height=400,
                title=dict(text=title,font=dict(size=12,color=TXT)),
                yaxis=dict(autorange="reversed"),
                xaxis=dict(showgrid=True,gridcolor=BRD))
            return fig

        abw = d[d["uebereinstimmung"]==0].sort_values("text_sentiment_score",ascending=False)
        abw_s = abw[["land_name","rating","rating_sentiment","text_sentiment",
                      "text_sentiment_score","review_text"]].head(100).copy()
        abw_s["rating_sentiment"] = abw_s["rating_sentiment"].map(lmap).fillna(abw_s["rating_sentiment"])
        abw_s["text_sentiment"]   = abw_s["text_sentiment"].map(lmap).fillna(abw_s["text_sentiment"])
        abw_s.columns = [L.get("col_country","Country"),L.get("col_stars","Stars"),L.get("col_rlabel","Rating Label"),L.get("col_sent","Sentiment"),L.get("col_conf","Confidence"),L.get("col_text","Review Text")]

        br = d[["review_datum","land_name","rating","text_sentiment",
                "text_sentiment_score","uebereinstimmung",
                "review_titel","review_text"]].head(300).copy()
        br["text_sentiment"] = br["text_sentiment"].map(lmap).fillna(br["text_sentiment"])
        br.columns = [L.get("col_date","Date"),L.get("col_country","Country"),L.get("col_stars","Stars"),L.get("col_sent","Sentiment"),
                      L.get("col_conf","Confidence"),L.get("col_match","Match"),L.get("col_title","Title"),L.get("col_text","Review Text")]

        return html.Div([kpis,
            html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr",
                            "gap":"14px","marginBottom":"14px"}, children=[
                html.Div(style=CARD,children=[
                    dcc.Graph(figure=wfig("negativ",NEG,L["words_neg"]),
                              config={"displayModeBar":False}),
                ]),
                html.Div(style=CARD,children=[
                    dcc.Graph(figure=wfig("positiv",POS,L["words_pos"]),
                              config={"displayModeBar":False}),
                ]),
            ]),
            html.Div(style={**CARD,"marginBottom":"14px"},children=[
                html.P(L["disc_h"],style=HDR),
                html.P(
                    "These are the most analytically interesting cases: reviews where the AI model's "
                    "reading of the text contradicts what the star rating implies. "
                    "High confidence means the model was certain — making the discrepancy meaningful.",
                    style=SUB),
                dash_table.DataTable(
                    data=abw_s.to_dict("records"),
                    columns=[{"name":c,"id":c} for c in abw_s.columns],
                    tooltip_data=[{L.get("col_text","Review Text"):{"value":str(r[L.get("col_text","Review Text")]),"type":"markdown"}}
                                  for r in abw_s.to_dict("records")],
                    tooltip_duration=None,**TBL),
            ]),
            html.Div(style=CARD,children=[
                html.P(L["browser_h"],style=HDR),
                html.P(L["browser_s"],style=SUB),
                dash_table.DataTable(
                    data=br.to_dict("records"),
                    columns=[{"name":c,"id":c} for c in br.columns],
                    tooltip_data=[{L.get("col_text","Review Text"):{"value":str(r[L.get("col_text","Review Text")]),"type":"markdown"}}
                                  for r in br.to_dict("records")],
                    tooltip_duration=None,**TBL),
            ]),
        ])

if __name__ == "__main__":
    print("="*50)
    print("  Dashboard ready.")
    print("  Open: http://127.0.0.1:8050")
    print("  Stop: red square in Spyder")
    print("="*50)
    app.run(debug=False, host="127.0.0.1", port=8050)
