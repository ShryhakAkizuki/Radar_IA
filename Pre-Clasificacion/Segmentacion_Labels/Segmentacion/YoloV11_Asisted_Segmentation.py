# -*- coding: utf-8 -*-
"""
Script para pre-segmentar las imagenes de la base de datos con bounding boxes manualmente
Actualizado: 26 de julio de 2025
"""

# ------ Librerías -----------------------------------------------------------------------------------
import csv
import cv2
from typing import Type

from ultralytics import YOLO

# ------------ Clases --------------------------------------------------------------------------------
class BoxDrawer:
    
    def __init__(self: 'BoxDrawer',Path: str, Segments:str, model_path: str) -> None:
        """
        Constructor de la clase, inicializa las variables necesarias para generar una interfaz que permita dibujar 
        rectangulos y exportarlos en formato de YOLO, adicionalmente carga los segmentos existentes y ejecuta el 
        modelo de deteccion de YOLO de modo que sus resultados se grafican en la respectiva interfaz.

        Args:
            self  (BoxDrawer): Instancia del objeto (Variables y metodos del objeto)
            path        (str): Ruta relativa o absoluta hacia el archivo de imagen a analizar.
            Segments    (str): String que posee la lista de segmentos en el formato de YOLO la cual sera procesada para obtener la informacion.  
            model_path  (str): Ruta relativa o absoluta hacia el modelo de YOLO entrenado.  
        """
        # -------- Variables -----------------------------------------------------------------------------
        self.drawing = False                # Estado de la clase al dibujar o no un rectangulo
        self.ix, self.iy = -1, -1           # Ultimas coordenadas almacenadas (se sobreescribe al hacer click)
        self.path = Path                    # Path de la imagen
        self.img = cv2.imread(Path)         # Imagen leida en OpenCV
        self.h, self.w = self.img.shape[:2] # Dimensiones de la imagen
        self.backup = self.img.copy()       # Copia de seguridad de la imagen para borrar los segmentos
        self.Yolo_segments = []             # Lista de segmentos generados por YOLO
        self.bboxes = []                    # Lista de segmentos existentes en el CSV
        self.Yolo_Probs = []                # Lista de probabilidades de deteccion de YOLO

        # -------- Desempaquetamiento de los Segmentos del documento CSV ---------------------------------
        if Segments!="N/A":                 
            Segments = Segments.strip("[]").split(",")  
            Segments = [item.strip().strip("'").strip('"').strip().split() for item in Segments]   
            Segments =  [list(map(float,item[1:])) for item in Segments]        # Extraccion de segmentos a partir de un String a elementos float
            self.class_id = Segments[0][0]                                      # Extraccion del Main_Label en los segmentos
            self.bboxes = [self.Cords_Transform(item) for item in Segments]     # Transformacion de la normalizacion del formato YOLO a [x1,y1,x2,y2]
        else: 
            self.class_id = "0"             # Si no existen segmentos, coloca el Main_Label en 0

        # -------- Prediccion de YOLO - Modo deteccion ---------------------------------------------------
        model = YOLO(model_path)                        # YOLOV11 con el entrenamiento custom
        predict = model(self.path, verbose=False)[0]    # Prediccion del modelo YOLOV11
        
        if len(predict.boxes.xywhn.tolist())>0:         # Si YOLOV11 realizo la prediccion
            self.Yolo_segments = [self.Cords_Transform(item) for item in predict.boxes.xywhn.tolist()]  # Extraer los segmentos y transforma el formato
            self.Yolo_Probs = predict.boxes.conf.tolist()                                               # Obtiene las probabilidades de deteccion

        # -------- Ventana Emergente - Segmentacion Semi-Automatica --------------------------------------
        if (len(self.bboxes)!=0 or len(self.Yolo_segments)!=0):                     # Se ejecuta en dado caso que existieran segmentos previamente o YOLO detectase algo
            cv2.namedWindow(self.path.split("\\")[-1])                              # Crea una ventana emergente   
            cv2.moveWindow(self.path.split("\\")[-1], 100, 100)                     # Fija la ventana emergente a una posicion especifica
            cv2.setMouseCallback(self.path.split("\\")[-1], self.Draw_Rectangle)    # Inicializa la generacion de segmentos manual

            for (x1, y1, x2, y2), prob in zip(self.Yolo_segments,self.Yolo_Probs):  # Dibuja los segmentos generados por YOLOV11 en caso de existir
                cv2.rectangle(self.img, (x1,y1),(x2,y2),(255, 229, 180),2)          
                cv2.putText(self.img, f"{prob:.2f}", (x1 - 15, y1 - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 100), 2)

            self.backup = self.img.copy()                                           # Actualiza la copia de seguridad guardando los posibles segmentos generados por YOLO
            
            for x1, y1, x2, y2 in self.bboxes:                                      # Dibuja los segmentos Existentes en caso de existir
                cv2.rectangle(self.img, (x1,y1),(x2,y2),(0, 100, 255),2)    


    def Cords_Transform(self: 'BoxDrawer', Segment: list) -> list:
        """
        Convierte coordenadas YOLO normalizadas (x_center, y_center, width, height)
        a coordenadas absolutas (x1, y1, x2, y2) en píxeles.

        Args:
            self (BoxDrawer): Instancia del objeto que contiene los atributos `w` y `h`.
            Segment   (list): Lista [x_center, y_center, width, height], normalizadas entre 0 y 1.
        Returns:
            list: Lista [x1, y1, x2, y2] en píxeles.
        """
        x_center, y_center, width, height = Segment

        x1 = int((x_center - width / 2) * self.w)
        y1 = int((y_center - height / 2) * self.h)
        x2 = int((x_center + width / 2) * self.w)
        y2 = int((y_center + height / 2) * self.h)

        return [x1, y1, x2, y2]

    def Draw_Rectangle(self: 'BoxDrawer', event: int, x: int, y: int, flags: int, param: object) -> None:
        """
        Funcion que llama OpenCV para dibujar los segmentos

        Args:
            self  (BoxDrawer): Instancia del objeto (Variables y metodos del objeto)
            event       (int): Evento de OpenCV en la ventana emergente.
            x           (int): Coordenada X en la ventana emergente dada por OpenCV.    
            y           (int): Coordenada Y en la ventana emergente dada por OpenCV.    
            flags       (int): Flags de OpenCV.    
            param    (object): Parametros de OpenCV.    
        """
        
        if event == cv2.EVENT_LBUTTONDOWN:      # Si se hace Click
            self.drawing = True
            self.ix, self.iy = x, y             # Copia las coordenadas
        
        elif event == cv2.EVENT_LBUTTONUP:      # Si se suelta el Click
            self.drawing = False
            x1, y1 = min(self.ix, x), min(self.iy, y)               # Registra como coordenadas iniciales los valores minimos del ultimo llamado y el actual
            x2, y2 = max(self.ix, x), max(self.iy, y)               # Registra como coordenadas finales los valores maximos del ultimo llamado y el actual
            self.bboxes.append((x1,y1,x2,y2))                       # Guarda los valores en la lista bboxes
            cv2.rectangle(self.img, (x1,y1),(x2,y2),(0,255,0),2)    # Crea el rectangulo visualmente en la ventana emergente
            cv2.imshow(self.path.split("\\")[-1], self.img)         # Visualiza el contenido

    def Yolo_Format(self: 'BoxDrawer') -> list:
        """
        Funcion que calcula las coordenadas de los segmentos en el formato aceptado por YOLO

        Args:
            self  (BoxDrawer): Instancia del objeto (Variables y metodos del objeto)
        Returns:
            list: Lista que contiene los segmentos clasificados manualmente en el formato de YOLO [x_center, y_center, width, height]
        """
        Yolo_Segment = []
        for x1, y1, x2, y2 in self.bboxes:  # Por cada conjunto de coordenadas almacenado en bboxes
            x_center = ((x1+x2)/2)/self.w   # Centro en x del segmento
            y_center = ((y1+y2)/2)/self.h   # Centro en y del segmento
            width  = (x2-x1)/self.w         # ancho del segmento
            height = (y2-y1)/self.h         # alto del segmento

            # Guarda la informacion calculada en una lista de sementos en el formato adecuado
            Yolo_Segment.append(f"{self.class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")  

        return Yolo_Segment

    def Manual_Segmentation(self: 'BoxDrawer') -> list:
        """
        Funcion que ejecuta la aplicacion para guardar los segmentos generados, o reestablecer los segmentos,
        ademas mantiene el ciclo que permite capturar los eventos del mouse para dibujar los segmentos.

        Args:
            self  (BowDrawer): Instancia del objeto (Variables y metodos del objeto)
        Returns:
            list: Lista de los segmentos generados manualmente
        """
        if (len(self.bboxes)==0 and len(self.Yolo_segments)==0):
            return self.bboxes

        while True:
            cv2.imshow(self.path.split("\\")[-1], self.img)                
            key = cv2.waitKey(1) & 0XFF
            if key == ord("s"):
                cv2.destroyAllWindows()
                return self.Yolo_Format()
            elif key == ord("r"):
                self.img = self.backup.copy()
                self.bboxes = []
                print("Segmentos borrados")

    @ classmethod
    def ejecutar(cls: Type['BoxDrawer'], Path: str, Segments:str, model_path: str) -> None:
        """
        Funcion especifica de la clase que no depende de la instancia self.
        Optimiza la ejecucion de la aplicacion en una sola linea de codigo para su posterior implementacion
        al ejecutar el constructor y llamar a su funcion run.
        
        Args:
            cls  (Type['BoxDrawer']): Clase a instanciar
            path        (str): Ruta relativa o absoluta hacia el archivo de imagen a analizar.
            Label       (str): Etiqueta base que posee la imagen (1 Presencia de embarcacion, 0 ausencia de embarcacion).
            model_path  (str): Ruta relativa o absoluta hacia el modelo de YOLO entrenado.  

        """
        return cls(Path, Segments, model_path).Manual_Segmentation()

# ----------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # -------- Variables -----------------------------------------------------------------------------
    csv_path = "..\\"                           # Ruta de la carpeta donde se encuentra el archivo CSV
    model_path = "..\\Asisted_Segmentation.pt"  # Ruta de la carpeta donde se el modelo de YOLO entrenado

    # -------- Lectura y escritura del CSV -----------------------------------------------------------
    with open(f"{csv_path}Registros_Segmentados.csv", mode="r", newline='', encoding='utf-8') as infile, \
         open(f"{csv_path}Registros_Segmentados_Asistidos.csv", mode="w", newline='', encoding='utf-8') as outfile:

        print("Instrucciones:")
        print(" - Dibuja con el mouse.")
        print(" - 's' = guardar y salir")
        print(" - 'r' = reiniciar cajas\n\n")

        reader = csv.DictReader(infile)                                     # Lee el Header Original        
        writer = csv.DictWriter(outfile, fieldnames=(reader.fieldnames))    # Escribe el nuevo Header
        
        writer.writeheader()

        for row in reader:                      # Por cada elemento del archivo CSV
            if row["Image_Name"]!="N/A":        # Si encuentra una imagen
                Ruta_Image=f"{row['Path']}\\{row['Image_Path']}\\{row['Image_Name']}"   
                results = BoxDrawer.ejecutar(Ruta_Image, row["Segment"],model_path)             
                    
                if results == []:                   # Si no se dibujo ningun rectangulo, cambia la etiqueta a 0 y el segmento a "N/A"
                    row["Main_Label"]="0"
                    row["Segment"] = "N/A"
                else:
                    row["Main_Label"]="1"
                    row["Segment"] = results        # Escribe los segmento en el CSV
            
            writer.writerow(row)
            
    # -------------------------------------------------------------------------------------------------
