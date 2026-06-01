import os
import io
import torch
import torchvision.transforms as transforms
from flask import Flask, request, jsonify
from PIL import Image

# ── Import model from same directory ──────────────────────────────────────────
from model import load_model

# ── Configuration ──────────────────────────────────────────────────────────────
WEIGHTS_PATH = os.environ.get(
    'MODEL_WEIGHTS_PATH',
    r'D:\Model_weights.pth.zip'      # default path — override via env var
)
NUM_CLASSES  = 36
DEVICE       = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 36 classes: 0-9 then A-Z
CLASS_LABELS = [str(i) for i in range(10)] + [chr(c) for c in range(ord('A'), ord('Z') + 1)]

def download_weights_if_url(path_or_url):
    if path_or_url.startswith(('http://', 'https://')):
        local_filename = os.path.basename(path_or_url.split('?')[0])
        if not local_filename.endswith(('.pth', '.zip', '.bin')):
            local_filename = 'Model_weights.pth'
        
        local_path = os.path.join(os.getcwd(), local_filename)
        
        if os.path.exists(local_path):
            print(f"[AI Service] Weights already downloaded at: {local_path}")
            return local_path
            
        print(f"[AI Service] Downloading weights from {path_or_url} to {local_path}...")
        import urllib.request
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(path_or_url, local_path)
        print("[AI Service] Download complete!")
        return local_path
    return path_or_url

# ── Load model once at startup ─────────────────────────────────────────────────
resolved_weights_path = download_weights_if_url(WEIGHTS_PATH)
print(f"[AI Service] Loading model from: {resolved_weights_path}")
print(f"[AI Service] Using device: {DEVICE}")

model = load_model(resolved_weights_path)
model = model.to(DEVICE)
model.eval()

print("[AI Service] Model loaded successfully!")

# ── Image preprocessing (must match training pipeline) ────────────────────────
transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# ── Flask app ──────────────────────────────────────────────────────────────────
app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'device': str(DEVICE)}), 200


@app.route('/predict', methods=['POST'])
def predict():
    """
    Accepts a multipart/form-data POST with key 'file' (image).
    Returns JSON: { "translation": "A", "confidence": 0.98, "result": "A" }
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded. Use key "file".'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename.'}), 400

    try:
        # Read & preprocess image
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        tensor = transform(image).unsqueeze(0).to(DEVICE)   # [1, 3, 64, 64]

        # Inference
        with torch.no_grad():
            outputs    = model(tensor)                        # [1, 36]
            probs      = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probs, dim=1)

        label      = CLASS_LABELS[predicted.item()]
        confidence = round(confidence.item(), 4)

        return jsonify({
            'translation': label,
            'result'     : label,
            'confidence' : confidence,
        }), 200

    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('AI_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
