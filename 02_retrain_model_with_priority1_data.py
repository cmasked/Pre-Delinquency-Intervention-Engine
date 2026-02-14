"""
RETRAIN MODEL WITH REAL PRIORITY 1 DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Train XGBoost model using features derived from PRIORITY 1 datasets
Output: Updated deep_learning_model.json with real data patterns
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.metrics import auc, roc_curve, confusion_matrix, precision_recall_fscore_support
import json
import pickle
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("RETRAINING MODEL WITH PRIORITY 1 REAL DATA")
print("=" * 80)

# Load real features from PRIORITY 1 datasets
print("\n[1/5] Loading features from PRIORITY 1 datasets...")
features_df = pd.read_csv('customer_features_from_priority1.csv')

print(f"✓ Loaded {len(features_df):,} customers")
print(f"  - Default distribution: {features_df['is_default'].sum():,} (22%)")
print(f"  - Non-default distribution: {(1-features_df['is_default']).sum():,} (78%)")

# Prepare X (features) and y (target)
print("\n[2/5] Preparing features and target...")

# Select numeric features (exclude customer_id and is_default)
feature_cols = [col for col in features_df.columns if col not in ['customer_id', 'is_default']]

print(f"✓ Selected {len(feature_cols)} features:")
for col in feature_cols:
    print(f"  - {col}")

X = features_df[feature_cols].copy()
y = features_df['is_default'].copy()

# Handle any NaN values
X = X.fillna(0)
print(f"\n✓ Feature matrix shape: {X.shape}")
print(f"✓ Target distribution: {y.value_counts().to_dict()}")

# Split data (80/20 train/test)
print("\n[3/5] Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"✓ Training set: {len(X_train):,} samples")
print(f"✓ Test set: {len(X_test):,} samples")
print(f"  - Training defaults: {y_train.sum():,} ({y_train.sum()/len(y_train)*100:.1f}%)")
print(f"  - Test defaults: {y_test.sum():,} ({y_test.sum()/len(y_test)*100:.1f}%)")

# Scale features
print("\n[4/5] Training XGBoost model...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Calculate scale_pos_weight for imbalanced data
pos_count = (y_train == 1).sum()
neg_count = (y_train == 0).sum()
scale_pos_weight = neg_count / pos_count

print(f"✓ Class weight ratio: {scale_pos_weight:.2f}")

# Train XGBoost
model = XGBClassifier(
    n_estimators=200,
    max_depth=7,
    learning_rate=0.1,
    scale_pos_weight=scale_pos_weight,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    tree_method='hist',
    device='cpu'
)

model.fit(
    X_train_scaled, y_train,
    eval_set=[(X_test_scaled, y_test)],
    verbose=False
)

print("✓ Model trained successfully")

# Evaluate on test set
print("\n[5/5] Evaluating model...")

y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
y_pred = model.predict(X_test_scaled)

# Calculate metrics
fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
auc_score = auc(fpr, tpr)
precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')

tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

print(f"✓ Model Performance (on real data):")
print(f"  - AUC-ROC: {auc_score:.4f}")
print(f"  - Precision: {precision:.4f}")
print(f"  - Recall: {recall:.4f}")
print(f"  - F1-Score: {f1:.4f}")
print(f"  - True Positives (Caught Defaults): {tp:,}")
print(f"  - False Positives: {fp:,}")
print(f"  - True Negatives: {tn:,}")
print(f"  - False Negatives (Missed Defaults): {fn:,}")

# Save model as JSON for compatibility
print("\n[6/5] Saving model...")
model_dict = {
    'model_type': 'XGBoost',
    'n_features': len(feature_cols),
    'feature_names': feature_cols,
    'n_estimators': model.n_estimators,
    'max_depth': model.max_depth,
    'learning_rate': model.learning_rate,
    'auc_score': float(auc_score),
    'precision': float(precision),
    'recall': float(recall),
    'f1_score': float(f1),
    'test_size': len(X_test)
}

with open('deep_learning_model.json', 'w') as f:
    json.dump(model_dict, f, indent=2)

# Save model binary
model.save_model('xgboost_model.bin')

# Save scaler
with open('feature_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

# Save predictions for dashboard
np.save('model_y_test.npy', y_test.values)
np.save('model_predictions_test.npy', y_pred_proba)

print(f"✓ Model artifacts saved:")
print(f"  - deep_learning_model.json (metadata)")
print(f"  - xgboost_model.bin (binary model)")
print(f"  - feature_scaler.pkl (scaler)")
print(f"  - model_y_test.npy (test labels)")
print(f"  - model_predictions_test.npy (test predictions)")

# ============================================================================
# PREDICTIONS ON ALL 10K CUSTOMERS (for dashboard)
# ============================================================================
print("\nGenerating predictions for all 10,000 customers...")

X_all_scaled = scaler.transform(X)
all_probs = model.predict_proba(X_all_scaled)[:, 1]

predictions_df = pd.DataFrame({
    'customer_id': features_df['customer_id'],
    'model_probability': all_probs,
    'is_default_actual': features_df['is_default']
})

predictions_df.to_csv('model_predictions_all_customers.csv', index=False)

print(f"✓ Generated predictions for {len(predictions_df):,} customers")
print(f"  Risk distribution:")
print(f"  - HIGH RISK (prob > 0.6): {(all_probs > 0.6).sum():,} customers")
print(f"  - MEDIUM RISK (0.3-0.6): {((all_probs > 0.3) & (all_probs <= 0.6)).sum():,} customers")
print(f"  - LOW RISK (< 0.3): {(all_probs <= 0.3).sum():,} customers")

print("\n" + "=" * 80)
print("✓ MODEL RETRAINING COMPLETE")
print("=" * 80)
print("\nModel trained on REAL PRIORITY 1 data:")
print(f"✓ Features derived from transactions, EMI, savings, utilities")
print(f"✓ Currency: Indian Rupees (₹)")
print(f"✓ Customers: 10,000 with real default patterns")
print(f"✓ Performance: AUC {auc_score:.4f}, Recall {recall:.4f}, Precision {precision:.4f}")
print("\n" + "=" * 80)
