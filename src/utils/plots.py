import plotly.express as px
import pandas as pd
from datetime import datetime
from src.utils.formatters import formatar_brl

def plot_despesa_mensal(df):
    df_agrupado = df.groupby(['mes', 'mes_nome'], observed=True)['valor'].sum().reset_index()
    df_agrupado = df_agrupado.sort_values('mes')
    df_agrupado['TextoValor'] = df_agrupado['valor'].apply(formatar_brl)
    fig = px.bar(df_agrupado, x='mes_nome', y='valor', title='Despesas Mensais', labels={"mes_nome": "Mês", "valor": "Total R$"}, text='TextoValor')
    fig.update_traces(textposition='outside', textangle=0)
    return fig

def plot_total_estabelecimento_bar(df):
    df_agrupado = df.groupby('estabelecimento', observed=True)['valor'].sum().reset_index().sort_values('valor')
    df_agrupado['TextoValor'] = df_agrupado['valor'].apply(formatar_brl)
    fig = px.bar(df_agrupado, x='valor', y='estabelecimento', orientation='h', title='Total por Estabelecimento', labels={"estabelecimento": "Estabelecimento", "valor": "Total R$"}, text='TextoValor', color="estabelecimento", color_discrete_sequence=px.colors.sequential.Viridis)
    return fig

def plot_classificacao(df):
    df_agrupado = df.groupby('classificacao', observed=True)['valor'].sum().reset_index()
    df_agrupado['TextoValor'] = df_agrupado['valor'].apply(formatar_brl)
    fig = px.bar(df_agrupado, x='classificacao', y='valor', title='Despesas por Classificação', labels={"classificacao": "Classificação", "valor": "Total R$"}, text='TextoValor')
    fig.update_traces(textposition='outside', textangle=0)
    return fig

def plot_top_prestadores(df):
    df_agrupado = df.groupby('contrato', observed=True)['valor'].sum().nlargest(10).sort_values().reset_index()
    df_agrupado['TextoValor'] = df_agrupado['valor'].apply(formatar_brl)
    fig = px.bar(df_agrupado, x='valor', y='contrato', orientation='h', title='Top 10 Prestadores', labels={"contrato": "Prestador", "valor": "Total R$"}, text='TextoValor')
    return fig

def plot_faturamento_hcompany(df, dash_ano_selecionado):
    from src.utils.stamp import mes_dict

    df_hcompany = df[
        (df['contrato'].str.startswith("HCOMPANY")) &
        (df['ano'].isin(dash_ano_selecionado)) &
        (df['status'] == 'LANÇADO')
    ]

    df_agrupado = df_hcompany.groupby(['mes', 'mes_nome'], observed=True)['valor'].sum().reset_index()

    meses_completos = pd.DataFrame({
        'mes_nome': list(mes_dict.keys()),
        'mes': list(mes_dict.values())
    })

    df_completo = meses_completos.merge(df_agrupado, on=['mes', 'mes_nome'], how='left')
    df_completo['valor'] = df_completo['valor'].fillna(0)
    
    df_completo = df_completo.sort_values('mes')

    
    fig = px.line(
        df_completo, 
        x='mes_nome', 
        y='valor', 
        title='Faturamento HCOMPANY', 
        labels={'mes_nome': 'Mês', 'valor': 'Total R$'}, 
        markers=True
    )
    return fig

def plot_gantt_contratos(contratos_df):
    contratos = contratos_df.copy()
    contratos["inicio"] = pd.to_datetime(contratos["inicio"])
    contratos["termino"] = pd.to_datetime(contratos["termino"])

    df_gantt = contratos.dropna(subset=["inicio", "termino"])
    
    fig = px.timeline(
        df_gantt, 
        x_start="inicio", 
        x_end="termino", 
        y="contrato",   
        color_discrete_sequence=px.colors.sequential.Viridis[2:],
        title="Cronograma de Vigência de Contratos",
        height=1400,
        width=1900
    )
    hoje = datetime.now()
    fig.add_vline(
        x=hoje,
        line_width=2,
        line_dash="dash",
        line_color="cyan"
    )
    fig.add_annotation(
        x=hoje,
        y=1.03,
        yref="paper",
        text="Hoje",
        showarrow=False,
        font=dict(color="cyan"),
        align="center"
    )

    fig.update_yaxes(autorange="reversed")
    return fig