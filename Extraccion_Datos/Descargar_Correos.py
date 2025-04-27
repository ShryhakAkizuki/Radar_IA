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
from email import message_from_bytes
# ------------ Funciones ------------
def Aut_Gmail_Service(path: str ="../") -> object:
    """
    Carga las credenciales de autorización de Google a traves de GMAIL API en google cloud desde un archivo json y devuelve un servicio de Gmail autenticado.

    Args:
        path (string): Ruta de los archivo de credenciales json/pickle, por defecto esta afuera de la carpeta del script con el nombre AuthCredentials.json y token.pickle respectivamente.
    Returns:
        object: Retorna un objeto de servicio de Gmail autenticado.
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

# ------------ Variables ------------
mail = Aut_Gmail_Service()  # Servicio de correo Gmail autenticado

# Rango de fechas
FECHA_INICIO = datetime(2024, 1, 1)   # Fecha de inicio
FECHA_FIN = datetime(2025, 4, 22)     # Fecha de fin
Lista_Fechas = [FECHA_INICIO + timedelta(days=x) for x in range((FECHA_FIN - FECHA_INICIO).days + 1)]   # Creamos una lista de fechas desde la fecha de inicio hasta la fecha de fin (incluyendo ambas fechas)

# path de guardado
savepath="../Correos/"  # Ruta donde se guardaran los correos descargados
os.makedirs(savepath, exist_ok=True)  # Creamos la carpeta si no existe

# ------------ Guardar Correos ------------
    
def guardarCorreos():

    folder_path = os.path.join(savepath, Fecha.strftime("%Y/%B/%d"), "e-mail")
    html_filename = f"{subject}.html"  # Usamos el asunto como nombre del archivo
    html_filename = html_filename.replace(":", "_")
    
    file_path = os.path.join(folder_path, html_filename)
    folder_path = os.path.normpath(folder_path)
    # Crear las carpetas necesarias si no existen
    os.makedirs(folder_path, exist_ok=True)

    # Guardar el archivo HTML en la carpeta correcta
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(body)

    print(f"Archivo guardado en: {file_path}")
    

# ------------ Extracción de correos ------------
for Fecha in Lista_Fechas: # Buqueda de correos por fecha
    print(f"📅 Buscando correos para: {Fecha.strftime('%Y-%B-%d')}")

    # String de consulta para buscar correos en una fecha especifica
    search_query = f'(after:{(Fecha-timedelta(days=1)).strftime("%Y/%m/%d")} before:{(Fecha+timedelta(days=1)).strftime("%Y/%m/%d")}'  
    
    # -------- Realizamos la busqueda de todos los correos en la bandeja de entrada del dia --------
    response  = mail.users().messages().list(userId='me', q=search_query).execute() # Primera pagina de resultados de correos del dia
    messages  = response.get('messages', [])  

    while "nextPageToken" in response: # Si hay mas de 100 mensajes, paginamos
        page_token = response['nextPageToken']                                                                  # Obtenemos el token de la siguiente pagina
        response = mail.users().messages().list(userId='me', q=search_query, pageToken=page_token).execute()    # Obtenemos la siguiente pagina de resultados
        messages.extend(response.get('messages', []))                                                           # Agregamos los mensajes de la siguiente pagina a la lista de mensajes
    
    if(len(messages) == 0): # Si no hay mensajes, mostramos un mensaje y continuamos
        print(f"❌ No se encontraron correos")
    else:
        print(f"✅ Se encontraron {len(messages)} correos")
        # -------- Creamos la carpeta Año/mes/dia (si hay correos) --------
        os.makedirs(savepath+Fecha.strftime("%Y/%B/%d"), exist_ok=True)
    
    Folder_ID = 0
    # -------- Extraemos la informacion de los mensajes del dia --------
    for msg_id in messages:
        
        msg=mail.users().messages().get(userId='me', id=msg_id['id'], format='raw').execute()   # Obtenemos el mensaje completo usando el ID del mensaje
        msg = urlsafe_b64decode(msg["raw"].encode("utf-8"))                                     # Decodificamos el mensaje en base64
        msg = message_from_bytes(msg)                                                           # Convertimos el mensaje a un objeto de mensaje de email

        # -------- Asunto del mensaje --------
        subject = msg.get('subject')    
        #-------------------------------------

        body = ""                       # Inicializamos el cuerpo del mensaje

        if msg.is_multipart():          
            for part in msg.walk():     # Si el mensaje es multipart, recorremos las partes del mensaje
                
                # -------- Cuerpo del mensaje (HTML) --------
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    guardarCorreos()                    
                # -------- Imagenes del mensaje (JPEG) ------
                if part.get_content_type() == "image/jpeg":
                    filename = part.get_filename()
                    imageName=Fecha.strftime("%Y-%B-%d")
                    filename = f"{imageName}_{filename}"

                    # -------- Guardar Imagenes del mensaje ------

                    if filename:  # Si tiene nombre de archivo
                        file_data = part.get_payload(decode=True)  # Obtener el contenido del archivo
                        folder_path_images = os.path.join(savepath, Fecha.strftime("%Y/%B/%d"), "images")
                        os.makedirs(folder_path_images, exist_ok=True)
                        file_path = os.path.join(folder_path_images, filename)
    
                        with open(file_path, 'wb') as f:
                            f.write(file_data)
                        print(f"Imagen guardada en: {file_path}")
                        
                #--------------------------------------------
    
        else:   # Si el mensaje no es multipart, obtenemos el cuerpo e imagenes del mensaje directamente
            
            # -------- Cuerpo del mensaje (HTML) --------
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            # -------- Imagenes del mensaje (JPEG) ------
            filename = msg.get_filename()
            #--------------------------------------------

            guardarCorreos()



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
