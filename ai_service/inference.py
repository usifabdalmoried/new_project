import cv2
import mediapipe as mp
mp_hands = mp.solutions.hands
import numpy as np
import torch
from model import CustomCNN

# Global state for model and mediapipe
_model = None
_hands = None
_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
_class_names = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
               'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
               'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
               'u', 'v', 'w', 'x', 'y', 'z']

def _initialize_assets(model_path="weights/collected_weights.pth"):
    """Internal function to ensure model and hand tracker are loaded."""
    global _model, _hands
    if _model is None:
        _model = CustomCNN(num_classes=36).to(_device)
        try:
            _model.load_state_dict(torch.load(model_path, map_location=_device))
            _model.eval()
        except Exception as e:
            print(f"Error loading model weights: {e}")
    
    if _hands is None:
        _hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

def get_camera_stream(source=0):
    """
    1. Returns an active camera stream.
    """
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Warning: Could not open video source {source}")
    return cap

def capture_frame(cap):
    """
    2. Captures the latest frame from the stream.
    """
    if cap is None or not cap.isOpened():
        return None
    success, frame = cap.read()
    if not success:
        return None
    return cv2.flip(frame, 1)  # Flip for selfie view

def preprocess_frame(frame, return_metadata=False):
    """
    3. Extracts the hand region using MediaPipe and prepares it for the model.
       Returns a PyTorch tensor (or None if no hand detected).
       If return_metadata is True, returns (tensor, metadata_dict).
    """
    if frame is None:
        return (None, None) if return_metadata else None
        
    _initialize_assets()
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = _hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        landmarks = results.multi_hand_landmarks[0]
        lms = landmarks.landmark
        x_coords = [lm.x for lm in lms]
        y_coords = [lm.y for lm in lms]

        # Calculate bounding box
        x_min, x_max = int(min(x_coords) * w), int(max(x_coords) * w)
        y_min, y_max = int(min(y_coords) * h), int(max(y_coords) * h)

        # Add padding
        padding = 20
        x_min, x_max = max(0, x_min - padding), min(w, x_max + padding)
        y_min, y_max = max(0, y_min - padding), min(h, y_max + padding)

        metadata = {
            "bbox": (x_min, y_min, x_max, y_max),
            "landmarks": landmarks
        }

        if x_max > x_min and y_max > y_min:
            hand_region = rgb_frame[y_min:y_max, x_min:x_max]
            if hand_region.size > 0:
                hand_resized = cv2.resize(hand_region, (64, 64))
                hand_norm = hand_resized.astype(np.float32) / 255.0
                hand_transposed = np.transpose(hand_norm, (2, 0, 1))
                tensor = torch.from_numpy(hand_transposed).unsqueeze(0).to(_device)
                
                return (tensor, metadata) if return_metadata else tensor
    
    return (None, None) if return_metadata else None

def predict_distribution(hand_tensor):
    """
    4. Runs the model and returns the probability distribution.
    """
    if hand_tensor is None:
        return None
        
    _initialize_assets()
    with torch.no_grad():
        outputs = _model(hand_tensor)
        probabilities = torch.softmax(outputs, dim=1)
    return probabilities

def get_top_k_classes(probs, k=5):
    """
    5. Returns the top K labels and their associated probabilities.
    """
    if probs is None:
        return []

    top_probs, top_idxs = torch.topk(probs, k=min(k, 36))
    results = []
    
    for i in range(top_probs.size(1)):
        idx = top_idxs[0][i].item()
        prob = top_probs[0][i].item()
        label = _class_names[idx]
        
        # Digit adjustment logic from original test script
        if label.isdigit():
            label = str(int(label) - 1)
            
        results.append({
            "label": label,
            "confidence": float(prob)
        })
        
    return results
