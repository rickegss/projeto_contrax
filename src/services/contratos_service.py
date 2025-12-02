import time
import pandas as pd
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.stamp import ano_atual
from utils.formatters import formatar_brl

def new_contract(df, supabase) -> None:
    ccol1, = st.columns(1)

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


def delete_contract(df, supabase) -> None: 
    ccol2, = st.columns(1)
    
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


def active_deactive_contract(df, supabase) -> None:
    coll3, = st.columns(1)
    
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


def edit_contract(df, supabase) -> None:
    coll4, = st.columns(1)
    
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


def renew_contract(df, supabase) -> None:
    coll5, = st.columns(1)
    
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