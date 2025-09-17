import pandas as pd

mes_dict = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4,
    "mai": 5, "jun": 6, "jul": 7, "ago": 8,
    "set": 9, "out": 10, "nov": 11, "dez": 12
}

now = pd.Timestamp.now()
mes_atual = [k for k, v in mes_dict.items() if v == now.month][0]
ano_atual = now.year
data_lanc = now.strftime("%d/%m/%y %H:%M")