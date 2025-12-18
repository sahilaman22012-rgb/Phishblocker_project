import joblib
import pandas as pd
from urllib.parse import urlparse
import re
import os
import threading
import logging


from rules_engine import apply_rules


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

# Get the directory where this script is located
_model_lock = threading.Lock()
logger = logging.getLogger(__name__)

def load_model():
    global bundle, scaler, rf_model, gb_model, dnn_model, label_encoder

    # Double-checked locking
    if bundle is not None:
        return

    with _model_lock:
        if bundle is not None:
            return
        if not os.path.exists("phish_url_model.joblib"):
            raise FileNotFoundError(f"Model file not found at {"phish_url_model.joblib"}")
        try:
            bundle_local = joblib.load("phish_url_model.joblib")
        except Exception as e:
            logger.exception("Failed to load model bundle")
            raise

        # assign to globals
        bundle = bundle_local
        logger.info("Loaded model bundle keys: %s", list(bundle.keys()))

        # required keys: scaler, rf, gb, dnn, label_encoder
        scaler = bundle.get("scaler")
        rf_model = bundle.get("rf")
        gb_model = bundle.get("gb")
        dnn_model = bundle.get("dnn")
        label_encoder = bundle.get("label_encoder")

        # optional: feature names saved when training (recommended)
        # e.g., bundle['feature_names'] = ['url_length', 'host_length', ...]
        # If present use that ordering when creating DataFrame for transform
        # We'll not assign here, but check in predict_url below



# ---------- 3. prediction function (rules + ensemble ML) ----------

def predict_url(url: str):
    # Ensure model is loaded
    load_model()

    # Run rules engine first
    rule_decision, rule_score, rule_reasons = apply_rules(url)

    # ensure reasons is a list we can append to without modifying caller's object
    reasons = list(rule_reasons) if rule_reasons else []

    if rule_decision is not None:
        # If rules were decisive return immediately, but ensure reasons is list
        return rule_decision, float(rule_score) if rule_score is not None else 0.0, reasons

    # ML ensemble path
    feats = extract_features(url)

    # Build DataFrame using feature_name order if available in bundle
    X_new = pd.DataFrame([feats])
    # If the model bundle stored feature names, reorder to that exact order
    feature_names = bundle.get("feature_names") if bundle is not None else None
    if feature_names:
        # ensure all feature_names exist in X_new, fill missing with 0
        for fn in feature_names:
            if fn not in X_new.columns:
                X_new[fn] = 0
        X_new = X_new[feature_names]
    # else rely on DataFrame order (must match training)

    try:
        X_scaled = scaler.transform(X_new)
    except Exception as e:
        logger.exception("Scaler transform failed")
        raise

    # Get probabilities from each model
    probs_rf = rf_model.predict_proba(X_scaled)[0]
    probs_gb = gb_model.predict_proba(X_scaled)[0]
    probs_dnn = dnn_model.predict_proba(X_scaled)[0]

    # Ensure we map each model's probabilities to the same class order
    # Use label_encoder.classes_ as canonical order if available
    canonical_classes = list(label_encoder.classes_) if label_encoder is not None else None

    def align_probs(model, probs):
        """
        If model has attribute classes_ (sklearn models do), map its probs into
        the canonical_classes order. If can't, assume probs are already aligned.
        """
        try:
            model_classes = list(model.classes_)
            if canonical_classes and model_classes != canonical_classes:
                # build mapping
                mapped = [0.0] * len(canonical_classes)
                for i, cls in enumerate(model_classes):
                    if cls in canonical_classes:
                        idx = canonical_classes.index(cls)
                        mapped[idx] = probs[i]
                return mapped
        except Exception:
            pass
        return probs

    aligned_rf = align_probs(rf_model, probs_rf)
    aligned_gb = align_probs(gb_model, probs_gb)
    aligned_dnn = align_probs(dnn_model, probs_dnn)

    import numpy as np
    ensemble_probs = (np.array(aligned_rf) + np.array(aligned_gb) + np.array(aligned_dnn)) / 3.0

    # Determine final label using label_encoder canonical mapping
    top_idx = int(np.argmax(ensemble_probs))
    if label_encoder is not None:
        final_label = label_encoder.inverse_transform([top_idx])[0]
    else:
        final_label = str(top_idx)

    # safe phishing index lookup
    phishing_prob = 0.0
    if canonical_classes and "phishing" in canonical_classes:
        phishing_idx = canonical_classes.index("phishing")
        phishing_prob = float(ensemble_probs[phishing_idx])
    else:
        # fallback: if classes not found, treat 'phishing' as index 1 if binary, else use top index
        if len(ensemble_probs) == 2:
            phishing_prob = float(ensemble_probs[1])
        else:
            phishing_prob = float(ensemble_probs[top_idx])

    combined_score = phishing_prob * 100.0

    # append ML reasons to local reasons list
    reasons.append(f"Ensemble phishing probability = {phishing_prob:.2f}")
    reasons.append(f"Combined ML risk score = {combined_score:.1f}")

    return final_label, combined_score, reasons



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
                print("WARNING: This URL looks PHISHING.")
            else:
                print("This URL looks BENIGN / SAFE.")
        except Exception as e:
            print("Error predicting URL:", e)
