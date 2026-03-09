import os
import gdown

MODEL_PATH = "phish_url_model.joblib"

if not os.path.exists(MODEL_PATH):
    print("Downloading ML model...")
    
    url = "https://drive.google.com/uc?id=YOUR_FILE_ID"
    
    gdown.download(url, MODEL_PATH, quiet=False)
