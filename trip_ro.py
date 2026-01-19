import pandas as pd
import numpy as np
from itertools import combinations
from datetime import datetime, timedelta

#Lectura de documento + limpieza de horas
def lectura_csv(path_file):
    df = pd.read_csv(path_file, parse_dates=['hora_inicio', 'hora_fin'], sep=";")
    limit=timedelta(hours=3)
    today = pd.Timestamp.today().normalize()  # Obtener fecha de hoy sin hora
    date_limit=today+limit
    for j in df.index:
        if df.loc[j,"hora_inicio"]<=date_limit:
            df.loc[j,"hora_inicio"]=df.loc[j,"hora_inicio"]+timedelta(days=1)
        else:
            df.loc[j,"hora_inicio"]=df.loc[j,"hora_inicio"]
        if df.loc[j,"hora_fin"]<=date_limit:
            df.loc[j,"hora_fin"]=df.loc[j,"hora_fin"]+timedelta(days=1)
        else:
            df.loc[j,"hora_fin"]=df.loc[j,"hora_fin"]
    
    return df

def filtro_ro(df,lista_estaciones):
    lista_ro = df[df['estación_fin'].isin(lista_estaciones['estaciones'])].sort_values(by='hora_inicio')
    df_sal = df.loc[df["hora_inicio"].idxmin()]
    df_enc = df.loc[df["hora_fin"].idxmax()]
    return lista_ro,df_sal,df_enc

def frame_ro(df,lista_estaciones):
    #Extracción del primer punto con PNOR
    lista_perm_PNOR = df[df['estacion_inicio'] == "PNOR"][['id_viaje','CC', 'hora_inicio', 'estacion_inicio']].copy()
    lista_perm_PNOR.rename(columns={'hora_inicio': 'hora_ro', 'estacion_inicio': 'estacion_ro'}, inplace=True)
    
    #Extracción de las estaciones de destino presentes en la lista 'estaciones'
    lista_perm_rest = df[df['estación_fin'].isin(lista_estaciones['estaciones'])& (df['estacion_inicio']!="PNOR")][['id_viaje','CC', 'hora_fin', 'estación_fin']].copy()
    lista_perm_rest.rename(columns={'hora_fin': 'hora_ro', 'estación_fin': 'estacion_ro'}, inplace=True)

    #Extracción del último punto con PNOR
    lista_PNOR_fin = df[df['estación_fin']=="PNOR"][['id_viaje','CC', 'hora_fin', 'estación_fin']].copy()
    lista_PNOR_fin.rename(columns={'hora_fin': 'hora_ro', 'estación_fin': 'estacion_ro'}, inplace=True)

    #Concatenar 3 listas y reemplazo de nombres de estación Naranjal (alimentador)
    lista_ro = pd.concat([lista_perm_PNOR, lista_perm_rest,lista_PNOR_fin], ignore_index=True)
    lista_ro_fin=lista_ro.sort_values(by=['CC','hora_ro']).drop_duplicates().reset_index(drop=True)
    lista_ro_fin.replace({'estacion_ro':{'NA16':'NARL','NA02':'NARL','NA02':'NARL', 'NA06':'NARL','NA07':'NARL','NA14':'NARL','NA15':'NARL','NA17':'NARL','NA18':'NARL'}},inplace=True)

    return lista_ro_fin
