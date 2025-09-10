# -*- coding: utf-8 -*-
"""
Script para realizar el entrenamiento del modelo de deteccion de YOLOV11 a traves de Bounding-Boxes
Actualizado: 10 de septiembre de 2025
"""

# ------ Librerías ------------------------------------------------------------------
import os
import csv
import random
import shutil
import yaml

from ultralytics import YOLO

# ------------ Funciones ------------------------------------------------------------
def copiar(path :str, imagenes :list, subset: str) -> None:
    """
    Copia las imagenes localizadas en una ruta a otra teniendo en cuenta su etiqueta de clasificacion y al Dataset al que pertenecen (Entrenamiento o validacion) ademas de copiar su respectivo label de bounding boxes

    Parámetros:
        path      (str): Ruta a la carpeta que contiene las subcarpetas 'images' y 'labels' con las imágenes clasificadas.
        imagenes (list): Lista que contiene las tuplas de la forma (Ruta de la imagen, bounding box).
        subset    (str): Carpeta destino del Dataset para todas las imagenes de la lista (Entrenamiento o validacion).
    """
    img_dir   = os.path.join(path, "Dataset", "images", subset)     # Ruta de la carpeta con las imagenes
    label_dir = os.path.join(path, "Dataset", "labels", subset)     # Ruta de la carpeta con los labels
    
    for i, (ruta, segmentos) in enumerate(imagenes):                # Analiza todos los elementos de la lista de imagenes, en un formato de dupla doble (i, (ruta, segmento)).
        label = "0" if segmentos!="N/A" else ""                     # Si el segmento es "N/A" (no tiene) su respectivo label es "" (no hay embarcacion), de otra manera es 0 (Hay embarcacion)
        ext = os.path.splitext(ruta)[1]                             # Obtiene el tipo de extension de la imagen
        nombre_base = f"img_{subset}_{label}_{i}"                   # Los labels y las imagenes tienen el mismo nombre, por ende se genera el nombre base en el formato "img_{subset}_{label}_{i}"
        nuevo_nombre = f"{nombre_base}{ext}"                        # Nombre para la imagen con la extension que posee
        nuevo_label = f"{nombre_base}{".txt"}"                      # Nombre de la etiqueta con extension .txt
        destino_img = os.path.join(img_dir, nuevo_nombre)           # Path destino de la imagen en el dataset
        destino_label = os.path.join(label_dir, nuevo_label)        # Path destino del label en el dataset
        
        shutil.copy2(ruta, destino_img)                             # Copia las imagenes desde una ruta a la otra
        if label == "0":
            with open(destino_label, "w") as f:                     # Genera el label .txt escribiendo todas las bounding boxes que se encuentren
                for linea in segmentos:
                    valores = linea.strip("[]'").split()            # quita corchetes/comillas y separa por espacio
                    valores[0] = "0"                                # fuerza el primer valor a 0
                    f.write(" ".join(valores) + "\n")
                    
def Generador_Yaml(path: str, Etiquetas: dict, nombre:str) -> None:
    """
    Genera un archivo YAML para YOLOV11.

    Parámetros:
        path           (str): Ruta raíz del dataset.
        Etiquetas     (dict): Diccionario que contiene las etiquetas en el formato index: clase.
        nombre         (str): Nombre del archivo a generar.
    """

    yaml_data = {     # Estructura del archivo Yaml
        'path': os.path.abspath(os.path.join(path, "Dataset")),
        'train': 'images/train',
        'val': 'images/val',
        'names': Etiquetas
    } 

    ruta_salida = os.path.join(path, "Dataset",nombre)                              # Ruta destino del archivo Yaml
    with open(ruta_salida, 'w') as f:   yaml.dump(yaml_data, f, sort_keys=False)    # Genera el archivo Yaml

def YOLO_Training(path: str, results_name: str, nombre_yaml: str) -> None:
    """
    Entrena un modelo YOLO utilizando las imágenes ubicadas en la ruta especificada.

    Parámetros:
        path         (str): Ruta a la carpeta que contiene el archivo .yaml
        results_name (str): Nombre de la carpeta donde se guardan los resultados en \\run\\results_name
        nombre_yaml  (str): Nombre del archivo YAML del dataset

    """
    model = YOLO(f"{path}\\yolo11n.pt")                     # Carga el modelo base clasificador de YoloV11

    model.train(
        data=os.path.join(path, "Dataset", nombre_yaml),     # Carpeta con train/ y val/
        epochs=100,                                          # Número de épocas
        imgsz=416,                                           # Tamaño de imagen recomendado para cls
        batch=128,                                            # Tamaño del batch
        project=f"{path}\\runs",                             # Carpeta donde guarda resultados
        name=results_name,                                   # Nombre del experimento
        device = 0,                                          # Dispositivo que se encargara del entrenamiento
        amp=True,                                            # Precision Mixta -> Tensor Cores
        cache=False,                                         # Cache de las imagenes en la memoria Ram
        workers=8                                            # Numero de Hilos del procesador
    )

# -----------------------------------------------------------------------------------

if __name__ == "__main__":

    # -------- Variables ------------------------------------------------------------
    csv_path    = "..\\DB_Embarcaciones.csv"                                       # Ruta de la carpeta donde se encuentra el archivo CSV
    output_dir  = "..\\Model_Training\\YoloV11_Segmentation_Experimental-Result"   # Ruta donde se copiara el Dataset en el formato adecuado
    train_ratio = 0.8                                                              # 80% entrenamiento, 20% validación
    imagenes    = []                                                               # Lista que contendra los pares (Ruta, Bounding Boxes) extraidos del .CSV

    # ------ Creacion de la carpeta con el Dataset con la estructura requerida ------

    if not os.path.exists(os.path.join(output_dir,"Dataset")):                  # Si la carpeta del Dataset no existe, lo crea y organiza

        for subset in ["images", "labels"]:                                     # Creacion de las carpetas
            for subfolder in ["train", "val"]:
                dir_path = os.path.join(output_dir,"Dataset", subset, subfolder)
                if not os.path.exists(dir_path):    os.makedirs(dir_path)
                

        # -------- Lectura del CSV y creacion de la base de datos -------------------

        with open(csv_path, mode="r", newline='', encoding='utf-8') as infile:
            
            reader = csv.DictReader(infile)         # Lee el Header Original

            for row in reader:                      # Por cada elemento del archivo CSV
                if row["Image_Name"] != "N/A" and row["Main_Label"] in ["0", "1"]:

                    ruta = f"{row["Path"]}\\{row["Image_Path"]}\\{row["Image_Name"]}"   # Path de la imagen
                    label = row["Segment"]                                              # Bounding boxes
                    
                    if label!="N/A":                                                    # Si el contenido es una lista en lugar de "N/A"
                        label = label.strip("[]").split(",")                            # Elimina los caracteres "[]" y separa por las "," presentes
                        label = [item.strip().strip("'").strip('"') for item in label]  # A cada string separado en la lista, elimina los elementos "" y '' que los identifican como string para obtener la lista de string original

                    if os.path.exists(ruta):    imagenes.append((ruta, label))          
                    
        random.shuffle(imagenes)                            # Mezclar aleatoriamente las imagenes para dividirlas uniformemente entre Train y Validation
        split_index = int(len(imagenes) * train_ratio)      # Divide imágenes en train y val
        train_imgs = imagenes[:split_index]
        val_imgs = imagenes[split_index:]

        copiar(output_dir, train_imgs, "train")                                                 # Copiar imagenes del entrenamiento
        copiar(output_dir, val_imgs, "val")                                                     # Copiar imagenes de validacion
        Generador_Yaml(output_dir, {0: "embarcacion"}, "dataset.yaml")    # Genera el archivo Yaml

    else:
        print("El path ya existe por ende se procede al entrenamiento del modelo")

    # # ---------------- Realizar el entrenamiento del modelo -------------------------
    YOLO_Training(output_dir,"Modelo_416_Nano", "dataset.yaml") 