# -*- coding: utf-8 -*-
"""
Script para realizar el entrenamiento del modelo de clasificacion de YOLOV11 - A traves de GPU
Actualizado: 10 de septiembre de 2025
"""

# ------ Librerías ------------------------------------------------------------------
import os
import csv
import random
import shutil

from ultralytics import YOLO

# ------------ Funciones ------------------------------------------------------------
def copiar(path :str, imagenes :list, subset: str) -> None:
    """
    Copia las imagenes localizadas en una ruta a otra teniendo en cuenta su etiqueta de clasificacion y al Dataset al que pertenecen (Entrenamiento o validacion)

    Parámetros:
        path      (str): Ruta a la carpeta que contiene las subcarpetas 'train' y 'val' con las imágenes clasificadas.
        imagenes (list): Lista que contiene las tuplas de la forma (Ruta de la imagen, etiqueta de clasificacion).
        subset    (str): Carpeta destino del Dataset para todas las imagenes de la lista (Entrenamiento o validacion).
    """

    for i, (ruta, label) in enumerate(imagenes):        # Analiza todos los elementos de la lista de imagenes, en un formato de dupla doble (i, (ruta, label)).
        
        ext = os.path.splitext(ruta)[1]                                           # Obtiene el tipo de extension de la imagen
        nuevo_nombre = f"img_{subset}_{label}_{i}{ext}"                           # Renombra la imagen a copiar con el formato "img_{subset}_{label}_{i}{ext}"
        destino = os.path.join(path,"Dataset", subset, label, nuevo_nombre)       # Genera el path destino donde se copiaran las imagenes del Dataset en el formato requerido para YOLOV11
        shutil.copy2(ruta, destino)                                               # Copia los archivos desde una ruta a la otra

def YOLO_Training(path: str, results_name: str) -> None:
    """
    Entrena un modelo YOLO utilizando las imágenes ubicadas en la ruta especificada.

    Parámetros:
        path         (str): Ruta a la carpeta que contiene las subcarpetas 'train' y 'val' con las imágenes clasificadas.
        results_name (str): Nombre de la carpeta donde se guardan los resultados en \\run\\results_name
    """
    model = YOLO(f"{path}\\yolo11n-cls.pt")                     # Carga el modelo base clasificador de YoloV11

    model.train(
        data=os.path.abspath(os.path.join(path,"Dataset")),     # Carpeta con train/ y val/
        epochs=100,                                             # Número de épocas
        imgsz=416,                                              # Tamaño de imagen recomendado para cls
        batch=150,                                               # Tamaño del batch
        project=f"{path}\\runs",                                # Carpeta donde guarda resultados
        name=results_name,                                      # Nombre del experimento
        device=0,                                               # Entrenamiento por GPU
        amp=True,                                               # Precision Mixta -> Tensor Cores
        cache=False,                                           # Cache de las imagenes en la memoria Ram
        workers=8,                                              # Numero de Hilos del procesador
    )

# -----------------------------------------------------------------------------------

if __name__ == "__main__":

    # -------- Variables ------------------------------------------------------------
    csv_path    = "..\\DB_Embarcaciones.csv"                                                    # Ruta de la carpeta donde se encuentra el archivo CSV
    output_dir  = "..\\Model_Training\\YoloV11_Clasification_Experimental-Result"     # Ruta donde se copiara el Dataset en el formato adecuado
    train_ratio = 0.8                                                                           # 80% entrenamiento, 20% validación
    imagenes    = []                                                                            # Lista que contendra los pares (Ruta, Clasificacion) extraidos del .CSV

    # ------ Creacion de la carpeta con el Dataset con la estructura requerida ------

    if not os.path.exists(os.path.join(output_dir,"Dataset")):                  # Si la carpeta del Dataset no existe, lo crea y organiza

        for subset in ["train", "val"]:                                         # Creacion de las carpetas
            for label in ["0", "1"]:
                dir_path = os.path.join(output_dir,"Dataset", subset, label)
                if not os.path.exists(dir_path):    os.makedirs(dir_path)
                

        # -------- Lectura del CSV y creacion de la base de datos -------------------

        with open(csv_path, mode="r", newline='', encoding='utf-8') as infile:
            
            reader = csv.DictReader(infile)         # Lee el Header Original

            for row in reader:                      # Por cada elemento del archivo CSV
                if row["Image_Name"] != "N/A" and row["Main_Label"] in ["0", "1"]:

                    ruta = f"{row["Path"]}\\{row["Image_Path"]}\\{row["Image_Name"]}"
                    if os.path.exists(ruta):    imagenes.append((ruta, row["Main_Label"]))
                    
        random.shuffle(imagenes)                            # Mezclar aleatoriamente las imagenes para dividirlas uniformemente entre Train y Validation
        split_index = int(len(imagenes) * train_ratio)      # Divide imágenes en train y val
        train_imgs = imagenes[:split_index]
        val_imgs = imagenes[split_index:]

        copiar(output_dir, train_imgs, "train")                         # Copiar imagenes del entrenamiento
        copiar(output_dir, val_imgs, "val")                             # Copiar imagenes de validacion

    else:
        print("El path ya existe por ende se procede al entrenamiento del modelo")


    # ---------------- Realizar el entrenamiento del modelo -------------------------

    YOLO_Training(output_dir,"Modelo_416_Nano") 