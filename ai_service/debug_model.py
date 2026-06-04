"""
Debug script to inspect model weights and determine class label ordering.
Run from the ai_service directory:
    python debug_model.py
"""
import torch
import numpy as np
from model import load_model
import os

WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), 'Model_weights.pth.zip')

print("=" * 60)
print("MODEL DEBUG INSPECTION")
print("=" * 60)

# Load model
device = torch.device('cpu')
model = load_model(WEIGHTS_PATH, num_classes=36)
model.eval()

# Check the final layer to understand output structure
print("\n[1] Model final layer info:")
# Get the last linear layer
last_linear = None
for name, module in model.named_modules():
    if isinstance(module, torch.nn.Linear):
        last_linear = (name, module)
        
if last_linear:
    name, layer = last_linear
    print(f"  Layer name: {name}")
    print(f"  Input features: {layer.in_features}")
    print(f"  Output features (num_classes): {layer.out_features}")
    
    # Check bias values - they can hint at class distribution
    if layer.bias is not None:
        bias = layer.bias.data.numpy()
        print(f"\n[2] Final layer bias values (can indicate class ordering):")
        for i, b in enumerate(bias):
            print(f"  Class {i:2d}: bias = {b:+.4f}")
        
        print(f"\n  Max bias at class {np.argmax(bias)}: {np.max(bias):.4f}")
        print(f"  Min bias at class {np.argmin(bias)}: {np.min(bias):.4f}")

# Try creating synthetic test images and see what happens
print("\n[3] Testing with synthetic images...")
import torchvision.transforms as transforms
from PIL import Image

transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# Test with a solid black image and solid white image
for color_name, color in [("BLACK", (0,0,0)), ("WHITE", (255,255,255)), ("RED", (255,0,0))]:
    img = Image.new('RGB', (64, 64), color)
    tensor = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)
        top5 = torch.topk(probs, 5, dim=1)
    
    print(f"\n  {color_name} image - Top 5 predictions:")
    # Print with BOTH orderings so we can compare
    labels_0_9_A_Z = [str(i) for i in range(10)] + [chr(c) for c in range(ord('A'), ord('Z') + 1)]
    labels_A_Z_0_9 = [chr(c) for c in range(ord('A'), ord('Z') + 1)] + [str(i) for i in range(10)]
    
    for j in range(5):
        idx = top5.indices[0][j].item()
        conf = top5.values[0][j].item()
        print(f"    Class {idx:2d}: confidence={conf:.4f}  "
              f"(if 0-9,A-Z: '{labels_0_9_A_Z[idx]}')  "
              f"(if A-Z,0-9: '{labels_A_Z_0_9[idx]}')")

# Test with actual test image if available
test_img_path = os.path.join(os.path.dirname(__file__), 'test_sign.jpg')
if os.path.exists(test_img_path):
    print(f"\n[4] Testing with test_sign.jpg...")
    img = Image.open(test_img_path).convert('RGB')
    print(f"  Image size: {img.size}")
    tensor = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)
        top5 = torch.topk(probs, 5, dim=1)
    
    print(f"  Top 5 predictions:")
    for j in range(5):
        idx = top5.indices[0][j].item()
        conf = top5.values[0][j].item()
        print(f"    Class {idx:2d}: confidence={conf:.4f}  "
              f"(if 0-9,A-Z: '{labels_0_9_A_Z[idx]}')  "
              f"(if A-Z,0-9: '{labels_A_Z_0_9[idx]}')")

# Also check: is the checkpoint maybe a dict with class names?
print(f"\n[5] Checking raw checkpoint structure...")
checkpoint = torch.load(WEIGHTS_PATH, map_location=device, weights_only=False)
if isinstance(checkpoint, dict):
    print(f"  Checkpoint is a dict with keys: {list(checkpoint.keys())[:20]}")
    if 'class_names' in checkpoint:
        print(f"  class_names: {checkpoint['class_names']}")
    if 'classes' in checkpoint:
        print(f"  classes: {checkpoint['classes']}")
    if 'label_map' in checkpoint:
        print(f"  label_map: {checkpoint['label_map']}")
    if 'class_to_idx' in checkpoint:
        print(f"  class_to_idx: {checkpoint['class_to_idx']}")
    if 'idx_to_class' in checkpoint:
        print(f"  idx_to_class: {checkpoint['idx_to_class']}")
    
    # Check if it's a state_dict (keys look like layer names)
    sample_keys = list(checkpoint.keys())[:5]
    if any('weight' in k or 'bias' in k for k in sample_keys):
        print(f"  Looks like a plain state_dict (no metadata)")
    else:
        print(f"  Non-standard checkpoint format, first keys: {sample_keys}")
else:
    print(f"  Checkpoint type: {type(checkpoint)}")

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)
