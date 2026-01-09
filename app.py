import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="MotoFlow", layout="wide")

st.title("🧪 Teste de Conexão – Neon + Streamlit")

DATABASE_URL = st.secrets.get("DATABASE_URL")

if not DATABASE_URL:
    st.error("❌ DATABASE_URL não encontrada nos Secrets")
    st.stop()

st.write("🔌 Tentando conectar ao banco...")

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"}
    )

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    st.success("✅ Conexão com Neon estabelecida com sucesso!")

except Exception as e:
    st.error("❌ Falha ao conectar no banco")
    st.exception(e)
    st.stop()
