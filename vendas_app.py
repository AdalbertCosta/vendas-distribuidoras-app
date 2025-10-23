import pandas as pd
import streamlit as st
import altair as alt
import hashlib
import requests
import io
from datetime import datetime

# ============================================================
# 🎨 CONFIGURAÇÃO VISUAL
# ============================================================
st.set_page_config(page_title='Therapi Analytics - Vendas Distribuidora', layout='wide')

st.markdown("""
<style>
    body { background-color: #f7f9fb; font-family: 'Poppins', sans-serif; }
    .main-header {
        background-color: #095a7f; color: white; padding: 1rem 2rem;
        border-radius: 0 0 1rem 1rem; display: flex; justify-content: space-between;
        align-items: center;
    }
    .header-title { font-size: 1.6rem; font-weight: 600; }
    .logo { height: 50px; border-radius: 6px; }
    .metric-card {
        background: white; border-radius: 10px; text-align: center;
        padding: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .footer {
        margin-top: 2rem; text-align: center; font-size: 0.9rem;
        color: #555; border-top: 1px solid #ddd; padding-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 🔒 LOGIN SIMPLES
# ============================================================
USUARIOS = {"adalberto": "1234", "admin": "admin"}

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
        st.rerun()

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    autenticar()
    st.stop()
else:
    st.sidebar.info(f"Usuário: **{st.session_state['usuario']}**")
    logout()

# ============================================================
# 🧭 CABEÇALHO
# ============================================================
st.markdown("""
<div class='main-header'>
    <div class='header-title'>📊 Therapi Analytics — Painel de Vendas</div>
    <img src='https://i.imgur.com/hwAJpVn.png' class='logo'>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 📦 ARQUIVO DE DADOS
# ============================================================
URL_GITHUB = "https://github.com/AdalbertCosta/vendas-distribuidoras-app/raw/refs/heads/main/data/Vendas_Dist.xlsx"
nome_aba = "dist_novobi"
colunas_desejadas = [
    'Operacao', 'Data', 'CodEmpresa', 'CardCode', 'Origem', 'Utilizacao',
    'ItemCode', 'Quantidade', 'TotalLinha'
]

@st.cache_data
def carregar_dados():
    try:
        r = requests.get(URL_GITHUB)
        r.raise_for_status()
        bytes_io = io.BytesIO(r.content)
        df = pd.read_excel(bytes_io, sheet_name=nome_aba, usecols=colunas_desejadas, dtype=str)
        df.columns = df.columns.str.strip()
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df['TotalLinha'] = (
            df['TotalLinha'].astype(str)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .astype(float)
        )
        df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce')
        df = df.dropna(subset=['Data', 'TotalLinha', 'Quantidade'])
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar o arquivo: {e}")
        return pd.DataFrame()

df = carregar_dados()
if df.empty:
    st.warning("⚠️ Nenhum dado carregado. Verifique o Excel.")
    st.stop()

# ============================================================
# 🎛️ FILTROS
# ============================================================
st.sidebar.header("🧭 Filtros de Visualização")
cardcodes = st.sidebar.multiselect(
    '🔍 Selecione cliente(s):',
    options=sorted(df['CardCode'].dropna().unique()),
    placeholder='Digite ou selecione...'
)

min_data, max_data = df['Data'].min(), df['Data'].max()
data_inicio, data_fim = st.sidebar.date_input("📅 Intervalo de datas:",
                                              [min_data, max_data],
                                              min_value=min_data, max_value=max_data)

if not cardcodes:
    st.warning("⚠️ Selecione ao menos um cliente para começar.")
    st.stop()

df_filtrado = df[
    (df['CardCode'].isin(cardcodes)) &
    (df['Data'] >= pd.to_datetime(data_inicio)) &
    (df['Data'] <= pd.to_datetime(data_fim))
].copy()

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
    st.stop()

# ============================================================
# 📊 MÉTRICAS GERAIS
# ============================================================
col1, col2 = st.columns(2)
col1.markdown(f"<div class='metric-card'><h4>💰 Total de Vendas</h4><h2>R$ {df_filtrado['TotalLinha'].sum():,.2f}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-card'><h4>📦 Quantidade Total</h4><h2>{df_filtrado['Quantidade'].sum():,.0f}</h2></div>", unsafe_allow_html=True)

st.markdown(f"🕒 **Última atualização:** {datetime.now().strftime('%d/%m/%Y - %H:%M')} (via GitHub)")

# ============================================================
# 📈 ABAS ANALÍTICAS
# ============================================================
abas = st.tabs(['📈 Evolução de Vendas', '🏆 Top Produtos', '👤 Total por Cliente', '💳 Ticket Médio', '📦 Por Origem'])

# 📈 Evolução das Vendas
with abas[0]:
    st.subheader("📈 Evolução de Vendas ao Longo do Tempo")
    grafico_tempo = alt.Chart(df_filtrado).mark_line(point=True, color="#12ac68").encode(
        x=alt.X('yearmonth(Data):T', title='Data'),
        y=alt.Y('sum(TotalLinha):Q', title='Total de Vendas (R$)'),
        color='CardCode:N',
        tooltip=[
            alt.Tooltip('yearmonth(Data):T', title='Data'),
            alt.Tooltip('sum(TotalLinha):Q', title='Total de Vendas', format=',.2f'),
            alt.Tooltip('CardCode:N', title='Cliente')
        ]
    ).properties(height=400)
    st.altair_chart(grafico_tempo, use_container_width=True)

# 🏆 Top Produtos
with abas[1]:
    st.subheader("🏆 Top Produtos Vendidos")
    top_itens = df_filtrado.groupby('ItemCode')['Quantidade'].sum().nlargest(10).reset_index()
    chart_top = alt.Chart(top_itens).mark_bar(color="#095a7f").encode(
        x=alt.X('Quantidade:Q'),
        y=alt.Y('ItemCode:N', sort='-x'),
        tooltip=['ItemCode', 'Quantidade']
    ).properties(height=400)
    st.altair_chart(chart_top, use_container_width=True)

# 👤 Total por Cliente
with abas[2]:
    st.subheader("👤 Total de Vendas por Cliente")
    total_cliente = df_filtrado.groupby('CardCode')['TotalLinha'].sum().reset_index()
    chart_cliente = alt.Chart(total_cliente).mark_bar(color="#12ac68").encode(
        x=alt.X('TotalLinha:Q', title='Total (R$)'),
        y=alt.Y('CardCode:N', sort='-x'),
        tooltip=[
            alt.Tooltip('CardCode:N', title='Cliente'),
            alt.Tooltip('TotalLinha:Q', title='Total', format=',.2f')
        ]
    ).properties(height=400)
    st.altair_chart(chart_cliente, use_container_width=True)

# 💳 Ticket Médio
with abas[3]:
    st.subheader("💳 Ticket Médio por Cliente")
    ticket_medio = (
        df_filtrado.groupby('CardCode', as_index=False)
        .agg({'TotalLinha': 'sum', 'Quantidade': 'sum'})
    )
    ticket_medio = ticket_medio[ticket_medio['Quantidade'] > 0]
    ticket_medio['Ticket Médio'] = ticket_medio['TotalLinha'] / ticket_medio['Quantidade']
    ticket_medio = ticket_medio[['CardCode', 'Ticket Médio']].sort_values(by='Ticket Médio', ascending=False)
    chart_ticket = alt.Chart(ticket_medio).mark_bar(color="#5BA77C").encode(
        x=alt.X('Ticket Médio:Q', title='R$'),
        y=alt.Y('CardCode:N', sort='-x'),
        tooltip=[alt.Tooltip('CardCode:N'), alt.Tooltip('Ticket Médio:Q', format=',.2f')]
    ).properties(height=400)
    st.altair_chart(chart_ticket, use_container_width=True)

# 📦 Por Origem
with abas[4]:
    st.subheader("📦 Distribuição por Origem")
    quant_origem = df_filtrado.groupby('Origem')['Quantidade'].sum().reset_index()
    chart_origem = alt.Chart(quant_origem).mark_bar(color="#095a7f").encode(
        x=alt.X('Quantidade:Q', title='Qtd Total'),
        y=alt.Y('Origem:N', sort='-x'),
        tooltip=['Origem', 'Quantidade']
    ).properties(height=400)
    st.altair_chart(chart_origem, use_container_width=True)

# ============================================================
# 🧾 TABELA FINAL
# ============================================================
st.subheader("📋 Dados Filtrados")
df_exib = df_filtrado.copy()
df_exib['Data'] = df_exib['Data'].dt.strftime('%d/%m/%Y')
st.dataframe(df_exib, use_container_width=True)

# ============================================================
# ⚙️ RODAPÉ
# ============================================================
st.markdown("""
<div class='footer'>
    Desenvolvido por <b>Adalberto Costa</b> • Therapi Analytics © 2025<br>
    Sistema de visualização de dados — Streamlit + Power BI DNA
</div>
""", unsafe_allow_html=True)


# ============================================================
# 🧠 RESUMO EXECUTIVO
# ============================================================
with abas[0]:
    st.subheader("📊 Resumo Executivo — Insights Automáticos")

    total = df_filtrado['TotalLinha'].sum()
    qtd = df_filtrado['Quantidade'].sum()

    # ====== Análise mensal ======
    df_mes = df_filtrado.copy()
    df_mes['Mes'] = df_mes['Data'].dt.to_period('M')
    vendas_mes = df_mes.groupby('Mes')['TotalLinha'].sum().reset_index()
    vendas_mes['Mes'] = vendas_mes['Mes'].astype(str)

    if len(vendas_mes) > 1:
        crescimento = (vendas_mes.iloc[-1, 1] - vendas_mes.iloc[-2, 1]) / vendas_mes.iloc[-2, 1] * 100
        direcao = "⬆️ Crescimento" if crescimento > 0 else "⬇️ Queda"
        cor = "#12ac68" if crescimento > 0 else "#b94a48"
    else:
        crescimento = 0
        direcao = "Estável"
        cor = "#999999"

    # ====== Indicadores de destaque ======
    ticket_medio = total / qtd if qtd > 0 else 0
    cliente_top = df_filtrado.groupby('CardCode')['TotalLinha'].sum().nlargest(1).index[0]
    produto_top = df_filtrado.groupby('ItemCode')['Quantidade'].sum().nlargest(1).index[0]

    # ====== Texto analítico ======
    st.markdown(f"""
    💬 **Resumo Automático**
    - Faturamento total no período: **R$ {total:,.2f}**
    - Quantidade total vendida: **{qtd:,.0f} unidades**
    - Ticket médio: **R$ {ticket_medio:,.2f}**
    - Cliente destaque: **{cliente_top}**
    - Produto destaque: **{produto_top}**
    - Variação em relação ao mês anterior: **{direcao} de {abs(crescimento):.2f}%**
    """, unsafe_allow_html=True)

    # ====== Mini gráfico de tendência + projeção ======
    st.markdown("---")
    st.subheader("📈 Tendência Mensal de Faturamento e Projeção")

    base_chart = alt.Chart(vendas_mes).mark_line(point=True, strokeWidth=3, color=cor).encode(
        x=alt.X('Mes:N', title='Mês'),
        y=alt.Y('TotalLinha:Q', title='Faturamento (R$)', axis=alt.Axis(format=',.0f')),
        tooltip=[
            alt.Tooltip('Mes:N', title='Mês'),
            alt.Tooltip('TotalLinha:Q', title='Faturamento', format=',.2f')
        ]
    )

    # Projeção de regressão linear
    regressao = alt.Chart(vendas_mes).transform_regression(
        'month(Mes)', 'TotalLinha', method='linear', extent=[0, len(vendas_mes)+2]
    ).mark_line(color='orange', strokeDash=[6, 3]).encode(
        x=alt.X('Mes:N', title='Mês'),
        y='TotalLinha:Q'
    )

    # Combina gráfico real + linha de tendência
    chart_tendencia = (base_chart + regressao).properties(height=350)
    st.altair_chart(chart_tendencia, use_container_width=True)

    # ====== Frase final de destaque ======
    if crescimento > 0:
        st.success(f"✅ Excelente desempenho! O último mês apresentou **{crescimento:.2f}% de crescimento** em relação ao anterior. A tendência indica **continuidade positiva** nos próximos meses.")
    elif crescimento < 0:
        st.error(f"⚠️ Atenção: houve **queda de {abs(crescimento):.2f}%** no faturamento em relação ao mês anterior. A tendência indica **necessidade de ação corretiva** para recuperação.")
    else:
        st.info("ℹ️ O faturamento permaneceu estável. A projeção sugere **leve oscilação neutra** nos próximos meses.")
