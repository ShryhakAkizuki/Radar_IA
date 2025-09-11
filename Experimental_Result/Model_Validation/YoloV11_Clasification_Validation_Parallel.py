# -*- coding: utf-8 -*-
"""
Script para realizar la clasificacion del Dataset a traves de YOLOV11 usando diferentes modelos y multiples imagenes
Adaptado a ejecución en paralelo en CPU
"""

import os
import csv
import multiprocessing as mp
from ultralytics import YOLO

# ------------ Funciones ------------------------------------------------------------
def Model_list(base_path: str, device_type: str) -> list:
    Models = []
    for path in os.listdir(base_path):
        Complete_Path = f"{base_path}\\{path}\\weights\\best.pt"
        if os.path.exists(Complete_Path):
            Models.append((path, Complete_Path))  # guardamos solo la ruta, no el modelo
    return Models

def Make_Header(models: list) -> list:
    Header = ["Ruta", "Main_Label"]
    for name, _ in models:
        Header.append(f"{name} - prediction")
        Header.append(f"{name} - conf")
        Header.append(f"{name} - time [ms]")
    return Header

def run_model(args):
    """
    Función que se ejecuta en paralelo.
    Carga el modelo en este proceso, procesa el batch y devuelve resultados.
    """
    name, model_path, device, batch, data = args
    model = YOLO(model_path)
    model.to(device)

    results = []
    predict = model(batch, verbose=False)

    for i in range(len(predict)):
        row = data[i].copy()
        row[f"{name} - prediction"] = predict[i].probs.top1
        row[f"{name} - conf"] = predict[i].probs.top1conf.item()
        row[f"{name} - time [ms]"] = sum(predict[i].speed.values())
        results.append(row)

    return results

# -----------------------------------------------------------------------------------

if __name__ == "__main__":
    batch_size  = 20
    csv_path    = "..\\DB_Embarcaciones.csv"
    model_dir   = "..\\Model_Training\\YoloV11_Clasification_Experimental-Result\\runs"
    output_path = f"..\\YoloV11_Clasification-Results_Ryzen7-9800X3D_Batch_{batch_size}.csv"
    device      = "cpu"

    with open(csv_path, mode="r", newline='', encoding='utf-8') as infile, \
         open(output_path, mode="w", newline='', encoding='utf-8') as outfile:

        Models = Model_list(model_dir, device)                  # [(nombre, ruta_modelo), ...]
        reader = csv.DictReader(infile)
        Header = Make_Header(Models)
        writer = csv.DictWriter(outfile, fieldnames=Header)
        writer.writeheader()

        Batch = []
        Data = []
        Count = 0

        for row in reader:
            if row["Image_Name"] != "N/A":
                Ruta_Image = f"{row['Path']}\\{row['Image_Path']}\\{row['Image_Name']}"
                Batch.append(Ruta_Image)
                Data.append({"Ruta": Ruta_Image, "Main_Label": row["Main_Label"]})

            if len(Batch) == batch_size:
                # Ejecutamos todos los modelos en paralelo
                tasks = [(name, path, device, Batch, Data) for name, path in Models]

                with mp.Pool(processes=len(Models)) as pool:
                    results = pool.map(run_model, tasks)

                # results es una lista de listas (una por modelo)
                for model_results in results:
                    for row in model_results:
                        # merge results into Data (matching by Ruta)
                        idx = next(i for i, d in enumerate(Data) if d["Ruta"] == row["Ruta"])
                        Data[idx].update(row)

                for item in Data:
                    writer.writerow(item)

                print(f"Batch Finalizado, ultima imagen: {Batch[-1]}")
                Count += len(Data)
                Batch = []
                Data = []

        # último batch (incompleto)
        if Batch:
            tasks = [(name, path, device, Batch, Data) for name, path in Models]
            with mp.Pool(processes=len(Models)) as pool:
                results = pool.map(run_model, tasks)

            for model_results in results:
                for row in model_results:
                    idx = next(i for i, d in enumerate(Data) if d["Ruta"] == row["Ruta"])
                    Data[idx].update(row)

            for item in Data:
                writer.writerow(item)

            print(f"Batch Finalizado (último batch incompleto), última imagen: {Batch[-1]}")
            Count += len(Data)

        print(Count)
