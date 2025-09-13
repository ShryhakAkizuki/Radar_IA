# -*- coding: utf-8 -*-
"""
Script para realizar la deteccion del Dataset a traves de YOLOV11 usando diferentes modelos y multiples imagenes
de modo que un proceso analiza una imagen completa con todos los modelos
Actualizado: 13 de septiembre de 2025
"""

# ------ Librerías ------------------------------------------------------------------
import os
import csv
import multiprocessing as mp
import math

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
        models  (list): Lista con la tupla de modelos (nombre, modelos).

    Returns:
        List: Retorna una lista con los encabezados listos para el documento de salida.
    """  
    Header = ["Ruta", "Main_Label", "Segments"] # Contenido base (Ruta, etiqueta y segmentos de la base de datos)
        
    for name, _ in models:                      
        Header.append(f"{name} - prediction")   # Prediccion realizada por el modelo
        Header.append(f"{name} - segment")      # Segmentos realizados por el modelo
        Header.append(f"{name} - conf")         # Confiabilidad con la que el modelo realiza la prediccion
        Header.append(f"{name} - time [ms]")    # Tiempo de ejecucion de la prediccion

    return Header

def worker(task_queue: mp.Queue, result_queue: mp.Queue, models: list, device_type: str) -> None:
    """
    Crea un proceso en paralelo el cual ejecuta la lista tareas de procesamiento del conjunto de imagenes con diversos modelos y exporta los resultados
    para su posterior conversion en una base de datos.

    Args:
        task_queue   (queue): Cola de tareas a procesar con la estructura [([Batch...], [Main_Labels...], [Segments...]), ...].
        models        (list): Lista de los modelos que procesaran la imagen asignada
        result_queue (queue): Cola de resultados que contiene diccionarios con los resultados asociados a las imagenes procesadas por los modelos.
        device_type    (str): Tecnologia en la que se ejecutara el dispositivo "CPU" o "CUDA".
    """ 
    
    # -------- Pre-carga de los modelos ---------------------------------------------
    loaded_models = []                                                  
    for model_name, model_path in models:                                       # Por cada modelo existente
        loaded_models.append((model_name, YOLO(model_path).to(device_type)))    # Lo carga para trabajar en el dispositivo especificado en una lista de modelos
    
    while True:                                                                 # Ciclo de ejecucion del proceso
        
        # -------- Extraccion de tareas ---------------------------------------------
        try:
            Task = task_queue.get(timeout=3)   
        except:
            break                                                       

        if Task is None:                                          
            break
        
        # -------- Creacion del diccionario de resultados para el batch -------------
        Data = {}
        Batch, Main_Labels, Segments = Task

        for image, label, segment in zip(Batch,Main_Labels, Segments):      # Por cada imagen en el batch, crea una entrada en el diccionario con la ruta, etiqueta y segmento3
            Data[image] = { "Ruta": image,                             
                            "Main_Label": label,
                            "Segments": segment
                          }
            
        # -------- Procesamiento de los modelos -------------------------------------
        for model_name, model in loaded_models:                             # Por cada modelo existente, procesa el conjunto de imagenes
            predict = model(Batch, verbose=False)                           

            for item, result in zip(Batch,predict):                         # Por cada resultado obtenido del conjunto, actualiza su entrada en el respectivo diccionario.
                Predict_Segments = []
                Predict_Conf = []
                if len(result.boxes) == 0:                                  # Si no se obtuvieron cajas en el procesamiento, no se detectaron embarcaciones y guarda este resultado en la entrada respectiva.
                    Data[item].update({                      
                        f"{model_name} - prediction": '0',
                        f"{model_name} - segment": 'N/A',
                        f"{model_name} - conf": '1',
                        f"{model_name} - time [ms]": sum(result.speed.values())
                    })
                else:                                                       # En dado caso que se detectaran cajas, se detectaron embarcaciones
                    for box in result.boxes:                                # Por cada caja, obtiene sus coordenadas en el formato de YOLO y las guarda en una lista; ademas de guardar sus confiabilidades en otra lista
                        x, y, w, h = box.xywhn[0]
                        Predict_Segments.append(f"1 {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
                        Predict_Conf.append(float(box.conf.item()))
                        
                    Data[item].update({                                     # Una vez guardados todos los segmentos y confiabilidades, exporta los resultados en la entrada de la imagen procesada respectivamente.
                        f"{model_name} - prediction": '1',
                        f"{model_name} - segment": Predict_Segments,
                        f"{model_name} - conf": Predict_Conf,
                        f"{model_name} - time [ms]": sum(result.speed.values())
                    })    
                    
        result_queue.put(Data)                                              # Exporta los resultados de los modelos en el conjunto de imagenes a la cola de datos

# -----------------------------------------------------------------------------------

if __name__ == "__main__":

    # -------- Variables ------------------------------------------------------------
    batch_size   = 1                                                                                                        # Cantidad de imagenes que se agrupan y analizan al tiempo
    num_workers  = math.floor(mp.cpu_count() *3/8)                                                                          # Cantidad de procesos que se crean
    csv_path     = "..\\DB_Embarcaciones.csv"                                                                               # Ruta donde se encuentra la base de datos
    model_dir    = "..\\Model_Training\\YoloV11_Segmentation_Experimental-Result\\runs"                                     # Ruta donde se encuentran los modelos clasificadores
    output_path  = f"..\\YoloV11_Segmentation-Results_RTX4090_Batch_{batch_size}_parallelV2_{num_workers}_workers.csv"      # Ruta donde se exportaran los resultados
    device       = "cuda"                                                                                                   # Dispositivo que procesa, puede ser CPU o CUDA
    task_queue   = mp.Queue()                                                                                               # Cola de tareas para el procesamiento de los workers
    result_queue = mp.Queue()                                                                                               # Cola de resultados de las imagenes procesadas por los workers

    Models = Model_Path(model_dir)                              #  Examina las carpetas con los modelos y los importa en una lista de tuplas [(nombre, model_path), ...]
    print(f"Se estan usando {num_workers} procesos")
    
    # -------- Lectura del CSV y procesamiento de los datos -------------------------
    with open(csv_path, mode="r", newline='', encoding='utf-8') as infile:       
        reader = csv.DictReader(infile)                                                 # Lector de la base de datos
        Batch = []                                                                      # Lista que agrupa la ruta de las imagenes
        Labels = []                                                                     # Lista que agrupa la etiqueta preexistente de las imagenes
        Segments = []                                                                   # Lista que agrupa los segmentos preexistentes de las imagenes
        
        for row in reader:                                                              # Por cada elemento del archivo CSV
            # -------- Agrupamiento de las imagenes en un batch ---------------------
            if row['Image_Name']!="N/A":                                                # Si el elemento contiene una imagen la procesa
                Ruta_Image= f"{row['Path']}\\{row['Image_Path']}\\{row['Image_Name']}"  # Arma la ruta de la imagen
                Batch.append(Ruta_Image)                                                # Agrupa la ruta al Batch
                Labels.append(row['Main_Label'])                                        # Agrupa las etiquetas
                Segments.append(row['Segment'])                                         # Agrupa los segmentos
            
            # -------- Creacion de la cola de tareas para los procesos --------------
            if (len(Batch)==batch_size):                                                # Si la cantidad de elementos en el Batch alcanza el tamaño definido
                task_queue.put((Batch,Labels,Segments))                                 # Crea una nueva tarea que contiene el conjunto de imagenes(path), etiquetas y segmentos
                Batch = []                                                              # Limpia el batch
                Labels = []                                                             # Limpia las etiquetas
                Segments = []                                                           # Limpia los segmentos
       
        # -------- Creacion de la cola de tareas restantes --------------------------
        if Batch:                                                                       # Realiza el proceso de analizar el Batch en dado caso que sobren imagenes y no hayan mas elementos en la base de datos
            task_queue.put((Batch,Labels,Segments))                                     # Crea una nueva tarea que contiene el conjunto de imagenes(path), etiquetas y segmentos
            Batch = []                                                                  # Limpia el batch
            Labels = []                                                                 # Limpia las etiquetas
            Segments = []                                                               # Limpia los segmentos

        total_tasks = task_queue.qsize()                                                # Total de tareas generadas
        # -------- Inicio de los procesos para ejecutar las tareas ------------------
        workers = []                                                                        
        for _ in range(num_workers):                                                        # Genera la cantidad de procesos especificada y la guarda en una lista
            p = mp.Process(target=worker, args=(task_queue, result_queue, Models, device))  # Inicializa los procesos
            p.start()                                                                   
            workers.append(p)                                                           
        
        # -------- Escritura del CSV y extraccion de los resultados -----------------
        Header = Make_Header(Models)                                                # Crea el Header para los resultados
        Count = 0
        with open(output_path, mode="w", newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=Header)                     # Escritor del archivo de resultados
            writer.writeheader()                                                    # Escribe el encabezado de los resultados

            # -------- Procesamiento de la cola de resultados -----------------------
            for _ in range(total_tasks):                                            # Procesa exactamente la cantidad de tareas totales generadas
                partial = result_queue.get()                                        # Espera y extrae el resultado de la cola de resultados
                for _, item in partial.items():                                     
                    writer.writerow(item)                                           # Desempaqueta el diccionario del conjunto de imagenes y guarda el resultado en el archivo CSV
                    Count+=1
                outfile.flush()                                                     # Fuerza la escritura de los datos en el CSV (en lugar de almacenarlos en un buffer)
   
        # -------- Termina formalmente los procesos ---------------------------------
        for _ in range(num_workers):                                                # Por cada proceso generado
            task_queue.put(None)                                                    # Crea una tarea sin informacion para terminar el proceso
        for p in workers:                                                           # Por cada proceso, espera a que el proceso termine
            p.join()

        print(f"Procesamiento completado. Filas escritas: {Count}")
