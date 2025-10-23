# ============================================================
# 📈 Painel de Vendas Therapi Distribuidoras - vFinal
# ============================================================

import pandas as pd
import streamlit as st
import altair as alt
import hashlib

# ------------------------------------------------------------
# Configuração da página
# ------------------------------------------------------------
st.set_page_config(page_title="Vendas Distribuidoras", layout="wide")
st.title("📊 Visualização de Vendas - Distribuidora")

# ------------------------------------------------------------
# Caminho e parâmetros
# ------------------------------------------------------------
caminho_arquivo = "data/Vendas_Dist.xlsx"
nome_aba = "dist_novobi"
colunas_desejadas = [
    "Operacao", "Data", "CodEmpresa", "DocNum", "CardCode", "Cancelado",
    "Origem", "Utilizacao", "ItemCode", "TotalDocumento", "TotalLinha", "Quantidade"
]

# ------------------------------------------------------------
# Função de hash (cache inteligente)
# ------------------------------------------------------------
def hash_arquivo(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

# ------------------------------------------------------------
# Função de limpeza de números
# ------------------------------------------------------------
def _parse_number(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    s = (s.replace('R$', '')
           .replace('\u00A0', '')
           .replace(' ', '')
           .strip())
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    elif s.count('.') > 1:
        partes = s.split('.')
        s = ''.join(partes[:-1]) + '.' + partes[-1]
    if s == '' or s == '-':
        return None
    try:
        return float(s)
    except Exception:
        return None

# ------------------------------------------------------------
# Função para carregar dados
# ------------------------------------------------------------
@st.cache_data
def carregar_dados(hash_arquivo=None):
    try:
        df = pd.read_excel(caminho_arquivo, sheet_name=nome_aba, usecols=colunas_desejadas, dtype=str)
        df.columns = df.columns.str.strip()

        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["TotalLinha"] = df["TotalLinha"].map(_parse_number)
        df["Quantidade"] = df["Quantidade"].map(_parse_number)
        df = df.dropna(subset=["Data", "TotalLinha", "Quantidade"])
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar o arquivo: {e}")
        return pd.DataFrame()

df = carregar_dados(hash_arquivo(caminho_arquivo))

if df.empty:
    st.warning("⚠️ Nenhum dado foi carregado. Verifique se o Excel está acessível.")
    st.stop()

# ------------------------------------------------------------
# Filtros laterais
# ------------------------------------------------------------
st.sidebar.header("🧭 Filtros de Visualização")

clientes = sorted(df["CardCode"].dropna().unique())
operacoes = sorted(df["Operacao"].dropna().unique())
itens = sorted(df["ItemCode"].dropna().unique())

cardcodes = st.sidebar.multiselect("🔍 Selecione cliente(s):", options=clientes)
operacao_sel = st.sidebar.multiselect("⚙️ Tipo de operação:", options=operacoes)
item_sel = st.sidebar.multiselect("📦 Código do produto:", options=itens)

min_data, max_data = df["Data"].min(), df["Data"].max()
data_inicio, data_fim = st.sidebar.date_input(
    "📅 Intervalo de datas:", [min_data, max_data],
    min_value=min_data, max_value=max_data
)

# ------------------------------------------------------------
# Aplicação dos filtros
# ------------------------------------------------------------
df_filtrado = df.copy()
if cardcodes:
    df_filtrado = df_filtrado[df_filtrado["CardCode"].isin(cardcodes)]
if operacao_sel:
    df_filtrado = df_filtrado[df_filtrado["Operacao"].isin(operacao_sel)]
if item_sel:
    df_filtrado = df_filtrado[df_filtrado["ItemCode"].isin(item_sel)]

df_filtrado = df_filtrado[
    (df_filtrado["Data"] >= pd.to_datetime(data_inicio)) &
    (df_filtrado["Data"] <= pd.to_datetime(data_fim))
]

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# ------------------------------------------------------------
# KPIs principais
# ------------------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("💰 Total de Vendas", f"R$ {df_filtrado['TotalLinha'].sum():,.2f}")
col2.metric("📦 Quantidade Total", f"{df_filtrado['Quantidade'].sum():,.0f}")
col3.metric("🧾 Total de Registros", f"{len(df_filtrado):,}")

# ------------------------------------------------------------
# Exibição da tabela formatada
# ------------------------------------------------------------
df_exibicao = df_filtrado.copy()
df_exibicao["Data"] = df_exibicao["Data"].dt.strftime("%d/%m/%Y")

st.dataframe(
    df_exibicao.style.format({
        "TotalLinha": "{:,.2f}",
        "Quantidade": "{:,.0f}"
    }),
    use_container_width=True
)

# ------------------------------------------------------------
# Abas analíticas
# ------------------------------------------------------------
abas = st.tabs([
    "📊 Resumo Executivo", "📈 Evolução de Vendas",
    "🏆 Top Produtos", "👤 Total por Cliente",
    "💳 Ticket Médio", "📦 Por Origem"
])

# ------------------------------------------------------------
# 🧠 Resumo Executivo
# ------------------------------------------------------------
with abas[0]:
    st.subheader("📊 Resumo Executivo — Insights Automáticos")

    total = df_filtrado["TotalLinha"].sum()
    qtd = df_filtrado["Quantidade"].sum()

    df_mes = df_filtrado.copy()
    df_mes["Mes"] = df_mes["Data"].dt.to_period("M")
    vendas_mes = df_mes.groupby("Mes")["TotalLinha"].sum().reset_index()
    vendas_mes["Mes"] = vendas_mes["Mes"].astype(str)

    if len(vendas_mes) > 1:
        crescimento = (vendas_mes.iloc[-1, 1] - vendas_mes.iloc[-2, 1]) / vendas_mes.iloc[-2, 1] * 100
        direcao = "⬆️ Crescimento" if crescimento > 0 else "⬇️ Queda"
        cor = "#12ac68" if crescimento > 0 else "#b94a48"
    else:
        crescimento, direcao, cor = 0, "Estável", "#999999"

    ticket_medio = total / qtd if qtd > 0 else 0
    cliente_top = df_filtrado.groupby("CardCode")["TotalLinha"].sum().nlargest(1).index[0]
    produto_top = df_filtrado.groupby("ItemCode")["Quantidade"].sum().nlargest(1).index[0]

    st.markdown(f"""
    💬 **Resumo Automático**
    - Faturamento total: **R$ {total:,.2f}**
    - Quantidade total: **{qtd:,.0f}**
    - Ticket médio: **R$ {ticket_medio:,.2f}**
    - Cliente destaque: **{cliente_top}**
    - Produto destaque: **{produto_top}**
    - Variação: **{direcao} de {abs(crescimento):.2f}%**
    """)

    base_chart = alt.Chart(vendas_mes).mark_line(point=True, strokeWidth=3, color=cor).encode(
        x=alt.X("Mes:N", title="Mês"),
        y=alt.Y("TotalLinha:Q", title="Faturamento (R$)"),
        tooltip=["Mes:N", alt.Tooltip("TotalLinha:Q", format=",.2f")]
    )

    regressao = alt.Chart(vendas_mes).transform_regression(
        "month(Mes)", "TotalLinha", method="linear", extent=[0, len(vendas_mes)+2]
    ).mark_line(color="orange", strokeDash=[6, 3])

    st.altair_chart(base_chart + regressao, use_container_width=True)

# ------------------------------------------------------------
# 📈 Evolução das Vendas
# ------------------------------------------------------------
with abas[1]:
    st.subheader("📈 Evolução das Vendas ao Longo do Tempo")
    grafico_tempo = alt.Chart(df_filtrado).mark_line(point=True).encode(
        x=alt.X("yearmonth(Data):T", title="Data"),
        y=alt.Y("sum(TotalLinha):Q", title="Total de Vendas"),
        color="CardCode:N",
        tooltip=["yearmonth(Data):T", alt.Tooltip("sum(TotalLinha):Q", format=",.2f")]
    ).properties(height=400)
    st.altair_chart(grafico_tempo, use_container_width=True)

# ------------------------------------------------------------
# 🏆 Top Produtos
# ------------------------------------------------------------
with abas[2]:
    st.subheader("🏆 Top Produtos Vendidos")
    top_itens = df_filtrado.groupby("ItemCode")["Quantidade"].sum().nlargest(10).reset_index()
    chart_top = alt.Chart(top_itens).mark_bar().encode(
        x="Quantidade:Q", y=alt.Y("ItemCode:N", sort="-x"),
        tooltip=["ItemCode", "Quantidade"]
    )
    st.altair_chart(chart_top, use_container_width=True)

# ------------------------------------------------------------
# 👤 Total por Cliente
# ------------------------------------------------------------
with abas[3]:
    st.subheader("👤 Total de Vendas por Cliente")
    total_cliente = df_filtrado.groupby("CardCode")["TotalLinha"].sum().reset_index()
    chart_cliente = alt.Chart(total_cliente).mark_bar().encode(
        x=alt.X("TotalLinha:Q"), y=alt.Y("CardCode:N", sort="-x"),
        tooltip=[alt.Tooltip("TotalLinha:Q", format=",.2f")]
    )
    st.altair_chart(chart_cliente, use_container_width=True)

# ------------------------------------------------------------
# 💳 Ticket Médio
# ------------------------------------------------------------
with abas[4]:
    st.subheader("💳 Ticket Médio por Cliente")
    ticket = df_filtrado.groupby("CardCode").agg({"TotalLinha": "sum", "Quantidade": "sum"}).reset_index()
    ticket["Ticket Médio"] = ticket["TotalLinha"] / ticket["Quantidade"]
    chart_ticket = alt.Chart(ticket).mark_bar().encode(
        x=alt.X("Ticket Médio:Q"), y=alt.Y("CardCode:N", sort="-x"),
        tooltip=[alt.Tooltip("Ticket Médio:Q", format=",.2f")]
    )
    st.altair_chart(chart_ticket, use_container_width=True)

# ------------------------------------------------------------
# 📦 Por Origem
# ------------------------------------------------------------
with abas[5]:
    st.subheader("📦 Distribuição por Origem")
    origem = df_filtrado.groupby("Origem")["Quantidade"].sum().reset_index()
    chart_origem = alt.Chart(origem).mark_bar().encode(
        x="Quantidade:Q", y=alt.Y("Origem:N", sort="-x"),
        tooltip=["Origem", "Quantidade"]
    )
    st.altair_chart(chart_origem, use_container_width=True)
