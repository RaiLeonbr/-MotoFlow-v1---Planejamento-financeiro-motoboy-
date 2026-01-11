# ===============================
# IMPORTAÇÕES
# ===============================
import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import create_engine

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(
    page_title="MotoFlow",
    page_icon="🏍️",
    layout="wide"
)

# ===============================
# ESTILO
# ===============================
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

# ===============================
# CONEXÃO SQL SERVER
# ===============================
def get_engine():
    server = "localhost"
    database = "MotoFlowDB"
    username = "sa"          # ALTERE SE NECESSÁRIO
    password = "SENHA"       # ALTERE AQUI

    connection_string = (
        f"mssql+pyodbc://{username}:{password}"
        f"@{server}/{database}"
        "?driver=ODBC Driver 17 for SQL Server"
    )
    return create_engine(connection_string)

# ===============================
# FUNÇÕES DE BANCO
# ===============================
def carregar_registros():
    try:
        engine = get_engine()
        query = "SELECT * FROM registros ORDER BY data DESC"
        return pd.read_sql(query, engine)
    except:
        return pd.DataFrame(columns=[
            "data", "corridas",
            "ganho_calculado", "ganho_real",
            "meta_diaria", "aproveitamento", "status"
        ])

def salvar_registro(df):
    engine = get_engine()
    df.to_sql("registros", engine, if_exists="append", index=False)

# ===============================
# HEADER
# ===============================
st.title("🏍️ MotoFlow")
st.caption("Planejamento financeiro inteligente para motoboy")

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
# CARREGAR DADOS
# ===============================
registros_df = carregar_registros()

# ===============================
# CARDS PRINCIPAIS
# ===============================
if registros_df.empty:
    st.warning("Ainda não há dados suficientes para exibir os indicadores.")
else:
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "💰 Total ganho calculado",
        f"R$ {registros_df['ganho_calculado'].sum():,.2f}"
    )
    col2.metric(
        "💰 Total ganho real",
        f"R$ {registros_df['ganho_real'].sum():,.2f}"
    )
    col3.metric(
        "📊 Aproveitamento médio",
        f"{registros_df['aproveitamento'].mean():.1f}%"
    )

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
    st.subheader("📊 Visão Geral")

    if not registros_df.empty:
        col1, col2 = st.columns(2)

        col1.metric(
            "💰 Ganho Total",
            f"R$ {registros_df['ganho_real'].sum():,.2f}"
        )

        meta_mensal = registros_df["meta_diaria"].mean() * dias_trabalho
        col2.metric("🎯 Meta Mensal Estimada", f"R$ {meta_mensal:,.2f}")

        st.dataframe(registros_df, use_container_width=True)

# ===============================
# REGISTRO DIÁRIO
# ===============================
with tab2:
    st.subheader("🧾 Registro Diário")

    with st.form("form_registro"):
        data = st.date_input("Data", value=date.today())
        corridas = st.number_input("Corridas realizadas", 0, 300)
        ganho_real = st.number_input("Ganho real do dia (R$)", 0.0, 10000.0)
        salvar = st.form_submit_button("Salvar Registro")

    if salvar:
        ganho_calculado = corridas * valor_corrida
        meta_diaria = ganho_calculado if dias_trabalho > 0 else 0

        aproveitamento = (
            (ganho_real / meta_diaria) * 100
            if meta_diaria > 0 else 0
        )

        status = "🟢 Acima da meta" if ganho_real >= meta_diaria else "🔴 Abaixo da meta"

        novo = pd.DataFrame([{
            "data": data,
            "corridas": corridas,
            "ganho_calculado": ganho_calculado,
            "ganho_real": ganho_real,
            "meta_diaria": meta_diaria,
            "aproveitamento": round(aproveitamento, 1),
            "status": status
        }])

        salvar_registro(novo)
        st.success("Registro salvo com sucesso 🚀")
        st.rerun()

# ===============================
# RELATÓRIO
# ===============================
with tab3:
    st.subheader("📅 Relatório Geral")

    if not registros_df.empty:
        st.dataframe(registros_df, use_container_width=True)

        st.subheader("📊 Meta vs Ganho Real")
        chart_df = registros_df.set_index("data")[["meta_diaria", "ganho_real"]]
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
