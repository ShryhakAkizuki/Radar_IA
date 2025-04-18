# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 13:39:58 2025
"""

import imaplib 
import email
import os
from datetime import datetime, timedelta

# --------------------------------------
# Leer credenciales desde archivo externo
# --------------------------------------
def cargar_credenciales(path="../../credenciales.txt"):
    credenciales = {}
    with open(path, "r", encoding="utf-8") as f:
        for linea in f:
            if "=" in linea:
                clave, valor = linea.strip().split("=", 1)
                credenciales[clave.strip()] = valor.strip()
    return credenciales

cred = cargar_credenciales()
EMAIL_ACCOUNT = cred["EMAIL"]
EMAIL_PASSWORD = cred["PASSWORD"]

# Configuración del servidor
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

# Rango de fechas
FECHA_INICIO = "15-Mar-2025"
FECHA_FIN = "20-Mar-2025"

# Conectar al correo
mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
mail.select("inbox")

# Convertimos las fechas a objetos datetime
fecha_actual = datetime.strptime(FECHA_INICIO, "%d-%b-%Y")
fecha_limite = datetime.strptime(FECHA_FIN, "%d-%b-%Y")

while fecha_actual <= fecha_limite:
    FECHA_OBJETIVO = fecha_actual.strftime("%d-%b-%Y")
    FECHA_BEFORE = (fecha_actual + timedelta(days=1)).strftime("%d-%b-%Y")

    search_query = f'(SINCE {FECHA_OBJETIVO} BEFORE {FECHA_BEFORE} FROM "{EMAIL_ACCOUNT}")'
    print(f"📅 Buscando correos para: {FECHA_OBJETIVO}")

    result, data = mail.search(None, search_query)
    email_ids = data[0].split()

    carpeta_mes = fecha_actual.strftime("Correos_%b-%Y")
    os.makedirs(carpeta_mes, exist_ok=True)

    carpeta_dia = os.path.join(carpeta_mes, FECHA_OBJETIVO)
    os.makedirs(carpeta_dia, exist_ok=True)

    for num in email_ids:
        result, msg_data = mail.fetch(num, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        with open(f"{carpeta_dia}/correo_{num.decode()}.txt", "w", encoding="utf-8") as f:
            f.write(f"De: {msg['From']}\nAsunto: {msg['Subject']}\n\n")

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        f.write(part.get_payload(decode=True).decode("utf-8", errors="ignore"))
            else:
                f.write(msg.get_payload(decode=True).decode("utf-8", errors="ignore"))

        for part in msg.walk():
            if part.get_content_disposition() and part.get_filename():
                filename = part.get_filename()
                filepath = os.path.join(carpeta_dia, filename)

                with open(filepath, "wb") as attachment_file:
                    attachment_file.write(part.get_payload(decode=True))

                print(f"📁 Archivo guardado: {filepath}")

    fecha_actual += timedelta(days=1)

mail.logout()