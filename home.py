import streamlit as st
import pandas as pd
from pathlib import Path
import time
from utils.stamp import mes_atual, ano_atual, data_lanc
from utils.pdf_extractor import extract_pdf 

# --- Configurações Iniciais e Constantes ---
SCRIPT_DIR = Path(__file__).resolve().parent
PATH_CSV = SCRIPT_DIR / "data" / "processed" / 'parcelas.csv'


# --- Funções de Dados ---
@st.cache_data
def load_data(path):
    """Carrega os dados de um arquivo CSV."""
    try:
        df = pd.read_csv(path)
        return df
    
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado em: {path}")
        st.stop()

def save_data(df, path):
    """Salva o DataFrame no arquivo CSV, limpa o cache e recarrega a página."""
    df.to_csv(path, index=False)
    st.cache_data.clear()
    st.success("Operação realizada com sucesso!")
    time.sleep(0.5)
    st.rerun()


# --- Início da Interface do Streamlit ---
st.set_page_config(
    page_title="Gestão Contratual",
    page_icon="https://cdn-icons-png.freepik.com/512/8521/8521282.png",
    layout="wide",
)
st.title("Lançamento de Parcelas")


if 'df' not in st.session_state:
    st.session_state.df = load_data(PATH_CSV)
df_parcelas = st.session_state.df

# --- Seção de Filtros ---
st.header("Filtros")
col1, col2, col3, col4 = st.columns(4)

with col1:
    anos_selecionados = st.multiselect(
        "Ano",
        options=df_parcelas["Ano"].dropna().unique(),
        default=[ano_atual]
    )
with col2:
    meses_selecionados = st.multiselect(
        "Mês",
        options=df_parcelas["Mês"].dropna().unique(),
        default=[mes_atual]
    )
with col3:
    contratos_selecionados = st.multiselect(
        "Contrato",
        options=df_parcelas["Contrato"].dropna().unique(),
        default=df_parcelas["Contrato"].dropna().unique()
    )
with col4:
    status_selecionados = st.multiselect(
        "Status",
        options=df_parcelas["Status"].dropna().unique(),
        default=['ABERTO']
    )

# --- Aplicação dos Filtros e Exibição do DataFrame ---
query_parts = []
if anos_selecionados: query_parts.append("Ano in @anos_selecionados")
if meses_selecionados: query_parts.append("Mês in @meses_selecionados")
if contratos_selecionados: query_parts.append("Contrato in @contratos_selecionados")
if status_selecionados: query_parts.append("Status in @status_selecionados")

df_filtrado = df_parcelas
if query_parts:
    query_string = " & ".join(query_parts)
    df_filtrado = df_parcelas.query(query_string)

st.divider()
st.header('Parcelas Filtradas')
st.dataframe(
    df_filtrado,
    hide_index=False,
    use_container_width=True,
    column_config={
        "Dt.Lanç": st.column_config.DateColumn("Data Lançamento", format="DD/MM/YYYY"),
        "Emissão": st.column_config.DateColumn("Emissão", format="DD/MM/YYYY"),
        "Venc": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
        "Valor R$": st.column_config.NumberColumn("Valor da Parcela", format='R$ %.2f')
    }
)

# --- Seção de Ações ---
st.divider()
st.subheader("Selecione uma Ação:")

acao_escolhida = st.radio(
    "Selecione uma Ação:",
    ["Lançar Parcela", "Modificar/Reverter", "Duplicar Parcela", "Excluir Parcela"],
    horizontal=True,
    label_visibility="collapsed"
)

# --- Formulários de Ação ---
if acao_escolhida == "Lançar Parcela":
    st.subheader("Lançar Nova Parcela")

    # Filtra contratos que podem receber lançamentos no período atual
    filtro_lancamento = (df_parcelas['Mês'] == mes_atual) & (df_parcelas['Ano'] == ano_atual) & (df_parcelas['Status'] == 'ABERTO')
    contratos_lancaveis = df_parcelas.loc[filtro_lancamento, 'Contrato'].dropna().unique()

    if not contratos_lancaveis.any():
        st.error("Não há parcelas em aberto para o mês e ano atuais.")

    else:
        valor_extraido, doc_extraido = "", ""
        uploaded_file = st.file_uploader("1. Anexar Documento Fiscal para preenchimento automático (Opcional)", type=["pdf"], label_visibility="visible")
        if uploaded_file:
            info = extract_pdf(uploaded_file)
            valor_extraido = str(info.get('valor', '')) 
            doc_extraido = str(info.get('numero', ''))

            if not valor_extraido or not doc_extraido:
                st.warning('Não foi possível extrair todos os dados do PDF 😕. Preencha manualmente:')

        with st.form("form_lancar", clear_on_submit=True):
            st.subheader("2. Confirmar Lançamento")
            contrato_lanc = st.selectbox("Contrato para Lançamento:", options=contratos_lancaveis)
            valor_lanc = st.text_input("Valor R$", value=valor_extraido)
            doc_lanc = st.text_input("Número do Documento", value=doc_extraido)

            if st.form_submit_button("Confirmar Lançamento"):
                if not contrato_lanc or not valor_lanc:
                    st.warning("É necessário selecionar um contrato e preencher um valor válido.")

                else:
                    try:
                        valor = float(valor_lanc.replace(",", "."))
                        filtro_update = (df_parcelas["Contrato"] == contrato_lanc) & \
                                        (df_parcelas["Mês"] == mes_atual) & \
                                        (df_parcelas['Ano'] == ano_atual) & \
                                        (df_parcelas["Status"] == 'ABERTO')

                        if df_parcelas[filtro_update].empty:
                             st.error("Nenhuma parcela em aberto encontrada para este contrato no período atual.")
                        else:
                            index_to_update = df_parcelas[filtro_update].index[0]
                            df_parcelas.loc[index_to_update, ["Valor R$", "Dt.Lanç", "Doc", "Status"]] = [valor, data_lanc, doc_lanc, "LANÇADO"]
                            save_data(df_parcelas, PATH_CSV)

                    except ValueError:
                        st.error("O valor informado é inválido!")


elif acao_escolhida == "Modificar/Reverter":
    col_mod, col_rev = st.columns(2)
    
    with col_mod:
        with st.form("form_alterar"):
            st.subheader("Alterar Lançamento")
            linha_alt = st.text_input("Índice da linha para alterar")
            novo_valor = st.number_input("Novo Valor R$ (opcional)")
            novo_doc = st.text_input("Novo N° Documento (opcional)")

            if st.form_submit_button("Confirmar Alteração"):
                if not linha_alt or not (novo_valor or novo_doc):
                    st.warning("Preencha o índice da linha e pelo menos um campo para alterar.")
                else:
                    try:
                        idx = int(linha_alt)
                        if novo_valor: df_parcelas.loc[idx, "Valor R$"] = novo_valor
                        if novo_doc: df_parcelas.loc[idx, "Doc"] = novo_doc
                        df_parcelas.loc[idx, "Dt.Lanç"] = data_lanc
                        save_data(df_parcelas, PATH_CSV)
                    except (ValueError, KeyError):
                        st.error("Índice ou valor inválido.")

    with col_rev:
        with st.form("form_reverter"):
            st.subheader("Reverter Status para 'Aberto'")
            linha_rev = st.text_input("Índice da linha para reverter")

            if st.form_submit_button("Confirmar Reversão"):
                try:
                    idx = int(linha_rev)
                    df_parcelas.loc[idx, ["Valor R$", "Dt.Lanç", "Doc", "Status"]] = [pd.NA, pd.NA, pd.NA, 'ABERTO']
                    save_data(df_parcelas, PATH_CSV)
                except (ValueError, KeyError):
                    st.error("Índice inválido.")


elif acao_escolhida == "Duplicar Parcela":
    st.subheader("Duplicar Parcela em Aberto")
    filtro_dup = (df_parcelas['Mês'] == mes_atual) & (df_parcelas['Ano'] == ano_atual) & (df_parcelas['Status'] == 'ABERTO')
    contratos_duplicaveis = df_parcelas.loc[filtro_dup, 'Contrato'].dropna().unique()

    if not contratos_duplicaveis.any():
        st.warning("Não há contratos com parcelas abertas no período atual para duplicar.")
    else:
        with st.form('form_duplicar', clear_on_submit=True):
            contrato_dup = st.selectbox('Contrato a ter a parcela duplicada:', options=contratos_duplicaveis)
            qtd_dup = st.number_input('Adicionar quantas parcelas?:', min_value=1, value=1, step=1)
            
            if st.form_submit_button('Confirmar Duplicação'):
                linha_original = df_parcelas[filtro_dup & (df_parcelas['Contrato'] == contrato_dup)].head(1)
                if not linha_original.empty:
                    novas_linhas = pd.concat([linha_original] * qtd_dup, ignore_index=True)
                    df_atualizado = pd.concat([df_parcelas, novas_linhas], ignore_index=True)
                    st.session_state.df = df_atualizado 
                    save_data(df_atualizado, PATH_CSV)


elif acao_escolhida == "Excluir Parcela":
    st.subheader("Excluir Parcela")
    with st.form('form_excluir', clear_on_submit=True):
        linha_exc = st.text_input('Índice da linha a ser excluída:')
        
        if st.form_submit_button('Confirmar Exclusão'):
            try:
                idx = int(linha_exc)
                df_atualizado = df_parcelas.drop(idx).reset_index(drop=True)
                st.session_state.df = df_atualizado
                save_data(df_atualizado, PATH_CSV)

            except (ValueError, KeyError):
                st.error('Índice inválido! Por favor, insira um número de linha existente.')