# -*- coding: utf-8 -*-
import copy
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from modelo import PARAMETROS_PADRAO, resolver_pl_unico

st.set_page_config(page_title="PL Único - 3 Estágios", page_icon="⚡", layout="wide")
st.markdown("""
<style>
:root {color-scheme: light !important;}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {background:#fff!important;color:#111!important;}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {background:#f4f7fb!important;}
.stApp *, [data-testid="stSidebar"] * {color:#111;}
input, [data-baseweb="select"] > div, [data-baseweb="input"] > div {background:#fff!important;color:#111!important;-webkit-text-fill-color:#111!important;}
.stButton>button {background:#fff!important;color:#111!important;border:1px solid #64748b!important;font-weight:700!important;}
[data-testid="stMetric"] {background:#fff!important;border:1px solid #d7dee8;border-radius:10px;padding:12px;}
.block-container {max-width:1500px;padding-top:1.5rem;}
</style>
""", unsafe_allow_html=True)

def br(v, casas=2):
    return f"{v:,.{casas}f}".replace(",","X").replace(".",",").replace("X",".")

def tema(fig, titulo, y):
    fig.update_layout(title=dict(text=titulo,x=.5), paper_bgcolor="#fff", plot_bgcolor="#fff",
        font=dict(color="#111"), height=540, barmode="stack", hovermode="x unified",
        xaxis=dict(title="Estágio",gridcolor="#e5e7eb"),
        yaxis=dict(title=y,gridcolor="#e5e7eb",rangemode="tozero"),
        legend=dict(orientation="h",y=1.12,x=0), margin=dict(l=60,r=30,t=110,b=60))
    return fig

with st.sidebar:
    st.header("Parâmetros do PL Único")
    vi = st.number_input("Volume inicial de Chavantes",5754.0,8795.0,8000.0,10.0)
    carga_pct = st.slider("Carga do sistema (%)",50,150,100,5)
    st.subheader("Afluências")
    a1=st.number_input("M1 conhecida",0.0,value=2156.11,step=10.0)
    a2o=st.number_input("M2 otimista",0.0,value=1838.59,step=10.0)
    a2p=st.number_input("M2 pessimista",0.0,value=713.66,step=10.0)
    a3o=st.number_input("M3 otimista",0.0,value=1674.00,step=10.0)
    a3p=st.number_input("M3 pessimista",0.0,value=656.21,step=10.0)
    st.subheader("Probabilidades")
    p2o_pct=st.slider("M2: cenário otimista (%)",0,100,50,1)
    st.caption(f"M2 pessimista: {100-p2o_pct}%")
    p3o_pct=st.slider("M3: cenário otimista (%)",0,100,50,1)
    st.caption(f"M3 pessimista: {100-p3o_pct}%")
    executar=st.button("Executar PL Único",type="primary",use_container_width=True)

p=copy.deepcopy(PARAMETROS_PADRAO)
p["UHE"]["VI"]=vi
p["Carga"]={e:v*carga_pct/100 for e,v in p["Carga"].items()}
p["Afluencias"]={"M1":a1,"M2-O":a2o,"M2-P":a2p,"M3-O":a3o,"M3-P":a3p}
p["Probabilidades"]={"M2-O":p2o_pct/100,"M2-P":1-p2o_pct/100,
                     "M3-O":p3o_pct/100,"M3-P":1-p3o_pct/100}

st.title("PL Único com Afluências Esperadas")
st.caption("Uma decisão e um volume final por estágio: M1, M2 e M3")

if executar or "resultado" not in st.session_state:
    try:
        with st.spinner("Resolvendo um único PL no SCIP..."):
            st.session_state.resultado=resolver_pl_unico(p)
            st.session_state.parametros=p
    except Exception as exc:
        st.error(str(exc)); st.stop()

r=st.session_state.resultado
p_usado=st.session_state.parametros
df=pd.DataFrame(r["Resultados"])

c1,c2,c3,c4=st.columns(4)
c1.metric("Custo total",f"R$ {br(r['CustoTotal'])}")
c2.metric("Afluência esperada M2",br(r["AfluenciasEsperadas"][2]))
c3.metric("Afluência esperada M3",br(r["AfluenciasEsperadas"][3]))
c4.metric("Déficit total",f"{br(df.Deficit.sum())} MW")

aba1,aba2,aba3,aba4=st.tabs(["Resumo do despacho","Reservatório","Probabilidades","Resultados"])
with aba1:
    fig=go.Figure()
    fig.add_bar(x=df.Estagio,y=df.GeracaoHidraulica,name="UHE Chavantes",marker_color="#6baed6")
    fig.add_bar(x=df.Estagio,y=df.Termobahia,name="UTE Termobahia",marker_color="#ef6a6a")
    fig.add_bar(x=df.Estagio,y=df.PecemII,name="UTE Pecém II",marker_color="#f5a04a")
    if (df.Deficit>1e-6).any(): fig.add_bar(x=df.Estagio,y=df.Deficit,name="Déficit",marker_color="#7c3aed")
    fig.add_scatter(x=df.Estagio,y=df.Carga,mode="lines+markers",name="Carga",
                    line=dict(color="#111",width=3),marker=dict(size=8,color="#111"))
    st.plotly_chart(tema(fig,"Despacho ótimo e carga - resultado do PL Único","Potência (MW)"),use_container_width=True,theme=None)
    st.success(f"Resultado do PL Único: custo total = R$ {br(r['CustoTotal'])}")
with aba2:
    fig=go.Figure()
    fig.add_scatter(x=df.Estagio,y=df.VolumeFinal,mode="lines+markers+text",name="Volume final",
                    text=[br(v) for v in df.VolumeFinal],textposition="top center",line=dict(color="#2563eb",width=3))
    st.plotly_chart(tema(fig,"Volume final único por estágio","Volume (hm³)"),use_container_width=True,theme=None)
with aba3:
    st.latex(r"AFL^{esp}_2=p_{2,O}AFL_{2,O}+(1-p_{2,O})AFL_{2,P}")
    st.latex(r"AFL^{esp}_3=p_{3,O}AFL_{3,O}+(1-p_{3,O})AFL_{3,P}")
    st.write(f"M2: {p_usado['Probabilidades']['M2-O']:.0%} otimista e {p_usado['Probabilidades']['M2-P']:.0%} pessimista.")
    st.write(f"M3: {p_usado['Probabilidades']['M3-O']:.0%} otimista e {p_usado['Probabilidades']['M3-P']:.0%} pessimista.")
    st.warning("Com uma única decisão por estágio, ponderar na função objetivo custos idênticos de cenários faz as probabilidades somarem 1. Por isso, as probabilidades alteram efetivamente o PL por meio das afluências esperadas nos balanços hídricos.")
with aba4:
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button("Baixar resultados em CSV",df.to_csv(index=False).encode("utf-8-sig"),"resultado_pl_unico.csv","text/csv",use_container_width=True)
