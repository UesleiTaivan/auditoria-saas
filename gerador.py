import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def gerar_dados_saas(n_total=20000):
    produtos = {
        'Arroz 5kg': 24.90, 'Feijão 1kg': 8.50, 'Óleo de Soja': 6.90,
        'Patinho 1kg': 38.90, 'Mussarela 1kg': 45.90, 'Leite Integral': 5.20,
        'Pão de Forma': 7.50, 'Café 500g': 16.90, 'Detergente': 2.50, 'Shampoo': 18.00
    }
    
    metodos = ['Dinheiro', 'Cartão de Crédito', 'Cartão de Débito', 'PIX']
    empresas = ['pmw2026', 'adminpmw2026'] # Seus usuários do Secrets
    
    dados = []
    
    for empresa in empresas:
        # Definindo operadores por empresa para facilitar a auditoria
        if empresa == 'pmw2026':
            ops = [101, 102, 103, 104, 105] # 105 é o suspeito
        else:
            ops = [201, 202, 203, 204, 205] # 205 é o suspeito

        for _ in range(n_total // len(empresas)):
            prod = random.choice(list(produtos.keys()))
            preco = produtos[prod]
            qtd = random.randint(1, 5)
            valor = preco * qtd
            op = random.choice(ops)
            desc = 0
            
            # Simulação de fraude (30% de chance para o operador final de cada lista)
            if op in [105, 205] and random.random() < 0.3:
                desc = round(valor * random.uniform(0.4, 0.8), 2)
                valor -= desc

            dados.append({
                'ID_Transacao': 100000 + len(dados),
                'Empresa': empresa, # COLUNA CHAVE
                'ID_Operador': op,
                'Data_Hora': (datetime(2026, 1, 1) + timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))),
                'Descricao_Produto': prod,
                'Quantidade': qtd,
                'Preco_Unitario': preco,
                'Desconto_Aplicado': desc,
                'Valor_Total': round(valor, 2),
                'Metodo_Pagamento': random.choice(metodos)
            })

    df = pd.DataFrame(dados)
    df.to_csv('vendas_10k.csv', index=False)
    print(f"✅ Arquivo 'vendas_10k.csv' gerado com sucesso!")
    print(f"Empresas incluídas: {df['Empresa'].unique()}")

if __name__ == "__main__":
    gerar_dados_saas()