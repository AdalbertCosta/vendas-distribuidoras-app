# 📊 Painel de Vendas - Distribuidora

Aplicação interativa desenvolvida em **Python + Streamlit**, para visualização e análise de dados de vendas de uma distribuidora, com base hospedada no GitHub.

---

## 🚀 **Deploy Online**
Acesse o painel online diretamente no Streamlit Cloud:  
👉 [https://vendas-distribuidoras-app.streamlit.app](https://vendas-distribuidoras-app.streamlit.app)

---

## 🧠 **Principais Recursos**
- Carregamento automático de base Excel via GitHub (`/data/Vendas_Dist.xlsx`);
- Atualização manual via botão no painel (“🔄 Atualizar dados”);
- KPIs dinâmicos e gráficos de evolução;
- Filtros interativos e visualização em tempo real;
- Armazenamento em cache com expiração automática.

---

## ⚙️ **Executando Localmente**

```bash
# Clone o repositório
git clone https://github.com/AdalbertCosta/vendas-distribuidoras-app.git
cd vendas-distribuidoras-app

# Crie e ative o ambiente virtual (opcional)
python -m venv venv
venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Execute o app
streamlit run vendas_app.py
