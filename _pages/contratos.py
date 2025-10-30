import pandas as pd
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client

def show_stats(df, coluna_valor):
    count = len(df)
    total = df[coluna_valor].sum()

    def formata_val(valor):
        if valor is None:
            return "0,00"
        val_str = f"{valor:,.2f}"
        val_str_br = val_str.replace(",", "X").replace(".", ",").replace("X", ".")
        return val_str_br


    colun1, colun2 = st.columns(2)

    with colun1:
        st.markdown(f"""
        <div style='width: 100%; text-align: left;'>
            <div style='display: inline-block; border: 2px solid; padding: 3px 10px; border-radius: 25px; font-size: 15px; width: 20%;'>
                Contagem: {count}
            </div>
        </div>    
        """, unsafe_allow_html=True)

    with colun2:
        st.markdown(f"""
        <div style='width: 100%; text-align: right;'>
            <div style='display: inline-block; border: 2px solid; padding: 3px 10px; border-radius: 25px; font-size: 15px; width: 25%;'>
                Total: R$ {formata_val(total)}
            </div>
        </div>
        """, unsafe_allow_html=True)


def contratos():
    url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
    key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    @st.cache_data
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
        return df

    def initialize_state(df, filters):
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


    def show_filters(df, filter_config):
        from .parcelas import selecionar_todos, limpar_selecao
        cols = st.columns(len(filter_config))
        with cols[0]:
            st.multiselect(
                "Situação", 
                options=df["situacao"].dropna().unique(), 
                key='contratos_situacao_selecionado'
            )
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('contratos_situacao_selecionado', df["situacao"].dropna().unique().tolist()), key='contratos_todos_situacao')
            b_col2.button("Limpar", on_click=limpar_selecao, args=('contratos_situacao_selecionado',), key='contratos_limpar_situacao')
        
        with cols[1]:
            st.multiselect(
                "Contratos", 
                options=df["contrato"].dropna().unique(), 
                key='contratos_contrato_selecionado'
            )
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('contratos_contrato_selecionado', df["contrato"].dropna().unique().tolist()), key='contratos_todos_contrato')
            b_col2.button("Limpar", on_click=limpar_selecao, args=('contratos_contrato_selecionado',), key='contratos_limpar_contrato')

        with cols[2]:
            st.multiselect(
                "Estabelecimento", 
                options=df["estabelecimento"].dropna().unique(), 
                key='contratos_estabelecimento_selecionado'
            )
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('contratos_estabelecimento_selecionado', df["estabelecimento"].dropna().unique().tolist()), key='contratos_todos_estabelecimento')
            b_col2.button("Limpar", on_click=limpar_selecao, args=('contratos_estabelecimento_selecionado',), key='contratos_limpar_estabelecimento')

        with cols[3]:
            st.multiselect(
                "Classificação", 
                options=df["classificacao"].dropna().unique(), 
                key='contratos_classificacao_selecionado'
            )
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('contratos_classificacao_selecionado', df["classificacao"].dropna().unique().tolist()), key='contratos_todos_classificacao')
            b_col2.button("Limpar", on_click=limpar_selecao, args=('contratos_classificacao_selecionado',), key='contratos_limpar_classificacao')

        with cols[4]:
            st.multiselect(
                "Contrato/Pedido", 
                options=["Contrato", "Pedido"], 
                key='contratos_pedido_selecionado'
            )
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=('contratos_pedido_selecionado', ["Contrato", "Pedido"]), key='contratos_todos_pedido')
            b_col2.button("Limpar", on_click=limpar_selecao, args=('contratos_pedido_selecionado',), key='contratos_limpar_pedido')

    def new_contract(df):

        ccol1, = st.columns(1)

        with ccol1:
            st.subheader("Dados do Contrato")
            
            with st.form("form_novo_contrato", clear_on_submit=True):
                contrato = st.text_input("Nome do Contrato")
                contrato = contrato.upper()
                cnpj = st.text_input("CNPJ")
                numero_contrato = st.text_input("Número do Contrato")
                estabelecimento = st.segmented_control("Estabelecimento", options=(df["estabelecimento"].dropna().unique()))
                valor_contrato = st.number_input("Valor do Contrato R$", format="%.2f", step=1.0, min_value=1.0)
                duracao = st.number_input("Duração do contrato (meses)", format="%d", min_value=1)
                conta = st.number_input("Conta", step=1.0)
                conta = str(float(conta))
                centro_custo = st.number_input("Centro de Custo", step=1.0)
                centro_custo = str(float(centro_custo))
                classificacao = st.segmented_control("Classificação", options=df["classificacao"].dropna().unique())  
                categoria = st.segmented_control("Categoria", options=df["categoria"].dropna().unique())
                data_inicio = st.date_input("Data de Início", value=datetime.now().date())
                valor_parcela = valor_contrato / duracao
                duracao_delta = relativedelta(months=duracao)
                data_termino = data_inicio + relativedelta(months=duracao, days=-1)

                st.markdown("### Anexos:")

                nf_check = st.checkbox("Nota Fiscal")
                nf_str = "NF" if nf_check else ""
                bol_check = st.checkbox("BOL")
                bol_str = "BOL" if bol_check else ""
                fat_check = st.checkbox("FAT")
                fat_str = "FAT" if fat_check else ""

                anexos = [nf_str, bol_str, fat_str]
                anexos = [a for a in anexos if a]

                anexos_str =  " / ".join(anexos)  

                st.divider()

                if st.form_submit_button("Confirmar adição de contrato", type="secondary"):
                    if duracao <= 0:
                        st.error("A 'Duração do contrato (meses)' deve ser de pelo menos 1 mês.")
                        return
                    
                    data_inicio = datetime.combine(data_inicio, datetime.min.time())
                    data_termino = data_inicio + relativedelta(months=duracao, days=-1)
                    valor_parcela = valor_contrato / duracao

                    new_contrato = {
                       "situacao": "ATIVO",
                       "numero": numero_contrato,
                       "contrato": contrato,
                       "conta": conta,
                       "centro_custo": centro_custo,
                       "estabelecimento": estabelecimento,
                       "classificacao": classificacao,
                       "categoria": categoria,
                       "cnpj": cnpj,
                       "anexos": anexos_str,
                       "valor_contrato": valor_contrato,
                       "inicio": data_inicio.isoformat(),
                       "termino": data_termino.isoformat(),
                        }
                    
                    try:
                        response = supabase.table("contratos").insert(new_contrato).execute()
                        batch_parcelas = []
                        new_id = response.data[0]["id"]

                        for i in range(duracao):
                            data_parcela = data_inicio + relativedelta(months=i)

                            batch_parcelas.append({
                                "contrato_id": new_id,
                                "situacao": "ATIVO",
                                "ano": data_parcela.year,
                                "mes": data_parcela.month,
                                "data_emissao": data_parcela.isoformat(),
                                "data_vencimento": (data_parcela + relativedelta(months=1)).isoformat(),       
                                "tipo": "CONTRATO",
                                "contrato": contrato,
                                "referente": categoria,
                                "estabelecimento": estabelecimento,
                                "status": "ABERTO",
                                "valor": valor_parcela,})
                            print(f"{contrato} - parcela {i+1} adicionada")

                        supabase.table("parcelas").insert(batch_parcelas).execute()

                        st.success(f"Contrato adicionado! \n{len(batch_parcelas)} Parcelas criadas com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                            
                    except Exception as e:
                        st.error(f"Erro ao criar contrato: {e}")

    def delete_contract(df):
        ccol2, = st.columns(1)

        with ccol2:
            st.subheader("Excluir Contrato")
            
            with st.form("form_excluir_contrato", clear_on_submit=True):
                contrato_exc = st.selectbox("Contrato a excluir: ", options=df["contrato"].dropna().unique())
                st.warning("Atenção: A exclusão é permanente e não pode ser desfeita.", icon="⚠️")

                if st.form_submit_button("Confirmar Exclusão", type="primary"):
                    try:
                        supabase.table("contratos").delete().eq("contrato", contrato_exc).execute()
                        supabase.table("parcelas").delete().eq("contrato", contrato_exc).execute()
                        st.success("Contrato excluído com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir contrato: {e}")


    def active_deactive_contract(df):
            coll3, = st.columns(1)

            with coll3:
                st.subheader("Ativar/Desativar Contrato")

                opcoes_contrato = df["contrato"].dropna().unique()
                if not any(opcoes_contrato):
                    st.warning("Nenhum contrato para ativar ou desativar.")
                    return

                contrato_selecionado = st.selectbox(
                    "Selecione o Contrato:",
                    options=opcoes_contrato,
                    key="sb_contrato_status"  
                )

                if contrato_selecionado:
                    contrato_info = df[df["contrato"] == contrato_selecionado]
                    
                    if not contrato_info.empty:
                        status_atual = contrato_info.iloc[0]["situacao"]

                        if status_atual == "ATIVO":
                            with st.form("form_desativar_contrato"):
                                if st.form_submit_button("Desativar Contrato", type="primary"):
                                    try:
                                        supabase.table("contratos").update({"situacao": "INATIVO"}).eq("contrato", contrato_selecionado).execute()
                                        supabase.table("parcelas").update({"situacao": "INATIVO"}).eq("contrato", contrato_selecionado).execute()
                                        st.success("Contrato desativado com sucesso!")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao desativar contrato: {e}")

                        elif status_atual == "INATIVO":
                            with st.form("form_ativar_contrato"):
                                if st.form_submit_button("Ativar Contrato", type="primary"):
                                    try:
                                        supabase.table("contratos").update({"situacao": "ATIVO"}).eq("contrato", contrato_selecionado).execute()
                                        supabase.table("parcelas").update({"situacao": "ATIVO"}).eq("contrato", contrato_selecionado).execute()
                                        st.success("Contrato ativado com sucesso!")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao ativar contrato: {e}")

    def edit_contract(df):
        coll4, = st.columns(1)

        with coll4:
            st.subheader("Editar informações")
            opcoes_contrato = df["contrato"].dropna().unique()
            if not any(opcoes_contrato):
                st.warning("Nenhum contrato existente.")
                return

            contrato_edit = st.selectbox(label="Selecione o Contrato",options=opcoes_contrato)
            st.markdown("##### Dados do Contrato")
            dados_contrato = supabase.table("contratos").select("*").eq("contrato", contrato_edit).execute()
            dict_dados = dados_contrato.data[0]
            dict_dados["valor_contrato"] = 1 if not dict_dados["valor_contrato"] else dict_dados["valor_contrato"]


            with st.form("form_editar_contrato", clear_on_submit=True):
                if dict_dados["termino"] and dict_dados["inicio"]:
                   print(dict_dados["termino"], type(dict_dados["termino"])) 
                   print(dict_dados["inicio"], type(dict_dados["termino"])) 
                   duracao = relativedelta(datetime.fromisoformat(dict_dados["termino"]), datetime.fromisoformat(dict_dados["inicio"]))
                   duracao = int(duracao.years * 12 + duracao.months)
                else:
                    duracao = 1
                contrato = st.text_input("Nome do Contrato", value=dict_dados["contrato"])
                contrato = contrato.upper()
                cnpj = st.text_input("CNPJ", value=dict_dados["cnpj"])
                numero_contrato = st.text_input("Número do Contrato (ou 'PEDIDO')", value=dict_dados["numero"])
                descricao = st.text_input("Descrição", value=dict_dados["descricao"])
                st.markdown("---")
                estabelecimento = st.selectbox("Estabelecimento", options=df["estabelecimento"].dropna().unique(), index=df["estabelecimento"].dropna().unique().tolist().index(dict_dados["estabelecimento"]))
                valor_contrato = st.number_input("Valor do Contrato R$", format="%.2f", step=1.0, min_value=1.0, value=float(dict_dados["valor_contrato"]))
                duracao = st.number_input("Duração do contrato (meses)", format="%d", value=duracao, min_value=1, step=1)
                conta = st.number_input("Conta", step=1.0, value=float(dict_dados["conta"]))
                conta = str(float(conta))
                centro_custo = st.number_input("Centro de Custo", step=1.0, value=float(dict_dados["centro_custo"]))
                centro_custo = str(float(centro_custo))
                classificacao = st.selectbox("Classificação", options=df["classificacao"].dropna().unique(), index=list(df["classificacao"].dropna().unique()).index(dict_dados["classificacao"]))  
                categoria = st.selectbox("Categoria", options=df["categoria"].dropna().unique(), index=df["categoria"].dropna().unique().tolist().index(dict_dados["categoria"]))
                data_inicio = st.date_input("Data de Início", value=dict_dados["inicio"])
                if duracao:
                    valor_parcela = valor_contrato / duracao
                    if data_inicio:
                        duracao_delta = relativedelta(months=duracao)
                        data_termino = data_inicio + relativedelta(months=duracao, days=-1)
                if st.form_submit_button("Atualizar Dados", type="primary"):
                    edited_contract = {
                        "situacao": "ATIVO",
                        "numero": numero_contrato,
                        "contrato": contrato,
                        "cnpj": cnpj,
                        "conta": conta,
                        "centro_custo": centro_custo,
                        "classificacao": classificacao,
                        "categoria": categoria,
                        "estabelecimento": estabelecimento,
                        "descricao": descricao,
                        "valor_contrato": valor_contrato,
                        "anexos": dict_dados["anexos"],
                    }

                    if data_inicio:
                        edited_contract["inicio"] = data_inicio.isoformat()
                        edited_contract["termino"] = data_termino.isoformat()


                    try:
                        supabase.table("contratos").update(edited_contract).eq("contrato", contrato_edit).execute()
                        st.success("Contrato atualizado com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar contrato: {e}")

    def renew_contract(df):
        coll5, = st.columns(1)

        with coll5:
            st.subheader("Renovação de Contrato")
            
            hoje = datetime.now().date()
            df['termino'] = pd.to_datetime(df['termino']).dt.date
            
            contratos_renovar = df["contrato"][df["termino"] < hoje].dropna().unique()
            
            if not any(contratos_renovar):
                st.warning("Nenhum contrato para renovar.")
                return
            
            contrato_renew = st.selectbox("Contrato a renovar:", options=contratos_renovar)
            data_termino = df.loc[df["contrato"] == contrato_renew, "termino"].iloc[0]
            dias_vencido = (hoje - data_termino).days
            
            st.warning(f"O contrato {contrato_renew} está vencido há {dias_vencido} dias.")

            with st.form("form_renovar_contrato", clear_on_submit=True):
                dias_renovar = st.number_input("Renovar por quantos dias?", min_value=1, step=29)

                if st.form_submit_button("Renovar Contrato", type="primary"):
                    renovacao = {
                        "termino": (hoje + relativedelta(days=dias_renovar)).isoformat(),
                        "situacao": "ATIVO",
                    }
                
                    try:
                        supabase.table("contratos").update(renovacao).eq("contrato", contrato_renew).execute()
                        st.success("Contrato renovado com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao renovar contrato: {e}")
    
    
    def tabs_show():
        contratos = load_data("contratos")
        tab_novo, tab_editar, tab_renovar, tab_desativar, tab_excluir = st.tabs([
        "Novo Contrato", "Editar Contrato", "Renovar Contrato", "Desativar Contrato", "Excluir Contrato "])

        with tab_novo:
            new_contract(contratos)
        with tab_editar:
            edit_contract(contratos)
        with tab_renovar:
            renew_contract(contratos)
        with tab_desativar:
            active_deactive_contract(contratos)
        with tab_excluir:
            delete_contract(contratos)
        

    def show():
        st.set_page_config(
            page_title="ContraX",
            layout="wide",
        )
        
        contratos = load_data("contratos")

        filter_config = [
            ("situacao"),
            ("contrato"),
            ("estabelecimento"),
            ("classificacao"),
            ("pedido")
        ]
        
        filter_keys = [f for f in filter_config]
        initialize_state(contratos, filter_keys)

        im, ti = st.columns([0.05, 0.95])
        with im:
            st.image('https://cdn-icons-png.flaticon.com/256/2666/2666501.png', width=70)
        with ti:
            st.title("Prestadores de Contratos")
        st.divider()
        with st.expander("Filtros de Contratos", expanded=True):
          show_filters(contratos, filter_config)
        
        contratos_filtrado = contratos[
            (contratos["situacao"].isin(st.session_state.contratos_situacao_selecionado)) &
            (contratos["contrato"].isin(st.session_state.contratos_contrato_selecionado)) &
            (contratos["estabelecimento"].isin(st.session_state.contratos_estabelecimento_selecionado)) &
            (contratos["classificacao"].isin(st.session_state.contratos_classificacao_selecionado)) 
        ]
        if st.session_state.contratos_pedido_selecionado == ["Pedido"]:
            contratos_filtrado = contratos_filtrado[
                (contratos_filtrado["numero"] == "PEDIDO")
        ]
        elif st.session_state.contratos_pedido_selecionado == ['Contrato']:
            contratos_filtrado = contratos_filtrado[
                (contratos_filtrado["numero"] != "PEDIDO")
            ]


        contratos_filtrado = contratos_filtrado.drop(columns=["id", 'categoria', 'inicio'])
        st.dataframe(
            contratos_filtrado,
            hide_index=True,
            width='stretch',
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


        show_stats(contratos_filtrado, "valor_contrato")
        st.divider()
        tabs_show()

    show()

if __name__ == "__main__":
    contratos()