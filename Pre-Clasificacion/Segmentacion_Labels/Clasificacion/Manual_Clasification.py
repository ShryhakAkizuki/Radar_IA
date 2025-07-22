# -*- coding: utf-8 -*-
"""
Script para pre-clasificar las imagenes de la base de datos manualmente
Actualizado: 22 de julio de 2025
"""

# ------ Librerías -----
import os
import csv

import cv2

# ------------ Funciones ------------
def Manual_Clasification(path: str) -> int:
    """
    Abre una ventana que contiene la imagen a analizar. Si se presiona "y", se clasifica como 1 y si no como 0.

    Args:
        path (str): Ruta relativa o absoluta hacia el archivo de imagen a analizar.
    Returns:
        int: Retorna la etiqueta como un entero, si es 1 significa (presencia de embarcación) y si es 0 como (ausencia de embarcación).
    """
    
    # Imprime la ruta en la cual se esta analizando la imagen para tener una referencia en consola
    print(path)

    # Mostrar la imagen con OpenCV
    cv2.imshow("Detecciones Radar", cv2.imread(path))

    Tecla = cv2.waitKey(0)  # Espera indefinidamente hasta presionar una tecla

    if(Tecla == ord('y')): return 1 # Si la tecla es y, devolver 1 (Etiqueta para presencia de embarcaciones)
    else: return 0                  # Si se presiona otra tecla devolver 0 (Etiqueta para ausencia de embarcaciones)

if __name__ == "__main__":

    # -------- Variables -----------------------------------------------------------
    csv_path = "..\\"      # Ruta de la carpeta donde se encuentra el archivo CSV

    # -------- Lectura y escritura del CSV -----------------------------------------------------------
    with open(f"{csv_path}Registros.csv", mode="r", newline='', encoding='utf-8') as infile, \
         open(f"{csv_path}Registros_Clasificados.csv", mode="w", newline='', encoding='utf-8') as outfile:

        
        reader = csv.DictReader(infile)         # Lee el Header Original
        Nuevas_Columnas = ["Main_Label"         # Nuevo Header
        ]

        writer = csv.DictWriter(outfile, fieldnames=(reader.fieldnames+Nuevas_Columnas))    # Escribe el nuevo Header
        writer.writeheader()

        for row in reader:                     # Por cada elemento del archivo CSV
            if row["Image_Name"]!="N/A":       # Si encuentra una imagen
                Ruta_Image=f"{row["Path"]}\\{row["Image_Path"]}\\{row["Image_Name"]}"   # Obtiene su ruta

                results = Manual_Clasification(Ruta_Image) # La clasifica

            else:
                results = -1                # Si no la encuentra, obtiene valores por defecto

            row["Main_Label"] = results     # Escribe los valores respectivos al CSV
            writer.writerow(row)
    # -------------------------------------------------------------------------------------------------
