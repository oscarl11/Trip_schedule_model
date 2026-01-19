import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from itertools import combinations
import pulp
import ast

def set_covering4schedule(
        df_id_viajes: pd.DataFrame,
        df_jornadas: pd.DataFrame,
        solver_msg: bool = False):
    """
    Resuelve un problema de Set Covering para selección mínima de jornadas.

    Parámetros
    ----------
    df_jornadas : DataFrame
        Debe contener columna 'lista_id_viaje' (list[int] o string convertible)
    df_id_viajes : DataFrame
        Debe contener columna 'id_viaje'
    solver_msg : bool
        Mostrar salida del solver CBC

    Retorna
    -------
    dict con:
        - status: str
        - df_solucion: DataFrame o None
        - viajes_sin_cubrir: list
        - n_jornadas_seleccionadas: int
    """

    df = df_jornadas.copy()

    # -------------------------------------------------------
    # 1. Normalizar lista_id_viaje
    # -------------------------------------------------------
    df["lista_id_viaje"] = df["lista_id_viaje"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    # Universo de viajes
    U = set(df_id_viajes["id_viaje"].unique())
    J = df.index.tolist()

    # -------------------------------------------------------
    # 2. Modelo
    # -------------------------------------------------------
    model = pulp.LpProblem("SetCovering_Jornadas", pulp.LpMinimize)

    x = pulp.LpVariable.dicts("x", J, cat="Binary")

    # Objetivo
    model += pulp.lpSum(x[j] for j in J)

    # -------------------------------------------------------
    # 3. Restricciones
    # -------------------------------------------------------
    viajes_sin_cobertura_previa = []

    for v in U:
        jornadas_que_cubren = [j for j in J if v in df.loc[j, "lista_id_viaje"]]

        if not jornadas_que_cubren:
            viajes_sin_cobertura_previa.append(v)
            continue

        model += pulp.lpSum(x[j] for j in jornadas_que_cubren) == 1

    # -------------------------------------------------------
    # 4. Resolver
    # -------------------------------------------------------
    solver = pulp.PULP_CBC_CMD(msg=solver_msg)
    model.solve(solver)

    status = pulp.LpStatus[model.status]

    # -------------------------------------------------------
    # 5. Resultados
    # -------------------------------------------------------
    if status == "Optimal":
        seleccionadas = [j for j in J if x[j].value() == 1]

        df_sol = df.loc[seleccionadas].copy()
        df_sol.reset_index(drop=True, inplace=True)

        return {
            "status": status,
            "df_solucion": df_sol,
            "viajes_sin_cubrir": viajes_sin_cobertura_previa,
            "n_jornadas_seleccionadas": len(seleccionadas)
        }

    else:
        viajes_sin_cubrir = []
        for v in U:
            if sum(
                x[j].value() for j in J
                if v in df.loc[j, "lista_id_viaje"] and x[j].value() is not None
            ) == 0:
                viajes_sin_cubrir.append(v)

        return {
            "status": status,
            "df_solucion": None,
            "viajes_sin_cubrir": viajes_sin_cubrir,
            "n_jornadas_seleccionadas": 0
        }