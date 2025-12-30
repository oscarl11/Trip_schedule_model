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

#Formación de Jornadas turno partido
max_hora_partido=timedelta(hours=22,minutes=30)

def jornadas_partido_eq_est (df,tmin_part,tmax_part,max_hora_partido):
    df_combinaciones = df[df["hora_fin"]<max_hora_partido]
    df_combinaciones_partido = df_combinaciones.sort_values("hora_inicio").reset_index(drop=True)

    resultados_filtro_avanzado = []

    for idx_a in range(len(df_combinaciones_partido) - 1):
        tramo_a = df_combinaciones_partido.loc[idx_a]

        for idx_b in range(idx_a + 1, len(df_combinaciones_partido)):
            tramo_b = df_combinaciones_partido.loc[idx_b]

            # Verificamos duración total combinada
            tiempo_total = tramo_a["duracion"] + tramo_b["duracion"]
            if not (tmin_part <= tiempo_total <= tmax_part):
                continue

            # Calculamos la espera entre tramos
            lapso_descanso = tramo_b["hora_inicio"] - tramo_a["hora_fin"]

            misma_base = tramo_a["estacion_fin"] == tramo_b["estacion_inicio"]
            if misma_base:
                if lapso_descanso <= timedelta(hours=1, minutes=42):
                    continue
            else:
                if lapso_descanso <= timedelta(hours=2, minutes=40):
                    continue

            hora_limite_part = datetime.combine(tramo_a["hora_inicio"].date(), max_hora_partido)
            if tramo_b["hora_fin"] > hora_limite_part:
                continue

            # Validamos límite horario del segundo tramo
            '''
            if tramo_b["hora_fin"].time() > pd.to_datetime("22:30").time():
                continue
            '''
            # Si pasa todos los filtros, lo agregamos
            resultados_filtro_avanzado.append({
                "CC_1": tramo_a["CC"],
                "hora_inicio_1": tramo_a["hora_inicio"],
                "estacion_inicio_1": tramo_a["estacion_inicio"],
                "hora_fin_1": tramo_a["hora_fin"],
                "estacion_fin_1": tramo_a["estacion_fin"],

                "CC_2": tramo_b["CC"],
                "hora_inicio_2": tramo_b["hora_inicio"],
                "estacion_inicio_2": tramo_b["estacion_inicio"],
                "hora_fin_2": tramo_b["hora_fin"],
                "estacion_fin_2": tramo_b["estacion_fin"],

                "espera_entre_tramos": lapso_descanso,
                "duracion_total": tiempo_total,
                "lista_id_viaje":tramo_a["lista_id_viaje"]+tramo_b["lista_id_viaje"]
            })

    # Convertimos a DataFrame
    df_avanzado = pd.DataFrame(resultados_filtro_avanzado)
    df_avanzado["tipo_turno"]="Partido"
    return df_avanzado

def jornadas_regular_diff_est (df_combinaciones,traslados_validos,ESPERA_MIN,ESPERA_MAX,DUR_MIN,DUR_MAX):
    df = df_combinaciones.sort_values("hora_inicio").reset_index(drop=True)

    df["lista_id_viaje"] = df["lista_id_viaje"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    resultados = []

    for i in range(len(df) - 1):
        t1 = df.loc[i]

        for j in range(i + 1, len(df)):
            t2 = df.loc[j]

            if t1["CC"] == t2["CC"]:
                continue

            est_fin_1 = t1["estacion_fin"]
            est_ini_2 = t2["estacion_inicio"]

            if est_fin_1 == est_ini_2:
                continue

            clave = (est_fin_1, est_ini_2)
            if clave not in traslados_validos:
                continue

            traslado_info = traslados_validos[clave]
            traslado = traslado_info["tiempo"]
            modos_validos = traslado_info["modos"]

            # ==================================================
            # ESCENARIO A → ADELANTAR INICIO TRAMO 2
            # ==================================================
            if "adelantar_2" in modos_validos:

                nuevo_inicio_2 = t2["hora_inicio"] - traslado

                if nuevo_inicio_2 >= t1["hora_fin"]:

                    espera_total = nuevo_inicio_2 - t1["hora_fin"]

                    duracion_total = (
                        (t1["hora_fin"] - t1["hora_inicio"]) +
                        (t2["hora_fin"] - nuevo_inicio_2)
                    )

                    if ESPERA_MIN <= espera_total <= ESPERA_MAX and \
                    DUR_MIN <= duracion_total <= DUR_MAX:

                        resultados.append({
                            "CC_1": t1["CC"],
                            "hora_inicio_1": t1["hora_inicio"],
                            "estacion_inicio_1": t1["estacion_inicio"],
                            "hora_fin_1": t1["hora_fin"],
                            "estacion_fin_1": est_fin_1,

                            "CC_2": t2["CC"],
                            "hora_inicio_2": nuevo_inicio_2,
                            "estacion_inicio_2": est_fin_1,
                            "hora_fin_2": t2["hora_fin"],
                            "estacion_fin_2": t2["estacion_fin"],

                            "tipo_ajuste": "adelantar_2",
                            "traslado": traslado,
                            "espera_total": espera_total,
                            "duracion_total": duracion_total,
                            "lista_id_viaje": t1["lista_id_viaje"] + t2["lista_id_viaje"]
                        })

            # ==================================================
            # ESCENARIO B → EXTENDER FIN TRAMO 1
            # ==================================================
            if "extender_1" in modos_validos:

                nuevo_fin_1 = t1["hora_fin"] + traslado

                if t2["hora_inicio"] >= nuevo_fin_1:

                    espera_total = t2["hora_inicio"] - nuevo_fin_1

                    duracion_total = (
                        (nuevo_fin_1 - t1["hora_inicio"]) +
                        (t2["hora_fin"] - t2["hora_inicio"])
                    )

                    if ESPERA_MIN <= espera_total <= ESPERA_MAX and \
                    DUR_MIN <= duracion_total <= DUR_MAX:

                        resultados.append({
                            "CC_1": t1["CC"],
                            "hora_inicio_1": t1["hora_inicio"],
                            "estacion_inicio_1": t1["estacion_inicio"],
                            "hora_fin_1": nuevo_fin_1,
                            "estacion_fin_1": est_ini_2,

                            "CC_2": t2["CC"],
                            "hora_inicio_2": t2["hora_inicio"],
                            "estacion_inicio_2": est_ini_2,
                            "hora_fin_2": t2["hora_fin"],
                            "estacion_fin_2": t2["estacion_fin"],

                            "tipo_ajuste": "extender_1",
                            "traslado": traslado,
                            "espera_entre_tramos": espera_total,
                            "duracion_total": duracion_total,
                            "lista_id_viaje": t1["lista_id_viaje"] + t2["lista_id_viaje"]
                        })

    df_empalmes_diff = pd.DataFrame(resultados)

    return df_empalmes_diff
