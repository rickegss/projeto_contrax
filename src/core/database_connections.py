import streamlit as st
import pandas as pd
from supabase import create_client, Client
from utils.stamp import mes_dict

@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
    key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
    if key == st.secrets["connections_homolog"]["supabase"]["SUPABASE_KEY"]:
        st.title("Ambiente de teste")

    return create_client(url, key)

@st.cache_data(ttl=300)
def load_data(table_name: str) -> pd.DataFrame:
    supabase = get_supabase_client()
    all_data = []
    offset = 0
    batch_size = 1000

    try:
        while True:
            data = supabase.table(table_name).select("*").range(offset, offset + batch_size - 1).execute()

            if not data.data:
                break
            
            all_data.extend(data.data)
            offset += batch_size
            
    except Exception as e:
        st.error(f"Erro de conexão com o Supabase na tabela '{table_name}'. O banco pode estar pausado ou indisponível.")
        st.error(f"Detalhe técnico: {e}")

        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    
    if df.empty:
        return df

    if table_name == "parcelas":
        cols_date = ["data_lancamento", "data_emissao", "data_vencimento"]
        for col in cols_date:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        cols_cat = ["tipo", "contrato", "estabelecimento", "status"]
        for col in cols_cat:
            if col in df.columns:
                df[col] = df[col].astype("category")
        
        if 'mes' in df.columns:
            month_display_map = {v: k for k, v in mes_dict.items()}
            df['mes_nome'] = df['mes'].map(lambda x: month_display_map.get(x, f'Mês {x}'))

    return df