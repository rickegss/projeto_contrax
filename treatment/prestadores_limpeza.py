# streamlit run "C:\Users\ricardo.gomes\Desktop\Python VS\projeto_contratos\treatment\prestadores_limpeza.py"
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# adiciona a pasta raiz do projeto no path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "raw" / "prestadores_raw.csv"
df = pd.read_csv(DATA_PATH, encoding="utf-8", sep=";")

from utils.clean import clean, remove_unnamed
clean(df)
remove_unnamed(df)
df = df.iloc[1:].reset_index(drop=True)

colunas = ["Situação", "Prestador", "Nr", "Conta", "CC", "Estab", "Classificacao", "CNPJ Prestador", " Valor do Contrato R$ ", "Início", "Término", "Renovação", "Duração"]
df = df[colunas]
df = df.drop_duplicates()
df["Qtd Notas"] = 1

df[["Situação", "Classificacao", "Prestador", "Conta", "CC", "Estab"]] = df[["Situação", "Classificacao", "Prestador", "Conta", "CC", "Estab"]].astype("category")
df[" Valor do Contrato R$ "] = df[" Valor do Contrato R$ "].str.replace(".", "").str.replace(",", ".").astype(float)
for col in ["Início", "Término", "Renovação"]:
    df[col] = pd.to_datetime(df[col], format='%d/%m/%y', errors='coerce')
df['Duração'] = pd.to_numeric(df['Duração'], errors='coerce')
df["Duração"] = pd.to_timedelta(df["Duração"], unit="D")
df["Duração"] = df["Duração"] * 30
df["Qtd Notas"] = pd.to_numeric(df['Qtd Notas'])
st.write(df)
print(df.dtypes)

save_path = BASE_DIR / "data" / "processed" / "prestadores.csv"
df.to_csv(save_path, index=False, encoding="utf-8")