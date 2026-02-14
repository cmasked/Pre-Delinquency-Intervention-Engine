"""
Rebuild and save model using Pickle (reliable format)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
import pickle
import json

print("=" * 80)
print("REBUILDING MODEL WITH PICKLE FORMAT")
print("=" * 80)

# Load data
print("\n[1/4] Loading data...")
df_features = pd.read_csv('customer_features_from_priority1.csv')

X = df_features.drop(['customer_id', 'is_default'], axis=1)
y = df_features['is_default']

print(f"✓ Features shape: {X.shape}")
print(f"✓ Default rate: {y.mean():.1%}")

# Split and scale
print("\n[2/4] Preparing data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
print("\n[3/4] Training XGBoost...")
model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=7,
    learning_rate=0.1,
    random_state=42,
    eval_metric='logloss',
    use_label_encoder=False
)

model.fit(
    X_train_scaled, y_train,
    eval_set=[(X_test_scaled, y_test)],
    verbose=False
)

# Evaluate
print("\n[4/4] Evaluating model...")
y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
y_pred = model.predict(X_test_scaled)

auc = roc_auc_score(y_test, y_pred_proba)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"✓ AUC-ROC: {auc:.4f}")
print(f"✓ Precision: {precision:.4f}")
print(f"✓ Recall: {recall:.4f}")
print(f"✓ F1-Score: {f1:.4f}")

# Save model and scaler as PICKLE (not XGBoost binary)
print("\nSaving artifacts...")

# Save model as pickle
with open('xgboost_model.pkl', 'wb') as f:
    pickle.dump(model, f)
print("✓ Model saved: xgboost_model.pkl")

# Save scaler
with open('feature_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
print("✓ Scaler saved: feature_scaler.pkl")

# Save metadata
metadata = {
    "model_type": "XGBoost",
    "model_file": "xgboost_model.pkl",
    "n_features": X.shape[1],
    "feature_names": X.columns.tolist(),
    "n_estimators": 200,
    "max_depth": 7,
    "learning_rate": 0.1,
    "auc_score": float(auc),
    "precision": float(precision),
    "recall": float(recall),
    "f1_score": float(f1),
    "test_size": len(X_test)
}

with open('deep_learning_model.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("✓ Metadata saved: deep_learning_model.json")

print("\n" + "=" * 80)
print("✓ MODEL REBUILD COMPLETE - READY FOR DASHBOARD")
print("=" * 80)
