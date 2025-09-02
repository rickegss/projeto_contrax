import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from utils.stamp import mes_atual, ano_atual, data_lanc, mes_dict
import time

def show():
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_PATH = BASE_DIR / "data" / "processed" / "parcelas.csv"

    ano_atual2 = [ano_atual]
    mes_atual2 = [mes_atual]

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

    col1, col2, col3, col4 = st.columns(4)

    mes_atual_nome = mes_dict.get(mes_atual)

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
            default=parcelas['Ano'][parcelas['Ano'].isin(ano_atual2)].dropna().unique()
        )

    with col2:
        if st.button("Selecionar Todos", key="btn_mes"):
            toggle("mes")
        mes_filt = st.multiselect(
            "Mês",
            options=parcelas["Mês"].dropna().unique(),
            default=parcelas['Mês'][parcelas['Mês'].isin(mes_atual2)].dropna().unique()
        )

    with col3:
        if st.button("Selecionar Todos", key="btn_contrato"):
            toggle("contrato")
        contrato_filt = st.multiselect(
            "Contrato",
            options=parcelas["Contrato"].dropna().unique(),
            default=parcelas["Contrato"].dropna().unique() if st.session_state["toggle_contrato"] else []
        )

    with col4:
        if st.button("Selecionar Todos", key="btn_status"):
            toggle("status")
        status_filt = st.multiselect(
            "Status",
            options=parcelas["Status"].dropna().unique(),
            default=parcelas["Status"][parcelas["Status"].isin(["ABERTO"])].dropna().unique() 
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
        "Emissão": st.column_config.DateColumn(
            "Emissão", 
            format="DD/MM/YY"  
        ),
         "Venc": st.column_config.DateColumn(
             "Vencimento",
             format="DD/MM/YY"
         ),
         "Valor R$": st.column_config.NumberColumn(
             "Valor da Parcela",
             format='R$ %.2f'
         )
    }
)

    col5, col6 = st.columns(2)

    with col5:
        if "show_lancar" not in st.session_state:
            st.session_state.show_lancar = False

        if st.button("Lançar parcela", key="lancar"):
            st.session_state.show_lancar = not st.session_state.show_lancar

        filtr_opc = (parcelas['Mês'].isin(mes_filt)) & (parcelas['Ano'].isin(ano_filt)) & (parcelas['Status'] == 'ABERTO')
        contratos_lancaveis = parcelas.loc[filtr_opc, 'Contrato'].dropna().unique()

    if len(contratos_lancaveis) > 0:
        if st.session_state.show_lancar:
            with st.form("form_lancar", clear_on_submit=False):
                    contrato_val_lanc = st.multiselect(
                        "Contrato:",
                        options=contratos_lancaveis
                    )
                    valor_val_lanc = st.text_input("Valor R$")
                    doc_val_lanc = st.text_input("Número do documento")

                    if st.form_submit_button("Confirmar lançamento"):
                            if contrato_val_lanc and valor_val_lanc:
                                try:
                                    valor = float(valor_val_lanc.replace(",", "."))
                                    filtro = (parcelas["Contrato"].isin(contrato_val_lanc)) & (parcelas["Mês"] == mes_atual) & (parcelas['Ano'] == ano_atual)
                                    
                                    if parcelas[filtro].empty:
                                        st.error("Nenhuma parcela encontrada para o contrato e mês atual.")
                                    else:
                                        parcelas.loc[filtro, ["Valor R$", "Dt.Lanç", "Doc", "Status"]] = [valor, data_lanc, doc_val_lanc, "LANÇADO"]
                                        update_csv(parcelas)
                                        st.success("Parcela lançada")
                                        time.sleep(2)
                                        st.rerun()

                                except ValueError:
                                    st.error("Digite um valor numérico válido!")
                            else:
                                st.warning("Preencha Contrato e Valor!")
    else:
        st.error("Não há parcelas abertas para o mês atual")

    with col6:
        if "show_modificar" not in st.session_state:
            st.session_state.show_modificar = False

        if st.button("Modificar lançamento", key="modificar"):
            st.session_state.show_modificar = not st.session_state.show_modificar

        if st.session_state.show_modificar:
            with st.form("form_update_lancamento", clear_on_submit=False):
                st.subheader("Alterar Dados do Lançamento")
                num_linha_update = st.text_input("Nº da linha (índice) para alterar", key="linha_update")
                valor_val_mod = st.text_input("Novo Valor R$ (opcional)", key="valor_mod")
                doc_val_mod = st.text_input("Novo N° Documento (opcional)", key="doc_mod")
                
                if st.form_submit_button("Confirmar Alteração"):
                    if num_linha_update and (valor_val_mod or doc_val_mod):
                        try:
                            linha_mod = int(num_linha_update)
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
                                time.sleep(2)
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
                                parcelas.loc[line, "Valor R$"] = pd.NA
                                parcelas.loc[line, "Dt.Lanç"] = pd.NA
                                parcelas.loc[line, "Doc"] = pd.NA
                                parcelas.loc[line, "Status"] = 'ABERTO'
                                
                                update_csv(parcelas)
                                st.success(f"Status da parcela {line} alterado para ABERTO.")
                                time.sleep(2)
                                st.rerun()
                        except ValueError:
                            st.error("Digite um número de linha válido!")
                    else:
                        st.warning("Preencha o número da linha!")