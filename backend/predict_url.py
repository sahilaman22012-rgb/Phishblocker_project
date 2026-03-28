import joblib
import pandas as pd
from urllib.parse import urlparse
import re

from rules_engine import apply_rules   # your rule book


# ---------- 1. feature extraction (MUST match train_phish_model.py) ----------

def extract_features(url: str) -> dict:
    if not isinstance(url, str):
        url = str(url)

    url = url.strip()

    try:
        to_parse = url if "://" in url else "http://" + url
        parsed = urlparse(to_parse)
    except ValueError:
        parsed = urlparse("http://invalid-url")

    host = parsed.netloc or ""
    path = parsed.path or ""

    url_len = len(url)
    host_len = len(host)
    path_len = len(path)

    count_dot = url.count(".")
    count_hyphen = url.count("-")
    count_at = url.count("@")
    count_qmark = url.count("?")
    count_percent = url.count("%")
    count_equal = url.count("=")
    count_slash = url.count("/")

    count_digits = sum(c.isdigit() for c in url)
    count_letters = sum(c.isalpha() for c in url)

    uses_https = 1 if parsed.scheme == "https" else 0
    has_ip = 1 if re.search(r"(\d{1,3}\.){3}\d{1,3}", host) else 0

    shortening_services = [
        "bit.ly", "goo.gl", "tinyurl.com", "ow.ly", "t.co",
        "is.gd", "buff.ly", "adf.ly"
    ]
    is_shortened = 1 if any(s in host for s in shortening_services) else 0

    suspicious_words = [
        "login", "verify", "update", "secure", "account", "bank",
        "free", "bonus", "paypal", "confirm", "signin", "security"
    ]
    url_lower = url.lower()
    count_suspicious_words = sum(word in url_lower for word in suspicious_words)

    digit_ratio = count_digits / url_len if url_len > 0 else 0
    letter_ratio = count_letters / url_len if url_len > 0 else 0
    special_chars = len([c for c in url if not c.isalnum()])
    special_ratio = special_chars / url_len if url_len > 0 else 0

    return {
        "url_length": url_len,
        "host_length": host_len,
        "path_length": path_len,
        "count_dot": count_dot,
        "count_hyphen": count_hyphen,
        "count_at": count_at,
        "count_question": count_qmark,
        "count_percent": count_percent,
        "count_equal": count_equal,
        "count_slash": count_slash,
        "count_digits": count_digits,
        "count_letters": count_letters,
        "uses_https": uses_https,
        "has_ip": has_ip,
        "is_shortened": is_shortened,
        "count_suspicious_words": count_suspicious_words,
        "digit_ratio": digit_ratio,
        "letter_ratio": letter_ratio,
        "special_ratio": special_ratio,
    }


# ---------- 2. load ensemble models & scaler ----------

bundle = joblib.load("phish_url_model.joblib")
print("Loaded model bundle keys:", bundle.keys())  # optional, for debugging

scaler = bundle["scaler"]
rf_model = bundle["rf"]
gb_model = bundle["gb"]
dnn_model = bundle["dnn"]
label_encoder = bundle["label_encoder"]


# ---------- 3. prediction function (rules + ensemble ML) ----------

def predict_url(url: str):
    # 1) RULE ENGINE FIRST (homograph, IDN, whitelist, domain age, etc.)
    rule_decision, rule_score, rule_reasons = apply_rules(url)

    if rule_decision is not None:
        # rules were confident enough to decide
        return rule_decision, rule_score, rule_reasons

    # 2) ML ENSEMBLE (RF + GB + DNN)
    feats = extract_features(url)
    X_new = pd.DataFrame([feats])
    X_scaled = scaler.transform(X_new)

    probs_gb = gb_model.predict_proba(X_scaled)[0]
    probs_dnn = dnn_model.predict_proba(X_scaled)[0]

    # simple average ensemble
    ensemble_probs = (probs_gb + probs_dnn) / 2.0

    top_idx = ensemble_probs.argmax()
    final_label = label_encoder.inverse_transform([top_idx])[0]

    classes = list(label_encoder.classes_)
    phishing_idx = classes.index("phishing")
    phishing_prob = ensemble_probs[phishing_idx]

    combined_score = phishing_prob * 100

    rule_reasons.append(f"Ensemble phishing probability = {phishing_prob:.2f}")
    rule_reasons.append(f"Combined ML risk score = {combined_score:.1f}")

    return final_label, combined_score, rule_reasons


# ---------- 4. CLI for manual testing ----------

if __name__ == "__main__":
    while True:
        url = input("\nEnter a URL (or 'q' to quit): ").strip()
        if url.lower() == "q":
            break
        try:
            label, score, reasons = predict_url(url)
            print(f"\nFinal prediction: {label}")
            print(f"Risk score: {score:.1f}")
            print("Reasons:")
            for r in reasons:
                print(" -", r)

            if label == "phishing":
                print("⚠️ WARNING: This URL looks PHISHING.")
            else:
                print("✅ This URL looks BENIGN / SAFE.")
        except Exception as e:
            print("Error predicting URL:", e)
