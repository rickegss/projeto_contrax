import streamlit as st
import pandas as pd
from utils.stamp import mes_atual, ano_atual, data_lanc
from utils.pdf_extractor import extract_pdf
import time
from pathlib import Path

script_dir = Path(__file__).resolve().parent.parent
path_csv = script_dir / "data" / "processed" / 'parcelas.csv'
mes_find_nome = [mes_atual]

def initialize_state():
    """Inicializa todas as chaves necessárias no session_state ."""

    states = {
        "show_lancar": False,
        "show_modificar": False,
        "show_duplicar": False,
        "show_excluir": False,
        "valor_manual": "",
        "doc_manual": "",
        "submission_success": False
    }

    for key, value in states.items():
        if key not in st.session_state:
            st.session_state[key] = value

    for filtro in ["ano", "mes", "contrato", "status"]:
        if f"toggle_{filtro}" not in st.session_state:
            st.session_state[f"toggle_{filtro}"] = (filtro == "contrato")

@st.cache_data
def load_data(path_csv):
    """Carrega os dados do CSV para o session_state, se ainda não estiverem lá."""

    if "df" not in st.session_state:
        try:
            st.session_state.df = pd.read_csv(path_csv)
        except FileNotFoundError:
            st.error(f"Arquivo de dados não encontrado em: {path_csv}")
            st.stop()
    return st.session_state.df.copy()

def update_csv(df_to_save, path_csv):
    df_to_save.to_csv(path_csv, index=False)
    st.session_state.df = pd.read_csv(path_csv)


def show_filters(df):
    col1, col2, col3, col4 = st.columns(4)

    def toggle(filtro):
        st.session_state[f"toggle_{filtro}"] = not st.session_state[f"toggle_{filtro}"]

    with col1:
        if st.button("Selecionar Todos", key="btn_ano"):
            toggle("ano")
        ano_filt = st.multiselect(
            "Ano",
            options=df["Ano"].dropna().unique(),
            default=[ano_atual]
        )


    with col2:
        if st.button("Selecionar Todos", key="btn_mes"):
            toggle("mes")
        mes_filt = st.multiselect(
            "Mês",
            options=df["Mês"].dropna().unique(),
            default=mes_find_nome
        )


    with col3:
        if st.button("Selecionar Todos", key="btn_contrato"):
            toggle("contrato")
        contrato_filt = st.multiselect(
            "Contrato",
            options=df["Contrato"].dropna(),
            default=df["Contrato"].dropna() if st.session_state["toggle_contrato"] else []
        )


    with col4:
        if st.button("Selecionar Todos", key="btn_status"):
            toggle("status")
        status_filt = st.multiselect(
            "Status",
            options=df["Status"].dropna().unique(),
            default=['ABERTO']
        )


    return ano_filt, mes_filt, contrato_filt, status_filt

def render_launch_form(df, ano_selecionado, mes_selecionado):
    filtr_opc = (df['Mês'].isin(mes_selecionado)) & (df['Ano'].isin(ano_selecionado)) & (df['Status'] == 'ABERTO')
    contratos_lancaveis = df.loc[filtr_opc, 'Contrato'].dropna().unique()

    if not contratos_lancaveis.any():
        st.error("Não há parcelas abertas para o período filtrado.")
        return

    def pdf_callback():
        uploaded_file = st.session_state.get("pdf_uploader_key")
        if uploaded_file:
            info = extract_pdf(uploaded_file)
            valor_extraido = info.get('valor', '')
            doc_extraido = info.get('numero', '')
                    
            st.session_state.valor_manual = str(valor_extraido) if pd.notna(valor_extraido) else ""
            st.session_state.doc_manual = str(doc_extraido) if pd.notna(doc_extraido) else ""

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
    
    st.text_input("Valor R$", key="valor_manual")
    st.text_input("Número do documento", key="doc_manual")
    st.write("---")

    if file and (not st.session_state.get('valor_manual') or not st.session_state.get('doc_manual')):
        st.warning('Não foi possível extrair todos os dados do documento. Preencha manualmente.')

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
                    filtro = (df["Contrato"] == contrato_val_lanc) & (df["Mês"] == mes_atual) & (df['Ano'] == ano_atual) & (df["Status"] == 'ABERTO')
                    
                    if df[filtro].empty:
                        st.error("Nenhuma parcela em aberto encontrada para o contrato e período atual.")
                    else:
                        index_to_update = df[filtro].index[0]
                        df.loc[index_to_update, ["Valor R$", "Dt.Lanç", "Doc", "Status"]] = [valor, data_lanc, doc_a_lancar, "LANÇADO"]
                        update_csv(df, path_csv)
                        st.session_state.submission_success = True
                        st.session_state['user_message'] = "Parcela lançada com sucesso!"

                except (ValueError, TypeError):
                    st.error("O valor informado é inválido!")
            else:
                st.warning("É necessário selecionar um contrato e preencher um valor válido!")

def render_modify_form(df):
    with st.form("form_altera_lancamento", clear_on_submit=True):
        st.subheader("Alterar Dados do Lançamento")
        num_linha_altera = st.text_input("Nº da linha (índice) para alterar", key="linha_altera")
        valor_val_mod = st.text_input("Novo Valor R$ (opcional)", key="valor_mod")
        doc_val_mod = st.text_input("Novo N° Documento (opcional)", key="doc_mod")
        
        if st.form_submit_button("Confirmar Alteração"):
            if num_linha_altera and (valor_val_mod or doc_val_mod):
                try:
                    linha_mod = int(num_linha_altera)
                    if linha_mod not in df.index:
                        st.error("Linha (índice) inválida.")
                    else:
                        if valor_val_mod:
                            valor = float(valor_val_mod.replace(",", "."))
                            df.loc[linha_mod, "Valor R$"] = valor
                        if doc_val_mod:
                            df.loc[linha_mod, "Doc"] = doc_val_mod
                        df.loc[linha_mod, "Dt.Lanç"] = data_lanc
                        update_csv(df, path_csv)
                        st.session_state['user_message'] = f"Parcela {linha_mod} atualizada."

                except ValueError:
                    st.error("Digite um número de linha e/ou valor numérico válido!")
            else:
                st.warning("Preencha a linha e pelo menos um campo para alterar!")

def render_revert_status_form(df):
    with st.form("form_revert_status", clear_on_submit=True):
        st.subheader("Reverter Status para 'Aberto'")
        num_linha_revert = st.text_input("Nº da linha (índice) para reverter", key="linha_revert")
        if st.form_submit_button("Confirmar Reversão"):
            if num_linha_revert:
                try:
                    line = int(num_linha_revert)
                    if line not in df.index:
                        st.error("Linha (índice) inválida.")
                    else:
                        df.loc[line, ["Valor R$", "Dt.Lanç", "Doc", "Status"]] = [pd.NA, pd.NA, pd.NA, 'ABERTO']
                        update_csv(df, path_csv)
                        st.session_state['user_message'] = f"Status da parcela {line} alterado para ABERTO."

                except ValueError:
                    st.error("Digite um número de linha válido!")
            else:
                st.warning("Preencha o número da linha!")

def render_duplicate_form(df):
    filtr_opc_dup = (df['Mês'].isin(mes_find_nome)) & (df['Ano'] == ano_atual) & (df['Status'] == 'ABERTO')
    contratos_duplicaveis = df.loc[filtr_opc_dup, 'Contrato'].dropna().unique()

    if not contratos_duplicaveis.any():
        st.warning("Não há contratos abertos no período para duplicar.")
        return

    with st.form('form_duplicar', clear_on_submit=True):
        st.subheader('Parcela a duplicar')
        contrato_dup = st.selectbox('Contrato: ', options=contratos_duplicaveis)
        qtd_dup = st.number_input('Adicionar quantos lançamentos?: ', min_value=1, value=1, step=1)
        
        if st.form_submit_button('Confirmar'):
            if contrato_dup:
                filtro_dup = (df['Contrato'] == contrato_dup) & (df['Ano'] == ano_atual) & (df['Mês'].isin(mes_find_nome)) & (df['Status'] == 'ABERTO')
                df_filt_dup = df[filtro_dup]
                if not df_filt_dup.empty:
                    linha_a_duplicar = df_filt_dup.iloc[[0]]
                    novas_linhas = pd.concat([linha_a_duplicar] * qtd_dup, ignore_index=False)
                    df_atualizado = pd.concat([df, novas_linhas], ignore_index=True)
                    update_csv(df_atualizado, path_csv)
                    st.session_state['user_message'] = "Linha duplicada com sucesso!"

def render_delete_form(df):
    with st.form('form_excluir', clear_on_submit=True):
        st.subheader('Excluir parcela')
        linha_a_excluir = st.text_input('Índice da linha a excluir: ', key='linha_excluir')
        if st.form_submit_button('Confirmar'):
            try:
                line = int(linha_a_excluir)
                if line not in df.index:
                    st.error("Índice da linha a ser excluída não existe.")
                else:
                    df.drop(line, inplace=True)
                    update_csv(df, path_csv)
                    st.session_state['user_message'] = "Linha excluída!"

            except (ValueError, TypeError):
                st.error('Índice inválido! Por favor, insira um número.')

def show_action(df, ano, mes, contrato, status):
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        if st.button("Lançar parcela", key="lancar"):
            st.session_state.show_lancar = not st.session_state.show_lancar
    with col6:
        if st.button("Modificar lançamento", key="modificar"):
            st.session_state.show_modificar = not st.session_state.show_modificar
    with col7:
        if st.button('Duplicar linha', key='duplica_parcela'):
            st.session_state.show_duplicar = not st.session_state.show_duplicar
    with col8: 
        if st.button('Excluir Linha', key='excluir'):
            st.session_state.show_excluir = not st.session_state.show_excluir
    
    if st.session_state.get("show_lancar"):
        render_launch_form(df, ano, mes)
    if st.session_state.get("show_modificar"):
        render_modify_form(df)
        st.write("---") 
        render_revert_status_form(df)
    if st.session_state.get("show_duplicar"):
        render_duplicate_form(df)
    if st.session_state.get("show_excluir"):
        render_delete_form(df)

def show():
    initialize_state()
    st.title("Lançamento de Parcelas")
    
    df_parcelas = load_data(path_csv)
    
    st.write("---")
    st.header("Filtros")
    ano, mes, contrato, status = show_filters(df_parcelas)

    df_filtrado = df_parcelas.copy()

    if ano:
        df_filtrado = df_filtrado[df_filtrado['Ano'].isin(ano)]
    if mes:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(mes)]
    if contrato:
        df_filtrado = df_filtrado[df_filtrado['Contrato'].isin(contrato)]
    if status:
        df_filtrado = df_filtrado[df_filtrado['Status'].isin(status)]

    st.write('---')
    st.header('Parcelas')
    st.dataframe(
        df_filtrado,
        column_config={
            "Dt.Lanç": st.column_config.DateColumn("Data Lançamento", format="DD/MM/YY"),
            "Emissão": st.column_config.DateColumn("Emissão", format="DD/MM/YY"),
            "Venc": st.column_config.DateColumn("Vencimento", format="DD/MM/YY"),
            "Valor R$": st.column_config.NumberColumn("Valor da Parcela", format='R$ %.2f')
        }
    )
    
    show_action(df_parcelas, ano, mes, contrato, status)