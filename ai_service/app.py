import os
import io
import threading
import torch
import torchvision.transforms as transforms
from flask import Flask, request, jsonify
from PIL import Image, ImageOps
import mediapipe as mp
import numpy as np

from model import load_model

PREDICTION_THRESHOLD = float(os.environ.get('PREDICTION_THRESHOLD', '0.35'))
REQUIRE_HAND = os.environ.get('REQUIRE_HAND_DETECT', 'true').lower() == 'true'
NUM_CLASSES = 36
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# Training folders: 1-10 then a-z (36 classes)
MODEL_CLASS_LABELS = [str(i) for i in range(1, 11)] + [chr(c) for c in range(ord('a'), ord('z') + 1)]
DISPLAY_LABELS = [str(i) for i in range(10)] + [chr(c) for c in range(ord('A'), ord('Z') + 1)]


def to_display_label(raw_label):
    if raw_label.isdigit():
        return str(int(raw_label) - 1)
    return raw_label.upper()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.3,
)

model = None
model_error = None
model_ready = threading.Event()
resolved_weights_path = None


def preprocess_image_or_hand(image):
    cv_img = np.array(image)
    h, w, _ = cv_img.shape
    results = hands.process(cv_img)

    hand_detected = False
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

    return image, hand_detected


def resolve_default_weights_path():
    base_dir = os.path.dirname(__file__)
    env_path = os.environ.get('MODEL_WEIGHTS_PATH', '').strip()
    if env_path:
        return env_path

    candidates = [
        os.path.join(base_dir, 'Model_weights.pth.zip'),
        os.path.join(base_dir, 'Model_weights.pth'),
        os.path.join(base_dir, 'weights', 'model.pth'),
        os.path.join(base_dir, 'collected_weights'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    return os.path.join(base_dir, 'Model_weights.pth.zip')


def download_weights_if_url(path_or_url):
    if path_or_url.startswith(('http://', 'https://')):
        local_filename = os.path.basename(path_or_url.split('?')[0])
        if not local_filename.endswith(('.pth', '.zip', '.bin', '.pt')):
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


def load_model_background():
    global model, model_error, resolved_weights_path
    try:
        weights_path = resolve_default_weights_path()
        resolved_weights_path = download_weights_if_url(weights_path)
        if not os.path.exists(resolved_weights_path):
            raise FileNotFoundError(f"Weights not found at: {resolved_weights_path}")

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


transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
])

app = Flask(__name__)
threading.Thread(target=load_model_background, daemon=True).start()


def _require_model():
    if model_error:
        return jsonify({'error': f'Model failed to load: {model_error}'}), 503
    if not model_ready.is_set():
        return jsonify({'error': 'Model is still loading, retry shortly.'}), 503
    return None


@app.route('/health', methods=['GET'])
def health():
    if model_error:
        return jsonify({'status': 'error', 'error': model_error, 'device': str(DEVICE)}), 503
    if not model_ready.is_set():
        return jsonify({'status': 'loading', 'device': str(DEVICE)}), 200
    return jsonify({
        'status': 'ok',
        'device': str(DEVICE),
        'weights': resolved_weights_path,
    }), 200


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

        if REQUIRE_HAND and not hand_detected:
            return jsonify({
                'error': 'No hand detected in image. Show your hand clearly in front of the camera.',
                'confidence': 0.0,
                'hand_detected': False,
            }), 400

        tensor = transform(image).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probs, dim=1)

        raw_label = MODEL_CLASS_LABELS[predicted.item()]
        label = to_display_label(raw_label)
        confidence = round(confidence.item(), 4)

        if confidence < PREDICTION_THRESHOLD:
            return jsonify({
                'error': "image doesn't include sign language character",
                'confidence': confidence,
            }), 400

        return jsonify({
            'translation': label,
            'result': label,
            'confidence': confidence,
            'hand_detected': hand_detected,
            'raw_label': raw_label,
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
        tensor = transform(image).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            top5 = torch.topk(probs, 5, dim=1)

        results = []
        for j in range(5):
            idx = top5.indices[0][j].item()
            conf = round(top5.values[0][j].item(), 4)
            raw_label = MODEL_CLASS_LABELS[idx]
            results.append({
                'rank': j + 1,
                'class_index': idx,
                'confidence': conf,
                'raw_label': raw_label,
                'display_label': to_display_label(raw_label),
            })

        top_raw = MODEL_CLASS_LABELS[top5.indices[0][0].item()]
        return jsonify({
            'image_original_size': list(original_size),
            'hand_detected': hand_detected,
            'current_label': to_display_label(top_raw),
            'current_raw_label': top_raw,
            'current_confidence': round(top5.values[0][0].item(), 4),
            'top5': results,
            'note': 'Model classes are 1-10,a-z. Digits are shifted by -1 for display (e.g. raw 1 -> 0).',
        }), 200

    except Exception as e:
        return jsonify({'error': f'Debug prediction failed: {str(e)}'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', os.environ.get('AI_PORT', 5000)))
    app.run(host='0.0.0.0', port=port, debug=False)
