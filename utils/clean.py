def clean(df):
    """
    Limpa colunas e linhas vazias, remove espaços
    """

    df = df.drop('Unnamed: 0', axis=1)
    df = df.dropna(how="all", axis=0)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    df.columns = df.columns.str.replace(r' ^\s+|\s+$', '', regex=True).str.strip()

def remove_unnamed(df):
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.reset_index(drop=True)