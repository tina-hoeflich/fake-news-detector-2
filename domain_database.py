# Fake News Domain Database
# ==========================
# Basiert auf akademischen Quellen:
# - OpenSources.co (Melissa Zimdars, Merrimack College)
# - Media Bias/Fact Check
# - PolitiFact
# - Snopes
# - FakeNewsCorpus (GitHub)
# - NELA-GT Dataset
#
# Kategorien:
# - fake: Komplett erfundene Inhalte
# - conspiracy: Verschwörungstheorien
# - unreliable: Unzuverlässig, schlechte Quellenarbeit
# - bias: Stark parteiisch/voreingenommen
# - clickbait: Reißerische Überschriften, dünner Inhalt
# - satire: Satire (aber oft missverstanden)
# - state: Staatlich kontrollierte Medien
# - junksci: Pseudowissenschaft
# - hate: Hassrede/Extremismus
# - aggregator: Content-Aggregatoren ohne eigene Redaktion

DOMAIN_DATABASE = {
    # ==========================================
    # FAKE NEWS (komplett erfunden)
    # ==========================================
    "fake": [
        "abcnews.com.co",
        "beforeitsnews.com",
        "civictribune.com",
        "denverguardian.com",
        "empirenews.net",
        "huzlers.com",
        "nationalreport.net",
        "newsexaminer.net",
        "newsbiscuit.com",
        "now8news.com",
        "prntly.com",
        "react365.com",
        "realorsatire.com",
        "thebostontribune.com",
        "thelastlineofdefense.org",
        "tmzhiphop.com",
        "usatoday.com.co",
        "uspoln.com",
        "worldnewsdailyreport.com",
        "yournewswire.com",
        "newspunch.com",  # formerly yournewswire
        "neonnettle.com",
        "awarenessact.com",
        "dailyworldupdate.com",
    ],
    
    # ==========================================
    # CONSPIRACY (Verschwörungstheorien)
    # ==========================================
    "conspiracy": [
        "infowars.com",
        "prisonplanet.com",
        "naturalnews.com",
        "globalresearch.ca",
        "activistpost.com",
        "collectiveevolution.com",
        "davidicke.com",
        "disclose.tv",
        "rense.com",
        "whatdoesitmean.com",
        "abovetopsecret.com",
        "vigilantcitizen.com",
        "zerohedge.com",
        "thefreethoughtproject.com",
        "intellihub.com",
        "newstarget.com",
        "humansarefree.com",
        "theeventchronicle.com",
        "stillnessinthestorm.com",
    ],
    
    # ==========================================
    # STATE MEDIA (Staatlich kontrolliert)
    # ==========================================
    "state": [
        "rt.com",
        "sputniknews.com",
        "tass.com",
        "ria.ru",
        "xinhuanet.com",
        "globaltimes.cn",
        "presstv.ir",
        "telesurtv.net",
        "almasdarnews.com",
        "southfront.org",
        "strategic-culture.org",
        "journal-neo.org",
        "veteranstoday.com",
    ],
    
    # ==========================================
    # UNRELIABLE (Unzuverlässig)
    # ==========================================
    "unreliable": [
        "bipartisanreport.com",
        "dailywire.com",
        "thegatewaypundit.com",
        "100percentfedup.com",
        "addictinginfo.com",
        "americannews.com",
        "conservativetribune.com",
        "dailycaller.com",
        "dcgazette.com",
        "endingthefed.com",
        "freedomdaily.com",
        "libertywriters.com",
        "madworldnews.com",
        "occupydemocrats.com",
        "palmerreport.com",
        "politicususa.com",
        "redstatewatcher.com",
        "rightwingnews.com",
        "usapoliticstoday.com",
        "westernjournalism.com",
        "youngcons.com",
    ],
    
    # ==========================================
    # EXTREME BIAS (Stark parteiisch)
    # ==========================================
    "bias": [
        "breitbart.com",
        "dailykos.com",
        "theblaze.com",
        "townhall.com",
        "redstate.com",
        "pjmedia.com",
        "hotair.com",
        "americanthinker.com",
        "frontpagemag.com",
        "wnd.com",
        "newsmax.com",
        "oann.com",
        "thefederalist.com",
        "twitchy.com",
        "ijr.com",
        "commondreams.org",
        "alternet.org",
        "truthout.org",
        "rawstory.com",
        "crooksandliars.com",
    ],
    
    # ==========================================
    # CLICKBAIT (Reißerisch)
    # ==========================================
    "clickbait": [
        "buzzfeed.com",
        "viralnova.com",
        "distractify.com",
        "upworthy.com",
        "hefty.co",
        "dailybuzzlive.com",
        "boredomtherapy.com",
        "faithit.com",
        "shareably.net",
        "inspiremore.com",
    ],
    
    # ==========================================
    # JUNK SCIENCE (Pseudowissenschaft)
    # ==========================================
    "junksci": [
        "naturalnews.com",
        "greenmedinfo.com",
        "mercola.com",
        "healthnutnews.com",
        "wakingtimes.com",
        "collective-evolution.com",
        "thehealthyhomeeconomist.com",
        "foodbabe.com",
        "realfarmacy.com",
        "preventdisease.com",
        "healthimpactnews.com",
    ],
    
    # ==========================================
    # HATE / EXTREMISM
    # ==========================================
    "hate": [
        "dailystormer.su",
        "vdare.com",
        "amren.com",
        "stormfront.org",
        "jihadwatch.org",
        "barenakedislam.com",
        "pamelageller.com",
    ],
    
    # ==========================================
    # SATIRE (oft missverstanden)
    # ==========================================
    "satire": [
        "theonion.com",
        "clickhole.com",
        "babylonbee.com",
        "borowitz-report.com",
        "dailycurrant.com",
        "duffelblog.com",
        "empiresports.co",
        "faking-news.com",
        "gomerblog.com",
        "huzlers.com",
        "nationalreport.net",
        "newsthump.com",
        "private-eye.co.uk",
        "reductress.com",
        "rockcitytimes.com",
        "satirewire.com",
        "thelapine.ca",
        "waterfordwhispersnews.com",
    ],
    
    # ==========================================
    # CONTENT AGGREGATORS (keine eigene Redaktion)
    # ==========================================
    "aggregator": [
        "bignewsnetwork.com",
        "northkoreatimes.com",
        "koaborea.com",
        "maborea.com",
        "newkerala.com",
        "menafn.com",
        "timesnewswire.com",
        "webindia123.com",
        "thestatesman.net",
        "morningstaronline.co.uk",
    ],
}

# Flat lists für einfachen Zugriff
FAKE_DOMAINS = DOMAIN_DATABASE["fake"]
CONSPIRACY_DOMAINS = DOMAIN_DATABASE["conspiracy"]
STATE_MEDIA_DOMAINS = DOMAIN_DATABASE["state"]
UNRELIABLE_DOMAINS = DOMAIN_DATABASE["unreliable"]
BIASED_DOMAINS = DOMAIN_DATABASE["bias"]
CLICKBAIT_DOMAINS = DOMAIN_DATABASE["clickbait"]
JUNKSCI_DOMAINS = DOMAIN_DATABASE["junksci"]
HATE_DOMAINS = DOMAIN_DATABASE["hate"]
SATIRE_DOMAINS = DOMAIN_DATABASE["satire"]
AGGREGATOR_DOMAINS = DOMAIN_DATABASE["aggregator"]

# Kombinierte Listen nach Risiko-Level
HIGH_RISK_DOMAINS = (
    FAKE_DOMAINS + 
    CONSPIRACY_DOMAINS + 
    STATE_MEDIA_DOMAINS + 
    HATE_DOMAINS
)

MEDIUM_RISK_DOMAINS = (
    UNRELIABLE_DOMAINS + 
    BIASED_DOMAINS + 
    CLICKBAIT_DOMAINS + 
    JUNKSCI_DOMAINS +
    AGGREGATOR_DOMAINS
)

# Satire separat - nicht unbedingt "fake", aber oft missverstanden
SATIRE_RISK_DOMAINS = SATIRE_DOMAINS


def get_domain_risk(domain: str) -> tuple[float, str, str]:
    """
    Berechnet Risiko-Score basierend auf Domain.
    
    Returns:
        tuple: (score_boost, risk_level, category)
    """
    domain_lower = domain.lower()
    
    # Check HIGH risk
    for d in HIGH_RISK_DOMAINS:
        if d in domain_lower:
            # Bestimme Kategorie
            if d in FAKE_DOMAINS:
                return (0.6, "HIGH", "fake")
            elif d in HATE_DOMAINS:
                return (0.6, "HIGH", "hate")
            elif d in CONSPIRACY_DOMAINS:
                return (0.5, "HIGH", "conspiracy")
            elif d in STATE_MEDIA_DOMAINS:
                return (0.5, "HIGH", "state_media")
    
    # Check MEDIUM risk
    for d in MEDIUM_RISK_DOMAINS:
        if d in domain_lower:
            if d in JUNKSCI_DOMAINS:
                return (0.35, "MEDIUM", "junk_science")
            elif d in UNRELIABLE_DOMAINS:
                return (0.3, "MEDIUM", "unreliable")
            elif d in BIASED_DOMAINS:
                return (0.25, "MEDIUM", "biased")
            elif d in AGGREGATOR_DOMAINS:
                return (0.25, "MEDIUM", "aggregator")
            elif d in CLICKBAIT_DOMAINS:
                return (0.2, "MEDIUM", "clickbait")
    
    # Check SATIRE
    for d in SATIRE_RISK_DOMAINS:
        if d in domain_lower:
            return (0.15, "LOW", "satire")
    
    # Unknown domain
    return (0.0, "UNKNOWN", "unknown")


# Statistiken
if __name__ == "__main__":
    print("Domain Database Statistics")
    print("=" * 40)
    for category, domains in DOMAIN_DATABASE.items():
        print(f"{category:15} : {len(domains):4} domains")
    print("=" * 40)
    print(f"{'HIGH RISK':15} : {len(HIGH_RISK_DOMAINS):4} domains")
    print(f"{'MEDIUM RISK':15} : {len(MEDIUM_RISK_DOMAINS):4} domains")
    print(f"{'SATIRE':15} : {len(SATIRE_RISK_DOMAINS):4} domains")
    print(f"{'TOTAL':15} : {len(HIGH_RISK_DOMAINS) + len(MEDIUM_RISK_DOMAINS) + len(SATIRE_RISK_DOMAINS):4} domains")