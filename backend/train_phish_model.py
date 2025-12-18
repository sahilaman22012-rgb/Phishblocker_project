import pandas as pd
import re
from urllib.parse import urlparse

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib


# ---------- 1. Feature extraction (same style as before) ----------


def extract_features(url: str) -> dict:
    # 1) Make sure it's a string
    if not isinstance(url, str):
        url = str(url)

    url = url.strip()

    # 2) Try to parse safely
    try:
        # If no scheme, prepend http://
        to_parse = url if "://" in url else "http://" + url
        parsed = urlparse(to_parse)
    except ValueError:
        # If urlparse explodes (e.g., invalid IPv6), fall back to empty parts
        parsed = urlparse("http://invalid-url")
    
    host = parsed.netloc or ""
    path = parsed.path or ""

    # 3) Normal feature extraction from here ↓↓↓

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



# ---------- 2. Load & clean dataset ----------

csv_path = "malicious_phish.csv"
df = pd.read_csv(csv_path)

if "url" not in df.columns or "type" not in df.columns:
    raise ValueError("CSV must contain 'url' and 'type' columns.")

url_col = "url"
label_col = "type"

df = df[[url_col, label_col]].dropna()
df[label_col] = df[label_col].str.strip().str.lower()
df = df.drop_duplicates(subset=[url_col, label_col])

print("Label counts:")
print(df[label_col].value_counts())


# ---------- 3. Features + labels ----------

features_list = df[url_col].apply(extract_features).tolist()
X = pd.DataFrame(features_list)
y = df[label_col].astype(str)

print("\nFeature shape:", X.shape)

le = LabelEncoder()
y_enc = le.fit_transform(y)
print("\nClasses:", le.classes_)


# ---------- 4. Train / test split ----------

X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc,
    test_size=0.2,
    random_state=42,
    stratify=y_enc
)

# ---------- 5. Standardize features (for DNN) ----------

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


# ---------- 6. Define models: RF + Boosting + DNN (MLP) ----------

rf_clf = RandomForestClassifier(
    n_estimators=120,
    max_depth=18,
    min_samples_split=4,
    min_samples_leaf=2,
    class_weight="balanced",
    n_jobs=-1,
    random_state=42
)

gb_clf = GradientBoostingClassifier(
    n_estimators=150,
    learning_rate=0.1,
    max_depth=3,
    random_state=42
)

dnn_clf = MLPClassifier(
    hidden_layer_sizes=(64, 32),
    activation="relu",
    solver="adam",
    max_iter=40,        # keep low so it trains fast; increase if you want
    random_state=42
)


print("\nTraining RandomForest...")
rf_clf.fit(X_train_scaled, y_train)

print("Training GradientBoosting...")
gb_clf.fit(X_train_scaled, y_train)

print("Training DNN (MLP)...")
dnn_clf.fit(X_train_scaled, y_train)


# ---------- 7. Evaluate individual models ----------

def eval_model(name, model):
    print(f"\n=== {name} ===")
    y_pred = model.predict(X_test_scaled)
    y_pred_labels = le.inverse_transform(y_pred)
    y_test_labels = le.inverse_transform(y_test)
    print(classification_report(y_test_labels, y_pred_labels))


eval_model("RandomForest", rf_clf)
eval_model("GradientBoosting", gb_clf)
eval_model("DNN (MLP)", dnn_clf)


# ---------- 8. Ensemble evaluation (average probabilities) ----------

import numpy as np

probs_rf = rf_clf.predict_proba(X_test_scaled)
probs_gb = gb_clf.predict_proba(X_test_scaled)
probs_dnn = dnn_clf.predict_proba(X_test_scaled)

ensemble_probs = (probs_rf + probs_gb + probs_dnn) / 3.0
ensemble_preds = ensemble_probs.argmax(axis=1)

y_pred_labels = le.inverse_transform(ensemble_preds)
y_test_labels = le.inverse_transform(y_test)

print("\n=== ENSEMBLE (RF + GB + DNN) ===")
print(classification_report(y_test_labels, y_pred_labels))
print("\nConfusion matrix labels:", le.classes_)
print(confusion_matrix(y_test_labels, y_pred_labels))


# ---------- 9. Save everything ----------

bundle = {
    "scaler": scaler,
    "rf": rf_clf,
    "gb": gb_clf,
    "dnn": dnn_clf,
    "label_encoder": le
}

joblib.dump(bundle, "phish_url_model.joblib")
print("\n✅ Ensemble model saved to phish_url_model.joblib")
