from ultralytics import YOLO
import os

# Carga del modelo previamente entrenado
model = YOLO("Clasificacion_Correos/best.pt")

# Ruta raíz que contiene todas las carpetas de años
root_folder = "..\\correos\\"  # Cambia esto al nombre real de tu carpeta raíz

# Recorre todas las carpetas y subcarpetas
for dirpath, dirnames, filenames in os.walk(root_folder):
    # Filtra carpetas que parecen ser de imágenes
    if os.path.basename(dirpath).startswith("images_"):
        # Filtra archivos .jpg
        image_files = [f for f in filenames if f.lower().endswith(".jpg")]

        for image_file in image_files:
            image_path = os.path.join(dirpath, image_file)
            results = model(image_path)

            # Acumula detecciones
            all_boxes = []
            for result in results:
                all_boxes.extend(result.boxes)

            if all_boxes:

                # Crea carpeta de etiquetas solo si hay detecciones
                label_folder = os.path.join(os.path.dirname(dirpath), "labels_" + os.path.basename(dirpath))
                os.makedirs(label_folder, exist_ok=True)

                # Nombre base del archivo
                base = os.path.splitext(image_file)[0]
                label_path = os.path.join(label_folder, base + ".txt")
                
                with open(label_path, "w") as f:
                    for box in all_boxes:
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        x_center, y_center, width, height = box.xywhn[0]
                        f.write(f"{cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

                print(f"[✔] Etiquetas generadas: {image_path} → {label_path}")
            else:
                print(f"[ ] Sin detecciones en: {image_path}")