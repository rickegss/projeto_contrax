import streamlit as st
from _pages.home import main

# --- FUNÇÃO DE LOGIN ---
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

    st.title("Login")
    st.text_input("Nome de Usuário", key="username").strip()
    st.text_input("Senha", type="password", key="password").strip()

    if st.button("Entrar"):
        if password_entered():
            st.rerun()
        else:
            st.error("😕 Nome de usuário ou senha incorretos.")
            
    return False

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    check_password()


else:
    st.toast("Você está logado com sucesso!")
    main()
    
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.toast("Você saiu com sucesso!")
        st.rerun() 