import os
import requests
import joblib

MODEL_PATH = "model.joblib"
MODEL_URL = "https://drive.google.com/uc?id=1oP6OTWlSjqy3qR0SySDFqnALZ8kZ0EH1"

def download_model():
    if os.path.exists(MODEL_PATH):
        print("Model already exists.")
        return

    print("Downloading model...")
    with requests.get(MODEL_URL, stream=True) as r:
        r.raise_for_status()
        with open(MODEL_PATH, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print("Download complete.")

download_model()

# Load model
model = joblib.load(MODEL_PATH)
