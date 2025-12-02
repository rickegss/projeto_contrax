import streamlit as st
from core.app import main
from ui_config.general_config import (
    setup_page_config, 
    apply_login_styles, 
    apply_global_styles, 
    render_footer
)

setup_page_config()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "env" not in st.session_state:
    st.session_state.env = "prod"

def on_env_change():
    st.cache_data.clear()
    st.cache_resource.clear()

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
        return False

    col1, col2, col3 = st.columns([0.3, 3, 0.3])

    with col2:
        st.image("src/logo/ContraX_Logo.png", width=250)
        
        st.title("Login")
        
        is_homolog = st.toggle(
            "Modo Homologação", 
            value=(st.session_state.env == "homolog"),
            on_change=on_env_change
        )
        st.session_state.env = "homolog" if is_homolog else "prod"

        if st.session_state.env == "homolog":
            st.warning("⚠️ Você está acessando o ambiente de TESTES.")

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

is_homolog_active = (st.session_state.env == "homolog")

if not st.session_state.logged_in:
    apply_login_styles(is_homolog=is_homolog_active)
    check_password()
    render_footer()

else:
    apply_global_styles(is_homolog=is_homolog_active)

    with st.sidebar:
        if is_homolog_active:
            st.warning("Ambiente: HOMOLOGAÇÃO", icon="🚧")
        else:
            st.success("Ambiente: PRODUÇÃO", icon="✅")
            
        st.write(f"Usuário logado.")
        
        if st.button("Sair"):
            st.session_state.logged_in = False
            st.cache_data.clear()
            st.toast("Você saiu com sucesso!")
            st.rerun()
            
    main()