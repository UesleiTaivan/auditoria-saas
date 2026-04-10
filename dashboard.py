import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

# 1. Configuração e Estilo
st.set_page_config(page_title="Sentinela Varejo", page_icon="🛡️", layout="wide")
st.title("🛡️ Sentinela Varejo: Auditoria & Gestão")

# 2. Carregando os Dados
@st.cache_data
def load_data():
    df = pd.read_csv('vendas_10k.csv')
    df['Data_Hora'] = pd.to_datetime(df['Data_Hora'])
    df['Hora_Venda'] = df['Data_Hora'].dt.hour
    df['Perc_Desconto'] = (df['Desconto_Aplicado'] / (df['Valor_Total'] + df['Desconto_Aplicado']) * 100).fillna(0)
    return df

df = load_data()

# 3. Motor de IA Moderno (Scikit-Learn)
def executar_ia(dados):
    df_ia = dados[['Hora_Venda', 'Quantidade', 'Preco_Unitario', 'Desconto_Aplicado', 'Valor_Total', 'Metodo_Pagamento']].copy()
    le = LabelEncoder()
    df_ia['Metodo_Pagamento'] = le.fit_transform(df_ia['Metodo_Pagamento'])
    
    # Isolation Forest: Algoritmo de ponta para detectar anomalias
    modelo = IsolationForest(contamination=0.02, random_state=42)
    modelo.fit(df_ia)
    
    dados['Anomaly_Score'] = modelo.decision_function(df_ia)
    dados['Eh_Anomalia'] = modelo.predict(df_ia) # -1 para suspeito, 1 para normal
    return dados

# Interface em Abas
aba_auditoria, aba_gerencial = st.tabs(["🔍 Auditoria de Fraudes", "📊 Visão Gerencial"])

# --- ABA 1: AUDITORIA (COM DESCRIÇÃO DO PRODUTO) ---
with aba_auditoria:
    if st.sidebar.button("Executar Varredura Inteligente"):
        with st.spinner('IA analisando padrões comportamentais...'):
            res = executar_ia(df)
            st.session_state['fraudes'] = res[res['Eh_Anomalia'] == -1].copy()
            st.session_state['ia_pronta'] = True

    if st.session_state.get('ia_pronta'):
        fraudes = st.session_state['fraudes']
        st.success(f"Varredura concluída! {len(fraudes)} transações suspeitas identificadas.")
        
        st.subheader("⚠️ Relatório de Transações Suspeitas")
        
        # ADICIONADA: 'Descricao_Produto' e 'Quantidade' para conferência matemática
        cols_auditoria = [
            'ID_Transacao', 
            'ID_Operador', 
            'Descricao_Produto', 
            'Quantidade', 
            'Preco_Unitario',
            'Desconto_Aplicado', 
            'Valor_Total',
            'Hora_Venda'
        ]
        
        st.dataframe(
            fraudes[cols_auditoria].sort_values(by='Desconto_Aplicado', ascending=False), 
            use_container_width=True
        )

        st.divider()
        st.subheader("🧠 Por que estes itens foram marcados?")
        
        # Explicação estratégica para o dono do mercado
        st.info("""
        **Dica de Auditoria:** Se uma transação tem 'Desconto 0' mas foi marcada pela IA, verifique se a multiplicação de 
        (Quantidade x Preço Unitário) condiz com o Valor Total. A IA detecta quando o preço do produto foi alterado 
        manualmente no caixa sem autorização.
        """)

# --- ABA 2: VISÃO GERENCIAL ---
with aba_gerencial:
    st.subheader("📈 Performance e Comportamento da Loja")
    
    faturamento_total = df['Valor_Total'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c2.metric("Ticket Médio", f"R$ {df.groupby('ID_Transacao')['Valor_Total'].sum().mean():.2f}".replace(".", ","))
    c3.metric("Média de Desconto", f"{df['Perc_Desconto'].mean():.2f}%")

    st.divider()

    # Linha de Gráficos de BI
    g1, g2 = st.columns(2)
    with g1:
        st.write("**🏆 Top 10 Produtos (Volume)**")
        st.bar_chart(df.groupby('Descricao_Produto')['Quantidade'].sum().sort_values(ascending=False).head(10))
    
    with g2:
        st.write("**💰 Faturamento por Método de Pagamento**")
        fatur_met = df.groupby('Metodo_Pagamento')['Valor_Total'].sum()
        st.bar_chart(fatur_met)

    # Tabela de Produtividade (Restaurada)
    st.write("**📊 Fechamento Detalhado por Operador**")
    fatur_op = df.groupby('ID_Operador')['Valor_Total'].sum()
    qtd_op = df.groupby('ID_Operador')['ID_Transacao'].nunique()
    
    fech_completo = pd.DataFrame({
        'Qtd_Operações': qtd_op,
        'Faturamento_Total': fatur_op
    }).reset_index().sort_values(by='Faturamento_Total', ascending=False)

    fech_completo['Faturamento_Total'] = fech_completo['Faturamento_Total'].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    st.table(fech_completo)