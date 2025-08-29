import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
from utils.stamp import mes_dict

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from utils.stamp import ano_atual, mes_atual

def show():
    DATA_PATH = BASE_DIR / "data" / "processed" / "parcelas.csv"

    parcelas = pd.read_csv(DATA_PATH)

    st.set_page_config(layout="wide") 
    st.title("Dashboard de Contratos")

    st.sidebar.header('Filtros')

    ano_atual2 = [ano_atual]
    mes_atual2 = [mes_atual]

    filtro_ano = parcelas['Ano'].dropna().unique()
    filtro_mes = parcelas['Mês'].dropna().unique()
    filtro_contrato = parcelas['Contrato'].dropna().unique()
    filtro_estab = parcelas['Estab'].dropna().unique()
    filtro_status = parcelas['Status'].dropna().unique()
    filtro_tipo = parcelas['Tipo'].dropna().unique()

    ano_filtrado = st.sidebar.multiselect(
        "Ano",
        options=filtro_ano,
        default=parcelas['Ano'][parcelas['Ano'].isin(ano_atual2)].dropna().unique()
    )
    mes_filtrado = st.sidebar.multiselect(
        'Mês',
        options=filtro_mes,
        default=filtro_mes
    )
    contrato_filtrado = st.sidebar.multiselect(
        "Contrato",
        options = filtro_contrato,
        default=filtro_contrato
    )
    estab_filtrado = st.sidebar.multiselect(
        "Empresa",
        options=filtro_estab,
        default=filtro_estab
    )
    status_filtrado = st.sidebar.multiselect(
        "Status de lançamento",
        options=filtro_status,
        default=parcelas['Status'][parcelas['Status'] == 'LANÇADO'].dropna().unique()
    )
    tipo_filtrado = st.sidebar.multiselect(
        "Tipo de despesa",
        options=filtro_tipo,
        default=parcelas['Tipo'][parcelas['Tipo'] == 'CONTRATO'].dropna().unique()
    )

    df_filtrado = parcelas[
    (parcelas['Ano'].isin(ano_filtrado)) &
    (parcelas['Mês'].isin(mes_filtrado)) &
    (parcelas['Contrato'].isin(contrato_filtrado)) &
    (parcelas['Estab'].isin(estab_filtrado)) &
    (parcelas['Status'].isin(status_filtrado)) &
    (parcelas['Tipo'].isin(tipo_filtrado))
]

    despesa_agrupada = df_filtrado.groupby('Mês')['Valor R$'].sum().reset_index()
    despesa_agrupada['Mes_Num'] = despesa_agrupada['Mês'].str.lower().map(mes_dict)
    despesa_agrupada = despesa_agrupada.sort_values('Mes_Num')
    despesa_agrupada['TextoValor'] = despesa_agrupada['Valor R$'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

    def despesa_mensal():
        fig = px.bar(
            data_frame=despesa_agrupada,
            x='Mês',
            y='Valor R$',
            title='Despesas Mensais',
            labels={"Mês": "Mês", "Valor R$": "Total R$"},
            text='TextoValor',
            color_continuous_scale='viridis',
            )
        
        fig.update_traces(
            textposition='outside', # Força o texto para o topo da barra
            textangle=0             # Garante que o texto fique na horizontal (ângulo 0)
        )
        return fig


    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(despesa_mensal(), use_container_width=True)