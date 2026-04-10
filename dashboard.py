import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

# 1. Configurações de Layout
st.set_page_config(page_title="Sentinela Varejo", page_icon="🛡️", layout="wide")

# --- SISTEMA DE LOGIN ---
def realizar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        _, col_central, _ = st.columns([1, 2, 1])
        with col_central:
            st.markdown("## 🛡️ Sentinela Varejo")
            st.info("Portal de Auditoria e Gestão de Fraudes")
            
            with st.form("form_acesso"):
                usuario_input = st.text_input("ID da Empresa")
                senha_input = st.text_input("Senha de Acesso", type="password")
                botao_entrar = st.form_submit_button("Entrar no Painel")

                if botao_entrar:
                    try:
                        # Validação via Streamlit Secrets
                        if usuario_input in st.secrets["usuarios"] and senha_input == st.secrets["usuarios"][usuario_input]:
                            st.session_state.clear()
                            st.session_state.logado = True
                            st.session_state.usuario = usuario_input
                            st.rerun()
                        else:
                            st.error("⚠️ Usuário ou senha inválidos.")
                    except KeyError:
                        st.error("❌ Erro: Configuração de segredos (Secrets) não encontrada.")
        return False
    return True

# --- INÍCIO DO CONTEÚDO PROTEGIDO ---
if realizar_login():
    
    # Barra Lateral
    st.sidebar.title(f"🏢 {st.session_state.usuario.upper()}")
    if st.sidebar.button("Encerrar Sessão (Sair)"):
        st.session_state.logado = False
        st.session_state.clear()
        st.rerun()

    # 2. Carregamento de Dados com Cache e Isolamento
    @st.cache_data
    def buscar_arquivo_completo():
        # Lê o arquivo bruto do repositório
        df_bruto = pd.read_csv('vendas_10k.csv')
        
        # Tipagem e Limpeza que se aplica a todos
        df_bruto['ID_Transacao'] = df_bruto['ID_Transacao'].astype(str)
        df_bruto['ID_Operador'] = df_bruto['ID_Operador'].astype(str)
        df_bruto['Data_Hora'] = pd.to_datetime(df_bruto['Data_Hora'])
        df_bruto['Hora_Venda'] = df_bruto['Data_Hora'].dt.hour
        df_bruto['Perc_Desconto'] = (df_bruto['Desconto_Aplicado'] / (df_bruto['Valor_Total'] + df_bruto['Desconto_Aplicado']) * 100).fillna(0)
        return df_bruto

    # Obtém o DataFrame completo (do cache)
    df_todos = buscar_arquivo_completo()

    # FILTRO DE ISOLAMENTO (Tenancy)
    if 'Empresa' in df_todos.columns:
        # Filtra apenas o que pertence ao usuário logado
        dados_empresa = df_todos[df_todos['Empresa'] == st.session_state.usuario].copy()
    else:
        dados_empresa = df_todos.copy()
        st.sidebar.warning("⚠️ Coluna 'Empresa' ausente no CSV.")

    # 3. Motor de Inteligência Artificial
    def detectar_anomalias(df_entrada):
        if df_entrada.empty: return df_entrada
        
        colunas_ia = ['Hora_Venda', 'Quantidade', 'Preco_Unitario', 'Desconto_Aplicado', 'Valor_Total', 'Metodo_Pagamento']
        df_ia = df_entrada[colunas_ia].copy()
        
        le = LabelEncoder()
        df_ia['Metodo_Pagamento'] = le.fit_transform(df_ia['Metodo_Pagamento'])
        
        # Algoritmo de Detecção
        modelo = IsolationForest(contamination=0.02, random_state=42)
        modelo.fit(df_ia)
        
        df_entrada['Eh_Anomalia'] = modelo.predict(df_ia)
        return df_entrada

    # 4. Interface em Abas
    aba_auditoria, aba_gerencial = st.tabs(["🔍 Auditoria de Fraudes", "📊 Visão Gerencial"])

    with aba_auditoria:
        st.sidebar.divider()
        if st.sidebar.button("Executar Varredura Inteligente"):
            with st.spinner('IA analisando padrões...'):
                res = detectar_anomalias(dados_empresa)
                st.session_state['lista_fraudes'] = res[res['Eh_Anomalia'] == -1].copy()
                st.session_state['processado'] = True

        if st.session_state.get('processado'):
            fraudes = st.session_state['lista_fraudes']
            st.success(f"Varredura concluída! {len(fraudes)} transações suspeitas.")
            
            st.subheader("⚠️ Relatório de Alertas Críticos")
            col_v = ['ID_Transacao', 'ID_Operador', 'Descricao_Produto', 'Quantidade', 'Preco_Unitario', 'Desconto_Aplicado', 'Valor_Total', 'Hora_Venda']
            st.dataframe(fraudes[col_v].sort_values(by='Desconto_Aplicado', ascending=False), use_container_width=True)
            
            st.divider()
            st.subheader("🧠 Perfil de Risco (Análise de Descontos)")
            c1, c2 = st.columns([1, 2])
            with c1:
                st.info("Concentração de descontos nas anomalias identificadas.")
            with c2:
                fig, ax = plt.subplots(figsize=(8, 3))
                fraudes['Desconto_Aplicado'].hist(bins=20, ax=ax, color='red', alpha=0.7)
                st.pyplot(fig)
        else:
            st.info("Utilize o botão lateral para iniciar a auditoria.")

    with aba_gerencial:
        if not dados_empresa.empty:
            st.subheader(f"📊 Painel Gerencial - {st.session_state.usuario.upper()}")
            
            # Métricas em colunas
            m1, m2, m3 = st.columns(3)
            m1.metric("Faturamento Total", f"R$ {dados_empresa['Valor_Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            m2.metric("Ticket Médio", f"R$ {dados_empresa.groupby('ID_Transacao')['Valor_Total'].sum().mean():.2f}".replace(".", ","))
            m3.metric("Média Desconto", f"{dados_empresa['Perc_Desconto'].mean():.2f}%")
            
            st.divider()
            
            # Gráficos de BI
            g1, g2 = st.columns(2)
            with g1:
                st.write("**🏆 Top 10 Produtos**")
                st.bar_chart(dados_empresa.groupby('Descricao_Produto')['Quantidade'].sum().sort_values(ascending=False).head(10))
            with g2:
                st.write("**💰 Faturamento por Pagamento**")
                st.bar_chart(dados_empresa.groupby('Metodo_Pagamento')['Valor_Total'].sum())

            # Tabela de Performance
            st.write("**👥 Produtividade por Operador**")
            fatur = dados_empresa.groupby('ID_Operador')['Valor_Total'].sum()
            qtd = dados_empresa.groupby('ID_Operador')['ID_Transacao'].nunique()
            tabela = pd.DataFrame({'Vendas': qtd, 'Total': fatur}).reset_index().sort_values(by='Total', ascending=False)
            tabela['Total'] = tabela['Total'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.table(tabela)
        else:
            st.error("Nenhum dado localizado para esta empresa. Verifique o arquivo CSV.")