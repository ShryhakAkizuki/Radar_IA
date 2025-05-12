# -*- coding: utf-8 -*-
"""
Script para extraer datos de TRACK ID y generar CSV
Actualizado: 27 de abril de 2025
"""
# ------ Librerías -----
import os
import csv
from datetime import datetime

from bs4 import BeautifulSoup

# ------------ Funciones ------------
def Get_Body_content(path: str, path_list:list, file: str) -> list:
    """
    Extrae el contenido del cuerpo del mensaje html, extrayendo asi multiples parametros asociados a la deteccion que realiza el radar.

    Args:
        path         (str): Ruta donde se encuentra el archivo .html.
        path_list   (list): Lista de las carpetas de la ruta (A traves de estos elementos se extrae la fecha del mensaje).
        file         (str): Nombre del archivo .html que se esta analizando.

    Returns:
        List: Retorna una lista de diccionarios (En caso de que el cuerpo contenga muchas detecciones), las llaves de los diccionarios son las siguientes:
            - Mail_Date     (datetime): Fecha de envio del correo.
            - System_Time   (datetime): Fecha que guarda el sistema de radar a la hora de detectar el objetivo.
            - Track_ID           (int): Identificador del objetivo en el sistema radar.
            - Sub_ID             (int): Identificador auxiliar para agrupar multiples detecciones de un objetivo.
            - Path               (str): Ruta relativa de donde se analizaron los correos/imagenes.
            - #_Images           (int): Cantidad de imagenes asociadas a una deteccion.
            - Duration           (str): Duracion de la deteccion realizada por el sistema.
            - Latitude           (str): Latitud de donde se detecto el objetivo.
            - Longitude          (str): Longitud de donde se detecto el objetivo.
            - Heading            (str): Angulo de orientacion relativo donde se detecto el objetivo.
            - Speed              (str): Velocidad de deteccion del objetivo.
    """  
    List_TrackID = []       # Lista que contendra todos los diccionarios con las respectivas detecciones
    Detection_Data = {}     # Diccionario que almacenara los parametros de las detecciones

    # -------- Lectura del archivo HTML -------------------------------
    with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
        body = BeautifulSoup(f, 'html.parser')

    # -------- Extraer la fecha que guarda el sistema de radar --------

    # Filtrar todo el cuerpo del texto para obtener la informacion entre [System Time:] y [NIO] (Correspondiente a la fecha)
    System_Time = body.get_text().split("System Time:")[1].split("NIO")[0].strip("\n") 
    
    System_Time = System_Time.split(" ")[:-1]                               # Separar todos los elementos espaciados y eliminar el ultimo (Correspontiende al UTC)   
    System_Time = " ".join(System_Time)                                     # Unir todo el texto separado por espacios a traves de espacios (No contendra el UTC)                                             
    System_Time = datetime.strptime(System_Time, ' %a, %d %b %Y %I:%M%p')   # Convertir el texto a un objeto datetime teniendo el cuenta el formato de fecha, hora del texto

    # -------- Extraer la fecha en la que se envio en correo ----------

    fecha = datetime.strptime(f"{path_list[0]}/{path_list[1]}/{path_list[2]}", '%Y/%B/%d')

    # -------- Analizar cada deteccion en el cuerpo del correo --------

    for Track_ID in body.find_all("h2"):    # Recorrer cada elemento dentro de las etiquetas <h2> (Formato <h2> TrackID: #### </h2>)
        Detection_Data = {}                 # Limpiar el diccionario

        # -------- Actualizar los datos del diccionario (En caso de no existir los crea) --------
        Detection_Data.update({"Mail_Date":fecha})
        Detection_Data.update({"System_Time":System_Time})

        Detection_Data.update({"Track_ID":int(Track_ID.contents[0].split(":")[1].strip())})
        Detection_Data.update({"Sub_ID":int(file.split("_")[1].split(".")[0])})

        Detection_Data.update({"Path": path})
        Detection_Data.update({"#_Images": 0})
        # ----------------------------------------------------------------------------------------

        # -------- Analizar las siguientes etiquetas que se encuentran a partir de un <h2> -------
        for tag in Track_ID.find_next_siblings():

            if tag.name == "label" and tag.next_sibling.strip() != "":  # Si el nombre de la etiqueta es <label> y el contenido fuera de las etiquetas no esta vacio lo guarda en el diccionario
                Detection_Data.update({tag.contents[0].replace(":",""): tag.next_sibling.strip()}) 
            elif tag.name == "h2":                                      # Si se encuentra con una etiqueta <h2> rompe el ciclo, dado que se trata de otra deteccion. Se evita sobreescritura
                break
        # ----------------------------------------------------------------------------------------

        # Guarda los parametros de la deteccion realizada y busca otra dentro del cuerpo
        List_TrackID.append(Detection_Data)
    
    # --------------------------------------------------------------------------------------------

    return List_TrackID

# -----------------------------------

if __name__ == "__main__":

    # -------- Variables -----------------------------------------------------------
    base_path = "..\\Correos\\"     # Ruta de la carpeta donde se encuentran los archivos
    save_path = "..\\"              # Ruta de la carpeta donde se guardara el archivo CSV

    Header = []                     # Encabezado de el documento CSV
    Indexed_Data_base = {}          # Base de datos indexada (Organizada) de las detecciones
    
    # -------- Recorrido a traves de todas las carpetas del Path -------------------
    for path, dir, files in os.walk(base_path):
        for file in files:

            path_list = path.split(base_path)[1].split("\\")            # Se divide el nombre del Path por cada ruta sin incluir el Path base
            
            # -------- Analisis de un archivo HTML (Body del correo)  --------------
            if len(path_list) == 4:     
                Body_Data = Get_Body_content(path, path_list, file)     # Obtener los parametros de las detecciones
                
                # -------- Indexamiento en la base de datos  -----------------------
                for Track in Body_Data:

                    if Track["Track_ID"] not in Indexed_Data_base:                  # Si es el primer elemento con llave primaria "Track_ID" en la base de datos, inserta un diccionario vacio
                        Indexed_Data_base[Track["Track_ID"]] = {}
                    
                    while Track["Sub_ID"] in Indexed_Data_base[Track["Track_ID"]]:  # Si ya existe la llave primaria "Sub_ID" dentro de un diccionario con "Track_ID", incrementa el valor del "Sub_ID"
                        Track["Sub_ID"] += 1

                    Indexed_Data_base[Track["Track_ID"]][Track["Sub_ID"]] = Track   # Guarda en la base de datos (Diccionario doble) con llaves "Track_ID" y "Sub_ID" unicos el Diccionario de la deteccion
                # ------------------------------------------------------------------

            # -------- Analisis de un archivo .jpg (Imagen Adjunta)  ---------------
            elif len(path_list) == 5: 
                Ruta = os.path.dirname(path)                        # Obtiene la ruta sin tener en cuenta la carpeta actual "Image_#"
                Sub_ID = int(path.split("\\")[-1].split("_")[1])    # Obtiene el # del ultimo elemento de la ruta "Image_#"

                # -------- Busqueda del Track ID en el nombre de la imagen  --------        
                try:
                    Track_ID = int(file.split("_")[1].split("-")[0])
                except (IndexError, ValueError):
                    continue

                # -------- Busqueda a que deteccion pertenece la imagen  -----------
                Is_Track = Indexed_Data_base.get(Track_ID,{}).get(Sub_ID,{})        # Si no existe la deteccion en la base de datos, devuelve un diccionario vacio

                if Is_Track and Is_Track["Path"] == Ruta:                           # Si el diccionario existe y la ruta es la misma, incrementa la cantidad de fotos de la deteccion
                    Indexed_Data_base[Track_ID][Sub_ID]["#_Images"]+=1

                elif Is_Track:                                                          # Si la deteccion existe, pero la ruta no coincide
                    for Track_Sub_ID in Indexed_Data_base[Track_ID]:                    # Busca dentro de todas las detecciones con el TrackID
                        
                        if Indexed_Data_base[Track_ID][Track_Sub_ID]["Path"] == Ruta:   # Si alguna deteccion tiene la misma ruta, incrementa la cantidad de fotos a la deteccion.
                            Indexed_Data_base[Track_ID][Track_Sub_ID]["#_Images"]+=1    
                            break

                # -------------------------------------------------------------------

    # -------------------------------------------------------------------------------

    # Obtener las llaves de los diccionarios de detecciones, guardadas dentro del primer elemento de la base de datos
    Header = list(list(list(Indexed_Data_base.values())[0].values())[0].keys())

    # -------- Guardar el Archivo CSV -----------------------------------------------
    with open(f"{save_path}Registros.csv", 'w', newline='', encoding='utf-8') as csvfile:   
        writer = csv.writer(csvfile)
        writer.writerow(Header)                                                 # Escribe el Encabezado

        for TrackID in Indexed_Data_base:                                       # Recorre todas las detecciones
            for SubId in Indexed_Data_base[TrackID]:    
                writer.writerow(Indexed_Data_base[TrackID][SubId].values())     # Guarda los valores de las detecciones 

    print(f"✅ Archivo CSV generado correctamente en: ..\\Registros.csv")

    # -------------------------------------------------------------------------------