import os
import gdown

MODEL_PATH = "phish_url_model.joblib"

if not os.path.exists(MODEL_PATH):
    print("Downloading ML model...")
    
    url = "https://drive.google.com/file/d/1rMNUuve1gC-bjZfLIElQ7b2m8VAq6XWm/view?usp=drive_link"
    
    gdown.download(url, MODEL_PATH, quiet=False)
