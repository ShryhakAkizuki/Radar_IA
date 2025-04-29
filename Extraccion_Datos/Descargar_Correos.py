# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 13:39:58 2025
"""
# ------ Librerias -----
import os
from datetime import datetime, timedelta

import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from base64 import urlsafe_b64decode

# ------------ Funciones ------------
def Aut_Gmail_Service(path: str ="../") -> object:
    """
    Autentica y construye un servicio de la API de Gmail utilizando credenciales almacenadas localmente.

    Args:
        path (str): Ruta relativa o absoluta hacia los archivos de credenciales. 
                    Por defecto, se asume que `token.pickle` y `AuthCredentials.json` se encuentran 
                    en el directorio padre del script (`../`).
    Returns:
        object: Instancia autenticada del servicio de la API de Gmail (`googleapiclient.discovery.Resource`).
    """
    credentials = None
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    # ----- Token de Autenticación -----
    if os.path.exists(path+'token.pickle'):
        with open(path+'token.pickle', 'rb') as token:
            credentials = pickle.load(token)    # Cargamos las credenciales desde el archivo token.pickle

    # ----- Login si las credenciales no son validas -----
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(path+'AuthCredentials.json', SCOPES) # Cargamos las credenciales desde el archivo AuthCredentials.json
        credentials = flow.run_local_server(port=0) # Inicia una pestaña del navegador para autenticar al usuario y obtener el token de acceso
        with open(path+'token.pickle', 'wb') as token:
            pickle.dump(credentials, token)         # Guardamos las credenciales en el archivo token.pickle para su uso futuro


    service = build('gmail', 'v1', credentials=credentials)
    return service

def Get_message_ID_list(mail:object, fecha:datetime) -> list: 
    """
    Obtiene la lista de identificadores de mensajes de la bandeja de entrada de Gmail para una fecha específica.
    
    Args:
        mail    (object): Servicio de correo de Gmail API autenticado.
        fecha (datetime): Fecha objetivo para la búsqueda de mensajes.
    Returns:
        list: Lista de diccionarios que contienen los IDs de los mensajes encontrados durante la fecha especificada.
    """
    # String de consulta para buscar correos en una fecha especifica
    search_query = f'after:{(fecha-timedelta(days=1)).strftime("%Y/%m/%d")} before:{(fecha+timedelta(days=1)).strftime("%Y/%m/%d")}'  
    
    # -------- Busqueda de todos los correos en la bandeja de entrada del dia --------
    response  = mail.users().messages().list(       # Primera pagina de resultados de correos del dia
        userId='me', 
        q=search_query
    ).execute() 
    messages  = response.get('messages', [])  
    
    while "nextPageToken" in response:              # Si hay mas de 100 mensajes, paginamos
        page_token = response['nextPageToken']          # Obtenemos el token de la siguiente pagina
        response = mail.users().messages().list(        # Obtenemos la siguiente pagina de resultados
            userId='me', 
            q=search_query, 
            pageToken=page_token
        ).execute()    
        messages.extend(response.get('messages', []))   # Agregamos los mensajes de la siguiente pagina a la lista de mensajes

    return messages # Retornamos la lista de mensajes

def Get_message_content(mail:object, msg_id:str) -> tuple[str, str, list, list]:
    """
    Extrae el contenido principal de un mensaje de Gmail utilizando su ID, incluyendo el asunto, 
    el cuerpo en formato HTML, y las imágenes adjuntas en formato JPEG.
    
    Args:
        mail (object): Servicio de correo de Gmail API autenticado.
        msg_id  (str): ID del mensaje del cual se desea obtener la información.
    Returns:
        tuple:
            - subject          (str): Asunto del mensaje.
            - body             (str): Cuerpo del mensaje en formato HTML, decodificado.
            - filename   (list[str]): Lista de nombres de archivos de imágenes JPEG adjuntas.
            - filedata (list[bytes]): Lista de contenidos binarios de las imágenes JPEG adjuntas,
                                      decodificados desde base64.
    """   
    subject = str("")   # Inicializamos el asunto del mensaje
    body = str("")      # Inicializamos el cuerpo del mensaje
    filename = list([]) # Inicializamos el nombre de los archivos del mensaje
    filedata = list([]) # Inicializamos el contenido de los archivos del mensaje

    msg=mail.users().messages().get(    # Obtenemos el mensaje completo decodificado usando el ID del mensaje
        userId='me', 
        id=msg_id['id'], 
        format='full'
    ).execute()  
    msg = msg.get('payload')            # Obtenemos el payload del mensaje

    # -------- Asunto del mensaje --------
    for header in msg['headers']:               # Recorremos la lista de los headers del mensaje
        if header['name'].lower() == 'subject': # Si el header es el asunto, lo guardamos
            subject = header.get('value',"")
    # -------------------------------------

    # -------- Mensaje con partes (Cuerpo del mensaje y imagenes) --------
    if 'parts' in msg:                         
        for part in msg['parts']:   # Recorremos las partes del mensaje
            
            # -------- Cuerpo del mensaje (HTML) --------
            if part['mimeType'] == 'multipart/alternative':     # si la parte es de tipo multipart/alternative (HTML), la recorremos
                for subpart in part['parts']:               
                    if subpart['mimeType'] == 'text/html':      # Si la subparte es de tipo text/html, obtenemos el contenido de la subparte
                        body = subpart['body'].get('data',"")   
                        if body: # Si hay contenido, lo decodificamos
                            body = urlsafe_b64decode(body).decode('utf-8', errors='ignore') 
            # -------------------------------------------

            # -------- Imagenes del mensaje (JPEG) ------
            elif part['mimeType'] == 'image/jpeg':                  # Si la parte es de tipo imagen/jpeg, obtenemos el nombre del archivo
                if part.get('filename',""):                     
                    filename.extend([part['filename']])             # agregamos el nombre del archivo a la lista de nombres de archivos
                    attachment_id = part['body']['attachmentId']    # Obtenemos el ID del archivo adjunto
                    
                    attachment = mail.users().messages().attachments().get(     # Obtenemos el contenido del archivo adjunto usando el ID del mensaje y el ID del archivo adjunto   
                        userId='me',
                        messageId=msg_id,
                        id=attachment_id
                    ).execute()

                    filedata.extend([urlsafe_b64decode(attachment['data'])])    # Decodificamos el contenido del archivo adjunto y lo agregamos a la lista de contenido de archivos
                    
            # -------------------------------------------

    # -------- Mensaje sin partes (Solo el cuerpo del mensaje) --------
    else:                                               
        # -------- Cuerpo del mensaje (HTML) --------
        if msg['mimeType'] == 'text/html':      # Si el mensaje es de tipo text/html
            body = msg['body'].get('data',"")   # Obtenemos el contenido del mensaje
            if body: # Si hay contenido, lo decodificamos
                body = urlsafe_b64decode(body).decode('utf-8', errors='ignore')
        # -------------------------------------------

    # -----------------------------------------------------------------

    return subject, body, filename, filedata # Retornamos el asunto, el cuerpo, el nombre y los archivo del mensaje

# def guardarCorreos():

#     folder_path = os.path.join(savepath, Fecha.strftime("%Y/%B/%d"), "e-mail")
#     html_filename = f"{subject}.html"  # Usamos el asunto como nombre del archivo
#     html_filename = html_filename.replace(":", "_")
    
#     file_path = os.path.join(folder_path, html_filename)
#     folder_path = os.path.normpath(folder_path)
#     # Crear las carpetas necesarias si no existen
#     os.makedirs(folder_path, exist_ok=True)

#     # Guardar el archivo HTML en la carpeta correcta
#     with open(file_path, 'w', encoding='utf-8') as f:
#         f.write(body)

#     print(f"Archivo guardado en: {file_path}")
    
# ------------ Variables ------------
mail = Aut_Gmail_Service()  # Servicio de correo Gmail autenticado

# Rango de fechas
FECHA_INICIO = datetime(2024, 1, 1)   # Fecha de inicio
FECHA_FIN = datetime(2025, 4, 22)     # Fecha de fin
Lista_Fechas = [FECHA_INICIO + timedelta(days=x) for x in range((FECHA_FIN - FECHA_INICIO).days + 1)]   # Creamos una lista de fechas desde la fecha de inicio hasta la fecha de fin (incluyendo ambas fechas)

# path de guardado
savepath="../Correos/"  # Ruta donde se guardaran los correos descargados
os.makedirs(savepath, exist_ok=True)  # Creamos la carpeta si no existe
    
# ------------ Extracción de correos ------------
for Fecha in Lista_Fechas: # Buqueda de correos por fecha
    print(f"📅 Buscando correos para: {Fecha.strftime('%Y-%B-%d')}")

    messages_list=Get_message_ID_list(mail, Fecha) 
  
    if(len(messages_list) == 0): # Si no hay mensajes, mostramos un mensaje y continuamos
        print(f"❌ No se encontraron correos")
    else:
        print(f"✅ Se encontraron {len(messages_list)} correos")
    #     # -------- Creamos la carpeta Año/mes/dia (si hay correos) --------
    #     os.makedirs(savepath+Fecha.strftime("%Y/%B/%d"), exist_ok=True)
    
    # Folder_ID = 0
    # -------- Extraemos la informacion de los mensajes del dia --------
    for message in messages_list:

        # Obtenemos el contenido del mensaje usando el ID del mensaje
        subject, body, filename, filedata = Get_message_content(mail, message) 




        #         # -------- Imagenes del mensaje (JPEG) ------
        #         if part.get_content_type() == "image/jpeg":
        #             filename = part.get_filename()
        #             imageName=Fecha.strftime("%Y-%B-%d")
        #             filename = f"{imageName}_{filename}"

        #             # -------- Guardar Imagenes del mensaje ------

        #             if filename:  # Si tiene nombre de archivo
        #                 file_data = part.get_payload(decode=True)  # Obtener el contenido del archivo
        #                 folder_path_images = os.path.join(savepath, Fecha.strftime("%Y/%B/%d"), "images")
        #                 os.makedirs(folder_path_images, exist_ok=True)
        #                 file_path = os.path.join(folder_path_images, filename)
    
        #                 with open(file_path, 'wb') as f:
        #                     f.write(file_data)
        #                 print(f"Imagen guardada en: {file_path}")
                        
        #         #--------------------------------------------
    


        #     guardarCorreos()



#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


    #     with open(f"{carpeta_dia}/correo_{num.decode()}.txt", "w", encoding="utf-8") as f:
    #         f.write(f"De: {msg['From']}\nAsunto: {msg['Subject']}\n\n")

    #         if msg.is_multipart():
    #             for part in msg.walk():
    #                 if part.get_content_type() == "text/plain":
    #                     f.write(part.get_payload(decode=True).decode("utf-8", errors="ignore"))
    #         else:
    #             f.write(msg.get_payload(decode=True).decode("utf-8", errors="ignore"))

    #     for part in msg.walk():
    #         if part.get_content_disposition() and part.get_filename():
    #             filename = part.get_filename()
    #             filepath = os.path.join(carpeta_dia, filename)

    #             with open(filepath, "wb") as attachment_file:
    #                 attachment_file.write(part.get_payload(decode=True))

    #             print(f"📁 Archivo guardado: {filepath}")

    # fecha_actual += timedelta(days=1)

# mail.logout()
