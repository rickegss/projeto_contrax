import time
import streamlit as st
import pandas as pd
from utils.stamp import now, mes_atual, ano_atual, data_lanc, mes_dict
from utils.pdf_extractor import extract_pdf 
from supabase import create_client, Client
from _pages.contratos import contratos, show_stats
from _pages.dashboard import show_dashboard
import base64


# --- Conexão com o Supabase ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

@st.cache_data(ttl=300) # recarregar os dados a cada 5 minutos
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
    if table_name == "parcelas":
        for col in ["data_lancamento", "data_emissao", "data_vencimento"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    
            df[["tipo", "contrato", "estabelecimento", "status"]] = df[["tipo", "contrato", "estabelecimento", "status"]].astype("category") 
            month_display_map = {v: k for k, v in mes_dict.items()}
            df['mes_nome'] = df['mes'].apply(lambda x: month_display_map.get(x, f'Mês {x}'))

    return df

# Funções de callback para os botões "Todos" e "Limpar"
def selecionar_todos(chave_estado, opcoes):
    st.session_state[chave_estado] = opcoes

def limpar_selecao(chave_estado):
    st.session_state[chave_estado] = []

def home():
    st.set_page_config(
    page_title="ContraX",
    page_icon='logo/ContraX_Favicon.png',
    layout="wide",
    )

   


    st.title("Lançamento de Parcelas")
    st.divider()


    try:
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
                st.session_state.home_status_selecionado = 'ABERTO'
            if "home_situacao_selecionado" not in st.session_state:
                st.session_state.home_situacao_selecionado = 'ATIVO'


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
                st.segmented_control("Status", options=status_disponiveis, key='home_status_selecionado')
            
            with col5:
                st.segmented_control("Situação", options=situacao_disponiveis, key='home_situacao_selecionado')


        # --- Aplicação dos Filtros e Exibição do DataFrame ---
        df_filter = df[
            (df["ano"].isin(st.session_state.home_ano_selecionado)) &
            (df["mes_nome"].isin(st.session_state.home_mes_selecionado)) &
            (df["contrato"].isin(st.session_state.home_contrato_selecionado)) &
            (df["situacao"] == (st.session_state.home_situacao_selecionado)) &
            (df["status"] == (st.session_state.home_status_selecionado))
        ]

        df_show = df_filter.drop(columns=["data_lancamento", 'documento', "mes_nome", "classificacao", "situacao", "contrato_id", "id", 'mes', 'data_vencimento', 'referente']) if "ABERTO" in st.session_state.home_status_selecionado else df_filter.drop(columns=['mes','classificacao', 'data_emissao', 'situacao', 'id', 'contrato_id', 'status','mes_nome'])

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
            "valor": st.column_config.NumberColumn("Valor da Parcela", format='R$ %.2f')
        }, hide_index=True)

        show_stats(df_show, "valor")

        st.divider()

        tab_lancar, tab_modificar, tab_duplicar, tab_excluir = st.tabs([
            " Lançar Parcela ", " Modificar / Reverter ", " Duplicar Parcela ", " Excluir Parcela "
        ])


    # --- Aba 1: Lançar Parcela ---
        with tab_lancar:
            st.subheader("Lançar Nova Parcela")


            filtro_lancaveis = (df["status"] == "ABERTO") & (df["mes"] == df_filter["mes"].iloc[0]) & (df["ano"] == df_filter["ano"].iloc[0])
            parcelas_lancaveis = df[filtro_lancaveis].sort_values(by="contrato", ascending=True)

            if parcelas_lancaveis.empty:
                st.warning("Não há parcelas em aberto para o mês e ano atuais.", icon="🚨")
            else:
                options_box = {
                    f"{row['contrato']} | {row['id']}": row['id'] 
                    for index, row in parcelas_lancaveis.iterrows()
                }
                
                uploaded_file = st.file_uploader("1. Anexar Documento Fiscal (Opcional)", type=["pdf"], key="file_uploader_lancar")
                
                valor_extraido_str, doc_extraido = "", ""
                if uploaded_file:
                    info = extract_pdf(uploaded_file)
                    valor_extraido = info.get('valor', '')
                    doc_extraido = info.get('numero', '')
                    if not valor_extraido or not doc_extraido:
                        st.info('Não foi possível extrair todos os dados do PDF. Complete manualmente.')


                with st.form("form_lancar", clear_on_submit=True):
                    st.subheader("2. Confirmar Lançamento")

                    contrato_lanc = st.selectbox("Contrato para Lançamento:", options=list(options_box.keys()))
                    valor_lanc = st.number_input("Valor R$", value=None, placeholder="Ex: 1234,56", format="%.2f", step=1.0, min_value=0.01)
                    doc_lanc = st.text_input("Número do Documento", value=doc_extraido)
                    
                    if st.form_submit_button("Confirmar Lançamento"):
                        if not contrato_lanc or not valor_lanc or valor_lanc <= 0:
                            st.warning("É necessário selecionar um contrato e preencher um valor válido.", icon="🚨")
                        else:
                            try:
                                id_lanc = options_box[contrato_lanc] 
                                if df_filter["mes"].iloc[0] == mes_atual:
                                    update_data = {
                                        "valor": valor_lanc, "data_lancamento": data_lanc.isoformat(),
                                        "documento": doc_lanc, "status": "LANÇADO"
                                    }
                                else:
                                    update_data = {
                                        "valor": valor_lanc, "data_lancamento": data_lanc.isoformat(),
                                        "documento": doc_lanc, "status": "LANÇADO"
                                    }

                                upd = supabase.table("parcelas").update(update_data).eq("id", id_lanc).execute()
                                
                                if upd.data:
                                    st.success("Parcela atualizada com sucesso! ✅")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Nenhuma parcela encontrada com este ID para atualização.", icon="❌")
                            except ValueError as e:
                                st.error(f"""O valor informado é inválido!
                                        Erro: {e}""", icon="❌")
                            except Exception as e:
                                st.error(f"Ocorreu um erro inesperado: {e}", icon="❌")



    # --- Aba 2: Modificar / Reverter ---
            with tab_modificar:
                col_mod, col_rev = st.columns(2)
                with col_mod:
                    st.subheader("Alterar Lançamento")
                    filtro_modificar = (df["ano"] == df_filter["ano"].iloc[0]) & (df["mes"] == df_filter["mes"].iloc[0]) & (df["status"] == 'LANÇADO')
                    df_modificar = df[filtro_modificar].sort_values(by="contrato", ascending=True)
                    contratos_modificar = df_modificar["contrato"].dropna().unique()

                    contrato_mod = st.selectbox("Contrato a modificar parcela:", options=contratos_modificar)
                    parcelas_modificar = df[(df["contrato"] == contrato_mod) & (df['status'] == 'LANÇADO') & (df["mes"] == df_filter["mes"].iloc[0]) & (df["ano"] == df_filter["ano"].iloc[0])]

                    opcoes_mod = [f"{row['id']} | {row['contrato']} | N° {row['documento']} | R$ {row['valor']}" for index, row in parcelas_modificar.iterrows()]
                    parcela_mod = st.radio("Parcela a modificar:", options=opcoes_mod, key="radio_mod_parcela")

                    id_parcela_mod = int(parcela_mod.split(" | ")[0])
                    parcela_original = df_modificar[df_modificar['id'] == id_parcela_mod]

                    novo_valor = st.number_input("Valor R$", value=parcela_original["valor"].iloc[0], format="%.2f", step=1.0, min_value=0.01)
                    novo_doc = st.text_input("N° Documento", value=parcela_original["documento"].iloc[0])

                    with st.form("form_alterar", clear_on_submit=True):
                        if st.form_submit_button("Confirmar Alteração"):
                            if (novo_valor is None or not novo_doc):
                                st.warning("Preencha número do documento e valor.", icon="🚨")
                                
                            else:
                                data_atualizar = {}
                                if novo_valor is not None and novo_valor > 0: 
                                    data_atualizar["valor"] = novo_valor
                                    
                                if novo_doc:
                                    data_atualizar["documento"] = novo_doc
                                
                                if data_atualizar:
                                    res = supabase.table("parcelas").update(data_atualizar).eq("id", id_parcela_mod).execute()

                                    if res.data:
                                        st.success("Parcela atualizada com sucesso! ✅")
                                        st.cache_data.clear()
                                        st.rerun()
                                    else: st.error("ID não encontrado ou falha na atualização.", icon="❌")
                                    
                                else:
                                    st.warning("Nenhum dado válido fornecido para a atualização.", icon="🚨")

                with col_rev:
                    with st.form("form_reverter", clear_on_submit=True):
                        st.subheader("Desfazer Lançamento")
                        st.text("Clique no botão abaixo para cancelar o lançamento da parcela:")

                        if st.form_submit_button("Cancelar Lançamento"):
                            if id_parcela_mod:
                                update_data = {"valor": None, "documento": None, "data_lancamento": None, "status": "ABERTO"}
                                res = supabase.table("parcelas").update(update_data).eq("id", id_parcela_mod).execute()
                                if res.data:
                                    st.success("Parcela revertida com sucesso! ✅")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("ID não encontrado ou falha ao reverter.", icon="❌")
                            else:
                                st.warning("Por favor, insira um ID para reverter.", icon="🚨")


            # --- Aba 3: Duplicar Parcela ---
            with tab_duplicar:
                st.subheader("Duplicar Parcela de Contrato")
                filtro_contratos = (df['mes'] == df_filter['mes'].iloc[0]) & (df['ano'] == df_filter['ano'].iloc[0]) & (df['situacao'] == 'ATIVO')

                contratos_duplicaveis = df.loc[filtro_contratos, 'contrato'].dropna().unique()

                if contratos_duplicaveis.size == 0:
                    st.warning("Não há contratos com parcelas no período atual para duplicar.", icon="🚨")
                else:
                    contrato_dup = st.selectbox('Selecione o Contrato:', options=contratos_duplicaveis, key="select_dup_contrato")
                    df_abertas = df[(df['contrato'] == contrato_dup) & (df['situacao'] == 'ATIVO') & (df["mes"] == df_filter['mes'].iloc[0]) & (df['ano'] == df_filter['ano'].iloc[0])]
                    
                    if df_abertas.empty:
                        st.info("Não há parcelas disponíveis para este contrato.")
                    else:
                        opcoes_dup = [f"{row['id']} | {row['contrato']} | {row['referente']}" for index, row in df_abertas.iterrows()]

                        with st.form('form_duplicar', clear_on_submit=True):
                            parcela_dup = st.radio("Parcela a duplicar:", options=opcoes_dup, key="radio_dup_parcela")
                            qtd_dup = st.number_input('Adicionar quantas parcelas?:', min_value=1, value=1, step=1)
                            
                            if st.form_submit_button('Confirmar Duplicação'):
                                if not parcela_dup:
                                    st.error("Nenhuma parcela foi selecionada.", icon="❌")
                                else:
                                    try:
                                        id_parcela_dup = int(parcela_dup.split(" | ")[0])
                                        parcela_original_df = df_abertas[df_abertas['id'] == id_parcela_dup]

                                        if parcela_original_df.empty:
                                            st.error("ID não encontrado. Verifique na tabela acima e tente novamente.", icon="❌")
                                        else:
                                            parcela = parcela_original_df.iloc[0].to_dict()
                                            duplicatas = []
                                            campos_para_remover = ['id', 'data_lancamento', 'mes_nome']
                                            
                                            for _ in range(qtd_dup):
                                                new_dup = parcela.copy()
                                                for campo in campos_para_remover: new_dup.pop(campo, None)
                                                for k, v in new_dup.items():
                                                    if pd.isna(v):
                                                        new_dup[k] = None
                                                    elif isinstance(v, pd.Timestamp):
                                                        new_dup[k] = v.isoformat()
                                                new_dup.update({
                                                    'status': 'ABERTO',
                                                    'valor': None,
                                                    'documento': None
                                                })

                                                duplicatas.append(new_dup)

                                            supabase.table("parcelas").insert(duplicatas).execute()
                                            st.success(f"{qtd_dup} parcela(s) duplicada(s) com sucesso! ✅")
                                            time.sleep(0.7)
                                            st.cache_data.clear()
                                            st.rerun()

                                    except ValueError as e:
                                        st.error(f"ID inválido. Por favor, insira um número de ID válido. Erro: {e}", icon="❌")
                                    except Exception as e:
                                        st.error(f"Falha na duplicação. Erro: {e}", icon="❌")


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
                                    time.sleep(0.7)
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("ID não encontrado. Verifique o ID e tente novamente.", icon="❌")
                            except Exception as e:
                                st.error(f"Ocorreu um erro ao excluir: {e}", icon="❌")
                        else:
                            st.warning("Por favor, insira um ID para excluir.", icon="🚨")

    except:
        st.error("Não foi possível carregar a tabela", icon="❌")
        

def main():
    """
    Função principal que organiza a aplicação em abas.
    """
    logo1, logo2 = st.columns([0.2, 1])
    with logo1:
         st.image("logo/ContraX_Logo.png", width=240, caption="Gestão de Contratos")
    with logo2:
         st.image("logo/hcompany_branco_intranet.png", width=200)

    tab_lancamentos, tab_contratos, tab_dashboard = st.tabs([" Lançamentos ", " Contratos ", " Dashboard "])

    with tab_lancamentos:
        home()
    
    with tab_contratos:
        contratos()

    with tab_dashboard:
        show_dashboard()

if __name__ == "__main__":
    main()