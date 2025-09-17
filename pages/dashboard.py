import streamlit as st
import pandas as pd
import plotly.express as px
from utils.stamp import mes_dict,ano_atual, mes_atual
from pathlib import Path

def show():
    script_dir = Path(__file__).resolve().parent.parent
    path_csv = script_dir / 'data' / 'processed' / 'parcelas.csv'

    parcelas = pd.read_csv(path_csv)

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
        default=parcelas['Mês'][parcelas['Mês'].isin(mes_atual2)].dropna().unique()
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

    df_mensal = parcelas[
        (parcelas['Ano'].isin(ano_filtrado)) &
        (parcelas['Contrato'].isin(contrato_filtrado)) &
        (parcelas['Estab'].isin(estab_filtrado)) &
        (parcelas['Status'].isin(status_filtrado)) &
        (parcelas['Tipo'].isin(tipo_filtrado))
    ]

    despesa_agrupada = df_mensal.groupby('Mês')['Valor R$'].sum().reset_index()
    despesa_agrupada['Mes_Num'] = despesa_agrupada['Mês'].str.lower().map(mes_dict)
    despesa_agrupada = despesa_agrupada.sort_values('Mes_Num')
    despesa_agrupada['TextoValor'] = despesa_agrupada['Valor R$'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

    estab_agrupado = df_filtrado.groupby('Estab')['Valor R$'].sum().reset_index()
    estab_agrupado = estab_agrupado.sort_values('Valor R$')
    estab_agrupado['TextoValor'] = estab_agrupado['Valor R$'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

    prest_agrupado = df_filtrado.groupby('Contrato')['Valor R$'].sum().reset_index()
    prest_agrupado = prest_agrupado.sort_values(by='Valor R$', ascending=False).head(10)
    prest_agrupado = prest_agrupado[::-1]
    prest_agrupado['TextoValor'] = prest_agrupado['Valor R$'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

    parcelas_hcompany = parcelas[
        (parcelas['Contrato'].str.startswith("HCOMPANY")) & 
        (parcelas['Ano'].isin(ano_filtrado)) &
        (parcelas['Status'] == 'LANÇADO')
    ]

    faturamento_hcompany = parcelas_hcompany.groupby(['Ano', 'Mês'])['Valor R$'].sum().reset_index()
    faturamento_hcompany['MesNum'] = faturamento_hcompany['Mês'].str.lower().map(mes_dict)
    faturamento_hcompany = faturamento_hcompany.sort_values('MesNum')

    def despesa_mensal():
        fig = px.bar(
            data_frame=despesa_agrupada,
            x='Mês',
            y='Valor R$',
            title='Despesas Mensais',
            labels={"Mês": "Mês", "Valor R$": "Total R$"},
            text='TextoValor',
            color_continuous_scale='viridis'
            )
        
        fig.update_traces(
            textposition='outside', 
            textangle=0             
        )
        return fig

    def total_estabelecimento():
        fig = px.bar(
            data_frame=estab_agrupado,
            x='Valor R$',
            y='Estab',
            orientation='h',
            title='Total Estabelecimento',
            labels={"Estab": "Estabelecimento", "Valor R$": "Total R$"},
            text='TextoValor',
            color_continuous_scale='viridis'
        )
        return fig
    
    def pizza_estabelecimentos():
        fig = px.pie(
            data_frame=estab_agrupado,
            values='Valor R$',
            names='Estab',
            title='Distribuição Gastos por Estabelecimento',
            labels={"Estab": "Estabelecimento", "Valor R$": "Total R$"},
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        return fig
    
    def top_prestadores():
        fig = px.bar(
            data_frame=prest_agrupado,
            x='Valor R$',
            y='Contrato',
            orientation='h',
            title='Ranking Prestadores',
            labels={"Contrato": "Contrato", "Valor R$": "Total R$"},
            text='TextoValor',
            color_continuous_scale='viridis'
        )
        return fig
    
    def faturamento_mensal():
        fig = px.line(
            data_frame=faturamento_hcompany,
            x='Mês',
            y='Valor R$',
            title='Faturamento HCOMPANY',
            labels={'Mês': 'Mês', 'Valor R$': 'Total R$'}
        )
        return fig

    main_col, side_col = st.columns([2.5, 1.5])

    with side_col:
        with st.container(border=True):
            top_prestadores().update_layout(height=650)
            st.plotly_chart(faturamento_mensal(), use_container_width=True)
    
        st.write('---')

        with st.container(border=True):
            st.plotly_chart(top_prestadores(), use_container_width=True)

    with main_col:
        with st.container(border=True):
            st.plotly_chart(despesa_mensal(), use_container_width=True)
        
        st.write('---')

        sub_col1, sub_col2 = st.columns(2)

        with sub_col1:
            with st.container(border=True):
                st.plotly_chart(total_estabelecimento(), use_container_width=True)

        with sub_col2:
            with st.container(border=True):
                st.plotly_chart(pizza_estabelecimentos(), use_container_width=True)