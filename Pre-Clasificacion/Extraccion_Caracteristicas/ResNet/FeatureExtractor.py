import os
from PIL import Image
import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights

# Modelo ResNet50 sin la capa de clasificación
weights = ResNet50_Weights.DEFAULT
model = resnet50(weights=weights)
model.eval()
feature_extractor = torch.nn.Sequential(*list(model.children())[:-1])
transform = weights.transforms()

def extract_features(image_path):
    image = Image.open(image_path).convert("RGB")
    image_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        features = feature_extractor(image_tensor)
    return features.squeeze().numpy()

def process_recortes_with_oswalk(root_folder):
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for dirname in dirnames:
            if dirname.startswith("recortes_"):
                recortes_path = os.path.join(dirpath, dirname)
                features_dirname = dirname.replace("recortes", "features")
                features_path = os.path.join(dirpath, features_dirname)
                os.makedirs(features_path, exist_ok=True)

                for filename in os.listdir(recortes_path):
                    if filename.lower().endswith(".jpg"):
                        try:
                            img_path = os.path.join(recortes_path, filename)
                            features = extract_features(img_path)
                            npy_filename = os.path.splitext(filename)[0] + ".npy"
                            npy_path = os.path.join(features_path, npy_filename)
                            np.save(npy_path, features)
                            print(f"[✓] Guardado: {npy_path}")
                        except Exception as e:
                            print(f"[✗] Error con {filename}: {e}")

if __name__ == "__main__":
    root_folder = "..\\correos\\"
    process_recortes_with_oswalk(root_folder)