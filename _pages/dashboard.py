import streamlit as st
import pandas as pd
import plotly.express as px
from utils.stamp import mes_dict, ano_atual, mes_atual
from pathlib import Path

@st.cache_data
def load_data(path):
    """Carrega os dados de um arquivo CSV, com tratamento de erro."""
    try:
        df = pd.read_csv(path)
        # Otimizações básicas no carregamento dos dados
        for col in ['Ano', 'Mês', 'Contrato', 'Estab', 'Status', 'Tipo']:
            if col in df.columns:
                df[col] = df[col].astype('category')
        return df
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado no caminho: {path}")
        return pd.DataFrame()

def show_filters(df):
    """Exibe os filtros na barra lateral e gerencia o estado das seleções."""
    st.sidebar.header('Filtros do Dashboard')

    filter_options = {col: df[col].unique().tolist() for col in ['Ano', 'Mês', 'Contrato', 'Estab', 'Status', 'Tipo']}

    if 'selections' not in st.session_state:
        st.session_state.selections = {
            'Ano': [ano_atual], 'Mês': [mes_atual], 'Contrato': filter_options['Contrato'],
            'Estab': filter_options['Estab'], 'Status': ['LANÇADO'], 'Tipo': ['CONTRATO']
        }
    
    def select_all(column): st.session_state.selections[column] = filter_options[column]
    def clear_selection(column): st.session_state.selections[column] = []

    selections = {}
    for label, col in {'Ano': 'Ano', 'Mês': 'Mês', 'Contrato': 'Contrato', 'Empresa': 'Estab', 'Status': 'Status', 'Tipo': 'Tipo'}.items():
        # A seleção do multiselect é diretamente atribuída ao seu valor de estado
        selections[col] = st.sidebar.multiselect(label, options=filter_options[col], default=st.session_state.selections[col])
        st.session_state.selections[col] = selections[col] # Atualiza o estado
        
        b_col1, b_col2 = st.sidebar.columns(2)
        b_col1.button("Todos", on_click=select_all, args=(col,), key=f'btn_all_{col}', use_container_width=True)
        b_col2.button("Limpar", on_click=clear_selection, args=(col,), key=f'btn_clear_{col}', use_container_width=True)
        
    return st.session_state.selections

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
    df_agrupado = df.groupby('Contrato')['Valor R$'].sum().nlargest(10).sort_values().reset_index()
    df_agrupado['TextoValor'] = df_agrupado['Valor R$'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    fig = px.bar(df_agrupado, x='Valor R$', y='Contrato', orientation='h', title='Top 10 Prestadores', labels={"Contrato": "Contrato", "Valor R$": "Total R$"}, text='TextoValor')
    return fig

def plot_faturamento_hcompany(df, ano_selecionado):
    df_hcompany = df[(df['Contrato'].str.startswith("HCOMPANY")) & (df['Ano'].isin(ano_selecionado)) & (df['Status'] == 'LANÇADO') != 0]
    df_agrupado = df_hcompany.groupby('Mês')['Valor R$'].sum().reset_index()
    df_agrupado['Mes_Num'] = df_agrupado['Mês'].str.lower().map(mes_dict)
    df_agrupado = df_agrupado.sort_values('Mes_Num')
    fig = px.line(df_agrupado, x='Mês', y='Valor R$', title='Faturamento HCOMPANY', labels={'Mês': 'Mês', 'Valor R$': 'Total R$'}, markers=True)
    return fig


def show_dashboard():
    """
    Função principal que renderiza a página do Dashboard.
    Esta função será importada e chamada pelo arquivo `home.py`.
    """
    st.header("Dashboard de Contratos")

    script_dir = Path(__file__).resolve().parent.parent
    path_csv = script_dir / 'data' / 'processed' / 'parcelas.csv'

    # Cria um arquivo mock se ele não existir
    if not path_csv.exists():
        path_csv.parent.mkdir(parents=True, exist_ok=True)
        mock_data = {
            'Ano': [ano_atual, ano_atual], 'Mês': [mes_atual, 'janeiro'], 'Contrato': ['HCOMPANY', 'Outro'],
            'Estab': ['Matriz', 'Filial'], 'Status': ['LANÇADO', 'ABERTO'], 'Tipo': ['CONTRATO', 'CONTRATO'],
            'Valor R$': [5000, 2500]
        }
        pd.DataFrame(mock_data).to_csv(path_csv, index=False)

    parcelas_df = load_data(path_csv)
    if parcelas_df.empty:
        st.warning("Não foi possível carregar os dados. O dashboard não pode ser exibido.")
        return # Use 'return' em vez de 'st.stop()' para não interromper o app inteiro

    selections = show_filters(parcelas_df)

    # --- Lógica de Filtragem ---
    df_filtrado = parcelas_df.copy()
    df_mensal = parcelas_df.copy()
    for column, selected_values in selections.items():
        if selected_values:
            df_filtrado = df_filtrado[df_filtrado[column].isin(selected_values)]
            if column != 'Mês':
                df_mensal = df_mensal[df_mensal[column].isin(selected_values)]
    
    # --- Layout da Página ---
    main_col, side_col = st.columns([2.5, 1.7])
    with main_col:
        with st.container(border=True):
            fig_despesa = plot_despesa_mensal(df_mensal)
            st.plotly_chart(fig_despesa, use_container_width=True)
        st.divider()
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1, st.container(border=True):
            fig_bar_estab = plot_total_estabelecimento_bar(df_filtrado)
            st.plotly_chart(fig_bar_estab, use_container_width=True)
        with sub_col2, st.container(border=True):
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