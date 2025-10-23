# ============================================================
# 📊 VISUALIZAÇÃO DE VENDAS - DISTRIBUIDORA (v11 FINAL COMPLETO)
# ============================================================

import pandas as pd
import streamlit as st
import altair as alt
from io import BytesIO

# ============================================================
# ⚙️ CONFIG GERAL
# ============================================================
st.set_page_config(page_title="Vendas Distribuidora", layout="wide")

# 🎨 Paleta
COR_PRIMARIA = "#095a7f"
COR_SUCESSO  = "#12ac68"
COR_ALERTA   = "#e63946"
COR_NEUTRA   = "#6b7280"

st.title("📊 Visualização de Vendas - Distribuidora")

# ============================================================
# 🔐 LOGIN
# ============================================================
USUARIOS = {"adalberto": "1234"}

if "auth" not in st.session_state:
    st.session_state.auth = {"logado": False, "usuario": None}
if "filtros_aplicados" not in st.session_state:
    st.session_state.filtros_aplicados = False

def autenticar():
    st.sidebar.header("🔐 Acesso Restrito")
    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar", type="primary", key="btn_login"):
        if usuario in USUARIOS and senha == USUARIOS[usuario]:
            st.session_state.auth["logado"] = True
            st.session_state.auth["usuario"] = usuario
            st.rerun()
        else:
            st.sidebar.error("Usuário ou senha inválidos.")

def logout():
    if st.sidebar.button("Sair", key="btn_logout"):
        st.session_state.auth["logado"] = False
        st.session_state.auth["usuario"] = None
        st.session_state.filtros_aplicados = False
        st.rerun()

if not st.session_state.auth["logado"]:
    autenticar()
    st.stop()
else:
    st.sidebar.success(f"Usuário: **{st.session_state.auth['usuario']}**")
    logout()

# ============================================================
# 📦 FONTE DE DADOS
# ============================================================
URL_VENDAS = "https://github.com/AdalbertCosta/vendas-distribuidoras-app/raw/refs/heads/main/data/Vendas_Dist.xlsx"
URL_PRODUTOS = "https://github.com/AdalbertCosta/vendas-distribuidoras-app/raw/refs/heads/main/data/Produtos.xlsx"

NOME_ABA = "dist_novobi"
COLUNAS = ["Operacao", "Data", "CodEmpresa", "CardCode", "Origem", "Utilizacao", "ItemCode", "Quantidade", "TotalLinha"]

@st.cache_data(ttl=600)
def carregar_dados():
    df = pd.read_excel(URL_VENDAS, sheet_name=NOME_ABA, usecols=COLUNAS, dtype=str, engine="openpyxl")
    df.columns = df.columns.str.strip()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    for col in ["TotalLinha", "Quantidade"]:
        df[col] = (
            df[col].astype(str)
            .str.replace(r"[^0-9,.-]", "", regex=True)
            .str.replace(",", ".", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Data", "TotalLinha", "Quantidade"])
    df["Operacao"] = df["Operacao"].astype(str).str.strip().str.upper()
    df.loc[df["Operacao"] == "NF_DEV", ["TotalLinha", "Quantidade"]] *= -1

    df["TipoOperacao"] = df["Operacao"].apply(lambda x: "Venda" if x == "NF" else "Devolução")
    df["EmpresaNome"] = df["CodEmpresa"].astype(str).map({"10": "GAM", "20": "AND", "30": "FARMED"}).fillna(df["CodEmpresa"])
    return df

@st.cache_data(ttl=600)
def carregar_produtos():
    dfp = pd.read_excel(URL_PRODUTOS, usecols=["ItemCode", "ItemName", "Categoria"], engine="openpyxl")
    dfp["ItemCode"] = dfp["ItemCode"].astype(str).str.strip().str.zfill(3)
    dfp["ItemName"] = dfp["ItemName"].astype(str).str.strip()
    dfp["Categoria"] = dfp["Categoria"].astype(str).str.strip()
    return dfp

df = carregar_dados()
df_produtos = carregar_produtos()

# Padroniza códigos e faz merge
df["ItemCode"] = df["ItemCode"].astype(str).str.strip().str.zfill(3)
df = df.merge(df_produtos, on="ItemCode", how="left")

# Alerta lateral
itens_sem_nome = df[df["ItemName"].isna()]["ItemCode"].unique()
if len(itens_sem_nome) > 0:
    st.sidebar.warning(f"⚠️ {len(itens_sem_nome)} produtos sem correspondência no catálogo.")
else:
    st.sidebar.success("📚 Catálogo de produtos vinculado com sucesso!")

# ============================================================
# 🧭 FILTROS
# ============================================================
st.sidebar.header("🧩 Filtros de Visualização")

clientes   = sorted(df["CardCode"].dropna().unique())
operacoes  = sorted(df["Operacao"].dropna().unique())
itens      = sorted(df["ItemCode"].dropna().unique())
empresas   = sorted(df["EmpresaNome"].dropna().unique())

cardcodes    = st.sidebar.multiselect("🔍 Cliente(s):", options=clientes, placeholder="Selecione...")
operacao_sel = st.sidebar.multiselect("⚙️ Operação:", options=operacoes, placeholder="Todas")
itens_sel    = st.sidebar.multiselect("📦 ItemCode:", options=itens, placeholder="Todos")
empresa_sel  = st.sidebar.multiselect("🏢 Empresa:", options=empresas, placeholder="Todas")

min_data, max_data = df["Data"].min(), df["Data"].max()
intervalo_datas = st.sidebar.date_input("📅 Intervalo de Datas:", [min_data, max_data], min_value=min_data, max_value=max_data)

if st.sidebar.button("📊 Gerar Gráficos", type="primary", key="btn_gerar_graficos"):
    st.session_state.filtros_aplicados = True

if not st.session_state.filtros_aplicados:
    st.info("👆 Selecione filtros e clique em **Gerar Gráficos** para visualizar os painéis.")
    st.stop()

# ============================================================
# 🔍 APLICAÇÃO DE FILTROS
# ============================================================
df_filtrado = df.copy()
if empresa_sel:
    df_filtrado = df_filtrado[df_filtrado["EmpresaNome"].isin(empresa_sel)]
if cardcodes:
    df_filtrado = df_filtrado[df_filtrado["CardCode"].isin(cardcodes)]
if operacao_sel:
    df_filtrado = df_filtrado[df_filtrado["Operacao"].isin(operacao_sel)]
if itens_sel:
    df_filtrado = df_filtrado[df_filtrado["ItemCode"].isin(itens_sel)]

data_inicio, data_fim = pd.to_datetime(intervalo_datas[0]), pd.to_datetime(intervalo_datas[1])
df_filtrado = df_filtrado[(df_filtrado["Data"] >= data_inicio) & (df_filtrado["Data"] <= data_fim)]

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado para os filtros aplicados.")
    st.stop()

# ============================================================
# 🔢 MÉTRICAS
# ============================================================
vendas_brutas = df_filtrado.loc[df_filtrado["TotalLinha"] > 0, "TotalLinha"].sum()
devolucoes = df_filtrado.loc[df_filtrado["TotalLinha"] < 0, "TotalLinha"].sum()
vendas_liq = df_filtrado["TotalLinha"].sum()

qtd_bruta = df_filtrado.loc[df_filtrado["Quantidade"] > 0, "Quantidade"].sum()
qtd_dev = df_filtrado.loc[df_filtrado["Quantidade"] < 0, "Quantidade"].sum()
qtd_liq = df_filtrado["Quantidade"].sum()

def fmt_moeda_br(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_int_br(v): return f"{int(round(v)):,}".replace(",", ".") if pd.notna(v) else "0"

st.markdown(f"🗓️ **Período selecionado:** {data_inicio.strftime('%d/%m/%Y')} → {data_fim.strftime('%d/%m/%Y')}")
c1, c2, c3 = st.columns(3)
c1.metric("💰 Vendas Brutas", fmt_moeda_br(vendas_brutas))
c2.metric("↩️ Devoluções", fmt_moeda_br(devolucoes))
c3.metric("🧮 Vendas Líquidas", fmt_moeda_br(vendas_liq))

c4, c5, c6 = st.columns(3)
c4.metric("📦 Quantidade Bruta", fmt_int_br(qtd_bruta))
c5.metric("↩️ Quantidade Devolvida", fmt_int_br(qtd_dev))
c6.metric("🧮 Quantidade Líquida", fmt_int_br(qtd_liq))

# ============================================================
# 📤 EXPORTAÇÃO
# ============================================================
with st.sidebar.expander("📤 Exportar Dados"):
    buffer = BytesIO()
    df_filtrado.to_excel(buffer, index=False)
    st.download_button(
        label="💾 Baixar Excel Filtrado",
        data=buffer.getvalue(),
        file_name=f"vendas_filtradas_{data_inicio:%Y%m%d}_{data_fim:%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_download_excel"
    )

# ============================================================
# 📋 VISUALIZAR DADOS
# ============================================================
with st.expander("📋 Visualizar Dados Filtrados"):
    df_show = df_filtrado.copy()
    df_show["Data"] = df_show["Data"].dt.strftime("%d/%m/%Y")
    st.dataframe(df_show, use_container_width=True)

# ============================================================
# 🧭 ABAS ANALÍTICAS
# ============================================================
st.markdown("---")
st.success("✅ Filtros aplicados com sucesso!")
st.caption("Abaixo estão as análises interativas de vendas:")

abas = st.tabs([
    "📈 Evolução de Vendas",
    "🏆 Top Produtos",
    "👤 Total por Cliente",
    "💳 Ticket Médio",
    "📦 Por Origem",
    "🧱 Vendas x Devoluções (mês)",
    "📊 Crescimento por Cliente",
    "♻️ Análise de Devoluções"
])

# ============================================================
# 📈 EVOLUÇÃO DE VENDAS
# ============================================================
with abas[0]:
    st.subheader("📈 Evolução das Vendas ao Longo do Tempo")
    grafico_tempo = alt.Chart(df_filtrado).mark_line(point=True, color=COR_PRIMARIA).encode(
        x=alt.X("yearmonth(Data):T", title="Data"),
        y=alt.Y("sum(TotalLinha):Q", title="Total de Vendas (R$)"),
        color=alt.Color("CardCode:N", legend=alt.Legend(title="Cliente")),
        tooltip=["yearmonth(Data):T", "CardCode:N", alt.Tooltip("sum(TotalLinha):Q", format=",.2f")],
    ).properties(width="container", height=420)
    st.altair_chart(grafico_tempo, use_container_width=True)

# ============================================================
# 🏆 TOP PRODUTOS
# ============================================================
with abas[1]:
    st.subheader("🏆 Top Produtos (por Quantidade Líquida)")
    top_itens = (
        df_filtrado.groupby(["ItemCode", "ItemName", "Categoria"])["Quantidade"]
        .sum()
        .nlargest(10)
        .reset_index()
    )
    chart_top = alt.Chart(top_itens).mark_bar().encode(
        x="Quantidade:Q",
        y=alt.Y("ItemName:N", sort="-x", title="Produto"),
        color=alt.Color("Categoria:N", legend=alt.Legend(title="Categoria")),
        tooltip=["ItemCode", "ItemName", "Categoria", alt.Tooltip("Quantidade:Q", format=",.0f")]
    ).properties(width="container", height=420)
    st.altair_chart(chart_top, use_container_width=True)

# ============================================================
# 👤 TOTAL POR CLIENTE
# ============================================================
with abas[2]:
    st.subheader("👤 Total de Vendas Líquidas por Cliente")
    total_por_cliente = df_filtrado.groupby("CardCode")["TotalLinha"].sum().reset_index()
    chart_cliente = alt.Chart(total_por_cliente).mark_bar(color=COR_PRIMARIA).encode(
        x="TotalLinha:Q", y=alt.Y("CardCode:N", sort="-x"),
        tooltip=["CardCode", alt.Tooltip("TotalLinha:Q", format=",.2f")]
    ).properties(width="container", height=420)
    st.altair_chart(chart_cliente, use_container_width=True)

# ============================================================
# 💳 TICKET MÉDIO
# ============================================================
with abas[3]:
    st.subheader("💳 Ticket Médio por Cliente")
    tm = df_filtrado.groupby("CardCode", as_index=False).agg({"TotalLinha": "sum", "Quantidade": "sum"})
    tm = tm[tm["Quantidade"] != 0]
    tm["Ticket Médio"] = tm["TotalLinha"] / tm["Quantidade"]
    chart_ticket = alt.Chart(tm).mark_bar(color=COR_PRIMARIA).encode(
        x="Ticket Médio:Q", y=alt.Y("CardCode:N", sort="-x"),
        tooltip=["CardCode", alt.Tooltip("Ticket Médio:Q", format=",.2f")]
    ).properties(width="container", height=420)
    st.altair_chart(chart_ticket, use_container_width=True)

# ============================================================
# 📦 POR ORIGEM
# ============================================================
with abas[4]:
    st.subheader("📦 Distribuição por Origem (Quantidade Líquida)")
    por_origem = df_filtrado.groupby("Origem")["Quantidade"].sum().reset_index()
    chart_origem = alt.Chart(por_origem).mark_bar(color=COR_PRIMARIA).encode(
        x="Quantidade:Q", y=alt.Y("Origem:N", sort="-x"), tooltip=["Origem", "Quantidade"]
    ).properties(width="container", height=420)
    st.altair_chart(chart_origem, use_container_width=True)

# ============================================================
# 🧱 VENDAS X DEVOLUÇÕES
# ============================================================
with abas[5]:
    st.subheader("🧱 Vendas x Devoluções por Mês")
    df_mes = df_filtrado.copy()
    df_mes["Mes"] = df_mes["Data"].dt.to_period("M").astype(str)
    base = df_mes.groupby(["Mes", "TipoOperacao"])["TotalLinha"].sum().reset_index()
    chart_stack = alt.Chart(base).mark_bar().encode(
        x="Mes:N", y="TotalLinha:Q",
        color=alt.Color("TipoOperacao:N", scale=alt.Scale(domain=["Venda", "Devolução"], range=[COR_PRIMARIA, COR_ALERTA])),
        tooltip=["Mes", "TipoOperacao", alt.Tooltip("TotalLinha:Q", format=",.2f")],
    ).properties(width="container", height=420)
    st.altair_chart(chart_stack, use_container_width=True)

# ============================================================
# 📊 CRESCIMENTO POR CLIENTE
# ============================================================
with abas[6]:
    st.subheader("📊 Crescimento por Cliente (mês a mês)")
    df_mes = df_filtrado.copy()
    df_mes["Mes"] = df_mes["Data"].dt.to_period("M")
    total_mes = df_mes.groupby(["CardCode", "Mes"])["TotalLinha"].sum().reset_index()
    total_mes["Mes"] = total_mes["Mes"].astype(str)
    meses = sorted(total_mes["Mes"].unique())
    if len(meses) < 2:
        st.info("📅 É necessário pelo menos dois meses de dados.")
    else:
        mes_atual, mes_ant = meses[-1], meses[-2]
        atual = total_mes[total_mes["Mes"] == mes_atual].set_index("CardCode")
        anterior = total_mes[total_mes["Mes"] == mes_ant].set_index("CardCode")
        cres = atual.join(anterior, lsuffix="_atual", rsuffix="_ant").fillna(0)
        cres["Crescimento_pct"] = ((cres["TotalLinha_atual"] - cres["TotalLinha_ant"]) /
                                   cres["TotalLinha_ant"].replace({0: pd.NA})) * 100
        cres = cres.reset_index()
        chart_cres = alt.Chart(cres).mark_bar().encode(
            x=alt.X("Crescimento_pct:Q", title="% Crescimento"),
            y=alt.Y("CardCode:N", sort="-x"),
            color=alt.condition(alt.datum.Crescimento_pct > 0, alt.value(COR_SUCESSO), alt.value(COR_ALERTA)),
            tooltip=["CardCode", alt.Tooltip("Crescimento_pct:Q", format=".2f")]
        ).properties(width="container", height=420)
        st.altair_chart(chart_cres, use_container_width=True)


# ============================================================
# ♻️ ANÁLISE DE DEVOLUÇÕES
# ============================================================
with abas[7]:
    st.subheader("♻️ Análise de Devoluções")
    vendas_pos = df_filtrado.loc[df_filtrado["TotalLinha"] > 0, "TotalLinha"].sum()
    devolucoes_abs = -df_filtrado.loc[df_filtrado["TotalLinha"] < 0, "TotalLinha"].sum()
    indice_geral = (devolucoes_abs / vendas_pos * 100) if vendas_pos > 0 else 0.0

    m1, m2 = st.columns(2)
    m1.metric("🔄 Índice de Devolução", f"{indice_geral:.2f}%")
    m2.metric("↩️ Devoluções (R$)", fmt_moeda_br(-devolucoes))

    st.markdown("---")

    st.subheader("👥 Top Clientes por Devolução")
    base_cli = df_filtrado.groupby("CardCode").agg(
        vendas_brutas=("TotalLinha", lambda s: s[s > 0].sum()),
        devolucao_abs=("TotalLinha", lambda s: -s[s < 0].sum())
    ).reset_index()
    base_cli["indice_%"] = (base_cli["devolucao_abs"] / base_cli["vendas_brutas"] * 100).fillna(0)

    top_cli_valor = base_cli.sort_values("devolucao_abs", ascending=False).head(10)
    chart_cli_valor = alt.Chart(top_cli_valor).mark_bar(color=COR_ALERTA).encode(
        x="devolucao_abs:Q", y=alt.Y("CardCode:N", sort="-x"),
        tooltip=["CardCode", alt.Tooltip("devolucao_abs:Q", format=",.2f"), alt.Tooltip("indice_%:Q", format=".2f")]
    ).properties(width="container", height=380)
    st.altair_chart(chart_cli_valor, use_container_width=True)

    st.subheader("📦 Top Itens mais Devolvidos")
    base_item = df_filtrado.groupby("ItemCode").agg(devolucao_abs=("TotalLinha", lambda s: -s[s < 0].sum())).reset_index()
    base_item = base_item.sort_values("devolucao_abs", ascending=False).head(10)
    chart_item = alt.Chart(base_item).mark_bar(color=COR_ALERTA).encode(
        x="devolucao_abs:Q", y=alt.Y("ItemCode:N", sort="-x"),
        tooltip=["ItemCode", alt.Tooltip("devolucao_abs:Q", format=",.2f")]
    ).properties(width="container", height=380)
    st.altair_chart(chart_item, use_container_width=True)
