import streamlit as st
import pandas as pd
from utils.stamp import now, mes_atual, ano_atual, data_lanc, mes_dict
from utils.pdf_extractor import extract_pdf 
from supabase import create_client, Client
from _pages.contratos import contratos
from _pages.dashboard import show_dashboard



# --- Conexão com o Supabase ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

@st.cache_data(ttl=300) # Adicionado TTL para recarregar os dados a cada 5 minutos
def load_data(table_name):
    all_data = []
    offset = 0
    batch_size = 1000

    while True:
        data = supabase.table(table_name).select("*").range(offset, offset + batch_size - 1).execute()
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

def home():
    st.set_page_config(
    page_title="Gestão Contratual",
    page_icon="https://images.vexels.com/media/users/3/137610/isolated/preview/f41aac24df7e7778180e33ab75c69d88-flat-geometric-abstract-logo.png",
    layout="wide",
    )

    im, ti = st.columns([0.05, 0.95])
    with im:
     st.image("https://cdn-icons-png.flaticon.com/512/8807/8807373.png", width=65)
    with ti:
        st.title("Lançamento de Parcelas")
    st.divider()
    # --- Carregamento de Dados ---
    df = load_data("parcelas")

    # --- Seção de Filtros ---

    with st.expander("Filtros de Visualização", expanded=True):
        anos_disponiveis = df["ano"].dropna().sort_values().unique().tolist()
        meses_disponiveis = df["mes_nome"].dropna().unique().tolist()
        contratos_disponiveis = df["contrato"].dropna().sort_values().unique().tolist()
        status_disponiveis = df["status"].dropna().sort_values().unique().tolist()
        situacao_disponiveis = df["situacao"].dropna().sort_values().unique().tolist()


        if 'home_ano_selecionado' not in st.session_state:
            st.session_state.home_ano_selecionado = [ano_atual]
        if 'home_mes_selecionado' not in st.session_state:
            st.session_state.home_mes_selecionado = [mes_atual]
        if 'home_contrato_selecionado' not in st.session_state:
            st.session_state.home_contrato_selecionado = contratos_disponiveis
        if 'home_status_selecionado' not in st.session_state:
            st.session_state.home_status_selecionado = ['ABERTO']
        if "home_situacao_disponiveis" not in st.session_state:
            st.session_state.home_situacao_disponiveis = ['ATIVO']

        # Funções de callback para os botões "Todos" e "Limpar"
        def selecionar_todos(chave_estado, opcoes):
            st.session_state[chave_estado] = opcoes

        def limpar_selecao(chave_estado):
            st.session_state[chave_estado] = []


        # Layout dos filtros em colunas
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.multiselect("Ano", options=anos_disponiveis, key='home_ano_selecionado')
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('home_ano_selecionado', anos_disponiveis), key='home_btn_todos_anos')
            b_col2.button("Limpar", on_click=limpar_selecao, args=('home_ano_selecionado',), key='home_btn_limpar_anos')

        with col2:
            st.multiselect("Mês", options=meses_disponiveis, key='home_mes_selecionado')
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('home_mes_selecionado', meses_disponiveis), key='home_btn_todos_meses')
            b_col2.button("Limpar", on_click=limpar_selecao, args=('home_mes_selecionado',), key='home_btn_limpar_meses')

        with col3:
            st.multiselect("Contrato", options=contratos_disponiveis, key='home_contrato_selecionado')
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('home_contrato_selecionado', contratos_disponiveis), key='home_btn_todos_contratos')
            b_col2.button("Limpar", on_click=limpar_selecao, args=('home_contrato_selecionado',), key='home_btn_limpar_contratos')

        with col4:
            st.multiselect("Status", options=status_disponiveis, key='home_status_selecionado')
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('home_status_selecionado', status_disponiveis), key='home_btn_todos_status')
            b_col2.button("Limpar", on_click=limpar_selecao, args=('home_status_selecionado',), key='home_btn_limpar_status')
        
        with col5:
            st.multiselect("Situação", options=situacao_disponiveis, key='home_situacao_selecionado')
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('home_situacao_selecionado', situacao_disponiveis), key='home_btn_todos_situacao')
            b_col2.button("Limpar", on_click=limpar_selecao, args=('home_situacao_selecionado',), key='home_btn_limpar_situacao')
    

    # --- Aplicação dos Filtros e Exibição do DataFrame ---
    df_filter = df[
        (df["ano"].isin(st.session_state.home_ano_selecionado)) &
        (df["mes_nome"].isin(st.session_state.home_mes_selecionado)) &
        (df["contrato"].isin(st.session_state.home_contrato_selecionado)) &
        (df["situacao"].isin(st.session_state.home_situacao_selecionado)) &
        (df["status"].isin(st.session_state.home_status_selecionado))
    ]

    df_show = df_filter.drop(columns=["data_lancamento", 'documento', "mes_nome", "situacao"]) if "ABERTO" in st.session_state.home_status_selecionado else df_filter.drop(columns=["mes_nome"])

    st.dataframe(df_show, column_config={
        "id": st.column_config.TextColumn("ID", width="small"),
        "ano": st.column_config.TextColumn("Ano", width="small"),
        "mes": st.column_config.TextColumn("Mês", width="small"),
        "data_lancamento": st.column_config.DateColumn("Data de Lançamento", format="DD/MM/YY", width="small"),
        "data_emissao": st.column_config.DateColumn("Emissão", format="DD/MM", width="small"),
        "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM", width="small"),
        "tipo": st.column_config.TextColumn("Tipo", width="small"),
        "contrato": st.column_config.TextColumn("Contrato", width="small"),
        "referente": st.column_config.TextColumn("Referente", width="small"),
        "documento": st.column_config.TextColumn("N° Documento", width="small"),
        "estabelecimento": st.column_config.TextColumn("Estabelecimento", width="small"),
        "status": st.column_config.TextColumn("Status", width="small"),
        "valor": st.column_config.NumberColumn("Valor da Parcela", format='R$ %.2f')
    }, hide_index=True)

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
            
            valor_extraido_str, doc_extraido = "", ""
            if uploaded_file:
                info = extract_pdf(uploaded_file)
                valor_extraido_str = str(info.get('valor', ''))
                doc_extraido = str(info.get('numero', ''))
                if not valor_extraido_str or not doc_extraido:
                    st.info('Não foi possível extrair todos os dados do PDF. Preencha manualmente.')

            # --- INÍCIO DA CORREÇÃO ---
            # Trata o valor extraído para garantir que seja float ou None
            valor_inicial_input = None
            if valor_extraido_str:  # Apenas tenta converter se a string não for vazia
                try:
                    # Lida com formatos como "1.234,56"
                    valor_limpo = valor_extraido_str.replace('.', '').replace(',', '.')
                    valor_inicial_input = float(valor_limpo)
                except (ValueError, TypeError):
                    # Se a conversão falhar, o valor continua None e o campo fica vazio
                    valor_inicial_input = None
            # --- FIM DA CORREÇÃO ---

            with st.form("form_lancar", clear_on_submit=True):
                st.subheader("2. Confirmar Lançamento")
                contrato_lanc = st.selectbox("Contrato para Lançamento:", options=contratos_lancaveis)
                
                # Usa a variável tratada (valor_inicial_input) ao invés da string original
                valor_lanc = st.number_input("Valor R$", value=valor_inicial_input, placeholder="Ex: 1234,56", format="%.2f", step=1.0, min_value=0.01)
                
                doc_lanc = st.text_input("Número do Documento", value=doc_extraido)
                
                if st.form_submit_button("Confirmar Lançamento"):
                    if not contrato_lanc or not valor_lanc or valor_lanc <= 0:
                        st.warning("É necessário selecionar um contrato e preencher um valor válido.")
                    else:
                        try:
                            update_data = {
                                "valor": valor_lanc, "data_lancamento": data_lanc.isoformat(),
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
            with st.form("form_alterar", clear_on_submit=True):
                st.subheader("Alterar Lançamento")
                id_alt = st.text_input("ID da parcela")
                novo_valor = st.number_input("Novo Valor R$ (opcional)", value=None, format="%.2f", placeholder="Deixe em branco para não alterar", step=1.0, min_value=0.01)
                novo_doc = st.text_input("Novo N° Documento (opcional)")

                if st.form_submit_button("Confirmar Alteração"):
                    if not id_alt or (novo_valor is None and not novo_doc):
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
            with st.form("form_reverter", clear_on_submit=True):
                st.subheader("Reverter Status para 'Aberto'")
                id_rev = st.text_input("ID da parcela a desfazer o lançamento")

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
            df_abertas = df[(df['contrato'] == contrato_dup) & (df['status'] == 'ABERTO') & (df["mes"] == now.month) & (df['ano'] == ano_atual)]
            
            if df_abertas.empty:
                st.info("Não há parcelas abertas para este contrato.")
            else:
                st.info("Abaixo estão as parcelas disponíveis para duplicação. Copie o ID desejado.")
                st.dataframe(df_abertas[['id', 'referente', 'valor', 'mes_nome', 'ano']], column_config={
                    "id": st.column_config.TextColumn("ID", width="small"),
                    "referente": st.column_config.TextColumn("Referente", width="small"),
                    "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f", width="small"),
                    "mes_nome": st.column_config.TextColumn("Mês", width="small"),
                    "ano": st.column_config.TextColumn("Ano", width="small")
                }, hide_index=True)

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
            id_exc = st.text_input('ID da linha para exclusão')
            
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

    tab_lancamentos, tab_contratos, tab_dashboard = st.tabs([" Lançamentos ", " Contratos ", " Dashboard "])

    with tab_lancamentos:
        home()
    
    with tab_contratos:
        contratos()

    with tab_dashboard:
        show_dashboard()

if __name__ == "__main__":
    main()