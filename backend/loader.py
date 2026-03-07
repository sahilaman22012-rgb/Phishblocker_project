import os
import gdown

DATA_PATH = "data/dataset.csv"

if not os.path.exists(DATA_PATH):
    os.makedirs("data", exist_ok=True)

    url = "https://drive.google.com/file/d/1WSYi4g-oY36YRVmQRNDhliGhDPPrRf_7/view?usp=drive_link"
    gdown.download(url, DATA_PATH, quiet=False)
