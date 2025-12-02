import streamlit as st
from src.core.app import main
from src.ui_config.general_config import setup_page_config, apply_login_styles, render_footer

setup_page_config()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def check_password():
    def password_entered():
        if (
            st.session_state["username"] == st.secrets["credentials"]["username"]
            and st.session_state["password"] == st.secrets["credentials"]["password"]
        ):
            st.session_state["logged_in"] = True
            del st.session_state["password"]
            del st.session_state["username"]
            return True
        else:
            st.session_state["logged_in"] = False
            return False

    col1, col2, col3 = st.columns([0.3,3,0.3])

    with col2:

            st.image("src/logo/ContraX_Logo.png", width=250)
            st.title("Login")
            st.divider()
            st.subheader('Preencha suas credenciais:')
            st.text_input("Nome de Usuário", key="username")
            st.text_input("Senha", type="password", key="password")
            st.divider()

            if st.button("Entrar"):
                if password_entered():
                    st.rerun()
                else:
                    st.error("😕 Nome de usuário ou senha incorretos.")
            return False


if not st.session_state.logged_in:
    apply_login_styles()
    check_password()
    render_footer()

else:
    with st.sidebar:
        st.success("Você está logado!")
        if st.button("Sair"):
            st.session_state.logged_in = False
            st.toast("Você saiu com sucesso!")
            st.rerun()
    main()