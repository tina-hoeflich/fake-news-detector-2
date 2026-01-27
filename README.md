# 🔍 Fake News Detector - Free Version

**100% kostenlos** mit GitHub Actions – kein Server nötig!

## So funktioniert's

1. GitHub Actions führt den Crawler alle 6 Stunden aus
2. Ergebnisse werden als JSON/CSV im Repo gespeichert
3. Du kannst die Ergebnisse im Dashboard ansehen

## Setup (5 Minuten)

### 1. Fork dieses Repo

Klicke auf "Fork" oben rechts.

### 2. Aktiviere GitHub Actions

Gehe zu `Settings` → `Actions` → `General` → Enable "Allow all actions"

### 3. Optional: API Key hinzufügen

Für bessere Fact-Check-Ergebnisse:
1. Hole einen [Google Fact Check API Key](https://developers.google.com/fact-check/tools/api/v1alpha1/factchecktools)
2. Gehe zu `Settings` → `Secrets and variables` → `Actions`
3. Klicke "New repository secret"
4. Name: `GOOGLE_FACTCHECK_API_KEY`, Value: dein Key

### 4. Manuell starten (optional)

Gehe zu `Actions` → `Fake News Crawler` → `Run workflow`

## Ergebnisse ansehen

### Option A: Im Repo
- `results/latest.json` – Aktuelle Ergebnisse
- `results/results_YYYYMMDD_HHMM.json` – Archiv

### Option B: Dashboard
1. Aktiviere GitHub Pages: `Settings` → `Pages` → Source: `main` / `root`
2. Öffne `https://<dein-username>.github.io/<repo-name>/`
3. Lade `results/latest.json`

### Option C: Download
Gehe zu `Actions` → Klicke auf einen Run → Download "results" Artifact

## Kosten

**$0** – GitHub Actions Free Tier beinhaltet:
- 2000 Minuten/Monat
- Dieser Crawler braucht ~2-3 Min pro Run
- Bei 4 Runs/Tag = ~360 Min/Monat ✅

## Anpassen

### Crawl-Frequenz ändern

In `.github/workflows/crawl.yml`:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Alle 6 Stunden
  # Oder:
  - cron: '0 8,20 * * *'  # 2x täglich (8:00 und 20:00 UTC)
  - cron: '0 12 * * *'    # 1x täglich (12:00 UTC)
```

### Andere Sprachen

In `crawler_simple.py`:
```python
GDELT_LANGUAGES = ["german", "english", "french", "spanish"]
```

### Mehr/Weniger Artikel

```python
MAX_ARTICLES = 50  # Standard: 30
```

## Struktur

```
├── .github/
│   └── workflows/
│       └── crawl.yml      # GitHub Action
├── results/
│   ├── latest.json        # Aktuelle Ergebnisse
│   └── results_*.json     # Archiv
├── crawler_simple.py      # Hauptscript
├── index.html             # Dashboard
└── README.md
```

## Limitierungen

- Keine Echtzeit-Analyse (nur alle paar Stunden)
- Keine persistente Datenbank (nur JSON-Dateien)
- Kein Web-API (nur statische Dateien)

Für eine Always-On-Lösung mit API: Siehe die `fake-news-service` Version (~$5/Monat).

## FAQ

**Q: Warum alle 6 Stunden und nicht öfter?**
A: Um im Free Tier zu bleiben. Du kannst es auf stündlich ändern, aber dann ~720 Min/Monat.

**Q: Kann ich RSS-Feeds hinzufügen?**
A: Ja! Erweitere `crawler_simple.py` mit der RSS-Logik aus der Service-Version.

**Q: Wo sind meine alten Ergebnisse?**
A: Im `results/` Ordner oder unter Actions → Artifacts (30 Tage).
