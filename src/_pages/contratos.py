import time
import pandas as pd
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client
from src.utils.stamp import mes_dict, ano_atual
import io

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

def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
    return output.getvalue()

def formatar_brl(valor) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def relatorio_anual(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['valor'] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
    df['ano'] = pd.to_numeric(df['ano'], errors='coerce')
    
    df = df[(df["ano"] == ano_atual) & (df["status"] == 'LANÇADO')]

    if "" not in df['contrato'].cat.categories:
        df['contrato'] = df['contrato'].cat.add_categories([""])
    
    contratos_limpos = df['contrato'].fillna("")
    contratos_match = contratos_limpos.str.upper().str.strip()

    df["contrato_unificado"] = contratos_limpos.str.replace(r'\s+\d+$', '', regex=True)
    
    mappings = {
        "INGR": "INGRAM", "INGRAM": "INGRAM", "TOTVS": "TOTVS", "ALGAR": "ALGAR",
        "CLARO": "CLARO", "HCOMPANY": "HCOMPANY", "UNE": "UNE TELECOM", "SAP": "SAP",
        "PRODUTIVE": "PRODUTIVE", "OI": "OI TELECOM", "NEOMIND": "NEOMIND",
        "LUCAS": "LUCAS BICALHO", "JETTELECOM": "JETTELECOM", "ILOC3": "ILOC3 LOCAÇÕES",
        "HPFS": "HPFS - LOCAÇÃO", "GRENKE": "GRENKE", "GLOBO": "GLOBO SOLUÇÕES", "COMPEX": "COMPEX"
    }
    
    for key, val in mappings.items():
        df.loc[contratos_match.str.startswith(key), "contrato_unificado"] = val
    
    df.loc[contratos_match.str.contains("VELOMAX"), "contrato_unificado"] = "VELOMAX"
    df["contrato_unificado"] = df["contrato_unificado"].replace("", "Sem Contrato")

    if 'mes' in df.columns:
        df['mes'] = pd.to_numeric(df['mes'], errors='coerce')
        meses_ordenados = list(df.sort_values(by='mes')['mes_nome'].unique())
    else:
        meses_ordenados = sorted(list(df['mes_nome'].unique()))

    df_relatorio = pd.pivot_table(
        df, index="contrato_unificado", columns="mes_nome", values="valor",
        aggfunc="sum", fill_value=0
    )

    colunas_presentes = [mes for mes in meses_ordenados if mes in df_relatorio.columns]
    if colunas_presentes:
        df_relatorio = df_relatorio[colunas_presentes]

    df_relatorio["Total"] = df_relatorio.sum(axis=1)
    df_relatorio = df_relatorio.reset_index().rename(columns={'contrato_unificado': 'Contrato'})
    
    df_relatorio = df_relatorio[~df_relatorio['Contrato'].str.startswith("HCOMPANY")]

    colunas_numericas = df_relatorio.columns.drop('Contrato')
    somas_colunas = df_relatorio[colunas_numericas].sum()
    linha_total = pd.DataFrame(somas_colunas).T
    linha_total['Contrato'] = '[TOTAL R$]:'
    
    df_relatorio = pd.concat([df_relatorio, linha_total], ignore_index=True)
    
    return df_relatorio.style.format(formatar_brl, subset=colunas_numericas)

def show_stats(df, coluna_valor, parcelas_df) -> None:
    count = len(df)
    total = df[coluna_valor].sum()
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style='width: 100%; text-align: left;'>
            <div style='display: inline-block; border: 2px solid; padding: 3px 10px; border-radius: 25px; font-size: 15px; width: 20%;'>
                Contagem: {count}
            </div>
        </div>    
        """, unsafe_allow_html=True)

    with col2:
        chave_unica = f"contrato_bttn_relatorio_{coluna_valor}"
        if st.button("Gerar relatório Anual", key=chave_unica):
            df_styled = relatorio_anual(parcelas_df)
            st.dataframe(df_styled)
            
            st.download_button(
                label=" 📥 Exportar para Excel",
                data=to_excel(df_styled.data),
                file_name=f"relatorio_anual_{ano_atual}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_excel_{chave_unica}" 
            )
            if st.button(" ↩️ Fechar relatório", key=f"contrato_bttn_fechar_{coluna_valor}"):
                st.rerun()

    with col3:
        val_str = "0,00" if total is None else formatar_brl(total)
        st.markdown(f"""
        <div style='width: 100%; text-align: right;'>
            <div style='display: inline-block; border: 2px solid; padding: 3px 10px; border-radius: 25px; font-size: 15px; width: 25%;'>
                Total: R$ {val_str}
            </div>
        </div>
        """, unsafe_allow_html=True)

def initialize_state(df, filters) -> None:
    if "initialized_contratos" in st.session_state:
        return
    
    st.session_state.initialized_contratos = True
    for key in filters:
        st.session_state[f"toggle_{key}"] = True
    
        if f'contratos_{key}_selecionado' not in st.session_state:
            if key in ['contrato', 'estabelecimento', 'classificacao']:
                st.session_state[f'contratos_{key}_selecionado'] = df[key].dropna().sort_values().unique().tolist()
            elif key == 'pedido':
                st.session_state[f'contratos_pedido_selecionado'] = ['Contrato']

    if 'contratos_situacao_selecionado' not in st.session_state:
        st.session_state[f'contratos_situacao_selecionado'] = ["ATIVO"]

def show_filters(df, filter_config) -> None:
    from .parcelas import selecionar_todos, limpar_selecao
    
    cols = st.columns(len(filter_config))
    
    labels = {
        "situacao": "Situação", "contrato": "Contratos", 
        "estabelecimento": "Estabelecimento", "classificacao": "Classificação", 
        "pedido": "Contrato/Pedido"
    }

    for i, key in enumerate(filter_config):
        with cols[i]:
            label = labels.get(key, key.capitalize())
            
            if key == "pedido":
                options = ["Contrato", "Pedido"]
            else:
                options = df[key].dropna().unique()
                if key != "situacao": 
                    options = sorted(options.tolist()) if hasattr(options, 'tolist') else sorted(options)
            
            if not isinstance(options, list) and not isinstance(options, pd.Categorical):
                 options = list(options)

            key_state = f'contratos_{key}_selecionado'
            
            st.multiselect(label, options=options, key=key_state)
            
            b_col1, b_col2 = st.columns(2)
            b_col1.button("Todos", on_click=selecionar_todos, args=(key_state, options), key=f'contratos_todos_{key}')
            b_col2.button("Limpar", on_click=limpar_selecao, args=(key_state,), key=f'contratos_limpar_{key}')
            
            if key == "pedido":
                 st.button("Recarregar tabela", on_click=st.cache_data.clear, key='contratos_atualizar')


# --- CRUD  ---
def new_contract(df) -> None:
    ccol1, = st.columns(1)
    supabase = get_supabase_client()

    with ccol1:
        st.subheader("Dados do Contrato")
        
        with st.form("form_novo_contrato", clear_on_submit=True):
            contrato = st.text_input("Nome do Contrato*").upper()
            cnpj = st.text_input("CNPJ")
            numero_contrato = st.text_input("Número do Contrato*")
            estabelecimento = st.segmented_control("Estabelecimento*", options=(df["estabelecimento"].dropna().unique()))
            valor_contrato = st.number_input("Valor do Contrato R$", format="%.2f", step=1.0, min_value=1.0)
            duracao = st.number_input("Duração do contrato (meses)*", format="%d", min_value=1)
            conta = str(float(st.number_input("Conta", step=1.0)))
            centro_custo = str(float(st.number_input("Centro de Custo", step=1.0)))
            classificacao = st.segmented_control("Classificação*", options=df["classificacao"].dropna().unique())  
            data_inicio = st.date_input("Data de Início", value=datetime.now().date())
            
            st.markdown("### Anexos:")
            anexos = [lbl for lbl, chk in [("NF", st.checkbox("Nota Fiscal")), ("BOL", st.checkbox("BOL")), ("FAT", st.checkbox("FAT"))] if chk]
            anexos_str = " / ".join(anexos)

            st.divider()

            if st.form_submit_button("Confirmar adição de contrato", type="secondary"):
                if any([not contrato, not numero_contrato, not estabelecimento, not classificacao, duracao <= 0]):
                    st.error("Preencha todos os campos obrigatórios.", icon="🚨")
                else:
                    data_inicio_dt = datetime.combine(data_inicio, datetime.min.time())
                    data_termino_dt = data_inicio_dt + relativedelta(months=duracao, days=-1)
                    valor_parcela = valor_contrato / duracao

                    new_contrato = {
                        "situacao": "ATIVO", "numero": numero_contrato, "contrato": contrato,
                        "conta": conta, "centro_custo": centro_custo, "estabelecimento": estabelecimento,
                        "classificacao": classificacao, "cnpj": cnpj, "anexos": anexos_str,
                        "valor_contrato": valor_contrato, "inicio": data_inicio_dt.isoformat(),
                        "termino": data_termino_dt.isoformat(),
                    }
                    
                    try:
                        response = supabase.table("contratos").insert(new_contrato).execute()
                        new_id = response.data[0]["id"]
                        
                        batch_parcelas = []
                        for i in range(duracao):
                            d_parc = data_inicio_dt + relativedelta(months=i)
                            batch_parcelas.append({
                                "contrato_id": new_id, "situacao": "ATIVO",
                                "ano": d_parc.year, "mes": d_parc.month,
                                "data_emissao": d_parc.isoformat(),
                                "data_vencimento": (d_parc + relativedelta(months=1)).isoformat(),       
                                "tipo": "CONTRATO", "contrato": contrato,
                                "classificacao": classificacao, "referente": classificacao,
                                "estabelecimento": estabelecimento, "status": "ABERTO",
                                "valor": valor_parcela
                            })
                        
                        supabase.table("parcelas").insert(batch_parcelas).execute()
                        st.toast(f"Contrato criado com {len(batch_parcelas)} parcelas.")
                        time.sleep(1)
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao criar contrato: {e}")


def delete_contract(df) -> None: 
    ccol2, = st.columns(1)
    supabase = get_supabase_client()

    with ccol2:
        st.subheader("Excluir Contrato")
        with st.form("form_excluir_contrato", clear_on_submit=True):
            contrato_exc = st.selectbox("Contrato a excluir: ", options=df["contrato"].dropna().unique())
            st.warning("Atenção: A exclusão é permanente.", icon="⚠️")

            if st.form_submit_button("Confirmar Exclusão", type="primary"):
                try:
                    supabase.table("contratos").delete().eq("contrato", contrato_exc).execute()
                    supabase.table("parcelas").delete().eq("contrato", contrato_exc).execute()
                    st.success("Contrato excluído!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")

def active_deactive_contract(df) -> None:
    coll3, = st.columns(1)
    supabase = get_supabase_client()

    with coll3:
        st.subheader("Ativar/Desativar Contrato")
        opcoes_contrato = df["contrato"].dropna().unique()
        
        if not any(opcoes_contrato):
            st.warning("Nenhum contrato disponível.")
            return

        contrato_sel = st.selectbox("Selecione o Contrato:", options=opcoes_contrato, key="sb_contrato_status")

        if contrato_sel:
            contrato_info = df[df["contrato"] == contrato_sel]
            if not contrato_info.empty:
                status_atual = contrato_info.iloc[0]["situacao"]
                novo_status = "INATIVO" if status_atual == "ATIVO" else "ATIVO"
                btn_label = f"{'Desativar' if status_atual == 'ATIVO' else 'Ativar'} Contrato"

                with st.form(f"form_{novo_status.lower()}_contrato"):
                    if st.form_submit_button(btn_label, type="primary"):
                        try:
                            supabase.table("contratos").update({"situacao": novo_status}).eq("contrato", contrato_sel).execute()
                            supabase.table("parcelas").update({"situacao": novo_status}).eq("contrato", contrato_sel).execute()
                            st.success(f"Contrato {novo_status.lower()} com sucesso!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao alterar status: {e}")

def edit_contract(df) -> None:
    coll4, = st.columns(1)
    supabase = get_supabase_client()

    with coll4:
        st.subheader("Editar informações")
        opcoes_contrato = df["contrato"].dropna().unique()
        if not any(opcoes_contrato):
            st.warning("Nenhum contrato existente.")
            return

        contrato_edit = st.selectbox("Selecione o Contrato", options=opcoes_contrato)
        st.markdown("##### Dados do Contrato")
        
        dados = supabase.table("contratos").select("*").eq("contrato", contrato_edit).execute().data[0]
        dados["valor_contrato"] = dados.get("valor_contrato") or 1

        with st.form("form_editar_contrato", clear_on_submit=True):
            duracao = 1
            if dados["termino"] and dados["inicio"]:
                d_rel = relativedelta(datetime.fromisoformat(dados["termino"]), datetime.fromisoformat(dados["inicio"]))
                duracao = int(d_rel.years * 12 + d_rel.months)
            
            contrato = st.text_input("Nome do Contrato", value=dados["contrato"]).upper()
            cnpj = st.text_input("CNPJ", value=dados["cnpj"])
            numero_contrato = st.text_input("Número (ou 'PEDIDO')", value=dados["numero"])
            descricao = st.text_input("Descrição", value=dados["descricao"])
            st.markdown("---")
            
            try:
                idx_estab = df["estabelecimento"].dropna().unique().tolist().index(dados["estabelecimento"])
            except ValueError: idx_estab = 0
            
            try:
                idx_class = list(df["classificacao"].dropna().unique()).index(dados["classificacao"])
            except ValueError: idx_class = 0

            estabelecimento = st.selectbox("Estabelecimento", options=df["estabelecimento"].dropna().unique(), index=idx_estab)
            valor_contrato = st.number_input("Valor R$", format="%.2f", step=1.0, min_value=1.0, value=float(dados["valor_contrato"]))
            duracao = st.number_input("Duração (meses)", format="%d", value=duracao, min_value=1, step=1)
            conta = str(float(st.number_input("Conta", step=1.0, value=float(dados.get("conta") or 0))))
            centro_custo = str(float(st.number_input("Centro de Custo", step=1.0, value=float(dados.get("centro_custo") or 0))))
            classificacao = st.selectbox("Classificação", options=df["classificacao"].dropna().unique(), index=idx_class)
            data_inicio = st.date_input("Data de Início", value=datetime.fromisoformat(dados["inicio"]).date() if dados["inicio"] else None)

            if st.form_submit_button("Atualizar Dados", type="primary"):
                edited_contract = {
                    "situacao": "ATIVO", "numero": numero_contrato, "contrato": contrato,
                    "cnpj": cnpj, "conta": conta, "centro_custo": centro_custo,
                    "classificacao": classificacao, "estabelecimento": estabelecimento,
                    "descricao": descricao, "valor_contrato": valor_contrato, "anexos": dados["anexos"],
                }
                if data_inicio:
                    edited_contract["inicio"] = data_inicio.isoformat()
                    edited_contract["termino"] = (data_inicio + relativedelta(months=duracao, days=-1)).isoformat()

                try:
                    supabase.table("contratos").update(edited_contract).eq("contrato", contrato_edit).execute()
                    st.success("Atualizado com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")

def renew_contract(df) -> None:
    coll5, = st.columns(1)
    supabase = get_supabase_client()

    with coll5:
        st.subheader("Renovação de Contrato")
        hoje = datetime.now().date()
        df['termino_dt'] = pd.to_datetime(df['termino']).dt.date
        
        contratos_renovar = df.loc[df["termino_dt"] < hoje, "contrato"].dropna().unique()
        
        if len(contratos_renovar) == 0:
            st.warning("Nenhum contrato para renovar.")
            return
        
        contrato_renew = st.selectbox("Contrato a renovar:", options=contratos_renovar)
        data_termino = df.loc[df["contrato"] == contrato_renew, "termino_dt"].iloc[0]
        dias_vencido = (hoje - data_termino).days
        
        st.warning(f"O contrato {contrato_renew} está vencido há {dias_vencido} dias.")

        with st.form("form_renovar_contrato", clear_on_submit=True):
            dias_renovar = st.number_input("Renovar por quantos dias?", min_value=30, step=30)
            if st.form_submit_button("Renovar Contrato", type="primary"):
                try:
                    renovacao = {
                        "termino": (hoje + relativedelta(days=dias_renovar)).isoformat(),
                        "situacao": "ATIVO",
                    }
                    supabase.table("contratos").update(renovacao).eq("contrato", contrato_renew).execute()
                    st.success("Renovado com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao renovar: {e}")


# --- FUNÇÃO PRINCIPAL ---
def contratos() -> None:
    contratos_df = load_data("contratos")
    parcelas_df = load_data("parcelas")

    filter_config = ["situacao", "contrato", "estabelecimento", "classificacao", "pedido"]
    initialize_state(contratos_df, filter_config)

    st.title("Prestadores de Contratos")
    st.divider()
    
    with st.expander("Filtros de Contratos", expanded=True):
        show_filters(contratos_df, filter_config)
    
    mask = (
        contratos_df["situacao"].isin(st.session_state.contratos_situacao_selecionado) &
        contratos_df["contrato"].isin(st.session_state.contratos_contrato_selecionado) &
        contratos_df["estabelecimento"].isin(st.session_state.contratos_estabelecimento_selecionado) &
        contratos_df["classificacao"].isin(st.session_state.contratos_classificacao_selecionado)
    )
    
    if st.session_state.contratos_pedido_selecionado == ["Pedido"]:
        mask &= (contratos_df["numero"] == "PEDIDO")
    elif st.session_state.contratos_pedido_selecionado == ['Contrato']:
        mask &= (contratos_df["numero"] != "PEDIDO")

    contratos_filtrado = contratos_df[mask].drop(columns=["id", 'inicio'])
    
    st.dataframe(
        contratos_filtrado, hide_index=True, width='stretch',
        column_config={
            "situacao": st.column_config.TextColumn("Situação", width="small"),
            "numero": st.column_config.TextColumn("Número", width="small"),
            "contrato": st.column_config.TextColumn("Contrato", width="small"),
            "conta": st.column_config.TextColumn("Conta", width="small"),
            "centro_custo": st.column_config.TextColumn("Centro de Custo", width="small"),
            "estabelecimento": st.column_config.TextColumn("Estabelecimento", width="small"),
            "classificacao": st.column_config.TextColumn("Classificação", width="small"),
            "descricao": st.column_config.TextColumn("Descrição", width="small"),
            "cnpj": st.column_config.TextColumn("CNPJ", width="small"),
            "anexos": st.column_config.TextColumn("Anexos", width="small"),
            "valor_contrato": st.column_config.NumberColumn("Valor do Contrato", format='R$ %.2f'),
            "termino": st.column_config.DateColumn("Término", format="DD/MM/YY")                
        }
    )

    show_stats(contratos_filtrado, "valor_contrato", parcelas_df)
    st.divider()
    
    if "navegacao_acoes_contratos" not in st.session_state:
        st.session_state.navegacao_acoes_contratos = "Novo Contrato"

    opcoes_acao = ["Novo Contrato", "Editar Contrato", "Renovar Contrato", "Ativar/Desativar", 'Excluir Contrato']
    acao_selecionada = st.segmented_control(
        "Gerenciar Contratos:", options=opcoes_acao, 
        selection_mode="single", key="navegacao_acoes_contratos"
    )
    
    if not acao_selecionada: acao_selecionada = "Novo Contrato"
    st.write("---")

    acoes = {
        "Novo Contrato": new_contract,
        "Editar Contrato": edit_contract,
        "Renovar Contrato": renew_contract,
        "Ativar/Desativar": active_deactive_contract,
        "Excluir Contrato": delete_contract
    }
    
    if acao_selecionada in acoes:
        acoes[acao_selecionada](contratos_df)

if __name__ == "__main__":
    contratos()