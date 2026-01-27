"""
Fake News Detection Pipeline - MVP
===================================
Ein minimales aber funktionales System zur automatisierten Erkennung 
von potenziellen Fake News. Iterativ erweiterbar.

Features MVP:
- Artikel-Extraktion von URLs
- Claim-Extraktion (einfache Heuristik + LLM-basiert optional)
- Google Fact Check API Abgleich
- Einfaches Scoring
- CSV/JSON Output für Review

Autor: Claude MVP Generator
"""

import requests
import json
import csv
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import urlparse
import hashlib

# ============================================================
# KONFIGURATION
# ============================================================

CONFIG = {
    # Google Fact Check API (kostenlos, Rate-Limited)
    "GOOGLE_FACTCHECK_API_KEY": "YOUR_API_KEY_HERE",  # Optional - funktioniert auch ohne
    "GOOGLE_FACTCHECK_URL": "https://factchecktools.googleapis.com/v1alpha1/claims:search",
    
    # Claim-Extraktion Settings
    "MIN_CLAIM_LENGTH": 30,
    "MAX_CLAIM_LENGTH": 300,
    
    # Scoring Thresholds
    "HIGH_RISK_THRESHOLD": 0.7,
    "MEDIUM_RISK_THRESHOLD": 0.4,
}

# ============================================================
# DATENMODELLE
# ============================================================

@dataclass
class Article:
    """Repräsentiert einen zu prüfenden Artikel."""
    url: str
    title: str
    text: str
    source_domain: str
    extracted_at: str
    content_hash: str

@dataclass  
class Claim:
    """Ein extrahierter Fakten-Claim."""
    text: str
    source_article_url: str
    extraction_method: str
    confidence: float

@dataclass
class FactCheckResult:
    """Ergebnis einer Fact-Check-Prüfung."""
    claim_text: str
    source_url: str
    has_existing_factcheck: bool
    factcheck_rating: Optional[str]
    factcheck_source: Optional[str]
    factcheck_url: Optional[str]
    risk_score: float
    risk_category: str
    checked_at: str

# ============================================================
# ARTIKEL-EXTRAKTION
# ============================================================

def extract_article(url: str) -> Optional[Article]:
    """
    Extrahiert Artikel-Inhalt von einer URL.
    MVP: Einfache Extraktion, später erweiterbar mit newspaper3k, trafilatura etc.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        html = response.text
        
        # Einfache Title-Extraktion
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "Unbekannt"
        
        # Einfache Text-Extraktion (MVP: nur Paragraphen)
        # Entferne Scripts und Styles
        html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html_clean = re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
        
        # Extrahiere Text aus Paragraphen
        paragraphs = re.findall(r'<p[^>]*>([^<]+(?:<[^>]+>[^<]*)*)</p>', html_clean, re.IGNORECASE)
        text = ' '.join(re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 100:
            print(f"⚠️  Wenig Text extrahiert von {url}")
            return None
        
        domain = urlparse(url).netloc
        content_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        
        return Article(
            url=url,
            title=title,
            text=text[:5000],  # Limit für MVP
            source_domain=domain,
            extracted_at=datetime.now().isoformat(),
            content_hash=content_hash
        )
        
    except Exception as e:
        print(f"❌ Fehler bei Extraktion von {url}: {e}")
        return None

# ============================================================
# CLAIM-EXTRAKTION
# ============================================================

# Indikatoren für prüfbare Fakten-Claims
CLAIM_INDICATORS = [
    r'\b\d+(?:\.\d+)?(?:\s*(?:prozent|%|millionen|milliarden|euro|dollar))',
    r'\b(?:studie|forschung|wissenschaftler|experten)\s+(?:zeigt|belegt|beweist)',
    r'\b(?:laut|nach angaben|gemäß)\s+[A-Z]',
    r'\b(?:ist|war|wurde|hat)\s+(?:der|die|das)\s+(?:erste|größte|kleinste|beste)',
    r'\b(?:immer|nie|alle|keine|jeder)\b',
    r'\b(?:offiziell|bestätigt|verkündet|ankündigt)',
]

def extract_claims(article: Article) -> list[Claim]:
    """
    Extrahiert prüfbare Fakten-Claims aus einem Artikel.
    MVP: Regelbasierte Heuristik. Später erweiterbar mit ClaimBuster/LLM.
    """
    claims = []
    sentences = re.split(r'[.!?]+', article.text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        
        # Längenfilter
        if len(sentence) < CONFIG["MIN_CLAIM_LENGTH"]:
            continue
        if len(sentence) > CONFIG["MAX_CLAIM_LENGTH"]:
            continue
            
        # Prüfe auf Claim-Indikatoren
        claim_score = 0
        for pattern in CLAIM_INDICATORS:
            if re.search(pattern, sentence, re.IGNORECASE):
                claim_score += 1
        
        # Mindestens 1 Indikator für MVP
        if claim_score >= 1:
            confidence = min(0.3 + (claim_score * 0.2), 0.9)
            claims.append(Claim(
                text=sentence,
                source_article_url=article.url,
                extraction_method="rule_based_v1",
                confidence=confidence
            ))
    
    return claims

# ============================================================
# FACT-CHECK API INTEGRATION
# ============================================================

def check_google_factcheck(claim_text: str) -> dict:
    """
    Prüft einen Claim gegen die Google Fact Check Tools API.
    Kostenlos, aber Rate-Limited.
    """
    result = {
        "found": False,
        "rating": None,
        "source": None,
        "url": None
    }
    
    api_key = CONFIG["GOOGLE_FACTCHECK_API_KEY"]
    
    # API funktioniert auch ohne Key (mit niedrigerem Limit)
    params = {"query": claim_text[:200], "languageCode": "de"}
    if api_key and api_key != "YOUR_API_KEY_HERE":
        params["key"] = api_key
    
    try:
        response = requests.get(
            CONFIG["GOOGLE_FACTCHECK_URL"],
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            claims = data.get("claims", [])
            
            if claims:
                # Nehme den ersten/besten Match
                best_match = claims[0]
                review = best_match.get("claimReview", [{}])[0]
                
                result["found"] = True
                result["rating"] = review.get("textualRating", "Unbekannt")
                result["source"] = review.get("publisher", {}).get("name", "Unbekannt")
                result["url"] = review.get("url", "")
                
    except Exception as e:
        print(f"⚠️  Fact-Check API Fehler: {e}")
    
    return result

# ============================================================
# SCORING & RISIKOBEWERTUNG
# ============================================================

# Bekannte unzuverlässige Domains (MVP: kleine Liste, erweiterbar)
UNRELIABLE_DOMAINS = [
    "rt.com", "sputniknews", "epochtimes", "breitbart",
    "infowars", "naturalnews", "beforeitsnews"
]

def calculate_risk_score(claim: Claim, factcheck_result: dict, source_domain: str) -> tuple[float, str]:
    """
    Berechnet einen Risiko-Score für einen Claim.
    
    Faktoren:
    - Bereits debunked? → Hohes Risiko
    - Quelle bekannt unzuverlässig? → Erhöhtes Risiko
    - Extreme Sprache (alle, nie, etc.)? → Leicht erhöhtes Risiko
    """
    score = 0.0
    
    # Faktor 1: Existierender Fact-Check
    if factcheck_result["found"]:
        rating = (factcheck_result["rating"] or "").lower()
        if any(w in rating for w in ["falsch", "false", "pants on fire", "unbelegt", "irreführend", "misleading"]):
            score += 0.5
        elif any(w in rating for w in ["wahr", "true", "correct", "richtig"]):
            score -= 0.2  # Bestätigter Fakt = niedriges Risiko
    
    # Faktor 2: Quellen-Reputation
    for domain in UNRELIABLE_DOMAINS:
        if domain in source_domain.lower():
            score += 0.3
            break
    
    # Faktor 3: Extreme Sprache
    extreme_words = ["immer", "nie", "alle", "keine", "jeder", "niemand", "100%", "garantiert"]
    for word in extreme_words:
        if word.lower() in claim.text.lower():
            score += 0.05
    
    # Normalisiere auf 0-1
    score = max(0, min(1, score))
    
    # Kategorisierung
    if score >= CONFIG["HIGH_RISK_THRESHOLD"]:
        category = "🔴 HOHES RISIKO"
    elif score >= CONFIG["MEDIUM_RISK_THRESHOLD"]:
        category = "🟡 PRÜFEN"
    else:
        category = "🟢 NIEDRIG"
    
    return score, category

# ============================================================
# PIPELINE ORCHESTRIERUNG
# ============================================================

def process_url(url: str) -> list[FactCheckResult]:
    """Verarbeitet eine einzelne URL durch die komplette Pipeline."""
    results = []
    
    print(f"\n{'='*60}")
    print(f"📰 Verarbeite: {url}")
    print(f"{'='*60}")
    
    # Schritt 1: Artikel extrahieren
    article = extract_article(url)
    if not article:
        print("❌ Artikel-Extraktion fehlgeschlagen")
        return results
    
    print(f"✅ Titel: {article.title[:60]}...")
    print(f"   Text: {len(article.text)} Zeichen")
    
    # Schritt 2: Claims extrahieren
    claims = extract_claims(article)
    print(f"✅ {len(claims)} prüfbare Claims gefunden")
    
    if not claims:
        print("ℹ️  Keine prüfbaren Claims identifiziert")
        return results
    
    # Schritt 3: Jeden Claim prüfen
    for i, claim in enumerate(claims[:10], 1):  # Limit 10 Claims pro Artikel (MVP)
        print(f"\n   Claim {i}: \"{claim.text[:50]}...\"")
        
        # Fact-Check API
        fc_result = check_google_factcheck(claim.text)
        
        # Scoring
        risk_score, risk_category = calculate_risk_score(
            claim, fc_result, article.source_domain
        )
        
        result = FactCheckResult(
            claim_text=claim.text,
            source_url=url,
            has_existing_factcheck=fc_result["found"],
            factcheck_rating=fc_result["rating"],
            factcheck_source=fc_result["source"],
            factcheck_url=fc_result["url"],
            risk_score=round(risk_score, 2),
            risk_category=risk_category,
            checked_at=datetime.now().isoformat()
        )
        results.append(result)
        
        # Output
        if fc_result["found"]:
            print(f"      → Fact-Check gefunden: {fc_result['rating']} ({fc_result['source']})")
        print(f"      → Risiko: {risk_category} ({risk_score:.0%})")
    
    return results

def run_pipeline(urls: list[str], output_file: str = "results.csv"):
    """Führt die Pipeline für mehrere URLs aus und speichert Ergebnisse."""
    all_results = []
    
    print("\n" + "="*60)
    print("🔍 FAKE NEWS DETECTION PIPELINE - MVP")
    print("="*60)
    print(f"📋 {len(urls)} URLs zu prüfen")
    
    for url in urls:
        results = process_url(url)
        all_results.extend(results)
    
    # Ergebnisse speichern
    if all_results:
        # CSV Export
        csv_file = output_file
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(all_results[0]).keys())
            writer.writeheader()
            for result in all_results:
                writer.writerow(asdict(result))
        
        # JSON Export
        json_file = output_file.replace('.csv', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(r) for r in all_results], f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print("📊 ZUSAMMENFASSUNG")
        print(f"{'='*60}")
        print(f"✅ {len(all_results)} Claims geprüft")
        
        high_risk = sum(1 for r in all_results if "HOHES" in r.risk_category)
        medium_risk = sum(1 for r in all_results if "PRÜFEN" in r.risk_category)
        low_risk = sum(1 for r in all_results if "NIEDRIG" in r.risk_category)
        
        print(f"   🔴 Hohes Risiko: {high_risk}")
        print(f"   🟡 Prüfen: {medium_risk}")
        print(f"   🟢 Niedrig: {low_risk}")
        print(f"\n💾 Ergebnisse gespeichert:")
        print(f"   → {csv_file}")
        print(f"   → {json_file}")
    
    return all_results

# ============================================================
# DEMO / HAUPTPROGRAMM
# ============================================================

if __name__ == "__main__":
    # Demo-URLs (ersetze mit echten URLs)
    demo_urls = [
        # Hier URLs einfügen zum Testen
        # "https://example.com/news-article",
    ]
    
    if demo_urls:
        results = run_pipeline(demo_urls, "fake_news_results.csv")
    else:
        print("""
╔══════════════════════════════════════════════════════════════╗
║         FAKE NEWS DETECTION PIPELINE - MVP                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Nutzung:                                                    ║
║  1. Füge URLs in demo_urls Liste ein, oder                   ║
║  2. Importiere und nutze als Modul:                          ║
║                                                              ║
║     from main import run_pipeline                            ║
║     results = run_pipeline(["https://..."], "output.csv")    ║
║                                                              ║
║  3. Oder nutze das CLI-Interface (cli.py)                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
