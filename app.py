# ===============================
# IMPORTAÇÕES E BIBLIOTECAS
# ===============================
import os
import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt

# ===============================
# FUNÇÃO UTILITÁRIA
# ===============================
def garantir_pasta(caminho_arquivo):
    pasta = os.path.dirname(caminho_arquivo)
    if pasta and not os.path.exists(pasta):
        os.makedirs(pasta)

# ===============================
# CAMINHOS DOS ARQUIVOS
# ===============================
CAMINHO_REGISTROS = "data/registros.csv"
CAMINHO_DESPESAS = "data/despesas.csv"

# ===============================
# FUNÇÕES DE PERSISTÊNCIA
# ===============================
def salvar_despesa(data, nome, valor):
    garantir_pasta(CAMINHO_DESPESAS)

    nova = pd.DataFrame([{
        "Data": data,
        "Despesa": nome,
        "Valor": valor
    }])

    if os.path.exists(CAMINHO_DESPESAS):
        df = pd.read_csv(CAMINHO_DESPESAS)
        df = pd.concat([df, nova], ignore_index=True)
    else:
        df = nova

    df.to_csv(CAMINHO_DESPESAS, index=False)


def salvar_registro(data, corridas, ganho_real, meta_diaria, valor_corrida):
    garantir_pasta(CAMINHO_REGISTROS)

    ganho_calculado = corridas * valor_corrida
    aproveitamento = (ganho_real / meta_diaria) * 100 if meta_diaria > 0 else 0
    status = "🟢 Acima da meta" if ganho_real >= meta_diaria else "🔴 Abaixo da meta"

    novo = pd.DataFrame([{
        "Data": data,
        "Corridas": corridas,
        "Ganho Calculado": ganho_calculado,
        "Ganho Real": ganho_real,
        "Meta Diária": meta_diaria,
        "Aproveitamento (%)": round(aproveitamento, 1),
        "Status": status
    }])

    if os.path.exists(CAMINHO_REGISTROS):
        df = pd.read_csv(CAMINHO_REGISTROS)
        df = pd.concat([df, novo], ignore_index=True)
    else:
        df = novo

    df.to_csv(CAMINHO_REGISTROS, index=False)


def carregar_csv(caminho, colunas):
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    return pd.DataFrame(columns=colunas)

# ===============================
# CONFIGURAÇÃO DA PÁGINA
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
# CARREGAMENTO INICIAL
# ===============================
despesas_df = carregar_csv(
    CAMINHO_DESPESAS,
    ["Data", "Despesa", "Valor"]
)

registros_df = carregar_csv(
    CAMINHO_REGISTROS,
    [
        "Data", "Corridas", "Ganho Calculado",
        "Ganho Real", "Meta Diária",
        "Aproveitamento (%)", "Status"
    ]
)

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

with st.sidebar.form("form_despesa"):
    data_despesa = st.date_input("Data", value=date.today())
    nome = st.text_input("Nome da despesa")
    valor = st.number_input("Valor (R$)", 0.0, 10000.0)
    adicionar = st.form_submit_button("Adicionar")

    if adicionar and nome:
        salvar_despesa(data_despesa, nome, valor)
        st.success("Despesa salva com sucesso 💾")
        st.rerun()

despesas_totais = despesas_df["Valor"].sum() if not despesas_df.empty else 0

# ===============================
# CÁLCULOS
# ===============================
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

    col1.metric("💰 Despesas Totais", f"R$ {despesas_totais:,.2f}")
    col2.metric("📆 Corridas/mês", f"{corridas_mes:.0f}")
    col3.metric("🎯 Meta diária (corridas)", f"{corridas_dia_meta:.1f}")

    st.subheader("📋 Despesas")
    st.dataframe(despesas_df, use_container_width=True)

# ===============================
# REGISTRO DIÁRIO
# ===============================
with tab2:
    st.subheader("🧾 Registro Diário")

    with st.form("form_registro"):
        data = st.date_input("Data", value=date.today())
        corridas_feitas = st.number_input("Corridas realizadas", 0, 300)
        ganho_real = st.number_input("Ganho real do dia (R$)", 0.0, 10000.0)
        salvar = st.form_submit_button("Salvar registro")

        if salvar:
            salvar_registro(
                data,
                corridas_feitas,
                ganho_real,
                meta_diaria_reais,
                valor_corrida
            )

            # cálculo do aproveitamento do dia
            aproveitamento_dia = (
                (ganho_real / meta_diaria_reais) * 100
                if meta_diaria_reais > 0
                else 0
            )

            st.success("Registro salvo com sucesso 🚀")

            
            

# ===============================
# RELATÓRIO + GRÁFICOS
# ===============================
with tab3:
    st.subheader("📅 Relatório")

    if not registros_df.empty:
        st.dataframe(registros_df, use_container_width=True)

        col1, col2 = st.columns(2)
        col1.metric(
            "💵 Total ganho calculado",
            f"R$ {registros_df['Ganho Calculado'].sum():,.2f}"
        )
        col2.metric(
            "💵 Total ganho real",
            f"R$ {registros_df['Ganho Real'].sum():,.2f}"
        )

        st.subheader("📊 Meta vs Ganho Real")
        chart_df = registros_df.set_index("Data")[["Meta Diária", "Ganho Real"]]
        st.bar_chart(chart_df)

with tab3:
    st.subheader("📅 Relatório")

    df = st.session_state.registros

    if not df.empty:
        st.dataframe(df, use_container_width=True)

        col1, col2 = st.columns(2)
        col1.metric(
            "💵 Total ganho calculado",
            f"R$ {df['Ganho Calculado'].sum():,.2f}"
        )
        col2.metric(
            "💵 Total ganho real",
            f"R$ {df['Ganho Real'].sum():,.2f}"
        )
        st.subheader("📊 Meta vs Ganho Real")
        chart_df = df.set_index("Data")[["Meta Diária", "Ganho Real"]]
        st.bar_chart(chart_df)
        


    

        
