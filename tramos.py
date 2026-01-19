import pandas as pd
import numpy as np
from itertools import combinations
from datetime import datetime, timedelta
import pulp
import ast

#Iteración de tramos de trabajo
def form_tramos(df,tmin,tmax,lista_estaciones):
    # Lista para guardar las combinaciones válidas
    combinaciones_validas = []

    # Recorrer cada grupo por CC
    for cc, grupo in df.groupby("CC"):
        grupo = grupo.sort_values("hora_ro").reset_index(drop=True)

        for i, j in combinations(grupo.index, 2):
            t1 = grupo.loc[i, "hora_ro"]
            t2 = grupo.loc[j, "hora_ro"]
            if grupo.loc[i,"estacion_ro"] != "PNOR" and grupo.loc[i,"estacion_ro"] in (lista_estaciones['estaciones']): 
                relevo=timedelta(hours=0,minutes=4)
            else: relevo = timedelta(0)
            diff = t2 - t1- relevo
            

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

#Descartar tramos que tengan totalmente incluido los horarios límites de almuerzo
def sel_tramo_incl_Talm(df,Talm_min,Talm_max):
    fecha_base=df["hora_inicio"].dt.date.min()
    limite_min = datetime.combine(fecha_base, Talm_min)
    limite_max = datetime.combine(fecha_base, Talm_max)
    df_subconj_lim_alm=df[(df['hora_inicio']<limite_min) &(df['hora_fin']>limite_max)]
    df_extr_alm=df[~df['lista_id_viaje'].isin(df_subconj_lim_alm['lista_id_viaje'])]
    return df_extr_alm
