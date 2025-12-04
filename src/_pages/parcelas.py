import streamlit as st
from src.utils.stamp import mes_atual, ano_atual
from src._pages.contratos import show_stats
from src.core.database_connections import load_data
from src.services.parcelas_service import view_lancar, view_modificar, view_adicionar, view_excluir

def selecionar_todos(chave_estado, opcoes):
    st.session_state[chave_estado] = opcoes

def limpar_selecao(chave_estado):
    st.session_state[chave_estado] = []

def render_filters(df):
    with st.expander("Filtros de Visualização", expanded=True):
        cols = st.columns(5)
        
        filters_conf = [
            ("ano", "Ano", "multiselect"),
            ("mes_nome", "Mês", "multiselect"),
            ("contrato", "Contrato", "multiselect"),
            ("status", "Status", "segmented"),
            ("situacao", "Situação", "segmented")
        ]

        defaults = {
            "ano": [ano_atual],
            "mes_nome": [mes_atual],
            "contrato": df["contrato"].dropna().sort_values().unique().tolist(),
            "status": "ABERTO",
            "situacao": "ATIVO"
        }

        for i, (col_name, label, widget_type) in enumerate(filters_conf):
            key = f'home_{col_name}_selecionado' if col_name != "mes_nome" else 'home_mes_selecionado'
            if col_name == "contrato": key = 'home_contrato_selecionado' 

            if key not in st.session_state:
                st.session_state[key] = defaults[col_name]

            options = df[col_name].dropna().unique()
            if col_name == "ano": options = sorted(options)
            if col_name == "contrato": options = sorted(options)

            with cols[i]:
                if widget_type == "multiselect":
                    st.multiselect(label, options=options, key=key)
                    c1, c2 = st.columns(2)
                    c1.button("Todos", on_click=selecionar_todos, args=(key, options), key=f'btn_all_{col_name}')
                    c2.button("Limpar", on_click=limpar_selecao, args=(key,), key=f'btn_clr_{col_name}')
                else:
                    st.segmented_control(label, options=options, key=key)


def home(supabase):
    st.title("Lançamento de Parcelas")
    st.divider()

    try:
        df = load_data("parcelas")
        render_filters(df)

        mask = (
            df["ano"].isin(st.session_state.home_ano_selecionado) &
            df["mes_nome"].isin(st.session_state.home_mes_selecionado) &
            df["contrato"].isin(st.session_state.home_contrato_selecionado) &
            (df["situacao"] == st.session_state.home_situacao_selecionado) &
            (df["status"] == st.session_state.home_status_selecionado)
        )
        df_filter = df[mask]

        cols_drop_aberto = ["data_lancamento", 'documento', "mes_nome", "classificacao", "situacao", "contrato_id", "id", 'mes', 'data_vencimento', 'referente']
        cols_drop_lancado = ['mes','classificacao', 'data_emissao', 'situacao', 'id', 'contrato_id', 'status','mes_nome']
        
        df_show = df_filter.drop(columns=cols_drop_aberto) if "ABERTO" in st.session_state.home_status_selecionado else df_filter.drop(columns=cols_drop_lancado)

        st.dataframe(df_show, column_config={
            "ano": st.column_config.TextColumn("Ano", width="small"),
            "data_lancamento": st.column_config.DateColumn("Data de Lançamento", format="DD/MM/YY", width="small"),
            "data_emissao": st.column_config.DateColumn("Emissão", format="DD/MM", width="small"),
            "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM", width="small"),
            "tipo": st.column_config.TextColumn("Tipo", width="small"),
            "contrato": st.column_config.TextColumn("Contrato", width="small"),
            "referente": st.column_config.TextColumn("Referente", width="small"),
            "documento": st.column_config.TextColumn("N° Documento", width="small"),
            "estabelecimento": st.column_config.TextColumn("Estabelecimento", width="small"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "valor": st.column_config.NumberColumn("Valor", format='R$ %.2f')
        }, hide_index=True)

        show_stats(df_show, "valor", df)
        st.divider()

        if "navegacao_acoes_parcelas" not in st.session_state:
            st.session_state.navegacao_acoes_parcelas = "Lançar Parcela"
            
        opcoes_acao = ["Lançar Parcela", "Modificar / Reverter", "Adicionar Parcela", "Excluir Parcela"]
        acao = st.segmented_control("Selecione a ação:", options=opcoes_acao, selection_mode="single", key="navegacao_acoes_parcelas")
        
        if not acao: acao = "Lançar Parcela"
        st.write("---")

        actions_map = {
            "Lançar Parcela": lambda: view_lancar(df, df_filter, supabase),
            "Modificar / Reverter": lambda: view_modificar(df, df_filter, supabase),
            "Adicionar Parcela": lambda: view_adicionar(df, df_filter, supabase),
            "Excluir Parcela": lambda: view_excluir(df, supabase)
        }
        
        if acao in actions_map:
            actions_map[acao]()

    except:
        st.error(f"Erro ao carregar, selecione os filtros corretamente.", icon="❌")