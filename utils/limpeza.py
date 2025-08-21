import pandas as pd
# limpando colunas e linhas vazias
df = pd.read_csv(r"C:\Users\ricardo.gomes\Desktop\Python VS\projeto_contratos\data\CONTRATOS 2024-2025.CSV", encoding="latin-1", sep=";")
df = df.drop('Unnamed: 0', axis=1)
df = df.dropna(how="all", axis=0)
df.columns = df.iloc[0]
df = df[1:].reset_index(drop=True)
df.columns = df.columns.str.replace(r'^\s+|\s+$', '', regex=True).str.strip()

# colunas de data
date_cols = ["Dt.Lanç", "Emissão", "Venc"]
for col in date_cols:
    df[col] = pd.to_datetime(df[col], format='%d/%m/%y', errors='coerce')

df['Ano'] = df["Emissão"].dt.year.fillna(0).astype(int)

# coluna monetaria
df["Valor R$"] = (
    df["Valor R$"]\
    .str.replace('.', '', regex=False)\
    .str.replace(',', '.', regex=False)
)

df["Valor R$"] = pd.to_numeric(df["Valor R$"], errors='coerce')  

# colunas de categoria
cat_cols = ["Situação", "Status", "Categoria", "Estab", "CNPJ", "Classificação", 
            "Descrição", "Parcela", "Contrato", "Tipo","Mês"]
df[cat_cols] = df[cat_cols].astype('category')


df.to_csv("contratos.csv", index=False, encoding="utf-8")