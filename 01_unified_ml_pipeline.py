"""
UNIFIED ML PIPELINE
===================

This combines:
1. Data loading
2. Feature engineering
3. Stress Index calculation
4. XGBoost model training
5. Decision Engine
6. Predictions for all customers

Output: All data ready for Streamlit
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, recall_score, precision_score, f1_score, confusion_matrix
import xgboost as xgb
import pickle
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("UNIFIED ML PIPELINE")
print("="*80)

# ============================================================================
# [1] LOAD DATA
# ============================================================================
print("\n[1] Loading realistic customer data...")

df = pd.read_csv('realistic_customer_features.csv')

print(f"✓ Loaded {len(df):,} customers")
print(f"\nRisk Distribution:")
low_count = (df['stress_score'] < 35).sum()
med_count = ((df['stress_score'] >= 35) & (df['stress_score'] < 65)).sum()
high_count = ((df['stress_score'] >= 65) & (df['stress_score'] < 85)).sum()
crit_count = (df['stress_score'] >= 85).sum()

print(f"  LOW RISK: {low_count:,} ({low_count/len(df)*100:.0f}%)")
print(f"  MEDIUM RISK: {med_count:,} ({med_count/len(df)*100:.0f}%)")
print(f"  HIGH RISK: {high_count:,} ({high_count/len(df)*100:.0f}%)")
print(f"  CRITICAL RISK: {crit_count:,} ({crit_count/len(df)*100:.0f}%)")

# ============================================================================
# [2] PREPARE FEATURES
# ============================================================================
print("\n[2] Preparing features...")

features_to_use = [col for col in df.columns 
                   if col not in ['customer_id', 'is_default', 'stress_score']]

X = df[features_to_use].values
y = df['is_default'].values

print(f"✓ Features: {len(features_to_use)}")
print(f"✓ Target: is_default (default rate: {y.mean():.1%})")

# ============================================================================
# [3] SPLIT & SCALE
# ============================================================================
print("\n[3] Splitting data (80/20)...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"✓ Train: {len(X_train):,} | Test: {len(X_test):,}")

# ============================================================================
# [4] TRAIN XGBOOST
# ============================================================================
print("\n[4] Training XGBoost model...")

scale_pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()

model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=7,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
    scale_pos_weight=scale_pos_weight
)

model.fit(X_train_scaled, y_train, verbose=False)

print("✓ Model trained")

# ============================================================================
# [5] EVALUATE
# ============================================================================
print("\n[5] Model Evaluation...")

y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
y_pred = (y_pred_proba >= 0.5).astype(int)

auc = roc_auc_score(y_test, y_pred_proba)
recall = recall_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"AUC: {auc:.4f} | Recall: {recall:.4f} | Precision: {precision:.4f} | F1: {f1:.4f}")

# ============================================================================
# [6] PREDICT ON ALL CUSTOMERS
# ============================================================================
print("\n[6] Generating predictions for all customers...")

X_all_scaled = scaler.transform(X)
y_pred_proba_all = model.predict_proba(X_all_scaled)[:, 1]

# Create decisions dataframe
# Rank all customers by probability, then assign risk levels by percentile
ranked_indices = np.argsort(y_pred_proba_all)[::-1]  # Sort descending
n_total = len(y_pred_proba_all)
n_crit = int(n_total * 0.05)    # Top 5%
n_high = int(n_total * 0.10)    # Next 10%
n_med = int(n_total * 0.15)     # Next 15%
# Rest are LOW (70%)

risk_assignments = np.full(n_total, 'LOW', dtype=object)
risk_assignments[ranked_indices[:n_crit]] = 'CRITICAL'
risk_assignments[ranked_indices[n_crit:n_crit+n_high]] = 'HIGH'
risk_assignments[ranked_indices[n_crit+n_high:n_crit+n_high+n_med]] = 'MEDIUM'

decisions = []

for i, (cust_id, stress, default_prob, risk_level) in enumerate(zip(df['customer_id'], df['stress_score'], y_pred_proba_all, risk_assignments)):
    
    # Set action based on risk level
    if risk_level == 'CRITICAL':
        action = 'PAYMENT_HOLIDAY'
        urgency = 'IMMEDIATE'
        contact_method = 'PHONE_CALL'
    elif risk_level == 'HIGH':
        action = 'LOAN_RESTRUCTURE'
        urgency = '24_HOURS'
        contact_method = 'PHONE_CALL + SMS'
    elif risk_level == 'MEDIUM':
        action = 'PROACTIVE_OUTREACH'
        urgency = '72_HOURS'
        contact_method = 'SMS + EMAIL'
    else:  # LOW
        action = 'STANDARD_MONITORING'
        urgency = 'ROUTINE'
        contact_method = 'EMAIL'
    
    decisions.append({
        'customer_id': cust_id,
        'stress_score': stress,
        'default_probability': default_prob,
        'risk_level': risk_level,
        'recommended_action': action,
        'urgency': urgency,
        'contact_method': contact_method,
        'last_updated': '2026-02-14'
    })

df_decisions = pd.DataFrame(decisions)
df_decisions.to_csv('unified_customer_decisions.csv', index=False)

print(f"✓ {len(df_decisions):,} decision records created")
print(f"\nDecision Distribution:")
print(f"  CRITICAL: {(df_decisions['risk_level'] == 'CRITICAL').sum():,} ({(df_decisions['risk_level'] == 'CRITICAL').mean()*100:.1f}%)")
print(f"  HIGH: {(df_decisions['risk_level'] == 'HIGH').sum():,} ({(df_decisions['risk_level'] == 'HIGH').mean()*100:.1f}%)")
print(f"  MEDIUM: {(df_decisions['risk_level'] == 'MEDIUM').sum():,} ({(df_decisions['risk_level'] == 'MEDIUM').mean()*100:.1f}%)")
print(f"  LOW: {(df_decisions['risk_level'] == 'LOW').sum():,} ({(df_decisions['risk_level'] == 'LOW').mean()*100:.1f}%)")

# ============================================================================
# [7] SAVE MODEL & SCALER
# ============================================================================
print("\n[7] Saving models...")

model.save_model('xgboost_model.bin')
with open('feature_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("✓ Model saved: xgboost_model.bin")
print("✓ Scaler saved: feature_scaler.pkl")

print("\n" + "="*80)
print("✓ PIPELINE COMPLETE - READY FOR STREAMLIT")
print("="*80)
print(f"\nOutputs:")
print(f"  1. realistic_customer_features.csv - Customer data (10,000 rows)")
print(f"  2. unified_customer_decisions.csv - Risk & decisions (ready for dashboard)")
print(f"  3. xgboost_model.bin - Trained model")
print(f"  4. feature_scaler.pkl - Feature scaler")
print(f"\nNext step: streamlit run streamlit_app_proper.py")
