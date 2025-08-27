import pandas as pd
from utils import clean
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "raw" / "CONTRATOS 2024-2025.CSV"
df = pd.read_csv(DATA_PATH, encoding="latin-1", sep=";")
clean(df)

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