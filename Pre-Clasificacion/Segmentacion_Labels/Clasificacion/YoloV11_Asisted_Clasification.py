# -*- coding: utf-8 -*-
"""
Script para pre-clasificar las imagenes de la base de datos manualmente con asistencia del modelo YOLOV11
Actualizado: 22 de julio de 2025
"""

# ------ Librerías -----------------------------------------------------------------------------------
import csv

import cv2
from ultralytics import YOLO

# ------------ Funciones -----------------------------------------------------------------------------
def Asisted_Clasification(path: str, model_path: str) -> int:
    """
    Abre una ventana que contiene la imagen a analizar. Si se presiona "y", se clasifica como 1 y si no como 0.

    Args:
        path (str):         Ruta relativa o absoluta hacia el archivo de imagen a analizar.
        model_path (str):   Ruta relativa o absoluta hacia el modelo de YOLO entrenado.

    Returns:
        int: Retorna la etiqueta como un entero, si es 1 significa (presencia de embarcación) y si es 0 como (ausencia de embarcación).
    """
    posicion = (50, 50)                 # Posicion en la que se mostrara el texto
    fuente = cv2.FONT_HERSHEY_SIMPLEX   # Fuente del texto
    tamaño = 1.2                        # Tamaño del texto

    model = YOLO(model_path)                        # YOLOV11 con el entrenamiento custom
    predict = model(path, verbose=False)[0].probs   # Prediccion del modelo YOLOV11

    if ((predict.top1conf.item() > 0.4 and predict.top1 == 1) or (predict.top1conf.item() < 0.6 and predict.top1 == 0)):       # Si con un 50% de confiabilidad cree que es una embarcacion o con un 40% de confiabilidad cree que no es nada

        print(path)                                                                             # Imprime la ruta de la imagen
        imagen = cv2.imread(path)                                                               # Lee la imagen
        texto = f"Pred: {predict.top1}, Conf: {predict.top1conf.item():.2f}"                    # Texto de la prediccion

        cv2.putText(imagen, texto, posicion, fuente, tamaño, (0, 0, 0), 4, cv2.LINE_AA)         # Coloca el texto en la imagen con un borde negro
        cv2.putText(imagen, texto, posicion, fuente, tamaño, (0, 140, 255), 2, cv2.LINE_AA) 

        cv2.imshow("Detecciones Radar", imagen)             # Muestra la imagen en una ventana emergente
        Tecla = cv2.waitKey(0) & 0XFF                       # Espera indefinidamente hasta presionar una tecla

        if(Tecla == ord('y')):                              # Si la tecla es "y", devolver 1 (Etiqueta para presencia de embarcaciones)
            print("✅")  
            return 1 
        else:                                               # Si se presiona otra tecla devolver 0 (Etiqueta para ausencia de embarcaciones)
            print("❌")  
            return 0                  
    else:
        return -1                                           # Si no cumple el filtro del modelo YOLO retorna -1

# ----------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # -------- Variables -----------------------------------------------------------------------------
    csv_path = "..\\"                           # Ruta de la carpeta donde se encuentra el archivo CSV
    model_path = "..\\Asisted_Clasification.pt" # Ruta de la carpeta donde se el modelo de YOLO entrenado

    # -------- Lectura y escritura del CSV -----------------------------------------------------------
    with open(f"{csv_path}Registros_Clasificados.csv", mode="r", newline='', encoding='utf-8') as infile, \
         open(f"{csv_path}Registros_Clasificados_Asistido.csv", mode="w", newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)                                     # Lector del CSV 
        writer = csv.DictWriter(outfile, fieldnames=(reader.fieldnames))    # Escribe el Header

        writer.writeheader()

        for row in reader:                     # Por cada elemento del archivo CSV
            if row["Image_Name"]!="N/A":       # Si encuentra una imagen
                Ruta_Image= f"{row["Path"]}\\{row["Image_Path"]}\\{row["Image_Name"]}"      # Obtiene su ruta
                results = Asisted_Clasification(Ruta_Image,model_path)                      # La clasifica

                if (results!=-1):
                    row["Main_Label"] = results     # En dado caso que se verifique manualmente sobreescribe la etiqueta

            writer.writerow(row)
            
    # ------------------------------------------------------------------------------------------------
