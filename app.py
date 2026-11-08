# -*- coding: utf-8 -*-
import copy
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from modelo import PARAMETROS_PADRAO, resolver_pl_unico

st.set_page_config(page_title="PL Unico - 3 Estagios", page_icon="⚡", layout="wide")

# Tema claro nativo + CSS de reforco para TODOS os widgets.
st.markdown(r"""
<style>
:root { color-scheme: light !important; }
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"],
[data-testid="stSidebarContent"] { background-color: #FFFFFF !important; color: #000000 !important; }
[data-testid="stSidebar"] { background-color: #F4F7FB !important; border-right: 1px solid #CBD5E1 !important; }
.stApp *, [data-testid="stSidebar"] * { color: #000000; }

/* Number input: caixa + botoes - e + */
[data-testid="stNumberInput"] > div,
[data-testid="stNumberInput"] div,
[data-testid="stNumberInput"] input,
[data-testid="stNumberInput"] button {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
[data-testid="stNumberInput"] button {
    border-color: #94A3B8 !important;
}
[data-testid="stNumberInput"] button svg,
[data-testid="stNumberInput"] button svg path {
    fill: #000000 !important;
    color: #000000 !important;
    stroke: #000000 !important;
}

/* Demais inputs e seletores */
input, textarea,
[data-baseweb="input"], [data-baseweb="input"] > div,
[data-baseweb="select"], [data-baseweb="select"] > div,
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [role="option"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}

/* Botoes */
.stButton > button,
[data-testid="baseButton-primary"], [data-testid="baseButton-secondary"],
[data-testid="stDownloadButton"] button {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    border: 1px solid #64748B !important;
    font-weight: 700 !important;
}
.stButton > button:hover, [data-testid="stDownloadButton"] button:hover {
    background-color: #EAF2FF !important;
    color: #000000 !important;
    border-color: #2563EB !important;
}

/* Sliders */
[data-testid="stSlider"] * { color: #000000 !important; }
[data-baseweb="slider"] div { color: #000000 !important; }

/* Abas, metricas, tabelas, expansores e mensagens */
[data-testid="stMetric"], [data-testid="stDataFrame"], [data-testid="stTable"],
[data-testid="stExpander"], div[data-baseweb="tab-list"], button[role="tab"] {
    background-color: #FFFFFF !important; color: #000000 !important;
}
[data-testid="stMetric"] { border: 1px solid #D7DEE8; border-radius: 10px; padding: 12px; }
button[role="tab"][aria-selected="true"] { background-color: #DBEAFE !important; }

/* Alertas: sempre claros */
[data-testid="stAlert"] { background-color: #F8FAFC !important; color: #000000 !important; border: 1px solid #CBD5E1 !important; }
[data-testid="stAlert"] * { color: #000000 !important; }

.block-container { max-width: 1500px; padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

def br(v, casas=2):
    return f"{float(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def tema(fig, titulo, eixo_y, barmode=None):
    fig.update_layout(
        title=dict(text=titulo, x=0.5), paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(color="#000000"), height=540, hovermode="x unified",
        xaxis=dict(title="Estagio", gridcolor="#E5E7EB", color="#000000"),
        yaxis=dict(title=eixo_y, gridcolor="#E5E7EB", color="#000000", rangemode="tozero"),
        legend=dict(orientation="h", y=1.12, x=0, bgcolor="#FFFFFF", font=dict(color="#000000")),
        margin=dict(l=60, r=30, t=110, b=60),
    )
    if barmode:
        fig.update_layout(barmode=barmode)
    return fig

with st.sidebar:
    st.header("Parametros do PL Unico")
    with st.form("form_parametros", clear_on_submit=False):
        vi = st.number_input("Volume inicial de Chavantes", 5754.0, 8795.0, 8000.0, 10.0, format="%.2f")
        carga_pct = st.slider("Carga do sistema (%)", 50, 150, 100, 5)
        st.subheader("Afluencias")
        a1 = st.number_input("M1 conhecida", 0.0, value=2156.11, step=10.0, format="%.2f")
        a2o = st.number_input("M2 otimista", 0.0, value=1838.59, step=10.0, format="%.2f")
        a2p = st.number_input("M2 pessimista", 0.0, value=713.66, step=10.0, format="%.2f")
        a3o = st.number_input("M3 otimista", 0.0, value=1674.00, step=10.0, format="%.2f")
        a3p = st.number_input("M3 pessimista", 0.0, value=656.21, step=10.0, format="%.2f")
        st.subheader("Probabilidades")
        p2o_pct = st.slider("M2: cenario otimista (%)", 0, 100, 50, 1)
        st.caption(f"M2 pessimista: {100-p2o_pct}%")
        p3o_pct = st.slider("M3: cenario otimista (%)", 0, 100, 50, 1)
        st.caption(f"M3 pessimista: {100-p3o_pct}%")
        executar = st.form_submit_button("Executar PL Unico", use_container_width=True)

p_atual = copy.deepcopy(PARAMETROS_PADRAO)
p_atual["UHE"]["VI"] = float(vi)
p_atual["Carga"] = {e: float(v) * carga_pct / 100.0 for e, v in p_atual["Carga"].items()}
p_atual["Afluencias"] = {"M1": float(a1), "M2-O": float(a2o), "M2-P": float(a2p), "M3-O": float(a3o), "M3-P": float(a3p)}
p_atual["Probabilidades"] = {
    "M2-O": p2o_pct / 100.0, "M2-P": (100-p2o_pct) / 100.0,
    "M3-O": p3o_pct / 100.0, "M3-P": (100-p3o_pct) / 100.0,
}

st.title("PL Unico com Afluencias Esperadas")
st.caption("Uma decisao e um volume final por estagio: M1, M2 e M3")

if "resultado_pl_unico" not in st.session_state:
    st.session_state["parametros_pl_unico"] = copy.deepcopy(p_atual)
    st.session_state["resultado_pl_unico"] = resolver_pl_unico(p_atual)

if executar:
    try:
        with st.spinner("Resolvendo o PL Unico com os novos parametros..."):
            resultado_novo = resolver_pl_unico(p_atual)
        st.session_state["parametros_pl_unico"] = copy.deepcopy(p_atual)
        st.session_state["resultado_pl_unico"] = resultado_novo
    except Exception as exc:
        st.error(f"Erro ao resolver o PL: {exc}")
        st.stop()

r = st.session_state["resultado_pl_unico"]
p_usado = st.session_state["parametros_pl_unico"]
if "CustoTotal" not in r or "Resultados" not in r:
    st.error("O app.py e o modelo.py estao em versoes diferentes. Substitua os dois arquivos e reinicie o app.")
    st.stop()

st.caption("Parametros efetivamente usados na ultima otimizacao:")
st.code(
    f"M2: {p_usado['Probabilidades']['M2-O']:.0%} otimista / {p_usado['Probabilidades']['M2-P']:.0%} pessimista | "
    f"M3: {p_usado['Probabilidades']['M3-O']:.0%} otimista / {p_usado['Probabilidades']['M3-P']:.0%} pessimista"
)

df = pd.DataFrame(r["Resultados"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Custo total", f"R$ {br(r['CustoTotal'])}")
c2.metric("Afluencia esperada M2", br(r["AfluenciasEsperadas"][2]))
c3.metric("Afluencia esperada M3", br(r["AfluenciasEsperadas"][3]))
c4.metric("Deficit total", f"{br(df['Deficit'].sum())} MW")

aba1, aba2, aba3, aba4 = st.tabs(["Resumo do despacho", "Reservatorio", "Probabilidades", "Resultados"])

with aba1:
    fig = go.Figure()
    fig.add_bar(x=df["Estagio"], y=df["GeracaoHidraulica"], name="UHE Chavantes", marker_color="#6BAED6")
    fig.add_bar(x=df["Estagio"], y=df["Termobahia"], name="UTE Termobahia", marker_color="#EF6A6A")
    fig.add_bar(x=df["Estagio"], y=df["PecemII"], name="UTE Pecem II", marker_color="#F5A04A")
    if (df["Deficit"] > 1e-6).any():
        fig.add_bar(x=df["Estagio"], y=df["Deficit"], name="Deficit", marker_color="#7C3AED")
    fig.add_scatter(x=df["Estagio"], y=df["Carga"], mode="lines+markers", name="Carga",
                    line=dict(color="#000000", width=3), marker=dict(size=8, color="#000000"))
    st.plotly_chart(tema(fig, "Despacho otimo e carga - resultado do PL Unico", "Potencia (MW)", "stack"),
                    use_container_width=True, theme=None)
    st.write(f"**Resultado do PL Unico: custo total = R$ {br(r['CustoTotal'])}**")

with aba2:
    fig = go.Figure()
    fig.add_scatter(x=df["Estagio"], y=df["VolumeFinal"], mode="lines+markers+text",
                    text=[br(v) for v in df["VolumeFinal"]], textposition="top center",
                    name="Volume final", line=dict(color="#2563EB", width=3))
    st.plotly_chart(tema(fig, "Volume final unico por estagio", "Volume", None),
                    use_container_width=True, theme=None)

with aba3:
    st.latex(r"AFL^{esp}_2=p_{2,O}AFL_{2,O}+p_{2,P}AFL_{2,P}")
    st.latex(r"AFL^{esp}_3=p_{3,O}AFL_{3,O}+p_{3,P}AFL_{3,P}")
    st.write(f"M2: {p_usado['Probabilidades']['M2-O']:.0%} otimista e {p_usado['Probabilidades']['M2-P']:.0%} pessimista.")
    st.write(f"M3: {p_usado['Probabilidades']['M3-O']:.0%} otimista e {p_usado['Probabilidades']['M3-P']:.0%} pessimista.")

with aba4:
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Baixar resultados em CSV", df.to_csv(index=False).encode("utf-8-sig"),
                       "resultado_pl_unico.csv", "text/csv", use_container_width=True)
