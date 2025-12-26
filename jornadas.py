import pandas as pd
import numpy as np
from itertools import combinations
from datetime import datetime, timedelta
import pulp
import ast

#Formación de Jornadas turno regular, misma estación
def jornadas_regular_eq_est (df,tmin_jornada,tmax_jornada,tmin_alm,tmax_alm):
    # Ordenamos por hora de inicio
    df_combinaciones_regular = df.sort_values("hora_inicio").reset_index(drop=True)

    combinaciones_encadenadas = []

# Recorremos todas las combinaciones de pares (i, j) donde j > i
    for i in range(len(df_combinaciones_regular) - 1):
        fila_i = df_combinaciones_regular.loc[i]

        for j in range(i + 1, len(df_combinaciones_regular)):
            fila_j = df_combinaciones_regular.loc[j]

            # Estación debe coincidir
            misma_estacion = fila_i["estacion_fin"] == fila_j["estacion_inicio"]

            # Tiempo entre fin del tramo 1 e inicio del tramo 2
            diff_espera = fila_j["hora_inicio"] - fila_i["hora_fin"]
            espera_valida = tmin_alm <= diff_espera <= tmax_alm

            # Suma de duración total
            duracion_total = fila_i["duracion"] + fila_j["duracion"]
            duracion_valida = tmin_jornada <= duracion_total <= tmax_jornada

            if misma_estacion and espera_valida and duracion_valida:
                combinaciones_encadenadas.append({
                    "CC_1": fila_i["CC"],
                    "hora_inicio_1": fila_i["hora_inicio"],
                    "estacion_inicio_1": fila_i["estacion_inicio"],
                    "hora_fin_1": fila_i["hora_fin"],
                    "estacion_fin_1": fila_i["estacion_fin"],
                    "CC_2": fila_j["CC"],
                    "hora_inicio_2": fila_j["hora_inicio"],
                    "estacion_inicio_2": fila_j["estacion_inicio"],
                    "hora_fin_2": fila_j["hora_fin"],
                    "estacion_fin_2": fila_j["estacion_fin"],
                    "espera_entre_tramos": diff_espera,
                    "duracion_total": duracion_total,
                    "lista_id_viaje":fila_i["lista_id_viaje"]+fila_j["lista_id_viaje"]
                })

    # Creamos el DataFrame con los resultados
    df_jorn_eq_regular = pd.DataFrame(combinaciones_encadenadas)
    df_jorn_eq_regular["tipo_turno"]="Regular"
    return df_jorn_eq_regular