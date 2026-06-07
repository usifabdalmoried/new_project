import os
import io
import torch
import torchvision.transforms as transforms
from flask import Flask, request, jsonify
from PIL import Image
import numpy as np

# Install via: pip install mediapipe
import mediapipe as mp 

# ── Import model from same directory ──────────────────────────────────────────
from model import load_model

# ── Configuration ──────────────────────────────────────────────────────────────
WEIGHTS_PATH = os.environ.get(
    'MODEL_WEIGHTS_PATH',
    os.path.join(os.path.dirname(__file__), 'Model_weights.pth.zip')
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

# ── Load models once at startup ────────────────────────────────────────────────
resolved_weights_path = download_weights_if_url(WEIGHTS_PATH)
print(f"[AI Service] Loading classifier model from: {resolved_weights_path}")
print(f"[AI Service] Using device: {DEVICE}")

# 1. Load Stage 2 Classifier
model = load_model(resolved_weights_path)
model = model.to(DEVICE)
model.eval()
print("[AI Service] Classifier model loaded successfully!")

# 2. Initialize Stage 1 MediaPipe Detector
print("[AI Service] Initializing MediaPipe Hands detector...")
mp_hands = mp.solutions.hands
hands_detector = mp_hands.Hands(
    static_image_mode=True, 
    max_num_hands=1, 
    min_detection_confidence=0.5
)
print("[AI Service] MediaPipe Hands detector ready!")

# ── Image preprocessing (must match training pipeline) ────────────────────────
# Note: Update to (128, 128) if you switch to your clean 4.56 GB dataset!
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
    Locates hand landmarks with MediaPipe, crops the region, and predicts the sign.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded. Use key "file".'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename.'}), 400

    try:
        # Read raw image sent by the app
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        
        # Convert to NumPy array format for MediaPipe processing
        image_np = np.array(image)
        h, w, _ = image_np.shape

        # ── STAGE 1: Run MediaPipe Hand Detection ─────────────────────────────
        results = hands_detector.process(image_np)

        # Handle frame if no hand landmarks are detected
        if not results.multi_hand_landmarks:
            return jsonify({
                'translation': 'No hand detected',
                'result': 'No hand detected',
                'confidence': 0.0
            }), 200

        # Calculate a tight bounding box around the detected landmark coordinates
        hand_landmarks = results.multi_hand_landmarks[0]
        x_coords = [lm.x for lm in hand_landmarks.landmark]
        y_coords = [lm.y for lm in hand_landmarks.landmark]
        
        # Scale normalized coordinates (0.0 to 1.0) back to raw pixel dimensions
        xmin, xmax = int(min(x_coords) * w), int(max(x_coords) * w)
        ymin, ymax = int(min(y_coords) * h), int(max(y_coords) * h)

        # Add 20px padding to keep boundary features and fingertips from clipping
        padding = 20
        xmin = max(0, xmin - padding)
        ymin = max(0, ymin - padding)
        xmax = min(w, xmax + padding)
        ymax = min(h, ymax + padding)

        # Slice out just the hand region from the original PIL image
        hand_crop = image.crop((xmin, ymin, xmax, ymax))

        # ── STAGE 2: Preprocess Crop & Classify Sign ─────────────────────────
        tensor = transform(hand_crop).unsqueeze(0).to(DEVICE)

        # Inference
        with torch.no_grad():
            outputs    = model(tensor)
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
    port = int(os.environ.get('PORT', os.environ.get('AI_PORT', 5000)))
    app.run(host='0.0.0.0', port=port, debug=False)