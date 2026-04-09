import streamlit as st
import pandas as pd
from pycaret.anomaly import load_model, predict_model
import shap
import matplotlib.pyplot as plt

# 1. Configuração de Página
st.set_page_config(page_title="Auditoria SaaS", page_icon="🛡️", layout="wide")
st.title("🛡️ Sistema de Auditoria e Gestão Inteligente")

# 2. Carregamento de Dados e Cache do Modelo
@st.cache_data
def load_data():
    df = pd.read_csv('vendas_10k.csv')
    df['Data_Hora'] = pd.to_datetime(df['Data_Hora'])
    df['Hora_Venda'] = df['Data_Hora'].dt.hour
    df['Perc_Desconto'] = (df['Desconto_Aplicado'] / (df['Valor_Total'] + df['Desconto_Aplicado']) * 100).fillna(0)
    return df

@st.cache_resource
def get_model():
    return load_model('modelo_auditoria_varejo')

df = load_data()

# Abas de navegação
aba_auditoria, aba_gerencial = st.tabs(["🔍 Auditoria de Fraudes", "📊 Visão Gerencial"])

# --- ABA 1: AUDITORIA (RESTAURADA E COMPLETA) ---
with aba_auditoria:
    st.sidebar.header("Painel de Controle")
    
    if st.sidebar.button("Executar Varredura Diária"):
        with st.spinner('Analisando padrões de fraude...'):
            modelo = get_model()
            resultados = predict_model(modelo, data=df)
            limiar = resultados['Anomaly_Score'].quantile(0.98) 
            fraudes = resultados[resultados['Anomaly_Score'] >= limiar]
            
            res_final = df.iloc[fraudes.index].copy()
            res_final['Nível_Suspeita'] = fraudes['Anomaly_Score']
            
            st.session_state['df_fraudes'] = res_final
            st.session_state['ia_pronta'] = True

    if st.session_state.get('ia_pronta'):
        res_final = st.session_state['df_fraudes']
        
        c_aud1, c_aud2 = st.columns(2)
        c_aud1.metric("Transações Analisadas", len(df))
        c_aud2.metric("Alertas Críticos", len(res_final))
        
        st.subheader("⚠️ Relatório de Transações Suspeitas")
        # RESTAURADO: Colunas ID_Operador, Desconto_Aplicado e Valor_Total lado a lado
        cols_relatorio = ['ID_Transacao', 'ID_Operador', 'Hora_Venda', 'Metodo_Pagamento', 'Desconto_Aplicado', 'Valor_Total', 'Nível_Suspeita']
        st.dataframe(res_final[cols_relatorio].sort_values(by='Nível_Suspeita', ascending=False), use_container_width=True)

        st.divider()

        # INVESTIGAÇÃO SHAP
        st.subheader("🧠 Justificativa Detalhada da IA")
        lista_ids = res_final.sort_values(by='Nível_Suspeita', ascending=False)['ID_Transacao'].tolist()
        id_selecionado = st.selectbox("Selecione o ID para diagnóstico:", lista_ids)

        if id_selecionado:
            idx = df[df['ID_Transacao'] == id_selecionado].index[0]
            col_tr = ['Hora_Venda', 'Quantidade', 'Preco_Unitario', 'Desconto_Aplicado', 'Valor_Total', 'Metodo_Pagamento']
            
            modelo = get_model()
            pipeline, model_iso = modelo[:-1], modelo[-1]
            lin_transf = pipeline.transform(df.iloc[[idx]][col_tr])
            
            explainer = shap.TreeExplainer(model_iso)
            shap_v = explainer.shap_values(lin_transf)
            
            plt.clf()
            fig, ax = plt.subplots(figsize=(10, 4))
            shap.plots.bar(shap.Explanation(values=shap_v[0], data=lin_transf.iloc[0], feature_names=lin_transf.columns), show=False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

# --- ABA 2: VISÃO GERENCIAL ---
with aba_gerencial:
    st.subheader("📈 Performance e Comportamento da Loja")
    
    faturamento = df['Valor_Total'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Faturamento Total", f"R$ {faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c2.metric("Média de Desconto", f"{df['Perc_Desconto'].mean():.2f}%")
    c3.metric("Ticket Médio", f"R$ {df.groupby('ID_Transacao')['Valor_Total'].sum().mean():.2f}".replace(".", ","))

    st.divider()

    g1, g2 = st.columns(2)
    with g1:
        st.write("**🏆 Top Produtos (Volume)**")
        st.bar_chart(df.groupby('Descricao_Produto')['Quantidade'].sum().sort_values(ascending=False).head(10))
    with g2:
        st.write("**💰 Faturamento por Método**")
        st.bar_chart(df.groupby('Metodo_Pagamento')['Valor_Total'].sum())

    st.write("**📊 Fechamento por Operador**")
    fatur_op = df.groupby('ID_Operador')['Valor_Total'].sum()
    qtd_op = df.groupby('ID_Operador')['ID_Transacao'].nunique()
    fech = pd.DataFrame({'Qtd_Operações': qtd_op, 'Faturamento_Total': fatur_op}).reset_index().sort_values(by='Faturamento_Total', ascending=False)
    fech['Faturamento_Total'] = fech['Faturamento_Total'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.table(fech)