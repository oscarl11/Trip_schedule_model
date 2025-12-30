import pandas as pd
import numpy as np
import streamlit as st
#import graphviz as graphviz
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from itertools import combinations
import pulp
import ast

from trip_ro import *
from tramos import *
from jornadas import *

#INICIALIZACIÓN DE ESTADOS
if "df_ro" not in st.session_state:
    st.session_state.df_ro = None

if "estaciones" not in st.session_state:
    st.session_state.estaciones = None

if "df_lista_ro" not in st.session_state:
    st.session_state.df_lista_ro = None

if "df_tramos" not in st.session_state:
    st.session_state.df_tramos = None
if "df_jornada_partida" not in st.session_state:
    st.session_state.df_jornada_partida = None

if "df_jornada_regular" not in st.session_state:
    st.session_state.df_jornada_regular = None

if "df_jornada_despl" not in st.session_state:
    st.session_state.df_jornada_despl = None

if "traslados_validos" not in st.session_state:
    st.session_state.traslados_validos = {}

#DISEÑO

st.title("Generación de Horarios POD - TRV")

st.sidebar.title("Línea de programación")
st.sidebar.radio("Elija la línea",["Alimentador","Troncal"])

#SUBIDA DE ARCHIVO CSV

st.subheader("Subida de archivo")
st.write("Ingrese el archivo excel a modelar:")
format_POD=st.file_uploader("Archivo xlsx",type=['csv'])

if format_POD is not None:
    POD=lectura_csv(format_POD)
    df=pd.DataFrame(POD)
    st.write('Archivo subido exitosamente')
    st.dataframe(df.head(20))
    st.write(f"Dimensiones del DataFrame: {df.shape[0]} filas, {df.shape[1]} columnas")
else:
    st.info("Por favor, sube un archivo CSV con la programación para empezar.")

#ACONDICIONAMIENTO DE ARCHIVO + EXTRACCIÓN DE RO

lista_estaciones=st.text_input('Ingrese las estaciones de relevo factibles en el siguiente formato: EST1,EST2,EST3')

if st.button('Generar relief opportunities'):
    estaciones_list = [
        e.strip() for e in lista_estaciones.split(",") if e.strip()
    ]
    estaciones=pd.DataFrame({'estaciones': estaciones_list})
    permutaciones= pd.DataFrame()
    df_ro=pd.DataFrame()
    for i in df["CC"].unique():
        lista_de_rosxCC,dfsal,dfenc=filtro_ro(df[df["CC"]==i],estaciones)
        df_ro = pd.concat([df_ro, lista_de_rosxCC,dfsal.to_frame().T,dfenc.to_frame().T], ignore_index=True)
    st.session_state.df_ro=df_ro
    st.session_state.estaciones=estaciones
    st.dataframe(st.session_state.df_ro.head(20))
else:
    st.write('Dele click para generar la base preliminar de puntos de relevo')


#CONFECCIÓN DE LISTA DE RELIEF OPPORTUNITIES

if st.button("Generar lista total de RO's"):
    df_lista_ro=frame_ro(st.session_state.df_ro,st.session_state.estaciones)
    st.dataframe(df_lista_ro.head(20))
    st.session_state.df_lista_ro=df_lista_ro
else:
    st.write('Dele click para generar la base de puntos de relevo')


#INGRESO DE PARÁMETROS

st.subheader("Parámetros de horarios")

Tlim_alm_min=st.time_input("Hora mínima de almuerzo",step=600)
Tlim_alm_max=st.time_input("Hora máxima de almuerzo",step=600)

#DURACIÓN DE ALMUERZO
st.write('Ingrese los límites duración de los almuerzos')
#Tint_min=st.time_input("Duración mínima almuerzo, regulares",step=600)
col1_1,col2_1=st.columns(2)
with col1_1:
    Tlim_min_alm_h = st.number_input(
        "Duración mínima refrigerio (horas)",
        min_value=0,
        max_value=24,
        value=0
    )
with col2_1:
    Tlim_min_alm_m = st.number_input(
        "Duración mínima refrigerio (minutos)",
        min_value=0,
        max_value=59,
        value=49
    )

tmin_alm = pd.Timedelta(
    hours=Tlim_min_alm_h,
    minutes=Tlim_min_alm_m
)

col1_1,col2_1=st.columns(2)
#Tint_max=st.time_input("Duración máxima almuerzo, regulares",step=600)
with col1_1:
    Tlim_max_alm_h = st.number_input(
        "Duración máxima refrigerio (horas)",
        min_value=0,
        max_value=24,
        value=1
    )

with col2_1:
    Tlim_max_alm_m = st.number_input(
        "Duración máxima refrigerio (minutos)",
        min_value=0,
        max_value=59,
        value=30
    )

tmax_alm = pd.Timedelta(
    hours=Tlim_max_alm_h,
    minutes=Tlim_max_alm_m
)



Tlim_ro_min=st.time_input("Mínima hora de relevo",step=600)
Tlim_ro_max=st.time_input("Máxima hora de relevo",step=600)
Hora_trabajo_max_partido=st.text_input("Hora máxima de salida turno partido")
#despl_estaciones=
#despl_tiempos=

# LIMITE DE TIEMPO DE TRABAJO CONTINUO (TRAMOS DE TRABAJO)
#Tlim_min_tramo=st.time_input("Mínima duración de tramo de trabajo")

st.write('Ingrese los límites duración de los tramos de trabajo')

col1_1,col2_1=st.columns(2)
with col1_1:
    Tlim_min_tramo_h = st.number_input(
        "Duración mínima tramo (horas)",
        min_value=0,
        max_value=24,
        value=1
    )

with col2_1:
    Tlim_min_tramo_m = st.number_input(
        "Duración mínima tramo (minutos)",
        min_value=0,
        max_value=59,
        value=20
    )

Tlim_min_tramo = pd.Timedelta(
    hours=Tlim_min_tramo_h,
    minutes=Tlim_min_tramo_m
)

#Tlim_max_tramo=st.time_input("Máxima duración de tramo de trabajo")
col1_1,col2_1=st.columns(2)

with col1_1:
    Tlim_max_tramo_h = st.number_input(
        "Duración máxima tramo (horas)",
        min_value=0,
        max_value=24,
        value=6
    )

with col2_1:
    Tlim_max_tramo_m = st.number_input(
        "Duración máxima tramo (minutos)",
        min_value=0,
        max_value=59,
        value=30
    )

Tlim_max_tramo = pd.Timedelta(
    hours=Tlim_max_tramo_h,
    minutes=Tlim_max_tramo_m
)



#FORMACIÓN DE TRAMOS DE TRABAJO
if st.button("Generar tramos"):
    st.session_state.df_tramos = form_tramos(
        df=st.session_state.df_lista_ro,
        tmin=Tlim_min_tramo,
        tmax=Tlim_max_tramo,
        lista_estaciones=st.session_state.estaciones
    )
    st.session_state.df_tramos['lista_id_viaje']=st.session_state.df_tramos.apply(generar_lista_ids,axis=1)
    csv_tramos=st.session_state.df_tramos.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Descargar base de tramos de trabajo",
        csv_tramos,
        'Tramos_trabajo.csv',
        'text/csv',
        key='download-csv'
    )
    st.dataframe(st.session_state.df_tramos.head(20))

st.divider()

#LÍMITE DE TIEMPO JORNADAS DE TRABAJO REGULARES

st.write('Ingrese los límites duración de las jornadas de trabajo del turno regular')

col1_1,col2_1=st.columns(2)

with col1_1:
    Tmin_jornada_h = st.number_input(
        "Duración mínima jornada regular (horas)",
        min_value=0,
        max_value=24,
        value=6
    )

with col2_1:
    Tmin_jornada_m = st.number_input(
        "Duración mínima jornada regular (minutos)",
        min_value=0,
        max_value=59,
        value=30
    )

tmin_jornada = pd.Timedelta(
    hours=Tmin_jornada_h,
    minutes=Tmin_jornada_m
)

#------------------------------------------------------------------------------------------
with col1_1:
    Tmax_jornada_h = st.number_input(
        "Duración máxima jornada regular (horas)",
        min_value=0,
        max_value=24,
        value=9
    )

with col2_1:
    Tmax_jornada_m = st.number_input(
        "Duración máxima jornada regular (minutos)",
        min_value=0,
        max_value=59,
        value=11
    )

tmax_jornada = pd.Timedelta(
    hours=Tmax_jornada_h,
    minutes=Tmax_jornada_m
)

#LÍMITE DE TIEMPO JORNADAS DE TRABAJO PARTIDOS
st.write('Ingrese los límites duración de las jornadas de trabajo del turno partido')

col1_1,col2_1=st.columns(2)

with col1_1:
    Tmin_jornada_part_h = st.number_input(
        "Duración mínima jornada partida (horas)",
        min_value=0,
        max_value=24,
        value=6
    )

with col2_1:
    Tmin_jornada_part_m = st.number_input(
        "Duración mínima jornada partida (minutos)",
        min_value=0,
        max_value=59,
        value=30
    )

tmin_part_jornada = pd.Timedelta(
    hours=Tmin_jornada_h,
    minutes=Tmin_jornada_m
)

#------------------------------------------------------------------------------------------
with col1_1:
    Tmax_jornada_part_h = st.number_input(
        "Duración máxima jornada partida (horas)",
        min_value=0,
        max_value=24,
        value=9
    )

with col2_1:
    Tmax_jornada_part_m = st.number_input(
        "Duración máxima jornada partida (minutos)",
        min_value=0,
        max_value=59,
        value=11
    )

tmax_part_jornada = pd.Timedelta(
    hours=Tmax_jornada_h,
    minutes=Tmax_jornada_m
)

#FORMACIÓN DE JORNADAS DE TRABAJO PARTIDOS, HORA LÍMITE FIN
max_hora_partido=st.time_input("Hora fin límite para turno partido", value=datetime.strptime("22:30", "%H:%M").time())

#Traslado de conductor entre estaciones

st.write("Definir traslados válidos entre estaciones")
col1_2,col2_2,col3_2,col4_2=st.columns(4)
with col1_2:
    est1_tras = st.text_input("Est. inicio traslado ej: NARL")

with col2_2:
    est2_tras = st.text_input("Est. fin traslado ej: RCAS")

with col3_2:
    min_tras = st.number_input("Min. de traslado", min_value=1, max_value=180, value=25)

with col4_2:
    modo_tras = st.selectbox("Tipo de traslado", ["adelantar_2", "extender_1"])

# Botón para agregar traslado al diccionario
if st.button("Agregar traslado"):
    if est1_tras and est2_tras:  # evitar claves vacías
        clave = (est1_tras, est2_tras)

        # Construir modos como set interno que espera tu función
        if modo_tras == "adelantar_2":
            modos = {"adelantar_2"}
        else:
            modos = {"extender_1"}

        # Guardar en session_state
        st.session_state.traslados_validos[clave] = {
            "tiempo": timedelta(minutes=min_tras),
            "modos": modos
        }
        st.success(f"Traslado {clave} agregado.")
    else:
        st.error("Debes completar ambas estaciones.")

# Mostrar todos los traslados registrados
if st.session_state.traslados_validos:
    st.write("Traslados registrados:")
    registros = [
        {"est_fin_1": k[0], "est_ini_2": k[1], "minutos": v["tiempo"].seconds // 60, "modos": list(v["modos"])}
        for k, v in st.session_state.traslados_validos.items()
    ]
    st.dataframe(registros)

st.divider()

if st.button("Generar jornadas"):
    st.session_state.df_jornada_regular=jornadas_regular_eq_est(st.session_state.df_tramos,tmin_jornada,tmax_jornada,tmin_alm,tmax_alm)
    csv_jornadas_regular=st.session_state.df_jornada_regular.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Descargar base de jornadas de trabajo regulares",
        csv_jornadas_regular,
        'Jornadas_regular.csv',
        'text/csv',
        key='download-csv'
    )
    st.session_state.df_jornada_partida=jornadas_partido_eq_est(st.session_state.df_tramos,tmin_part_jornada,tmax_part_jornada,max_hora_partido)
    csv_jornadas_partida=st.session_state.df_jornada_partida.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Descargar base de jornadas de trabajo partida",
        csv_jornadas_partida,
        'Jornadas_partidas.csv',
        'text/csv',
        key='download-csv'
    )

    st.session_state.df_jornada_despl=jornadas_regular_diff_est(st.session_state.df_tramos,st.session_state.traslados_validos,tmin_alm,tmax_alm,tmin_jornada,tmax_jornada)
    csv_jornadas_despl=st.session_state.df_jornada_despl.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Descargar base de jornadas de trabajo regular con desplazamiento",
        csv_jornadas_despl,
        'Jornadas_despl.csv',
        'text/csv',
        key='download-csv'
    )
    st.dataframe(st.session_state.df_jornada_despl.head(20))






