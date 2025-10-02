import streamlit as st
import plotly.express as px
from utils.stamp import ano_atual, mes_atual

def plot_despesa_mensal(df):
    df_agrupado = df.groupby(['mes', 'mes_nome'], observed=True)['valor'].sum().reset_index()
    df_agrupado = df_agrupado.sort_values('mes')
    df_agrupado['TextoValor'] = df_agrupado['valor'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    fig = px.bar(df_agrupado, x='mes_nome', y='valor', title='Despesas Mensais', labels={"mes_nome": "Mês", "valor": "Total R$"}, text='TextoValor')
    fig.update_traces(textposition='outside', textangle=0)
    return fig

def plot_total_estabelecimentoelecimento_bar(df):
    df_agrupado = df.groupby('estabelecimento', observed=True)['valor'].sum().reset_index().sort_values('valor')
    df_agrupado['TextoValor'] = df_agrupado['valor'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    fig = px.bar(df_agrupado, x='valor', y='estabelecimento', orientation='h', title='Total por Estabelecimento', labels={"estabelecimento": "Estabelecimento", "valor": "Total R$"}, text='TextoValor')
    return fig

def plot_pizza_estabelecimentoelecimentos(df):
    df_agrupado = df.groupby('estabelecimento', observed=True)['valor'].sum().reset_index()
    fig = px.pie(df_agrupado, values='valor', names='estabelecimento', title='Distribuição de Gastos', labels={"estabelecimento": "Estabelecimento", "valor": "Total R$"}, color_discrete_sequence=px.colors.sequential.Viridis)
    return fig

def plot_top_prestadores(df):
    df_agrupado = df.groupby('contrato', observed=True)['valor'].sum().nlargest(10).sort_values().reset_index()
    df_agrupado['TextoValor'] = df_agrupado['valor'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    fig = px.bar(df_agrupado, x='valor', y='contrato', orientation='h', title='Top 10 Prestadores', labels={"contrato": "Prestador", "valor": "Total R$"}, text='TextoValor')
    return fig

def plot_faturamento_hcompany(df, dash_ano_selecionado):
    df_hcompany = df[(df['contrato'].str.startswith("HCOMPANY")) & (df['ano'].isin(dash_ano_selecionado)) & (df['status'] == 'LANÇADO') != 0]
    df_hcompany = df.groupby(['mes', 'mes_nome'], observed=True)['valor'].sum().reset_index()
    df_hcompany = df_hcompany.sort_values('mes')
    fig = px.line(df_hcompany, x='mes_nome', y='valor', title='Faturamento HCOMPANY', labels={'mes_nome': 'Mês', 'valor': 'Total R$'}, markers=True)
    return fig


def show_filters(df):
    st.sidebar.header("Filtros")

    ano_filtro = sorted(df["ano"].dropna().unique().tolist())
    mes_filtro = (df["mes_nome"].dropna().unique().tolist())
    contrato_filtro = sorted(df["contrato"].dropna().unique().tolist())
    tipo_filtro = sorted(df["tipo"].dropna().unique().tolist())
    estabelecimento_filtro = sorted(df["estabelecimento"].dropna().unique().tolist())
    status_filtro = sorted(df["status"].dropna().unique().tolist())

    if 'dash_ano_selecionado' not in st.session_state:
        st.session_state.dash_ano_selecionado = [ano_atual]
    if 'dash_mes_selecionado' not in st.session_state:
        st.session_state.dash_mes_selecionado = [mes_atual]
    if 'dash_contrato_selecionado' not in st.session_state:
        st.session_state.dash_contrato_selecionado = contrato_filtro
    if 'dash_tipo_selecionado' not in st.session_state:
        st.session_state.dash_tipo_selecionado = ['CONTRATO']
    if 'dash_estabelecimento_selecionado' not in st.session_state:
        st.session_state.dash_estabelecimento_selecionado = estabelecimento_filtro
    if 'dash_status_selecionado' not in st.session_state:
        st.session_state.dash_status_selecionado = ['LANÇADO']

    def selecionar_todos(chave_estado, opcoes):
        st.session_state[chave_estado] = opcoes

    def limpar_selecao(chave_estado):
        st.session_state[chave_estado] = []

    # --- Renderização dos Filtros na Sidebar ---
    with st.sidebar.expander("Filtros do Dashboard", expanded=True):
        st.multiselect("Ano", options=ano_filtro, key='dash_ano_selecionado')
        b_col1, b_col2 = st.columns(2)
        b_col1.button("Todos", on_click=selecionar_todos, args=('dash_ano_selecionado', ano_filtro), key='btn_todos_anos', use_container_width=True)
        b_col2.button("Limpar", on_click=limpar_selecao, args=('dash_ano_selecionado',), key='btn_limpar_anos', use_container_width=True)

        st.multiselect("Mês", options=mes_filtro, key='dash_mes_selecionado')
        b_col1, b_col2 = st.columns(2)
        b_col1.button("Todos", on_click=selecionar_todos, args=('dash_mes_selecionado', mes_filtro), key='btn_todos_meses', use_container_width=True)
        b_col2.button("Limpar", on_click=limpar_selecao, args=('dash_mes_selecionado',), key='btn_limpar_meses', use_container_width=True)

        st.multiselect("Contrato", options=contrato_filtro, key='dash_contrato_selecionado')
        b_col1, b_col2 = st.columns(2)
        b_col1.button("Todos", on_click=selecionar_todos, args=('dash_contrato_selecionado', contrato_filtro), key='btn_todos_contratos', use_container_width=True)
        b_col2.button("Limpar", on_click=limpar_selecao, args=('dash_contrato_selecionado',), key='btn_limpar_contratos', use_container_width=True)

        st.multiselect("Tipo", options=tipo_filtro, key='dash_tipo_selecionado')
        b_col1, b_col2 = st.columns(2)
        b_col1.button("Todos", on_click=selecionar_todos, args=('dash_tipo_selecionado', tipo_filtro), key='btn_todos_tipos', use_container_width=True)
        b_col2.button("Limpar", on_click=limpar_selecao, args=('dash_tipo_selecionado',), key='btn_limpar_tipos', use_container_width=True)
        
        st.multiselect("Estabelecimento", options=estabelecimento_filtro, key='dash_estabelecimento_selecionado')
        b_col1, b_col2 = st.columns(2)
        b_col1.button("Todos", on_click=selecionar_todos, args=('dash_estabelecimento_selecionado', estabelecimento_filtro), key='btn_todos_estabelecimentos', use_container_width=True)
        b_col2.button("Limpar", on_click=limpar_selecao, args=('dash_estabelecimento_selecionado',), key='btn_limpar_estabelecimentos', use_container_width=True)

        st.multiselect("Status", options=status_filtro, key='dash_status_selecionado')
        b_col1, b_col2 = st.columns(2)
        b_col1.button("Todos", on_click=selecionar_todos, args=('dash_status_selecionado', status_filtro), key='btn_todos_status', use_container_width=True)
        b_col2.button("Limpar", on_click=limpar_selecao, args=('dash_status_selecionado',), key='btn_limpar_status', use_container_width=True)

def show_dashboard():
    from _pages.parcelas import load_data
    """
    Função principal que renderiza a página do Dashboard.
    """

    im, ti = st.columns([0.05, 0.95])
    with im:
        st.image("https://cdn-icons-png.flaticon.com/512/4573/4573150.png", width=75)
    with ti:
        st.title("Dashboard")
    st.divider()
    parcelas_df = load_data("parcelas")
    if parcelas_df.empty:
        st.warning("Não foi possível carregar os dados. O dashboard não pode ser exibido.")
        return

    show_filters(parcelas_df)
    df_filtrado = parcelas_df[
        (parcelas_df["ano"].isin(st.session_state.dash_ano_selecionado)) &
        (parcelas_df["mes_nome"].isin(st.session_state.dash_mes_selecionado)) &
        (parcelas_df["contrato"].isin(st.session_state.dash_contrato_selecionado)) &
        (parcelas_df["tipo"].isin(st.session_state.dash_tipo_selecionado)) &
        (parcelas_df["estabelecimento"].isin(st.session_state.dash_estabelecimento_selecionado)) &
        (parcelas_df["status"].isin(st.session_state.dash_status_selecionado))
    ]

    df_mensal = parcelas_df[
        (parcelas_df["ano"].isin(st.session_state.dash_ano_selecionado)) &
        (parcelas_df["contrato"].isin(st.session_state.dash_contrato_selecionado)) &
        (parcelas_df["tipo"].isin(st.session_state.dash_tipo_selecionado)) &
        (parcelas_df["estabelecimento"].isin(st.session_state.dash_estabelecimento_selecionado)) &
        (parcelas_df["status"].isin(st.session_state.dash_status_selecionado))
    ]

    # --- Layout da Página ---
    main_col, side_col = st.columns([2.5, 1.7])
    with main_col:
        with st.container(border=True):
            if not df_mensal.empty:
                fig_despesa = plot_despesa_mensal(df_mensal)
                st.plotly_chart(fig_despesa, use_container_width=True)
            else:
                st.info("Nenhum dado de despesa mensal para exibir com os filtros atuais.")
        
        st.divider()

        if not df_filtrado.empty:
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1, st.container(border=True):
                fig_bar_estabelecimento = plot_total_estabelecimentoelecimento_bar(df_filtrado)
                st.plotly_chart(fig_bar_estabelecimento, use_container_width=True)
            with sub_col2, st.container(border=True):
                fig_pie_estabelecimento = plot_pizza_estabelecimentoelecimentos(df_filtrado)
                st.plotly_chart(fig_pie_estabelecimento, use_container_width=True)
        else:
             st.info("Nenhum dado de estabelecimento para exibir com os filtros atuais.")

    with side_col:
        with st.container(border=True):
            if not df_filtrado.empty:
                fig_top_prest = plot_top_prestadores(df_filtrado)
                fig_top_prest.update_layout(height=450)
                st.plotly_chart(fig_top_prest, use_container_width=True)
            else:
                st.info("Nenhum dado para o Top 10 Prestadores com os filtros atuais.")

        st.divider()
        with st.container(border=True):
            fig_fat_hcompany = plot_faturamento_hcompany(parcelas_df, st.session_state.dash_ano_selecionado)
            st.plotly_chart(fig_fat_hcompany, use_container_width=True)

if __name__ == "__main__":
    show_dashboard()