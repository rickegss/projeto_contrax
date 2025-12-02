import base64
from pathlib import Path
import streamlit as st

def setup_page_config():
    st.set_page_config(
            page_title="ContraX - Login",
            page_icon="src/logo/ContraX_Favicon.png",
            layout="wide"
        )

def get_homolog_css():
    return """
    <style>
    /* Botões Amarelos em Homolog */
    div.stButton > button:first-child {
        background-color: #FFD700 !important;
        color: black !important;
        border: 1px solid #FFA500 !important;
    }
    div.stButton > button:hover {
        background-color: #FFA500 !important;
        color: white !important;
    }
    /* Faixa de Aviso no Topo */
    div[data-testid="stHeader"]::after {
        content: "⚠️ AMBIENTE DE HOMOLOGAÇÃO ⚠️";
        visibility: visible;
        display: block;
        background-color: #FFD700;
        color: black;
        text-align: center;
        font-weight: bold;
        padding: 5px;
    }
    </style>
    """

def apply_login_styles(is_homolog=False):

    shadow_color = "rgba(255, 215, 0, 0.4)" if is_homolog else "rgba(15, 20, 30, 1)"
    border_color = "rgba(255, 215, 0, 0.8)" if is_homolog else "rgba(0.1, 0.1, 0.1, 0.1)"
    
    base_css = f"""
    <style>
    .stApp {{
        background-image: url("https://rare-gallery.com/uploads/posts/1105868-digital-art-black-background-minimalism-water-drops-blue-technology-circle-Cable-line-wing-screenshot-computer-wallpaper-font.jpg");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: scroll;
    }}

    div[data-testid="stLayoutWrapper"] {{
        background: rgba(0, 0, 3, 0.99);
        padding: 15px;
        border-radius: 75px;
        max-width: 550px;
        margin: 20px auto;
        box-shadow: 0 0 80px rgba(0, 0, 0, 0.9), 0 0 45px {shadow_color};
        border: 4px solid {border_color};
    }}
    </style>
    """

    full_css = base_css + (get_homolog_css() if is_homolog else "")
    st.markdown(full_css, unsafe_allow_html=True)

def apply_global_styles(is_homolog=False):
    if is_homolog:
        st.markdown(get_homolog_css(), unsafe_allow_html=True)

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

def render_footer(image_path="src/logo/GHE_logo.png"):
    img_base64 = img_to_base64(image_path)
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