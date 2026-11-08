# -*- coding: utf-8 -*-
import copy
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from modelo import PARAMETROS_PADRAO, resolver_pl_arvore

st.set_page_config(page_title="PL Estocastico - Arvore Completa", page_icon="⚡", layout="wide")

st.markdown("""
<style>
:root { color-scheme: light !important; }
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stHeader"] { background: #ffffff !important; color: #111111 !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
  background: #f4f7fb !important; border-right: 1px solid #d7dee8 !important;
}
.stApp *, [data-testid="stSidebar"] * { color: #111111; }
input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"] > div,
[data-testid="stNumberInput"] input { background: #ffffff !important; color: #111111 !important;
  -webkit-text-fill-color: #111111 !important; }
.stButton > button, [data-testid="baseButton-primary"], [data-testid="baseButton-secondary"] {
  background: #ffffff !important; color: #111111 !important; border: 1px solid #64748b !important;
  font-weight: 700 !important; border-radius: 8px !important;
}
.stButton > button:hover { background: #eaf2ff !important; border-color: #2563eb !important; }
[data-testid="stMetric"] { background: #ffffff !important; border: 1px solid #d7dee8;
  border-radius: 10px; padding: 12px; }
div[data-baseweb="tab-list"] { background: #f4f7fb !important; padding: 7px; border-radius: 10px; }
button[role="tab"] { background: #ffffff !important; color: #111111 !important; border-radius: 7px; }
button[role="tab"][aria-selected="true"] { background: #dbeafe !important; }
[data-testid="stDataFrame"], [data-testid="stTable"] { background: #ffffff !important; }
.block-container { max-width: 1500px; padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

CORES = {"M1":"#2563eb", "Otimista":"#16a34a", "Pessimista":"#dc2626"}

def formato_br(v, casas=2):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def tema_claro(fig, titulo, eixo_y=None, altura=500):
    fig.update_layout(title=dict(text=titulo, x=0.01), paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff", font=dict(color="#111111"), height=altura,
        hovermode="x unified", margin=dict(l=60, r=35, t=75, b=60),
        legend=dict(bgcolor="#ffffff", bordercolor="#cbd5e1", borderwidth=1),
        xaxis=dict(gridcolor="#e5e7eb", zerolinecolor="#cbd5e1", title="No da arvore"),
        yaxis=dict(gridcolor="#e5e7eb", zerolinecolor="#cbd5e1", title=eixo_y))
    return fig

def diagrama_arvore(afl):
    pos = {"M1":(0, 0), "M2-O":(1, 1.15), "M2-P":(1, -1.15),
           "M3-OO":(2, 1.75), "M3-OP":(2, 0.55), "M3-PO":(2, -0.55), "M3-PP":(2, -1.75)}
    pais = {"M2-O":"M1", "M2-P":"M1", "M3-OO":"M2-O", "M3-OP":"M2-O",
            "M3-PO":"M2-P", "M3-PP":"M2-P"}
    textos = {"M1":f"<b>M1</b><br>AFL conhecida<br>{formato_br(afl['M1'])}",
      "M2-O":f"<b>M2</b><br>Otimista<br>AFL {formato_br(afl['M2-O'])}",
      "M2-P":f"<b>M2</b><br>Pessimista<br>AFL {formato_br(afl['M2-P'])}",
      "M3-OO":f"<b>M3</b><br>Otimista<br>AFL {formato_br(afl['M3-O'])}",
      "M3-OP":f"<b>M3</b><br>Pessimista<br>AFL {formato_br(afl['M3-P'])}",
      "M3-PO":f"<b>M3</b><br>Otimista<br>AFL {formato_br(afl['M3-O'])}",
      "M3-PP":f"<b>M3</b><br>Pessimista<br>AFL {formato_br(afl['M3-P'])}"}
    fig = go.Figure()
    for filho, pai in pais.items():
        x0,y0=pos[pai]; x1,y1=pos[filho]
        fig.add_trace(go.Scatter(x=[x0,x1], y=[y0,y1], mode="lines",
            line=dict(color="#64748b", width=2), hoverinfo="skip", showlegend=False))
    for no,(x,y) in pos.items():
        cor = CORES["M1"] if no == "M1" else (CORES["Otimista"] if no.endswith("O") else CORES["Pessimista"])
        fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers+text", text=[textos[no]],
            textposition="middle center", marker=dict(symbol="square", size=92, color="#ffffff",
            line=dict(color=cor, width=3)), textfont=dict(color="#111111", size=12),
            hovertemplate=textos[no]+"<extra></extra>", showlegend=False))
    fig.add_annotation(x=0,y=2.35,text="Estagio 1<br>p = 100%",showarrow=False,font=dict(size=14,color="#111111"))
    fig.add_annotation(x=1,y=2.35,text="Estagio 2<br>p = 50% por no",showarrow=False,font=dict(size=14,color="#111111"))
    fig.add_annotation(x=2,y=2.35,text="Estagio 3<br>p = 25% por no",showarrow=False,font=dict(size=14,color="#111111"))
    fig.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", height=620,
        margin=dict(l=40,r=40,t=35,b=25), xaxis=dict(visible=False,range=[-0.35,2.35]),
        yaxis=dict(visible=False,range=[-2.35,2.65]), font=dict(color="#111111"))
    return fig

with st.sidebar:
    st.header("Parametros do modelo")
    st.caption("Altere os dados e execute novamente.")
    carga_pct = st.slider("Carga do sistema (%)", 50, 150, 100, 5)
    vi = st.number_input("Volume inicial de Chavantes", 5754.0, 8795.0, 8000.0, 10.0)
    with st.expander("Afluencias", expanded=True):
        a1 = st.number_input("M1, conhecida", 0.0, value=2156.11, step=10.0)
        a2o = st.number_input("M2, otimista", 0.0, value=1838.59, step=10.0)
        a2p = st.number_input("M2, pessimista", 0.0, value=713.66, step=10.0)
        a3o = st.number_input("M3, otimista", 0.0, value=1674.00, step=10.0)
        a3p = st.number_input("M3, pessimista", 0.0, value=656.21, step=10.0)
    executar = st.button("Executar otimizacao", type="primary", use_container_width=True)

st.title("PL Unico Estocastico com Arvore Completa")
st.caption("UHE Chavantes, UTE Termobahia e UTE Pecem II | Tres estagios")

p = copy.deepcopy(PARAMETROS_PADRAO)
p["UHE"]["VI"] = vi
p["Carga"] = {t: v*carga_pct/100 for t,v in p["Carga"].items()}
p["Afluencias"] = {"M1":a1, "M2-O":a2o, "M2-P":a2p, "M3-O":a3o, "M3-P":a3p}

if executar or "resultado" not in st.session_state:
    try:
        with st.spinner("Resolvendo o PL estocastico no SCIP..."):
            st.session_state["resultado"] = resolver_pl_arvore(p)
            st.session_state["parametros"] = p
    except Exception as e:
        st.error(f"Falha na otimizacao: {e}")
        st.stop()

r = st.session_state["resultado"]
p_usado = st.session_state["parametros"]
df = pd.DataFrame(r["Resultados"])

c1,c2,c3,c4 = st.columns(4)
c1.metric("Custo esperado", f"R$ {formato_br(r['CustoEsperado'])}")
c2.metric("Geracao hidraulica media", f"{formato_br((df.Probabilidade*df.GeracaoHidraulica).sum()/3)} MW")
c3.metric("Geracao termica esperada", f"{formato_br((df.Probabilidade*(df.Termobahia+df.PecemII)).sum())} MW-estagio")
c4.metric("Deficit esperado", f"{formato_br((df.Probabilidade*df.Deficit).sum())} MW-estagio")

aba_arvore, aba_gh, aba_gt, aba_res, aba_tab = st.tabs([
    "Arvore de cenarios", "Geracao hidraulica", "Geracao termeletrica", "Reservatorio", "Resultados numericos"])

with aba_arvore:
    st.plotly_chart(diagrama_arvore(p_usado["Afluencias"]), use_container_width=True, theme=None)
    st.info("As probabilidades exibidas sao incondicionais: 100% em M1, 50% em cada no de M2 e 25% em cada no de M3.")

with aba_gh:
    fig = go.Figure(go.Bar(x=df.No, y=df.GeracaoHidraulica, marker_color="#2563eb",
                           text=df.GeracaoHidraulica.round(2), textposition="outside", name="Chavantes"))
    st.plotly_chart(tema_claro(fig,"Geracao hidraulica por no","Geracao (MW)"),use_container_width=True,theme=None)

with aba_gt:
    fig = go.Figure()
    fig.add_bar(x=df.No,y=df.Termobahia,name="UTE Termobahia",marker_color="#f59e0b")
    fig.add_bar(x=df.No,y=df.PecemII,name="UTE Pecem II",marker_color="#dc2626")
    fig.update_layout(barmode="stack")
    st.plotly_chart(tema_claro(fig,"Geracao termeletrica por no","Geracao (MW)"),use_container_width=True,theme=None)

with aba_res:
    fig = go.Figure()
    for caminho, nos in {"O-O":["M1","M2-O","M3-OO"], "O-P":["M1","M2-O","M3-OP"],
                          "P-O":["M1","M2-P","M3-PO"], "P-P":["M1","M2-P","M3-PP"]}.items():
        d = df.set_index("No").loc[nos]
        fig.add_scatter(x=[1,2,3],y=d.VolumeFinal,mode="lines+markers",name=caminho)
    fig.update_xaxes(tickmode="array",tickvals=[1,2,3],ticktext=["M1","M2","M3"])
    st.plotly_chart(tema_claro(fig,"Trajetorias do volume final de Chavantes","Volume final",520),use_container_width=True,theme=None)

with aba_tab:
    mostrar = df.rename(columns={"No":"No", "Estagio":"Estagio", "Cenario":"Cenario",
        "Probabilidade":"Probabilidade", "Afluencia":"Afluencia", "VolumeFinal":"Volume final",
        "VolumeTurbinado":"Volume turbinado", "VolumeVertido":"Vertimento",
        "GeracaoHidraulica":"Geracao hidraulica", "Termobahia":"UTE Termobahia",
        "PecemII":"UTE Pecem II", "Deficit":"Deficit", "CustoPonderado":"Custo ponderado"})
    st.dataframe(mostrar, use_container_width=True, hide_index=True)
    st.download_button("Baixar resultados em CSV", mostrar.to_csv(index=False).encode("utf-8-sig"),
                       "resultados_arvore_completa.csv", "text/csv", use_container_width=True)
