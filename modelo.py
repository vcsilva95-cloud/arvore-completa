# -*- coding: utf-8 -*-
"""PL unico estocastico em arvore completa com 3 estagios."""
from dataclasses import dataclass
from typing import Dict, Optional
from pyscipopt import Model, quicksum

@dataclass(frozen=True)
class No:
    nome: str
    estagio: int
    probabilidade: float
    afluencia: float
    pai: Optional[str]
    cenario: str

def resolver_pl_arvore(parametros: dict):
    uhe = parametros["UHE"]
    utes = parametros["UTE"]
    carga = parametros["Carga"]
    cdef = parametros["CDef"]
    afl = parametros["Afluencias"]

    nos: Dict[str, No] = {
        "M1": No("M1", 1, 1.00, afl["M1"], None, "Conhecido"),
        "M2-O": No("M2-O", 2, 0.50, afl["M2-O"], "M1", "Otimista"),
        "M2-P": No("M2-P", 2, 0.50, afl["M2-P"], "M1", "Pessimista"),
        "M3-OO": No("M3-OO", 3, 0.25, afl["M3-O"], "M2-O", "Otimista"),
        "M3-OP": No("M3-OP", 3, 0.25, afl["M3-P"], "M2-O", "Pessimista"),
        "M3-PO": No("M3-PO", 3, 0.25, afl["M3-O"], "M2-P", "Otimista"),
        "M3-PP": No("M3-PP", 3, 0.25, afl["M3-P"], "M2-P", "Pessimista"),
    }

    m = Model("PL_unico_arvore_completa")
    m.hideOutput()
    vf, vt, vv, deficit, gt = {}, {}, {}, {}, {}

    for n in nos:
        vf[n] = m.addVar(f"vf_{n}", lb=uhe["Vmin"], ub=uhe["Vmax"])
        vt[n] = m.addVar(f"vt_{n}", lb=0, ub=uhe["Engol"])
        vv[n] = m.addVar(f"vv_{n}", lb=0)
        deficit[n] = m.addVar(f"def_{n}", lb=0)
        for t, dados in utes.items():
            gt[t, n] = m.addVar(f"gt_{t}_{n}", lb=0, ub=dados["Capac"])

    m.setObjective(quicksum(
        nos[n].probabilidade * (
            quicksum(utes[t]["Custo"] * gt[t, n] for t in utes)
            + cdef * deficit[n] + uhe["CustoVert"] * vv[n]
        ) for n in nos
    ), "minimize")

    for n, no in nos.items():
        entrada = uhe["VI"] if no.pai is None else vf[no.pai]
        m.addCons(vf[n] + vt[n] + vv[n] == entrada + no.afluencia)
        m.addCons(uhe["Prod"] * vt[n] + quicksum(gt[t, n] for t in utes)
                  + deficit[n] == carga[no.estagio])

    m.optimize()
    if str(m.getStatus()).lower() != "optimal":
        raise RuntimeError(f"SCIP nao encontrou solucao otima: {m.getStatus()}")

    resultado = []
    ordem = ["M1", "M2-O", "M2-P", "M3-OO", "M3-OP", "M3-PO", "M3-PP"]
    for n in ordem:
        no = nos[n]
        vt_n = m.getVal(vt[n])
        custo_n = (sum(utes[t]["Custo"] * m.getVal(gt[t, n]) for t in utes)
                   + cdef * m.getVal(deficit[n]) + uhe["CustoVert"] * m.getVal(vv[n]))
        resultado.append({
            "No": n, "Estagio": no.estagio, "Pai": no.pai or "-",
            "Cenario": no.cenario, "Probabilidade": no.probabilidade,
            "Afluencia": no.afluencia, "VolumeFinal": m.getVal(vf[n]),
            "VolumeTurbinado": vt_n, "VolumeVertido": m.getVal(vv[n]),
            "GeracaoHidraulica": uhe["Prod"] * vt_n,
            "Termobahia": m.getVal(gt["Termobahia", n]),
            "PecemII": m.getVal(gt["PecemII", n]),
            "Deficit": m.getVal(deficit[n]), "CustoNodal": custo_n,
            "CustoPonderado": no.probabilidade * custo_n,
        })
    return {"CustoEsperado": m.getObjVal(), "Resultados": resultado}

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
}
