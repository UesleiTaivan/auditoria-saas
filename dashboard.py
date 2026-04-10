import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def gerar_dados_multi_empresa(n_registros=20000):
    produtos = {
        'Arroz 5kg': 24.90,
        'Feijão 1kg': 8.50,
        'Óleo de Soja': 6.90,
        'Patinho 1kg': 38.90,
        'Mussarela 1kg': 45.90,
        'Leite Integral': 5.20,
        'Pão de Forma': 7.50,
        'Café 500g': 16.90,
        'Detergente': 2.50,
        'Shampoo': 18.00
    }
    
    metodos_pagamento = ['Dinheiro', 'Cartão de Crédito', 'Cartão de Débito', 'PIX']
    
    dados = []
    
    # Metade para cada empresa
    empresas = ['pmw2026', 'adminpmw2026']
    registros_por_empresa = n_registros // len(empresas)

    for empresa in empresas:
        # Definimos IDs de operadores diferentes para cada empresa para facilitar a visualização
        if empresa == 'pmw2026':
            operadores = [101, 102, 103, 104, 105] # 105 será o fraudador aqui
        else:
            operadores = [201, 202, 203, 204, 205] # 205 será o fraudador aqui

        for i in range(registros_por_empresa):
            data_base = datetime(2026, 1, 1)
            data_venda = data_base + timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            produto = random.choice(list(produtos.keys()))
            preco_unitario = produtos[produto]
            quantidade = random.randint(1, 5)
            valor_total = preco_unitario * quantidade
            
            operador = random.choice(operadores)
            metodo = random.choice(metodos_pagamento)
            desconto = 0
            
            # Simulação de Fraude (Operadores 105 e 205)
            # Se for o operador "vilão", ele dá descontos absurdos em 30% das suas vendas
            if operador in [105, 205] and random.random() < 0.3:
                desconto = round(valor_total * random.uniform(0.5, 0.9), 2)
                valor_total -= desconto

            dados.append({
                'ID_Transacao': 100000 + len(dados), # ID único sequencial
                'Empresa': empresa,
                'ID_Operador': operador,
                'Data_Hora': data_venda,
                'Descricao_Produto': produto,
                'Quantidade': quantidade,
                'Preco_Unitario': preco_unitario,
                'Desconto_Aplicado': desconto,
                'Valor_Total': round(valor_total, 2),
                'Metodo_Pagamento': metodo
            })

    df = pd.DataFrame(dados)
    df.to_csv('vendas_10k.csv', index=False)
    print(f"Sucesso! Arquivo gerado com {len(df)} registros divididos entre {empresas}")

if __name__ == "__main__":
    gerar_dados_multi_empresa()