from ultralytics import YOLO
import os

# Cargar modelo YOLO una sola vez
model = YOLO("Clasificacion_Correos/best.pt")

# Carpeta raíz
root_folder = "..\\Paquete01\\"

for dirpath, _, filenames in os.walk(root_folder):
    folder_name = os.path.basename(dirpath)
    if not folder_name.startswith("images_"):
        continue  # Ignora carpetas que no empiecen con 'images_'

    # Extraer índice de la carpeta
    image_index = folder_name.split("_")[1]
    label_folder = os.path.join(os.path.dirname(dirpath), f"labels_{image_index}")

    # Esta vez NO usamos bandera, sino que verificamos en el bucle con un generador
    detections_exist = False

    # Filtrar imágenes .jpg
    image_files = [f for f in filenames if f.lower().endswith(".jpg")]

    for image_file in image_files:
        image_path = os.path.join(dirpath, image_file)
        results = model(image_path)

        # Unir todas las cajas de todos los resultados
        all_boxes = [box for result in results for box in result.boxes]

        if not all_boxes:
            print(f"[ ] Sin detecciones: {image_path}")
            continue

        # Solo crear carpeta una vez, cuando haya la primera detección
        if not detections_exist:
            os.makedirs(label_folder, exist_ok=True)
            detections_exist = True

        label_path = os.path.join(
            label_folder, os.path.splitext(image_file)[0] + ".txt"
        )

        # Guardar etiquetas en formato YOLO
        with open(label_path, "w") as f:
            for box in all_boxes:
                cls = int(box.cls[0])
                x_center, y_center, width, height = box.xywhn[0]
                f.write(f"{cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

        print(f"[✔] Etiquetas generadas: {image_path} → {label_path}")

    if not detections_exist:
        print(f"[ ] Sin detecciones en toda la carpeta: {dirpath}")
