# -*- coding: utf-8 -*-
"""
Script para realizar la clasificacion del Dataset a traves de YOLOV11 usando diferentes modelos y multiples imagenes
Actualizado: 10 de septiembre de 2025
"""

# ------ Librerías ------------------------------------------------------------------
import os
import csv

from ultralytics import YOLO

# ------------ Funciones ------------------------------------------------------------
def Model_list(base_path: str, device_type: str) -> list:
    """
    Analiza la ruta donde se encuentran los modelos y retorna una lista de tuplas de la forma [(name_1, model_1), ... ,(name_n, model_n)].

    Args:
        base_path   (str): Ruta donde se encuentran las carpetas con los modelos entrenados.
        device_type (str): Nombre del dispositivo donde se realiza el entrenamiento "Cuda" o "CPU".

    Returns:
        List: Retorna una lista de tuplas que contiene los modelos y sus nombres listos para trabajar en el dispositivo especificado.
    """  
    Models = []

    for path in os.listdir(base_path):                              # Por cada nombre en carpeta dodne se encuentran los modelos
        Complete_Path = f"{base_path}\\{path}\\weights\\best.pt"    # Obtiene la ruta del modelo
        
        if (os.path.exists(Complete_Path)):                         # Si esta ruta existe:
            model = YOLO(Complete_Path)                             # Carga el modelo
            model.to(device_type)                                   # Especifica en que dispositivo se ejecutan
            Models.append((path, model))                            # Anexa la tupla a la lista

    return Models

def Make_Header(models: list) -> list:
    """
    Realiza el encabezado del documento de resultados teniendo en cuenta todos los modelos que se usaran.

    Args:
        models  (list): Lista con la tupla de modelos (nombre, modelos).

    Returns:
        List: Retorna una lista con los encabezados listos para el documento de salida.
    """  
    Header = ["Ruta", "Main_Label"]             # Contenido base (Ruta y etiqueta de la base de datos)
        
    for name, _ in models:                      
        Header.append(f"{name} - prediction")   # Prediccion realizada por el modelo
        Header.append(f"{name} - conf")         # Confiabilidad con la que el modelo realiza la prediccion
        Header.append(f"{name} - time [ms]")    # Tiempo de ejecucion de la prediccion

    return Header

# -----------------------------------------------------------------------------------

if __name__ == "__main__":

    # -------- Variables ------------------------------------------------------------
    batch_size  = 20                                                                            # Cantidad de imagenes que se agrupan y analizan al tiempo
    csv_path    = "..\\DB_Embarcaciones.csv"                                                    # Ruta donde se encuentra la base de datos
    model_dir   = "..\\Model_Training\\YoloV11_Clasification_Experimental-Result\\runs"         # Ruta donde se encuentran los modelos clasificadores
    output_path = f"..\\YoloV11_Clasification-Results_Ryzen7-9800X3D_Batch_{batch_size}.csv"    # Ruta donde se exportaran los resultados
    device      = "cpu"                                                                         # Dispositivo que procesa, puede ser CPU o CUDA

    with open(csv_path, mode="r", newline='', encoding='utf-8') as infile, \
         open(output_path, mode="w", newline='', encoding='utf-8') as outfile:

        Models = Model_list(model_dir, device)                  # Examina las carpetas con los modelos y los importa en una lista de tuplas [(nombre, modelo), ...]

        reader = csv.DictReader(infile)                         # Lector de la base de datos
        Header = Make_Header(Models)                            # Crea el Header para los resultados
        writer = csv.DictWriter(outfile, fieldnames=Header)     # Escritor del archivo de resultados
        writer.writeheader()                                    # Escribe el encabezado de los resultados


        Batch = []                                              # Lista que agrupa la ruta de las imagenes
        Data = []                                               # Lista que agrupa diccionarios con los resultados por imagen analizada
        Count = 0                                               # Contador auxiliar para saber cuantas imagenes se analizaron
        
        for row in reader:                                                              # Por cada elemento del archivo CSV
            
            if row["Image_Name"]!="N/A":                                                # Si el elemento contiene una imagen la procesa
                Ruta_Image= f"{row["Path"]}\\{row["Image_Path"]}\\{row["Image_Name"]}"  # Arma la ruta de la imagen
                Batch.append(Ruta_Image)                                                # Agrupa la ruta al Batch
                Data.append({"Ruta": Ruta_Image, "Main_Label": row["Main_Label"]})      # Agrupa la parte inicial de los diccionarios por cada imagen en el Batch

            if (len(Batch)==batch_size):                                                # Si la cantidad de elementos en el Batch alcanza el tamaño definido
                for name, model in Models:                                              # Por cada modelo en la lista, procesa el Batch
                    predict = model(Batch, verbose=False)

                    for i in range(len(predict)):                                       # Una vez procesado el batch, analiza los resultados de cada imagen
                        Data[i][f"{name} - prediction"] = predict[i].probs.top1         # El resultado de prediccion
                        Data[i][f"{name} - conf"] = predict[i].probs.top1conf.item()    # La confiabilidad de prediccion
                        Data[i][f"{name} - time [ms]"] = sum(predict[i].speed.values()) # El tiempo de analisis de la imagen

                for item in Data:                                       # Por cada diccionario de resultados relacionado a una imagen
                    writer.writerow(item)                               # Lo escribe como una columna en el CSV de resultados

                print(f"Batch Finalizado, ultima imagen: {Batch[-1]}")
                Count += len(Data)
                Batch = []                                              # Limpia el batch
                Data = []                                               # Limpia la lista de diccionarios de resultados

        if Batch:                                                       # Realiza el proceso de analizar el Batch en dado caso que sobren imagenes y no hayan mas elementos en la base de datos
            for name, model in Models:
                predict = model(Batch, verbose=False)

                for i in range(len(predict)):
                    Data[i][name] = name
                    Data[i][f"{name} - prediction"] = predict[i].probs.top1
                    Data[i][f"{name} - conf"] = predict[i].probs.top1conf.item()
                    Data[i][f"{name} - time [ms]"] = sum(predict[i].speed.values())

            for item in Data:
                writer.writerow(item)

            print(f"Batch Finalizado (último batch incompleto), última imagen: {Batch[-1]}")
            Count += len(Data)

        print(Count)