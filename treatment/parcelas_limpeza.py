import pandas as pd
from utils.clean import clean
from pathlib import Path

script_dir = Path(__file__).resolve().parent.parent
path_csv = script_dir / "data" / "raw" / 'parcelas_raw.csv'

df = pd.read_csv(path_csv, encoding="utf-8", sep=";", skiprows=1)
df = clean(df)

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
cat_cols = ["Situação", "Status", "Estab", "CNPJ", "Classificação", 
            "Referente", "Parcela", "Contrato", "Tipo","Mês"]
df[cat_cols] = df[cat_cols].astype('category')

colunas = ["Ano", 'Mês', 'Dt.Lanç', 'Emissão', 'Venc', 'Tipo', 'Contrato', 'Referente', 'Doc', 'Estab', 'Status', 'Valor R$']
df = df[colunas]

save_path = script_dir / 'data' / 'processed' / 'parcelas.csv'
df.to_csv(save_path, index=False, encoding="utf-8")