# -*- coding: utf-8 -*-
"""Equivalente deterministico de arvore completa resolvido em UM UNICO PL."""
from dataclasses import dataclass
from typing import Optional
from pyscipopt import Model, quicksum

PARAMETROS_PADRAO = {
    "UHE": {"Nome":"UHE Chavantes", "Vmin":5754.0, "Vmax":8795.0,
            "VI":8000.0, "Prod":0.235, "Engol":1628.0, "CustoVert":0.01},
    "UTE": {
        "Termobahia":{"Capac":186.0, "Custo":424080.0},
        "PecemII":{"Capac":144.0, "Custo":1764000.0},
    },
    "Carga": {1:530.0, 2:508.0, 3:516.0},
    "CDef":5969520.0,
    "Afluencias":{"M1":2156.11, "M2-O":1838.59, "M2-P":713.66,
                   "M3-O":1674.00, "M3-P":656.21},
    "Probabilidades":{"M2-O":0.50, "M2-P":0.50,
                       "M3-O|M2-O":0.50, "M3-P|M2-O":0.50,
                       "M3-O|M2-P":0.50, "M3-P|M2-P":0.50},
}

@dataclass(frozen=True)
class No:
    nome: str
    estagio: int
    pai: Optional[str]
    afluencia: float
    probabilidade: float
    cenario: str


def construir_nos(p):
    a, pr = p["Afluencias"], p["Probabilidades"]
    p2o, p2p = pr["M2-O"], pr["M2-P"]
    return {
        "M1": No("M1",1,None,a["M1"],1.0,"Conhecido"),
        "M2-O": No("M2-O",2,"M1",a["M2-O"],p2o,"Otimista"),
        "M2-P": No("M2-P",2,"M1",a["M2-P"],p2p,"Pessimista"),
        "M3-OO": No("M3-OO",3,"M2-O",a["M3-O"],p2o*pr["M3-O|M2-O"],"Otimista"),
        "M3-OP": No("M3-OP",3,"M2-O",a["M3-P"],p2o*pr["M3-P|M2-O"],"Pessimista"),
        "M3-PO": No("M3-PO",3,"M2-P",a["M3-O"],p2p*pr["M3-O|M2-P"],"Otimista"),
        "M3-PP": No("M3-PP",3,"M2-P",a["M3-P"],p2p*pr["M3-P|M2-P"],"Pessimista"),
    }


def resolver_pl_unico(parametros):
    uhe, utes = parametros["UHE"], parametros["UTE"]
    carga, cdef = parametros["Carga"], parametros["CDef"]
    nos = construir_nos(parametros)
    m = Model("PL_unico_arvore_completa")
    m.hideOutput()
    vf, vt, vv, deficit, gt = {}, {}, {}, {}, {}

    for n in nos:
        vf[n] = m.addVar(f"vf_{n}", lb=uhe["Vmin"], ub=uhe["Vmax"])
        vt[n] = m.addVar(f"vt_{n}", lb=0.0, ub=uhe["Engol"])
        vv[n] = m.addVar(f"vv_{n}", lb=0.0)
        deficit[n] = m.addVar(f"def_{n}", lb=0.0)
        for t,d in utes.items():
            gt[t,n] = m.addVar(f"gt_{t}_{n}", lb=0.0, ub=d["Capac"])

    custo_nodal = {}
    for n,no in nos.items():
        custo_nodal[n] = (quicksum(utes[t]["Custo"]*gt[t,n] for t in utes)
                          + cdef*deficit[n] + uhe["CustoVert"]*vv[n])
    m.setObjective(quicksum(no.probabilidade*custo_nodal[n] for n,no in nos.items()), "minimize")

    for n,no in nos.items():
        entrada = uhe["VI"] if no.pai is None else vf[no.pai]
        m.addCons(vf[n] + vt[n] + vv[n] == entrada + no.afluencia,
                  name=f"balanco_{n}")
        m.addCons(uhe["Prod"]*vt[n] + quicksum(gt[t,n] for t in utes)
                  + deficit[n] == carga[no.estagio], name=f"carga_{n}")

    m.optimize()
    if str(m.getStatus()).lower() != "optimal":
        raise RuntimeError(f"SCIP nao encontrou solucao otima: {m.getStatus()}")

    ordem=["M1","M2-O","M2-P","M3-OO","M3-OP","M3-PO","M3-PP"]
    res=[]
    for n in ordem:
        no=nos[n]; vtn=m.getVal(vt[n])
        cn=sum(utes[t]["Custo"]*m.getVal(gt[t,n]) for t in utes)+cdef*m.getVal(deficit[n])+uhe["CustoVert"]*m.getVal(vv[n])
        res.append({"No":n,"Estagio":no.estagio,"Pai":no.pai or "-","Cenario":no.cenario,
            "Probabilidade":no.probabilidade,"Afluencia":no.afluencia,
            "VolumeFinal":m.getVal(vf[n]),"VolumeTurbinado":vtn,"VolumeVertido":m.getVal(vv[n]),
            "GeracaoHidraulica":uhe["Prod"]*vtn,"Termobahia":m.getVal(gt["Termobahia",n]),
            "PecemII":m.getVal(gt["PecemII",n]),"Deficit":m.getVal(deficit[n]),
            "Carga":carga[no.estagio],"CustoNodal":cn,"CustoPonderado":no.probabilidade*cn})

    # Resumo esperado por estagio: soma ponderada dos nos do mesmo estagio.
    resumo=[]
    for e in (1,2,3):
        re=[x for x in res if x["Estagio"]==e]
        resumo.append({"Estagio":f"M{e}", **{
            k:sum(x["Probabilidade"]*x[k] for x in re)
            for k in ["Afluencia","VolumeFinal","VolumeTurbinado","VolumeVertido",
                      "GeracaoHidraulica","Termobahia","PecemII","Deficit","Carga"]}})
    return {"CustoEsperado":m.getObjVal(),"ResultadosNos":res,"ResumoEsperado":resumo}
