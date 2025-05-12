from PIL import Image
import os

def recortar_detecciones_yolo(image_path, label_path, output_folder):
    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    with open(label_path, "r") as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        parts = line.strip().split()
        if len(parts) != 5:
            continue
        cls, x_center, y_center, w, h = map(float, parts)

        x_center *= width
        y_center *= height
        w *= width
        h *= height

        left = int(x_center - w / 2)
        upper = int(y_center - h / 2)
        right = int(x_center + w / 2)
        lower = int(y_center + h / 2)

        cropped = image.crop((left, upper, right, lower))
        filename = f"{os.path.splitext(os.path.basename(image_path))[0]}_crop{idx}.jpg"
        output_path = os.path.join(output_folder, filename)
        cropped.save(output_path)
        print(f"[✔] Recorte guardado: {output_path}")

# --- Recorre la estructura completa desde la raíz ---
root_folder = "..\\correos\\"  # ← Cambia esto a tu ruta principal

for dirpath, dirnames, filenames in os.walk(root_folder):
    for dirname in dirnames:
        if dirname.startswith("images_"):
            images_path = os.path.join(dirpath, dirname)
            index = dirname.split("_")[1]
            labels_path = os.path.join(dirpath, f"labels_{index}")

            # Solo proceder si existe la carpeta de etiquetas
            if not os.path.exists(labels_path):
                print(f"[ ] No se encontró la carpeta de etiquetas: {labels_path}")
                continue

            recortes_path = os.path.join(dirpath, f"recortes_{index}")
            os.makedirs(recortes_path, exist_ok=True)

            for filename in os.listdir(images_path):
                if filename.lower().endswith(".jpg"):
                    base_name = os.path.splitext(filename)[0]
                    image_file = os.path.join(images_path, filename)
                    label_file = os.path.join(labels_path, base_name + ".txt")

                    if os.path.exists(label_file):
                        recortar_detecciones_yolo(image_file, label_file, recortes_path)
                    else:
                        print(f"[ ] No se encontró etiqueta para: {filename}")
