import os
import io
import threading
import torch
import torchvision.transforms as transforms
from flask import Flask, request, jsonify
from PIL import Image, ImageOps
import numpy as np

IS_RAILWAY = bool(os.environ.get('RAILWAY_ENVIRONMENT'))
DISABLE_MEDIAPIPE = os.environ.get(
    'DISABLE_MEDIAPIPE',
    'true' if IS_RAILWAY else 'false',
).lower() == 'true'
USE_IMAGENET_NORM = os.environ.get('USE_IMAGENET_NORM', 'false').lower() == 'true'
MODEL_INPUT_SIZE = int(os.environ.get('MODEL_INPUT_SIZE', '64'))

from model import load_model

NUM_CLASSES = 36
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
CLASS_LABELS = [str(i) for i in range(10)] + [chr(c) for c in range(ord('A'), ord('Z') + 1)]

model = None
hands_detector = None
model_error = None
model_ready = threading.Event()
resolved_weights_path = None


def resolve_default_weights_path():
    """Pick the first available weights file/folder."""
    base_dir = os.path.dirname(__file__)
    env_path = os.environ.get('MODEL_WEIGHTS_PATH', '').strip()
    if env_path:
        return env_path

    candidates = [
        os.path.join(base_dir, 'weights', 'model.pth'),
        os.path.join(base_dir, 'weights', 'Model_weights.pth'),
        os.path.join(base_dir, 'Model_weights.pth'),
        os.path.join(base_dir, 'Model_weights.pth.zip'),
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
            local_filename = 'model_weights.pth'

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


def build_transform():
    steps = [
        transforms.Resize((MODEL_INPUT_SIZE, MODEL_INPUT_SIZE)),
        transforms.ToTensor(),
    ]
    if USE_IMAGENET_NORM:
        steps.append(transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ))
    return transforms.Compose(steps)


transform = build_transform()


def detect_and_crop_hand(image):
    if DISABLE_MEDIAPIPE or hands_detector is None:
        return image, False

    image_np = np.array(image)
    h, w, _ = image_np.shape
    results = hands_detector.process(image_np)

    if not results.multi_hand_landmarks:
        return image, False

    hand_landmarks = results.multi_hand_landmarks[0]
    x_coords = [lm.x for lm in hand_landmarks.landmark]
    y_coords = [lm.y for lm in hand_landmarks.landmark]

    xmin = max(0, int(min(x_coords) * w) - 20)
    ymin = max(0, int(min(y_coords) * h) - 20)
    xmax = min(w, int(max(x_coords) * w) + 20)
    ymax = min(h, int(max(y_coords) * h) + 20)

    if xmax <= xmin or ymax <= ymin:
        return image, False

    return image.crop((xmin, ymin, xmax, ymax)), True


def load_models_background():
    global model, hands_detector, model_error, resolved_weights_path
    try:
        weights_path = resolve_default_weights_path()
        resolved_weights_path = download_weights_if_url(weights_path)

        if not os.path.exists(resolved_weights_path):
            raise FileNotFoundError(
                f"Weights not found at: {resolved_weights_path}. "
                "Set MODEL_WEIGHTS_PATH or place file in ai_service/weights/model.pth"
            )

        print(f"[AI Service] Loading classifier from: {resolved_weights_path}")
        print(f"[AI Service] Device: {DEVICE}, input: {MODEL_INPUT_SIZE}px, imagenet_norm: {USE_IMAGENET_NORM}")

        loaded = load_model(resolved_weights_path)
        loaded = loaded.to(DEVICE)
        loaded.eval()
        model = loaded
        print("[AI Service] Classifier loaded successfully!")

        if not DISABLE_MEDIAPIPE:
            import mediapipe as mp
            print("[AI Service] Initializing MediaPipe Hands detector...")
            hands_detector = mp.solutions.hands.Hands(
                static_image_mode=True,
                max_num_hands=1,
                min_detection_confidence=0.5,
            )
            print("[AI Service] MediaPipe ready!")
        else:
            print("[AI Service] MediaPipe disabled.")
    except Exception as err:
        model_error = str(err)
        print(f"[AI Service] Startup failed: {model_error}")
    finally:
        model_ready.set()


app = Flask(__name__)


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
        'input_size': MODEL_INPUT_SIZE,
    }), 200


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

        hand_crop, hand_detected = detect_and_crop_hand(image)
        if not hand_detected and not DISABLE_MEDIAPIPE:
            return jsonify({'error': 'No hand detected in image', 'confidence': 0.0}), 400

        tensor = transform(hand_crop).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probs, dim=1)

        label = CLASS_LABELS[predicted.item()]
        confidence = round(confidence.item(), 4)

        if label.isdigit():
            label = str(int(label) - 1)

        if confidence < 0.50:
            return jsonify({
                'error': "image doesn't include sign language character",
                'confidence': confidence,
            }), 400

        return jsonify({
            'translation': label,
            'result': label,
            'confidence': confidence,
            'hand_detected': hand_detected,
        }), 200

    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


if __name__ == '__main__':
    print(f"[AI Service] Railway: {IS_RAILWAY}, MediaPipe off: {DISABLE_MEDIAPIPE}")
    threading.Thread(target=load_models_background, daemon=True).start()
    port = int(os.environ.get('PORT', os.environ.get('AI_PORT', 5000)))
    app.run(host='0.0.0.0', port=port, debug=False)
