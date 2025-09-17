def clean(df):
    """
    Limpeza de DataFrame
    """
    df = df.iloc[:, 1:] 
    df = df.dropna(how="all", axis=0)

    df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
    
    return df