# -*- coding: utf-8 -*-
import copy
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from modelo import PARAMETROS_PADRAO, resolver_pl_unico

st.set_page_config(page_title="PL Único", page_icon="⚡", layout="wide")
st.markdown("""<style>
:root{color-scheme:light!important}html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stHeader"]{background:#fff!important;color:#000!important}
[data-testid="stSidebar"],[data-testid="stSidebarContent"]{background:#f4f7fb!important;color:#000!important}.stApp *{color:#000}
input,textarea,[data-baseweb="input"],[data-baseweb="input"]>div,[data-baseweb="select"],[data-baseweb="select"]>div{background:#fff!important;color:#000!important;-webkit-text-fill-color:#000!important}
[data-testid="stNumberInput"] div,[data-testid="stNumberInput"] input,[data-testid="stNumberInput"] button{background:#fff!important;color:#000!important;-webkit-text-fill-color:#000!important}
[data-testid="stNumberInput"] button svg,[data-testid="stNumberInput"] button path{fill:#000!important;stroke:#000!important}
.stButton>button,[data-testid="stFormSubmitButton"] button,[data-testid="stDownloadButton"] button{background:#fff!important;color:#000!important;border:1px solid #64748b!important;font-weight:700!important}
[data-testid="stMetric"],button[role="tab"],[data-testid="stDataFrame"],[data-testid="stCode"]{background:#fff!important;color:#000!important}
[data-testid="stMetric"]{border:1px solid #d7dee8;border-radius:10px;padding:12px}button[role="tab"][aria-selected="true"]{background:#dbeafe!important}
.block-container{max-width:1500px;padding-top:1.4rem}
</style>""", unsafe_allow_html=True)

def br(v,c=2): return f"{float(v):,.{c}f}".replace(",","X").replace(".",",").replace("X",".")
def tema(fig,titulo,y=None,h=530):
    fig.update_layout(title=dict(text=titulo,x=.5),paper_bgcolor="#fff",plot_bgcolor="#fff",font=dict(color="#000"),height=h,
      xaxis=dict(gridcolor="#e5e7eb"),yaxis=dict(title=y,gridcolor="#e5e7eb",rangemode="tozero"),legend=dict(orientation="h",y=1.12,x=0,bgcolor="#fff"),margin=dict(l=60,r=30,t=110,b=55))
    return fig

def grafico_arvore(a,pr):
    pos={"M1":(0,0),"M2-O":(1,1.05),"M2-P":(1,-1.05),"M3-OO":(2,1.65),"M3-OP":(2,.55),"M3-PO":(2,-.55),"M3-PP":(2,-1.65)}
    pais={"M2-O":"M1","M2-P":"M1","M3-OO":"M2-O","M3-OP":"M2-O","M3-PO":"M2-P","M3-PP":"M2-P"}
    probs={"M1":1,"M2-O":pr["M2-O"],"M2-P":pr["M2-P"],"M3-OO":pr["M2-O"]*pr["M3-O"],"M3-OP":pr["M2-O"]*pr["M3-P"],"M3-PO":pr["M2-P"]*pr["M3-O"],"M3-PP":pr["M2-P"]*pr["M3-P"]}
    af={"M1":a["M1"],"M2-O":a["M2-O"],"M2-P":a["M2-P"],"M3-OO":a["M3-O"],"M3-OP":a["M3-P"],"M3-PO":a["M3-O"],"M3-PP":a["M3-P"]}
    fig=go.Figure()
    for f,pai in pais.items(): fig.add_scatter(x=[pos[pai][0],pos[f][0]],y=[pos[pai][1],pos[f][1]],mode="lines",line=dict(color="#64748b",width=2),showlegend=False,hoverinfo="skip")
    for n,(x,y) in pos.items():
        cen="Conhecido" if n=="M1" else ("Otimista" if n.endswith("O") else "Pessimista")
        cor="#2563eb" if n=="M1" else ("#16a34a" if cen=="Otimista" else "#dc2626")
        txt=f"<b>{n.split('-')[0]}</b><br>{cen}<br>AFL {br(af[n])}<br>p={probs[n]:.1%}"
        fig.add_scatter(x=[x],y=[y],mode="markers+text",text=[txt],textposition="middle center",marker=dict(symbol="square",size=100,color="#fff",line=dict(color=cor,width=3)),textfont=dict(size=11,color="#000"),showlegend=False,hovertemplate=txt+"<extra></extra>")
    fig.update_layout(paper_bgcolor="#fff",plot_bgcolor="#fff",height=620,xaxis=dict(visible=False,range=[-.3,2.3]),yaxis=dict(visible=False,range=[-2.2,2.2]),margin=dict(l=20,r=20,t=20,b=20))
    return fig

with st.sidebar:
    st.header("Entradas do PL Único")
    with st.form("form_pl_unico", clear_on_submit=False):
        vi=st.number_input("Volume inicial",5754.,8795.,8000.,10.,format="%.2f")
        carga_pct=st.slider("Carga do sistema (%)",50,150,100,5)
        st.subheader("Afluências")
        a1=st.number_input("M1 conhecida",0.,value=2156.11,step=10.,format="%.2f")
        a2o=st.number_input("M2 otimista",0.,value=1838.59,step=10.,format="%.2f")
        a2p=st.number_input("M2 pessimista",0.,value=713.66,step=10.,format="%.2f")
        a3o=st.number_input("M3 otimista",0.,value=1674.,step=10.,format="%.2f")
        a3p=st.number_input("M3 pessimista",0.,value=656.21,step=10.,format="%.2f")
        st.subheader("Probabilidades")
        p2o=st.slider("M2 otimista (%)",0,100,50,1)
        st.caption(f"M2 pessimista: {100-p2o}%")
        p3o=st.slider("M3 otimista (%)",0,100,50,1)
        st.caption(f"M3 pessimista: {100-p3o}%")
        executar=st.form_submit_button("Executar PL Único",use_container_width=True)

p=copy.deepcopy(PARAMETROS_PADRAO)
p["UHE"]["VI"]=float(vi);p["Carga"]={e:v*carga_pct/100 for e,v in p["Carga"].items()}
p["Afluencias"]={"M1":a1,"M2-O":a2o,"M2-P":a2p,"M3-O":a3o,"M3-P":a3p}
p["Probabilidades"]={"M2-O":p2o/100,"M2-P":1-p2o/100,"M3-O":p3o/100,"M3-P":1-p3o/100}

# O formulario envia TODOS os valores somente no clique.
# Nao guardamos resultado antigo: o clique sempre chama o solver usando os valores submetidos.
if executar:
    with st.spinner("Executando novamente o PL Único..."):
        r = resolver_pl_unico(p)
    st.session_state["ultimo_resultado_exibido"] = r
    st.session_state["ultimas_entradas_exibidas"] = copy.deepcopy(p)
    st.session_state["numero_execucoes"] = st.session_state.get("numero_execucoes", 0) + 1
else:
    if "ultimo_resultado_exibido" not in st.session_state:
        r = resolver_pl_unico(p)
        st.session_state["ultimo_resultado_exibido"] = r
        st.session_state["ultimas_entradas_exibidas"] = copy.deepcopy(p)
        st.session_state["numero_execucoes"] = 1
    else:
        r = st.session_state["ultimo_resultado_exibido"]

pu = st.session_state["ultimas_entradas_exibidas"]
df = pd.DataFrame(r["Resultados"])
st.title("PL Único Árvore Completa")
st.success(f"Execução nº {st.session_state['numero_execucoes']} concluída. Probabilidades usadas: M2 O={r['ProbabilidadesUsadas']['M2-O']:.0%}, M2 P={r['ProbabilidadesUsadas']['M2-P']:.0%}, M3 O={r['ProbabilidadesUsadas']['M3-O']:.0%}, M3 P={r['ProbabilidadesUsadas']['M3-P']:.0%}.")
c1,c2,c3,c4=st.columns(4);c1.metric("Custo total",f"R$ {br(r['CustoTotal'])}");c2.metric("Afluência ponderada M2",br(r["AfluenciasPonderadas"][2]));c3.metric("Afluência ponderada M3",br(r["AfluenciasPonderadas"][3]));c4.metric("Déficit",f"{br(df.Deficit.sum())} MW")

t1,t2,t3,t4=st.tabs(["Árvore de cenários","Resultado do PL Único","Reservatório único","Tabela"])
with t1:
    st.plotly_chart(grafico_arvore(pu["Afluencias"],pu["Probabilidades"]),use_container_width=True,theme=None)
    st.caption("A árvore representa apenas as entradas que formam as afluências ponderadas. A solução exibida possui uma decisão por estágio.")
with t2:
    fig=go.Figure();fig.add_bar(x=df.Estagio,y=df.GeracaoHidraulica,name="UHE Chavantes",marker_color="#6baed6");fig.add_bar(x=df.Estagio,y=df.Termobahia,name="UTE Termobahia",marker_color="#ef6a6a");fig.add_bar(x=df.Estagio,y=df.PecemII,name="UTE Pecém II",marker_color="#f5a04a");fig.add_scatter(x=df.Estagio,y=df.Carga,mode="lines+markers",name="Carga",line=dict(color="#000",width=3));fig.update_layout(barmode="stack");st.plotly_chart(tema(fig,"Único despacho ótimo: M1, M2 e M3","Potência (MW)"),use_container_width=True,theme=None)
with t3:
    fig=go.Figure(go.Scatter(x=df.Estagio,y=df.VolumeFinal,mode="lines+markers+text",text=[br(v) for v in df.VolumeFinal],textposition="top center",line=dict(color="#2563eb",width=3),name="Volume final"));st.plotly_chart(tema(fig,"Um único volume final por estágio","Volume (hm³)"),use_container_width=True,theme=None)
with t4:
    st.dataframe(df,use_container_width=True,hide_index=True);st.download_button("Baixar CSV",df.to_csv(index=False).encode("utf-8-sig"),"resultado_pl_unico.csv","text/csv",use_container_width=True)
