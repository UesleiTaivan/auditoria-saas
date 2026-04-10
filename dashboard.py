import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

# 1. Configurações de Layout
st.set_page_config(page_title="Nexus IA: Inteligência & Auditoria ©", page_icon="logo.png", layout="wide")

# --- FUNÇÃO DE LOGIN (ATUALIZADA COM LOGO) ---
def realizar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        # Colunas para centralizar
        _, col_central, _ = st.columns([1, 2, 1])
        
        with col_central:
            # --- NOVA LOGO PROFISSIONAL (Conceito Shield) ---
            # Adiciona a imagem da logo, centralizando-a
            # 'use_container_width=True' faz ela se ajustar à coluna central
            st.image('logo.png', use_container_width=True)
            
            # Subtítulo complementar (opcional, já que está na logo)
            # st.markdown("<h4 style='text-align: center;'>Portal de Inteligência</h4>", unsafe_allow_html=True)
            st.divider() # Uma linha sutil para separar a logo do formulário

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
    st.sidebar.image('logo.png', use_container_width=True)
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
            st.subheader("🧠 Perfil de Risco (Análise de Descontos em R$)")
            c1, c2 = st.columns([1, 2])
            with c1:
                st.info("Concentração de descontos nas anomalias identificadas.")
            with c2:
                st.write("**📊 Frequência de Descontos Suspeitos em R$**")
                fig, ax = plt.subplots(figsize=(8, 4))
                
                # Criando o histograma e pegando os valores de cada barra (n)
                n, bins, patches = ax.hist(fraudes['Desconto_Aplicado'], bins=10, color='red', alpha=0.7, edgecolor='white')
                
                # Adiciona o quantitativo (contagem) em cima de cada barra do histograma
                for i in range(len(patches)):
                    if n[i] > 0: # Só coloca legenda se houver valor
                        ax.text(bins[i] + (bins[i+1]-bins[i])/2, n[i], int(n[i]), 
                                ha='center', va='bottom', fontweight='bold')
                
                ax.set_xlabel("Valor do Desconto (R$)")
                ax.set_ylabel("Quantidade de Transações")
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
                st.write("**🏆 Top 10 Produtos (Qtd Vendida)**")
                
                # Prepara os dados: Agrupa por produto e soma a quantidade
                top_produtos = dados_empresa.groupby('Descricao_Produto')['Quantidade'].sum().sort_values(ascending=False).head(10)
                
                if not top_produtos.empty:
                    fig, ax = plt.subplots(figsize=(8, 5))
                    
                    # Cria as barras (usando uma cor verde para diferenciar do faturamento)
                    bars = ax.bar(top_produtos.index, top_produtos.values, color='#2ca02c')
                    
                    # ADICIONA AS LEGENDAS (O quantitativo em cima de cada barra)
                    ax.bar_label(bars, labels=[f'{int(x)}' for x in top_produtos.values], padding=3, fontweight='bold')
                    
                    # Ajustes de layout para não cortar os nomes dos produtos
                    plt.xticks(rotation=45, ha='right')
                    ax.set_ylabel("Unidades Vendidas")
                    
                    # Remove as bordas desnecessárias para ficar mais "clean"
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    
                    st.pyplot(fig)
                else:
                    st.warning("Sem dados de produtos para exibir.")
            with g2:
                st.write("**💰 Faturamento por Pagamento**")
                # Prepara os dados
                pagamentos = dados_empresa.groupby('Metodo_Pagamento')['Valor_Total'].sum()
                
                fig, ax = plt.subplots(figsize=(8, 5))
                bars = ax.bar(pagamentos.index, pagamentos.values, color='#1f77b4')
                
                # Adiciona os valores em cima das barras formatados como Moeda
                ax.bar_label(bars, labels=[f'R$ {x:,.2f}' for x in pagamentos.values], padding=3)
                
                ax.set_ylabel("Total Vendido")
                plt.xticks(rotation=45)
                st.pyplot(fig)

            # Tabela de Performance
            st.write("**👥 Produtividade por Operador**")
            fatur = dados_empresa.groupby('ID_Operador')['Valor_Total'].sum()
            qtd = dados_empresa.groupby('ID_Operador')['ID_Transacao'].nunique()
            tabela = pd.DataFrame({'Vendas': qtd, 'Total': fatur}).reset_index().sort_values(by='Total', ascending=False)
            tabela['Total'] = tabela['Total'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.table(tabela)
        else:
            st.error("Nenhum dado localizado para esta empresa. Verifique o arquivo CSV.")