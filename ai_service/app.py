import os
import io
import torch
from flask import Flask, request, jsonify
from PIL import Image, ImageOps
import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Hands module reference (instantiated per-request to save memory and avoid crashes)
mp_hands = mp.solutions.hands

def preprocess_image_or_hand(image):
    if os.environ.get('DISABLE_MEDIAPIPE', 'false').lower() == 'true':
        print("[AI Service] MediaPipe is disabled via environment variable.")
        return image, False

    cv_img = np.array(image)
    h, w, _ = cv_img.shape
    
    hand_detected = False
    try:
        # Create hands instance inside request and close it to free C++ memory immediately
        with mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=0.5
        ) as hands_detector:
            results = hands_detector.process(cv_img)
            
            if results.multi_hand_landmarks:
                landmarks = results.multi_hand_landmarks[0]
                lms = landmarks.landmark
                x_coords = [lm.x for lm in lms]
                y_coords = [lm.y for lm in lms]

                x_min, x_max = int(min(x_coords) * w), int(max(x_coords) * w)
                y_min, y_max = int(min(y_coords) * h), int(max(y_coords) * h)

                padding = 20
                x_min, x_max = max(0, x_min - padding), min(w, x_max + padding)
                y_min, y_max = max(0, y_min - padding), min(h, y_max + padding)

                if x_max > x_min and y_max > y_min:
                    hand_region = cv_img[y_min:y_max, x_min:x_max]
                    if hand_region.size > 0:
                        image = Image.fromarray(hand_region)
                        hand_detected = True
    except Exception as mp_err:
        print(f"[AI Service] MediaPipe processing failed/crushed: {mp_err}")
        # Safely fall back to the original image
        hand_detected = False
                
    return image, hand_detected

# ── Import model from same directory ──────────────────────────────────────────
from model import load_model

# ── Configuration ──────────────────────────────────────────────────────────────
# Use collected_weights if it exists, otherwise fall back to Model_weights.pth.zip
collected_weights_path = os.path.join(os.path.dirname(__file__), 'collected_weights')
if os.path.exists(collected_weights_path):
    DEFAULT_WEIGHTS = collected_weights_path
else:
    DEFAULT_WEIGHTS = os.path.join(os.path.dirname(__file__), 'Model_weights.pth.zip')

WEIGHTS_PATH = os.environ.get('MODEL_WEIGHTS_PATH', DEFAULT_WEIGHTS)
NUM_CLASSES  = 36
DEVICE       = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 36 classes: 0-9 then A-Z (matches training data folder ordering)
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

# PyTorch saved directory models can sometimes be loaded directly, but on some platforms,
# torch.load requires the file path or directory path depending on format.
# Let's ensure it is loaded correctly by model.py
model = load_model(resolved_weights_path)
model = model.to(DEVICE)
model.eval()

print("[AI Service] Model loaded successfully!")

# -- Image preprocessing (must match training pipeline) ────────────────────────
# NOTE: Model was trained with ToTensor() only (scales pixels to [0, 1]).
#       Do NOT apply ImageNet normalization here.
def transform_image(img):
    # Resize PIL Image to 64x64
    img_resized = img.resize((64, 64))
    # Convert PIL Image to float numpy array and scale to [0, 1]
    arr = np.array(img_resized, dtype=np.float32) / 255.0
    # Transpose from (H, W, C) to (C, H, W)
    arr = np.transpose(arr, (2, 0, 1))
    # Convert to PyTorch tensor
    tensor = torch.from_numpy(arr)
    return tensor

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
        image = Image.open(io.BytesIO(img_bytes))
        # Fix EXIF rotation from mobile cameras
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')

        # Detect and crop hand region
        image, hand_detected = preprocess_image_or_hand(image)
        
        tensor = transform_image(image).unsqueeze(0).to(DEVICE)   # [1, 3, 64, 64]

        # Inference
        with torch.no_grad():
            outputs    = model(tensor)                        # [1, 36]
            probs      = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probs, dim=1)

        label      = CLASS_LABELS[predicted.item()]
        confidence = round(confidence.item(), 4)

        # Digit adjustment mapping (matches get_top_k_classes digit offset logic)
        if label.isdigit():
            label = str(int(label) - 1)

        THRESHOLD = 0.50  # Lower threshold because hand is pre-cropped, making predictions cleaner

        if confidence < THRESHOLD:
            return jsonify({
                'error': "image doesn't include sign language character",
                'confidence': confidence
            }), 400

        return jsonify({
            'translation': label,
            'result'     : label,
            'confidence' : confidence,
            'hand_detected': hand_detected
        }), 200

    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


@app.route('/predict/debug', methods=['POST'])
def predict_debug():
    """
    Debug endpoint: returns top-5 predictions with BOTH possible class orderings.
    Use this to determine which ordering matches your actual sign.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded. Use key "file".'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename.'}), 400

    try:
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes))
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')
        original_size = image.size
        
        # Detect and crop hand region
        image, hand_detected = preprocess_image_or_hand(image)
        
        tensor = transform_image(image).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            top5 = torch.topk(probs, 5, dim=1)

        labels_0_9_AZ = [str(i) for i in range(10)] + [chr(c) for c in range(ord('A'), ord('Z') + 1)]
        labels_AZ_0_9 = [chr(c) for c in range(ord('A'), ord('Z') + 1)] + [str(i) for i in range(10)]

        results = []
        for j in range(5):
            idx = top5.indices[0][j].item()
            conf = round(top5.values[0][j].item(), 4)
            results.append({
                'rank': j + 1,
                'class_index': idx,
                'confidence': conf,
                'label_if_0to9_AtoZ': labels_0_9_AZ[idx],
                'label_if_AtoZ_0to9': labels_AZ_0_9[idx],
            })

        return jsonify({
            'image_original_size': list(original_size),
            'hand_detected': hand_detected,
            'current_label': CLASS_LABELS[top5.indices[0][0].item()],
            'current_confidence': round(top5.values[0][0].item(), 4),
            'top5': results,
            'note': 'Compare the sign you made with both label columns to find the correct ordering',
        }), 200

    except Exception as e:
        return jsonify({'error': f'Debug prediction failed: {str(e)}'}), 500


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', os.environ.get('AI_PORT', 5000)))
    app.run(host='0.0.0.0', port=port, debug=False)
