import os
import io
import threading
import torch
from flask import Flask, request, jsonify
from PIL import Image, ImageOps
import numpy as np

IS_RAILWAY = bool(os.environ.get('RAILWAY_ENVIRONMENT'))
DISABLE_MEDIAPIPE = os.environ.get(
    'DISABLE_MEDIAPIPE',
    'true' if IS_RAILWAY else 'false',
).lower() == 'true'

def preprocess_image_or_hand(image):
    if DISABLE_MEDIAPIPE:
        return image, False

    import mediapipe as mp
    mp_hands = mp.solutions.hands

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
        hand_detected = False
                
    return image, hand_detected

# ── Import model from same directory ──────────────────────────────────────────
from model import load_model

# ── Configuration ──────────────────────────────────────────────────────────────
collected_weights_path = os.path.join(os.path.dirname(__file__), 'collected_weights')
if os.path.exists(collected_weights_path):
    DEFAULT_WEIGHTS = collected_weights_path
else:
    DEFAULT_WEIGHTS = os.path.join(os.path.dirname(__file__), 'Model_weights.pth.zip')

WEIGHTS_PATH = os.environ.get('MODEL_WEIGHTS_PATH', DEFAULT_WEIGHTS)
NUM_CLASSES  = 36
DEVICE       = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

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

# ── Load model in background so Flask binds to PORT before Railway health checks ──
model = None
model_error = None
model_ready = threading.Event()

def load_model_background():
    global model, model_error
    try:
        resolved_weights_path = download_weights_if_url(WEIGHTS_PATH)
        print(f"[AI Service] Loading model from: {resolved_weights_path}")
        print(f"[AI Service] Using device: {DEVICE}")
        loaded = load_model(resolved_weights_path)
        loaded = loaded.to(DEVICE)
        loaded.eval()
        model = loaded
        print("[AI Service] Model loaded successfully!")
    except Exception as err:
        model_error = str(err)
        print(f"[AI Service] Model load failed: {model_error}")
    finally:
        model_ready.set()

def transform_image(img):
    img_resized = img.resize((64, 64))
    arr = np.array(img_resized, dtype=np.float32) / 255.0
    arr = np.transpose(arr, (2, 0, 1))
    return torch.from_numpy(arr)

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    if model_error:
        return jsonify({'status': 'error', 'error': model_error, 'device': str(DEVICE)}), 503
    if not model_ready.is_set():
        return jsonify({'status': 'loading', 'device': str(DEVICE)}), 200
    return jsonify({'status': 'ok', 'device': str(DEVICE)}), 200


def _require_model():
    if model_error:
        return jsonify({'error': f'Model failed to load: {model_error}'}), 503
    if not model_ready.is_set():
        return jsonify({'error': 'Model is still loading, retry shortly.'}), 503
    return None


@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded. Use key "file".'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename.'}), 400

    not_ready = _require_model()
    if not_ready:
        return not_ready

    try:
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes))
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')
        image, hand_detected = preprocess_image_or_hand(image)
        
        tensor = transform_image(image).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            outputs    = model(tensor)
            probs      = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probs, dim=1)

        label      = CLASS_LABELS[predicted.item()]
        confidence = round(confidence.item(), 4)

        if label.isdigit():
            label = str(int(label) - 1)

        THRESHOLD = 0.50

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
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded. Use key "file".'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename.'}), 400

    not_ready = _require_model()
    if not_ready:
        return not_ready

    try:
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes))
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')
        original_size = image.size
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


if __name__ == '__main__':
    print(f"[AI Service] Railway mode: {IS_RAILWAY}, MediaPipe disabled: {DISABLE_MEDIAPIPE}")
    threading.Thread(target=load_model_background, daemon=True).start()
    port = int(os.environ.get('PORT', os.environ.get('AI_PORT', 5000)))
    app.run(host='0.0.0.0', port=port, debug=False)
