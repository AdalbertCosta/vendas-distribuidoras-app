import streamlit as st
import pandas as pd
import altair as alt
import hashlib
import requests
import io
from datetime import datetime

# =====================================================
# 🎨 CONFIGURAÇÃO GLOBAL
# =====================================================
st.set_page_config(page_title="Therapi Analytics - Vendas Distribuidora", layout="wide")

# CSS personalizado
st.markdown("""
<style>
    body {
        background-color: #f7f9fb;
        font-family: 'Poppins', sans-serif;
    }
    .main-header {
        background-color: #095a7f;
        padding: 1rem 2rem;
        color: white;
        border-radius: 0 0 1rem 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .header-title {
        font-size: 1.8rem;
        font-weight: 600;
    }
    .logo {
        height: 50px;
        border-radius: 8px;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .footer {
        margin-top: 2rem;
        text-align: center;
        font-size: 0.9rem;
        color: #666;
        border-top: 1px solid #ddd;
        padding-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

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
# 🧭 CABEÇALHO
# =====================================================
st.markdown("""
<div class='main-header'>
    <div class='header-title'>📊 Therapi Analytics — Painel de Vendas</div>
    <img src='https://i.imgur.com/hwAJpVn.png' class='logo'>
</div>
""", unsafe_allow_html=True)

# =====================================================
# 📦 CARREGAMENTO DO ARQUIVO
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

        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df['TotalLinha'] = (
            df['TotalLinha']
            .astype(str)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .astype(float)
        )
        df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce')
        df = df.dropna(subset=['Data', 'TotalLinha'])
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar o arquivo: {e}")
        return pd.DataFrame()

df = carregar_dados()
if df.empty:
    st.warning("⚠️ Nenhum dado carregado. Verifique se o Excel está acessível.")
    st.stop()

# =====================================================
# 🎛️ FILTROS
# =====================================================
st.sidebar.header("🧭 Filtros")

coluna_filtro = st.sidebar.selectbox("Selecione uma coluna de filtro:", df.columns)
valores_unicos = ["Todos"] + sorted(df[coluna_filtro].dropna().unique().tolist())
valor_filtro = st.sidebar.selectbox("Selecione o valor:", valores_unicos)

if valor_filtro != "Todos":
    df = df[df[coluna_filtro] == valor_filtro]

if st.sidebar.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.success("🔁 Dados atualizados com sucesso! Recarregue a página.")

# =====================================================
# 📈 INDICADORES
# =====================================================
st.markdown(f"🕒 **Última atualização:** {datetime.now().strftime('%d/%m/%Y - %H:%M')} (via GitHub)")

col1, col2 = st.columns(2)
col1.markdown(f"<div class='metric-card'><h4>💰 Total de Vendas</h4><h2>R$ {df['TotalLinha'].sum():,.2f}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-card'><h4>📦 Quantidade Total</h4><h2>{df['Quantidade'].sum():,.0f}</h2></div>", unsafe_allow_html=True)

# =====================================================
# 📊 EVOLUÇÃO DAS VENDAS
# =====================================================
st.subheader("📈 Evolução das Vendas")

if 'Data' in df.columns and 'TotalLinha' in df.columns:
    df_graf = df.groupby(df['Data'].dt.date, as_index=False)['TotalLinha'].sum()
    chart = alt.Chart(df_graf).mark_line(point=True, color="#12ac68").encode(
        x=alt.X('Data:T', title='Data da Venda'),
        y=alt.Y('TotalLinha:Q', title='Total de Vendas (R$)', scale=alt.Scale(domainMin=0)),
        tooltip=[
            alt.Tooltip('Data:T', title='Data'),
            alt.Tooltip('TotalLinha:Q', title='Total (R$)', format=',.2f')
        ]
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("ℹ️ Colunas necessárias ('Data' e 'TotalLinha') não encontradas.")

# =====================================================
# 🏆 TOP CLIENTES
# =====================================================
st.subheader("🏆 Top Clientes por Volume de Vendas")
top_clientes = df.groupby('CardCode')['TotalLinha'].sum().nlargest(10).reset_index()
chart_top = alt.Chart(top_clientes).mark_bar(color="#095a7f").encode(
    x=alt.X('TotalLinha:Q', title='Total de Vendas (R$)'),
    y=alt.Y('CardCode:N', title='Cliente', sort='-x'),
    tooltip=['CardCode', alt.Tooltip('TotalLinha:Q', format=',.2f')]
).properties(height=400)
st.altair_chart(chart_top, use_container_width=True)

# =====================================================
# 📋 DADOS FILTRADOS
# =====================================================
st.subheader("📋 Dados Filtrados")
st.dataframe(df, use_container_width=True)

# =====================================================
# ⚙️ RODAPÉ
# =====================================================
st.markdown("""
<div class='footer'>
    Desenvolvido por <b>Adalberto Costa</b> • Therapi Analytics © 2025<br>
    Sistema de visualização de dados com <b>Streamlit + Power BI DNA</b>
</div>
""", unsafe_allow_html=True)
