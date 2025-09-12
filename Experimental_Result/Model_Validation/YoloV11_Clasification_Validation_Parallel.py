# -*- coding: utf-8 -*-
"""
Script para realizar la clasificacion del Dataset a traves de YOLOV11 usando diferentes modelos y multiples imagenes en paralelo
Actualizado: 10 de septiembre de 2025
"""

# ------ Librerías ------------------------------------------------------------------
import os
import csv
import multiprocessing as mp

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
    Header = ["Ruta", "Main_Label"]             # Contenido base (Ruta y etiqueta de la base de datos)
        
    for name, _ in models:                      
        Header.append(f"{name} - prediction")   # Prediccion realizada por el modelo
        Header.append(f"{name} - conf")         # Confiabilidad con la que el modelo realiza la prediccion
        Header.append(f"{name} - time [ms]")    # Tiempo de ejecucion de la prediccion

    return Header

def worker(task_queue: mp.Queue, result_queue: mp.Queue, device_type: str) -> None:
    """
    Crea un proceso en paralelo el cual ejecuta la lista tareas de procesamiento del conjunto de imagenes con diversos modelos y exporta los resultados
    para su posterior conversion en una base de datos.

    Args:
        task_queue   (queue): Cola de tareas a procesar con la estructura [(Model_name, Model_Path, [Batch...]), ...].
        result_queue (queue): Cola de resultados que contiene diccionarios con los resultados asociados a las imagenes procesadas por los modelos.
        device_type    (str): Tecnologia en la que se ejecutara el dispositivo "CPU" o "CUDA".
    """ 
    while True:                                                         # Ciclo de ejecucion del proceso
        try:
            model_name, model_path, batch = task_queue.get(timeout=3)   # Intenta obtener alguna tarea de la cola de tareas, en caso de no ser posible, se termina el proceso
        except:
            break                                                       

        if model_name is None:                                          # Si no llega a obtener ningun modelo, termina el proceso
            break

        Data = {}

        model = YOLO(model_path)                                        # Carga el modelo a utilizar
        model.to(device_type)                                           # Le especifica donde se ejecutara
        predict = model(batch, verbose=False)                           # Realiza el procesamiento del conjunto de imagene
        
        for item, result in zip(batch,predict):                         # Por cada resultado obtenido, guarda el conjunto de datos en un diccionario asociado a la imagen procesada.
            Data[item] = {  f"{model_path[0]} - prediction": result.probs.top1,
                            f"{model_path[0]} - conf": result.probs.top1conf.item(),
                            f"{model_path[0]} - time [ms]": sum(result.speed.values())
                         }

        print(f"Batch Finalizado, ultima imagen: {batch[-1]}") 

        result_queue.put(Data)                                          # Exporta los resultados a la cola de resultados

# -----------------------------------------------------------------------------------

if __name__ == "__main__":

    # -------- Variables ------------------------------------------------------------
    batch_size  = 20                                                                                # Cantidad de imagenes que se agrupan y analizan al tiempo
    csv_path    = "..\\DB_Embarcaciones.csv"                                                        # Ruta donde se encuentra la base de datos
    model_dir   = "..\\Model_Training\\YoloV11_Clasification_Experimental-Result\\runs"             # Ruta donde se encuentran los modelos clasificadores
    output_path = f"..\\YoloV11_Clasification-Results_i7-1185G7_Batch_{batch_size}_parallel.csv"    # Ruta donde se exportaran los resultados
    device      = "cpu"                                                                             # Dispositivo que procesa, puede ser CPU o CUDA
    num_workers = mp.cpu_count()
    task_queue  = mp.Queue()
    result_queue = mp.Queue()

    Models = Model_Path(model_dir)                              #  Examina las carpetas con los modelos y los importa en una lista de tuplas [(nombre, model_path), ...]

    with open(csv_path, mode="r", newline='', encoding='utf-8') as infile, \
         open(output_path, mode="w", newline='', encoding='utf-8') as outfile:


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
                Ruta_Image= f"{row['Path']}\\{row['Image_Path']}\\{row['Image_Name']}"  # Arma la ruta de la imagen
                Batch.append(Ruta_Image)                                                # Agrupa la ruta al Batch
                Data[Ruta_Image] = {    "Ruta": Ruta_Image,                             # Genera su entrada en la base de datos
                                        "Main_Label": row["Main_Label"]
                                   }
            
            # -------- Creacion de la cola de tareas para los procesos --------------
            if (len(Batch)==batch_size):                                                # Si la cantidad de elementos en el Batch alcanza el tamaño definido
                for model in Models:                                                    # Por cada modelo existente
                    task_queue.put((model[0], model[1], Batch))                         # Crea una nueva tarea entre el conjunto de imagenes y cada modelo existente

                Batch = []                                                              # Limpia el batch

        # -------- Creacion de la cola de tareas restantes --------------------------
        if Batch:                                                                       # Realiza el proceso de analizar el Batch en dado caso que sobren imagenes y no hayan mas elementos en la base de datos
            for model in Models:                                                        # Por cada modelo existente
                    task_queue.put((model[0], model[1], Batch))                         # Crea una nueva tarea entre el conjunto de imagenes y cada modelo existente

        # -------- Inicio de los procesos para ejecutar las tareas ------------------
        workers = []                                                                    # Lista de procesos activos
        for _ in range(num_workers):                                                    # Genera procesos por la cantidad de hilos disponibles 
            p = mp.Process(target=worker, args=(task_queue, result_queue, device))      # Inicializa los procesos con las respectivas colas de tareas y resultados
            p.start()                                                                   
            workers.append(p)                                                           

        # -------- Inicio de los procesos para ejecutar las tareas ------------------

        total_tasks = task_queue.qsize()                                                # Define la cantidad de tareas (resultados) a procesar
        for _ in range(total_tasks):                                                    # Por cada tarea (resultado)
            partial = result_queue.get()                                                # extrae el resultado de la cola de resultados (Espera a que haya un resultado en caso de que este vacio)
            for key, value in partial.items():                                          # Guarda los valores de los resultados en la base de datos principal
                Data[key].update(value)                                                 
            Count += len(partial)

        # -------- Termina formalmente los procesos ---------------------------------
        for _ in range(num_workers):                                                    # Por cada proceso
            task_queue.put((None, None, None))                                          # Crea una tarea sin informacion para terminar el proceso
        for p in workers:                                                               # Por cada proceso, espera a que el proceso termine
            p.join()

        for _, item in Data.items():                                                    # Una vez cada proceso termina, guarda los items de la base de datos en el CSV de salida
            writer.writerow(item)

        print(Count)