import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

# 1. Configurações Iniciais de Layout
st.set_page_config(page_title="Sentinela Varejo", page_icon="🛡️", layout="wide")

# --- FUNÇÃO DE LOGIN ---
def realizar_login():
    # Inicializa a variável de estado de login se ela não existir
    if "logado" not in st.session_state:
        st.session_state.logado = False

    # Se NÃO estiver logado, mostra a tela de login
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
                    # Tenta validar no Streamlit Secrets
                    try:
                        if usuario_input in st.secrets["usuarios"] and senha_input == st.secrets["usuarios"][usuario_input]:
                            st.session_state.logado = True
                            st.session_state.usuario = usuario_input
                            st.rerun()
                        else:
                            st.error("⚠️ Usuário ou senha inválidos.")
                    except KeyError:
                        st.error("❌ Erro: Lista de usuários não encontrada no Secrets.")
        return False
    return True

# --- FLUXO PRINCIPAL ---
# O código abaixo só será executado se realizar_login() retornar True
if realizar_login():
    
    # Barra Lateral (Sidebar)
    st.sidebar.title(f"🏢 {st.session_state.usuario.upper()}")
    if st.sidebar.button("Encerrar Sessão (Sair)"):
        st.session_state.logado = False
        st.rerun()

    # 2. Função de Carregamento de Dados (AJUSTADA)
    @st.cache_data
    def load_data(usuario_logado):
        # Forçamos a leitura do CSV original toda vez que o usuário mudar
        df = pd.read_csv('vendas_10k.csv')
        
        # Limpeza e Tipagem
        df['ID_Transacao'] = df['ID_Transacao'].astype(str)
        df['ID_Operador'] = df['ID_Operador'].astype(str)
        df['Data_Hora'] = pd.to_datetime(df['Data_Hora'])
        df['Hora_Venda'] = df['Data_Hora'].dt.hour
        df['Perc_Desconto'] = (df['Desconto_Aplicado'] / (df['Valor_Total'] + df['Desconto_Aplicado']) * 100).fillna(0)
        
        # IMPORTANTE: O filtro deve acontecer aqui dentro para o cache entender a separação
        if 'Empresa' in df.columns:
            # Filtramos apenas os dados da empresa que acabou de logar
            df_filtrado = df[df['Empresa'] == usuario_logado].copy()
            return df_filtrado
        
        return df

    # Chamada da função (garanta que está passando o usuário atual)
    dados_empresa = load_data(st.session_state.usuario)
    

    # 3. Motor de IA (Isolation Forest)
    def detectar_anomalias(df_entrada):
        if df_entrada.empty: return df_entrada
        
        # Prepara colunas para a IA
        colunas_ia = ['Hora_Venda', 'Quantidade', 'Preco_Unitario', 'Desconto_Aplicado', 'Valor_Total', 'Metodo_Pagamento']
        df_ia = df_entrada[colunas_ia].copy()
        
        # Transforma texto do Pagamento em número
        le = LabelEncoder()
        df_ia['Metodo_Pagamento'] = le.fit_transform(df_ia['Metodo_Pagamento'])
        
        # Modelo Isolation Forest
        modelo = IsolationForest(contamination=0.02, random_state=42)
        modelo.fit(df_ia)
        
        df_entrada['Anomaly_Score'] = modelo.decision_function(df_ia)
        df_entrada['Eh_Anomalia'] = modelo.predict(df_ia)
        return df_entrada

    # 4. Interface em Abas
    aba_auditoria, aba_gerencial = st.tabs(["🔍 Auditoria de Fraudes", "📊 Visão Gerencial"])

    with aba_auditoria:
        st.sidebar.divider()
        if st.sidebar.button("Executar Varredura Inteligente"):
            with st.spinner('IA analisando padrões comportamentais...'):
                res = detectar_anomalias(dados_empresa)
                st.session_state['lista_fraudes'] = res[res['Eh_Anomalia'] == -1].copy()
                st.session_state['processado'] = True

        if st.session_state.get('processado'):
            fraudes = st.session_state['lista_fraudes']
            st.success(f"Varredura concluída! {len(fraudes)} transações suspeitas.")
            
            st.subheader("⚠️ Relatório de Alertas Críticos")
            colunas_v = ['ID_Transacao', 'ID_Operador', 'Descricao_Produto', 'Quantidade', 'Preco_Unitario', 'Desconto_Aplicado', 'Valor_Total', 'Hora_Venda']
            st.dataframe(fraudes[colunas_v].sort_values(by='Desconto_Aplicado', ascending=False), use_container_width=True)
            
            st.divider()
            st.subheader("🧠 Análise do Perfil de Risco")
            c1, c2 = st.columns([1, 2])
            with c1:
                st.info("O gráfico mostra a concentração de descontos nas transações que a IA isolou como anormais.")
            with c2:
                fig, ax = plt.subplots(figsize=(8, 3))
                fraudes['Desconto_Aplicado'].hist(bins=20, ax=ax, color='red', alpha=0.7)
                st.pyplot(fig)
        else:
            st.write("Aguardando comando de varredura...")

    with aba_gerencial:
        if not dados_empresa.empty:
            st.subheader(f"📊 Dashboard Gerencial - {st.session_state.usuario.upper()}")
            
            # Métricas
            m1, m2, m3 = st.columns(3)
            m1.metric("Faturamento Total", f"R$ {dados_empresa['Valor_Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            m2.metric("Ticket Médio", f"R$ {dados_empresa.groupby('ID_Transacao')['Valor_Total'].sum().mean():.2f}".replace(".", ","))
            m3.metric("Média Desconto", f"{dados_empresa['Perc_Desconto'].mean():.2f}%")
            
            st.divider()
            
            # Gráficos
            g1, g2 = st.columns(2)
            with g1:
                st.write("**🏆 Produtos Mais Vendidos**")
                st.bar_chart(dados_empresa.groupby('Descricao_Produto')['Quantidade'].sum().sort_values(ascending=False).head(10))
            with g2:
                st.write("**💰 Faturamento por Pagamento**")
                st.bar_chart(dados_empresa.groupby('Metodo_Pagamento')['Valor_Total'].sum())

            # Tabela de Operadores
            st.write("**👥 Desempenho por Operador**")
            fatur = dados_empresa.groupby('ID_Operador')['Valor_Total'].sum()
            qtd = dados_empresa.groupby('ID_Operador')['ID_Transacao'].nunique()
            tabela = pd.DataFrame({'Vendas': qtd, 'Total': fatur}).reset_index().sort_values(by='Total', ascending=False)
            tabela['Total'] = tabela['Total'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.table(tabela)
        else:
            st.error("Nenhum dado encontrado para sua empresa.")