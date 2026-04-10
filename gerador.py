import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

print("Fabricando 10.000 transações com Mix de Produtos expandido...")

num_linhas = 10000
data_base = datetime(2026, 4, 1, 8, 0, 0)

# Catálogo expandido para análise de estoque e vendas
catalogo = [
    ('7891001', 'Arroz 5kg', 'Mercearia', 24.90),
    ('7891002', 'Feijão Preto 1kg', 'Mercearia', 8.50),
    ('7891005', 'Cerveja Lata', 'Bebidas', 3.50),
    ('7891006', 'Refrigerante 2L', 'Bebidas', 8.90),
    ('7891011', 'Patinho 1kg', 'Açougue', 38.90),
    ('7891012', 'Frango Inteiro', 'Açougue', 15.90),
    ('7891008', 'Detergente', 'Limpeza', 2.20),
    ('7891009', 'Sabão em Pó', 'Limpeza', 14.50),
    ('7891015', 'Mussarela 1kg', 'Laticínios', 45.90),
    ('7891016', 'Leite Integral 1L', 'Laticínios', 5.20),
    ('7891020', 'Pão Francês kg', 'Padaria', 12.00),
    ('7891021', 'Bolo de Milho', 'Padaria', 15.00),
    ('7891030', 'Banana Prata kg', 'Hortifruti', 6.50),
    ('7891031', 'Tomate kg', 'Hortifruti', 7.90),
    ('7891040', 'Shampoo', 'Higiene', 18.00)
]

dados = []
transacao_atual = 20000
tempo_atual = data_base

for i in range(num_linhas):
    if random.random() > 0.7: 
        transacao_atual += 1
        tempo_atual += timedelta(minutes=random.randint(0, 2))
        
    sku, descricao, categoria, preco_unit = random.choice(catalogo)
    quantidade = random.randint(1, 5)
    desconto = 0.0
    metodo = np.random.choice(['PIX', 'Cartão de Crédito', 'Cartão de Débito', 'Dinheiro'], p=[0.35, 0.40, 0.15, 0.10])
    operador = random.randint(101, 115) 
    
    # Injeção de Fraudes (Operador 105)
    if random.random() < 0.005: 
        desconto = round(preco_unit * quantidade * random.uniform(0.4, 0.8), 2)
        metodo = 'Dinheiro'
        operador = 105
        
    valor_total = round((preco_unit * quantidade) - desconto, 2)
    dados.append([transacao_atual, operador, tempo_atual.strftime('%Y-%m-%d %H:%M:%S'), 
                  descricao, categoria, quantidade, preco_unit, desconto, valor_total, metodo])

df = pd.DataFrame(dados, columns=['ID_Transacao', 'ID_Operador', 'Data_Hora', 'Descricao_Produto', 'Categoria', 'Quantidade', 'Preco_Unitario', 'Desconto_Aplicado', 'Valor_Total', 'Metodo_Pagamento'])
df.to_csv('vendas_10k.csv', index=False)
print("Sucesso! Novo arquivo 'vendas_10k.csv' com 15 produtos criado.")