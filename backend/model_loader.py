import os
import gdown

MODEL_PATH = "phish_url_model.joblib"

if not os.path.exists(MODEL_PATH):
    print("Downloading ML model...")
    
    url = "https://drive.google.com/uc?export=download&id=1rMNUuve1gC-bjZfLIElQ7b2m8VAq6XWm"
    
    gdown.download(url, MODEL_PATH, quiet=False)
