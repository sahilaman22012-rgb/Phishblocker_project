from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from functools import lru_cache
from predict_url import predict_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@lru_cache(maxsize=1000)
def cached_predict(url):
    """Cache predictions for frequently checked URLs"""
    return predict_url(url)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "PhishBlocker API is running"})

@app.route('/api/check-url', methods=['POST'])
def check_url():
    """
    Check if a URL is phishing or benign.
    
    Request body:
    {
        "url": "https://example.com"
    }
    
    Response:
    {
        "url": "https://example.com",
        "prediction": "benign" or "phishing",
        "risk_score": 85.5,
        "reasons": ["list", "of", "reasons"],
        "safe": true or false
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                "error": "Missing 'url' in request body"
            }), 400
        
        url = data['url'].strip()
        
        if not url:
            return jsonify({
                "error": "URL cannot be empty"
            }), 400
        
        logger.info(f"Checking URL: {url}")
        label, score, reasons = cached_predict(url)
        
        is_safe = label != "phishing"
        
        # 🔁 Map ML output → extension status
        if label == "benign" or score <= 40:
            status = "safe"
        elif score < 80:
            status = "suspicious"
        else:
            status = "malicious"
        response = {
            "url": url,
            "prediction": label,
            "risk_score": round(score, 2),
            "reasons": reasons,
            "status": status   # 👈 REQUIRED BY CONTENT SCRIPT
        }

        
        logger.info(f"Prediction: {label}, Score: {score:.2f}")
        
        return jsonify(response)
    
    except Exception as e:
        logger.exception("Error processing URL check")
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/batch-check', methods=['POST'])
def batch_check():
    """
    Check multiple URLs at once.
    
    Request body:
    {
        "urls": ["https://example1.com", "https://example2.com"]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'urls' not in data:
            return jsonify({
                "error": "Missing 'urls' array in request body"
            }), 400
        
        urls = data['urls']
        
        if not isinstance(urls, list):
            return jsonify({
                "error": "'urls' must be an array"
            }), 400
        
        if len(urls) > 100:
            return jsonify({
                "error": "Maximum 100 URLs per batch"
            }), 400
        
        results = []
        
        for url in urls:
            try:
                label, score, reasons = cached_predict(url.strip())
                results.append({
                    "url": url,
                    "prediction": label,
                    "risk_score": round(score, 2),
                    "reasons": reasons,
                    "safe": label != "phishing"
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "error": str(e)
                })
        
        return jsonify({"results": results})
    
    except Exception as e:
        logger.exception("Error processing batch check")
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Pre-load the model on startup
    try:
        from predict_url import load_model
        logger.info("Loading ML model...")
        load_model()
        logger.info("ML model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        logger.error("Make sure you have run train_phish_model.py first!")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
