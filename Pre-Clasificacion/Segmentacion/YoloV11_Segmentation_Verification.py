# -*- coding: utf-8 -*-
"""
Script para verificar los cambios de etiqueta/segmentos generados por la clasificacion asistida por YOLOV11
Actualizado: 27 de julio de 2025
"""

# ------ Librerías -----------------------------------------------------------------------------------
import csv
import cv2
from typing import Type

# ------------ Clases --------------------------------------------------------------------------------
class BoxDrawer:
    
    def __init__(self: 'BoxDrawer',Path: str, Old_Main_Label:str, New_Main_Label:str, Old_Segment:str, New_Segment:str) -> None:
        """
        Constructor de la clase, inicializa las variables necesarias para generar una interfaz que permita dibujar 
        rectangulos y exportarlos en formato de YOLO, adicionalmente carga los segmentos existentes en diferentes
        versiones del archivo CSV para verificar los cambios visualmente, ademas de poderlos modificar

        Args:
            self      (BoxDrawer): Instancia del objeto (Variables y metodos del objeto).
            path            (str): Ruta relativa o absoluta hacia el archivo de imagen a analizar.
            Old_Main_Label  (str): Etiqueta de la foto antes de la segmentacion asistida.
            New_Main_Label  (str): Etiqueta de la foto despues de la segmentacion asistida.
            Old_Segment     (str): String que posee la lista de segmentos en el formato de YOLO antes de la segmentacion asistida. 
            New_Segment     (str): String que posee la lista de segmentos en el formato de YOLO de la segmentacion asistida.
        """
        # -------- Variables -----------------------------------------------------------------------------
        self.drawing = False                # Estado de la clase al dibujar o no un rectangulo
        self.ix, self.iy = -1, -1           # Ultimas coordenadas almacenadas (se sobreescribe al hacer click)
        self.path = Path                    # Path de la imagen
        self.img = cv2.imread(Path)         # Imagen leida en OpenCV
        self.h, self.w = self.img.shape[:2] # Dimensiones de la imagen
        self.backup = self.img.copy()       # Copia de seguridad de la imagen para borrar los segmentos
        self.old_bboxes = []                # Lista de segmentos existentes en el CSV antes de la segmentacion asistida
        self.new_bboxes = []                # Lista de segmentos existentes en el CSV despues de la segmentacion asistida
        self.old_class_id = Old_Main_Label  # Clase a la que pertenece la deteccion antes de la segmentacion asistida
        self.new_class_id = New_Main_Label  # Clase a la que pertenece la deteccion despues de la segmentacion asistida

        # -------- Desempaquetamiento de los Segmentos del documento CSV ---------------------------------
        if Old_Segment!="N/A":                 
            Old_Segment = Old_Segment.strip("[]").split(",")  
            Old_Segment = [item.strip().strip("'").strip('"').strip().split() for item in Old_Segment]   
            Old_Segment =  [list(map(float,item[1:])) for item in Old_Segment]          # Extraccion de segmentos a partir de un String a elementos float
            self.old_bboxes = [self.Cords_Transform(item) for item in Old_Segment]      # Transformacion de la normalizacion del formato YOLO a [x1,y1,x2,y2]

        if New_Segment!="N/A":                 
            New_Segment = New_Segment.strip("[]").split(",")  
            New_Segment = [item.strip().strip("'").strip('"').strip().split() for item in New_Segment]   
            New_Segment =  [list(map(float,item[1:])) for item in New_Segment]          # Extraccion de segmentos a partir de un String a elementos float
            self.new_bboxes = [self.Cords_Transform(item) for item in New_Segment]      # Transformacion de la normalizacion del formato YOLO a [x1,y1,x2,y2]

        # -------- Ventana Emergente - Verificacion de modificaciones --------------------------------------
        cv2.namedWindow(self.path.split("\\")[-1])                              # Crea una ventana emergente   
        cv2.moveWindow(self.path.split("\\")[-1], 100, 100)                     # Fija la ventana emergente a una posicion especifica
        cv2.setMouseCallback(self.path.split("\\")[-1], self.Draw_Rectangle)    # Inicializa la generacion de segmentos manual
            
        for x1, y1, x2, y2 in self.old_bboxes:                                  # Dibuja los segmentos Existentes antes de la segmentacion asistida en caso de existir
            cv2.rectangle(self.img, (x1,y1),(x2,y2),(255, 229, 180),4)    
       
        for x1, y1, x2, y2 in self.new_bboxes:                                  # Dibuja los segmentos Existentes despues de la segmentacion asistida en caso de existir
            cv2.rectangle(self.img, (x1,y1),(x2,y2),(100, 100, 255),2)    

        # Escribe en la ventana la etiqueta antes de la segmentacion asistida
        cv2.putText(self.img, f"Old_Label: {self.old_class_id}", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
        cv2.putText(self.img, f"Old_Label: {self.old_class_id}", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 229, 180), 2)

        # Escribe en la ventana la etiqueta despues de la segmentacion asistida
        cv2.putText(self.img, f"New_Label: {self.new_class_id}", (15, 50+50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
        cv2.putText(self.img, f"New_Label: {self.new_class_id}", (15, 50+50), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 255), 2)


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
            self.new_class_id = '1'
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
        for x1, y1, x2, y2 in self.new_bboxes:  # Por cada conjunto de coordenadas almacenado en bboxes
            x_center = ((x1+x2)/2)/self.w       # Centro en x del segmento
            y_center = ((y1+y2)/2)/self.h       # Centro en y del segmento
            width  = (x2-x1)/self.w             # ancho del segmento
            height = (y2-y1)/self.h             # alto del segmento

            # Guarda la informacion calculada en una lista de sementos en el formato adecuado
            Yolo_Segment.append(f"{self.new_class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")  

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
                self.new_class_id = '0'
                self.new_bboxes = []
                print("Segmentos borrados")

    @ classmethod
    def ejecutar(cls: Type['BoxDrawer'], Path: str,  Old_Main_Label:str, New_Main_Label:str, Old_Segment:str, New_Segment:str) -> None:
        """
        Funcion especifica de la clase que no depende de la instancia self.
        Optimiza la ejecucion de la aplicacion en una sola linea de codigo para su posterior implementacion
        al ejecutar el constructor y llamar a su funcion run.
        
        Args:
            cls  (Type['BoxDrawer']): Clase a instanciar
            path            (str): Ruta relativa o absoluta hacia el archivo de imagen a analizar.
            Old_Main_Label  (str): Etiqueta de la foto antes de la segmentacion asistida.
            New_Main_Label  (str): Etiqueta de la foto despues de la segmentacion asistida.
            Old_Segment     (str): String que posee la lista de segmentos en el formato de YOLO antes de la segmentacion asistida. 
            New_Segment     (str): String que posee la lista de segmentos en el formato de YOLO de la segmentacion asistida.

        """

        return cls(Path, Old_Main_Label, New_Main_Label, Old_Segment, New_Segment).Manual_Segmentation()

# ----------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # -------- Variables -----------------------------------------------------------------------------
    base_path = "..\\"                                                  # Ruta de la carpeta donde se encuentran los archivos CSV
    csv0_name = "Registros_Segmentados.csv"                             # Nombre del archivo .CSV anterior
    csv1_name = "Registros_Segmentados_Asistidos.csv"                   # Nombre del archivo .CSV reciente
    csvoutput_name = "Registros_Segmentados_Asistido_Auditados.csv"     # Nombre del nuevo archivo .CSV 

    # -------- Lectura y escritura del CSV -----------------------------------------------------------
    with open(f"{base_path}{csv0_name}", mode="r", newline='', encoding='utf-8') as f0, \
         open(f"{base_path}{csv1_name}", mode="r", newline='', encoding='utf-8') as f1, \
         open(f"{base_path}{csvoutput_name}", mode="w", newline='', encoding='utf-8') as fout:

        print("Instrucciones:")
        print(" - Dibuja con el mouse.")
        print(" - 's' = guardar y salir")
        print(" - 'r' = reiniciar cajas\n\n")

        reader_0 = csv.DictReader(f0)                                   # Lector del primer CSV
        reader_1 = csv.DictReader(f1)                                   # Lector del segundo CSV
        writer   = csv.DictWriter(fout,fieldnames=reader_1.fieldnames)  # Escribe el Header en el nuevo archivo CSV
        writer.writeheader()

        for row_0, row_1 in zip(reader_0, reader_1):        # Itera sobre ambos lectores al tiempo y cada linea se guarda en las variables row_#
            if row_0["Image_Name"]==row_1["Image_Name"] and \
            (row_0["Main_Label"]!=row_1["Main_Label"] or \
            len(row_0["Segment"].strip("[]").split(","))!=len(row_1["Segment"].strip("[]").split(","))):                                # Si existen cambios entre segmentos o etiquetas
                
                full_path = f"{row_1['Path']}\\{row_1['Image_Path']}\\{row_1['Image_Name']}"                                            # Genera la ruta de la imagen
                results = BoxDrawer.ejecutar(full_path, row_0["Main_Label"], row_1["Main_Label"], row_0["Segment"],row_1["Segment"])    # Ejecuta la inspeccion visual           

                if results == []:                   # Si la inspeccion visual devuelve una lista sin segmentos lo etiqueta como ausencia
                    row_1["Main_Label"]="0"
                    row_1["Segment"] = "N/A"
                else:                               # De lo contrario lo etiqueta como embarcacion y guarda los segmentos generados
                    row_1["Main_Label"]="1"
                    row_1["Segment"] = results       
        
            writer.writerow(row_1)                  # Escribe en el nuevo archivo la fila del CSV mas reciente con el analisis manual
            
    # -------------------------------------------------------------------------------------------------
