"""
QUICK MODEL TESTING SCRIPT
=========================

Run this to test your model and see all metrics:
    python 06_quick_test.py
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, recall_score, precision_score, f1_score, confusion_matrix

# Load data
df = pd.read_csv('synthetic_customer_features_FIXED.csv')

print('='*70)
print('MODEL TESTING EXAMPLE - STEP BY STEP')
print('='*70)

print(f'\n[1] DATA LOADED')
print(f'    Total customers: {len(df):,}')
print(f'    Defaults: {df["is_default"].sum():,} ({df["is_default"].mean():.1%})')

# Features & target
features = [col for col in df.columns if col not in ['customer_id', 'is_default']]
X, y = df[features], df['is_default']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f'\n[2] DATA SPLIT')
print(f'    Train: {len(X_train):,} | Test: {len(X_test):,}')

# Train model
print(f'\n[3] TRAINING MODEL...')
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
model.fit(X_train_scaled, y_train)
y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

print(f'    Model: RandomForestClassifier')
print(f'    Predictions generated: {len(y_pred_proba):,}')

# Metrics at threshold 0.5
y_pred = (y_pred_proba >= 0.5).astype(int)
tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

print(f'\n[4] EVALUATION AT THRESHOLD 0.5')
print(f'    AUC-ROC:    {roc_auc_score(y_test, y_pred_proba):.4f}')
print(f'    Recall:     {recall_score(y_test, y_pred):.4f}   (catch % of defaults)')
print(f'    Precision:  {precision_score(y_test, y_pred):.4f}   (of flagged, % actually default)')
print(f'    F1-Score:   {f1_score(y_test, y_pred):.4f}')

print(f'\n[5] CONFUSION MATRIX AT 0.5')
print(f'    True Negatives:  {tn:,}  (correct non-default)')
print(f'    False Positives: {fp:,}  (flagged but won\'t default)')
print(f'    False Negatives: {fn:,}  (MISS - will default)')
print(f'    True Positives:  {tp:,}  (correct default catch)')

# Business metrics
intervention_cost = 500
loss_per_default = 5000
prevented = tp * loss_per_default
cost = (tp + fp) * intervention_cost
missed = fn * loss_per_default
net_benefit = prevented - cost - missed

print(f'\n[6] BUSINESS IMPACT AT 0.5')
print(f'    Preventing defaults: ${prevented:,.0f}')
print(f'    Intervention cost:   ${cost:,.0f}')
print(f'    Missed defaults:     ${missed:,.0f}')
print(f'    NET BENEFIT:         ${net_benefit:,.0f}')

# Find optimal threshold
print(f'\n[7] TESTING DIFFERENT THRESHOLDS')
print(f'    {"Threshold":<12} {"Recall":<10} {"Precision":<12} {"F1":<8} {"Flagged":<10} {"Net Benefit":<15}')
print(f'    {"-"*67}')
for threshold in [0.3, 0.4, 0.5, 0.6, 0.7]:
    pred = (y_pred_proba >= threshold).astype(int)
    rec = recall_score(y_test, pred)
    prec = precision_score(y_test, pred, zero_division=0)
    f1_val = f1_score(y_test, pred, zero_division=0)
    
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    net = (tp * loss_per_default) - ((tp + fp) * intervention_cost) - (fn * loss_per_default)
    
    print(f'    {threshold:<12.1f} {rec:<10.1%} {prec:<12.1%} {f1_val:<8.4f} {tp+fp:<10,} ${net:>14,.0f}')

print(f'\n    NOTE: Different thresholds give different results!')
print(f'          - Threshold 0.3: Catch MORE defaults (high recall)')
print(f'          - Threshold 0.7: Fewer false alarms (high precision)')
print(f'          Choose based on business priority')

print(f'\n[8] TOP FEATURES PREDICTING DEFAULTS')
features_imp = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in features_imp.head(5).iterrows():
    print(f'    {row["feature"]:<30s}: {row["importance"]:7.4f}')

print('\n' + '='*70)
print('SUCCESS: Model tested and all metrics shown above')
print('='*70)
