# -*- coding: utf-8 -*-
"""
Script para corroborar los cambios de "Labels" entre archivos .CSV
Actualizado: 24 de julio de 2025
"""

# ------ Librerías -----------------------------------------------------------------------------------
import csv
import cv2

# ------------ Funciones -----------------------------------------------------------------------------
def Manual_Clasification(path: str, actual_label: str) -> int:
    """
    Abre una ventana que contiene la imagen a analizar. Si se presiona "y", se clasifica como 1 y si no como 0.

    Args:
        path         (str): Ruta relativa o absoluta hacia el archivo de imagen a analizar.
        actual_label (str): Ultima etiqueta que posee la imagen (0 ausencia de embarcaciones, 1 presencia de embarcacion)
    Returns:
        int: Retorna la etiqueta como un entero, si es 1 significa (presencia de embarcación) y si es 0 como (ausencia de embarcación).
    """
    posicion = (50, 50)                 # Posicion en la que se mostrara el texto
    fuente = cv2.FONT_HERSHEY_SIMPLEX   # Fuente del texto
    tamaño = 1.2                        # Tamaño del texto

    print(path)                                         # Imprime la ruta de la imagen que se esta analizando
    imagen = cv2.imread(path)                           # Lee la imagen
    texto = f"Actual label: {actual_label}"             # Texto de la etiqueta clasificada en el archivo mas reciente

    cv2.putText(imagen, texto, posicion, fuente, tamaño, (0, 0, 0), 4, cv2.LINE_AA)         # Coloca el texto en la imagen con un borde negro
    cv2.putText(imagen, texto, posicion, fuente, tamaño, (0, 140, 255), 2, cv2.LINE_AA) 

    
    cv2.imshow("Detecciones Radar", imagen)   # Muestra la imagen en una ventana emergente
    Tecla = cv2.waitKey(0) & 0XFF             # Espera indefinidamente hasta presionar una tecla

    if(Tecla == ord('y')):                    # Si la tecla es "y", devolver 1 (Etiqueta para presencia de embarcaciones)
        print("✅")  
        return 1 
    else:                                     # Si se presiona otra tecla devolver 0 (Etiqueta para ausencia de embarcaciones)
        print("❌")  
        return 0                  

# ----------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # -------- Variables -----------------------------------------------------------------------------
    base_path = "..\\"                                                  # Ruta de la carpeta donde se encuentran los archivos CSV
    csv0_name = "Registros_Clasificados.csv"                            # Nombre del archivo .CSV anterior
    csv1_name = "Registros_Clasificados_Asistido.csv"                   # Nombre del archivo .CSV reciente
    csvoutput_name = "Registros_Clasificados_Asistido_Auditados.csv"    # Nombre del nuevo archivo .CSV 

    # -------- Lectura de los CSV --------------------------------------------------------------------
    with open(f"{base_path}{csv0_name}", mode="r", newline='', encoding='utf-8') as f0, \
         open(f"{base_path}{csv1_name}", mode="r", newline='', encoding='utf-8') as f1, \
         open(f"{base_path}{csvoutput_name}", mode="w", newline='', encoding='utf-8') as fout:
        
        reader_0 = csv.DictReader(f0)                                   # Lector del primer CSV
        reader_1 = csv.DictReader(f1)                                   # Lector del segundo CSV
        writer   = csv.DictWriter(fout,fieldnames=reader_1.fieldnames)  # Escribe el Header en el nuevo archivo CSV
        writer.writeheader()

        for row_0, row_1 in zip(reader_0, reader_1):        # Itera sobre ambos lectores al tiempo y cada linea se guarda en las variables row_#
            
            if row_0["Image_Name"]==row_1["Image_Name"] and row_0["Main_Label"]!=row_1["Main_Label"]:   # Si la imagen coincide y el Label es diferente
                full_path = f"{row_1['Path']}\\{row_1['Image_Path']}\\{row_1['Image_Name']}"            # Genera la ruta de la imagen
                new_label = Manual_Clasification(full_path, row_1["Main_Label"])                        # Analiza manualmente la imagen
                row_1["Main_Label"] = new_label                                                         # Actualiza al Label analizado manualmente
            
            writer.writerow(row_1)                                                                      # Escribe en el nuevo archivo la fila del CSV mas reciente con el analisis manual

