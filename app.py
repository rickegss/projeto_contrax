import streamlit as st
import pandas as pd

st.title("Gestão de Contratos")
st.write("Parcelas de Contratos")

df = pd.read_csv(r"C:\Users\ricardo.gomes\Desktop\Python VS\projeto_contratos\data\contratos.csv")

col1, col2, col3, col4 = st.columns(4)

# Inicializa estado de "Selecionar Todos"
for filtro in ["ano", "mes", "prestador", "status"]:
    if filtro not in st.session_state:
        st.session_state[filtro] = True  # começa selecionado

# Função para alternar selecionar todos
def toggle(filtro):
    st.session_state[filtro] = not st.session_state[filtro]

# Coluna 1: Ano
with col1:
    st.button("Selecionar Todos", key="btn_ano", on_click=toggle, args=("ano",))
    ano_filt = st.multiselect(
        "Ano",
        options=df["Ano"].unique(),
        default=df["Ano"].unique() if st.session_state["ano"] else []
    )

# Coluna 2: Mês
with col2:
    st.button("Selecionar Todos", key="btn_mes", on_click=toggle, args=("mes",))
    mes_filt = st.multiselect(
        "Mês",
        options=df["Mês"].unique(),
        default=df["Mês"].unique() if st.session_state["mes"] else []
    )

# Coluna 3: Prestador
with col3:
    st.button("Selecionar Todos", key="btn_prestador", on_click=toggle, args=("prestador",))
    prestador_filt = st.multiselect(
        "Prestador",
        options=df["Prestador"].unique(),
        default=df["Prestador"].unique() if st.session_state["prestador"] else []
    )

# Coluna 4: Status
with col4:
    st.button("Selecionar Todos", key="btn_status", on_click=toggle, args=("status",))
    status_filt = st.multiselect(
        "Status",
        options=df["Status"].unique(),
        default=df["Status"].unique() if st.session_state["status"] else []
    )

# Filtragem final
df_filtrado = df[
    (df["Ano"].isin(ano_filt)) &
    (df["Mês"].isin(mes_filt)) &
    (df["Prestador"].isin(prestador_filt)) &
    (df["Status"].isin(status_filt))
]

st.write(df_filtrado)
