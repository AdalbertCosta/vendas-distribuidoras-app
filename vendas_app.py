# ============================================================
# 📊 VISUALIZAÇÃO DE VENDAS - DISTRIBUIDORA (v2)
# ============================================================

import pandas as pd
import streamlit as st
import altair as alt

# ============================================================
# ⚙️ CONFIGURAÇÕES GERAIS
# ============================================================
st.set_page_config(page_title="Vendas Distribuidora", layout="wide")
st.title("📊 Visualização de Vendas - Distribuidora")

# ============================================================
# 📦 ARQUIVO DE DADOS
# ============================================================
URL_GITHUB = "https://github.com/AdalbertCosta/vendas-distribuidoras-app/raw/refs/heads/main/data/Vendas_Dist.xlsx"
nome_aba = "dist_novobi"
colunas_desejadas = [
    "Operacao", "Data", "CodEmpresa", "CardCode", "Origem", "Utilizacao",
    "ItemCode", "Quantidade", "TotalLinha"
]


# ============================================================
# 🧭 FILTROS LATERAIS
# ============================================================
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_excel(
            URL_GITHUB,
            sheet_name=nome_aba,
            usecols=colunas_desejadas,
            dtype=str,
            engine="openpyxl"
        )

        df.columns = df.columns.str.strip()
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

        # Converte campos numéricos com segurança (suporta vírgulas)
        for col in ["TotalLinha", "Quantidade"]:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[^0-9,.-]", "", regex=True)  # remove R$, espaços, letras
                .str.replace(",", ".", regex=False)         # troca vírgula por ponto
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["Data", "TotalLinha", "Quantidade"])
        return df

    except Exception as e:
        st.error(f"❌ Erro ao carregar o arquivo: {e}")
        return pd.DataFrame()


# ============================================================
# 🔢 MÉTRICAS GERAIS
# ============================================================
col1, col2 = st.columns(2)
col1.metric("💰 Total de Vendas", f"R$ {df_filtrado['TotalLinha'].sum():,.2f}")
col2.metric("📦 Quantidade Total", f"{df_filtrado['Quantidade'].sum():,.0f}")

# ============================================================
# 🧮 EXIBIÇÃO DE DADOS
# ============================================================
with st.expander("📋 Visualizar Dados Filtrados"):
    df_exibicao = df_filtrado.copy()
    df_exibicao["Data"] = df_exibicao["Data"].dt.strftime("%d/%m/%Y")
    st.dataframe(df_exibicao, use_container_width=True)

# ============================================================
# 🧭 ABAS DE ANÁLISE
# ============================================================
abas = st.tabs([
    "📈 Evolução de Vendas",
    "🏆 Top Produtos",
    "👤 Total por Cliente",
    "💳 Ticket Médio",
    "📦 Por Origem",
    "📊 Crescimento por Cliente"
])

# ============================================================
# 📈 1. EVOLUÇÃO DE VENDAS
# ============================================================
with abas[0]:
    st.subheader("📈 Evolução das Vendas ao Longo do Tempo")
    grafico_tempo = alt.Chart(df_filtrado).mark_line(point=True).encode(
        x=alt.X("yearmonth(Data):T", title="Data"),
        y=alt.Y("sum(TotalLinha):Q", title="Total de Vendas"),
        color="CardCode:N",
        tooltip=[
            alt.Tooltip("yearmonth(Data):T", title="Data"),
            alt.Tooltip("sum(TotalLinha):Q", title="Total de Vendas", format=",0.2f"),
            alt.Tooltip("CardCode:N", title="Cliente")
        ]
    ).properties(width="container", height=400)
    st.altair_chart(grafico_tempo, use_container_width=True)

# ============================================================
# 🏆 2. TOP PRODUTOS
# ============================================================
with abas[1]:
    st.subheader("🏆 Top Produtos Vendidos")
    top_itens = df_filtrado.groupby("ItemCode")["Quantidade"].sum().nlargest(10).reset_index()
    chart_top = alt.Chart(top_itens).mark_bar().encode(
        x=alt.X("Quantidade:Q"),
        y=alt.Y("ItemCode:N", sort="-x"),
        tooltip=["ItemCode", "Quantidade"]
    ).properties(width="container", height=400)
    st.altair_chart(chart_top, use_container_width=True)

# ============================================================
# 👤 3. TOTAL POR CLIENTE
# ============================================================
with abas[2]:
    st.subheader("👤 Total de Vendas por Cliente")
    total_por_cliente = df_filtrado.groupby("CardCode")["TotalLinha"].sum().reset_index()
    chart_cliente = alt.Chart(total_por_cliente).mark_bar().encode(
        x=alt.X("TotalLinha:Q"),
        y=alt.Y("CardCode:N", sort="-x"),
        tooltip=[
            alt.Tooltip("CardCode:N", title="Cliente"),
            alt.Tooltip("TotalLinha:Q", title="Total", format=",0.2f")
        ]
    ).properties(width="container", height=400)
    st.altair_chart(chart_cliente, use_container_width=True)

# ============================================================
# 💳 4. TICKET MÉDIO
# ============================================================
with abas[3]:
    st.subheader("💳 Ticket Médio por Cliente")
    ticket_medio = df_filtrado.groupby("CardCode", as_index=False).agg(
        {"TotalLinha": "sum", "Quantidade": "sum"}
    )
    ticket_medio = ticket_medio[ticket_medio["Quantidade"] > 0]
    ticket_medio["Ticket Médio"] = ticket_medio["TotalLinha"] / ticket_medio["Quantidade"]
    chart_ticket = alt.Chart(ticket_medio).mark_bar().encode(
        x=alt.X("Ticket Médio:Q"),
        y=alt.Y("CardCode:N", sort="-x"),
        tooltip=[
            alt.Tooltip("CardCode:N"),
            alt.Tooltip("Ticket Médio:Q", format=",0.2f")
        ]
    ).properties(width="container", height=400)
    st.altair_chart(chart_ticket, use_container_width=True)

# ============================================================
# 📦 5. DISTRIBUIÇÃO POR ORIGEM
# ============================================================
with abas[4]:
    st.subheader("📦 Distribuição por Origem")
    quant_por_origem = df_filtrado.groupby("Origem")["Quantidade"].sum().reset_index()
    chart_origem = alt.Chart(quant_por_origem).mark_bar().encode(
        x=alt.X("Quantidade:Q"),
        y=alt.Y("Origem:N", sort="-x"),
        tooltip=["Origem", "Quantidade"]
    ).properties(width="container", height=400)
    st.altair_chart(chart_origem, use_container_width=True)

# ============================================================
# 📊 6. CRESCIMENTO POR CLIENTE
# ============================================================
with abas[5]:
    st.subheader("📊 Crescimento por Cliente (mês a mês)")

    df_mes = df_filtrado.copy()
    df_mes["Mes"] = df_mes["Data"].dt.to_period("M")
    total_mes = df_mes.groupby(["CardCode", "Mes"])["TotalLinha"].sum().reset_index()
    total_mes["Mes"] = total_mes["Mes"].astype(str)

    meses = sorted(total_mes["Mes"].unique())
    if len(meses) < 2:
        st.info("📅 É necessário pelo menos dois meses de dados para calcular o crescimento.")
    else:
        mes_atual, mes_anterior = meses[-1], meses[-2]
        atual = total_mes[total_mes["Mes"] == mes_atual].set_index("CardCode")
        anterior = total_mes[total_mes["Mes"] == mes_anterior].set_index("CardCode")

        df_crescimento = atual.join(anterior, lsuffix="_atual", rsuffix="_ant")
        df_crescimento["Crescimento (%)"] = (
            (df_crescimento["TotalLinha_atual"] - df_crescimento["TotalLinha_ant"])
            / df_crescimento["TotalLinha_ant"]
        ) * 100
        df_crescimento = df_crescimento.sort_values("Crescimento (%)", ascending=False).reset_index()

        chart_crescimento = alt.Chart(df_crescimento.head(15)).mark_bar().encode(
            x=alt.X("Crescimento (%):Q", title="% Crescimento"),
            y=alt.Y("CardCode:N", sort="-x"),
            color=alt.condition(
                alt.datum["Crescimento (%)"] > 0,
                alt.value("#12ac68"),
                alt.value("#e63946")
            ),
            tooltip=[
                alt.Tooltip("CardCode:N", title="Cliente"),
                alt.Tooltip("Crescimento (%):Q", format=".2f"),
                alt.Tooltip("TotalLinha_atual:Q", title=f"Vendas {mes_atual}", format=",0.2f"),
                alt.Tooltip("TotalLinha_ant:Q", title=f"Vendas {mes_anterior}", format=",0.2f")
            ]
        ).properties(width="container", height=400)

        st.altair_chart(chart_crescimento, use_container_width=True)
        st.dataframe(df_crescimento.head(20), use_container_width=True)
