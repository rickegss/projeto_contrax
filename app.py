# streamlit run "c:/Users/ricardo.gomes/Desktop/Python VS/projeto_contratos/app.py"
import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh


st.title("Gestão de Contratos")
st.write("Filtrar parcelas")

# planilha de contratos
parcelas = pd.read_csv(r"C:\Users\ricardo.gomes\Desktop\Python VS\projeto_contratos\data\contratos.csv")

# coluna superior de filtros
col1, col2, col3, col4 = st.columns(4)

# dados de data
mes_dict = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4,
    "mai": 5, "jun": 6, "jul": 7, "ago": 8,
    "set": 9, "out": 10, "nov": 11, "dez": 12
}
now = pd.Timestamp.now()
mes_atual = [k for k, v in mes_dict.items() if v == now.month][0]
data_lanc = now.strftime("%d/%m/%y %H:%M")


def update_csv():
    """
    Atualizar a planilha 
    """
    parcelas.to_csv(r"C:\Users\ricardo.gomes\Desktop\Python VS\projeto_contratos\data\contratos.csv", index=False)

# inicializa selecionar todos
for filtro in ["ano", "mes", "prestador", "status"]:
    if filtro not in st.session_state and filtro == "prestador":
        st.session_state[filtro] = True  # prestador começa selecionado
    elif filtro not in st.session_state and filtro != "prestador":
        st.session_state[filtro] = False

# função para alternar selecionar todos
def toggle(filtro):
    st.session_state[filtro] = not st.session_state[filtro]

# filtro ano
with col1:
    if st.button("Selecionar Todos", key="btn_ano"):
        toggle("ano")
    ano_filt = st.multiselect(
        "Ano",
        options=parcelas["Ano"].unique(),
        default=parcelas["Ano"].unique() if st.session_state["ano"] else []
    )

# filtro mes
with col2:
    if st.button("Selecionar Todos", key="btn_mes"):
        toggle("mes")
    mes_filt = st.multiselect(
        "Mês",
        options=parcelas["Mês"].unique(),
        default=parcelas["Mês"].unique() if st.session_state["mes"] else []
    )

# filtro prestador
with col3:
    if st.button("Selecionar Todos", key="btn_prestador"):
        toggle("prestador")
    prestador_filt = st.multiselect(
        "Prestador",
        options=parcelas["Prestador"].unique(),
        default=parcelas["Prestador"].unique() if st.session_state["prestador"] else []
    )

# filtro status
with col4:
    if st.button("Selecionar Todos", key="btn_status"):
        toggle("status")
    status_filt = st.multiselect(
        "Status",
        options=parcelas["Status"].unique(),
        default=parcelas["Status"].unique() if st.session_state["status"] else []
    )

# exibição final
parcelas_filtrado = parcelas[
    (parcelas["Ano"].isin(ano_filt)) &
    (parcelas["Mês"].isin(mes_filt)) &
    (parcelas["Prestador"].isin(prestador_filt)) &
    (parcelas["Status"].isin(status_filt))
]
st.write(parcelas_filtrado)

col5, col6 = st.columns(2)

# botão lançar parcela
with col5:
    if "show" not in st.session_state:
        st.session_state.show = False

    if st.button("Lançar parcela", key="lancar"):
        st.session_state.show = not st.session_state.show  # alterna abrir/fechar

    if st.session_state.show:
        if "contrato_val" not in st.session_state:
            st.session_state.contrato_val = []
        if "valor_val" not in st.session_state:
            st.session_state.valor_val = ""
        if "doc_val" not in st.session_state:
            st.session_state.doc_val = ""

        # inputs armazenados no session_state
        st.session_state.contrato_val = st.multiselect(
            "Contrato:",
            options=parcelas["Contrato"].unique(),
            default=st.session_state.contrato_val
        )
        st.session_state.valor_val = st.text_input(
            "Valor R$",
            value=st.session_state.valor_val
        )
        st.session_state.doc_val = st.text_input(
            "Número do documento",
            value=st.session_state.doc_val
        )

        # botão confirmar lançamento 
        if st.button("Confirmar lançamento"):
            if st.session_state.contrato_val and st.session_state.valor_val:
                try:
                    valor = float(st.session_state.valor_val)

                    filtro = (parcelas["Contrato"].isin(st.session_state.contrato_val)) & (parcelas["Mês"] == mes_atual)
                    parcelas.loc[filtro, ["Valor R$", "Dt.Lanç", "Doc"]] = [
                        valor, data_lanc, st.session_state.doc_val
                    ]
                    parcelas.loc[filtro, "Status"] = "LANÇADO"
                    update_csv()
                    st.success("Parcela lançada")

                    # fecha o bloco de inputs após lançar
                    st.session_state.show = False
                except ValueError:
                    st.error("Digite um valor numérico válido!")
            else:
                st.warning("Preencha todos os campos!")

# alterar parcela lançada:
with col6:
    if "show2" not in st.session_state:
        st.session_state.show2 = False

    if st.button("Modificar lançamento", key="modificar"):
        st.session_state.show2 = not st.session_state.show2 

    if st.session_state.show2:
        if "num_linha_val" not in st.session_state:
            st.session_state.num_linha_val = ""
        if "valor_val" not in st.session_state:
            st.session_state.valor_val = ""
        if "doc_val" not in st.session_state:
            st.session_state.doc_val = ""
        
        st.session_state.num_linha_val = st.text_input(
            "Insira o número da linha da parcela", 
            value=st.session_state.num_linha_val
        )
        
        st.session_state.valor_val = st.text_input(
            "Valor R$:",
            value=st.session_state.valor_val
        )

        if st.button("Alterar número de documento"):
            st.session_state.doc_val = st.text_input(
                "N° Documento",
                value=st.session_state.doc_val
            )

        # botão de confirmação
        if st.button("Confirmar Alteração"):
            if st.session_state.valor_val and st.session_state.num_linha_val:
                try:
                    linha_mod = int(st.session_state.num_linha_val)
                    valor_mod = float(st.session_state.valor_val)

                    parcelas.iloc[linha_mod, parcelas.columns.get_indexer(["Valor R$", "Dt.Lanç"])] = [valor_mod, data_lanc] 
                    st.success("Parcela atualizada")
                    update_csv()

                except ValueError:
                    st.error("Digite um valor numérico válido!")
            else:
                    st.warning("Preencha todos os campos!")

# Atualiza a página a cada x segundos (x000 ms)
st_autorefresh(interval=30000, key="auto_refresh")