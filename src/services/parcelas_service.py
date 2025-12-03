from dateutil.relativedelta import relativedelta
import time
from src.utils.gemini_extractor import process_invoice 
from src.utils.stamp import data_lanc
import streamlit as st

def view_lancar(df, df_filter, supabase):
    st.subheader("Lançar Nova Parcela")

    if df_filter.empty:
        st.warning("Selecione um ano e mês com parcelas para poder lançar.", icon="🚨")
        return

    filtro_lancaveis = (df["status"] == "ABERTO") & (df["mes"] == int(df_filter["mes"].iloc[0])) & (df["ano"] == int(df_filter["ano"].iloc[0]))
    parcelas_lancaveis = df[filtro_lancaveis].sort_values(by="contrato", ascending=True)

    if parcelas_lancaveis.empty:
        st.warning("Não há parcelas em aberto para o mês e ano atuais.", icon="🚨")
        return

    options_box = {f"{row['contrato']} | {row['id']}": row['id'] for _, row in parcelas_lancaveis.iterrows()}
    
    uploaded_file = st.file_uploader("1. Anexar Documento Fiscal (Opcional)", type=["pdf"], key="file_uploader_lancar")

    if "form_valor" not in st.session_state: st.session_state.form_valor = 0.0
    if "form_doc" not in st.session_state: st.session_state.form_doc = ""
    if "last_file" not in st.session_state: st.session_state.last_file = None

    if uploaded_file:
        if uploaded_file != st.session_state.last_file:
            st.session_state.form_valor = 0.0
            st.session_state.form_doc = ""
            
            with st.spinner("🤖 Lendo documento com IA..."):
                info = process_invoice(uploaded_file)
                st.session_state.form_valor = info.get('valor_doc', 0.0)
                st.session_state.form_doc = info.get('numero_doc', '')
                st.session_state.last_file = uploaded_file
                
                if st.session_state.form_valor > 0:
                    st.toast("Dados preenchidos via IA!", icon="✨")
    else:
        if st.session_state.last_file is not None:
            st.session_state.last_file = None
            st.session_state.form_valor = 0.0
            st.session_state.form_doc = ""
            st.rerun()

    with st.form("form_lancar", clear_on_submit=True):
        st.subheader("2. Confirmar Lançamento")
        contrato_lanc = st.selectbox("Contrato para Lançamento:", options=list(options_box.keys()))
        valor_lanc = st.number_input("Valor R$", value=st.session_state.form_valor, format="%.2f", step=1.0, min_value=0.0)
        doc_lanc = st.text_input("Número do Documento", value=st.session_state.form_doc)
        
        if st.form_submit_button("Confirmar Lançamento"):
            if not contrato_lanc or not doc_lanc or valor_lanc <= 0:
                st.warning("É necessário selecionar um contrato e preencher todos os campos devidamente.", icon="🚨")
            else:
                try:
                    id_lanc = options_box[contrato_lanc]
                    data_iso = data_lanc.isoformat() if hasattr(data_lanc, 'isoformat') else data_lanc
                    
                    update_data = {
                        "valor": valor_lanc, 
                        "data_lancamento": data_iso, 
                        "documento": doc_lanc, 
                        "status": "LANÇADO"
                    }
                    
                    upd = supabase.table("parcelas").update(update_data).eq("id", id_lanc).execute()
                    
                    if upd.data:
                        st.success("Parcela atualizada com sucesso! ✅")
                        st.session_state.form_valor = 0.0
                        st.session_state.form_doc = ""
                        st.session_state.last_file = None
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Nenhuma parcela encontrada com este ID.", icon="❌")
                except Exception as e:
                    st.error(f"Erro: {e}", icon="❌")


def view_modificar(df, df_filter, supabase):
    st.subheader("Alterar ou Desfazer Lançamento")
    
    if df_filter.empty:
        st.warning("Selecione um ano e mês com parcelas para poder modificar.", icon="🚨")
        return

    filtro_modificar = (df["ano"] == df_filter["ano"].iloc[0]) & (df["mes"] == df_filter["mes"].iloc[0]) & (df["status"] == 'LANÇADO')
    df_modificar = df[filtro_modificar].sort_values(by="contrato", ascending=True)
    contratos_modificar = df_modificar["contrato"].dropna().unique()

    contrato_mod = st.selectbox("Contrato a modificar parcela:", options=contratos_modificar)
    parcelas_modificar = df[(df["contrato"] == contrato_mod) & (df['status'] == 'LANÇADO') & (df["mes"] == df_filter["mes"].iloc[0]) & (df["ano"] == df_filter["ano"].iloc[0])]

    if parcelas_modificar.empty:
        st.info("Nenhuma parcela lançada encontrada para o contrato e período selecionados.")
        return

    opcoes_mod = [f"{row['id']} | {row['contrato']} | N° {row['documento']} | R$ {row['valor']}" for _, row in parcelas_modificar.iterrows()]
    parcela_mod = st.radio("Selecione a parcela:", options=opcoes_mod, key="radio_mod_parcela")

    st.write("---")
    col_mod, col_rev = st.columns(2)
    
    if parcela_mod:
        try:
            id_parcela_mod = int(parcela_mod.split(" | ")[0])
            parcela_original = df_modificar[df_modificar['id'] == id_parcela_mod]

            if not parcela_original.empty:
                with col_mod:
                    st.subheader("Alterar Lançamento")
                    novo_valor = st.number_input("Valor R$", value=parcela_original["valor"].iloc[0], format="%.2f", step=1.0, min_value=0.01)
                    novo_doc = st.text_input("N° Documento", value=parcela_original["documento"].iloc[0])

                    with st.form("form_alterar", clear_on_submit=True):
                        if st.form_submit_button("Confirmar Alteração"):
                            if (novo_valor is None or not novo_doc):
                                st.warning("Preencha número do documento e valor.", icon="🚨")
                            else:
                                data_atualizar = {}
                                if novo_valor > 0: data_atualizar["valor"] = novo_valor
                                if novo_doc: data_atualizar["documento"] = novo_doc
                                
                                if data_atualizar:
                                    res = supabase.table("parcelas").update(data_atualizar).eq("id", id_parcela_mod).execute()
                                    if res.data:
                                        st.success("Parcela atualizada! ✅")
                                        st.cache_data.clear()
                                        st.rerun()
                                    else: st.error("Falha na atualização.", icon="❌")

                with col_rev:
                    with st.form("form_reverter", clear_on_submit=True):
                        st.subheader("Desfazer Lançamento")
                        st.text("Cancelar o lançamento da parcela:")
                        if st.form_submit_button("Cancelar Lançamento"):
                            update_data = {"valor": None, "documento": None, "data_lancamento": None, "status": "ABERTO"}
                            res = supabase.table("parcelas").update(update_data).eq("id", id_parcela_mod).execute()
                            if res.data:
                                st.success("Parcela revertida! ✅")
                                st.cache_data.clear()
                                st.rerun()
                            else: st.error("Falha ao reverter.", icon="❌")
        except Exception as e:
            st.error(f"Erro ao processar parcela: {e}")


def view_adicionar(df, df_filter, supabase):
    st.subheader("Adicionar Parcela de Contrato")
    contratos_ativos = df.loc[df['situacao'] == 'ATIVO', 'contrato'].dropna().unique()

    if contratos_ativos.size == 0:
        st.warning("Não há contratos ativos.", icon="🚨")
        return

    contrato_add = st.selectbox('Selecione o Contrato:', options=contratos_ativos, key="select_add_contrato")

    with st.form('form_adicionar', clear_on_submit=True):
        qtd_add = st.number_input('Quantidade:', min_value=1, value=1, step=1)
        
        if st.form_submit_button('Confirmar Adição'):
            try:
                row_ref = df[
                    (df["contrato"] == contrato_add) & 
                    (df["situacao"] == 'ATIVO')
                ].sort_values(by="id", ascending=False).iloc[0]
                
                ano_selecionado = int(df_filter["ano"].iloc[0])
                mes_selecionado = int(df_filter["mes"].iloc[0])
                add_data = {
                    "ano": ano_selecionado, 
                    "mes": mes_selecionado,
                    "data_lancamento": None,
                    "data_emissao": data_lanc.isoformat(),
                    "data_vencimento": (data_lanc + relativedelta(months=1)).isoformat(),
                    "tipo": row_ref['tipo'],
                    "contrato": contrato_add,
                    "contrato_id": int(row_ref['contrato_id']),
                    "referente": row_ref['referente'],
                    "documento": None,
                    "estabelecimento": row_ref['estabelecimento'],
                    "status": "ABERTO",
                    "valor": None,
                    "situacao": "ATIVO",
                    "classificacao": row_ref['classificacao']
                }
                
                supabase.table("parcelas").insert([add_data] * qtd_add).execute()
                st.success(f"{qtd_add} parcela(s) adicionada(s)! ✅")
                time.sleep(0.5)
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao adicionar: {e}", icon="❌")


def view_excluir(df, supabase):
    st.subheader("Excluir Parcela")
    st.warning("Atenção: Exclusão permanente.", icon="⚠️")
    
    contrato_exc = st.selectbox("Contrato", options=df["contrato"].sort_values().dropna().unique())
    ano_exc = st.selectbox("Ano", options=df["ano"].dropna().unique())
    mes_exc = st.selectbox("Mês", options=df["mes_nome"].dropna().unique())
    
    df_excluir = df[(df["contrato"] == contrato_exc) & (df["mes_nome"] == mes_exc) & (df["ano"] == ano_exc)]

    if df_excluir.empty:
        st.warning("Não há parcelas para excluir.", icon="🚨")
        return

    with st.form('form_excluir', clear_on_submit=True):
        opcoes_exc = [f"{row['id']} | {row['ano']} | {row['mes_nome']} | {row['tipo']} | {row['status']}| R$ {row['valor']}" for _, row in df_excluir.iterrows()]
        parcela_exc = st.radio("Parcela a excluir:", options=opcoes_exc, key="radio_exc_parcela")
    
        if st.form_submit_button('Confirmar Exclusão', type="primary"):
            if parcela_exc:
                try:
                    id_exc = int(parcela_exc.split(" | ")[0])
                    response = supabase.table("parcelas").delete().eq("id", id_exc).execute()
                    if response.data:
                        st.success(f"Parcela {id_exc} excluída.")
                        time.sleep(0.7)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Parcela não encontrada.", icon="❌")
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}", icon="❌")