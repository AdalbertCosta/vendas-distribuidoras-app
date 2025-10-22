# ============================================================
# 📊 Visualização de Vendas - Distribuidora
# Desenvolvido por Adalberto Costa
# ============================================================

import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# ============================================================
# ⚙️ Configurações da página
# ============================================================
st.set_page_config(
    page_title="Visualização de Vendas - Distribuidora",
    page_icon="📈",
    layout="wide",
)

# ============================================================
# 🧩 Carregamento do Excel via GitHub
# ============================================================
EXCEL_URL = "https://github.com/AdalbertCosta/vendas-distribuidoras-app/raw/refs/heads/main/data/Vendas_Dist.xlsx"

@st.cache_data(ttl=3600)
def carregar_dados():
    try:
        df = pd.read_excel(EXCEL_URL, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None

# ============================================================
# 🕓 Cabeçalho e banner dinâmico
# ============================================================
st.markdown("""
    <h1 style='text-align:center; color:#0a5a7f;'>
        📊 Visualização de Vendas - Distribuidora
    </h1>
""", unsafe_allow_html=True)

# Informativo sobre atualização da base
ultima_atualizacao = datetime.now().strftime("%d/%m/%Y - %H:%M")
st.success(f"📅 **Última atualização:** {ultima_atualizacao} (via GitHub)")

# ============================================================
# 🧠 Carregamento dos dados
# ============================================================
df = carregar_dados()

if df is None:
    st.warning("⚠️ Nenhum dado foi carregado. Verifique se o Excel está acessível.")
    st.stop()

# ============================================================
# 🔍 Pré-processamento e KPIs
# ============================================================
st.sidebar.header("🔎 Filtros")

# Filtros dinâmicos
colunas_numericas = df.select_dtypes(include="number").columns.tolist()
colunas_texto = df.select_dtypes(include="object").columns.tolist()

filtro_coluna = st.sidebar.selectbox("Selecione uma coluna de filtro:", colunas_texto)
valores = ["Todos"] + sorted(df[filtro_coluna].dropna().unique().tolist())
filtro_valor = st.sidebar.selectbox("Selecione o valor:", valores)

if filtro_valor != "Todos":
    df = df[df[filtro_coluna] == filtro_valor]

# ============================================================
# 📊 KPIs principais
# ============================================================
col1, col2, col3 = st.columns(3)
col1.metric("📦 Total de Registros", f"{len(df):,}".replace(",", "."))
if "I" in df.columns:
    col2.metric("💰 Valor Médio (coluna I)", f"R$ {df['I'].mean():,.2f}")
if "B" in df.columns:
    col3.metric("📆 Última Data", str(df["B"].max()) if not df["B"].isna().all() else "—")

# ============================================================
# 📈 Gráfico de Vendas
# ============================================================
st.markdown("### 📈 Evolução das Vendas")

if "B" in df.columns and "I" in df.columns:
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("B:T", title="Data"),
            y=alt.Y("I:Q", title="Valor"),
            tooltip=["B", "I"]
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("Não foi possível exibir o gráfico. Verifique se as colunas estão corretas (B = Data, I = Valor).")

# ============================================================
# 📋 Exibição de Tabela
# ============================================================
st.markdown("### 📋 Dados Filtrados")
st.dataframe(df.head(100))

# ============================================================
# 🔁 Botão de atualização
# ============================================================
if st.sidebar.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.success("Cache limpo! Recarregue a página para buscar os dados mais recentes.")
