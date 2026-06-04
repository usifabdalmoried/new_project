"""
Debug script to test different preprocessing pipelines and class orderings.
This helps determine the correct combination for inference.
"""
import torch
import torchvision.transforms as transforms
from PIL import Image, ImageDraw
import numpy as np
import os
from model import load_model

WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), 'Model_weights.pth.zip')
device = torch.device('cpu')
model = load_model(WEIGHTS_PATH, num_classes=36)
model.eval()

# Two possible class orderings
ORDERING_1 = [str(i) for i in range(10)] + [chr(c) for c in range(ord('A'), ord('Z') + 1)]  # 0-9, A-Z
ORDERING_2 = [chr(c) for c in range(ord('A'), ord('Z') + 1)] + [str(i) for i in range(10)]  # A-Z, 0-9

# Multiple preprocessing pipelines to test
pipelines = {
    "ImageNet Norm (current)": transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]),
    "No Normalization (ToTensor only)": transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
    ]),
    "Grayscale + ToTensor": transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
    ]),
    "Grayscale + ImageNet Norm": transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]),
    "Simple 0.5 Norm": transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ]),
}

# Create synthetic "sign language-like" test images
# These are simple hand-like shapes on contrasting backgrounds
def create_test_images():
    """Create simple test images that mimic sign language hand poses."""
    images = {}
    
    # Fist on white bg (like letter A/S sign)
    img = Image.new('RGB', (200, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([60, 50, 140, 150], fill=(200, 160, 120))  # skin-colored oval
    images["Fist (skin on white)"] = img
    
    # Fist on black bg
    img = Image.new('RGB', (200, 200), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([60, 50, 140, 150], fill=(200, 160, 120))
    images["Fist (skin on black)"] = img
    
    # Open hand on white bg (like letter B sign)
    img = Image.new('RGB', (200, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([70, 30, 130, 170], fill=(200, 160, 120))
    for x in [75, 90, 105, 120]:
        draw.rectangle([x, 10, x+10, 40], fill=(200, 160, 120))
    images["Open hand (skin on white)"] = img
    
    # Open hand on black bg
    img = Image.new('RGB', (200, 200), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([70, 30, 130, 170], fill=(200, 160, 120))
    for x in [75, 90, 105, 120]:
        draw.rectangle([x, 10, x+10, 40], fill=(200, 160, 120))
    images["Open hand (skin on black)"] = img
    
    return images

print("=" * 70)
print("PREPROCESSING & CLASS ORDERING DIAGNOSIS")
print("=" * 70)

test_images = create_test_images()

for pipe_name, transform in pipelines.items():
    print(f"\n{'-' * 70}")
    print(f"Pipeline: {pipe_name}")
    print(f"{'-' * 70}")
    
    for img_name, img in test_images.items():
        tensor = transform(img).unsqueeze(0).to(device)
        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            top3 = torch.topk(probs, 3, dim=1)
        
        print(f"\n  {img_name}:")
        for j in range(3):
            idx = top3.indices[0][j].item()
            conf = top3.values[0][j].item()
            print(f"    #{j+1} Class {idx:2d} ({conf:.4f})  "
                  f"[0-9,A-Z]='{ORDERING_1[idx]}'  "
                  f"[A-Z,0-9]='{ORDERING_2[idx]}'")

# Also: Check what the model thinks about the entropy of predictions
# Low entropy = model is confident = likely correct preprocessing
print(f"\n{'=' * 70}")
print("ENTROPY ANALYSIS (lower = more confident = likely correct pipeline)")
print(f"{'=' * 70}")

# Use a more realistic test: random noise image
np.random.seed(42)
random_img = Image.fromarray(np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8))

for pipe_name, transform in pipelines.items():
    tensor = transform(random_img).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)
        entropy = -torch.sum(probs * torch.log(probs + 1e-10)).item()
        top1_conf = torch.max(probs).item()
    print(f"  {pipe_name:40s}: entropy={entropy:.4f}, top1_conf={top1_conf:.4f}")

# Check the weight statistics of the first layer to infer normalization
print(f"\n{'=' * 70}")
print("FIRST LAYER WEIGHT STATISTICS (helps infer expected input range)")
print(f"{'=' * 70}")
first_conv = None
for name, module in model.named_modules():
    if isinstance(module, torch.nn.Conv2d):
        first_conv = (name, module)
        break

if first_conv:
    name, layer = first_conv
    w = layer.weight.data
    print(f"  Layer: {name}")
    print(f"  Weight shape: {w.shape}")
    print(f"  Weight mean:  {w.mean().item():.6f}")
    print(f"  Weight std:   {w.std().item():.6f}")
    print(f"  Weight min:   {w.min().item():.6f}")
    print(f"  Weight max:   {w.max().item():.6f}")
    print(f"  Weight abs mean: {w.abs().mean().item():.6f}")
    
    # If weights are large, model likely expects normalized input [-1,1] or ImageNet norm
    # If weights are small, model likely expects [0,1] input
    if w.abs().mean().item() > 0.1:
        print("  → Weights are relatively large, suggesting the model expects normalized input")
    else:
        print("  → Weights are relatively small, suggesting the model expects [0,1] or raw input")

print(f"\n{'=' * 70}")
print("DIAGNOSIS COMPLETE")
print(f"{'=' * 70}")
