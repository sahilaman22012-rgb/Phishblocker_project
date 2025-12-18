# PhishBlocker - AI-Powered Phishing Detection

A comprehensive phishing detection system with browser extensions and a web dashboard.

## Project Structure

\`\`\`
phishblocker/
├── backend/                 # Flask API server
│   ├── app.py              # Main Flask application
│   ├── predict_url.py      # ML prediction logic
│   ├── rules_engine.py     # Rules-based detection
│   ├── requirements.txt    # Python dependencies
│   └── phish_url_model.joblib  # Trained ML model (you need to generate this)
│
├── extensions/             # Browser extensions
│   ├── chrome/            # Chrome/Brave/Edge extension
│   └── firefox/           # Firefox extension
│
└── dashboard/             # Next.js web dashboard
    └── (Next.js app files)
\`\`\`

## Setup Instructions

### 1. Train the ML Model

First, you need to train the model and generate `phish_url_model.joblib`:

\`\`\`bash
cd backend
pip install -r requirements.txt
# Place your malicious_phish.csv dataset in the backend folder
python train_phish_model.py
\`\`\`

This will generate `phish_url_model.joblib` file.

### 2. Start the Backend API

\`\`\`bash
cd backend
python app.py
\`\`\`

The API will run on `http://localhost:5000`

### 3. Run the Dashboard

\`\`\`bash
npm install
npm run dev
\`\`\`

The dashboard will run on `http://localhost:3000`

### 4. Install Browser Extensions

#### Chrome/Brave/Edge:
1. Open `chrome://extensions/` (or `brave://extensions/`, `edge://extensions/`)
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extensions/chrome` folder

#### Firefox:
1. Open `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Select the `manifest.json` file from `extensions/firefox` folder

## Usage

- **Dashboard**: Visit `http://localhost:3000` to test URLs and download extensions
- **Extension**: Browse the web and get real-time phishing alerts
- **API**: Send POST requests to `http://localhost:5000/api/check-url`

## API Endpoints

- `POST /api/check-url` - Check if a URL is phishing
  \`\`\`json
  {
    "url": "https://example.com"
  }
  \`\`\`

- `GET /health` - Health check endpoint
