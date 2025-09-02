import sys
import pandas as pd
import streamlit as st
from pathlib import Path

def show():
    st.set_page_config(
        page_title="Gestão Contratual",
        page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS7es5rHwd5SxSpDZ1LH9YLg9fyN5Bx_sAKfJ6L-3Zx-4-4uUvk0Qw7YYjFD9-mGXY_Gyw&usqp=CAU",
        layout="wide",
    )

    BASE_DIR = Path(__file__).resolve().parent.parent
    sys.path.append(str(BASE_DIR))
    DATA_PATH = BASE_DIR / "data" / "processed" / "prestadores.csv"

    try:
        contratos = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado em: {DATA_PATH}")
        st.stop()

    st.title("Prestadores de Contratos")
    st.write("---")
    st.header("Filtros")

    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([3, 3, 3, 3, 3, 4, 4, 3])

    for filtro in ["situacao", "prestador", "conta", "cc", "estab", "classificacao", "duracao", "qtd"]:
        if filtro not in st.session_state:
            st.session_state[filtro] = True

    def toggle(filtro):
        st.session_state[filtro] = not st.session_state[filtro]

    def formatar_duracao(dias):
        """Converte um número de dias para uma string formatada em anos, tratando o plural."""
        if pd.isna(dias):
            return "Não informado"
        
        anos = round((int(dias) * 30) / 365)

        if anos == 0 and int(dias) > 0: # Para durações menores que 6 meses
            return f"{dias} dias"
        
        label = 'ano' if anos == 1 else 'anos'
        return f"{anos} {label}"

# Aplica a função de formatação na coluna numérica original
    contratos['Duração'] = pd.to_numeric(contratos['Duração'], errors='coerce')
    contratos['Duração'] = contratos['Duração'].apply(formatar_duracao)

    with col1:
        if st.button("Selecionar Todos", key="btn_sit"):
            toggle("situacao")
        situacao_filtro = st.multiselect(
            "Situação",
            options=contratos["Situação"].dropna().unique(),
            default=contratos["Situação"].dropna().unique() if st.session_state["situacao"] else []
        )

    with col2:
        if st.button("Selecionar Todos", key="btn_pre"):
            toggle("prestador")
        prestador_filtro = st.multiselect(
            "Prestador",
            options=contratos["Prestador"].dropna().unique(),
            default=contratos["Prestador"].dropna().unique() if st.session_state["prestador"] else []
        )

    with col3:
        if st.button("Selecionar Todos", key="btn_con"):
            toggle("conta")
        conta_filtro = st.multiselect(
            "Conta",
            options=contratos["Conta"].dropna().unique(),
            default=contratos["Conta"].dropna().unique() if st.session_state["conta"] else []
        )

    with col4:
        if st.button("Selecionar Todos", key="btn_cc"):
            toggle("cc")
        cc_filtro = st.multiselect(
            "Centro de Custo",
            options=contratos["CC"].dropna().unique(),
            default=contratos["CC"].dropna().unique() if st.session_state["cc"] else []
        )

    with col5:
        if st.button("Selecionar Todos", key="btn_est"):
            toggle("estab")
        estab_filtro = st.multiselect(
            "Estabelecimento",
            options=contratos["Estab"].dropna().unique(),
            default=contratos["Estab"].dropna().unique() if st.session_state["estab"] else []
        )

    with col6:
        if st.button("Selecionar Todos", key="btn_cla"):
            toggle("classificacao")
        classificacao_filtro = st.multiselect(
            "Classificação",
            options=contratos["Classificacao"].dropna().unique(),
            default=contratos["Classificacao"].dropna().unique() if st.session_state["classificacao"] else []
        )

    with col7:
        if st.button("Selecionar Todos", key="btn_dur"):
            toggle("duracao")
        duracao_filtro = st.multiselect(
            "Duração do Contrato",
            options=contratos['Duração'].dropna().unique(),
            default=contratos['Duração'].dropna().unique() if st.session_state["duracao"] else []
        )

    with col8:
        if st.button("Selecionar Todos", key="btn_qtd"):
            toggle("qtd")
        qtd_filtro = st.multiselect(
            "Quantidade de Anexos",
            options=contratos["Qtd Notas"].dropna().unique(),
            default=contratos["Qtd Notas"].dropna().unique() if st.session_state["qtd"] else []
        )

    contratos_filtrado = contratos.copy()
    if situacao_filtro:
        contratos_filtrado = contratos_filtrado[contratos_filtrado["Situação"].isin(situacao_filtro)]
    if prestador_filtro:
        contratos_filtrado = contratos_filtrado[contratos_filtrado["Prestador"].isin(prestador_filtro)]
    if conta_filtro:
        contratos_filtrado = contratos_filtrado[contratos_filtrado["Conta"].isin(conta_filtro)]
    if cc_filtro:
        contratos_filtrado = contratos_filtrado[contratos_filtrado["CC"].isin(cc_filtro)]
    if estab_filtro:
        contratos_filtrado = contratos_filtrado[contratos_filtrado["Estab"].isin(estab_filtro)]
    if classificacao_filtro:
        contratos_filtrado = contratos_filtrado[contratos_filtrado["Classificacao"].isin(classificacao_filtro)]
    if duracao_filtro:
        contratos_filtrado = contratos_filtrado[contratos_filtrado['Duração'].isin(duracao_filtro)]
    if qtd_filtro:
        contratos_filtrado = contratos_filtrado[contratos_filtrado["Qtd Notas"].isin(qtd_filtro)]

    st.write('---')
    st.header("Contratos")
    st.dataframe(contratos_filtrado,
                 column_config={
                     "Início": st.column_config.DateColumn(
                         "Início",
                         format="DD/MM/YY"
                     ),
                     "Término": st.column_config.DateColumn(
                         "Término",
                         format="DD/MM/YY"
                     ),
                     "Renovação": st.column_config.DateColumn(
                         "Renovação",
                         format="DD/MM/YY"
                     ),
                     " Valor do Contrato R$ ": st.column_config.NumberColumn(
                         "Valor do Contrato",
                         format='R$ %.2f'
                     )
                 })