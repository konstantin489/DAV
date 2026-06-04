# Amazon Reviews – Sentiment-Analyse Dashboard

**Live-Dashboard:** https://konstantin489-dav.streamlit.app

Dieses Projekt analysiert 21.214 echte Kundenbewertungen von Amazon (Quelle: Kaggle / Trustpilot)
mit einem modernen KI-Sprachmodell und visualisiert die Ergebnisse in einem interaktiven Dashboard.

---

## Projektziel

Ziel ist es, aus den **Texten** der Kundenbewertungen automatisiert die Stimmung zu extrahieren –
unabhängig von der Sternebewertung. Dabei geht es bewusst um die **Käufer als Personen**,
nicht um die Produkte selbst: Wer schreibt? Aus welchem Land? Wie oft? Und was empfindet diese Person wirklich?

---

## Prozess-Übersicht

```
Rohdaten (CSV)  →  Bereinigung  →  Standardisierung  →  RoBERTa-Analyse  →  Datenbank  →  Dashboard
```

### Schritt 1 – Datenexploration

```python
import pandas as pd

df = pd.read_csv("Amazon_Reviews.csv", on_bad_lines="skip", engine="python")
print(f"Zeilen: {len(df):,}")       # 21.214
print(f"Spalten: {len(df.columns)}")  # 9
print(df.isnull().sum())            # Fehlende Werte prüfen
```

**Befund:** Fehlende Werte < 1 %, Rating und Review-Text vollständig.
806 Duplikate bewusst behalten (echte Bewertungen, spiegeln Realität wider).

---

### Schritt 2 – Datenbereinigung

Die Rohdaten lagen in menschenlesbarem, aber maschinenunlesbarem Format vor:

| Vorher | Nachher |
|---|---|
| `"Rated 1 out of 5 stars"` | `1` |
| `"2024-09-16T13:44:26.000Z"` | `2024-09-16` |
| `"9 reviews"` | `9` |
| `" gb "` | `"GB"` |

```python
# Rating extrahieren
def rating_zu_zahl(r):
    if pd.isna(r): return None
    t = re.search(r"(\d)", str(r))
    return int(t.group(1)) if t else None

# Datum vereinfachen
df["review_datum"] = pd.to_datetime(df["Review Date"], errors="coerce", utc=True).dt.strftime("%Y-%m-%d")

# Ländercode einheitlich
df["land"] = df["Country"].str.strip().str.upper()
```

**Grundsatz:** Keine Daten löschen – ausschließlich neue Spalten hinzufügen.

---

### Schritt 3 – Sentiment-Analyse mit RoBERTa

**Warum RoBERTa statt einer Wortliste?**

| Text | Wortliste | RoBERTa |
|---|---|---|
| `"Not bad at all"` | negativ ❌ | positiv ✅ |
| `"Oh great, broken again"` | positiv ❌ | negativ ✅ |

RoBERTa wurde auf 58 Millionen echten Nutzertexten trainiert und versteht
Kontext, Verneinung und Umgangssprache.

```python
# Ausgeführt in Google Colab (GPU, ~4 Minuten)
from transformers import pipeline

roberta = pipeline(
    task   = "text-classification",
    model  = "cardiffnlp/twitter-roberta-base-sentiment-latest",
    device = 0  # GPU
)

# Jede Bewertung wird einzeln analysiert
for i in range(0, len(texte), 32):
    batch      = texte[i:i+32]
    ergebnisse = roberta(batch, batch_size=32)
    # → label: "positive"/"neutral"/"negative"
    # → score: Konfidenz 0.0–1.0
```

**Ergebnisse:**
- 69,5 % negativ · 23,8 % positiv · 6,7 % neutral
- Ø Modell-Konfidenz: 82 %
- 14,4 % Abweichungen (Text ≠ Sterne)

---

### Schritt 4 – SQLite Datenbank

```python
import sqlite3

conn = sqlite3.connect("amazon_reviews.db")
df_final.to_sql("reviews", conn, if_exists="replace", index=True, index_label="id")

# Vorberechnete Views für das Dashboard
conn.executescript("""
    CREATE VIEW IF NOT EXISTS sentiment_pro_land AS
    SELECT land, COUNT(*) AS anzahl,
           ROUND(100.0 * SUM(CASE WHEN text_sentiment='negativ'
                 THEN 1 ELSE 0 END) / COUNT(*), 1) AS negativ_prozent
    FROM reviews WHERE land IS NOT NULL
    GROUP BY land ORDER BY anzahl DESC;
""")
```

---

### Schritt 5 – Dashboard

Entwickelt mit **Streamlit** und **Plotly**. Vier Tabs:

| Tab | Inhalt |
|---|---|
| Übersicht | KPI-Karten, Stimmungsverteilung, Modell-Konfidenz |
| Zeitverlauf | Monatliche Entwicklung 2007–2024 |
| Länder | Weltkarte, Bubble-Map, Top-15-Länder |
| Bewertungen | Häufigste Wörter, Abweichungen, Browser |

---

## Der Datensatz: Es geht um Personen, nicht Produkte

Der Datensatz enthält Informationen über **Käufer als Personen**:
- Name des Rezensenten
- Land und Anzahl bisheriger Bewertungen
- Datum und Text der Bewertung

Er enthält **keine** Produktnummern, Kategorien oder Rückgabedaten.
Die Analyse zeigt damit das **Stimmungsbild einer Käufergruppe** –
nicht die Qualität einzelner Produkte.

---

## Duplikate – Entscheidung und Beispiele

806 Reviews haben identischen Text. Beispiele:

| Reviewer | Land | Text (gekürzt) | Entscheidung |
|---|---|---|---|
| suman sarma & nunnu parma | IN | "Amazon customer very very good..." | behalten – möglicherweise Spam, aber real |
| tulsidas (2×) | IN | "Amazon used to be great..." | behalten – Mehrfach-Posting |
| Raju Ahmead & patdamnn | BD/US | "Great place to get quality products..." | behalten – zufällig identisch |

**Begründung:** Für die Stimmungsanalyse auf Plattformebene
spiegeln Duplikate die Realität wider. Würden wir sie entfernen,
würden wir den Datensatz aktiv verfälschen.

---

## Technische Umgebung

| Tool | Zweck |
|---|---|
| Python / Spyder | Entwicklung |
| Google Colab (GPU) | RoBERTa-Analyse |
| SQLite | Datenspeicherung |
| Streamlit + Plotly | Dashboard |
| GitHub | Versionierung & Hosting |

---

## Limitationen

- Modell ist englischzentriert (~98 % der Reviews auf Englisch)
- Ironie/Sarkasmus wird nicht immer korrekt erkannt
- Keine Produktdaten → keine Aussagen über einzelne Produkte
- Rückgaberate nicht analysierbar (keine Transaktionsdaten vorhanden)

---

*THWS Würzburg-Schweinfurt · Datenaufbereitung und Visualisierung*
