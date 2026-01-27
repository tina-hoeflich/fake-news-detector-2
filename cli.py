#!/usr/bin/env python3
"""
Fake News Detection - Command Line Interface
=============================================
Einfaches CLI für die MVP Pipeline.

Nutzung:
    python cli.py https://example.com/article
    python cli.py --file urls.txt
    python cli.py --file urls.txt --output results.csv
"""

import argparse
import sys
from main import run_pipeline, process_url, extract_article, extract_claims

def main():
    parser = argparse.ArgumentParser(
        description="🔍 Fake News Detection Pipeline - MVP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python cli.py https://example.com/news-article
  python cli.py --file urls.txt --output meine_results.csv
  python cli.py --analyze https://example.com/article
        """
    )
    
    parser.add_argument(
        'url',
        nargs='?',
        help='URL eines Artikels zum Prüfen'
    )
    
    parser.add_argument(
        '--file', '-f',
        help='Textdatei mit URLs (eine pro Zeile)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='fake_news_results.csv',
        help='Output-Dateiname (default: fake_news_results.csv)'
    )
    
    parser.add_argument(
        '--analyze', '-a',
        action='store_true',
        help='Zeige detaillierte Analyse (nur Extraktion, kein Fact-Check)'
    )
    
    args = parser.parse_args()
    
    # Sammle URLs
    urls = []
    
    if args.url:
        urls.append(args.url)
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                urls.extend(file_urls)
        except FileNotFoundError:
            print(f"❌ Datei nicht gefunden: {args.file}")
            sys.exit(1)
    
    if not urls:
        parser.print_help()
        print("\n⚠️  Bitte mindestens eine URL angeben!")
        sys.exit(1)
    
    # Nur Analyse-Modus
    if args.analyze:
        for url in urls:
            print(f"\n{'='*60}")
            print(f"📰 Analysiere: {url}")
            print(f"{'='*60}")
            
            article = extract_article(url)
            if article:
                print(f"\n📄 Titel: {article.title}")
                print(f"🌐 Domain: {article.source_domain}")
                print(f"📝 Text-Länge: {len(article.text)} Zeichen")
                print(f"#️⃣  Hash: {article.content_hash}")
                
                claims = extract_claims(article)
                print(f"\n🎯 {len(claims)} Claims gefunden:")
                for i, claim in enumerate(claims, 1):
                    print(f"\n   [{i}] (Confidence: {claim.confidence:.0%})")
                    print(f"       \"{claim.text}\"")
            else:
                print("❌ Extraktion fehlgeschlagen")
        return
    
    # Vollständige Pipeline
    results = run_pipeline(urls, args.output)
    
    if not results:
        print("\n⚠️  Keine Ergebnisse generiert")
        sys.exit(1)

if __name__ == "__main__":
    main()
