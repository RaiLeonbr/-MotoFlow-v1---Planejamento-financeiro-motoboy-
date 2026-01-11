import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import create_engine

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

def get_engine():
    server = "localhost"
    database = "MotoFlowDB"
    username = "sa"
    password = "SENHA"
    connection_string = (
        f"mssql+pyodbc://{username}:{password}"
        f"@{server}/{database}"
        "?driver=ODBC Driver 17 for SQL Server"
    )
    return create_engine(connection_string)

def carregar_registros():
    try:
        engine = get_engine()
        return pd.read_sql(
            "SELECT * FROM registros ORDER BY data DESC",
            engine
        )
    except:
        return pd.DataFrame(columns=[
            "data", "corridas", "ganho_calculado",
            "ganho_real", "meta_diaria",
            "aproveitamento", "status"
        ])

def salvar_registro(df):
    engine = get_engine()
    df.to_sql("registros", engine, if_exists="append", index=False)

def carregar_despesas():
    try:
        engine = get_engine()
        return pd.read_sql(
            "SELECT * FROM despesas ORDER BY data DESC",
            engine
        )
    except:
        return pd.DataFrame(columns=["data", "descricao", "valor"])

def salvar_despesa(df):
    engine = get_engine()
    df.to_sql("despesas", engine, if_exists="append", index=False)

st.title("🏍️ MotoFlow")
st.caption("Planejamento financeiro inteligente para motoboy")

st.sidebar.header("⚙️ Configurações")

valor_corrida = st.sidebar.number_input(
    "Valor médio por corrida (R$)", 1.0, 50.0, 7.0
)

dias_trabalho = st.sidebar.number_input(
    "Dias trabalhados no mês", 1, 31, 30
)

st.sidebar.subheader("💸 Adicionar Despesa")

with st.sidebar.form("form_despesa"):
    data_despesa = st.date_input("Data", value=date.today())
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", 0.0, 10000.0)
    salvar_desp = st.form_submit_button("Salvar")

if salvar_desp and descricao:
    nova = pd.DataFrame([{
        "data": data_despesa,
        "descricao": descricao,
        "valor": valor
    }])
    salvar_despesa(nova)
    st.sidebar.success("Despesa salva 💾")
    st.rerun()

registros_df = carregar_registros()
despesas_df = carregar_despesas()

if registros_df.empty:
    st.warning("Ainda não há dados suficientes para exibir os indicadores.")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric(
        "💰 Total ganho calculado",
        f"R$ {registros_df['ganho_calculado'].sum():,.2f}"
    )
    c2.metric(
        "💰 Total ganho real",
        f"R$ {registros_df['ganho_real'].sum():,.2f}"
    )
    c3.metric(
        "📊 Aproveitamento médio",
        f"{registros_df['aproveitamento'].mean():.1f}%"
    )

tab1, tab2, tab3 = st.tabs(
    ["📊 Dashboard", "🧾 Registrar Dia", "📅 Relatório"]
)

with tab1:
    despesas_totais = despesas_df["valor"].sum() if not despesas_df.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("💸 Despesas Totais", f"R$ {despesas_totais:,.2f}")
    c2.metric(
        "💰 Ganho Total",
        f"R$ {registros_df['ganho_real'].sum():,.2f}"
        if not registros_df.empty else "R$ 0,00"
    )
    meta_mensal = (
        registros_df["meta_diaria"].mean() * dias_trabalho
        if not registros_df.empty else 0
    )
    c3.metric("🎯 Meta Mensal Estimada", f"R$ {meta_mensal:,.2f}")

with tab2:
    with st.form("form_registro"):
        data = st.date_input("Data", value=date.today())
        corridas = st.number_input("Corridas realizadas", 0, 300)
        ganho_real = st.number_input("Ganho real do dia (R$)", 0.0, 10000.0)
        salvar_reg = st.form_submit_button("Salvar Registro")

    if salvar_reg:
        ganho_calculado = corridas * valor_corrida
        meta_diaria = ganho_calculado
        aproveitamento = (
            (ganho_real / meta_diaria) * 100
            if meta_diaria > 0 else 0
        )
        status = (
            "🟢 Acima da meta"
            if ganho_real >= meta_diaria
            else "🔴 Abaixo da meta"
        )

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

with tab3:
    if not registros_df.empty:
        st.dataframe(registros_df, use_container_width=True)
        chart_df = registros_df.set_index("data")[[
            "meta_diaria", "ganho_real"
        ]]
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
