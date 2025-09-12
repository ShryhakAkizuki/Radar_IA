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
def Model_Path(base_path: str) -> list:
    """
    Analiza la ruta donde se encuentran los modelos y retorna una lista de tuplas de la forma [(name_1, model_path1), ... ,(name_n, model_pathn)].

    Args:
        base_path   (str): Ruta donde se encuentran las carpetas con los modelos entrenados.

    Returns:
        List: Retorna una lista de tuplas que contiene la ruta donde se encuentran los modelos y sus nombres listos para trabajar en el dispositivo especificado.
    """  
    Models = []

    for name in os.listdir(base_path):                              # Por cada nombre en carpeta dodne se encuentran los modelos
        Complete_Path = f"{base_path}\\{name}\\weights\\best.pt"    # Obtiene la ruta del modelo
        
        if (os.path.exists(Complete_Path)):                         # Si esta ruta existe:
            Models.append((name, Complete_Path))                    # Anexa la tupla a la lista

    return Models

def Make_Header(models: list) -> list:
    """
    Realiza el encabezado del documento de resultados teniendo en cuenta todos los modelos que se usaran.

    Args:
        models  (list): Lista con la tupla de modelos (nombre, path_modelos).

    Returns:
        List: Retorna una lista con los encabezados listos para el documento de salida.
    """  
    Header = ["Ruta", "Main_Label"]             # Contenido base (Ruta y etiqueta de la base de datos)
        
    for name, _ in models:                      
        Header.append(f"{name} - prediction")   # Prediccion realizada por el modelo
        Header.append(f"{name} - conf")         # Confiabilidad con la que el modelo realiza la prediccion
        Header.append(f"{name} - time [ms]")    # Tiempo de ejecucion de la prediccion

    return Header

def Run_model(model_path: tuple, device_type: str, batch: list) -> dict:
    """
    Ejecuta el modelo especificado bajo la tecnologia especificada, procesando una lista de imagenes y retornando sus resultados en un diccionario.

    Args:
        model_path  (tuple): Lista con la tupla de modelos (nombre, path_modelos).
        device_type   (str): Tecnologia en la que se ejecutara el dispositivo "CPU" o "CUDA"
        batch        (list): Lista con las rutas asociadas a la coleccion de imagenes a procesar.
    
    Returns:
        Dict: Retorna un diccionario con los resultados asociados a cada imagen analizada con el respectivo modelo.
    """ 
    Data = {}

    model = YOLO(model_path[1])             # Carga el modelo a utilizar                        
    model.to(device_type)                   # Le especifica donde se ejecutara
    predict = model(batch, verbose=False)   # Realiza el procesamiento del conjunto de imagene

    for item, result in zip(batch,predict): # Por cada resultado obtenido, guarda el conjunto de datos en un diccionario asociado a la imagen procesada.
        Data[item] = {  f"{model_path[0]} - prediction": result.probs.top1,
                        f"{model_path[0]} - conf": result.probs.top1conf.item(),
                        f"{model_path[0]} - time [ms]": sum(result.speed.values())
                     }

    return Data

# -----------------------------------------------------------------------------------

if __name__ == "__main__":

    # -------- Variables ------------------------------------------------------------
    batch_size  = 20                                                                            # Cantidad de imagenes que se agrupan y analizan al tiempo
    csv_path    = "..\\DB_Embarcaciones.csv"                                                    # Ruta donde se encuentra la base de datos
    model_dir   = "..\\Model_Training\\YoloV11_Clasification_Experimental-Result\\runs"         # Ruta donde se encuentran los modelos clasificadores
    output_path = f"..\\YoloV11_Clasification-Results_Ryzen7-9800X3D_Batch_{batch_size}_Test2.csv"    # Ruta donde se exportaran los resultados
    device      = "cpu"                                                                         # Dispositivo que procesa, puede ser CPU o CUDA

    with open(csv_path, mode="r", newline='', encoding='utf-8') as infile, \
         open(output_path, mode="w", newline='', encoding='utf-8') as outfile:

        Models = Model_Path(model_dir)                          # Examina las carpetas con los modelos y los importa en una lista de tuplas [(nombre, model_path), ...]

        reader = csv.DictReader(infile)                         # Lector de la base de datos
        Header = Make_Header(Models)                            # Crea el Header para los resultados
        writer = csv.DictWriter(outfile, fieldnames=Header)     # Escritor del archivo de resultados
        writer.writeheader()                                    # Escribe el encabezado de los resultados

        Batch = []                                              # Lista que agrupa la ruta de las imagenes
        Data = {}                                               # Diccionario que agrupa diccionarios con los resultados por imagen analizada a modo de base de datos.
        Count = 0                                               # Contador auxiliar para saber cuantas imagenes se analizaron
        
        # -------- Lectura del CSV y procesamiento de los datos ---------------------
        for row in reader:                                                              # Por cada elemento del archivo CSV
            
            # -------- Agrupamiento de las imagenes en un batch ---------------------
            if row["Image_Name"]!="N/A":                                                # Si el elemento contiene una imagen la procesa
                Ruta_Image= f"{row["Path"]}\\{row["Image_Path"]}\\{row["Image_Name"]}"  # Arma la ruta de la imagen
                Batch.append(Ruta_Image)                                                # Agrupa la ruta al Batch
                Data[Ruta_Image] = {    "Ruta": Ruta_Image,                             # Genera su entrada en la base de datos
                                        "Main_Label": row["Main_Label"]
                                   }
            # -------- Procesamiento del batch de imagenes --------------------------
            if (len(Batch)==batch_size):                                                # Si la cantidad de elementos en el Batch alcanza el tamaño definido
                
                for model in Models:                                                    # Por cada modelo existente
                    Result = Run_model(model, device, Batch)                            # Procesa el conjunto de imagenes
                    for key, value in Result.items():                                   # Adjunta los resultados en la base de datos con la imagen asociada
                        Data[key].update(value)
                
                print(f"Batch Finalizado, ultima imagen: {Batch[-1]}")
                Count += len(Data)
                Batch = []                                              # Limpia el batch
            # -----------------------------------------------------------------------

        # -------- Procesamiento del batch de imagenes restantes por procesar -------
        if Batch:                                                       # Realiza el proceso de analizar el Batch en dado caso que sobren imagenes y no hayan mas elementos en la base de datos
            for model in Models:                                        # Por cada modelo existente
                    Result = Run_model(model, device, Batch)            # Procesa el conjunto de imagenes
                    for key, value in Result.items():                   # Adjunta los resultados en la base de datos con la imagen asociada
                        Data[key].update(value)

            print(f"Batch Finalizado (último batch incompleto), última imagen: {Batch[-1]}")
            Count += len(Data)

        # -------- Guardar el Archivo CSV -------------------------------------------
        for _, row in Data:                                    # Por cada entrada en la base de datos (imagen procesada), adjunta sus resultados al CSV de salida
            writer.writerow(row)                               

        print(Count)