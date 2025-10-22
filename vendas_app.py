import streamlit as st
import pandas as pd
import altair as alt
import hashlib

# =====================================================
# ⚙️ CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(page_title='Painel de Vendas Therapi Distribuidoras', layout='wide')
st.title('📊 Visualização de Vendas - Distribuidora')

# =====================================================
# 🔒 SISTEMA DE LOGIN SIMPLES
# =====================================================
USUARIOS = {
    "adalberto": "1234",
    "televendas": "2027"
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
# 📂 LINK DO ARQUIVO VIA GITHUB LFS
# =====================================================
url_excel = "https://github.com/AdalbertCosta/vendas-distribuidoras-app/raw/refs/heads/main/data/Vendas_Dist.xlsx"
nome_aba = "dist_novobi"

colunas_desejadas = [
    "Operacao", "Data", "CodEmpresa", "CardCode", "Origem", "Utilizacao",
    "ItemCode", "Quantidade", "TotalLinha"
]

# =====================================================
# 🧠 CACHE E FUNÇÃO DE CARREGAMENTO
# =====================================================
def hash_url(url):
    return hashlib.md5(url.encode()).hexdigest()

@st.cache_data
def carregar_dados(hash_url):
    try:
        df = pd.read_excel(
            url_excel,
            sheet_name=nome_aba,
            usecols=colunas_desejadas,
            dtype=str
        )
        df.columns = df.columns.str.strip()
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df['TotalLinha'] = pd.to_numeric(df['TotalLinha'].str.replace(',', '.'), errors='coerce')
        df['Quantidade'] = pd.to_numeric(df['Quantidade'].str.replace(',', '.'), errors='coerce')
        df = df.dropna(subset=['Data', 'TotalLinha', 'Quantidade'])
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar o arquivo: {e}")
        return pd.DataFrame()

# =====================================================
# 🔁 BOTÃO PARA ATUALIZAR OS DADOS
# =====================================================
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.success("Cache limpo! Recarregue a página para buscar os dados mais recentes.")
    st.stop()

# =====================================================
# 🚀 CARREGAR DADOS
# =====================================================
df = carregar_dados(hash_url(url_excel))

if df.empty:
    st.warning("⚠️ Nenhum dado foi carregado. Verifique se o Excel está acessível.")
    st.stop()

# =====================================================
# 🔍 FILTROS
# =====================================================
if 'CardCode' not in df.columns:
    st.error("❌ A coluna 'CardCode' não foi encontrada no arquivo.")
    st.stop()

cardcodes = st.multiselect(
    "🔍 Selecione o(s) código(s) de cliente (CardCode):",
    options=sorted(df['CardCode'].dropna().unique()),
    placeholder="Digite ou selecione o cliente..."
)
if not cardcodes:
    st.warning("⚠️ Selecione pelo menos um 'CardCode' para visualizar os dados.")
    st.stop()

min_data, max_data = df['Data'].min(), df['Data'].max()
data_inicio, data_fim = st.date_input(
    "📅 Intervalo de datas:",
    [min_data, max_data],
    min_value=min_data,
    max_value=max_data
)

df_filtrado = df[
    (df['CardCode'].isin(cardcodes)) &
    (df['Data'] >= pd.to_datetime(data_inicio)) &
    (df['Data'] <= pd.to_datetime(data_fim))
].copy()

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# =====================================================
# 📊 MÉTRICAS
# =====================================================
col1, col2 = st.columns(2)
col1.metric("💰 Total de Vendas", f"R$ {df_filtrado['TotalLinha'].sum():,.2f}")
col2.metric("📦 Quantidade Total", f"{df_filtrado['Quantidade'].sum():,.0f}")

df_exibicao = df_filtrado.copy()
df_exibicao['Data'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
st.dataframe(df_exibicao, use_container_width=True)

# =====================================================
# 📈 VISUALIZAÇÕES
# =====================================================
abas = st.tabs([
    "📈 Evolução de Vendas",
    "🏆 Top Produtos",
    "👤 Total por Cliente",
    "💳 Ticket Médio",
    "📦 Por Origem"
])

# 📈 Evolução
with abas[0]:
    st.subheader("📈 Evolução das Vendas ao Longo do Tempo")
    grafico_tempo = alt.Chart(df_filtrado).mark_line(point=True).encode(
        x=alt.X("yearmonth(Data):T", title="Data"),
        y=alt.Y("sum(TotalLinha):Q", title="Total de Vendas"),
        color="CardCode:N",
        tooltip=[
            alt.Tooltip("yearmonth(Data):T", title="Data"),
            alt.Tooltip("sum(TotalLinha):Q", title="Total de Vendas", format=",.2f"),
            alt.Tooltip("CardCode:N", title="Cliente")
        ]
    ).properties(width="container", height=400)
    st.altair_chart(grafico_tempo, use_container_width=True)

# 🏆 Top Produtos
with abas[1]:
    st.subheader("🏆 Top Produtos Vendidos")
    top_itens = df_filtrado.groupby("ItemCode")["Quantidade"].sum().nlargest(10).reset_index()
    chart_top = alt.Chart(top_itens).mark_bar().encode(
        x=alt.X("Quantidade:Q"),
        y=alt.Y("ItemCode:N", sort="-x"),
        tooltip=["ItemCode", "Quantidade"]
    ).properties(width="container", height=400)
    st.altair_chart(chart_top, use_container_width=True)

# 👤 Total por Cliente
with abas[2]:
    st.subheader("👤 Total de Vendas por Cliente")
    total_por_cliente = df_filtrado.groupby("CardCode")["TotalLinha"].sum().reset_index()
    chart_cliente = alt.Chart(total_por_cliente).mark_bar().encode(
        x=alt.X("TotalLinha:Q"),
        y=alt.Y("CardCode:N", sort="-x"),
        tooltip=[
            alt.Tooltip("CardCode:N", title="Cliente"),
            alt.Tooltip("TotalLinha:Q", title="Total", format=",.2f")
        ]
    ).properties(width="container", height=400)
    st.altair_chart(chart_cliente, use_container_width=True)

# 💳 Ticket Médio
with abas[3]:
    st.subheader("💳 Ticket Médio por Cliente")
    ticket_medio = (
        df_filtrado
        .groupby("CardCode", as_index=False)
        .agg({"TotalLinha": "sum", "Quantidade": "sum"})
    )
    ticket_medio = ticket_medio[ticket_medio["Quantidade"] > 0]
    ticket_medio["Ticket Médio"] = ticket_medio["TotalLinha"] / ticket_medio["Quantidade"]
    ticket_medio = ticket_medio[["CardCode", "Ticket Médio"]].sort_values(by="Ticket Médio", ascending=False)
    chart_ticket = alt.Chart(ticket_medio).mark_bar().encode(
        x=alt.X("Ticket Médio:Q"),
        y=alt.Y("CardCode:N", sort="-x"),
        tooltip=[
            alt.Tooltip("CardCode:N"),
            alt.Tooltip("Ticket Médio:Q", format=",.2f")
        ]
    ).properties(width="container", height=400)
    st.altair_chart(chart_ticket, use_container_width=True)

# 📦 Por Origem
with abas[4]:
    st.subheader("📦 Distribuição por Origem")
    quant_por_origem = df_filtrado.groupby("Origem")["Quantidade"].sum().reset_index()
    chart_origem = alt.Chart(quant_por_origem).mark_bar().encode(
        x=alt.X("Quantidade:Q"),
        y=alt.Y("Origem:N", sort="-x"),
        tooltip=["Origem", "Quantidade"]
    ).properties(width="container", height=400)
    st.altair_chart(chart_origem, use_container_width=True)
