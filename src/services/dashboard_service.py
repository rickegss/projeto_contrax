import streamlit as st

def filtrar_dados_dashboard(df):
    """
    Aplica os filtros do session_state ao DataFrame de parcelas.
    """
    
    mask_comum = (
        (df["ano"].isin(st.session_state.dash_ano_selecionado)) &
        (df["contrato"].isin(st.session_state.dash_contrato_selecionado)) &
        (df["tipo"].isin(st.session_state.dash_tipo_selecionado)) &
        (df["estabelecimento"].isin(st.session_state.dash_estabelecimento_selecionado)) &
        (df["status"].isin(st.session_state.dash_status_selecionado))
    )

    df_filtrado = df[
        mask_comum &
        (df["mes_nome"].isin(st.session_state.dash_mes_selecionado)) &
        (~df["contrato"].str.startswith("HCOMPANY")) &
        (df["classificacao"].isin(st.session_state.dash_classificacao_selecionada))
    ]

    df_mensal = df[
        mask_comum &
        (~df["contrato"].str.startswith("HCOMPANY")) &
        (df["classificacao"].isin(st.session_state.dash_classificacao_selecionada))
    ]

    df_hcompany = df[
        (df["ano"].isin(st.session_state.dash_ano_selecionado)) &
        (df["contrato"].isin(st.session_state.dash_contrato_selecionado)) &
        (df["tipo"].isin(st.session_state.dash_tipo_selecionado)) &
        (df["estabelecimento"].isin(st.session_state.dash_estabelecimento_selecionado)) &
        (df["status"].isin(st.session_state.dash_status_selecionado))
    ]

    return df_filtrado, df_mensal, df_hcompany