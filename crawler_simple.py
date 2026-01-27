#!/usr/bin/env python3
"""
Fake News Crawler - Serverless Version
======================================
Läuft als GitHub Action, speichert Ergebnisse als JSON/CSV.
Keine Datenbank nötig - alles in Dateien.
"""

import os
import json
import csv
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import requests

# ============================================================
# CONFIG
# ============================================================

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

GDELT_LANGUAGES = ["german", "english"]
MAX_ARTICLES = 30

CLAIM_INDICATORS = [
    r'\b\d+(?:\.\d+)?(?:\s*(?:prozent|%|millionen|milliarden|euro|dollar))',
    r'\b(?:studie|forschung|wissenschaftler|experten)\s+(?:zeigt|belegt|beweist)',
    r'\b(?:laut|nach angaben|gemäß)\s+[A-Z]',
    r'\b(?:immer|nie|alle|keine|jeder)\b',
    r'\b(?:offiziell|bestätigt|verkündet)',
]

UNRELIABLE_DOMAINS = [
    "rt.com", "sputniknews", "epochtimes", "breitbart",
    "infowars", "naturalnews", "beforeitsnews"
]

# ============================================================
# CRAWLERS
# ============================================================

def crawl_gdelt(languages=None, max_articles=30):
    """Fetch articles from GDELT DOC 2.0 API."""
    articles = []
    
    # GDELT verwendet sourcelang Parameter mit spezifischen Codes
    # Siehe: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
    lang_configs = [
        {"code": "german", "query": "politik OR regierung OR wirtschaft"},
        {"code": "english", "query": "politics OR government OR economy"},
    ]
    
    for config in lang_configs:
        try:
            # GDELT DOC 2.0 API URL-Struktur
            # Der Query muss ein Keyword enthalten UND sourcelang als Teil des Query
            query = f"{config['query']} sourcelang:{config['code']}"
            
            url = "https://api.gdeltproject.org/api/v2/doc/doc"
            params = {
                "query": query,
                "mode": "artlist",
                "maxrecords": max_articles,
                "timespan": "24h",
                "format": "json",
                "sort": "datedesc"
            }
            
            response = requests.get(
                url,
                params=params,
                timeout=30,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json"
                }
            )
            
            # Debug: Print URL und Status
            print(f"  GDELT [{config['code']}] Status: {response.status_code}")
            
            if response.status_code == 200:
                text = response.text.strip()
                if text and text.startswith('{'):
                    data = response.json()
                    article_list = data.get("articles", [])
                    for article in article_list:
                        articles.append({
                            "url": article.get("url"),
                            "title": article.get("title"),
                            "domain": article.get("domain"),
                            "language": config["code"],
                            "seen_date": article.get("seendate")
                        })
                    print(f"✅ GDELT [{config['code']}]: {len(article_list)} articles")
                else:
                    print(f"⚠️ GDELT [{config['code']}]: Non-JSON response")
            else:
                print(f"⚠️ GDELT [{config['code']}]: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⚠️ GDELT [{config['code']}]: Timeout")
        except Exception as e:
            print(f"❌ GDELT [{config['code']}] error: {type(e).__name__}: {e}")
    
    return articles


def crawl_rss_feeds():
    """Fetch articles from public RSS feeds as fallback."""
    feeds = [
        # German
        ("https://www.tagesschau.de/index~rss2.xml", "german"),
        ("https://www.spiegel.de/schlagzeilen/index.rss", "german"),
        ("https://www.zeit.de/news/index", "german"),
        # English
        ("https://feeds.bbci.co.uk/news/rss.xml", "english"),
        ("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "english"),
        ("https://feeds.reuters.com/reuters/topNews", "english"),
    ]
    
    articles = []
    
    for feed_url, lang in feeds:
        try:
            response = requests.get(
                feed_url, 
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}
            )
            
            if response.status_code != 200:
                continue
            
            # Simple RSS parsing without external library
            import re
            items = re.findall(r'<item>(.*?)</item>', response.text, re.DOTALL)
            
            count = 0
            for item in items[:10]:  # Max 10 per feed
                title_match = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item)
                link_match = re.search(r'<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>', item)
                
                if title_match and link_match:
                    url = link_match.group(1).strip()
                    title = title_match.group(1).strip()
                    
                    # Clean CDATA and HTML
                    title = re.sub(r'<[^>]+>', '', title)
                    
                    if url and title:
                        domain = url.split('/')[2] if '/' in url else ""
                        articles.append({
                            "url": url,
                            "title": title,
                            "domain": domain,
                            "language": lang
                        })
                        count += 1
            
            if count > 0:
                print(f"✅ RSS [{feed_url.split('/')[2]}]: {count} articles")
                
        except Exception as e:
            print(f"⚠️ RSS error for {feed_url[:30]}: {e}")
    
    return articles


def extract_text(url):
    """Extract article text from URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; FakeNewsBot/1.0)"}
        response = requests.get(url, headers=headers, timeout=15)
        html = response.text
        
        # Title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
        title = title_match.group(1).strip() if title_match else ""
        
        # Clean
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.I)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.I)
        
        # Paragraphs
        paragraphs = re.findall(r'<p[^>]*>([^<]+(?:<[^>]+>[^<]*)*)</p>', html, re.I)
        text = ' '.join(re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return {"title": title, "text": text[:3000]} if len(text) > 100 else None
    except:
        return None


def extract_claims(text):
    """Extract checkable claims from text."""
    claims = []
    for sentence in re.split(r'[.!?]+', text):
        sentence = sentence.strip()
        if 30 < len(sentence) < 250:
            score = sum(1 for p in CLAIM_INDICATORS if re.search(p, sentence, re.I))
            if score >= 1:
                claims.append({
                    "text": sentence,
                    "confidence": min(0.3 + score * 0.2, 0.9)
                })
    return claims


def check_factcheck_api(claim_text):
    """Check against Google Fact Check API."""
    api_key = os.getenv("GOOGLE_FACTCHECK_API_KEY", "")
    result = {"found": False, "rating": None, "source": None, "url": None}
    
    try:
        params = {"query": claim_text[:200], "languageCode": "de"}
        if api_key:
            params["key"] = api_key
        
        response = requests.get(
            "https://factchecktools.googleapis.com/v1alpha1/claims:search",
            params=params, timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("claims"):
                review = data["claims"][0].get("claimReview", [{}])[0]
                result = {
                    "found": True,
                    "rating": review.get("textualRating"),
                    "source": review.get("publisher", {}).get("name"),
                    "url": review.get("url")
                }
    except:
        pass
    
    return result


def calculate_risk(claim_text, factcheck, domain):
    """Calculate risk score."""
    score = 0.0
    
    if factcheck["found"]:
        rating = (factcheck["rating"] or "").lower()
        if any(w in rating for w in ["falsch", "false", "irreführend", "misleading"]):
            score += 0.5
        elif any(w in rating for w in ["wahr", "true"]):
            score -= 0.2
    
    if any(d in (domain or "").lower() for d in UNRELIABLE_DOMAINS):
        score += 0.3
    
    if any(w in claim_text.lower() for w in ["immer", "nie", "alle", "keine", "100%"]):
        score += 0.1
    
    score = max(0, min(1, score))
    
    if score >= 0.7:
        return score, "HIGH"
    elif score >= 0.4:
        return score, "MEDIUM"
    return score, "LOW"


# ============================================================
# MAIN
# ============================================================

def main():
    print(f"\n{'='*60}")
    print(f"🔍 FAKE NEWS CRAWLER - {datetime.utcnow().isoformat()}")
    print(f"{'='*60}\n")
    
    # 1. Crawl from multiple sources
    articles = []
    
    # Try GDELT first
    print("📡 Trying GDELT...")
    gdelt_articles = crawl_gdelt()
    articles.extend(gdelt_articles)
    
    # Always also try RSS feeds for reliability
    print("\n📡 Fetching RSS feeds...")
    rss_articles = crawl_rss_feeds()
    articles.extend(rss_articles)
    
    # Deduplicate by URL
    seen_urls = set()
    unique_articles = []
    for a in articles:
        if a["url"] not in seen_urls:
            seen_urls.add(a["url"])
            unique_articles.append(a)
    articles = unique_articles
    
    print(f"\n📰 Total unique articles: {len(articles)}")
    
    if len(articles) == 0:
        print("⚠️ No articles found from any source!")
        # Save empty results anyway
        with open(RESULTS_DIR / "latest.json", "w") as f:
            json.dump([], f)
        return
    
    # 2. Process
    results = []
    processed = 0
    
    for article in articles[:20]:  # Limit for free tier
        url = article["url"]
        domain = article.get("domain", "")
        
        extracted = extract_text(url)
        if not extracted:
            continue
        
        claims = extract_claims(extracted["text"])
        
        for claim in claims[:3]:  # Max 3 claims per article
            fc = check_factcheck_api(claim["text"])
            risk_score, risk_category = calculate_risk(claim["text"], fc, domain)
            
            results.append({
                "claim": claim["text"],
                "source_url": url,
                "source_domain": domain,
                "article_title": extracted["title"][:100],
                "risk_score": round(risk_score, 2),
                "risk_category": risk_category,
                "has_factcheck": fc["found"],
                "factcheck_rating": fc["rating"],
                "factcheck_source": fc["source"],
                "checked_at": datetime.utcnow().isoformat()
            })
        
        processed += 1
        print(f"  ✓ {processed}/{min(20, len(articles))}: {domain}")
    
    # 3. Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    
    # JSON
    json_path = RESULTS_DIR / f"results_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # CSV
    csv_path = RESULTS_DIR / f"results_{timestamp}.csv"
    if results:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    # Latest (für einfachen Zugriff)
    with open(RESULTS_DIR / "latest.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Summary
    high = sum(1 for r in results if r["risk_category"] == "HIGH")
    medium = sum(1 for r in results if r["risk_category"] == "MEDIUM")
    low = sum(1 for r in results if r["risk_category"] == "LOW")
    
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"  Articles processed: {processed}")
    print(f"  Claims analyzed: {len(results)}")
    print(f"  🔴 High risk: {high}")
    print(f"  🟡 Medium risk: {medium}")
    print(f"  🟢 Low risk: {low}")
    print(f"\n  💾 Saved to: {json_path}")
    
    # Print high-risk claims
    if high > 0:
        print(f"\n⚠️  HIGH RISK CLAIMS:")
        for r in results:
            if r["risk_category"] == "HIGH":
                print(f"  • \"{r['claim'][:80]}...\"")
                print(f"    Source: {r['source_domain']}")


if __name__ == "__main__":
    main()
