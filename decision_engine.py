"""
DECISION ENGINE - LOADS MODEL FROM PICKLE
==========================================

This script:
1. Loads trained model from pickle
2. Gets model predictions on customer features
3. Calculates Financial Stress Index
4. Applies business rules
5. Generates risk-based interventions
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler

class DecisionEngine:
    """Risk-based intervention decision making with trained model"""
    
    def __init__(self):
        """Initialize with trained model and scaler"""
        
        # Load model from pickle
        try:
            with open('xgboost_model.pkl', 'rb') as f:
                self.model = pickle.load(f)
            print("✓ Model loaded: xgboost_model.pkl")
        except FileNotFoundError:
            raise FileNotFoundError("xgboost_model.pkl not found. Run rebuild_model_pickle.py first")
        
        # Load scaler
        try:
            with open('feature_scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
            print("✓ Scaler loaded: feature_scaler.pkl")
        except FileNotFoundError:
            self.scaler = None
            print("⚠ Scaler not found")
        
        self.threshold_high = 0.6
        self.threshold_medium = 0.3
    
    def predict_default_risk(self, X_features):
        """Get default probability from model"""
        if self.model is None:
            return np.zeros(len(X_features))
        
        # Scale if scaler available
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X_features)
        else:
            X_scaled = X_features
        
        # Get probabilities
        try:
            y_prob = self.model.predict_proba(X_scaled)[:, 1]
        except:
            y_prob = np.zeros(len(X_features))
        
        return y_prob
    
    def calculate_stress_index(self, features_row):
        """Calculate stress score from behavioral signals"""
        
        try:
            salary_delay = features_row.get('salary_delay_days', 0)
            atm_count = features_row.get('atm_withdrawal_count', 0)
            failed_debits = features_row.get('failed_debit_count', 0)
            payment_ratio = features_row.get('payment_ratio', 1.0)
            discretionary = features_row.get('discretionary_spending', 0)
            lending = features_row.get('lending_app_transactions', 0)
            
            # Normalize components to 0-1
            salary_normalized = min(salary_delay / 30, 1.0)
            atm_normalized = min(atm_count / 20, 1.0)
            failed_normalized = min(failed_debits / 10, 1.0)
            payment_normalized = 1.0 - payment_ratio
            discretionary_normalized = 1.0 if discretionary < 1000 else 0.0
            lending_normalized = min(lending / 20, 1.0)
            
            # Weighted sum (0-100)
            stress_score = (
                salary_normalized * 15 +
                atm_normalized * 25 +
                failed_normalized * 25 +
                payment_normalized * 20 +
                discretionary_normalized * 10 +
                lending_normalized * 5
            )
            
            return min(stress_score, 100)
        except:
            return 0
    
    def generate_decision(self, customer_id, risk_prob, stress_score):
        """Apply business rules to generate decision"""
        
        if risk_prob > 0.7 and stress_score > 70:
            return {
                'customer_id': customer_id,
                'risk_level': 'CRITICAL',
                'model_probability': risk_prob,
                'stress_score': stress_score,
                'recommended_action': 'PAYMENT_HOLIDAY',
                'urgency': 'IMMEDIATE'
            }
        elif risk_prob > 0.6 and stress_score > 60:
            return {
                'customer_id': customer_id,
                'risk_level': 'HIGH',
                'model_probability': risk_prob,
                'stress_score': stress_score,
                'recommended_action': 'RESTRUCTURE',
                'urgency': '24_HOURS'
            }
        elif risk_prob > 0.4 and stress_score > 50:
            return {
                'customer_id': customer_id,
                'risk_level': 'HIGH',
                'model_probability': risk_prob,
                'stress_score': stress_score,
                'recommended_action': 'RESTRUCTURE',
                'urgency': '48_HOURS'
            }
        elif stress_score > 40:
            return {
                'customer_id': customer_id,
                'risk_level': 'MEDIUM',
                'model_probability': risk_prob,
                'stress_score': stress_score,
                'recommended_action': 'PROACTIVE_OUTREACH',
                'urgency': '72_HOURS'
            }
        elif risk_prob > 0.3:
            return {
                'customer_id': customer_id,
                'risk_level': 'LOW',
                'model_probability': risk_prob,
                'stress_score': stress_score,
                'recommended_action': 'MONITOR',
                'urgency': 'WEEKLY'
            }
        else:
            return {
                'customer_id': customer_id,
                'risk_level': 'LOW',
                'model_probability': risk_prob,
                'stress_score': stress_score,
                'recommended_action': 'STANDARD',
                'urgency': 'MONTHLY'
            }

    def process_batch(self, batch_df):
        """Process a batch of customers"""
        
        decisions = []
        
        # Get feature columns (exclude customer_id, is_default)
        feature_cols = [col for col in batch_df.columns if col not in ['customer_id', 'is_default']]
        
        # Get predictions
        X_batch = batch_df[feature_cols].fillna(0)
        risks = self.predict_default_risk(X_batch)
        
        # Generate decisions for each customer
        for idx, row in batch_df.iterrows():
            customer_id = row['customer_id']
            risk_prob = float(risks[idx])
            stress = self.calculate_stress_index(row)
            
            decision = self.generate_decision(customer_id, risk_prob, stress)
            decisions.append(decision)
        
        return pd.DataFrame(decisions)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    
    print("="*80)
    print("DECISION ENGINE - PERSON 3 TASK")
    print("="*80)
    
    # Initialize Decision Engine
    print("\n[1] Initializing Decision Engine...")
    engine = DecisionEngine()
    print("✓ Model loaded")
    print("✓ Feature scaler loaded")
    
    # Load test data
    print("\n[2] Loading test data...")
    df_customers = pd.read_csv('synthetic_customer_features_FIXED.csv')
    print(f"✓ Loaded {len(df_customers):,} customers")
    
    # Process first 100 customers for demonstration
    print("\n[3] Processing customers...")
    sample_df = df_customers.head(100)
    decisions_df = engine.process_batch(sample_df)
    
    print(f"✓ Processed {len(decisions_df)} customers")
    
    # Save decisions
    decisions_df.to_csv('customer_decisions.csv', index=False)
    print(f"✓ Saved to: customer_decisions.csv")
    
    # ========================================================================
    # DISPLAY RESULTS
    # ========================================================================
    
    print("\n" + "="*80)
    print("DECISION ENGINE OUTPUT - SAMPLE RESULTS")
    print("="*80)
    
    # Summary statistics
    print("\n[SUMMARY STATISTICS]")
    print(f"Total customers processed: {len(decisions_df)}")
    print(f"\nRisk Level Distribution:")
    print(decisions_df['risk_level'].value_counts().to_string())
    
    print(f"\n\nAction Distribution:")
    print(decisions_df['action'].value_counts().to_string())
    
    print(f"\n\nUrgency Distribution:")
    print(decisions_df['urgency'].value_counts().to_string())
    
    # Show high-risk customers
    print("\n" + "-"*80)
    print("HIGH-RISK CUSTOMERS (Top 10)")
    print("-"*80)
    
    high_risk = decisions_df.nlargest(10, 'stress_index')[
        ['customer_id', 'model_probability', 'stress_index', 'risk_level', 'action', 'urgency']
    ]
    
    for idx, row in high_risk.iterrows():
        print(f"\n  Customer: {row['customer_id']}")
        print(f"  ├─ Default Probability: {row['model_probability']:.1%}")
        print(f"  ├─ Stress Index: {row['stress_index']:.1f} ({row['risk_level']})")
        print(f"  ├─ Action: {row['action']}")
        print(f"  └─ Urgency: {row['urgency']}")
    
    # Show distribution of features
    print("\n" + "-"*80)
    print("AVERAGE METRICS BY ACTION")
    print("-"*80)
    
    for action in decisions_df['action'].unique():
        subset = decisions_df[decisions_df['action'] == action]
        avg_prob = subset['model_probability'].mean()
        avg_stress = subset['stress_index'].mean()
        count = len(subset)
        
        print(f"\n  {action}")
        print(f"  ├─ Count: {count}")
        print(f"  ├─ Avg Probability: {avg_prob:.1%}")
        print(f"  └─ Avg Stress Index: {avg_stress:.1f}")
    
    # Financial impact
    print("\n" + "-"*80)
    print("FINANCIAL IMPACT ANALYSIS")
    print("-"*80)
    
    intervention_cost = 500  # $ per contact
    default_loss = 5000      # $ per default
    
    for risk in ['CRITICAL', 'HIGH', 'MEDIUM_HIGH', 'MEDIUM']:
        subset = decisions_df[decisions_df['risk_level'] == risk]
        if len(subset) > 0:
            # Estimate defaults in this group
            estimated_defaults = (subset['model_probability'].mean() * len(subset)).astype(int)
            intervention_spend = len(subset) * intervention_cost
            prevented_loss = estimated_defaults * default_loss
            net_benefit = prevented_loss - intervention_spend
            
            print(f"\n  {risk} Risk Customers: {len(subset)}")
            print(f"  ├─ Est. Defaults: {estimated_defaults}")
            print(f"  ├─ Intervention Cost: ${intervention_spend:,.0f}")
            print(f"  ├─ Prevented Loss: ${prevented_loss:,.0f}")
            print(f"  └─ Net Benefit: ${net_benefit:,.0f}")
    
    print("\n" + "="*80)
    print("✓ DECISION ENGINE COMPLETE - Ready for Dashboard/UI")
    print("="*80 + "\n")
