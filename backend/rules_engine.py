from urllib.parse import urlparse
import re
import socket
import datetime
import whois
from functools import lru_cache


WHITELIST_DOMAINS = {
    "google.com", "www.google.com",
    "microsoft.com", "www.microsoft.com",
    "login.microsoftonline.com",
    "facebook.com", "www.facebook.com",
    "amazon.com", "www.amazon.com",
    "github.com", "www.github.com",
    "youtube.com", "www.youtube.com",
    "twitter.com", "x.com",
    "linkedin.com", "www.linkedin.com",
    "apple.com", "www.apple.com",
    "netflix.com", "www.netflix.com",
    "instagram.com", "www.instagram.com",
    "whatsapp.com", "www.whatsapp.com",
    "stackoverflow.com", "www.stackoverflow.com",
    "wikipedia.org", "www.wikipedia.org",
    "reddit.com", "www.reddit.com",
    "vercel.com", "vercel.app",
}

BLACKLIST_DOMAINS = {
    # add known bad domains here if you want
}

SUSPICIOUS_TLDS = {".ru", ".tk", ".cn", ".ga", ".ml", ".cf", ".gq"}

SUSPICIOUS_WORDS = [
    "login", "verify", "update", "secure", "account",
    "bank", "paypal", "confirm", "signin", "security",
    "free", "bonus", "win", "prize"
]

BRAND_DOMAINS = [
    "google.com", "microsoft.com", "paypal.com",
    "facebook.com", "apple.com", "amazon.com",
    "netflix.com", "outlook.com"
]


def get_domain_label(host: str) -> str:
    parts = host.split(".")
    if len(parts) >= 2:
        return parts[-2]
    return host


def levenshtein(a: str, b: str) -> int:
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if a[i-1] == b[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,
                dp[i][j-1] + 1,
                dp[i-1][j-1] + cost
            )
    return dp[m][n]

def get_host(url: str) -> str:
    if "://" not in url:
        url = "http://" + url
    return urlparse(url).netloc.lower()


def get_domain_name(host: str) -> str:
    parts = host.split(".")
    if len(parts) >= 2:
        return parts[-2] + "." + parts[-1]
    return host


@lru_cache(maxsize=5000)
def get_domain_age_days(domain: str):
    """
    Returns domain age in days using WHOIS.
    If lookup fails, returns None.
    """
    try:
        w = whois.whois(domain)
        created = w.creation_date

        if isinstance(created, list):
            created = created[0]

        if created is None:
            return None

        if isinstance(created, datetime.datetime):
            delta = datetime.datetime.utcnow() - created
        else:
            return None

        return delta.days
    except Exception:
        return None


@lru_cache(maxsize=5000)
def resolve_ip(host: str):
    try:
        return socket.gethostbyname(host)
    except Exception:
        return None


@lru_cache(maxsize=5000)
def get_ip_reputation_score(ip: str):
    """
    Placeholder: returns 0 (neutral).
    You can plug in any IP reputation API (AbuseIPDB, VirusTotal, etc.)
    """
    if ip is None:
        return 0
    return 0  # neutral for now


def looks_like_brand_homograph(host: str):
    label = get_domain_label(host)
    label_clean = label.replace("-", "").lower()

    for brand_full in BRAND_DOMAINS:
        brand_label = brand_full.split(".")[0]
        dist = levenshtein(label_clean, brand_label)

        if len(label_clean) == len(brand_label) and dist <= 2 and label_clean != brand_label:
            return True, brand_full

        if abs(len(label_clean) - len(brand_label)) == 1 and dist <= 1:
            return True, brand_full

    return False, ""


def is_idn_suspicious(host: str) -> bool:
    return any(label.startswith("xn--") for label in host.split("."))


def apply_rules(url: str):
    host = get_host(url)
    reasons = []
    score = 0
    decision = None

    # WHOIS domain age
    domain = get_domain_name(host)
    age_days = get_domain_age_days(domain)
    if age_days is not None:
        if age_days < 30:
            score += 30
            reasons.append(f"very young domain ({age_days} days old)")
        elif age_days < 180:
            score += 10
            reasons.append(f"newish domain ({age_days} days old)")

    # IP reputation
    ip = resolve_ip(host)
    rep_score = get_ip_reputation_score(ip)
    if rep_score >= 80:
        score += 40
        reasons.append(f"IP has very bad reputation (score {rep_score})")
    elif rep_score >= 50:
        score += 20
        reasons.append(f"IP has suspicious reputation (score {rep_score})")

    # WHITELIST
    if host in WHITELIST_DOMAINS or any(host.endswith("." + d) for d in WHITELIST_DOMAINS):
        return "benign", score, ["whitelisted trusted domain"]

    # BLACKLIST
    if host in BLACKLIST_DOMAINS:
        return "phishing", 100, ["blacklisted malicious domain"]

    # IDN HOMOGRAPH
    if is_idn_suspicious(host):
        score += 50
        reasons.append("IDN / Unicode homograph")

    # ASCII HOMOGRAPH
    suspicious, brand = looks_like_brand_homograph(host)
    if suspicious:
        score += 60
        reasons.append(f"homograph of {brand}")

    # IP URL
    if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", host):
        score += 30
        reasons.append("IP address used")

    # SUSPICIOUS TLD
    for tld in SUSPICIOUS_TLDS:
        if host.endswith(tld):
            score += 20
            reasons.append(f"suspicious TLD {tld}")
            break

    # LONG URL
    if len(url) > 100:
        score += 20
        reasons.append("very long URL")

    # SUSPICIOUS WORDS
    lower_url = url.lower()
    found_words = [w for w in SUSPICIOUS_WORDS if w in lower_url]
    if found_words:
        score += 10 + len(found_words) * 2
        reasons.append("suspicious words: " + ", ".join(found_words))

    score = min(score, 100)

    if score >= 70:
        decision = "phishing"

    return decision, score, reasons
