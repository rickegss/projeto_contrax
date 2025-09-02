import streamlit as st
from streamlit_autorefresh import st_autorefresh
from pages import parcelas, contratos, dashboard

import sys
from pathlib import Path
st.markdown("""
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

st.set_page_config(
    page_title="Gestão Contratual",
    page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS7es5rHwd5SxSpDZ1LH9YLg9fyN5Bx_sAKfJ6L-3Zx-4-4uUvk0Qw7YYjFD9-mGXY_Gyw&usqp=CAU",
    layout="wide",   
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
    dashboard.show()

# Atualiza a página a cada 10 segundos (10000 ms)
st_autorefresh(interval=10000, key="auto_refresh")