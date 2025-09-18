import streamlit as st
import pandas as pd
import plotly.express as px
from utils.stamp import mes_dict, ano_atual, mes_atual
from pathlib import Path

@st.cache_data
def load_data(path):
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado: {path}")
        st.stop()

def show_filters(df):
    st.sidebar.header('Filtros')
    
    filter_config = {
        'Ano': ('Ano', [ano_atual]),
        'Mês': ('Mês', [mes_atual]),
        'Contrato': ('Contrato', df['Contrato'].dropna().unique()),
        'Empresa': ('Estab', df['Estab'].dropna().unique()),
        'Status de lançamento': ('Status', ['LANÇADO']),
        'Tipo de despesa': ('Tipo', ['CONTRATO'])
    }
    
    selections = {}
    for label, (col, default) in filter_config.items():
        options = df[col].dropna().unique()
        selections[col] = st.sidebar.multiselect(label, options=options, default=default)
        
    return selections

def plot_despesa_mensal(df):
    df_agrupado = df.groupby('Mês')['Valor R$'].sum().reset_index()
    df_agrupado['Mes_Num'] = df_agrupado['Mês'].str.lower().map(mes_dict)
    df_agrupado = df_agrupado.sort_values('Mes_Num')
    df_agrupado['TextoValor'] = df_agrupado['Valor R$'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    fig = px.bar(df_agrupado, x='Mês', y='Valor R$', title='Despesas Mensais', labels={"Mês": "Mês", "Valor R$": "Total R$"}, text='TextoValor')
    fig.update_traces(textposition='outside', textangle=0)
    return fig

def plot_total_estabelecimento_bar(df):
    df_agrupado = df.groupby('Estab')['Valor R$'].sum().reset_index().sort_values('Valor R$')
    df_agrupado['TextoValor'] = df_agrupado['Valor R$'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    fig = px.bar(df_agrupado, x='Valor R$', y='Estab', orientation='h', title='Total por Estabelecimento', labels={"Estab": "Estabelecimento", "Valor R$": "Total R$"}, text='TextoValor')
    return fig

def plot_pizza_estabelecimentos(df):
    df_agrupado = df.groupby('Estab')['Valor R$'].sum().reset_index()
    fig = px.pie(df_agrupado, values='Valor R$', names='Estab', title='Distribuição de Gastos', labels={"Estab": "Estabelecimento", "Valor R$": "Total R$"}, color_discrete_sequence=px.colors.sequential.Viridis)
    return fig

def plot_top_prestadores(df):
    df_agrupado = df.groupby('Contrato')['Valor R$'].sum().reset_index().sort_values(by='Valor R$', ascending=False).head(10)
    df_agrupado = df_agrupado.iloc[::-1] # Inverte a ordem para o gráfico
    df_agrupado['TextoValor'] = df_agrupado['Valor R$'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

    fig = px.bar(df_agrupado, x='Valor R$', y='Contrato', orientation='h', title='Top 10 Prestadores', labels={"Contrato": "Contrato", "Valor R$": "Total R$"}, text='TextoValor')
    return fig

def plot_faturamento_hcompany(df, ano_selecionado):
    df_hcompany = df[(df['Contrato'].str.startswith("HCOMPANY", na=False)) & (df['Ano'].isin(ano_selecionado)) & (df['Status'] == 'LANÇADO')]
    df_agrupado = df_hcompany.groupby('Mês')['Valor R$'].sum().reset_index()
    df_agrupado['Mes_Num'] = df_agrupado['Mês'].str.lower().map(mes_dict)
    df_agrupado = df_agrupado.sort_values('Mes_Num')

    fig = px.line(df_agrupado, x='Mês', y='Valor R$', title='Faturamento HCOMPANY', labels={'Mês': 'Mês', 'Valor R$': 'Total R$'})
    return fig

def show():
    st.set_page_config(layout="wide")
    st.title("Dashboard de Contratos")

    script_dir = Path(__file__).resolve().parent.parent
    path_csv = script_dir / 'data' / 'processed' / 'parcelas.csv'

    parcelas_df = load_data(path_csv)
    selections = show_filters(parcelas_df)

    query_parts = [f"`{col}` in @selections['{col}']" for col, selection in selections.items() if selection]
    
    df_filtrado = parcelas_df
    if query_parts:
        query_string = " & ".join(query_parts)
        df_filtrado = parcelas_df.query(query_string)

    # DataFrame para o gráfico mensal, que não deve ser filtrado por mês
    selections_sem_mes = {k: v for k, v in selections.items() if k != 'Mês'}
    query_parts_sem_mes = [f"`{col}` in @selections_sem_mes['{col}']" for col, selection in selections_sem_mes.items() if selection]
    
    df_mensal = parcelas_df
    if query_parts_sem_mes:
        query_string_sem_mes = " & ".join(query_parts_sem_mes)
        df_mensal = parcelas_df.query(query_string_sem_mes)
    
    # --- Layout da Página ---
    main_col, side_col = st.columns([2.5, 1.7])

    with main_col:
        with st.container(border=True):
            fig_despesa = plot_despesa_mensal(df_mensal)
            st.plotly_chart(fig_despesa, use_container_width=True)
        
        st.divider()
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            with st.container(border=True):
                fig_bar_estab = plot_total_estabelecimento_bar(df_filtrado)
                st.plotly_chart(fig_bar_estab, use_container_width=True)
        with sub_col2:
            with st.container(border=True):
                fig_pie_estab = plot_pizza_estabelecimentos(df_filtrado)
                st.plotly_chart(fig_pie_estab, use_container_width=True)

    with side_col:
        with st.container(border=True):
            fig_top_prest = plot_top_prestadores(df_filtrado)
            fig_top_prest.update_layout(height=450)
            st.plotly_chart(fig_top_prest, use_container_width=True)
            
        st.divider()
        with st.container(border=True):
            fig_fat_hcompany = plot_faturamento_hcompany(parcelas_df, selections['Ano'])
            st.plotly_chart(fig_fat_hcompany, use_container_width=True)
    
show()