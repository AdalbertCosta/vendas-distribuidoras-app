# ============================================================
# 📊 VISUALIZAÇÃO DE VENDAS - DISTRIBUIDORA (v7)
# ============================================================

import pandas as pd
import streamlit as st
import altair as alt

# ============================================================
# ⚙️ CONFIG GERAL
# ============================================================
st.set_page_config(page_title="Vendas Distribuidora", layout="wide")

# Paleta corporativa
COR_PRIMARIA = "#095a7f"
COR_SUCESSO  = "#12ac68"
COR_ALERTA   = "#e63946"
COR_NEUTRA   = "#6b7280"

st.title("📊 Visualização de Vendas - Distribuidora")

# ============================================================
# 🔐 LOGIN (obrigatório)
# ============================================================
USUARIOS = {
    "adalberto": "1234",
    #"televendas": "2027",
}

def autenticar():
    st.sidebar.header("🔐 Acesso Restrito")
    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar", type="primary"):
        if usuario in USUARIOS and senha == USUARIOS[usuario]:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario
            st.rerun()
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
    st.sidebar.success(f"Usuário: **{st.session_state['usuario']}**")
    logout()

# ============================================================
# 📦 FONTE DE DADOS (GitHub RAW)
# ============================================================
URL_GITHUB = "https://github.com/AdalbertCosta/vendas-distribuidoras-app/raw/refs/heads/main/data/Vendas_Dist.xlsx"
NOME_ABA = "dist_novobi"
COLUNAS = [
    "Operacao", "Data", "CodEmpresa", "CardCode", "Origem", "Utilizacao",
    "ItemCode", "Quantidade", "TotalLinha"
]

# ============================================================
# 🔄 CARREGAMENTO + LIMPEZA
# ============================================================
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_excel(
            URL_GITHUB, sheet_name=NOME_ABA, usecols=COLUNAS, dtype=str, engine="openpyxl"
        )
        df.columns = df.columns.str.strip()

        # Datas
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

        # Conversão robusta de numéricos (suporta vírgula)
        for col in ["TotalLinha", "Quantidade"]:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[^0-9,.-]", "", regex=True)
                .str.replace(",", ".", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["Data", "TotalLinha", "Quantidade"])

        # NF_DEV como devolução (valores negativos)
        def _neg_total(row):
            op = str(row["Operacao"]).upper().strip()
            return -abs(row["TotalLinha"]) if op == "NF_DEV" else row["TotalLinha"]

        def _neg_qtd(row):
            op = str(row["Operacao"]).upper().strip()
            return -abs(row["Quantidade"]) if op == "NF_DEV" else row["Quantidade"]

        df["TotalLinha"] = df.apply(_neg_total, axis=1)
        df["Quantidade"] = df.apply(_neg_qtd, axis=1)

        # Tipo amigável
        df["TipoOperacao"] = df["Operacao"].apply(
            lambda x: "Venda" if str(x).upper().strip() == "NF" else "Devolução"
        )

        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar o arquivo: {e}")
        return pd.DataFrame()

df = carregar_dados()
if df.empty:
    st.stop()


# ============================================================
# 🧭 FILTROS
# ============================================================

st.sidebar.header("🧩 Filtros de Visualização")

clientes   = sorted(df["CardCode"].dropna().unique())
operacoes  = sorted(df["Operacao"].dropna().unique())
itens      = sorted(df["ItemCode"].dropna().unique())

cardcodes   = st.sidebar.multiselect("🔍 Cliente(s):", options=clientes,  placeholder="Selecione cliente(s)...")
operacao_sel= st.sidebar.multiselect("⚙️ Operação:",  options=operacoes, placeholder="Todas")
itens_sel   = st.sidebar.multiselect("📦 ItemCode:",   options=itens,     placeholder="Todos")

min_data, max_data = df["Data"].min(), df["Data"].max()
data_inicio, data_fim = st.sidebar.date_input(
    "📅 Intervalo de datas:", [min_data, max_data], min_value=min_data, max_value=max_data
)

# 🏢 Filtro por Empresa
mapeamento_empresas = {"10": "GAM", "20": "AND", "30": "FARMED"}
df["EmpresaNome"] = df["CodEmpresa"].astype(str).map(mapeamento_empresas).fillna(df["CodEmpresa"])
empresas = sorted(df["EmpresaNome"].dropna().unique())
empresa_sel = st.sidebar.multiselect("🏢 Empresa:", options=empresas, placeholder="Todas", key="empresa_filtro")

st.sidebar.markdown(
    """
    **🔎 Códigos de Empresa:**  
    • 10 → GAM  
    • 20 → AND  
    • 30 → FARMED
    """
)

# ============================================================
# 🎛️ BOTÃO PARA ATUALIZAR GRÁFICOS
# ============================================================

if "gerar" not in st.session_state:
    st.session_state.gerar = False

# Botão manual para aplicar filtros
if st.sidebar.button("📊 Gerar Gráficos", type="primary"):
    st.session_state.gerar = True

# ============================================================
# 🔍 APLICAÇÃO DE FILTROS (somente após clique)
# ============================================================

if not st.session_state.gerar:
    st.info("👆 Selecione filtros e clique em **Gerar Gráficos** para visualizar os painéis.")
    st.stop()

df_filtrado = df.copy()

# 🏢 Empresa
if empresa_sel:
    df_filtrado = df_filtrado[df_filtrado["EmpresaNome"].isin(empresa_sel)]

# 🧑 Cliente
if cardcodes:
    df_filtrado = df_filtrado[df_filtrado["CardCode"].isin(cardcodes)]

# ⚙️ Operação
if operacao_sel:
    df_filtrado = df_filtrado[df_filtrado["Operacao"].isin(operacao_sel)]

# 📦 ItemCode
if itens_sel:
    df_filtrado = df_filtrado[df_filtrado["ItemCode"].isin(itens_sel)]

# 📅 Intervalo de Datas
df_filtrado = df_filtrado[
    (df_filtrado["Data"] >= pd.to_datetime(data_inicio)) &
    (df_filtrado["Data"] <= pd.to_datetime(data_fim))
]

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado para os filtros aplicados.")
    st.stop()


# ============================================================
# 🏢 Filtro por Empresa (CodEmpresa)
# ============================================================
mapeamento_empresas = {
    "10": "GAM",
    "20": "AND",
    "30": "FARMED"
}

# Cria coluna com nome da empresa
df["EmpresaNome"] = df["CodEmpresa"].astype(str).map(mapeamento_empresas).fillna(df["CodEmpresa"])

empresas = sorted(df["EmpresaNome"].dropna().unique())
empresa_sel = st.sidebar.multiselect("🏢 Empresa:", options=empresas, placeholder="Todas")

# Aplica filtro por empresa
df_filtrado = df.copy()
if empresa_sel:
    df_filtrado = df_filtrado[df_filtrado["EmpresaNome"].isin(empresa_sel)]

# Mostra legenda explicativa
st.sidebar.markdown(
    """
    **🔎 Códigos de Empresa:**  
    • 10 → GAM  
    • 20 → AND  
    • 30 → FARMED
    """
)

# ============================================================
# 🔢 MÉTRICAS (Bruta, Devolução, Líquida)
# ============================================================
df_filtrado["TotalLinha"] = df_filtrado["TotalLinha"].astype(float)
df_filtrado["Quantidade"] = pd.to_numeric(df_filtrado["Quantidade"], errors="coerce")

vendas_brutas = df_filtrado.loc[df_filtrado["TotalLinha"] > 0, "TotalLinha"].sum()
devolucoes    = df_filtrado.loc[df_filtrado["TotalLinha"] < 0, "TotalLinha"].sum()
vendas_liq    = df_filtrado["TotalLinha"].sum()

qtd_bruta = df_filtrado.loc[df_filtrado["Quantidade"] > 0, "Quantidade"].sum()
qtd_dev   = df_filtrado.loc[df_filtrado["Quantidade"] < 0, "Quantidade"].sum()
qtd_liq   = df_filtrado["Quantidade"].sum()

def fmt_moeda_br(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_int_br(valor: float) -> str:
    try:
        return f"{int(round(valor)):,}".replace(",", ".")
    except:
        return "0"

c1, c2, c3 = st.columns(3)
c1.metric("💰 Vendas Brutas",          fmt_moeda_br(vendas_brutas))
c2.metric("↩️ Devoluções",             fmt_moeda_br(devolucoes))
c3.metric("🧮 Vendas Líquidas",        fmt_moeda_br(vendas_liq))

c4, c5, c6 = st.columns(3)
c4.metric("📦 Quantidade Bruta",       fmt_int_br(qtd_bruta))
c5.metric("↩️ Quantidade Devolvida",   fmt_int_br(qtd_dev))
c6.metric("🧮 Quantidade Líquida",     fmt_int_br(qtd_liq))

# ============================================================
# 📋 TABELA
# ============================================================
with st.expander("📋 Visualizar Dados Filtrados"):
    df_exib = df_filtrado.copy()
    df_exib["Data"] = df_exib["Data"].dt.strftime("%d/%m/%Y")
    st.dataframe(df_exib, use_container_width=True)

# ============================================================
# 🧭 ABAS
# ============================================================
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
# 📈 Evolução
# ============================================================
with abas[0]:
    st.subheader("📈 Evolução das Vendas ao Longo do Tempo")
    grafico_tempo = alt.Chart(df_filtrado).mark_line(point=True, color=COR_PRIMARIA).encode(
        x=alt.X("yearmonth(Data):T", title="Data"),
        y=alt.Y("sum(TotalLinha):Q", title="Total de Vendas (R$)"),
        color=alt.Color("CardCode:N", legend=alt.Legend(title="Cliente")),
        tooltip=[
            alt.Tooltip("yearmonth(Data):T", title="Data"),
            alt.Tooltip("sum(TotalLinha):Q", title="Total de Vendas", format=",.2f"),
            alt.Tooltip("CardCode:N", title="Cliente"),
        ],
    ).properties(width="container", height=420)
    st.altair_chart(grafico_tempo, use_container_width=True)

# ============================================================
# 🏆 Top Produtos (Quantidade)
# ============================================================
with abas[1]:
    st.subheader("🏆 Top Produtos (por Quantidade Líquida)")
    top_itens = (
        df_filtrado.groupby("ItemCode")["Quantidade"].sum().nlargest(10).reset_index()
    )
    chart_top = alt.Chart(top_itens).mark_bar(color=COR_PRIMARIA).encode(
        x=alt.X("Quantidade:Q", title="Quantidade Líquida"),
        y=alt.Y("ItemCode:N", sort="-x", title="ItemCode"),
        tooltip=["ItemCode", alt.Tooltip("Quantidade:Q", format=",.0f")],
    ).properties(width="container", height=420)
    st.altair_chart(chart_top, use_container_width=True)

# ============================================================
# 👤 Total por Cliente (Valor Líquido)
# ============================================================
with abas[2]:
    st.subheader("👤 Total de Vendas Líquidas por Cliente")
    total_por_cliente = df_filtrado.groupby("CardCode")["TotalLinha"].sum().reset_index()
    chart_cliente = alt.Chart(total_por_cliente).mark_bar(color=COR_PRIMARIA).encode(
        x=alt.X("TotalLinha:Q", title="Total (R$)"),
        y=alt.Y("CardCode:N", sort="-x", title="Cliente"),
        tooltip=[
            alt.Tooltip("CardCode:N", title="Cliente"),
            alt.Tooltip("TotalLinha:Q", title="Total", format=",.2f"),
        ],
    ).properties(width="container", height=420)
    st.altair_chart(chart_cliente, use_container_width=True)

# ============================================================
# 💳 Ticket Médio
# ============================================================
with abas[3]:
    st.subheader("💳 Ticket Médio por Cliente (Valor/Quantidade Líquida)")
    tm = df_filtrado.groupby("CardCode", as_index=False).agg(
        {"TotalLinha": "sum", "Quantidade": "sum"}
    )
    tm = tm[tm["Quantidade"] != 0]  # evita div zero
    tm["Ticket Médio"] = tm["TotalLinha"] / tm["Quantidade"]
    chart_ticket = alt.Chart(tm).mark_bar(color=COR_PRIMARIA).encode(
        x=alt.X("Ticket Médio:Q", title="Ticket Médio (R$)"),
        y=alt.Y("CardCode:N", sort="-x", title="Cliente"),
        tooltip=[
            alt.Tooltip("CardCode:N", title="Cliente"),
            alt.Tooltip("Ticket Médio:Q", format=",.2f"),
        ],
    ).properties(width="container", height=420)
    st.altair_chart(chart_ticket, use_container_width=True)

# ============================================================
# 📦 Por Origem (Quantidade Líquida)
# ============================================================
with abas[4]:
    st.subheader("📦 Distribuição por Origem (Quantidade Líquida)")
    por_origem = df_filtrado.groupby("Origem")["Quantidade"].sum().reset_index()
    chart_origem = alt.Chart(por_origem).mark_bar(color=COR_PRIMARIA).encode(
        x=alt.X("Quantidade:Q", title="Quantidade Líquida"),
        y=alt.Y("Origem:N", sort="-x", title="Origem"),
        tooltip=["Origem", alt.Tooltip("Quantidade:Q", format=",.0f")],
    ).properties(width="container", height=420)
    st.altair_chart(chart_origem, use_container_width=True)

# ============================================================
# 🧱 Vendas x Devoluções (Mês)
# ============================================================
with abas[5]:
    st.subheader("🧱 Vendas x Devoluções por Mês")
    df_mes = df_filtrado.copy()
    df_mes["Mes"] = df_mes["Data"].dt.to_period("M").astype(str)
    base = df_mes.groupby(["Mes", "TipoOperacao"])["TotalLinha"].sum().reset_index()

    chart_stack = alt.Chart(base).mark_bar().encode(
        x=alt.X("Mes:N", title="Mês", sort=None),
        y=alt.Y("TotalLinha:Q", title="Valor (R$)"),
        color=alt.Color(
            "TipoOperacao:N",
            scale=alt.Scale(domain=["Venda", "Devolução"], range=[COR_PRIMARIA, COR_ALERTA]),
            legend=alt.Legend(title="Tipo"),
        ),
        tooltip=[
            alt.Tooltip("Mes:N", title="Mês"),
            alt.Tooltip("TipoOperacao:N", title="Tipo"),
            alt.Tooltip("TotalLinha:Q", title="Valor", format=",.2f"),
        ],
    ).properties(width="container", height=420)

    st.altair_chart(chart_stack, use_container_width=True)

# ============================================================
# 📊 Crescimento por Cliente (mês a mês)
# ============================================================
with abas[6]:
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
        atual    = total_mes[total_mes["Mes"] == mes_atual].set_index("CardCode")
        anterior = total_mes[total_mes["Mes"] == mes_anterior].set_index("CardCode")

        cres = atual.join(anterior, lsuffix="_atual", rsuffix="_ant").fillna(0)
        cres["Crescimento_pct"] = (
            (cres["TotalLinha_atual"] - cres["TotalLinha_ant"]) /
            cres["TotalLinha_ant"].replace({0: pd.NA})
        ) * 100
        cres = cres.reset_index()
        cres["Mes_atual"] = mes_atual
        cres["Mes_ant"]   = mes_anterior

        # Tabela formatada
        tabela = cres.copy()
        tabela["Crescimento (%)"] = tabela["Crescimento_pct"].map(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "—"
        )
        tabela = tabela[["CardCode", "Mes_atual", "TotalLinha_atual", "Mes_ant", "TotalLinha_ant", "Crescimento (%)"]]

        # Gráfico
        graf = alt.Chart(cres).mark_bar().encode(
            x=alt.X("Crescimento_pct:Q", title="% Crescimento", axis=alt.Axis(format=".2f")),
            y=alt.Y("CardCode:N", sort="-x", title="Cliente"),
            color=alt.condition(alt.datum.Crescimento_pct > 0, alt.value(COR_SUCESSO), alt.value(COR_ALERTA)),
            tooltip=[
                alt.Tooltip("CardCode:N", title="Cliente"),
                alt.Tooltip("Crescimento_pct:Q", title="% Crescimento", format=".2f"),
                alt.Tooltip("TotalLinha_atual:Q", title=f"Vendas {mes_atual}", format=",.2f"),
                alt.Tooltip("TotalLinha_ant:Q", title=f"Vendas {mes_anterior}", format=",.2f"),
            ],
        ).properties(width="container", height=420)

        st.altair_chart(graf, use_container_width=True)
        st.dataframe(tabela.sort_values("Crescimento (%)", ascending=False).head(30), use_container_width=True)

# ============================================================
# ♻️ ANÁLISE DE DEVOLUÇÕES
# ============================================================
with abas[7]:
    st.subheader("♻️ Análise de Devoluções")

    # ---------- Índice de devolução geral ----------
    vendas_pos    = df_filtrado.loc[df_filtrado["TotalLinha"] > 0, "TotalLinha"].sum()
    devolucoes_abs= -df_filtrado.loc[df_filtrado["TotalLinha"] < 0, "TotalLinha"].sum()  # positivo
    indice_geral  = (devolucoes_abs / vendas_pos * 100) if vendas_pos > 0 else 0.0

    m1, m2 = st.columns(2)
    m1.metric("🔄 Índice de Devolução (período)", f"{indice_geral:.2f}%")
    m2.metric("↩️ Devoluções (R$)",             fmt_moeda_br(-devolucoes))  # devoluções é negativo

    st.markdown("---")

    # ---------- Top 10 clientes por devolução e índice ----------
    st.subheader("👥 Top Clientes por Devolução e Índice (%)")
    base_cli = df_filtrado.groupby(["CardCode"]).agg(
        vendas_brutas=("TotalLinha", lambda s: s[s > 0].sum()),
        devolucao_abs=("TotalLinha", lambda s: -s[s < 0].sum())
    ).reset_index()
    base_cli["indice_%"] = (base_cli["devolucao_abs"] / base_cli["vendas_brutas"] * 100).replace([pd.NA, pd.NaT], 0)
    base_cli = base_cli.fillna(0)

    top_cli_valor = base_cli.sort_values("devolucao_abs", ascending=False).head(10)
    chart_cli_valor = alt.Chart(top_cli_valor).mark_bar(color=COR_ALERTA).encode(
        x=alt.X("devolucao_abs:Q", title="Devolução (R$)"),
        y=alt.Y("CardCode:N", sort="-x", title="Cliente"),
        tooltip=[
            alt.Tooltip("CardCode:N", title="Cliente"),
            alt.Tooltip("vendas_brutas:Q", title="Vendas Brutas", format=",.2f"),
            alt.Tooltip("devolucao_abs:Q", title="Devolução", format=",.2f"),
            alt.Tooltip("indice_%:Q", title="Índice (%)", format=".2f"),
        ],
    ).properties(width="container", height=380)

    top_cli_indice = base_cli[base_cli["vendas_brutas"] > 0].sort_values("indice_%", ascending=False).head(10)
    chart_cli_indice = alt.Chart(top_cli_indice).mark_bar(color=COR_PRIMARIA).encode(
        x=alt.X("indice_%:Q", title="Índice de Devolução (%)", axis=alt.Axis(format=".2f")),
        y=alt.Y("CardCode:N", sort="-x", title="Cliente"),
        tooltip=[
            alt.Tooltip("CardCode:N", title="Cliente"),
            alt.Tooltip("vendas_brutas:Q", title="Vendas Brutas", format=",.2f"),
            alt.Tooltip("devolucao_abs:Q", title="Devolução", format=",.2f"),
            alt.Tooltip("indice_%:Q", title="Índice (%)", format=".2f"),
        ],
    ).properties(width="container", height=380)

    cA, cB = st.columns(2)
    cA.altair_chart(chart_cli_valor, use_container_width=True)
    cB.altair_chart(chart_cli_indice, use_container_width=True)

    with st.expander("🔎 Tabela completa de clientes (vendas, devolução e índice)"):
        tb = base_cli.copy()
        tb["Índice (%)"] = tb["indice_%"].map(lambda x: f"{x:.2f}%")
        tb = tb[["CardCode", "vendas_brutas", "devolucao_abs", "Índice (%)"]].rename(
            columns={"vendas_brutas": "Vendas Brutas", "devolucao_abs": "Devolução (R$)"}
        )
        st.dataframe(tb.sort_values("Devolução (R$)", ascending=False), use_container_width=True)

    st.markdown("---")

    # ---------- Top 10 itens mais devolvidos ----------
    st.subheader("📦 Top Itens mais Devolvidos (R$)")
    base_item = df_filtrado.groupby("ItemCode").agg(
        devolucao_abs=("TotalLinha", lambda s: -s[s < 0].sum())
    ).reset_index()
    base_item = base_item.sort_values("devolucao_abs", ascending=False).head(10)
    chart_item = alt.Chart(base_item).mark_bar(color=COR_ALERTA).encode(
        x=alt.X("devolucao_abs:Q", title="Devolução (R$)"),
        y=alt.Y("ItemCode:N", sort="-x", title="ItemCode"),
        tooltip=[
            alt.Tooltip("ItemCode:N", title="Item"),
            alt.Tooltip("devolucao_abs:Q", title="Devolução", format=",.2f"),
        ],
    ).properties(width="container", height=380)
    st.altair_chart(chart_item, use_container_width=True)

    st.markdown("---")

    # ---------- Índice de devolução por mês ----------
    st.subheader("🗓️ Índice de Devolução por Mês")
    df_mes = df_filtrado.copy()
    df_mes["Mes"] = df_mes["Data"].dt.to_period("M").astype(str)
    vendas_mes = df_mes[df_mes["TotalLinha"] > 0].groupby("Mes")["TotalLinha"].sum()
    dev_mes    = -df_mes[df_mes["TotalLinha"] < 0].groupby("Mes")["TotalLinha"].sum()
    devol_pct  = (dev_mes / vendas_mes * 100).fillna(0).reset_index()
    devol_pct.columns = ["Mes", "Indice_%"]

    chart_pct = alt.Chart(devol_pct).mark_bar(color=COR_PRIMARIA).encode(
        x=alt.X("Mes:N", title="Mês", sort=None),
        y=alt.Y("Indice_%:Q", title="Índice de Devolução (%)", axis=alt.Axis(format=".2f")),
        tooltip=[
            alt.Tooltip("Mes:N", title="Mês"),
            alt.Tooltip("Indice_%:Q", title="Índice (%)", format=".2f"),
        ],
    ).properties(width="container", height=380)
    st.altair_chart(chart_pct, use_container_width=True)

    with st.expander("📄 Tabela do Índice por Mês"):
        tbm = devol_pct.copy()
        tbm["Índice (%)"] = tbm["Indice_%"].map(lambda x: f"{x:.2f}%")
        st.dataframe(tbm[["Mes", "Índice (%)"]], use_container_width=True)
