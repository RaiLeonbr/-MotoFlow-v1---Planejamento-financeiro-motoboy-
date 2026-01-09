import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt

# ===============================
# CONFIG STREAMLIT
# ===============================
st.set_page_config(
    page_title="MotoFlow",
    layout="wide"
)

# ===============================
# CONEXÃO COM BANCO (POSTGRES)
# ===============================
@st.cache_resource
def get_engine():
    return create_engine(
        st.secrets["DATABASE_URL"],
        pool_pre_ping=True
    )

engine = get_engine()

# ===============================
# CRIAÇÃO DAS TABELAS
# ===============================
def criar_tabelas():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS despesas (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                valor NUMERIC(10,2) NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS registros (
                id SERIAL PRIMARY KEY,
                data DATE NOT NULL,
                corridas INT,
                ganho_calculado NUMERIC(10,2),
                ganho_real NUMERIC(10,2),
                meta_diaria NUMERIC(10,2),
                aproveitamento NUMERIC(5,2),
                status TEXT
            );
        """))

criar_tabelas()

# ===============================
# FUNÇÕES DE BANCO
# ===============================
def carregar_despesas():
    return pd.read_sql(
        "SELECT id, nome AS Despesa, valor AS Valor FROM despesas ORDER BY id",
        engine
    )

def salvar_despesa(nome, valor):
    df = pd.DataFrame([{"nome": nome, "valor": valor}])
    df.to_sql("despesas", engine, if_exists="append", index=False)

def carregar_registros():
    return pd.read_sql(
        "SELECT * FROM registros ORDER BY data",
        engine
    )

def salvar_registro(data, corridas, ganho_calc, ganho_real, meta, aproveitamento, status):
    df = pd.DataFrame([{
        "data": data,
        "corridas": corridas,
        "ganho_calculado": ganho_calc,
        "ganho_real": ganho_real,
        "meta_diaria": meta,
        "aproveitamento": aproveitamento,
        "status": status
    }])
    df.to_sql("registros", engine, if_exists="append", index=False)

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
h1, h2, h3 { color: #e5e7eb; }
section[data-testid="stSidebar"] { background-color: #020617; }
</style>
""", unsafe_allow_html=True)

st.title("🏍️ MotoFlow – Planejamento Financeiro do Motoboy")

# ===============================
# SIDEBAR
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
        salvar_despesa(nome, valor)
        st.success("Despesa adicionada!")
        st.rerun()

despesas_totais = df_despesas["Valor"].sum() if not df_despesas.empty else 0

# ===============================
# CÁLCULOS
# ===============================
corridas_mes = despesas_totais / valor_corrida if valor_corrida > 0 else 0
corridas_dia_meta = corridas_mes / dias_trabalho if dias_trabalho > 0 else 0
meta_diaria_reais = despesas_totais / dias_trabalho if dias_trabalho > 0 else 0

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
    col3.metric("🎯 Meta diária (corridas)", f"{corridas_dia_meta:.1f}")

    st.subheader("📋 Despesas")
    st.dataframe(df_despesas, use_container_width=True)

# ===============================
# REGISTRO DIÁRIO
# ===============================
with tab2:
    st.subheader("🧾 Registro Diário")

    with st.form("form_registro"):
        data_registro = st.date_input("Data", value=date.today())
        corridas_feitas = st.number_input("Corridas realizadas", 0, 300)
        ganho_real = st.number_input("Ganho real do dia (R$)", 0.0, 10000.0)
        salvar = st.form_submit_button("Salvar registro")

        if salvar:
            ganho_calculado = corridas_feitas * valor_corrida
            aproveitamento = (
                (ganho_real / meta_diaria_reais * 100)
                if meta_diaria_reais > 0 else 0
            )

            status = "🟢 Acima da meta" if ganho_real >= meta_diaria_reais else "🔴 Abaixo da meta"

            salvar_registro(
                data_registro,
                corridas_feitas,
                ganho_calculado,
                ganho_real,
                meta_diaria_reais,
                round(aproveitamento, 1),
                status
            )

            st.success("Registro salvo com sucesso!")
            st.rerun()

# ===============================
# RELATÓRIO
# ===============================
with tab3:
    st.subheader("📅 Relatório")

    df_registros = carregar_registros()

    if not df_registros.empty:
        st.dataframe(df_registros, use_container_width=True)

        col1, col2 = st.columns(2)
        col1.metric(
            "💵 Total ganho calculado",
            f"R$ {df_registros['ganho_calculado'].sum():,.2f}"
        )
        col2.metric(
            "💵 Total ganho real",
            f"R$ {df_registros['ganho_real'].sum():,.2f}"
        )

        st.subheader("📊 Meta vs Ganho Real")
        chart_df = df_registros.set_index("data")[["meta_diaria", "ganho_real"]]
        st.bar_chart(chart_df)

        st.subheader("🥧 Distribuição de Status")
        fig, ax = plt.subplots()
        df_registros["status"].value_counts().plot.pie(
            autopct="%1.1f%%", ax=ax
        )
        ax.set_ylabel("")
        st.pyplot(fig)
    else:
        st.info("Nenhum registro encontrado.")
