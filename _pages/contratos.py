import pandas as pd
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client

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

    def initialize_state(filters):
        if "initialized_contratos" in st.session_state:
            return
        
        st.session_state.initialized_contratos = True
        for key in filters:
            st.session_state[f"toggle_{key}"] = True

    def show_filters(df, filter_config):
        cols = st.columns(len(filter_config))
        selections = {}

        for i, (key, label, col_name) in enumerate(filter_config):
            with cols[i]:
                if st.button(f"Todos/Nenhum", key=f"btn_{key}"):
                    st.session_state[f"toggle_{key}"] = not st.session_state[f"toggle_{key}"]
                
                options = df[col_name].dropna().unique()
                default_value = list(options) if st.session_state[f"toggle_{key}"] else []
                
                selections[key] = st.multiselect(
                    label,
                    options=options,
                    default=default_value,
                    key=f"ms_{key}"
                )
        return selections

    def new_contract(df):

        ccol1, = st.columns(1)

        with ccol1:
            st.subheader("Dados do Contrato")
            
            with st.form("form_novo_contrato", clear_on_submit=True):
                contrato = st.text_input("Nome do Contrato")
                contrato = contrato.upper()
                cnpj = st.text_input("CNPJ")
                numero_contrato = st.text_input("Número do Contrato")
                estabelecimento = st.radio("Estabelecimento", options=(df["estabelecimento"].dropna().unique()))
                valor_contrato = st.number_input("Valor do Contrato R$", format="%.2f", step=1.0, min_value=1.0)
                duracao = st.number_input("Duração do contrato (meses)", format="%d", min_value=1)
                conta = st.number_input("Conta", step=1.0)
                conta = str(float(conta))
                centro_custo = st.number_input("Centro de Custo", step=1.0)
                centro_custo = str(float(centro_custo))
                classificacao = st.radio("Classificação", options=df["classificacao"].dropna().unique())  
                categoria = st.radio("Categoria", options=df["categoria"].dropna().unique())
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

    def renovar_contrato():
        pass

    def editar_contrato():
        pass
    
    
    def tabs_show():
        contratos = load_data("contratos")
        tab_novo, tab_excluir, tab_desativar = st.tabs([
        " Novo Contrato", " Excluir Contrato ", " Desativar Contrato",])

        with tab_novo:
            new_contract(contratos)
        with tab_excluir:
            delete_contract(contratos)
        with tab_desativar:
            active_deactive_contract(contratos)
               

    def show():
        st.set_page_config(
            page_title="ContraX",
            layout="wide",
        )
        
        contratos = load_data("contratos")

        filter_config = [
            ("situacao", "Situação", "situacao"),
            ("contrato", "Contrato", "contrato"),
            ("conta", "Conta", "conta"),
            ("centro_custo", "Centro de Custo", "centro_custo"),
            ("estabelecimento", "Estabelecimento", "estabelecimento"),
            ("classificacao", "Classificação", "classificacao"),
        ]
        
        filter_keys = [f[0] for f in filter_config]
        initialize_state(filter_keys)

        im, ti = st.columns([0.05, 0.95])
        with im:
            st.image('https://cdn-icons-png.flaticon.com/256/2666/2666501.png', width=70)
        with ti:
            st.title("Prestadores de Contratos")
        st.divider()
        st.header("Filtros")

        selections = show_filters(contratos, filter_config)

        query_parts = []
        filter_map = {
            "situacao": "`situacao` in @selections['situacao']",
            "contrato": "`contrato` in @selections['contrato']",
            "conta": "`conta` in @selections['conta']",
            "centro_custo": "`centro_custo` in @selections['centro_custo']",
            "estabelecimento": "`estabelecimento` in @selections['estabelecimento']",
            "classificacao": "`classificacao` in @selections['classificacao']",
        }
        
        for key, selection in selections.items():
            if selection:
                query_parts.append(filter_map[key])
        
        contratos_filtrado = contratos
        if query_parts:
            query_string = " & ".join(query_parts)
            contratos_filtrado = contratos.query(query_string)

        st.divider()
        st.header("Contratos")
        st.dataframe(
            contratos_filtrado,
            hide_index=True,
            width='stretch',
            column_config={
                "Início": st.column_config.DateColumn("Início", format="DD/MM/YY"),
                "Término": st.column_config.DateColumn("Término", format="DD/MM/YY"),
                "Renovação": st.column_config.DateColumn("Renovação", format="DD/MM/YY"),
                " Valor do Contrato R$ ": st.column_config.NumberColumn("Valor do Contrato", format='R$ %.2f'),
            }
        )

        st.divider()
        tabs_show()

    show()

if __name__ == "__main__":
    contratos()