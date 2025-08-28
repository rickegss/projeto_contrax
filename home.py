# streamlit run "c:/Users/ricardo.gomes/Desktop/Python VS/projeto_contratos/home.py"
import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from pages import parcelas, contratos

st.set_page_config(
    page_title="Gestão Contratual",
    page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS7es5rHwd5SxSpDZ1LH9YLg9fyN5Bx_sAKfJ6L-3Zx-4-4uUvk0Qw7YYjFD9-mGXY_Gyw&usqp=CAU",
    layout="wide",  # usa toda a largura da tela
    
)

# menu de navegação
tab1, tab2, tab3 = st.tabs([
    "Lançamento",
    "Contratos",
    "Dashboard"
])

with tab1:
    parcelas.show()
    
with tab2:
    contratos.show()

with tab3:
    ...

# Atualiza a página a cada 10 segundos (10000 ms)
st_autorefresh(interval=10000, key="auto_refresh")