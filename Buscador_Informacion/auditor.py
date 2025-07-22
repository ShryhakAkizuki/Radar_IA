# -*- coding: utf-8 -*-
"""
Created on Fri Apr 11 10:57:10 2025

"""

import csv

def buscar_por_codigo(archivo_csv, codigo_buscado):
    resultados = []

    with open(archivo_csv, 'r', encoding='utf-8') as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            if fila.get('codigo') == codigo_buscado:
                resultados.append(fila)

    if resultados:
        print(f"\nEncontradas {len(resultados)} imágenes para el código {codigo_buscado}:\n")
        for i, img in enumerate(resultados, start=1):
            print(f"[{i}] Nombre: {img['nombre_imagen']}")
            print(f"     Fecha: {img['carpeta_mes']}/{img['carpeta_dia']}")
            print(f"     Ruta: {img['ruta_relativa']}")
            print(f"     Total de imágenes para este código: {img['total_imagenes']}")
            print()
    else:
        print(f"No se encontraron imágenes con el código {codigo_buscado}.")

# Ejecución interactiva
if __name__ == "__main__":
    archivo_csv = 'indice_imagenes.csv'  # Cambia esto si tu archivo tiene otro nombre
    codigo = input("Ingrese el código de imagen que desea buscar: ").strip()
    buscar_por_codigo(archivo_csv, codigo)