import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image

from recommender.AImodels.facemesh_model import detect_and_crop_face, crop_left_eye, crop_right_eye

# ----------------------
# 📍 Path Setup
# ----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKIN_TYPE_MODEL_PATH = os.path.join(BASE_DIR, "skin_model.pth")
EYE_COLOR_MODEL_PATH = os.path.join(BASE_DIR, "eye_color_model.pth")
ACNE_MODEL_PATH = os.path.join(BASE_DIR, "acne.pth")

# ----------------------
# 🧠 Model Definitions
# ----------------------
class SkinCNN(nn.Module):
    def __init__(self):
        super(SkinCNN, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(3, 16, 3), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3), nn.ReLU(), nn.MaxPool2d(2)
        )
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 30 * 30, 128), nn.ReLU(),
            nn.Linear(128, 3)
        )
    def forward(self, x):
        return self.conv(x), self.fc(self.conv(x))

class EyeColorResNet(nn.Module):
    def __init__(self, num_classes=6):
        super(EyeColorResNet, self).__init__()
        self.base_model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.base_model.fc = nn.Linear(self.base_model.fc.in_features, num_classes)
    def forward(self, x):
        return self.base_model(x)

class AcneResNet(nn.Module):
    def __init__(self, num_classes=5):
        super(AcneResNet, self).__init__()
        self.backbone = models.resnet18(weights=None)
        self.backbone.fc = nn.Linear(self.backbone.fc.in_features, num_classes)
    def forward(self, x):
        return self.backbone(x)

# ----------------------
# 🔁 Image Transforms
# ----------------------
transform_type = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
])

transform_eye = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

transform_acne = transforms.Compose([
    transforms.Resize((640, 640)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ----------------------
# ⚙️ Load Models
# ----------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

type_model = SkinCNN()
type_model.load_state_dict(torch.load(SKIN_TYPE_MODEL_PATH, map_location=device))
type_model.to(device).eval()

eye_model = EyeColorResNet(num_classes=6)
eye_model.load_state_dict(torch.load(EYE_COLOR_MODEL_PATH, map_location=device))
eye_model.to(device).eval()

acne_model = AcneResNet(num_classes=5)
acne_model.load_state_dict(torch.load(ACNE_MODEL_PATH, map_location=device))
acne_model.to(device).eval()

# ----------------------
# 🏷️ Class Labels
# ----------------------
skin_type_labels = ['dry', 'normal', 'oily']
eye_color_labels = ['Amber', 'Blue', 'Brown', 'Green', 'Grey', 'Hazel']
acne_labels = ['0', '1', '2', '3', 'Clear']

# ----------------------
# 🔮 Prediction Functions
# ----------------------
def predict_acne(image: Image.Image) -> dict:
    image = image.convert("RGB")
    input_tensor = transform_acne(image).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = acne_model(input_tensor)
        probs = torch.softmax(outputs, dim=1).cpu().numpy()[0]
        pred_idx = probs.argmax()
        confidence = probs[pred_idx]
    return {
        "acne_pred": acne_labels[pred_idx],
        "acne_probs": probs.tolist(),
        "acne_confidence": float(confidence)
    }

def predict(image: Image.Image) -> dict:
    image = image.convert("RGB")
    try:
        face_image, left_closed, right_closed = detect_and_crop_face(image)
        left_eye = crop_left_eye(image)
        right_eye = crop_right_eye(image)
    except ValueError as e:
        return {"error": str(e)}

    input_type = transform_type(face_image).unsqueeze(0).to(device)
    with torch.no_grad():
        type_out = type_model(input_type)[1]
        type_probs = F.softmax(type_out, dim=1).cpu().numpy()[0]
        type_pred = skin_type_labels[int(type_probs.argmax())]

    # Eye color logic with per-eye closed check
    if left_closed:
        left_eye_color = "Eyes Closed"
    else:
        input_left_eye = transform_eye(left_eye).unsqueeze(0).to(device)
        with torch.no_grad():
            left_eye_out = torch.sigmoid(eye_model(input_left_eye)).cpu().numpy()[0]
        left_eye_dict = dict(zip(eye_color_labels, [float(p) for p in left_eye_out]))
        left_eye_color = max(left_eye_dict, key=left_eye_dict.get)

    if right_closed:
        right_eye_color = "Eyes Closed"
    else:
        input_right_eye = transform_eye(right_eye).unsqueeze(0).to(device)
        with torch.no_grad():
            right_eye_out = torch.sigmoid(eye_model(input_right_eye)).cpu().numpy()[0]
        right_eye_dict = dict(zip(eye_color_labels, [float(p) for p in right_eye_out]))
        right_eye_color = max(right_eye_dict, key=right_eye_dict.get)

    acne_result = predict_acne(face_image)

    return {
        "type_pred": type_pred,
        "type_probs": type_probs.tolist(),
        "left_eye_color": left_eye_color,
        "right_eye_color": right_eye_color,
        "cropped_face": face_image,
        **acne_result,
    }
