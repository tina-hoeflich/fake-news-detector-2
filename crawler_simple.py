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
    # Known misinformation sources
    "rt.com", "sputniknews", "epochtimes", "breitbart",
    "infowars", "naturalnews", "beforeitsnews",
    # Content farms / Aggregator networks (Big News Network)
    "northkoreatimes.com", "northkoreaTimes.com",
    "bignewsnetwork.com",
    "newkerala.com",
    "menafn.com",
    # Low quality aggregators
    "newsbreak.com",
    "newsmax.com",
    # Clickbait farms
    "dailywire.com",
]

# Domains that should get MEDIUM risk (not outright unreliable, but questionable)
QUESTIONABLE_DOMAINS = [
    "bignewsnetwork",
    "northkoreatimes",
    "timesnewswire",
    "newsnetwork",
    "newswire",
]

# Try to import comprehensive domain database
try:
    from domain_database import get_domain_risk, HIGH_RISK_DOMAINS, MEDIUM_RISK_DOMAINS
    USE_DOMAIN_DB = True
    print("✅ Domain database loaded")
except ImportError:
    USE_DOMAIN_DB = False
    print("⚠️ Domain database not found, using basic list")

# ============================================================
# CRAWLERS
# ============================================================

def crawl_euvsdisinfo():
    """
    Fetch disinformation cases from EUvsDisinfo database.
    They have a public API endpoint for their cases.
    """
    articles = []
    
    try:
        # EUvsDisinfo has a JSON API for their database
        # Try their search endpoint
        api_url = "https://euvsdisinfo.eu/wp-json/api/v1/disinformation-cases"
        
        response = requests.get(
            api_url,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://euvsdisinfo.eu/disinformation-cases/"
            }
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                cases = data if isinstance(data, list) else data.get("cases", data.get("items", []))
                
                for case in cases[:30]:  # Max 30 cases
                    title = case.get("title", case.get("claim", ""))
                    url = case.get("url", case.get("link", ""))
                    
                    if title:
                        articles.append({
                            "url": url or f"https://euvsdisinfo.eu/disinformation-cases/",
                            "title": f"[DISINFO] {title}",
                            "domain": "euvsdisinfo.eu",
                            "language": "english",
                            "source_type": "factcheck",
                            "is_factcheck_article": True,
                            "verdict": "FALSE"  # EUvsDisinfo only lists disinformation
                        })
                
                if articles:
                    print(f"🔍 EUvsDisinfo API: {len(articles)} disinformation cases")
                    
            except Exception as e:
                print(f"⚠️ EUvsDisinfo JSON parse error: {e}")
        else:
            print(f"⚠️ EUvsDisinfo API: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ EUvsDisinfo error: {type(e).__name__}")
    
    return articles


def crawl_gdelt(languages=None, max_articles=30):
    """Fetch articles from GDELT DOC 2.0 API."""
    articles = []
    
    # GDELT: Suche nach kontroversen/viralen Themen wo Fake News häufig sind
    lang_configs = [
        {"code": "german", "query": "(fake OR falsch OR verschwörung OR skandal OR geheim)"},
        {"code": "english", "query": "(fake OR hoax OR conspiracy OR scandal OR secret OR shocking)"},
    ]
    
    for config in lang_configs:
        try:
            # GDELT DOC 2.0 API - sourcelang muss im Query sein
            query = f"{config['query']} sourcelang:{config['code']}"
            
            url = "https://api.gdeltproject.org/api/v2/doc/doc"
            params = {
                "query": query,
                "mode": "ArtList",  # Case-sensitive!
                "maxrecords": max_articles,
                "timespan": "24h",
                "format": "json",
                "sort": "DateDesc"
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
            
            print(f"  GDELT [{config['code']}] Status: {response.status_code}")
            
            if response.status_code == 200:
                text = response.text.strip()
                
                # Debug: Zeige erste 200 Zeichen der Response
                print(f"  Response preview: {text[:200]}...")
                
                if text.startswith('{') or text.startswith('['):
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
                elif "<!DOCTYPE" in text or "<html" in text.lower():
                    print(f"⚠️ GDELT [{config['code']}]: Got HTML instead of JSON (API may be overloaded)")
                else:
                    print(f"⚠️ GDELT [{config['code']}]: Unknown response format")
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
        # ===========================================
        # FACT-CHECKERS (bereits identifizierte Fake News!)
        # ===========================================
        # GERMAN
        ("https://correctiv.org/feed/", "german", "factcheck"),  # Enthält auch Faktenchecks
        ("https://www.mimikama.org/feed/", "german", "factcheck"),
        ("https://www.volksverpetzer.de/feed/", "german", "factcheck"),
        ("https://www.dpa.com/de/feed/", "german", "factcheck"),
        
        # ENGLISH
        ("https://www.snopes.com/feed/", "english", "factcheck"),
        ("https://www.politifact.com/rss/all/", "english", "factcheck"),
        ("https://fullfact.org/feed/", "english", "factcheck"),
        ("https://www.factcheck.org/feed/", "english", "factcheck"),
        ("https://leadstories.com/atom.xml", "english", "factcheck"),
        ("https://www.poynter.org/feed/", "english", "factcheck"),
        ("https://africacheck.org/feed/", "english", "factcheck"),
        
        # EU DISINFO (via their blog - actual cases are harder to scrape)
        ("https://euvsdisinfo.eu/feed/", "english", "factcheck"),
        
        # ===========================================
        # REGULAR NEWS (zum Vergleich)
        # ===========================================
        ("https://www.tagesschau.de/index~rss2.xml", "german", "mainstream"),
        ("https://www.spiegel.de/schlagzeilen/index.rss", "german", "mainstream"),
        ("https://feeds.bbci.co.uk/news/rss.xml", "english", "mainstream"),
        ("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "english", "mainstream"),
    ]
    
    articles = []
    
    for feed_url, lang, source_type in feeds:
        try:
            response = requests.get(
                feed_url, 
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/rss+xml, application/xml, text/xml, */*"
                }
            )
            
            if response.status_code != 200:
                print(f"⚠️ RSS [{feed_url.split('/')[2][:20]}]: HTTP {response.status_code}")
                continue
            
            # Simple RSS parsing without external library
            import re
            content = response.text
            
            # Try RSS format first
            items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
            
            # Also try Atom format
            if not items:
                items = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
            
            count = 0
            for item in items[:15]:  # Max 15 per feed
                # Title
                title_match = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item, re.DOTALL)
                
                # Link - try multiple formats
                link_match = re.search(r'<link>(?:<!\[CDATA\[)?(https?://[^<\]]+)(?:\]\]>)?</link>', item)
                if not link_match:
                    link_match = re.search(r'<link[^>]*href=["\']([^"\']+)["\']', item)
                if not link_match:
                    link_match = re.search(r'<guid[^>]*>(https?://[^<]+)</guid>', item)
                
                if title_match and link_match:
                    url = link_match.group(1).strip()
                    title = title_match.group(1).strip()
                    
                    # Clean CDATA and HTML tags
                    title = re.sub(r'<!\[CDATA\[|\]\]>', '', title)
                    title = re.sub(r'<[^>]+>', '', title)
                    title = title.strip()
                    
                    # Filter: Only include if it looks like a factcheck article
                    if source_type == "factcheck":
                        # Check if URL or title contains factcheck indicators
                        factcheck_keywords = [
                            "faktencheck", "fakten", "fact", "check", "falsch", "fake", 
                            "wahr", "true", "false", "debunk", "claim", "verify",
                            "stimmt", "mythos", "gerücht", "hoax", "misleading",
                            "disinformation", "misinformation"
                        ]
                        url_title_lower = (url + " " + title).lower()
                        is_factcheck = any(kw in url_title_lower for kw in factcheck_keywords)
                        
                        # For correctiv, check if it's from the faktencheck section
                        if "correctiv.org" in url:
                            is_factcheck = "/faktencheck/" in url
                    else:
                        is_factcheck = False
                    
                    if url and title and url.startswith('http'):
                        domain = url.split('/')[2] if len(url.split('/')) > 2 else ""
                        articles.append({
                            "url": url,
                            "title": title,
                            "domain": domain,
                            "language": lang,
                            "source_type": source_type if not is_factcheck else "factcheck",
                            "is_factcheck_article": is_factcheck
                        })
                        count += 1
            
            if count > 0:
                emoji = "🔍" if source_type == "factcheck" else "📰"
                print(f"{emoji} RSS [{feed_url.split('/')[2][:25]}]: {count} articles ({source_type})")
                
        except Exception as e:
            print(f"⚠️ RSS error for {feed_url.split('/')[2][:20]}: {type(e).__name__}")
    
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


def is_factcheck_article(url, domain):
    """Check if article is from a fact-checking source."""
    factcheck_domains = [
        "correctiv.org", "mimikama", "snopes.com", "politifact.com",
        "fullfact.org", "factcheck.org", "leadstories.com", "br.de/faktenfuchs",
        "dpa.com/faktencheck", "afp.com/fact", "reuters.com/fact"
    ]
    return any(fc in (domain or "").lower() or fc in (url or "").lower() for fc in factcheck_domains)


def extract_factcheck_verdict(text):
    """
    Extract verdict from fact-check article.
    Returns: (verdict, original_claim) or (None, None)
    """
    text_lower = text.lower()
    
    # German verdicts
    if any(w in text_lower for w in ["falsch", "fake", "erfunden", "irreführend", "manipuliert"]):
        return "FALSE", None
    elif any(w in text_lower for w in ["richtig", "wahr", "korrekt", "bestätigt"]):
        return "TRUE", None
    elif any(w in text_lower for w in ["teilweise", "halb wahr", "kontext fehlt"]):
        return "MIXED", None
    
    # English verdicts  
    if any(w in text_lower for w in ["false", "fake", "fabricated", "misleading", "pants on fire"]):
        return "FALSE", None
    elif any(w in text_lower for w in ["true", "correct", "confirmed"]):
        return "TRUE", None
    elif any(w in text_lower for w in ["partly", "half true", "missing context", "mixture"]):
        return "MIXED", None
    
    return None, None


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
    """Calculate risk score based on multiple factors."""
    score = 0.0
    category_info = None
    
    # Factor 1: Existing fact-check result
    if factcheck["found"]:
        rating = (factcheck["rating"] or "").lower()
        if any(w in rating for w in ["falsch", "false", "irreführend", "misleading", "pants on fire"]):
            score += 0.5
        elif any(w in rating for w in ["wahr", "true", "correct"]):
            score -= 0.2
    
    # Factor 2: Domain credibility (use database if available)
    if USE_DOMAIN_DB:
        domain_score, domain_risk, domain_category = get_domain_risk(domain or "")
        score += domain_score
        category_info = domain_category
    else:
        # Fallback to basic lists
        if any(d in (domain or "").lower() for d in UNRELIABLE_DOMAINS):
            score += 0.4
        if any(d in (domain or "").lower() for d in QUESTIONABLE_DOMAINS):
            score += 0.25
    
    # Factor 3: Extreme/absolute language
    extreme_words = [
        "immer", "nie", "alle", "keine", "100%", "garantiert", "beweis",
        "always", "never", "everyone", "nobody", "guaranteed", "exposed", "exposed"
    ]
    if any(w in claim_text.lower() for w in extreme_words):
        score += 0.1
    
    # Factor 4: Sensationalist language
    sensational_words = [
        "schock", "unglaublich", "skandal", "geheim", "enthüllt",
        "shocking", "unbelievable", "scandal", "secret", "revealed", "breaking"
    ]
    if any(w in claim_text.lower() for w in sensational_words):
        score += 0.05
    
    # Normalize score
    score = max(0, min(1, score))
    
    # Determine risk category
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
    
    # Try EUvsDisinfo first (most valuable - confirmed disinfo)
    print("📡 Trying EUvsDisinfo...")
    euvsdisinfo_articles = crawl_euvsdisinfo()
    articles.extend(euvsdisinfo_articles)
    
    # Try GDELT
    print("\n📡 Trying GDELT...")
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
    
    for article in articles[:200]:  # Process up to 

        url = article["url"]
        domain = article.get("domain", "")
        source_type = article.get("source_type", "unknown")
        
        extracted = extract_text(url)
        if not extracted:
            continue
        
        # Special handling for fact-check articles
        if source_type == "factcheck" or is_factcheck_article(url, domain):
            verdict, _ = extract_factcheck_verdict(extracted["text"])
            
            # For fact-checks, the article title often IS the debunked claim
            title = extracted.get("title", article.get("title", ""))
            
            if verdict == "FALSE":
                # This is a CONFIRMED fake news item!
                results.append({
                    "claim": f"[DEBUNKED] {title}",
                    "source_url": url,
                    "source_domain": domain,
                    "article_title": title[:100],
                    "risk_score": 0.9,  # High because confirmed false
                    "risk_category": "HIGH",
                    "has_factcheck": True,
                    "factcheck_rating": "FALSE - Debunked by fact-checkers",
                    "factcheck_source": domain,
                    "source_type": "factcheck",
                    "checked_at": datetime.utcnow().isoformat()
                })
                processed += 1
                print(f"  🚨 DEBUNKED: {domain} - {title[:50]}...")
                continue
        
        # Regular processing for non-factcheck articles
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
                "source_type": source_type,
                "checked_at": datetime.utcnow().isoformat()
            })
        
        processed += 1
        print(f"  ✓ {processed}/{min(50, len(articles))}: {domain}")
    
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
