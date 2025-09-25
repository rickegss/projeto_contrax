import streamlit as st
import pandas as pd
from utils.stamp import now, mes_atual, ano_atual, data_lanc, mes_dict
from utils.pdf_extractor import extract_pdf 
from supabase import create_client, Client
from _pages.contratos import contratos
from _pages.dashboard import show_dashboard


def home():

    # --- Conexão com o Supabase ---
    url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
    key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    # --- Carregamento e Cache de Dados ---
    @st.cache_data(ttl=300) # Adicionado TTL para recarregar os dados a cada 5 minutos
    def load_data():
        all_data = []
        offset = 0
        batch_size = 1000

        while True:
            data = supabase.table("parcelas").select("*").range(offset, offset + batch_size - 1).execute()
            if not data.data:
                break
            all_data.extend(data.data)
            offset += batch_size

        df = pd.DataFrame(all_data)
        
        # Conversão de colunas de data e otimização de tipos de dados
        for col in ["data_lancamento", "data_emissao", "data_vencimento"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        df[["tipo", "contrato", "estabelecimento", "status"]] = df[["tipo", "contrato", "estabelecimento", "status"]].astype("category") 
        month_display_map = {v: k for k, v in mes_dict.items()}
        df['mes_nome'] = df['mes'].apply(lambda x: month_display_map.get(x, f'Mês {x}'))
        return df

    df = load_data()

    # --- Seção de Filtros Otimizada com st.expander ---
    # O expander permite que o usuário oculte os filtros para focar na tabela.
    with st.expander("Filtros de Visualização", expanded=True):
        # Define as opções dos filtros para evitar repetição de código
        anos_disponiveis = df["ano"].dropna().sort_values().unique().tolist()
        meses_disponiveis = df["mes_nome"].dropna().unique().tolist()
        contratos_disponiveis = df["contrato"].dropna().sort_values().unique().tolist()
        status_disponiveis = df["status"].dropna().sort_values().unique().tolist()

        # Inicializa o st.session_state para manter o estado dos filtros entre re-renderizações
        if 'ano_selecionado' not in st.session_state:
            st.session_state.ano_selecionado = [ano_atual]
        if 'mes_selecionado' not in st.session_state:
            st.session_state.mes_selecionado = [mes_atual]
        if 'contrato_selecionado' not in st.session_state:
            st.session_state.contrato_selecionado = contratos_disponiveis
        if 'status_selecionado' not in st.session_state:
            st.session_state.status_selecionado = ['ABERTO']

        # Funções de callback para os botões "Todos" e "Limpar"
        def selecionar_todos(chave_estado, opcoes):
            st.session_state[chave_estado] = opcoes

        def limpar_selecao(chave_estado):
            st.session_state[chave_estado] = []

        # Layout dos filtros em colunas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.multiselect("Ano", options=anos_disponiveis, key='ano_selecionado')
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('ano_selecionado', anos_disponiveis), key='btn_todos_anos', use_container_width=True)
            b_col2.button("Limpar", on_click=limpar_selecao, args=('ano_selecionado',), key='btn_limpar_anos', use_container_width=True)

        with col2:
            st.multiselect("Mês", options=meses_disponiveis, key='mes_selecionado')
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('mes_selecionado', meses_disponiveis), key='btn_todos_meses', use_container_width=True)
            b_col2.button("Limpar", on_click=limpar_selecao, args=('mes_selecionado',), key='btn_limpar_meses', use_container_width=True)

        with col3:
            st.multiselect("Contrato", options=contratos_disponiveis, key='contrato_selecionado')
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('contrato_selecionado', contratos_disponiveis), key='btn_todos_contratos', use_container_width=True)
            b_col2.button("Limpar", on_click=limpar_selecao, args=('contrato_selecionado',), key='btn_limpar_contratos', use_container_width=True)

        with col4:
            st.multiselect("Status", options=status_disponiveis, key='status_selecionado')
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('status_selecionado', status_disponiveis), key='btn_todos_status', use_container_width=True)
            b_col2.button("Limpar", on_click=limpar_selecao, args=('status_selecionado',), key='btn_limpar_status', use_container_width=True)
    
    # --- Aplicação dos Filtros e Exibição do DataFrame ---
    df_filter = df[
        (df["ano"].isin(st.session_state.ano_selecionado)) &
        (df["mes_nome"].isin(st.session_state.mes_selecionado)) &
        (df["contrato"].isin(st.session_state.contrato_selecionado)) &
        (df["status"].isin(st.session_state.status_selecionado))
    ]
    st.dataframe(df_filter)

    st.divider()

    tab_lancar, tab_modificar, tab_duplicar, tab_excluir = st.tabs([
        " Lançar Parcela ", " Modificar / Reverter ", " Duplicar Parcela ", " Excluir Parcela "
    ])

    # --- Aba 1: Lançar Parcela ---
    with tab_lancar:
        st.subheader("Lançar Nova Parcela")
        try:
            res = supabase.table("parcelas").select("contrato").eq("mes", now.month).eq("ano", ano_atual).eq("status", "ABERTO").execute()
            contratos_lancaveis = sorted({r.get("contrato") for r in res.data if r.get("contrato")})
        except Exception as e:
            st.error(f"Erro ao consultar o banco de dados: {e}")
            contratos_lancaveis = []

        if not contratos_lancaveis:
            st.warning("Não há parcelas em aberto para o mês e ano atuais.")
        else:
            uploaded_file = st.file_uploader("1. Anexar Documento Fiscal (Opcional)", type=["pdf"], key="file_uploader_lancar")
            valor_extraido, doc_extraido = "", ""
            if uploaded_file:
                info = extract_pdf(uploaded_file)
                valor_extraido = str(info.get('valor', '')) 
                doc_extraido = str(info.get('numero', ''))
                if not valor_extraido or not doc_extraido:
                    st.info('Não foi possível extrair todos os dados do PDF. Preencha manualmente.')

            with st.form("form_lancar", clear_on_submit=True):
                st.subheader("2. Confirmar Lançamento")
                contrato_lanc = st.selectbox("Contrato para Lançamento:", options=contratos_lancaveis)
                valor_lanc = st.text_input("Valor R$", value=valor_extraido, placeholder="Ex: 1234,56")
                doc_lanc = st.text_input("Número do Documento", value=doc_extraido)
                
                if st.form_submit_button("Confirmar Lançamento"):
                    if not contrato_lanc or not valor_lanc:
                        st.warning("É necessário selecionar um contrato e preencher um valor válido.")
                    else:
                        try:
                            valor = float(valor_lanc.replace(".", "").replace(",", "."))
                            update_data = {
                                "valor": valor, "data_lancamento": data_lanc.isoformat(),
                                "documento": doc_lanc, "status": "LANÇADO"
                            }
                            upd = supabase.table("parcelas").update(update_data).eq("contrato", contrato_lanc).eq("mes", now.month).eq("ano", ano_atual).eq("status", "ABERTO").execute()
                            
                            if upd.data:
                                st.success("Parcela atualizada com sucesso! ✅")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Nenhuma parcela 'ABERTA' encontrada para este contrato no período atual.")
                        except ValueError:
                            st.error("O valor informado é inválido!")

    # --- Aba 2: Modificar / Reverter ---
    with tab_modificar:
        col_mod, col_rev = st.columns(2)
        with col_mod:
            with st.form("form_alterar"):
                st.subheader("Alterar Lançamento")
                id_alt = st.text_input("ID da parcela")
                novo_valor = st.number_input("Novo Valor R$ (opcional)", format="%.2f")
                novo_doc = st.text_input("Novo N° Documento (opcional)")

                if st.form_submit_button("Confirmar Alteração"):
                    if not id_alt or (novo_valor <= 0 and not novo_doc):
                        st.warning("Preencha o ID e pelo menos um campo para alterar.")
                    else:
                        data_atualizar = {}
                        if novo_valor is not None and novo_valor > 0: data_atualizar["valor"] = novo_valor
                        if novo_doc: data_atualizar["documento"] = novo_doc
                        
                        if data_atualizar:
                            res = supabase.table("parcelas").update(data_atualizar).eq("id", id_alt).execute()
                            if res.data:
                                st.success("Parcela atualizada com sucesso! ✅")
                                st.cache_data.clear()
                                st.rerun()
                            else: st.error("ID não encontrado ou falha na atualização.")
                        else:
                            st.warning("Nenhum dado válido fornecido para a atualização.")
        with col_rev:
            with st.form("form_reverter"):
                st.subheader("Reverter Status para 'Aberto'")
                id_rev = st.text_input("ID da linha para reverter")

                if st.form_submit_button("Confirmar Reversão"):
                    if id_rev:
                        update_data = {"valor": None, "documento": None, "data_lancamento": None, "status": "ABERTO"}
                        res = supabase.table("parcelas").update(update_data).eq("id", id_rev).execute()
                        if res.data:
                            st.success("Parcela revertida com sucesso! ✅")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("ID não encontrado ou falha ao reverter.")
                    else:
                        st.warning("Por favor, insira um ID para reverter.")

    # --- Aba 3: Duplicar Parcela ---
    with tab_duplicar:
        st.subheader("Duplicar Parcela em Aberto")
        filtro_contratos = (df['mes'] == now.month) & (df['ano'] == ano_atual) & (df['status'] == 'ABERTO')
        contratos_duplicaveis = df.loc[filtro_contratos, 'contrato'].dropna().unique()

        if contratos_duplicaveis.size == 0:
            st.warning("Não há contratos com parcelas abertas no período atual para duplicar.")
        else:
            contrato_dup = st.selectbox('Selecione o Contrato:', options=contratos_duplicaveis, key="select_dup_contrato")
            df_abertas = df[(df['contrato'] == contrato_dup) & (df['status'] == 'ABERTO')]
            
            if df_abertas.empty:
                st.info("Não há parcelas abertas para este contrato.")
            else:
                st.info("Abaixo estão as parcelas disponíveis para duplicação. Copie o ID desejado.")
                st.dataframe(df_abertas[['id', 'referente', 'valor', 'mes_nome', 'ano']])

                with st.form('form_duplicar', clear_on_submit=True):
                    id_parcela_dup_input = st.text_input("Cole o ID da parcela a duplicar")
                    qtd_dup = st.number_input('Adicionar quantas parcelas?:', min_value=1, value=1, step=1)
                    
                    if st.form_submit_button('Confirmar Duplicação'):
                        if not id_parcela_dup_input:
                            st.error("O campo 'ID da parcela' é obrigatório.")
                        else:
                            try:
                                id_parcela_dup = int(id_parcela_dup_input)
                                parcela_original_df = df_abertas[df_abertas['id'] == id_parcela_dup]

                                if parcela_original_df.empty:
                                    st.error("ID não encontrado. Verifique na tabela acima e tente novamente.")
                                else:
                                    parcela = parcela_original_df.iloc[0].to_dict()
                                    duplicatas = []
                                    campos_para_remover = ['id', 'data_lancamento', 'mes_nome']
                                    
                                    for _ in range(qtd_dup):
                                        new_dup = parcela.copy()
                                        for campo in campos_para_remover: new_dup.pop(campo, None)
                                        for col_data in ['data_vencimento', 'data_emissao']:
                                            if col_data in new_dup and pd.notna(new_dup[col_data]):
                                                new_dup[col_data] = new_dup[col_data].isoformat()
                                            else:
                                                new_dup[col_data] = None
                                        duplicatas.append(new_dup)

                                    supabase.table("parcelas").insert(duplicatas).execute()
                                    st.success(f"{qtd_dup} parcela(s) duplicada(s) com sucesso! ✅")
                                    st.cache_data.clear()
                                    st.rerun()
                            except ValueError:
                                st.error("ID inválido. Por favor, insira um número de ID válido.")
                            except Exception as e:
                                st.error(f"Falha na duplicação. Erro: {e}")

    # --- Aba 4: Excluir Parcela ---
    with tab_excluir:
        st.subheader("Excluir Parcela")
        st.warning("Atenção: A exclusão é permanente e não pode ser desfeita.", icon="⚠️")
        with st.form('form_excluir', clear_on_submit=True):
            id_exc = st.text_input('ID da linha a ser excluída:')
            
            if st.form_submit_button('Confirmar Exclusão', type="primary"):
                if id_exc:
                    try:
                        response = supabase.table("parcelas").delete().eq("id", id_exc).execute()
                        if response.data:
                            st.success(f"Linha {id_exc} excluída com sucesso.")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("ID não encontrado. Verifique o ID e tente novamente.")
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao excluir: {e}")
                else:
                    st.warning("Por favor, insira um ID para excluir.")

# Ponto de entrada do script
def main():
    """
    Função principal que organiza a aplicação em abas.
    """
    st.set_page_config(
        page_title="Gestão Contratual",
        page_icon="https://i.redd.it/ziae62jnvw5e1.png",
        layout="wide",
    )
    st.title("Lançamento de Parcelas")

    tab_lancamentos, tab_contratos, tab_dashboard = st.tabs([" Lançamentos ", " Contratos ", " Dashboard "])

    with tab_lancamentos:
        home()
    
    with tab_contratos:
        contratos()

    with tab_dashboard:
        show_dashboard()

if __name__ == "__main__":
    main()
