import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

def clean(df):
    """
    Limpeza de DataFrame
    """
    df = df.dropna(how="all", axis=0)

    df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
    
    return df