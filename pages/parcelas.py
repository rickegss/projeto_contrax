import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from utils.stamp import mes_atual, ano_atual, data_lanc, mes_dict
from utils.pdf_extractor import extract_pdf
import time

def show():
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_PATH = BASE_DIR / "data" / "processed" / "parcelas.csv"

    mes_find_nome = [mes_atual]

    st.title("Lançamento de Parcelas")
    st.write("---")
    st.header("Filtros")

    if "parcelas" not in st.session_state:
        try:
            st.session_state.parcelas = pd.read_csv(DATA_PATH)
        except FileNotFoundError:
            st.error(f"Arquivo de dados não encontrado em: {DATA_PATH}")
            st.stop()

    parcelas = st.session_state.parcelas.copy()

    if st.session_state.get("submission_success", False):
        st.session_state.valor_manual = ""
        st.session_state.doc_manual = ""
        st.session_state.submission_success = False  

    col1, col2, col3, col4 = st.columns(4)

    def update_csv(df_to_save):
        df_to_save.to_csv(DATA_PATH, index=False)
        st.session_state.parcelas = pd.read_csv(DATA_PATH)

    for filtro in ["ano", "mes", "contrato", "status"]:
        if f"toggle_{filtro}" not in st.session_state:
            st.session_state[f"toggle_{filtro}"] = (filtro == "contrato")

    def toggle(filtro):
        st.session_state[f"toggle_{filtro}"] = not st.session_state[f"toggle_{filtro}"]

    with col1:
        if st.button("Selecionar Todos", key="btn_ano"):
            toggle("ano")
        ano_filt = st.multiselect(
            "Ano",
            options=parcelas["Ano"].dropna().unique(),
            default=[ano_atual]
        )

    with col2:
        if st.button("Selecionar Todos", key="btn_mes"):
            toggle("mes")
        mes_filt = st.multiselect(
            "Mês",
            options=parcelas["Mês"].dropna().unique(),
            default=mes_find_nome
        )

    with col3:
        if st.button("Selecionar Todos", key="btn_contrato"):
            toggle("contrato")
        contrato_filt = st.multiselect(
            "Contrato",
            options=parcelas["Contrato"].dropna(),
            default=parcelas["Contrato"].dropna() if st.session_state["toggle_contrato"] else []
        )

    with col4:
        if st.button("Selecionar Todos", key="btn_status"):
            toggle("status")
        status_filt = st.multiselect(
            "Status",
            options=parcelas["Status"].dropna().unique(),
            default=['ABERTO']
        )

    st.write("---")
    st.header("Parcelas")

    parcelas_filtrado = parcelas.copy()
    if ano_filt:
        parcelas_filtrado = parcelas_filtrado[parcelas_filtrado["Ano"].isin(ano_filt)]
    if mes_filt:
        parcelas_filtrado = parcelas_filtrado[parcelas_filtrado["Mês"].isin(mes_filt)]
    if contrato_filt:
        parcelas_filtrado = parcelas_filtrado[parcelas_filtrado["Contrato"].isin(contrato_filt)]
    if status_filt:
        parcelas_filtrado = parcelas_filtrado[parcelas_filtrado["Status"].isin(status_filt)]
    
    st.dataframe(
        parcelas_filtrado,
        column_config={
            "Emissão": st.column_config.DateColumn("Emissão", format="DD/MM/YY"),
            "Venc": st.column_config.DateColumn("Vencimento", format="DD/MM/YY"),
            "Valor R$": st.column_config.NumberColumn("Valor da Parcela", format='R$ %.2f')
        }
    )

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        if "show_lancar" not in st.session_state:
            st.session_state.show_lancar = False

        if st.button("Lançar parcela", key="lancar"):
            st.session_state.show_lancar = not st.session_state.show_lancar

        filtr_opc = (parcelas['Mês'].isin(mes_filt)) & (parcelas['Ano'].isin(ano_filt)) & (parcelas['Status'] == 'ABERTO')
        contratos_lancaveis = parcelas.loc[filtr_opc, 'Contrato'].dropna().unique()

        if len(contratos_lancaveis) > 0:
            if st.session_state.show_lancar:
                
                def pdf_callback():
                    uploaded_file = st.session_state.get("pdf_uploader_key")
                    if uploaded_file:
                        info = extract_pdf(uploaded_file)
                        st.session_state.valor_manual = info.get('valor', '')
                        st.session_state.doc_manual = info.get('numero', '')
                    else:
                        st.session_state.valor_manual = ""
                        st.session_state.doc_manual = ""

                st.subheader("1. Anexar Documento (Opcional)")
                file = st.file_uploader(
                    "Selecione ou arraste documento fiscal",
                    type=["pdf"],
                    key='pdf_uploader_key',
                    on_change=pdf_callback
                )
                
                valor_manual = st.text_input("Valor R$", key="valor_manual")
                doc_manual = st.text_input("Número do documento", key="doc_manual")
                st.write("---")

                if file and (not st.session_state.get('valor_manual') or not st.session_state.get('doc_manual')):
                    st.warning('Não foi possível extrair todos os dados do documento. \nPor favor, preencha manualmente.')

                st.subheader("2. Confirmar Lançamento")
                with st.form("form_lancar", clear_on_submit=True):
                    contrato_val_lanc = st.selectbox(
                        "Selecione o contrato para este lançamento:",
                        options=contratos_lancaveis
                    )

                    if st.form_submit_button("Confirmar lançamento"):
                        valor_a_lancar = st.session_state.get("valor_manual", "")
                        doc_a_lancar = st.session_state.get("doc_manual", "")

                        if contrato_val_lanc and valor_a_lancar:
                            try:
                                valor = float(str(valor_a_lancar).replace(",", "."))
                                filtro = (parcelas["Contrato"] == contrato_val_lanc) & (parcelas["Mês"] == mes_atual) & (parcelas['Ano'] == ano_atual) & (parcelas["Status"] == 'ABERTO')
                                
                                if parcelas[filtro].empty:
                                    st.error("Nenhuma parcela em aberto encontrada para o contrato e período atual.")
                                else:
                                    index_to_update = parcelas[filtro].index[0]
                                    parcelas.loc[index_to_update, ["Valor R$", "Dt.Lanç", "Doc", "Status"]] = [valor, data_lanc, doc_a_lancar, "LANÇADO"]
                                    update_csv(parcelas)
                                    
                                    st.session_state.submission_success = True
                                    
                                    st.success("Parcela lançada")
                                    time.sleep(0.7)
                                    st.rerun()
                            except (ValueError, TypeError):
                                st.error("O valor informado é inválido!")
                        else:
                            st.warning("É necessário selecionar um contrato e preencher um valor válido!")
        else:
            if st.session_state.get("show_lancar"):
                st.error("Não há parcelas abertas para o período filtrado.")

    with col6:
        if "show_modificar" not in st.session_state:
            st.session_state.show_modificar = False

        if st.button("Modificar lançamento", key="modificar"):
            st.session_state.show_modificar = not st.session_state.show_modificar

        if st.session_state.show_modificar:
            with st.form("form_altera_lancamento", clear_on_submit=True):
                st.subheader("Alterar Dados do Lançamento")
                num_linha_altera = st.text_input("Nº da linha (índice) para alterar", key="linha_altera")
                valor_val_mod = st.text_input("Novo Valor R$ (opcional)", key="valor_mod")
                doc_val_mod = st.text_input("Novo N° Documento (opcional)", key="doc_mod")
                
                if st.form_submit_button("Confirmar Alteração"):
                    if num_linha_altera and (valor_val_mod or doc_val_mod):
                        try:
                            linha_mod = int(num_linha_altera)
                            if linha_mod not in parcelas.index:
                                st.error("Linha (índice) inválida.")
                            else:
                                if valor_val_mod:
                                    valor = float(valor_val_mod.replace(",", "."))
                                    parcelas.loc[linha_mod, "Valor R$"] = valor
                                if doc_val_mod:
                                    parcelas.loc[linha_mod, "Doc"] = doc_val_mod
                                
                                parcelas.loc[linha_mod, "Dt.Lanç"] = data_lanc
                                update_csv(parcelas)
                                st.success(f"Parcela {linha_mod} atualizada.")
                                time.sleep(0.7)
                                st.rerun()
                        except ValueError:
                            st.error("Digite um número de linha e/ou valor numérico válido!")
                    else:
                        st.warning("Preencha a linha e pelo menos um campo para alterar!")

            st.write("---")
            with st.form("form_revert_status", clear_on_submit=True):
                st.subheader("Reverter Status para 'Aberto'")
                num_linha_revert = st.text_input("Nº da linha (índice) para reverter", key="linha_revert")

                if st.form_submit_button("Confirmar Reversão"):
                    if num_linha_revert:
                        try:
                            line = int(num_linha_revert)
                            if line not in parcelas.index:
                                st.error("Linha (índice) inválida.")
                            else:
                                parcelas.loc[line, ["Valor R$", "Dt.Lanç", "Doc"]] = [pd.NA, pd.NA, pd.NA]
                                parcelas.loc[line, "Status"] = 'ABERTO'
                                
                                update_csv(parcelas)
                                st.success(f"Status da parcela {line} alterado para ABERTO.")
                                time.sleep(0.7)
                                st.rerun()
                        except ValueError:
                            st.error("Digite um número de linha válido!")
                    else:
                        st.warning("Preencha o número da linha!")

    with col7:
        if "show_duplicar" not in st.session_state:
            st.session_state.show_duplicar = False

        if st.button('Duplicar linha', key='duplica_parcela'):
            st.session_state.show_duplicar = not st.session_state.show_duplicar
        
        if st.session_state.show_duplicar:
           filtr_opc_dup = (parcelas['Mês'].isin(mes_find_nome)) & (parcelas['Ano'] == ano_atual) & (parcelas['Status'] == 'ABERTO')
           contratos_duplicaveis = parcelas.loc[filtr_opc_dup, 'Contrato'].dropna().unique()

           if not contratos_duplicaveis.empty:
            with st.form('Selecionar contrato para duplicar', clear_on_submit=True):
                st.subheader('Parcela a duplicar: ')
                contrato_dup = st.selectbox('Contrato: ', options=contratos_lancaveis)
                qtd_dup = st.number_input('Adicionar quantos lançamentos?: ', min_value=1, value=1)
                submitted = st.form_submit_button('Confirmar')

                if submitted and contrato_dup:
                    df_filt_dup = parcelas[
                            (parcelas['Contrato'] == contrato_dup) & 
                            (parcelas['Ano'] == ano_atual) & 
                            (parcelas['Mês'].isin(mes_find_nome)) &
                            (parcelas['Status'] == 'ABERTO')
                        ]
                    
                    if not df_filt_dup.empty:
                        linha_dup = df_filt_dup.iloc[[0]]
                        novas_linhas = [linha_dup] * qtd_dup

                        parcelas = pd.concat([parcelas] + novas_linhas, ignore_index=True)
                        update_csv(parcelas)
                        st.success('Linhas duplicadas!')
                        time.sleep(0.5)
                        st.rerun()
           else:
                st.warning("Não há contratos abertos no período para duplicar.")

    with col8:
        if 'show_excluir' not in st.session_state:
            st.session_state.show_excluir = False
        
        if st.button('Excluir Linha', key='excluir'):
            st.session_state.show_excluir = not st.session_state.show_excluir

        if st.session_state.show_excluir:
            with st.form('form_excluir', clear_on_submit=True):
                st.subheader('Excluir parcela')
                st.text_input('Índice da linha a excluir: ', key='linha_excluir')
                submitted = st.form_submit_button('Confirmar')

            if submitted:
                try:
                    line = int(st.session_state.linha_excluir)
                    parcelas.drop(line, inplace=True)
                    update_csv(parcelas)
                    st.success('Linha excluída!')
                    time.sleep(0.5)
                    st.rerun()

                except(ValueError):
                    st.error('Valor inválido!')