import pandas as pd
import streamlit as st
from services.contratos_service import new_contract, delete_contract, active_deactive_contract, edit_contract, renew_contract, relatorio_anual
from utils.stamp import ano_atual
import io
from core.database_connections import load_data
from utils.formatters import formatar_brl

def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
    return output.getvalue()

def show_stats(df, coluna_valor, parcelas_df) -> None:
    count = len(df)
    total = df[coluna_valor].sum()
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style='width: 100%; text-align: left;'>
            <div style='display: inline-block; border: 2px solid; padding: 3px 10px; border-radius: 25px; font-size: 15px; width: 20%;'>
                Contagem: {count}
            </div>
        </div>    
        """, unsafe_allow_html=True)

    with col2:
        chave_unica = f"contrato_bttn_relatorio_{coluna_valor}"
        if st.button("Gerar relatório Anual", key=chave_unica):
            df_styled = relatorio_anual(parcelas_df)
            st.dataframe(df_styled)
            
            st.download_button(
                label=" 📥 Exportar para Excel",
                data=to_excel(df_styled.data),
                file_name=f"relatorio_anual_{ano_atual}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_excel_{chave_unica}" 
            )
            if st.button(" ↩️ Fechar relatório", key=f"contrato_bttn_fechar_{coluna_valor}"):
                st.rerun()

    with col3:
        val_str = "0,00" if total is None else formatar_brl(total)
        st.markdown(f"""
        <div style='width: 100%; text-align: right;'>
            <div style='display: inline-block; border: 2px solid; padding: 3px 10px; border-radius: 25px; font-size: 15px; width: 25%;'>
                Total: R$ {val_str}
            </div>
        </div>
        """, unsafe_allow_html=True)

def initialize_state(df, filters) -> None:
    if "initialized_contratos" in st.session_state:
        return
    
    st.session_state.initialized_contratos = True
    for key in filters:
        st.session_state[f"toggle_{key}"] = True
    
        if f'contratos_{key}_selecionado' not in st.session_state:
            if key in ['contrato', 'estabelecimento', 'classificacao']:
                st.session_state[f'contratos_{key}_selecionado'] = df[key].dropna().sort_values().unique().tolist()
            elif key == 'pedido':
                st.session_state[f'contratos_pedido_selecionado'] = ['Contrato']

    if 'contratos_situacao_selecionado' not in st.session_state:
        st.session_state[f'contratos_situacao_selecionado'] = ["ATIVO"]

def show_filters(df, filter_config) -> None:
    from .parcelas import selecionar_todos, limpar_selecao
    
    cols = st.columns(len(filter_config))
    
    labels = {
        "situacao": "Situação", "contrato": "Contratos", 
        "estabelecimento": "Estabelecimento", "classificacao": "Classificação", 
        "pedido": "Contrato/Pedido"
    }

    for i, key in enumerate(filter_config):
        with cols[i]:
            label = labels.get(key, key.capitalize())
            
            if key == "pedido":
                options = ["Contrato", "Pedido"]
            else:
                options = df[key].dropna().unique()
                if key != "situacao": 
                    options = sorted(options.tolist()) if hasattr(options, 'tolist') else sorted(options)
            
            if not isinstance(options, list) and not isinstance(options, pd.Categorical):
                 options = list(options)

            key_state = f'contratos_{key}_selecionado'
            
            st.multiselect(label, options=options, key=key_state)
            
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=(key_state, options), key=f'contratos_todos_{key}')
            b_col2.button("Limpar", on_click=limpar_selecao, args=(key_state,), key=f'contratos_limpar_{key}')
            
            if key == "pedido":
                 st.button("Recarregar tabela", on_click=st.cache_data.clear, key='contratos_atualizar')

def contratos(supabase) -> None:
    contratos_df = load_data("contratos")
    parcelas_df = load_data("parcelas")

    filter_config = ["situacao", "contrato", "estabelecimento", "classificacao", "pedido"]
    initialize_state(contratos_df, filter_config)

    st.title("Prestadores de Contratos")
    st.divider()
    
    with st.expander("Filtros de Contratos", expanded=True):
        show_filters(contratos_df, filter_config)
    
    mask = (
        contratos_df["situacao"].isin(st.session_state.contratos_situacao_selecionado) &
        contratos_df["contrato"].isin(st.session_state.contratos_contrato_selecionado) &
        contratos_df["estabelecimento"].isin(st.session_state.contratos_estabelecimento_selecionado) &
        contratos_df["classificacao"].isin(st.session_state.contratos_classificacao_selecionado)
    )
    
    if st.session_state.contratos_pedido_selecionado == ["Pedido"]:
        mask &= (contratos_df["numero"] == "PEDIDO")
    elif st.session_state.contratos_pedido_selecionado == ['Contrato']:
        mask &= (contratos_df["numero"] != "PEDIDO")

    contratos_filtrado = contratos_df[mask].drop(columns=["id", 'inicio'])
    
    st.dataframe(
        contratos_filtrado, hide_index=True, width='stretch',
        column_config={
            "situacao": st.column_config.TextColumn("Situação", width="small"),
            "numero": st.column_config.TextColumn("Número", width="small"),
            "contrato": st.column_config.TextColumn("Contrato", width="small"),
            "conta": st.column_config.TextColumn("Conta", width="small"),
            "centro_custo": st.column_config.TextColumn("Centro de Custo", width="small"),
            "estabelecimento": st.column_config.TextColumn("Estabelecimento", width="small"),
            "classificacao": st.column_config.TextColumn("Classificação", width="small"),
            "descricao": st.column_config.TextColumn("Descrição", width="small"),
            "cnpj": st.column_config.TextColumn("CNPJ", width="small"),
            "anexos": st.column_config.TextColumn("Anexos", width="small"),
            "valor_contrato": st.column_config.NumberColumn("Valor do Contrato", format='R$ %.2f'),
            "termino": st.column_config.DateColumn("Término", format="DD/MM/YY")                
        }
    )

    show_stats(contratos_filtrado, "valor_contrato", parcelas_df)
    st.divider()
    
    if "navegacao_acoes_contratos" not in st.session_state:
        st.session_state.navegacao_acoes_contratos = "Novo Contrato"

    opcoes_acao = ["Novo Contrato", "Editar Contrato", "Renovar Contrato", "Ativar/Desativar", 'Excluir Contrato']
    acao_selecionada = st.segmented_control(
        "Gerenciar Contratos:", options=opcoes_acao, 
        selection_mode="single", key="navegacao_acoes_contratos"
    )
    
    if not acao_selecionada: acao_selecionada = "Novo Contrato"
    st.write("---")

    acoes = {
        "Novo Contrato": new_contract,
        "Editar Contrato": edit_contract,
        "Renovar Contrato": renew_contract,
        "Ativar/Desativar": active_deactive_contract,
        "Excluir Contrato": delete_contract
    }
    
    if acao_selecionada in acoes:
        acoes[acao_selecionada](contratos_df, supabase)