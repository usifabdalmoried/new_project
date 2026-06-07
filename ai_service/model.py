import torch
import torch.nn as nn


class CustomCNN(nn.Module):
    def __init__(self, num_classes=36):
        super(CustomCNN, self).__init__()

        self.block1 = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(32),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(0.25)
        )

        self.block2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(64),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(0.25)
        )

        self.block3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(128),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(0.25)
        )

        # Classifier
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 8 * 8, 512),  # 64x64 -> 32x32 -> 16x16 -> 8x8
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(512),
            nn.Dropout(0.5),
            nn.Linear(512, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.classifier(x)
        return x


def load_torch_model(num_classes=36):
    return CustomCNN(num_classes=num_classes)


def load_model(saved_weights, num_classes=36):
    """Load CustomCNN with saved weights."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model  = load_torch_model(num_classes=num_classes)
    
    import os
    import zipfile
    import io

    if os.path.isdir(saved_weights):
        # If it's a directory (unpacked PyTorch v2 zip format), we can zip it in-memory
        # PyTorch expects all files to be inside a parent folder inside the zip archive (e.g., "archive/data.pkl").
        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(saved_weights):
                for file in files:
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, saved_weights)
                    # Prepend "archive/" or dummy top-level dir
                    archive_path = os.path.join("archive", relative_path).replace("\\", "/")
                    zf.write(full_path, archive_path)
        memory_zip.seek(0)
        state_dict = torch.load(memory_zip, map_location=device, weights_only=True)
    else:
        state_dict = torch.load(saved_weights, map_location=device, weights_only=True)
        
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model
