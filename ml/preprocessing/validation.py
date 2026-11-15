import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


def check_missing(df: pd.DataFrame) -> Dict[str, float]:
    """Return percentage of missing values per column."""
    return (df.isnull().sum() / len(df) * 100).to_dict()


def check_class_balance(y: pd.Series) -> Dict:
    counts = y.value_counts()
    total = len(y)
    return {
        "counts": counts.to_dict(),
        "ratios": (counts / total).round(4).to_dict(),
        "is_imbalanced": bool((counts.min() / counts.max()) < 0.2),
    }


def validate_feature_columns(df: pd.DataFrame, required_cols: List[str]) -> Tuple[bool, List[str]]:
    missing = [c for c in required_cols if c not in df.columns]
    return len(missing) == 0, missing


def validate_no_inf(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].replace([np.inf, -np.inf], np.nan)
    df[num_cols] = df[num_cols].fillna(0)
    return df


def validate_target_binary(y: pd.Series, name: str = "target") -> bool:
    unique = set(y.unique())
    if not unique.issubset({0, 1}):
        raise ValueError(f"Target '{name}' must be binary (0/1). Found: {unique}")
    return True


def generate_data_report(df: pd.DataFrame, name: str = "dataset") -> Dict:
    return {
        "name": name,
        "rows": len(df),
        "columns": len(df.columns),
        "missing_pct": check_missing(df),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "numeric_stats": df.describe().to_dict(),
    }
