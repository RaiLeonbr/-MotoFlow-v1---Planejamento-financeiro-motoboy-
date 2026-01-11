# ===============================
# IMPORTAÇÕES
# ===============================
import os
import streamlit as st
import pandas as pd
from datetime import date

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(
    page_title="MotoFlow",
    page_icon="🏍️",
    layout="wide"
)

st.markdown("""
<style>
.stApp { background-color: #0b0f14; }
[data-testid="metric-container"] {
    background-color: #111827;
    border-radius: 14px;
    padding: 18px;
    border-left: 6px solid #22c55e;
}
h1, h2, h3, h4 { color: #e5e7eb; }
section[data-testid="stSidebar"] { background-color: #020617; }
</style>
""", unsafe_allow_html=True)

st.title("🏍️ MotoFlow")
st.caption("Planejamento financeiro inteligente para motoboy")

# ===============================
# UTILIDADES
# ===============================
def garantir_pasta(caminho):
    pasta = os.path.dirname(caminho)
    if pasta and not os.path.exists(pasta):
        os.makedirs(pasta)

def carregar_csv(caminho, colunas):
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    return pd.DataFrame(columns=colunas)

# ===============================
# ARQUIVOS
# ===============================
CAMINHO_DESPESAS = "data/despesas.csv"
CAMINHO_REGISTROS = "data/registros.csv"

# ===============================
# CARREGAR DADOS
# ===============================
despesas_df = carregar_csv(
    CAMINHO_DESPESAS,
    ["Data", "Despesa", "Valor"]
)

registros_df = carregar_csv(
    CAMINHO_REGISTROS,
    [
        "Data", "Corridas",
        "Ganho Calculado",
        "Ganho Real",
        "Meta Diária",
        "Aproveitamento (%)",
        "Status"
    ]
)

# ===============================
# SIDEBAR – CONFIGURAÇÕES
# ===============================
st.sidebar.header("⚙️ Configurações")

valor_corrida = st.sidebar.number_input(
    "Valor médio por corrida (R$)",
    min_value=1.0,
    max_value=50.0,
    value=7.0
)

dias_trabalho = st.sidebar.number_input(
    "Dias trabalhados no mês",
    min_value=1,
    max_value=31,
    value=30
)

# ===============================
# SIDEBAR – DESPESAS
# ===============================
st.sidebar.subheader("💸 Adicionar Despesa")

with st.sidebar.form("form_despesa"):
    data_despesa = st.date_input("Data", value=date.today())
    nome_despesa = st.text_input("Nome da despesa")
    valor_despesa = st.number_input("Valor (R$)", 0.0, 10000.0)
    salvar_despesa = st.form_submit_button("Salvar")

if salvar_despesa and nome_despesa:
    garantir_pasta(CAMINHO_DESPESAS)

    nova = pd.DataFrame([{
        "Data": data_despesa,
        "Despesa": nome_despesa,
        "Valor": valor_despesa
    }])

    despesas_df = pd.concat([despesas_df, nova], ignore_index=True)
    despesas_df.to_csv(CAMINHO_DESPESAS, index=False)
    st.success("Despesa salva 💾")
    st.rerun()

# ===============================
# CÁLCULOS
# ===============================
despesas_totais = despesas_df["Valor"].sum() if not despesas_df.empty else 0
corridas_mes = despesas_totais / valor_corrida if valor_corrida > 0 else 0
corridas_dia_meta = corridas_mes / dias_trabalho if dias_trabalho > 0 else 0
meta_diaria_reais = despesas_totais / dias_trabalho if dias_trabalho > 0 else 0

# ===============================
# ABAS
# ===============================
tab1, tab2, tab3 = st.tabs(
    ["📊 Dashboard", "🧾 Registrar Dia", "📅 Relatório"]
)

# ===============================
# DASHBOARD
# ===============================
with tab1:
    col1, col2, col3 = st.columns(3)

    col1.metric("💸 Despesas Totais", f"R$ {despesas_totais:,.2f}")
    col2.metric("📆 Corridas no mês", f"{corridas_mes:.0f}")
    col3.metric("🎯 Meta diária (corridas)", f"{corridas_dia_meta:.1f}")

    st.subheader("📋 Despesas")
    st.dataframe(despesas_df, use_container_width=True)

# ===============================
# REGISTRO DIÁRIO
# ===============================
with tab2:
    st.subheader("🧾 Registro Diário")

    with st.form("form_registro_dia"):
        data = st.date_input("Data", value=date.today())
        corridas = st.number_input("Corridas realizadas", 0, 300)
        ganho_real = st.number_input("Ganho real do dia (R$)", 0.0, 10000.0)
        salvar_registro = st.form_submit_button("Salvar Registro")

    if salvar_registro:
        garantir_pasta(CAMINHO_REGISTROS)

        ganho_calculado = corridas * valor_corrida
        aproveitamento = (
            (ganho_real / meta_diaria_reais) * 100
            if meta_diaria_reais > 0 else 0
        )

        status = (
            "🟢 Acima da meta"
            if ganho_real >= meta_diaria_reais
            else "🔴 Abaixo da meta"
        )

        novo = pd.DataFrame([{
            "Data": data,
            "Corridas": corridas,
            "Ganho Calculado": ganho_calculado,
            "Ganho Real": ganho_real,
            "Meta Diária": meta_diaria_reais,
            "Aproveitamento (%)": round(aproveitamento, 1),
            "Status": status
        }])

        registros_df = pd.concat([registros_df, novo], ignore_index=True)
        registros_df.to_csv(CAMINHO_REGISTROS, index=False)

        st.success("Registro salvo 🚀")
        st.rerun()

# ===============================
# RELATÓRIO + GRÁFICOS
# ===============================
with tab3:
    st.subheader("📅 Relatório Geral")

    if not registros_df.empty:
        st.dataframe(registros_df, use_container_width=True)

        col1, col2 = st.columns(2)
        col1.metric(
            "💰 Total ganho calculado",
            f"R$ {registros_df['Ganho Calculado'].sum():,.2f}"
        )
        col2.metric(
            "💰 Total ganho real",
            f"R$ {registros_df['Ganho Real'].sum():,.2f}"
        )

        st.subheader("📊 Meta vs Ganho Real")
        chart_df = registros_df.set_index("Data")[["Meta Diária", "Ganho Real"]]
        st.bar_chart(chart_df)

        csv = registros_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Baixar relatório CSV",
            csv,
            "motoflow_relatorio.csv",
            "text/csv"
        )
    else:
        st.info("Nenhum registro encontrado.")
