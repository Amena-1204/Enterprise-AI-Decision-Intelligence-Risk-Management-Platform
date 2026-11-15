import pandas as pd
import numpy as np
from typing import Tuple


def load_raw_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    print(f"Dropped {before - len(df)} duplicate rows")
    return df


def fill_numeric_nulls(df: pd.DataFrame, strategy: str = "median") -> pd.DataFrame:
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if df[col].isnull().any():
            fill_val = df[col].median() if strategy == "median" else df[col].mean()
            df[col] = df[col].fillna(fill_val)
    return df


def fill_categorical_nulls(df: pd.DataFrame, fill_value: str = "unknown") -> pd.DataFrame:
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    for col in cat_cols:
        df[col] = df[col].fillna(fill_value)
    return df


def remove_outliers_iqr(df: pd.DataFrame, column: str, factor: float = 3.0) -> pd.DataFrame:
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - factor * IQR
    upper = Q3 + factor * IQR
    before = len(df)
    df = df[(df[column] >= lower) & (df[column] <= upper)]
    print(f"Removed {before - len(df)} outliers from '{column}'")
    return df


def clean_customer_data(df: pd.DataFrame) -> pd.DataFrame:
    df = drop_duplicates(df)
    df = fill_numeric_nulls(df)
    df = fill_categorical_nulls(df)
    if "lifetime_value" in df.columns:
        df = remove_outliers_iqr(df, "lifetime_value")
    if "email" in df.columns:
        df["email"] = df["email"].str.lower().str.strip()
    return df


def clean_transaction_data(df: pd.DataFrame) -> pd.DataFrame:
    df = drop_duplicates(df)
    df = fill_numeric_nulls(df)
    df = fill_categorical_nulls(df)
    if "amount" in df.columns:
        df = df[df["amount"] > 0]
    if "transaction_date" in df.columns:
        df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
        df = df.dropna(subset=["transaction_date"])
    return df
