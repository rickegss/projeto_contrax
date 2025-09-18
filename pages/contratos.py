import pandas as pd
import streamlit as st
from pathlib import Path

def formatar_duracao(dias):
    if pd.isna(dias):
        return "Não informado"
    
    anos = round(int(dias) / 12) if int(dias) >= 12 else 0

    if anos == 0 and int(dias) > 0:
        label_mes = 'mês' if int(dias) == 1 else 'meses'
        return f"{int(dias)} {label_mes}"
    
    label_ano = 'ano' if anos == 1 else 'anos'
    return f"{anos} {label_ano}"

@st.cache_data
def load_and_prepare_data(path):
    try:
        df = pd.read_csv(path)
        # Converte a coluna 'Duração' para numérico, tratando erros
        df['Duração Num'] = pd.to_numeric(df['Duração'], errors='coerce')
        # Cria uma nova coluna formatada para exibição
        df['Duração Formatada'] = df['Duração Num'].apply(formatar_duracao)
        return df
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado em: {path}")
        st.stop()

def initialize_state(filters):
    if "initialized_prestadores" in st.session_state:
        return
    
    st.session_state.initialized_prestadores = True
    for key in filters:
        st.session_state[f"toggle_{key}"] = True

def show_filters(df, filter_config):
    cols = st.columns(len(filter_config))
    selections = {}

    for i, (key, label, col_name) in enumerate(filter_config):
        with cols[i]:
            if st.button(f"Todos/Nenhum", key=f"btn_{key}"):
                st.session_state[f"toggle_{key}"] = not st.session_state[f"toggle_{key}"]
            
            options = df[col_name].dropna().unique()
            default_value = list(options) if st.session_state[f"toggle_{key}"] else []
            
            selections[key] = st.multiselect(
                label,
                options=options,
                default=default_value,
                key=f"ms_{key}"
            )
    return selections

def show():
    st.set_page_config(
        page_title="Gestão Contratual",
        layout="wide",
    )

    script_dir = Path(__file__).resolve().parent.parent
    path_csv = script_dir / 'data' / 'processed' / 'prestadores.csv'
    
    contratos = load_and_prepare_data(path_csv)

    filter_config = [
        ("situacao", "Situação", "Situação"),
        ("prestador", "Prestador", "Prestador"),
        ("conta", "Conta", "Conta"),
        ("cc", "Centro de Custo", "CC"),
        ("estab", "Estabelecimento", "Estab"),
        ("classificacao", "Classificação", "Classificacao"),
        ("duracao", "Duração", "Duração Formatada"),
    ]
    
    filter_keys = [f[0] for f in filter_config]
    initialize_state(filter_keys)

    st.title("Prestadores de Contratos")
    st.divider()
    st.header("Filtros")

    selections = show_filters(contratos, filter_config)

    query_parts = []
    filter_map = {
        "situacao": "`Situação` in @selections['situacao']",
        "prestador": "`Prestador` in @selections['prestador']",
        "conta": "`Conta` in @selections['conta']",
        "cc": "`CC` in @selections['cc']",
        "estab": "`Estab` in @selections['estab']",
        "classificacao": "`Classificacao` in @selections['classificacao']",
        "duracao": "`Duração Formatada` in @selections['duracao']",
    }
    
    for key, selection in selections.items():
        if selection:
            query_parts.append(filter_map[key])
    
    contratos_filtrado = contratos
    if query_parts:
        query_string = " & ".join(query_parts)
        contratos_filtrado = contratos.query(query_string)

    st.divider()
    st.header("Contratos")
    st.dataframe(
        contratos_filtrado,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Início": st.column_config.DateColumn("Início", format="DD/MM/YY"),
            "Término": st.column_config.DateColumn("Término", format="DD/MM/YY"),
            "Renovação": st.column_config.DateColumn("Renovação", format="DD/MM/YY"),
            " Valor do Contrato R$ ": st.column_config.NumberColumn("Valor do Contrato", format='R$ %.2f'),
            "Duração Num": None,
            "Duração Formatada": "Duração"
        }
    )

show()