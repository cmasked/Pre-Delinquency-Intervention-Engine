"""
REALISTIC DATA GENERATION WITH PROPER DISTRIBUTION
====================================================

This creates a realistic population with:
- 70% LOW RISK (stable customers)
- 15% MEDIUM RISK (showing early stress)
- 10% HIGH RISK (deteriorating rapidly)
- 5% CRITICAL RISK (about to default)

NOT binary (all high or all low) - proper gradient
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

class RealisticDataGenerator:
    
    def __init__(self, n_customers=10000):
        self.n_customers = n_customers
        
        # Create realistic risk segments
        self.n_low = int(n_customers * 0.70)      # 70% - Stable
        self.n_medium = int(n_customers * 0.15)   # 15% - Emerging stress
        self.n_high = int(n_customers * 0.10)     # 10% - Deteriorating
        self.n_critical = int(n_customers * 0.05) # 5% - About to default
        
        print(f"Generating {n_customers} customers:")
        print(f"  🟢 LOW RISK: {self.n_low} ({self.n_low/n_customers*100:.0f}%)")
        print(f"  🟡 MEDIUM RISK: {self.n_medium} ({self.n_medium/n_customers*100:.0f}%)")
        print(f"  🟠 HIGH RISK: {self.n_high} ({self.n_high/n_customers*100:.0f}%)")
        print(f"  🔴 CRITICAL RISK: {self.n_critical} ({self.n_critical/n_customers*100:.0f}%)")
    
    def generate_customer_segment_data(self, risk_segment, n_customers, start_idx):
        """Generate realistic data for each risk segment"""
        
        customers = []
        
        for i in range(n_customers):
            
            if risk_segment == 'LOW':
                # Stable customer
                customer_data = {
                    'customer_id': start_idx + i,
                    'age': np.random.randint(25, 60),
                    'monthly_salary': np.random.uniform(30000, 150000),
                    'salary_delay_days': np.random.normal(0, 1),  # Almost always on time
                    'atm_withdrawal_count': np.random.normal(2, 0.5),  # 1-3 per week
                    'avg_atm_amount': np.random.uniform(1000, 3000),
                    'failed_debit_count': np.random.poisson(0.1),  # Almost never fails
                    'failed_debit_amount': 0,
                    'payment_ratio': np.random.normal(0.98, 0.02),  # Pays 98%+ on time
                    'missed_emi_count': 0,
                    'late_emi_days_avg': np.random.normal(0, 0.5),  # On time
                    'discretionary_spending': np.random.uniform(5000, 15000),  # Healthy
                    'discretionary_transaction_count': np.random.normal(20, 3),
                    'lending_app_transactions': np.random.poisson(0.5),  # Rarely borrows
                    'lending_app_amount': 0,
                    'upi_total_transactions': np.random.normal(30, 5),
                    'savings_balance_change': np.random.uniform(1000, 5000),  # Growing
                    'savings_drawdown_ratio': np.random.normal(0.05, 0.02),  # Only 5% drawn
                    'final_savings_balance': np.random.uniform(50000, 200000),  # Healthy
                    'utility_late_payment_count': 0,
                    'utility_avg_days_late': 0,
                    'total_utility_amount': np.random.uniform(2000, 5000),
                    'is_default': 0,
                    'stress_score': np.random.uniform(10, 30),  # LOW STRESS
                }
            
            elif risk_segment == 'MEDIUM':
                # Emerging stress
                customer_data = {
                    'customer_id': start_idx + i,
                    'age': np.random.randint(30, 55),
                    'monthly_salary': np.random.uniform(25000, 100000),
                    'salary_delay_days': np.random.normal(3, 2),  # 3 days late sometimes
                    'atm_withdrawal_count': np.random.normal(4, 1),  # Withdrawing more
                    'avg_atm_amount': np.random.uniform(2000, 5000),
                    'failed_debit_count': np.random.poisson(1),  # 1 failure per month
                    'failed_debit_amount': np.random.uniform(5000, 15000),
                    'payment_ratio': np.random.normal(0.85, 0.10),  # Pays 85% on time
                    'missed_emi_count': np.random.poisson(0.5),  # Miss occasionally
                    'late_emi_days_avg': np.random.normal(5, 3),  # 5 days late avg
                    'discretionary_spending': np.random.uniform(2000, 8000),  # Cut back
                    'discretionary_transaction_count': np.random.normal(10, 3),  # Fewer
                    'lending_app_transactions': np.random.poisson(3),  # Borrowing more
                    'lending_app_amount': np.random.uniform(20000, 100000),
                    'upi_total_transactions': np.random.normal(50, 10),
                    'savings_balance_change': np.random.uniform(-5000, 1000),  # Declining
                    'savings_drawdown_ratio': np.random.normal(0.20, 0.08),  # 20% drawn
                    'final_savings_balance': np.random.uniform(10000, 50000),  # Lower
                    'utility_late_payment_count': np.random.poisson(1),  # Late on bills
                    'utility_avg_days_late': np.random.normal(3, 2),
                    'total_utility_amount': np.random.uniform(3000, 7000),
                    'is_default': 0,
                    'stress_score': np.random.uniform(40, 60),  # MEDIUM STRESS
                }
            
            elif risk_segment == 'HIGH':
                # Deteriorating rapidly
                customer_data = {
                    'customer_id': start_idx + i,
                    'age': np.random.randint(35, 58),
                    'monthly_salary': np.random.uniform(20000, 80000),
                    'salary_delay_days': np.random.normal(8, 3),  # Often delayed
                    'atm_withdrawal_count': np.random.normal(8, 2),  # Heavy withdrawals
                    'avg_atm_amount': np.random.uniform(3000, 8000),
                    'failed_debit_count': np.random.poisson(3),  # Multiple failures
                    'failed_debit_amount': np.random.uniform(10000, 30000),
                    'payment_ratio': np.random.normal(0.60, 0.15),  # Pays 60% on time
                    'missed_emi_count': np.random.poisson(2),  # Miss often
                    'late_emi_days_avg': np.random.normal(15, 5),  # 15 days late
                    'discretionary_spending': np.random.uniform(500, 3000),  # Cut drastically
                    'discretionary_transaction_count': np.random.normal(3, 1),  # Minimal
                    'lending_app_transactions': np.random.poisson(8),  # Heavy borrowing
                    'lending_app_amount': np.random.uniform(100000, 300000),
                    'upi_total_transactions': np.random.normal(80, 15),
                    'savings_balance_change': np.random.uniform(-20000, -5000),  # Depleting
                    'savings_drawdown_ratio': np.random.normal(0.50, 0.15),  # 50% drawn
                    'final_savings_balance': np.random.uniform(1000, 15000),  # Almost gone
                    'utility_late_payment_count': np.random.poisson(3),  # Consistently late
                    'utility_avg_days_late': np.random.normal(10, 3),
                    'total_utility_amount': np.random.uniform(5000, 10000),
                    'is_default': 0,
                    'stress_score': np.random.uniform(65, 80),  # HIGH STRESS
                }
            
            else:  # CRITICAL
                # About to default
                customer_data = {
                    'customer_id': start_idx + i,
                    'age': np.random.randint(38, 60),
                    'monthly_salary': np.random.uniform(15000, 60000),
                    'salary_delay_days': np.random.normal(12, 4),  # Very often delayed
                    'atm_withdrawal_count': np.random.normal(12, 3),  # Panic withdrawals
                    'avg_atm_amount': np.random.uniform(5000, 15000),
                    'failed_debit_count': np.random.poisson(6),  # Multiple failures every month
                    'failed_debit_amount': np.random.uniform(25000, 50000),
                    'payment_ratio': np.random.normal(0.30, 0.20),  # Pays only 30%
                    'missed_emi_count': np.random.poisson(4),  # Misses frequently
                    'late_emi_days_avg': np.random.normal(25, 8),  # 25 days late
                    'discretionary_spending': np.random.uniform(0, 1000),  # Almost zero
                    'discretionary_transaction_count': np.random.normal(1, 0.5),  # Almost none
                    'lending_app_transactions': np.random.poisson(15),  # Desperate borrowing
                    'lending_app_amount': np.random.uniform(250000, 500000),
                    'upi_total_transactions': np.random.normal(120, 20),
                    'savings_balance_change': np.random.uniform(-50000, -20000),  # Collapsing
                    'savings_drawdown_ratio': np.random.normal(0.85, 0.10),  # 85% depleted
                    'final_savings_balance': np.random.uniform(0, 5000),  # Nearly zero
                    'utility_late_payment_count': np.random.poisson(5),  # Always late
                    'utility_avg_days_late': np.random.normal(20, 5),
                    'total_utility_amount': np.random.uniform(8000, 15000),
                    'is_default': 1,  # WILL DEFAULT
                    'stress_score': np.random.uniform(85, 100),  # CRITICAL STRESS
                }
            
            customers.append(customer_data)
        
        return customers
    
    def run_all(self):
        """Generate all realistic data"""
        
        print("\n" + "="*80)
        print("GENERATING REALISTIC CUSTOMER DATA WITH PROPER DISTRIBUTION")
        print("="*80)
        
        all_customers = []
        idx = 1
        
        print("\n[1] Generating LOW RISK customers...")
        low_risk = self.generate_customer_segment_data('LOW', self.n_low, idx)
        all_customers.extend(low_risk)
        idx += self.n_low
        
        print("[2] Generating MEDIUM RISK customers...")
        medium_risk = self.generate_customer_segment_data('MEDIUM', self.n_medium, idx)
        all_customers.extend(medium_risk)
        idx += self.n_medium
        
        print("[3] Generating HIGH RISK customers...")
        high_risk = self.generate_customer_segment_data('HIGH', self.n_high, idx)
        all_customers.extend(high_risk)
        idx += self.n_high
        
        print("[4] Generating CRITICAL RISK customers...")
        critical_risk = self.generate_customer_segment_data('CRITICAL', self.n_critical, idx)
        all_customers.extend(critical_risk)
        
        df = pd.DataFrame(all_customers)
        
        # Format customer_id
        df['customer_id'] = df['customer_id'].apply(lambda x: f"CUST_{x:06d}")
        
        # Save
        df.to_csv('realistic_customer_features.csv', index=False)
        
        print("\n" + "="*80)
        print("✓ REALISTIC DATA GENERATED")
        print("="*80)
        
        print(f"\nDistribution Check:")
        print(f"  Stress Score Stats:")
        print(df['stress_score'].describe())
        print(f"\nDefault rate: {df['is_default'].mean():.1%}")
        print(f"\nRisk Segment Distribution:")
        low = len(df[df['stress_score'] < 35])
        med = len(df[(df['stress_score'] >= 35) & (df['stress_score'] < 65)])
        high = len(df[(df['stress_score'] >= 65) & (df['stress_score'] < 85)])
        crit = len(df[df['stress_score'] >= 85])
        print(f"  LOW: {low} ({low/len(df)*100:.1f}%)")
        print(f"  MEDIUM: {med} ({med/len(df)*100:.1f}%)")
        print(f"  HIGH: {high} ({high/len(df)*100:.1f}%)")
        print(f"  CRITICAL: {crit} ({crit/len(df)*100:.1f}%)")
        
        print(f"\nSaved to: realistic_customer_features.csv ({len(df):,} customers)")
        
        return df

if __name__ == "__main__":
    gen = RealisticDataGenerator(n_customers=10000)
    df = gen.run_all()
    print("\n✓ Ready for next step: python 01_unified_ml_pipeline.py")
