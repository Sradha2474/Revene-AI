"""
Layer 2: Risk Predictor
========================
WHY THIS EXISTS:
Before a customer completes checkout, predict: "if this customer pays
with method X, at this bank, this amount, this time -- what's the
probability it succeeds?" This runs once per available method, so the
route recommender can compare them and pick the best one.

WHY XGBOOST + SHAP (not an LLM):
This is a structured, tabular, numeric-and-categorical prediction
problem with a clear right answer to learn from historical data --
exactly what gradient-boosted trees are built for. An LLM would be
slower, less accurate, and impossible to audit. SHAP gives you a
reason for every single prediction ("this transaction is risky mainly
because of past_failures_this_method and hour"), which is what lets
you show, not just claim, that the agent's decisions are explainable.

HOW ACCURACY IS VALIDATED:
Standard train/test split (80/20), report accuracy + ROC-AUC on the
held-out test set the model never saw during training. In a real
deployment, you'd retrain weekly on rolling live transaction data so
the model adapts as bank behaviour changes.

Run: python train_risk_predictor.py
Output: risk_model.json, encoders.pkl in this folder
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import pickle
import shap
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "transactions.csv")
df = pd.read_csv(DATA_PATH)

# Encode categoricals
encoders = {}
for col in ["method", "bank"]:
    le = LabelEncoder()
    df[col + "_enc"] = le.fit_transform(df[col])
    encoders[col] = le

FEATURES = ["method_enc", "bank_enc", "amount", "hour", "day_of_week", "past_failures_this_method"]
X = df[FEATURES]
y = df["success"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = xgb.XGBClassifier(
    n_estimators=150, max_depth=4, learning_rate=0.08,
    eval_metric="logloss", random_state=42
)
model.fit(X_train, y_train)

preds = model.predict(X_test)
probs = model.predict_proba(X_test)[:, 1]
acc = accuracy_score(y_test, preds)
auc = roc_auc_score(y_test, probs)

print(f"Test accuracy: {acc:.3f}")
print(f"Test ROC-AUC:  {auc:.3f}")

# SHAP explainer -- lets every prediction come with a "why"
explainer = shap.TreeExplainer(model)
sample_shap = explainer.shap_values(X_test.iloc[:5])
print("\nSample SHAP values (feature contributions) for first test row:")
for feat, val in zip(FEATURES, sample_shap[0]):
    print(f"  {feat}: {val:+.3f}")

model.save_model(os.path.join(BASE_DIR, "risk_model.json"))
with open(os.path.join(BASE_DIR, "encoders.pkl"), "wb") as f:
    pickle.dump({"encoders": encoders, "features": FEATURES}, f)

print("\nSaved risk_model.json and encoders.pkl")
