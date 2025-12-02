import streamlit as st
from src._pages.parcelas import home
from src._pages.contratos import contratos
from src._pages.dashboard import show_dashboard

def main():
    logo1, logo2 = st.columns([0.2, 1])
    with logo1: st.image("src/logo/ContraX_Logo.png", width=240, caption="Gestão de Contratos")
    with logo2: st.image("src/logo/hcompany_branco_intranet.png", width=200)

    tab_lancamentos, tab_contratos, tab_dashboard = st.tabs([" Lançamentos ", " Contratos ", " Dashboard "])

    with tab_lancamentos: home()
    with tab_contratos: contratos()
    with tab_dashboard: show_dashboard()

if __name__ == "__main__":
    main()