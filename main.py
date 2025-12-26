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

lista_estaciones=st.text_input('Ingrese las estaciones en las que se realizarán los relevos')

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
Tlim_min_alm_h = st.number_input(
    "Duración mínima refrigerio (horas)",
    min_value=0,
    max_value=24,
    value=0
)

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


#Tint_max=st.time_input("Duración máxima almuerzo, regulares",step=600)
Tlim_max_alm_h = st.number_input(
    "Duración máxima refrigerio (horas)",
    min_value=0,
    max_value=24,
    value=1
)

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
Tlim_min_tramo_h = st.number_input(
    "Duración mínima tramo (horas)",
    min_value=0,
    max_value=24,
    value=1
)

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

Tlim_max_tramo_h = st.number_input(
    "Duración máxima tramo (horas)",
    min_value=0,
    max_value=24,
    value=6
)

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

#LÍMITE DE TIEMPO JORNADAS DE TRABAJO
st.write('Ingrese los límites duración de las jornadas de trabajo')
Tmin_jornada_h = st.number_input(
    "Duración mínima jornada (horas)",
    min_value=0,
    max_value=24,
    value=6
)

Tmin_jornada_m = st.number_input(
    "Duración mínima jornada (minutos)",
    min_value=0,
    max_value=59,
    value=30
)

tmin_jornada = pd.Timedelta(
    hours=Tmin_jornada_h,
    minutes=Tmin_jornada_m
)

#------------------------------------------------------------------------------------------

Tmax_jornada_h = st.number_input(
    "Duración máxima tramo (horas)",
    min_value=0,
    max_value=24,
    value=9
)

Tmax_jornada_m = st.number_input(
    "Duración máxima tramo (minutos)",
    min_value=0,
    max_value=59,
    value=11
)

tmax_jornada = pd.Timedelta(
    hours=Tmax_jornada_h,
    minutes=Tmax_jornada_m
)

#FORMACIÓN DE TRAMOS DE TRABAJO
if st.button("Generar tramos"):
    st.session_state.df_tramos = form_tramos(
        df=st.session_state.df_lista_ro,
        tmin=Tlim_min_tramo,
        tmax=Tlim_max_tramo
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

#FORMACIÓN DE JORNADAS DE TRABAJO
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
    st.dataframe(st.session_state.df_jornada_regular.head(20))

'''
st.graphviz_chart('''
    digraph {
        Inicio -> Subida_de_archivo
        Subida_de_archivo -> Identificación_de_relevos
        Identificación_de_relevos -> Iteración_de_tramos
        Iteración_de_tramos -> Formación_de_jornadas
        Formación_de_jornadas -> Selección_de_jornadas
        Selección_de_jornadas -> Fin                            
    }
''')
'''

