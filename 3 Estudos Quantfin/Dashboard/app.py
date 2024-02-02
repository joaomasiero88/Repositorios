#Dashboard de registro de trades 1.0v
# PARA EXECUTAR: 'streamlit run app.py' no terminal

#Libs
import pandas as pd
import numpy as np
import streamlit as st
import time
import plotly.express as px
import plotly.graph_objects as go
import datetime as dt

# Configuração da página
st.set_page_config(
    page_title="Trading Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide"
)

#Loading data
filepath = "C:\\Users\\joaom\\OneDrive\\Trades e investimentos\\Swing trades\\REGISTROS.xlsx"
pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)
diarioccm = pd.read_excel(filepath, sheet_name='CCMFUT')
diariobgi = pd.read_excel(filepath, sheet_name='BGIFUT')
diarioacoes = pd.read_excel(filepath, sheet_name='ACOES')
diariofull = pd.concat([diarioccm, diariobgi, diarioacoes]) #df = com as operações em aberto
diariofull['POS E'] = diariofull['PREÇO ENTRADA'] * diariofull['QDE'].astype(float)
diariofull.sort_values(by='SAÍDA', inplace=True)

########################################################

#STREAMLIT

@st.cache_data
def load_data():
    df_copy = diariofull.copy()  # Crie uma cópia para evitar modificar o original
    time.sleep(2)
    return df_copy

df = load_data()
st.session_state["df_ops"] = df
st.header('Registros')

## Add Sidebar
st.sidebar.header('Filtros')


# Filtro de Tempo
data_inicial = st.sidebar.date_input('Data Inicial', value=pd.to_datetime('2021-06-01'), min_value=None, max_value=None, key=None, help=None, on_change=None, args=None, kwargs=None, disabled=False, label_visibility="visible")
data_final = st.sidebar.date_input('Data Final', value=pd.to_datetime('today'), label_visibility='visible')
df1 = df.loc[(df['SAÍDA'].dt.date >= data_inicial) & (df['SAÍDA'].dt.date <= data_final)]

# Filtro de Ativo
ativo = st.sidebar.selectbox('Ativo', ('Todos', 'CCMFUT', 'BGIFUT', 'Ações'))
if ativo == 'Todos':
   df1 = df1
elif ativo == 'Ações':
   df1 = df1[~df1['ATIVO'].isin(['BGIFUT', 'CCMFUT'])]
else:
   df1 = df1[df1['ATIVO'] == ativo]
st.write(ativo)

# Métricas

df1['POS E'] = df1['PREÇO ENTRADA'] * df1['QDE']
df1['POS S'] = df1['PREÇO SAIDA'] * df1['QDE']
df1['VAR'] = np.where(
    df1['DIREÇÃO'] == 'LONG',
    df1['PREÇO SAIDA'] - df1['PREÇO ENTRADA'],
    df1['PREÇO ENTRADA'] - df1['PREÇO SAIDA'])
df1['VAR%'] = (df1['VAR'] / df1['PREÇO ENTRADA']) * 100
df1['GROSS P/L'] = (df1['VAR'] * df1['QDE'])
df1['NET P/L'] = (df1['GROSS P/L'] - df1['COSTS'])
df1['P/L ACUM'] = df1['NET P/L'].cumsum()
df1['VAR% ACUM'] = df1['VAR%'].cumsum()
df1['AJUSTES'].fillna(0, inplace=True)
df1["EQUITY"] = df1['P/L ACUM'] + df1['AJUSTES'].cumsum()
df1['PEAK'] = df1['P/L ACUM'].cummax()
df1['EDD'] = np.where(
    df1['VAR'] < 0,
    df1['P/L ACUM'] - df1['PEAK'],
    0
)
df1['EDD%'] = (df1['EDD'] / df1['EQUITY']) * 100
df1['SYSDRAW'] = (df1['EDD'] / df1['POS S'].rolling(10).max()) * 100
df1['SAÍDA'] = pd.to_datetime(df1['SAÍDA'])



# Exibe o dataframe em cache com as seguintes colunas:
#colunas_para_exibir = ['ENTRADA', 'SAÍDA', 'ATIVO', 'DIREÇÃO', 'SETUP', 'PREÇO ENTRADA', 'QDE', 'STOP', 'COSTS', 'PREÇO SAIDA', 'AJUSTES', 'VAR%', 'NET P/L', 'P/L ACUM']
st.dataframe(df1)

# Gráficos
st.header('Gráficos')

# Layout de colunas 1
col1, col2 = st.columns(2)

with col1:
   fig = px.line(df1, x="SAÍDA", y="P/L ACUM", title='P/L ACUM', color_discrete_sequence=['rgb(0,255,42)'])
   st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit")
with col2:
   df1['Color'] = df1['NET P/L'].apply(lambda x: 'Positivos' if x >= 0 else 'Negativos')
   color_map = {'Positivos': 'blue', 'Negativos': 'red'}
   fig = px.bar(df1, x=df1.index, y="NET P/L", title='Distribuição dos retornos por dia', color='Color', color_discrete_map=color_map)
   st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit")

df1_filtered = df1.dropna(subset=['NET P/L'])

# Colunas 2
col3, col4 = st.columns(2)

with col3:
   fig = px.line(df1, x="SAÍDA", y="EQUITY", title='Equity', color_discrete_sequence=['rgb(187,51,255)'])
   st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit")
with col4:
   fig = px.area(df1, x="SAÍDA", y="SYSDRAW", title='System Drawdown %', color_discrete_sequence=['rgb(255,77,106)'])
   st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit")



# Relatório de Performance e Trading Stats
st.header('Relatório de performance')

Results = pd.DataFrame(columns=['Results', 'VALUES'])

capital_alocado = df1['AJUSTES'][df1['AJUSTES'] > 0].sum()
Results.loc[1, 'Results'] = 'Capital Alocado (Aportes)'
Results.loc[1, 'VALUES'] = capital_alocado
retiradas = df1['AJUSTES'][df1['AJUSTES'] < 0].sum()
Results.loc[2, 'Results'] = 'Retiradas (Saques)'
Results.loc[2, 'VALUES'] = retiradas
df1 = df1.sort_values(by='SAÍDA', ascending=False)
account = df1['EQUITY'].iloc[0]
Results.loc[3, 'Results'] = 'Account (Valor Presente)'
Results.loc[3, 'VALUES'] = account
disponivel_saque = account - capital_alocado
Results.loc[4, 'Results'] = 'Disponível (Saques)'
Results.loc[4, 'VALUES'] = disponivel_saque
lucro_bruto = -retiradas + disponivel_saque
Results.loc[5, 'Results'] = 'Lucro Bruto'
Results.loc[5, 'VALUES'] = lucro_bruto
lucro_liq = lucro_bruto * 0.85
if lucro_bruto > 0:
    lucro_liq = lucro_bruto * (1 - 0.15)  # 15% de desconto para lucros positivos
else:
    lucro_liq = lucro_bruto
Results.loc[6, 'Results'] = 'Lucro Líquido (IR)'
Results.loc[6, 'VALUES'] = lucro_liq
capital_inicial = capital_alocado - lucro_liq
Results.loc[7, 'Results'] = 'Capital Inicial'
Results.loc[7, 'VALUES'] = capital_inicial
rentab = lucro_liq / capital_inicial
Results.loc[8, 'Results'] = 'Rentabilidade Liq %'
Results.loc[8, 'VALUES'] = rentab * 100
data_final = df1['SAÍDA'].iloc[0]
df1 = df1.sort_values(by='SAÍDA', ascending=True)
data_inicial = df1['SAÍDA'].iloc[0]
numero_anos = (data_final - data_inicial).days / 365.25
valor_final = lucro_liq + capital_inicial
rent_anual = (valor_final / capital_inicial) ** (1 / numero_anos) - 1
Results.loc[9, 'Results'] = 'CAGR% - Compound annual growth rate'
Results.loc[9, 'VALUES'] = abs(rent_anual) * 100

stats = pd.DataFrame(columns=['Stats', 'VALUES'])

no_trades = df1['SAÍDA'].count()
stats.loc[1, 'Stats'] = 'Número de operações'
stats.loc[1, 'VALUES'] = no_trades
op_positivas = df1[df1['VAR'] > 0]['VAR'].count()
stats.loc[2, 'Stats'] = 'Operações Positivas'
stats.loc[2, 'VALUES'] = op_positivas
op_negativas = no_trades - op_positivas
stats.loc[3, 'Stats'] = 'Operações negativas'
stats.loc[3, 'VALUES'] = op_negativas
taxa_acerto = (op_positivas / no_trades) * 100
stats.loc[4, 'Stats'] = 'Taxa de Acerto %'
stats.loc[4, 'VALUES'] = taxa_acerto
media_win = df1[df1['VAR'] > 0]['VAR%'].mean()
stats.loc[5, 'Stats'] = 'Média de Ganho %'
stats.loc[5, 'VALUES'] = media_win
media_loss = df1[df1['VAR'] < 0]['VAR%'].mean()
stats.loc[6, 'Stats'] = 'Média de Perda %'
stats.loc[6, 'VALUES'] = media_loss
payoff = media_win / media_loss
stats.loc[7, 'Stats'] = 'Payoff'
stats.loc[7, 'VALUES'] = abs(payoff)
max_dd = df1['SYSDRAW'].min()
stats.loc[8, 'Stats'] = 'Max System Drawdown'
stats.loc[8, 'VALUES'] = max_dd
max_edd = df1['EDD%'].min()
stats.loc[9, 'Stats'] = 'Max Equity Drawdown'
stats.loc[9, 'VALUES'] = max_edd

col5, col6, col7 = st.columns(3)
with col5:
    st.write(Results)
with col6:
   st.write(stats)

# Demais infos
num_valores_vazios = diariofull['SAÍDA'].isna().sum()
st.write('Operações em Aberto:', num_valores_vazios)

valor_em_aberto = diariofull.loc[diariofull['SAÍDA'].isna(), 'POS E'].sum()
st.write('Valor em Aberto:', valor_em_aberto)

