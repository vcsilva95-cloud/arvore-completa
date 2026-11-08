# -*- coding: utf-8 -*-
"""UM único PL com uma decisão por estágio e probabilidades editáveis."""
from pyscipopt import Model, quicksum

PARAMETROS_PADRAO = {
    "UHE": {"Vmin": 5754.0, "Vmax": 8795.0, "VI": 8000.0,
            "Prod": 0.235, "Engol": 1628.0, "CustoVert": 0.01},
    "UTE": {
        "Termobahia": {"Capac": 186.0, "Custo": 424080.0},
        "PecemII": {"Capac": 144.0, "Custo": 1764000.0},
    },
    "Carga": {1: 530.0, 2: 508.0, 3: 516.0},
    "CDef": 5969520.0,
    "Afluencias": {"M1": 2156.11, "M2-O": 1838.59, "M2-P": 713.66,
                    "M3-O": 1674.00, "M3-P": 656.21},
    "Probabilidades": {"M2-O": 0.50, "M2-P": 0.50,
                       "M3-O": 0.50, "M3-P": 0.50},
}


def resolver_pl_unico(p):
    uhe, utes = p["UHE"], p["UTE"]
    carga, cdef = p["Carga"], p["CDef"]
    a, pr = p["Afluencias"], p["Probabilidades"]

    # As probabilidades entram numericamente no ÚNICO PL.
    afl = {
        1: a["M1"],
        2: pr["M2-O"] * a["M2-O"] + pr["M2-P"] * a["M2-P"],
        3: pr["M3-O"] * a["M3-O"] + pr["M3-P"] * a["M3-P"],
    }

    m = Model("PL_UNICO_TRES_ESTAGIOS")
    m.hideOutput()
    vf, vt, vv, de, gt = {}, {}, {}, {}, {}

    for e in (1, 2, 3):
        vf[e] = m.addVar(f"vf_M{e}", lb=uhe["Vmin"], ub=uhe["Vmax"])
        vt[e] = m.addVar(f"vt_M{e}", lb=0.0, ub=uhe["Engol"])
        vv[e] = m.addVar(f"vv_M{e}", lb=0.0)
        de[e] = m.addVar(f"def_M{e}", lb=0.0)
        for t, d in utes.items():
            gt[t, e] = m.addVar(f"gt_{t}_M{e}", lb=0.0, ub=d["Capac"])

    custo = {}
    for e in (1, 2, 3):
        custo[e] = (quicksum(utes[t]["Custo"] * gt[t, e] for t in utes)
                    + cdef * de[e] + uhe["CustoVert"] * vv[e])

    # A escrita ponderada é mantida explicitamente na FO.
    # Em M2/M3, como há uma só decisão por estágio, pO*C + pP*C = C.
    objetivo = (
        custo[1]
        + pr["M2-O"] * custo[2] + pr["M2-P"] * custo[2]
        + pr["M3-O"] * custo[3] + pr["M3-P"] * custo[3]
    )
    m.setObjective(objetivo, "minimize")

    for e in (1, 2, 3):
        entrada = uhe["VI"] if e == 1 else vf[e-1]
        m.addCons(vf[e] + vt[e] + vv[e] == entrada + afl[e], name=f"BH_M{e}")
        m.addCons(uhe["Prod"] * vt[e] + quicksum(gt[t, e] for t in utes)
                  + de[e] == carga[e], name=f"AD_M{e}")

    m.optimize()
    if str(m.getStatus()).lower() != "optimal":
        raise RuntimeError(f"Status do SCIP: {m.getStatus()}")

    linhas = []
    for e in (1, 2, 3):
        vte = m.getVal(vt[e])
        linhas.append({
            "Estagio": f"M{e}", "AfluenciaPonderada": afl[e],
            "VolumeFinal": m.getVal(vf[e]), "VolumeTurbinado": vte,
            "VolumeVertido": m.getVal(vv[e]),
            "GeracaoHidraulica": uhe["Prod"] * vte,
            "Termobahia": m.getVal(gt["Termobahia", e]),
            "PecemII": m.getVal(gt["PecemII", e]),
            "Deficit": m.getVal(de[e]), "Carga": carga[e],
        })

    return {"CustoTotal": m.getObjVal(), "Resultados": linhas,
            "AfluenciasPonderadas": afl, "ProbabilidadesUsadas": pr.copy()}
