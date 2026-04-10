import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

st.set_page_config(page_title="Sentinela Varejo", page_icon="🛡️", layout="wide")

# --- LOGIN ---
def login():
    if "logado" not in st.session_state: st.session_state.logado = False
    if not st.session_state.logado:
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.title("🛡️ Sentinela Varejo")
            with st.form("l"):
                u = st.text_input("Usuário (Empresa)")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if u in st.secrets["usuarios"] and s == st.secrets["usuarios"][u]:
                        st.session_state.logado, st.session_state.usuario = True, u
                        st.rerun()
                    else: st.error("Erro de login")
        return False
    return True

if login():
    st.sidebar.title(f"🏢 {st.session_state.usuario.upper()}")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    @st.cache_data
    def load_all():
        df = pd.read_csv('vendas_10k.csv')
        # Normaliza nomes de colunas para evitar o erro de "Coluna Ausente"
        df.columns = [c.capitalize() for c in df.columns]
        
        df['ID_Transacao'] = df['ID_Transacao'].astype(str)
        df['ID_Operador'] = df['ID_Operador'].astype(str)
        df['Data_Hora'] = pd.to_datetime(df['Data_Hora'])
        df['Hora_Venda'] = df['Data_Hora'].dt.hour
        return df

    full_df = load_all()
    
    # FILTRO DE SEGURANÇA (Multi-empresa)
    if 'Empresa' in full_df.columns:
        df_loja = full_df[full_df['Empresa'].str.lower() == st.session_state.usuario.lower()].copy()
    else:
        df_loja = full_df.copy()
        st.sidebar.error("⚠️ Coluna 'Empresa' não encontrada!")

    # --- ABAS ---
    aba1, aba2 = st.tabs(["🔍 Auditoria IA", "📊 Gerencial"])

    with aba1:
        if st.sidebar.button("Rodar Auditoria"):
            with st.spinner("IA Analisando..."):
                df_ia = df_loja[['Hora_Venda', 'Quantidade', 'Preco_Unitario', 'Desconto_Aplicado', 'Valor_Total']].copy()
                modelo = IsolationForest(contamination=0.02, random_state=42)
                df_loja['Anomalia'] = modelo.fit_predict(df_ia)
                st.session_state.fraudes = df_loja[df_loja['Anomalia'] == -1].copy()
                st.session_state.pronto = True
        
        if st.session_state.get('pronto'):
            st.success(f"Detectadas {len(st.session_state.fraudes)} suspeitas")
            st.dataframe(st.session_state.fraudes.sort_values(by='Desconto_Aplicado', ascending=False))
        else:
            st.info("Aguardando varredura...")

    with aba2:
        st.subheader("Faturamento e Performance")
        c1, c2 = st.columns(2)
        c1.metric("Total", f"R$ {df_loja['Valor_Total'].sum():,.2f}")
        c2.metric("Vendas", len(df_loja))
        st.bar_chart(df_loja.groupby('Descricao_Produto')['Quantidade'].sum())