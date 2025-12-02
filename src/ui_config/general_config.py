import base64
from pathlib import Path
import streamlit as st

def setup_page_config():
    st.set_page_config(
            page_title="ContraX - Login",
            page_icon="logo/ContraX_Favicon.png",
            layout="wide"
        )

def apply_login_styles():
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

@st.cache_data  
def img_to_base64(image_path):
    path = Path(image_path)
    if not path.exists():
        return None
    try:
        with path.open("rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None


def render_footer(IMG_PATH = "src/logo/GHE_logo.png"):
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