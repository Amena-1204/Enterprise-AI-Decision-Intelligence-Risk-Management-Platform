import pandas as pd
import numpy as np
from datetime import datetime
from typing import List


# ── Churn features ────────────────────────────────────────────────────────────

def build_churn_features(customers: pd.DataFrame, transactions: pd.DataFrame,
                          tickets: pd.DataFrame, reference_date: datetime = None) -> pd.DataFrame:
    if reference_date is None:
        reference_date = datetime.utcnow()

    # Transaction aggregates per customer
    txn = transactions[transactions["status"] == "completed"].copy()
    txn["transaction_date"] = pd.to_datetime(txn["transaction_date"])

    txn_agg = txn.groupby("customer_id").agg(
        total_transactions=("id", "count"),
        total_spent=("amount", "sum"),
        avg_order_value=("amount", "mean"),
        last_purchase_date=("transaction_date", "max"),
    ).reset_index()

    txn_agg["days_since_last_purchase"] = (
        reference_date - txn_agg["last_purchase_date"]
    ).dt.days

    # Support ticket count per customer
    ticket_agg = tickets.groupby("customer_id").agg(
        support_tickets=("id", "count"),
        open_tickets=("id", lambda x: (tickets.loc[x.index, "status"] == "open").sum()),
    ).reset_index()

    # Merge
    df = customers.merge(txn_agg, left_on="id", right_on="customer_id", how="left")
    df = df.merge(ticket_agg, left_on="id", right_on="customer_id", how="left")

    # Fill missing values
    df["total_transactions"] = df["total_transactions"].fillna(0)
    df["total_spent"] = df["total_spent"].fillna(0)
    df["avg_order_value"] = df["avg_order_value"].fillna(0)
    df["days_since_last_purchase"] = df["days_since_last_purchase"].fillna(365)
    df["support_tickets"] = df["support_tickets"].fillna(0)
    df["open_tickets"] = df["open_tickets"].fillna(0)

    # Derived features
    df["purchase_frequency"] = df["total_transactions"] / (df["account_age_days"].clip(lower=1) / 30)
    df["avg_monthly_spend"] = df["total_spent"] / (df["account_age_days"].clip(lower=1) / 30)
    df["is_high_ticket"] = (df["support_tickets"] >= 3).astype(int)
    df["is_inactive_90d"] = (df["days_since_last_purchase"] > 90).astype(int)

    return df


CHURN_FEATURE_COLS: List[str] = [
    "account_age_days",
    "total_transactions",
    "total_spent",
    "avg_order_value",
    "days_since_last_purchase",
    "support_tickets",
    "open_tickets",
    "purchase_frequency",
    "avg_monthly_spend",
    "is_high_ticket",
    "is_inactive_90d",
]


# ── Fraud features ────────────────────────────────────────────────────────────

def build_fraud_features(transactions: pd.DataFrame) -> pd.DataFrame:
    df = transactions.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["hour_of_day"] = df["transaction_date"].dt.hour
    df["day_of_week"] = df["transaction_date"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_night"] = ((df["hour_of_day"] < 6) | (df["hour_of_day"] > 22)).astype(int)

    # Customer average amount
    customer_avg = df.groupby("customer_id")["amount"].transform("mean")
    df["amount_vs_avg_ratio"] = df["amount"] / (customer_avg + 1e-9)
    df["is_high_amount"] = (df["amount_vs_avg_ratio"] > 3).astype(int)

    # Encode payment method
    payment_risk = {
        "credit_card": 1, "debit_card": 1, "paypal": 2,
        "bank_transfer": 1, "crypto": 4, "cash": 3,
    }
    df["payment_risk_score"] = df["payment_method"].map(payment_risk).fillna(2)

    # Device risk
    df["is_unknown_device"] = (df["device_type"] == "unknown").astype(int)

    return df


FRAUD_FEATURE_COLS: List[str] = [
    "amount",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "is_night",
    "amount_vs_avg_ratio",
    "is_high_amount",
    "payment_risk_score",
    "is_unknown_device",
]


# ── Sales features ────────────────────────────────────────────────────────────

def build_sales_features(sales: pd.DataFrame) -> pd.DataFrame:
    df = sales.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df = df.sort_values("sale_date")

    df["month"] = df["sale_date"].dt.month
    df["day_of_week"] = df["sale_date"].dt.dayofweek
    df["week_of_year"] = df["sale_date"].dt.isocalendar().week.astype(int)
    df["quarter"] = df["sale_date"].dt.quarter

    # Lag features (grouped by region if available)
    df["lag_7"] = df["revenue"].shift(7).fillna(0)
    df["lag_14"] = df["revenue"].shift(14).fillna(0)
    df["lag_30"] = df["revenue"].shift(30).fillna(0)
    df["rolling_mean_7"] = df["revenue"].rolling(7, min_periods=1).mean()
    df["rolling_mean_30"] = df["revenue"].rolling(30, min_periods=1).mean()
    df["rolling_std_7"] = df["revenue"].rolling(7, min_periods=1).std().fillna(0)

    return df


SALES_FEATURE_COLS: List[str] = [
    "month",
    "day_of_week",
    "week_of_year",
    "quarter",
    "lag_7",
    "lag_14",
    "lag_30",
    "rolling_mean_7",
    "rolling_mean_30",
    "rolling_std_7",
]
