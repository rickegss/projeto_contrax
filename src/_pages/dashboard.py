from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
from src.utils.stamp import ano_atual, mes_atual

def plot_despesa_mensal(df):
    df_agrupado = df.groupby(['mes', 'mes_nome'], observed=True)['valor'].sum().reset_index()
    df_agrupado = df_agrupado.sort_values('mes')
    df_agrupado['TextoValor'] = df_agrupado['valor'].apply(formata_moeda)
    fig = px.bar(df_agrupado, x='mes_nome', y='valor', title='Despesas Mensais', labels={"mes_nome": "Mês", "valor": "Total R$"}, text='TextoValor')
    fig.update_traces(textposition='outside', textangle=0)
    return fig

def plot_total_estabelecimento_bar(df):
    df_agrupado = df.groupby('estabelecimento', observed=True)['valor'].sum().reset_index().sort_values('valor')
    df_agrupado['TextoValor'] = df_agrupado['valor'].apply(formata_moeda)
    fig = px.bar(df_agrupado, x='valor', y='estabelecimento', orientation='h', title='Total por Estabelecimento', labels={"estabelecimento": "Estabelecimento", "valor": "Total R$"}, text='TextoValor', color="estabelecimento", color_discrete_sequence=px.colors.sequential.Viridis)
    return fig

def plot_classificacao(df):
    df_agrupado = df.groupby('classificacao', observed=True)['valor'].sum().reset_index()
    df_agrupado['TextoValor'] = df_agrupado['valor'].apply(formata_moeda)
    fig = px.bar(df_agrupado, x='classificacao', y='valor', title='Despesas por Classificação', labels={"classificacao": "Classificação", "valor": "Total R$"}, text='TextoValor')
    fig.update_traces(textposition='outside', textangle=0)
    return fig

def plot_top_prestadores(df):
    df_agrupado = df.groupby('contrato', observed=True)['valor'].sum().nlargest(10).sort_values().reset_index()
    df_agrupado['TextoValor'] = df_agrupado['valor'].apply(formata_moeda)
    fig = px.bar(df_agrupado, x='valor', y='contrato', orientation='h', title='Top 10 Prestadores', labels={"contrato": "Prestador", "valor": "Total R$"}, text='TextoValor')
    return fig

def plot_faturamento_hcompany(df, dash_ano_selecionado):
    df_hcompany = df[
        (df['contrato'].str.startswith("HCOMPANY")) &
        (df['ano'].isin(dash_ano_selecionado)) &
        (df['status'] == 'LANÇADO')
    ]

    df_agrupado = df_hcompany.groupby(['mes', 'mes_nome'], observed=True)['valor'].sum().reset_index()
    df_agrupado = df_agrupado.sort_values('mes')
    
    fig = px.line(
        df_agrupado, 
        x='mes_nome', 
        y='valor', 
        title='Faturamento HCOMPANY', 
        labels={'mes_nome': 'Mês', 'valor': 'Total R$'}, 
        markers=True
    )
    return fig

def formata_moeda(valor):
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

def show_filters(df):
    st.sidebar.header("Filtros")

    ano_filtro = sorted(df["ano"].dropna().unique().tolist())
    mes_filtro = (df["mes_nome"].dropna().unique().tolist())
    contrato_filtro = sorted(df["contrato"].dropna().unique().tolist())
    tipo_filtro = sorted(df["tipo"].dropna().unique().tolist())
    estabelecimento_filtro = sorted(df["estabelecimento"].dropna().unique().tolist())
    status_filtro = sorted(df["status"].dropna().unique().tolist())
    classificacao_filtro = sorted(df["classificacao"].dropna().unique().tolist())

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
    if 'dash_classificacao_selecionada' not in st.session_state:
        st.session_state.dash_classificacao_selecionada = classificacao_filtro

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

        st.multiselect("Classificação", options=classificacao_filtro, key="dash_classificacao_selecionada")
        b_col1, b_col2 = st.columns(2)
        b_col1.button("Todos", on_click=selecionar_todos, args=('dash_classificacao_selecionada', status_filtro), key='btn_todos_classificacao', use_container_width=True)
        b_col2.button("Limpar", on_click=limpar_selecao, args=('dash_classificacao_selecionada',), key='btn_limpar_classificacao', use_container_width=True)

def show_dashboard():
    from src._pages.parcelas import load_data
    """
    Função principal que renderiza a página do Dashboard.
    """

 
    st.title("Dashboard de Despesas")
    st.divider()

    tab_geral, tab_gantt = st.tabs(["Gastos e Faturamento", "Contratos Gantt"])
    
    with tab_geral:
        parcelas_df = load_data("parcelas")
        if parcelas_df.empty:
            st.warning("Não foi possível carregar os dados. O dashboard não pode ser exibido.")
            return

        show_filters(parcelas_df)
        df_filtrado = parcelas_df[
            (parcelas_df["ano"].isin(st.session_state.dash_ano_selecionado)) &
            (parcelas_df["mes_nome"].isin(st.session_state.dash_mes_selecionado)) &
            (parcelas_df["contrato"].isin(st.session_state.dash_contrato_selecionado)) &
            (~parcelas_df["contrato"].str.startswith("HCOMPANY")) &
            (parcelas_df["tipo"].isin(st.session_state.dash_tipo_selecionado)) &
            (parcelas_df["estabelecimento"].isin(st.session_state.dash_estabelecimento_selecionado)) &
            (parcelas_df["status"].isin(st.session_state.dash_status_selecionado)) &
            (parcelas_df["classificacao"].isin(st.session_state.dash_classificacao_selecionada))
        ]

        df_mensal = parcelas_df[
            (parcelas_df["ano"].isin(st.session_state.dash_ano_selecionado)) &
            (parcelas_df["contrato"].isin(st.session_state.dash_contrato_selecionado)) &
            (~parcelas_df["contrato"].str.startswith("HCOMPANY")) &
            (parcelas_df["tipo"].isin(st.session_state.dash_tipo_selecionado)) &
            (parcelas_df["estabelecimento"].isin(st.session_state.dash_estabelecimento_selecionado)) &
            (parcelas_df["status"].isin(st.session_state.dash_status_selecionado)) &
            (parcelas_df["classificacao"].isin(st.session_state.dash_classificacao_selecionada))
        ]

        df_hcompany = parcelas_df[
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
            

            if not df_filtrado.empty:
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1, st.container(border=True):
                    fig_bar_estabelecimento = plot_total_estabelecimento_bar(df_filtrado)
                    st.plotly_chart(fig_bar_estabelecimento, use_container_width=True)
                with sub_col2, st.container(border=True):
                    fig_pie_estabelecimento = plot_classificacao(df_filtrado)
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

            with st.container(border=True):
                fig_fat_hcompany = plot_faturamento_hcompany(df_hcompany, st.session_state.dash_ano_selecionado)
                st.plotly_chart(fig_fat_hcompany, use_container_width=True)

    with tab_gantt:
        contratos = load_data("contratos")
        contratos["inicio"] = pd.to_datetime(contratos["inicio"])
        contratos["termino"] = pd.to_datetime(contratos["termino"])

        df_gantt = contratos.dropna(subset=["inicio", "termino"])
        
        fig = px.timeline(
            df_gantt, 
            x_start="inicio", 
            x_end="termino", 
            y="contrato",   
            color_discrete_sequence=px.colors.sequential.Viridis[2:],
            title="Cronograma de Vigência de Contratos",
            height=1400,
            width=1900
        )
        hoje = datetime.now()
        fig.add_vline(
            x=hoje,
            line_width=2,
            line_dash="dash",
            line_color="cyan"
        )
        fig.add_annotation(
            x=hoje,
            y=1.03,
            yref="paper",
            text="Hoje",
            showarrow=False,
            font=dict(color="cyan"),
            align="center"
        )
    
        fig.update_yaxes(autorange="reversed")

        st.plotly_chart(fig, use_container_width=False)

if __name__ == "__main__":
    show_dashboard()