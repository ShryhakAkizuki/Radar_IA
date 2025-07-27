# -*- coding: utf-8 -*-
"""
Script para pre-segmentar las imagenes de la base de datos con bounding boxes manualmente
Actualizado: 24 de julio de 2025
"""

# ------ Librerías -----------------------------------------------------------------------------------
import csv
import cv2
from typing import Type

# ------------ Clases --------------------------------------------------------------------------------
class BoxDrawer:
    
    def __init__(self: 'BoxDrawer',Path: str, Label:str) -> None:
        """
        Constructor de la clase, inicializa las variables necesarias para generar una interfaz que permita dibujar rectangulos y exportarlos en formato de YOLO

        Args:
            self  (BoxDrawer): Instancia del objeto (Variables y metodos del objeto)
            path        (str): Ruta relativa o absoluta hacia el archivo de imagen a analizar.
            Label       (str): Etiqueta base que posee la imagen (1 Presencia de embarcacion, 0 ausencia de embarcacion).    
        """
        # -------- Variables -----------------------------------------------------------------------------
        self.bboxes = []                    # Variable para guardar la lista de coordenadas en formato (x1, y1, x2, y2)
        self.drawing = False                # Estado de la clase al dibujar o no un rectangulo
        self.ix, self.iy = -1, -1           # Ultimas coordenadas almacenadas (se sobreescribe al hacer click)
        self.path = Path                    # Path de la imagen
        self.img = cv2.imread(Path)         # Imagen leida en OpenCV
        self.h, self.w = self.img.shape[:2] # Dimensiones de la imagen
        self.class_id = Label               # Etiqueta de la imagen
        self.backup = self.img.copy()       # Copia de seguridad de la imagen para borrar los segmentos

        # -------- Ventana Emergente  --------------------------------------------------------------------
        cv2.namedWindow(self.path.split("\\")[-1])          # Crea una ventana emergente   
        cv2.setMouseCallback(self.path.split("\\")[-1], self.Draw_Rectangle)  # Inicializa la generacion de segmentos

    def Draw_Rectangle(self: 'BoxDrawer', event: int, x: int, y: int, flags: int, param: object ) -> None:
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
    def ejecutar(cls: Type['BoxDrawer'], Path: str, Label:str) -> None:
        """
        Funcion especifica de la clase que no depende de la instancia self.
        Optimiza la ejecucion de la aplicacion en una sola linea de codigo para su posterior implementacion
        al ejecutar el constructor y llamar a su funcion run.
        
        Args:
            cls  (Type['BoxDrawer']): Clase a instanciar
            path        (str): Ruta relativa o absoluta hacia el archivo de imagen a analizar.
            Label       (str): Etiqueta base que posee la imagen (1 Presencia de embarcacion, 0 ausencia de embarcacion).
        """
        return cls(Path, Label).Manual_Segmentation()

# ----------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # -------- Variables -----------------------------------------------------------------------------
    csv_path = "..\\"      # Ruta de la carpeta donde se encuentra el archivo CSV

    # -------- Lectura y escritura del CSV -----------------------------------------------------------
    with open(f"{csv_path}Registros_Clasificados_Asistido_Auditados.csv", mode="r", newline='', encoding='utf-8') as infile, \
         open(f"{csv_path}Registros_Segmentados.csv", mode="w", newline='', encoding='utf-8') as outfile:

        print("Instrucciones:")
        print(" - Dibuja con el mouse.")
        print(" - 's' = guardar y salir")
        print(" - 'r' = reiniciar cajas\n\n")

        reader = csv.DictReader(infile)         # Lee el Header Original
        Nuevas_Columnas = ["Segment"]           # Nuevo Header
        
        writer = csv.DictWriter(outfile, fieldnames=(reader.fieldnames+Nuevas_Columnas))    # Escribe el nuevo Header
        writer.writeheader()

        for row in reader:                      # Por cada elemento del archivo CSV
            if row["Image_Name"]!="N/A":        # Si encuentra una imagen
                if row["Main_Label"] == "1":    # Si es una imagen con una embarcacion obtiene su ruta y la segmenta
                    Ruta_Image=f"{row['Path']}\\{row['Image_Path']}\\{row['Image_Name']}"   
                    results = BoxDrawer.ejecutar(Ruta_Image, row["Main_Label"])             
                    print(results)
                else:                           # En dado caso que no sea una embarcacion, escribe "N/A"
                    results = "N/A"
            else:
                results = "N/A"                 # Si no la encuentra, escribe "N/A"

            if results == []:                   # Si no se dibujo ningun rectangulo, cambia la etiqueta a 0 y el segmento a "N/A"
                row["Main_Label"]="0"
                row["Segment"] = "N/A"
            else:
                row["Segment"] = results        # Escribe los segmento en el CSV
            
            writer.writerow(row)
            
    # -------------------------------------------------------------------------------------------------
