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
from algoritmo import *

#INICIALIZACIÓN DE ESTADOS
if "df_pod" not in st.session_state:
    st.session_state.df_pod = None

if "df_ro" not in st.session_state:
    st.session_state.df_ro = None

if "estaciones" not in st.session_state:
    st.session_state.estaciones = None

if "df_lista_ro" not in st.session_state:
    st.session_state.df_lista_ro = None

if "df_excl_alm" not in st.session_state:
    st.session_state.df_excl_alm = None

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

if "traslados_validos_ini" not in st.session_state:
    st.session_state.traslados_validos_ini = {}

if "df_jornada_total" not in st.session_state:
    st.session_state.df_jornada_total = None

if "lista_ids_viaje" not in st.session_state:
    st.session_state.lista_ids_viaje = None

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
    st.session_state.df_pod=df
    st.write('Archivo subido exitosamente')
    st.dataframe(df.head(20))
    st.write(f"Dimensiones del DataFrame: {df.shape[0]} filas, {df.shape[1]} columnas")
else:
    st.info("Por favor, sube un archivo CSV con la programación para empezar.")

#Generación de la lista con los id_viaje

if st.session_state.df_pod is not None:
    st.session_state.lista_ids_viaje = (
        st.session_state.df_pod[['id_viaje']]
        .drop_duplicates()
        .reset_index(drop=True)
    )


#ACONDICIONAMIENTO DE ARCHIVO + EXTRACCIÓN DE RO

lista_estaciones=st.text_input('Ingrese las estaciones de relevo factibles en el siguiente formato: EST1,EST2,EST3')

if st.button('Filtrar lista con relief opportunities'):
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

if st.button("Generar base total de RO's"):
    df_lista_ro=frame_ro(st.session_state.df_ro,st.session_state.estaciones)
    st.dataframe(df_lista_ro.head(20))
    st.session_state.df_lista_ro=df_lista_ro
else:
    st.write('Dele click para generar la base de puntos de relevo')


#INGRESO DE PARÁMETROS

st.subheader("Parámetros de horarios")

#HORAS LÍMITE DE ALMUERZO
st.write("Se descartarán aquellos tramos que no tengan un corte de almuerzo en el siguiente rango")
col1_1,col2_1=st.columns(2)
with col1_1:
    Tlim_alm_min=st.time_input("Horario límite mínimo de almuerzo", value=datetime.strptime("12:30", "%H:%M").time(),step=300)
with col2_1:    
    Tlim_alm_max=st.time_input("Horario límite máximo de almuerzo", value=datetime.strptime("14:30", "%H:%M").time(),step=300)

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


st.write("Descarte de RO's que esten fuera del siguiente rango horario")
col1_1,col2_1=st.columns(2)
with col1_1:
    Tlim_ro_min=st.time_input("Mínima hora de relevo",step=600)
with col2_1:
    Tlim_ro_max=st.time_input("Máxima hora de relevo",step=600)
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
    df_tramos = form_tramos(
        df=st.session_state.df_lista_ro,
        tmin=Tlim_min_tramo,
        tmax=Tlim_max_tramo,
        lista_estaciones=st.session_state.estaciones
    )
    df_tramos['lista_id_viaje']=df_tramos.apply(generar_lista_ids,axis=1)
    df_tramos_2,df_excl_tramo=sel_tramo_incl_Talm(
        df=df_tramos,
        Talm_min=Tlim_alm_min,



        Talm_max=Tlim_alm_max
    )
    st.session_state.df_excl_alm=df_excl_tramo
    st.session_state.df_tramos=df_tramos_2
    csv_tramos=st.session_state.df_tramos.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Descargar base de tramos de trabajo",
        csv_tramos,
        'Tramos_trabajo.csv',
        'text/csv',
        key='download-csv-tramos'
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
max_hora_partido=st.time_input("Hora fin límite para turno partido", value=datetime.strptime("22:30", "%H:%M").time(),step=300)

#Traslado de conductor entre estaciones

st.write("Definir traslados válidos entre estaciones (relevos)")
col1_2,col2_2,col3_2,col4_2=st.columns(4)
with col1_2:
    est1_tras = st.text_input("Est. inicio traslado ej: NARL")

with col2_2:
    est2_tras = st.text_input("Est. fin traslado ej: RCAS")

with col3_2:
    min_tras = st.number_input("Min. de traslado", min_value=1, max_value=180, value=25)

with col4_2:
    modo_tras = st.selectbox("Tipo de traslado", ["adelantar_2", "extender_1"])

# Botón para agregar traslado en relevos al diccionario
if st.button("Agregar traslado de relevo"):
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

st.write("Definir traslados válidos entre estaciones (inicio de jornada)")
col1_2,col2_2,col3_2=st.columns(3)
with col1_2:
    est1_tras_ini = st.text_input("Est. inicio traslado para el inicio de jornada ej: NARL")

with col2_2:
    est2_tras_ini = st.text_input("Est. fin traslado para el inicio de jornada ej: RCAS")

with col3_2:
    min_tras_ini = st.number_input("Min. de traslado hacia la estación inicial", min_value=1, max_value=180, value=25)

if st.button("Agregar traslado (inicio jornada)"):
    if est1_tras_ini and est2_tras_ini:  # evitar claves vacías
        clave = (est1_tras_ini, est2_tras_ini)

        # Guardar en session_state
        st.session_state.traslados_validos_ini[clave] = {
            "tiempo": timedelta(minutes=min_tras_ini),
        }
        st.success(f"Traslado {clave} agregado.")
    else:
        st.error("Debes completar ambas estaciones.")

if st.session_state.traslados_validos_ini:
    st.write("Traslados de inicio de jornada registrados:")
    registros_ini = [
        {
            "est_ini_1": k[0],
            "est_ini_2": k[1],
            "minutos": int(v["tiempo"].total_seconds() // 60)
        }
        for k, v in st.session_state.traslados_validos_ini.items()
    ]
    st.dataframe(pd.DataFrame(registros_ini))

if st.button("Generar jornadas"):
    st.session_state.df_jornada_regular=jornadas_regular_eq_est(st.session_state.df_tramos,tmin_jornada,tmax_jornada,tmin_alm,tmax_alm)
    csv_jornadas_regular=st.session_state.df_jornada_regular.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Descargar base de jornadas de trabajo regulares",
        csv_jornadas_regular,
        'Jornadas_regular.csv',
        'text/csv',
        key='download-csv-REGULAR'
    )
    st.session_state.df_jornada_partida=jornadas_partido_eq_est(st.session_state.df_tramos,tmin_part_jornada,tmax_part_jornada,max_hora_partido)
    csv_jornadas_partida=st.session_state.df_jornada_partida.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Descargar base de jornadas de trabajo partida",
        csv_jornadas_partida,
        'Jornadas_partidas.csv',
        'text/csv',
        key='download-csv-PARTIDO'
    )

    df_jornada_despl=jornadas_regular_diff_est(
        df_combinaciones=st.session_state.df_tramos,
        traslados_validos=st.session_state.traslados_validos,
        ESPERA_MIN=tmin_alm,
        ESPERA_MAX=tmax_alm,
        DUR_MIN=tmin_jornada,
        DUR_MAX=tmax_jornada)
    csv_jornadas_despl=df_jornada_despl.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Descargar base de jornadas de trabajo regular con desplazamiento",
        csv_jornadas_despl,
        'Jornadas_despl.csv',
        'text/csv',
        key='download-csv-TRASLADO'
    )
    #st.dataframe(st.session_state.df_jornada_despl.head(20))

    st.session_state.df_jornada_despl= df_jornada_despl.drop(['tipo_ajuste','traslado'],axis=1)
    df_consolidado_1=pd.concat([st.session_state.df_jornada_regular,st.session_state.df_jornada_partida,st.session_state.df_jornada_despl],ignore_index=True)
    df_consolidado_1_copy=df_consolidado_1.copy()
    df_consolidado_1['origen']='base'
    df_total=correct_ini(
        df=df_consolidado_1_copy,
        traslados_validos_ini=st.session_state.traslados_validos_ini
    )
    df_total['origen']='ini_corregido'
    df_consolidado_2=pd.concat([df_consolidado_1,df_total],ignore_index=True)
    df_consolidado_2["lista_id_viaje_key"] = df_consolidado_2["lista_id_viaje"].apply(tuple)
    df_consolidado_2["prioridad"] = df_consolidado_2["origen"].map({
    "ini_corregido": 1,
    "base": 0
    })
    df_consolidado_2 = df_consolidado_2.sort_values(
    by=["lista_id_viaje_key", "prioridad", "duracion_total"],
    ascending=[True, False, False]
    )

    df_final = df_consolidado_2.drop_duplicates(
        subset="lista_id_viaje_key",
        keep="first"
    )
    df_final=df_final.drop(["lista_id_viaje_key", "prioridad"],axis=1)
    df_final_2=df_final[(df_final['dur_tramo_1']<=Tlim_max_tramo)&(df_final['dur_tramo_2']<=Tlim_max_tramo)&
            (
        ((df_final['tipo_turno'] == 'Partido') & (df_final['duracion_total'] <= tmax_part_jornada)) |
        ((df_final['tipo_turno'] != 'Partido') & (df_final['duracion_total'] <= tmax_jornada))
    )]
    
    st.session_state.df_jornada_total=df_final_2

    csv_jornadas_total=st.session_state.df_jornada_total.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Descargar base total de jornadas",
        csv_jornadas_total,
        'Jornadas_totales.csv',
        'text/csv',
        key='download-csv-total'
    )

    st.dataframe(st.session_state.df_jornada_total.head(50))


if st.button("Optimizar jornadas (Set Covering)"):

    resultado = set_covering4schedule(
        df_id_viajes=st.session_state.lista_ids_viaje,
        df_jornadas=st.session_state.df_jornada_total,
        solver_msg=False
    )

    st.write(f"Estado del modelo: **{resultado['status']}**")

    if resultado["viajes_sin_cubrir"]:
        st.warning(
            f"Viajes sin cobertura previa: {len(resultado['viajes_sin_cubrir'])}"
        )
        st.dataframe(resultado['viajes_sin_cubrir'])
        
    if resultado["status"] == "Optimal":
        st.success(
            f"Jornadas seleccionadas: {resultado['n_jornadas_seleccionadas']}"
        )

        st.session_state.df_solucion = resultado["df_solucion"]

        csv_sol = resultado["df_solucion"].to_csv(index=False).encode("utf-8")
        st.download_button(
            "Descargar solución óptima",
            csv_sol,
            "solucion_jornadas_scp.csv",
            "text/csv",
            key="download-scp-set_cover_sol"
        )

        st.dataframe(resultado["df_solucion"].head(50))







