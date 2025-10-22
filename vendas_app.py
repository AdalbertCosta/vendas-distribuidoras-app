import streamlit as st
import pandas as pd
import altair as alt
import hashlib
import io
import requests

# =====================================================
# ⚙️ CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(page_title="Vendas Distribuidoras", layout="wide")
st.title("📊 Visualização de Vendas - Distribuidora")

# =====================================================
# 🔒 LOGIN SIMPLES
# =====================================================
USUARIOS = {
    "adalberto": "1234",
    "admin": "admin"
}

def autenticar():
    st.sidebar.header("🔐 Acesso Restrito")
    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if usuario in USUARIOS and senha == USUARIOS[usuario]:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario
            st.sidebar.success(f"Bem-vindo, {usuario} 👋")
        else:
            st.sidebar.error("Usuário ou senha inválidos.")

def logout():
    if st.sidebar.button("Sair"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = None
        st.rerun()

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = None

if not st.session_state["autenticado"]:
    autenticar()
    st.stop()
else:
    st.sidebar.info(f"Usuário: **{st.session_state['usuario']}**")
    logout()

# =====================================================
# 📦 ARQUIVO EXCEL VIA GITHUB
# =====================================================
URL_GITHUB = "https://github.com/AdalbertCosta/vendas-distribuidoras-app/raw/refs/heads/main/data/Vendas_Dist.xlsx"
nome_aba = "dist_novobi"

@st.cache_data
def carregar_dados():
    try:
        r = requests.get(URL_GITHUB)
        r.raise_for_status()
        bytes_io = io.BytesIO(r.content)
        df = pd.read_excel(bytes_io, sheet_name=nome_aba, dtype=str)
        df.columns = df.columns.str.strip()
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        if 'TotalLinha' in df.columns:
            df['TotalLinha'] = pd.to_numeric(df['TotalLinha'].astype(str).str.replace(',', '.'), errors='coerce')
        if 'Quantidade' in df.columns:
            df['Quantidade'] = pd.to_numeric(df['Quantidade'].astype(str).str.replace(',', '.'), errors='coerce')
        df = df.dropna(subset=['Data', 'TotalLinha'])
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = carregar_dados()
if df.empty:
    st.warning("⚠️ Nenhum dado carregado. Verifique se o Excel está acessível.")
    st.stop()

# =====================================================
# 🔍 FILTROS LATERAIS
# =====================================================
st.sidebar.header("🧭 Filtros")

coluna_filtro = st.sidebar.selectbox("Selecione uma coluna de filtro:", df.columns)
valores_unicos = ["Todos"] + sorted(df[coluna_filtro].dropna().unique().tolist())
valor_filtro = st.sidebar.selectbox("Selecione o valor:", valores_unicos)

if valor_filtro != "Todos":
    df = df[df[coluna_filtro] == valor_filtro]

st.sidebar.button("🔄 Atualizar dados", on_click=lambda: st.cache_data.clear())

# =====================================================
# 📊 VISUALIZAÇÕES
# =====================================================
st.success("🕒 Última atualização: 22/10/2025 via GitHub")
st.metric("📦 Total de Registros", f"{len(df):,}")

# === Gráfico de evolução ===
if 'Data' in df.columns and 'TotalLinha' in df.columns:
    df_graf = df.groupby('Data', as_index=False)['TotalLinha'].sum()
    chart = alt.Chart(df_graf).mark_line(point=True).encode(
        x=alt.X('Data:T', title='Data'),
        y=alt.Y('TotalLinha:Q', title='Total de Vendas (R$)'),
        tooltip=['Data', 'TotalLinha']
    ).properties(title="📈 Evolução das Vendas", height=400)
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("ℹ️ Colunas necessárias ('Data' e 'TotalLinha') não encontradas.")

# === Dados Detalhados ===
st.subheader("📋 Dados Filtrados")
st.dataframe(df, use_container_width=True)

# === Rodapé ===
st.success("Cache limpo! Recarregue a página para buscar os dados mais recentes.")
