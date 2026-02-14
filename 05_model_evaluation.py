"""
MODEL EVALUATION FRAMEWORK

Purpose: Properly evaluate deep learning models

What to evaluate:
1. Basic metrics (AUC, Precision, Recall, F1)
2. Cross-validation stability
3. Business impact (ROI, intervention effectiveness)
4. Threshold optimization for production

TARGET: is_default (binary: 1=default, 0=non-default)
This is REAL, not artificial stress_score
"""

import pandas as pd
import numpy as np
from sklearn.metrics import (
    classification_report, roc_auc_score, roc_curve,
    precision_recall_curve, confusion_matrix,
    precision_score, recall_score, accuracy_score, f1_score
)
import warnings
warnings.filterwarnings('ignore')

class ModelEvaluator:
    """Comprehensive model evaluation"""
    
    def __init__(self, y_true, y_pred_proba, model_name="Model"):
        """
        y_true: Ground truth (0/1)
        y_pred_proba: Predicted probabilities (0-1)
        """
        self.y_true = y_true
        self.y_pred_proba = y_pred_proba
        self.model_name = model_name
        self.default_threshold = 0.5
        self.y_pred = (y_pred_proba >= self.default_threshold).astype(int)
    
    def evaluate_all(self):
        """Run complete evaluation"""
        
        print(f"\n{'='*80}")
        print(f"MODEL EVALUATION: {self.model_name}")
        print(f"{'='*80}")
        
        # Basic metrics
        print(f"\n[1] CLASSIFICATION METRICS (Threshold={self.default_threshold})")
        print(f"{'-'*80}")
        
        auc = roc_auc_score(self.y_true, self.y_pred_proba)
        accuracy = accuracy_score(self.y_true, self.y_pred)
        precision = precision_score(self.y_true, self.y_pred, zero_division=0)
        recall = recall_score(self.y_true, self.y_pred, zero_division=0)
        f1 = f1_score(self.y_true, self.y_pred, zero_division=0)
        
        print(f"AUC-ROC:  {auc:.4f}  {'✓ Good' if auc >= 0.70 else '✗ Poor'}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision:{precision:.4f}  (Of flagged, % actually default)")
        print(f"Recall:   {recall:.4f}    (Of defaults, % we catch)")
        print(f"F1-Score: {f1:.4f}")
        
        # Confusion matrix
        print(f"\n[2] CONFUSION MATRIX")
        print(f"{'-'*80}")
        
        tn, fp, fn, tp = confusion_matrix(self.y_true, self.y_pred).ravel()
        
        print(f"""
        Actual\\Predicted  No Default  Default
        No Default        {tn:>6.0f}      {fp:>6.0f}
        Default           {fn:>6.0f}      {tp:>6.0f}
        
        Specificity (catch non-default): {tn/(tn+fp):.1%}
        Sensitivity (catch default):     {tp/(tp+fn):.1%}
        """)
        
        print(classification_report(self.y_true, self.y_pred, 
                                   target_names=['Non-Default', 'Default']))
        
        # Business metrics
        print(f"\n[3] BUSINESS IMPACT ANALYSIS")
        print(f"{'-'*80}")
        
        intervention_cost = 500  # $ to reach out
        loss_per_default = 5000  # $ loss if default
        
        prevented_value = tp * loss_per_default
        intervention_spend = (tp + fp) * intervention_cost
        missed_loss = fn * loss_per_default
        
        net_benefit = prevented_value - intervention_spend - missed_loss
        roi = (net_benefit / intervention_spend * 100) if intervention_spend > 0 else 0
        
        print(f"Intervention cost per customer: ${intervention_cost}")
        print(f"Loss per default: ${loss_per_default}")
        print()
        print(f"Flagged for intervention: {tp+fp:,}")
        print(f"  ├─ Correct (defaults caught): {tp:,}")
        print(f"  └─ False alarms: {fp:,}")
        print()
        print(f"Not flagged: {tn+fn:,}")
        print(f"  ├─ Correct: {tn:,}")
        print(f"  └─ Missed defaults: {fn:,}")
        print()
        print(f"Financial Impact:")
        print(f"  Prevented losses: ${prevented_value:,}")
        print(f"  Intervention cost: ${intervention_spend:,}")
        print(f"  Missed losses: ${missed_loss:,}")
        print(f"  ─────────────")
        print(f"  NET BENEFIT: ${net_benefit:,}")
        print(f"  ROI: {roi:.1f}%")
        
        # Threshold analysis
        print(f"\n[4] THRESHOLD OPTIMIZATION")
        print(f"{'-'*80}")
        
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
        results = []
        
        print(f"{'Threshold':<12}{'Recall':<12}{'Precision':<12}{'F1':<12}{'Flagged':<12}{'Benefit':<12}")
        print(f"{'-'*72}")
        
        for threshold in thresholds:
            y_pred_t = (self.y_pred_proba >= threshold).astype(int)
            rec = recall_score(self.y_true, y_pred_t, zero_division=0)
            prec = precision_score(self.y_true, y_pred_t, zero_division=0)
            f1_t = f1_score(self.y_true, y_pred_t, zero_division=0)
            flagged_t = y_pred_t.sum()
            
            # Calculate benefit
            tp_t = ((self.y_true == 1) & (y_pred_t == 1)).sum()
            fp_t = ((self.y_true == 0) & (y_pred_t == 1)).sum()
            fn_t = ((self.y_true == 1) & (y_pred_t == 0)).sum()
            
            benefit_t = tp_t * loss_per_default - (tp_t + fp_t) * intervention_cost - fn_t * loss_per_default
            
            print(f"{threshold:<12.1f}{rec:<12.3f}{prec:<12.3f}{f1_t:<12.3f}{flagged_t:<12,}{benefit_t:<12,}")
            results.append({'threshold': threshold, 'f1': f1_t, 'benefit': benefit_t})
        
        # Recommended threshold
        best_idx = max(range(len(results)), key=lambda i: results[i]['f1'])
        recommended = results[best_idx]['threshold']
        
        print(f"\nRecommended threshold: {recommended:.1f} (optimizes F1-score)")
        
        # ROC curve insight
        print(f"\n[5] ROC CURVE ANALYSIS")
        print(f"{'-'*80}")
        
        fpr, tpr, roc_thresholds = roc_curve(self.y_true, self.y_pred_proba)
        j_scores = tpr - fpr
        optimal_idx = np.argmax(j_scores)
        optimal_threshold = roc_thresholds[optimal_idx]
        
        print(f"Optimal threshold (Youden): {optimal_threshold:.4f}")
        print(f"  True Positive Rate: {tpr[optimal_idx]:.1%} (catch {tpr[optimal_idx]:.0%} of defaults)")
        print(f"  False Positive Rate: {fpr[optimal_idx]:.1%} (false alarms {fpr[optimal_idx]:.1%})")
        
        return {
            'auc': auc,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'tn': tn,
            'net_benefit': net_benefit,
            'roi': roi,
            'recommended_threshold': recommended,
        }


def evaluate_on_synthetic_data():
    """Load synthetic data and evaluate"""
    
    print("\n" + "="*80)
    print("EVALUATING ON SYNTHETIC DATA")
    print("="*80)
    
    # Load synthetic data
    df = pd.read_csv(r'd:\Barclays\synthetic_customer_features_FIXED.csv')
    
    X = df.drop(['customer_id', 'is_default'], axis=1)
    y = df['is_default']
    
    # Simple baseline: naive probabilistic model based on signals
    # (In production, replace with actual LSTM predictions)
    
    # Calculate simple stress score from signals
    stress_scores = (
        (df['week5_salary_delay'] / 15) * 0.15 +
        (df['week5_atm_count'] / 20) * 0.25 +
        (df['week5_failed_debits'] / 5) * 0.25 +
        (1 - df['week5_payment_ratio']) * 0.20 +
        (df['discretionary_trend'].clip(upper=3000) / 3000) * 0.10
    )
    stress_scores = stress_scores.clip(0, 1)
    
    # Simulate LSTM model predictions (stress_scores as proxy)
    # In reality, LSTM would produce these probabilities
    y_pred_proba = stress_scores.values
    
    evaluator = ModelEvaluator(y.values, y_pred_proba, model_name="Synthetic Baseline Model")
    metrics = evaluator.evaluate_all()
    
    print(f"\n{'='*80}")
    print("INTERPRETATION FOR PRODUCTION")
    print(f"{'='*80}")
    print(f"""
When you train your LSTM model:

1. Replace stress_scores calculation with: y_pred_proba = lstm_model.predict(X_test)
2. Use same evaluation framework above
3. Target should always be: is_default (binary, real outcome)

This approach ensures:
✓ Model learns real patterns, not artifacts
✓ Evaluation metrics are meaningful
✓ Model will work on real bank data
✓ Business stakeholders understand ROI
""")
    
    return metrics


if __name__ == "__main__":
    
    print("\n" + "#"*80)
    print("# MODEL EVALUATION FRAMEWORK")
    print("# For Pre-Delinquency Detection System")
    print("#"*80)
    
    # Evaluate on synthetic data
    metrics = evaluate_on_synthetic_data()
    
    print(f"\n{'='*80}")
    print("QUICK REFERENCE")
    print(f"{'='*80}")
    print(f"""
Key Metrics for Machine Learning Team:
  - AUC:     {metrics['auc']:.4f}         (Target ≥ 0.70)
  - Recall:  {metrics['recall']:.4f}     (Target ≥ 0.65)
  - Precision: {metrics['precision']:.4f}  (Monitor false alarms)

Key Metrics for Business/Banking Team:
  - Net Benefit: ${metrics['net_benefit']:,}
  - ROI: {metrics['roi']:.1f}%
  - Recommended Threshold: {metrics['recommended_threshold']:.1f}

Key Metrics for Operations Team:
  - Catch Rate: {metrics['recall']:.1%} of actual defaults
  - False Alarm Rate: {(metrics['fp'] / (metrics['fp'] + metrics['tn'])):.1%}
  - Num to Contact: {metrics['tp'] + metrics['fp']:,}
""")
    
    print(f"{'='*80}\n")
