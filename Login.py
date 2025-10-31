import streamlit as st
from _pages.parcelas import main

st.set_page_config(
        page_title="ContraX - Login",
        page_icon="logo/ContraX_Favicon.png",
        layout="centered",
    )

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    page_background = """
    <style>
    .stApp {
        background-image: url("https://rare-gallery.com/uploads/posts/1105868-digital-art-black-background-minimalism-water-drops-blue-technology-circle-Cable-line-wing-screenshot-computer-wallpaper-font.jpg");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: scroll;
    }

    div[data-testid="stLayoutWrapper"] {
        background: rgba(0, 0, 3, 0.99);
        padding: 15px;
        border-radius: 75px;
        max-width: 550px;
        margin: 20px auto;
        box-shadow: 0 0 80px rgba(0, 0, 0, 0.9), 0 0 45px rgba(15, 20, 30, 1);
        border: 4px solid rgba(0.1, 0.1, 0.1, 0.1);
    }
    </style>
    """
    st.markdown(page_background, unsafe_allow_html=True)



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

    col1, col2, col3 = st.columns([0.3,3,0.3])

    with col2:

            st.image("logo\ContraX_Logo.png", width=250)
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


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    check_password()


else:
    with st.sidebar:
        st.success("Você está logado!")
        if st.button("Sair"):
            st.session_state.logged_in = False
            st.toast("Você saiu com sucesso!")
            st.rerun()
    main()

@st.cache_data  # Cache para melhorar a performance
def img_to_base64(image_path):
    import base64
    from pathlib import Path

    path = Path(image_path)
    if not path.exists():
        st.error(f"Caminho da imagem não encontrado: {image_path}")
        return None
    
    try:
        with path.open("rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.error(f"Erro ao ler a imagem {image_path}: {e}")
        return None
    
IMG_PATH = "logo/GHE_logo.png"
img_base64 = img_to_base64(IMG_PATH)

if img_base64:
    footer_html = f"""
    <div style="
        text-align: center; 
        padding-top: 15px; 
        padding-bottom: 15px; 
        border-top: 5px solid #ffffff;
        border-radius: 5px;
    ">
        <img src="data:image/png;base64,{img_base64}" alt="logo" width="130">
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
else:
    st.warning("Não foi possível carregar a imagem do rodapé.")