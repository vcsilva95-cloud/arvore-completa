# -*- coding: utf-8 -*-
import copy
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from modelo import PARAMETROS_PADRAO, resolver_pl_unico

st.set_page_config(page_title="PL Unico - Arvore Completa",page_icon="⚡",layout="wide")
st.markdown("""<style>
:root{color-scheme:light!important}html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stHeader"]{background:#fff!important;color:#000!important}
[data-testid="stSidebar"],[data-testid="stSidebarContent"]{background:#f4f7fb!important;color:#000!important}.stApp *{color:#000}
input,textarea,[data-baseweb="input"],[data-baseweb="input"]>div,[data-baseweb="select"],[data-baseweb="select"]>div,[role="listbox"],[role="option"]{background:#fff!important;color:#000!important;-webkit-text-fill-color:#000!important}
[data-testid="stNumberInput"] div,[data-testid="stNumberInput"] input,[data-testid="stNumberInput"] button{background:#fff!important;color:#000!important;-webkit-text-fill-color:#000!important}
[data-testid="stNumberInput"] button svg,[data-testid="stNumberInput"] button path{fill:#000!important;stroke:#000!important}
.stButton>button,[data-testid="stFormSubmitButton"] button,[data-testid="stDownloadButton"] button{background:#fff!important;color:#000!important;border:1px solid #64748b!important;font-weight:700!important}
[data-testid="stMetric"],button[role="tab"],[data-testid="stDataFrame"]{background:#fff!important;color:#000!important}
[data-testid="stMetric"]{border:1px solid #d7dee8;border-radius:10px;padding:12px}button[role="tab"][aria-selected="true"]{background:#dbeafe!important}
.block-container{max-width:1500px;padding-top:1.4rem}
</style>""",unsafe_allow_html=True)

def br(v,c=2):return f"{float(v):,.{c}f}".replace(",","X").replace(".",",").replace("X",".")
def layout(fig,titulo,y=None,h=540):
    fig.update_layout(title=dict(text=titulo,x=.5),paper_bgcolor="#fff",plot_bgcolor="#fff",font=dict(color="#000"),height=h,
      xaxis=dict(gridcolor="#e5e7eb"),yaxis=dict(title=y,gridcolor="#e5e7eb"),legend=dict(orientation="h",y=1.12,x=0,bgcolor="#fff"),margin=dict(l=60,r=30,t=110,b=55))
    return fig

def arvore(p):
    a,pr=p["Afluencias"],p["Probabilidades"]
    p2o,p2p=pr["M2-O"],pr["M2-P"]
    probs={"M1":1,"M2-O":p2o,"M2-P":p2p,"M3-OO":p2o*pr["M3-O|M2-O"],"M3-OP":p2o*pr["M3-P|M2-O"],"M3-PO":p2p*pr["M3-O|M2-P"],"M3-PP":p2p*pr["M3-P|M2-P"]}
    pos={"M1":(0,0),"M2-O":(1,1.25),"M2-P":(1,-1.25),"M3-OO":(2,1.9),"M3-OP":(2,.62),"M3-PO":(2,-.62),"M3-PP":(2,-1.9)}
    pais={"M2-O":"M1","M2-P":"M1","M3-OO":"M2-O","M3-OP":"M2-O","M3-PO":"M2-P","M3-PP":"M2-P"}
    af={"M1":a["M1"],"M2-O":a["M2-O"],"M2-P":a["M2-P"],"M3-OO":a["M3-O"],"M3-OP":a["M3-P"],"M3-PO":a["M3-O"],"M3-PP":a["M3-P"]}
    fig=go.Figure()
    for f,pa in pais.items():
        fig.add_scatter(x=[pos[pa][0],pos[f][0]],y=[pos[pa][1],pos[f][1]],mode="lines",line=dict(color="#64748b",width=2),hoverinfo="skip",showlegend=False)
    for n,(x,y) in pos.items():
        cen="Conhecido" if n=="M1" else ("Otimista" if n.endswith("O") else "Pessimista")
        cor="#2563eb" if n=="M1" else ("#16a34a" if cen=="Otimista" else "#dc2626")
        txt=f"<b>{n.split('-')[0]}</b><br>{cen}<br>AFL {br(af[n])}<br>p={probs[n]:.1%}"
        fig.add_scatter(x=[x],y=[y],mode="markers+text",text=[txt],textposition="middle center",marker=dict(symbol="square",size=105,color="#fff",line=dict(color=cor,width=3)),textfont=dict(size=12,color="#000"),hovertemplate=txt+"<extra></extra>",showlegend=False)
    fig.update_layout(paper_bgcolor="#fff",plot_bgcolor="#fff",height=650,xaxis=dict(visible=False,range=[-.35,2.35]),yaxis=dict(visible=False,range=[-2.55,2.55]),margin=dict(l=30,r=30,t=20,b=20))
    return fig

with st.sidebar:
    st.header("Parametros do PL Unico")
    with st.form("form_entrada_pl", clear_on_submit=False):
        vi=st.number_input("Volume inicial de Chavantes",5754.,8795.,8000.,10.,format="%.2f")
        carga_pct=st.slider("Carga do sistema (%)",50,150,100,5)
        st.subheader("Afluencias")
        a1=st.number_input("M1 conhecida",0.,value=2156.11,step=10.,format="%.2f")
        a2o=st.number_input("M2 otimista",0.,value=1838.59,step=10.,format="%.2f")
        a2p=st.number_input("M2 pessimista",0.,value=713.66,step=10.,format="%.2f")
        a3o=st.number_input("M3 otimista",0.,value=1674.,step=10.,format="%.2f")
        a3p=st.number_input("M3 pessimista",0.,value=656.21,step=10.,format="%.2f")
        st.subheader("Probabilidades condicionais")
        p2o=st.slider("M2 otimista (%)",0,100,50,1)
        p3o_o=st.slider("M3 otimista dado M2 otimista (%)",0,100,50,1)
        p3o_p=st.slider("M3 otimista dado M2 pessimista (%)",0,100,50,1)
        executar=st.form_submit_button("Executar PL Unico", use_container_width=True)

p=copy.deepcopy(PARAMETROS_PADRAO);p["UHE"]["VI"]=vi;p["Carga"]={e:v*carga_pct/100 for e,v in p["Carga"].items()}
p["Afluencias"]={"M1":a1,"M2-O":a2o,"M2-P":a2p,"M3-O":a3o,"M3-P":a3p}
p["Probabilidades"]={"M2-O":p2o/100,"M2-P":1-p2o/100,"M3-O|M2-O":p3o_o/100,"M3-P|M2-O":1-p3o_o/100,"M3-O|M2-P":p3o_p/100,"M3-P|M2-P":1-p3o_p/100}

if "pl_resultado" not in st.session_state:
    st.session_state["pl_resultado"] = resolver_pl_unico(p)
    st.session_state["pl_parametros_usados"] = copy.deepcopy(p)

if executar:
    with st.spinner("Resolvendo um unico PL com todos os nos da arvore..."):
        novo_resultado = resolver_pl_unico(p)
    st.session_state["pl_resultado"] = novo_resultado
    st.session_state["pl_parametros_usados"] = copy.deepcopy(p)

r = st.session_state["pl_resultado"]
pu = st.session_state["pl_parametros_usados"]
dfn=pd.DataFrame(r["ResultadosNos"]);dfe=pd.DataFrame(r["ResumoEsperado"])
st.title("PL Unico Estocastico - Arvore Completa")
st.caption("Uma unica chamada ao SCIP contempla simultaneamente os 7 nos da arvore.")
st.code(f"Ultima execucao: M2 O={pu['Probabilidades']['M2-O']:.0%}; M3 O|M2O={pu['Probabilidades']['M3-O|M2-O']:.0%}; M3 O|M2P={pu['Probabilidades']['M3-O|M2-P']:.0%}")
c1,c2,c3,c4=st.columns(4);c1.metric("Custo esperado",f"R$ {br(r['CustoEsperado'])}");c2.metric("Afluencia esperada M2",br(dfe.loc[1,"Afluencia"]));c3.metric("Afluencia esperada M3",br(dfe.loc[2,"Afluencia"]));c4.metric("Deficit esperado",f"{br(dfe.Deficit.sum())} MW")

t1,t2,t3,t4,t5=st.tabs(["Arvore de cenarios","Resumo esperado","Decisoes por no","Reservatorio","Resultados"])
with t1: st.plotly_chart(arvore(pu),use_container_width=True,theme=None)
with t2:
    fig=go.Figure();fig.add_bar(x=dfe.Estagio,y=dfe.GeracaoHidraulica,name="UHE Chavantes",marker_color="#6baed6");fig.add_bar(x=dfe.Estagio,y=dfe.Termobahia,name="UTE Termobahia",marker_color="#ef6a6a");fig.add_bar(x=dfe.Estagio,y=dfe.PecemII,name="UTE Pecem II",marker_color="#f5a04a");fig.add_scatter(x=dfe.Estagio,y=dfe.Carga,name="Carga",mode="lines+markers",line=dict(color="#000",width=3));fig.update_layout(barmode="stack");st.plotly_chart(layout(fig,"Despacho esperado do PL Unico","Potencia (MW)"),use_container_width=True,theme=None)
with t3:
    fig=go.Figure();fig.add_bar(x=dfn.No,y=dfn.GeracaoHidraulica,name="UHE Chavantes",marker_color="#6baed6");fig.add_bar(x=dfn.No,y=dfn.Termobahia,name="UTE Termobahia",marker_color="#ef6a6a");fig.add_bar(x=dfn.No,y=dfn.PecemII,name="UTE Pecem II",marker_color="#f5a04a");fig.update_layout(barmode="stack");st.plotly_chart(layout(fig,"Decisoes internas do unico PL em cada no","Potencia (MW)"),use_container_width=True,theme=None)
with t4:
    fig=go.Figure();
    for nome,nos in {"O-O":["M1","M2-O","M3-OO"],"O-P":["M1","M2-O","M3-OP"],"P-O":["M1","M2-P","M3-PO"],"P-P":["M1","M2-P","M3-PP"]}.items():
        d=dfn.set_index("No").loc[nos];fig.add_scatter(x=["M1","M2","M3"],y=d.VolumeFinal,mode="lines+markers",name=nome)
    st.plotly_chart(layout(fig,"Trajetorias de volume final","Volume (hm3)"),use_container_width=True,theme=None)
with t5:
    st.dataframe(dfn,use_container_width=True,hide_index=True);st.download_button("Baixar CSV",dfn.to_csv(index=False).encode("utf-8-sig"),"resultado_arvore_completa.csv","text/csv",use_container_width=True)
