# -*- coding: utf-8 -*-
"""PL unico de 3 estagios com decisoes unicas e afluencias esperadas."""
from pyscipopt import Model, quicksum

PARAMETROS_PADRAO = {
    "UHE": {"Nome": "UHE Chavantes", "Vmin": 5754.0, "Vmax": 8795.0,
            "VI": 8000.0, "Prod": 0.235, "Engol": 1628.0, "CustoVert": 0.01},
    "UTE": {
        "Termobahia": {"Capac": 186.0, "Custo": 424080.0},
        "PecemII": {"Capac": 144.0, "Custo": 1764000.0},
    },
    "Carga": {1: 530.0, 2: 508.0, 3: 516.0},
    "CDef": 5969520.0,
    "Afluencias": {"M1": 2156.11, "M2-O": 1838.59, "M2-P": 713.66,
                    "M3-O": 1674.00, "M3-P": 656.21},
    "Probabilidades": {"M2-O": 0.50, "M2-P": 0.50, "M3-O": 0.50, "M3-P": 0.50},
}

def resolver_pl_unico(parametros: dict):
    uhe = parametros["UHE"]
    utes = parametros["UTE"]
    carga = parametros["Carga"]
    cdef = parametros["CDef"]
    afl = parametros["Afluencias"]
    prob = parametros["Probabilidades"]

    # Uma única afluência de entrada por estágio, calculada pela esperança.
    afl_esperada = {
        1: afl["M1"],
        2: prob["M2-O"] * afl["M2-O"] + prob["M2-P"] * afl["M2-P"],
        3: prob["M3-O"] * afl["M3-O"] + prob["M3-P"] * afl["M3-P"],
    }

    m = Model("PL_unico_tres_estagios")
    m.hideOutput()
    vf, vt, vv, deficit, gt = {}, {}, {}, {}, {}

    for e in (1, 2, 3):
        vf[e] = m.addVar(f"vf_M{e}", lb=uhe["Vmin"], ub=uhe["Vmax"])
        vt[e] = m.addVar(f"vt_M{e}", lb=0.0, ub=uhe["Engol"])
        vv[e] = m.addVar(f"vv_M{e}", lb=0.0)
        deficit[e] = m.addVar(f"def_M{e}", lb=0.0)
        for t, dados in utes.items():
            gt[t, e] = m.addVar(f"gt_{t}_M{e}", lb=0.0, ub=dados["Capac"])

    # Como há uma decisão única em cada estágio, os custos dos cenários repetidos
    # têm a mesma variável. As probabilidades de cada estágio somam 1 e a FO
    # reduz-se à soma dos três custos operativos esperados.
    m.setObjective(quicksum(
        quicksum(utes[t]["Custo"] * gt[t, e] for t in utes)
        + cdef * deficit[e] + uhe["CustoVert"] * vv[e]
        for e in (1, 2, 3)
    ), "minimize")

    for e in (1, 2, 3):
        entrada = uhe["VI"] if e == 1 else vf[e - 1]
        m.addCons(vf[e] + vt[e] + vv[e] == entrada + afl_esperada[e],
                  name=f"balanco_hidrico_M{e}")
        m.addCons(uhe["Prod"] * vt[e] + quicksum(gt[t, e] for t in utes)
                  + deficit[e] == carga[e], name=f"atendimento_M{e}")

    m.optimize()
    if str(m.getStatus()).lower() != "optimal":
        raise RuntimeError(f"SCIP não encontrou solução ótima: {m.getStatus()}")

    resultados = []
    for e in (1, 2, 3):
        vt_e = m.getVal(vt[e])
        custo = (sum(utes[t]["Custo"] * m.getVal(gt[t, e]) for t in utes)
                 + cdef * m.getVal(deficit[e]) + uhe["CustoVert"] * m.getVal(vv[e]))
        resultados.append({
            "Estagio": f"M{e}", "AfluenciaEsperada": afl_esperada[e],
            "VolumeFinal": m.getVal(vf[e]), "VolumeTurbinado": vt_e,
            "VolumeVertido": m.getVal(vv[e]),
            "GeracaoHidraulica": uhe["Prod"] * vt_e,
            "Termobahia": m.getVal(gt["Termobahia", e]),
            "PecemII": m.getVal(gt["PecemII", e]),
            "Deficit": m.getVal(deficit[e]), "Carga": carga[e], "Custo": custo,
        })
    return {"CustoTotal": m.getObjVal(), "Resultados": resultados,
            "AfluenciasEsperadas": afl_esperada}
