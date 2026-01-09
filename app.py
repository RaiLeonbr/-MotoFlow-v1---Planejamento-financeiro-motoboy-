import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(
    page_title="MotoFlow",
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
h1, h2, h3 { color: #e5e7eb; }
section[data-testid="stSidebar"] { background-color: #020617; }
</style>
""", unsafe_allow_html=True)

st.title("🏍️ MotoFlow – Planejamento Financeiro do Motoboy")

# ===============================
# ESTADO INICIAL
# ===============================
if "despesas" not in st.session_state:
    st.session_state.despesas = pd.DataFrame(
        columns=["Despesa", "Valor"]
    )

if "registros" not in st.session_state:
    st.session_state.registros = pd.DataFrame(
        columns=[
            "Data",
            "Corridas",
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
    nome = st.text_input("Nome da despesa")
    valor = st.number_input("Valor (R$)", 0.0, 10000.0)
    adicionar = st.form_submit_button("Adicionar")

    if adicionar and nome:
        nova = pd.DataFrame(
            [{"Despesa": nome, "Valor": valor}]
        )
        st.session_state.despesas = pd.concat(
            [st.session_state.despesas, nova],
            ignore_index=True
        )
        st.success("Despesa adicionada!")

despesas_totais = (
    st.session_state.despesas["Valor"].sum()
    if not st.session_state.despesas.empty else 0
)

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
    st.dataframe(
        st.session_state.despesas,
        use_container_width=True
    )

# ===============================
# REGISTRO DIÁRIO
# ===============================
with tab2:
    st.subheader("🧾 Registro Diário")

    with st.form("form_registro"):
        data = st.date_input("Data", value=date.today())
        corridas_feitas = st.number_input(
            "Corridas realizadas", 0, 300
        )
        ganho_real = st.number_input(
            "Ganho real do dia (R$)", 0.0, 10000.0
        )
        salvar = st.form_submit_button("Salvar registro")

        if salvar:
            ganho_calculado = corridas_feitas * valor_corrida

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
                "Corridas": corridas_feitas,
                "Ganho Calculado": ganho_calculado,
                "Ganho Real": ganho_real,
                "Meta Diária": meta_diaria_reais,
                "Aproveitamento (%)": round(aproveitamento, 1),
                "Status": status
            }])

            st.session_state.registros = pd.concat(
                [st.session_state.registros, novo],
                ignore_index=True
            )

            st.success("Registro salvo com sucesso!")

# ===============================
# RELATÓRIO + GRÁFICOS
# ===============================
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

        # 🔹 GRÁFICO DE BARRAS
        st.subheader("📊 Meta vs Ganho Real")
        chart_df = df.set_index("Data")[
            ["Meta Diária", "Ganho Real"]
        ]
        st.bar_chart(chart_df)

        # 🔹 GRÁFICO DE PIZZA
        st.subheader("🥧 Distribuição de Resultados")
        fig, ax = plt.subplots()
        df["Status"].value_counts().plot.pie(
            autopct="%1.1f%%",
            ax=ax
        )
        ax.set_ylabel("")
        st.pyplot(fig)

    else:
        st.info("Nenhum registro encontrado.")
