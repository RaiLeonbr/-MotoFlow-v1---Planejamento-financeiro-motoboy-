import streamlit as st
import pandas as pd
import os
from datetime import date

# ===============================
# CONFIGURAÇÕES DE ARQUIVO
# ===============================
DATA_PATH = "data"
DESPESAS_FILE = os.path.join(DATA_PATH, "despesas.csv")
REGISTROS_FILE = os.path.join(DATA_PATH, "registros.csv")

os.makedirs(DATA_PATH, exist_ok=True)

# ===============================
# FUNÇÕES DE PERSISTÊNCIA
# ===============================
def carregar_despesas():
    if os.path.exists(DESPESAS_FILE):
        return pd.read_csv(DESPESAS_FILE)
    return pd.DataFrame(columns=["Despesa", "Valor"])

def salvar_despesas(df):
    df.to_csv(DESPESAS_FILE, index=False)

def carregar_registros():
    if os.path.exists(REGISTROS_FILE):
        return pd.read_csv(REGISTROS_FILE)
    return pd.DataFrame(columns=[
        "Data", "Corridas", "Ganho (R$)",
        "Meta diária", "Aproveitamento (%)", "Status"
    ])

def salvar_registros(df):
    df.to_csv(REGISTROS_FILE, index=False)

# ===============================
# ESTILO VISUAL
# ===============================
st.set_page_config(page_title="MotoFlow", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0b0f14; }
[data-testid="metric-container"] {
    background-color: #111827;
    border-radius: 14px;
    padding: 18px;
    border-left: 6px solid #22c55e;
}
h1, h2, h3 { color: #e5e7eb; }
section[data-testid="stSidebar"] { background-color: #020617; }
</style>
""", unsafe_allow_html=True)

st.title("🏍️ MotoFlow – Planejamento Financeiro do Motoboy")

# ===============================
# SIDEBAR – CONFIGURAÇÕES
# ===============================
st.sidebar.header("⚙️ Configurações")

valor_corrida = st.sidebar.number_input(
    "Valor médio por corrida (R$)", 1.0, 50.0, 7.0
)

dias_trabalho = st.sidebar.number_input(
    "Dias trabalhados no mês", 1, 31, 30
)

# ===============================
# DESPESAS
# ===============================
st.sidebar.subheader("💸 Despesas Mensais")

df_despesas = carregar_despesas()

with st.sidebar.form("form_despesa"):
    nome = st.text_input("Nome da despesa")
    valor = st.number_input("Valor (R$)", 0.0, 10000.0)
    adicionar = st.form_submit_button("Adicionar")

    if adicionar and nome:
        novo = pd.DataFrame([{"Despesa": nome, "Valor": valor}])
        df_despesas = pd.concat([df_despesas, novo], ignore_index=True)
        salvar_despesas(df_despesas)
        st.success("Despesa adicionada!")

despesas_totais = df_despesas["Valor"].sum() if not df_despesas.empty else 0

# ===============================
# CÁLCULOS
# ===============================
corridas_mes = despesas_totais / valor_corrida if valor_corrida > 0 else 0
corridas_dia_meta = corridas_mes / dias_trabalho if dias_trabalho > 0 else 0

# ===============================
# ABAS
# ===============================
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🧾 Registrar Dia", "📅 Relatório"])

# ===============================
# DASHBOARD
# ===============================
with tab1:
    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Despesas Totais", f"R$ {despesas_totais:,.2f}")
    col2.metric("📆 Corridas/mês", f"{corridas_mes:.0f}")
    col3.metric("🎯 Meta diária", f"{corridas_dia_meta:.1f}")

    st.subheader("📋 Despesas")
    st.dataframe(df_despesas, use_container_width=True)

# ===============================
# REGISTRO DIÁRIO
# ===============================
with tab2:
    st.subheader("🧾 Registro Diário")

    df_registros = carregar_registros()

    with st.form("form_registro"):
        data = st.date_input("Data", value=date.today())
        corridas_feitas = st.number_input("Corridas realizadas", 0, 300)
        salvar = st.form_submit_button("Salvar registro")

        if salvar:
            ganho_dia = corridas_feitas * valor_corrida
            aproveitamento = (
                corridas_feitas / corridas_dia_meta * 100
                if corridas_dia_meta > 0 else 0
            )

            status = (
                "🟢 Dentro da meta"
                if corridas_feitas >= corridas_dia_meta
                else "🔴 Abaixo da meta"
            )

            novo = pd.DataFrame([{
                "Data": data,
                "Corridas": corridas_feitas,
                "Ganho (R$)": ganho_dia,
                "Meta diária": round(corridas_dia_meta, 1),
                "Aproveitamento (%)": round(aproveitamento, 1),
                "Status": status
            }])

            df_registros = pd.concat([df_registros, novo], ignore_index=True)
            salvar_registros(df_registros)

            st.success("Registro salvo com sucesso!")

# ===============================
# RELATÓRIO
# ===============================
with tab3:
    st.subheader("📅 Relatório")

    df_registros = carregar_registros()

    if not df_registros.empty:
        st.dataframe(df_registros, use_container_width=True)

        st.metric(
            "💵 Total ganho",
            f"R$ {df_registros['Ganho (R$)'].sum():,.2f}"
        )
    else:
        st.info("Nenhum registro encontrado.")
