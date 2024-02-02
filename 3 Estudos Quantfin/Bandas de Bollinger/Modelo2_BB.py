# Modelo baseado em Bandas de Bollinger - versão 1.0.0
# Autor: João A. Masiero
#30/12/22
######################################################

## Carregando as bibliotecas necessárias
from pandas_datareader import data as pdr
from datetime import date
import yfinance as yf
yf.pdr_override()
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

## Configurações iniciais
ticker = "^BVSP" #ticker formato yfinance
inicio = "2010-01-01" #AAAA-MM-DD
fim = "2023-01-01"

## Coleta dos dados
df = pdr.get_data_yahoo(ticker, start = inicio, end = fim)

'''# Visualização dos Fechamentos no gráfico:
df["Adj Close"].plot(grid = True, figsize = (20, 15), linewidth = 2, fontsize = 15, color = "darkblue")
plt.xlabel("Data", fontsize = 15)
plt.ylabel("Pontos", fontsize = 15 )
plt.title("Ticker:"+" {}".format(ticker), fontsize = 25)
plt.legend()'''

## Inserindo mais valores no dataframe
# Bandas de bollinger e Media movel - Parâmetros iniciais
periodo = 50
desvios = 2

df["desvio"] = df["Adj Close"].rolling(periodo).std()
df["MM"] = df["Adj Close"].rolling(periodo).mean()
df["Banda_Sup"] = df["MM"] + (df["desvio"]*desvios)
df["Banda_Inf"] = df["MM"] - (df["desvio"]*desvios)

# Filtrando os valores missing
df = df.dropna(axis = 0) #se a linha tiver um NA, corta a linha do dataframe

## Visualização dos dados no gráfico
df[["Adj Close", "MM", "Banda_Sup", "Banda_Inf"]].plot(grid = True, figsize = (20, 15), linewidth = 1, fontsize = 15, color = ["darkblue", "red", "orange", "grey"])                                                            
plt.xlabel("Data", fontsize = 15)           
plt.ylabel("Pontos", fontsize = 15 )
plt.title("Ticker:"+" {}".format(ticker), fontsize = 25)
plt.legend()

## Construção dos Alvos
periodos = 10 #tempo de duração da operação(dias)

# Alvo 1 - Retorno
df.loc[:, "Retorno"] = df["Adj Close"].pct_change(periodos) #add coluna "Retorno %"
df.loc[:, "Alvo"] = df["Retorno"].shift(-periodos) #Retorno deslocado para frente
df = df.dropna(axis = 0) #tira valores missing

## Criando a regra de trade
# Close < banda_inf = venda (-1)
df.loc[:, "Regra"] = np.where(df.loc[:, "Adj Close"] > df.loc[:, "Banda_Sup"], 1, 0)
# Close > banda_sup = compra (1)
df.loc[:, "Regra"] = np.where(df.loc[:, "Adj Close"] < df.loc[:, "Banda_Inf"], -1, df.loc[:, "Regra"])

## Aplicando a regra no alvo: compra/venda*alvo
df.loc[:, "Trade"] = df.loc[:, "Regra"]*df.loc[:, "Alvo"]

## Calculando o resultado acumulado em juros simples
df.loc[:, "Retorno_Trade_BB"] = df["Trade"].cumsum()

#Exibe dataframe

display(df)

# Gráfico dos retornos
df["Retorno_Trade_BB"].plot(figsize=(20, 15), linewidth = 3, fontsize = 15, color = "green")
plt.xlabel("Data"
           , fontsize = 15);
plt.ylabel("Pontos"
           , fontsize = 15);
plt.title("{}".format(ticker)
           , fontsize = 25);
plt.legend()


