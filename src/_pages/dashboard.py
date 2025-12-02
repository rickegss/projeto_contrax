import streamlit as st
from utils.stamp import ano_atual, mes_atual
from core.database_connections import load_data
from services.dashboard_service import filtrar_dados_dashboard
from utils.plots import (
    plot_despesa_mensal, 
    plot_total_estabelecimento_bar, 
    plot_classificacao, 
    plot_top_prestadores, 
    plot_faturamento_hcompany,
    plot_gantt_contratos
)

def show_filters(df):
    st.sidebar.header("Filtros")

    opts = {
        "ano": sorted(df["ano"].dropna().unique().tolist()),
        "mes": df["mes_nome"].dropna().unique().tolist(),
        "contrato": sorted(df["contrato"].dropna().unique().tolist()),
        "tipo": sorted(df["tipo"].dropna().unique().tolist()),
        "estab": sorted(df["estabelecimento"].dropna().unique().tolist()),
        "status": sorted(df["status"].dropna().unique().tolist()),
        "class": sorted(df["classificacao"].dropna().unique().tolist())
    }

    defaults = {
        'dash_ano_selecionado': [ano_atual],
        'dash_mes_selecionado': [mes_atual],
        'dash_contrato_selecionado': opts["contrato"],
        'dash_tipo_selecionado': ['CONTRATO'],
        'dash_estabelecimento_selecionado': opts["estab"],
        'dash_status_selecionado': ['LANÇADO'],
        'dash_classificacao_selecionada': opts["class"]
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    def selecionar_todos(chave, opcoes):
        st.session_state[chave] = opcoes

    def limpar_selecao(chave):
        st.session_state[chave] = []

    with st.sidebar.expander("Filtros do Dashboard", expanded=True):
        filters_config = [
            ("Ano", opts["ano"], "dash_ano_selecionado"),
            ("Mês", opts["mes"], "dash_mes_selecionado"),
            ("Contrato", opts["contrato"], "dash_contrato_selecionado"),
            ("Tipo", opts["tipo"], "dash_tipo_selecionado"),
            ("Estabelecimento", opts["estab"], "dash_estabelecimento_selecionado"),
            ("Status", opts["status"], "dash_status_selecionado"),
            ("Classificação", opts["class"], "dash_classificacao_selecionada")
        ]

        for label, options, key in filters_config:
            st.multiselect(label, options=options, key=key)
            c1, c2 = st.columns(2)
            c1.button("Todos", on_click=selecionar_todos, args=(key, options), key=f'btn_all_{key}', use_container_width=True)
            c2.button("Limpar", on_click=limpar_selecao, args=(key,), key=f'btn_clr_{key}', use_container_width=True)

def show_dashboard():
    st.title("Dashboard de Despesas")
    st.divider()

    tab_geral, tab_gantt = st.tabs(["Gastos e Faturamento", "Contratos Gantt"])
    
    with tab_geral:
        parcelas_df = load_data("parcelas")
        if parcelas_df.empty:
            st.warning("Não foi possível carregar os dados. O dashboard não pode ser exibido.")
            return

        show_filters(parcelas_df)

        df_filtrado, df_mensal, df_hcompany = filtrar_dados_dashboard(parcelas_df)

        main_col, side_col = st.columns([2.5, 1.7])
        
        with main_col:
            with st.container(border=True):
                if not df_mensal.empty:
                    st.plotly_chart(plot_despesa_mensal(df_mensal), use_container_width=True)
                else:
                    st.info("Nenhum dado de despesa mensal para exibir.")

            if not df_filtrado.empty:
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1, st.container(border=True):
                    st.plotly_chart(plot_total_estabelecimento_bar(df_filtrado), use_container_width=True)
                with sub_col2, st.container(border=True):
                    st.plotly_chart(plot_classificacao(df_filtrado), use_container_width=True)
            else:
                st.info("Nenhum dado de estabelecimento para exibir.")

        with side_col:
            with st.container(border=True):
                if not df_filtrado.empty:
                    fig = plot_top_prestadores(df_filtrado)
                    fig.update_layout(height=450)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhum dado para o Top 10 Prestadores.")

            with st.container(border=True):
                st.plotly_chart(plot_faturamento_hcompany(df_hcompany, st.session_state.dash_ano_selecionado), use_container_width=True)

    with tab_gantt:
        contratos_df = load_data("contratos")
        if not contratos_df.empty:
            st.plotly_chart(plot_gantt_contratos(contratos_df), use_container_width=False)
        else:
            st.warning("Sem dados de contratos para exibir o Gantt.")

if __name__ == "__main__":
    show_dashboard()