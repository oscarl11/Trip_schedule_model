import pandas as pd
import numpy as np
from itertools import combinations
from datetime import datetime, timedelta
import pulp
import ast

#Iteración de tramos de trabajo
def form_tramos(df,tmin,tmax):
    # Lista para guardar las combinaciones válidas
    combinaciones_validas = []

    # Recorrer cada grupo por CC
    for cc, grupo in df.groupby("CC"):
        grupo = grupo.sort_values("hora_ro").reset_index(drop=True)

        for i, j in combinations(grupo.index, 2):
            t1 = grupo.loc[i, "hora_ro"]
            t2 = grupo.loc[j, "hora_ro"]
            diff = t2 - t1

            if tmin <= diff <= tmax:
                combinaciones_validas.append({
                    "CC": cc,
                    "hora_inicio": t1,
                    "estacion_inicio": grupo.loc[i, "estacion_ro"],
                    "hora_fin": t2,
                    "estacion_fin": grupo.loc[j, "estacion_ro"],
                    "duracion": diff,
                    "id_viaje_inicio": grupo.loc[i, "id_viaje"],
                    "id_viaje_fin": grupo.loc[j, "id_viaje"]
                })
    df_tramos_tr=pd.DataFrame(combinaciones_validas)
    return df_tramos_tr

#Agregar la columna a los tramos de trabajo en el que figura la lista de viajes que acapara el tramo
def generar_lista_ids(row):
    inicio = int(row['id_viaje_inicio'])
    fin = int(row['id_viaje_fin'])

    # Rango natural (sin incluir inicio)
    lista = list(range(inicio + 1, fin + 1))

    # Si inicio es múltiplo de 100 + 1 → incluir inicio
    if (inicio - 1) % 100 == 0:
        lista.insert(0, inicio)

    return lista