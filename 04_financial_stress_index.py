"""
Financial Stress Index - PROPER VERSION

Purpose: Calculate stress score FROM real behavioral signals
Not: Predict a synthetic stress score

The index combines signals into a 0-100 stress scale

Real signals analyzed:
1. Salary delay (days)
2. ATM withdrawal activity (spike %)
3. Failed debit attempts (count)
4. Payment ratio decline (0-1)
5. Discretionary spending collapse (%)
6. Lending app activity (spike)

This score will work on REAL BANK DATA because it derives from actual behaviors
"""

import pandas as pd
import numpy as np

class FinancialStressIndex:
    """
    Calculate stress score from behavioral signals
    
    Score Range:
    0-20:   LOW (Normal financial health)
    21-40:  MEDIUM (Minor stress signals)
    41-60:  MEDIUM-HIGH (Concerning patterns)
    61-80:  HIGH (Strong early warning signals)
    81-100: CRITICAL (Imminent default risk)
    """
    
    def __init__(self):
        """
        Weights (importance) of each signal
        Must sum to 100
        """
        self.weights = {
            'salary_delay': 0.15,           # 15% weight
            'atm_spike': 0.25,              # 25% weight
            'failed_debits': 0.25,          # 25% weight
            'payment_ratio_decline': 0.20,  # 20% weight
            'discretionary_decline': 0.10,  # 10% weight
            'lending_spike': 0.05,          # 5% weight
        }
        
        # Ensure weights sum to 1.0
        assert abs(sum(self.weights.values()) - 1.0) < 0.001, "Weights must sum to 1.0"
    
    def calculate_salary_delay_score(self, salary_delay_days):
        """
        Score: salary delay in days
        
        0 days: 0 points (on-time)
        5 days: 50 points
        10+ days: 100 points (critical)
        """
        score = min(100, (salary_delay_days / 10) * 100)
        return score
    
    def calculate_atm_spike_score(self, atm_count_current_week, atm_count_baseline=2):
        """
        Score: ATM activity spike
        
        Baseline (normal): 2 ATM txns/week = 0 points
        2x baseline: ~20 points
        5x baseline: 100 points
        """
        spike_ratio = max(1.0, atm_count_current_week / atm_count_baseline)
        # Log scale: more dramatic at high spikes
        score = min(100, (np.log(spike_ratio) / np.log(5)) * 100)
        return score
    
    def calculate_failed_debits_score(self, failed_debit_count):
        """
        Score: Failed payment attempts
        
        0 fails: 0 points
        2 fails: 40 points
        5+ fails: 100 points (customer cannot pay)
        """
        score = min(100, (failed_debit_count / 5) * 100)
        return score
    
    def calculate_payment_ratio_score(self, payment_ratio):
        """
        Score: Payment-to-EMI ratio decline
        
        1.0 (full payment): 0 points
        0.5 (50% payment): 50 points
        0.0 (no payment): 100 points
        """
        score = (1.0 - payment_ratio) * 100
        return score
    
    def calculate_discretionary_decline_score(self, discretionary_spend_current, 
                                             discretionary_spend_baseline=3000):
        """
        Score: Discretionary spending reduction
        
        No reduction: 0 points
        50% reduction: 50 points
        100% reduction (zero spending): 100 points
        """
        if discretionary_spend_baseline == 0:
            return 0
        
        decline_pct = max(0, (discretionary_spend_baseline - discretionary_spend_current) / discretionary_spend_baseline)
        score = min(100, decline_pct * 100)
        return score
    
    def calculate_lending_spike_score(self, lending_count_current, lending_count_baseline=0.5):
        """
        Score: UPI lending app activity
        
        Baseline (normal): 0.5 txns/week = 0 points
        5 txns/week: 100 points (desperate borrowing)
        """
        if lending_count_baseline == 0:
            lending_count_baseline = 0.5
        
        spike_ratio = lending_count_current / lending_count_baseline
        score = min(100, (spike_ratio / 10) * 100)
        return score
    
    def calculate_stress_index(self, week_data_dict):
        """
        Calculate comprehensive stress index from a week's signals
        
        Input dict must contain:
        {
            'salary_delay_days': int,
            'atm_withdrawal_count': int,
            'failed_debit_attempts': int,
            'payment_ratio': float (0-1),
            'discretionary_spending': float,
        }
        
        Returns:
        {
            'stress_index': 0-100,
            'risk_level': 'LOW'|'MEDIUM'|'MEDIUM_HIGH'|'HIGH'|'CRITICAL',
            'component_scores': {...},
            'interpretation': str
        }
        """
        
        # Calculate individual component scores
        component_scores = {
            'salary_delay': self.calculate_salary_delay_score(
                week_data_dict.get('salary_delay_days', 0)
            ),
            'atm_spike': self.calculate_atm_spike_score(
                week_data_dict.get('atm_withdrawal_count', 2)
            ),
            'failed_debits': self.calculate_failed_debits_score(
                week_data_dict.get('failed_debit_attempts', 0)
            ),
            'payment_ratio_decline': self.calculate_payment_ratio_score(
                week_data_dict.get('payment_ratio', 1.0)
            ),
            'discretionary_decline': self.calculate_discretionary_decline_score(
                week_data_dict.get('discretionary_spending', 3000)
            ),
            'lending_spike': self.calculate_lending_spike_score(
                week_data_dict.get('lending_app_transactions', 0)
            ),
        }
        
        # Calculate weighted stress index
        stress_index = sum(
            component_scores[key] * self.weights[key]
            for key in component_scores.keys()
        )
        stress_index = min(100, max(0, stress_index))
        
        # Determine risk level
        if stress_index < 21:
            risk_level = 'LOW'
        elif stress_index < 41:
            risk_level = 'MEDIUM'
        elif stress_index < 61:
            risk_level = 'MEDIUM_HIGH'
        elif stress_index < 81:
            risk_level = 'HIGH'
        else:
            risk_level = 'CRITICAL'
        
        # Generate interpretation
        interpretation = self._interpret_stress(stress_index, component_scores)
        
        return {
            'stress_index': stress_index,
            'risk_level': risk_level,
            'component_scores': component_scores,
            'interpretation': interpretation,
        }
    
    def _interpret_stress(self, stress_index, components):
        """Generate human-readable interpretation"""
        
        top_signals = sorted(components.items(), key=lambda x: x[1], reverse=True)[:2]
        top_signal_names = [s[0] for s in top_signals]
        
        if stress_index >= 81:
            trigger = f"Critical stress: {', '.join(top_signal_names)}"
        elif stress_index >= 61:
            trigger = f"High stress from: {', '.join(top_signal_names)}"
        elif stress_index >= 41:
            trigger = f"Concerning patterns: {', '.join(top_signal_names)}"
        elif stress_index >= 21:
            trigger = f"Minor stress signals: {', '.join(top_signal_names)}"
        else:
            trigger = f"Healthy financial status"
        
        return trigger
    
    def calculate_stress_index_from_weekly_data(self, weekly_signals_list):
        """
        Calculate stress index for each week in sequence
        
        Input: List of weekly signal dicts (one per week)
        Output: List of stress indices
        """
        
        indices = []
        for week_data in weekly_signals_list:
            result = self.calculate_stress_index(week_data)
            indices.append(result['stress_index'])
        
        return indices
    
    def calculate_stress_trend(self, stress_indices):
        """
        Analyze stress progression
        
        Returns:
        - 'ESCALATING': Stress increasing (warning sign)
        - 'STABLE': Stress stable (normal or still elevated)
        - 'IMPROVING': Stress improving (good)
        """
        
        if len(stress_indices) < 2:
            return 'STABLE'
        
        # Compare first week to last week
        first = stress_indices[0]
        last = stress_indices[-1]
        
        if last > first + 10:  # >10 point increase
            return 'ESCALATING'
        elif last < first - 10:  # >10 point decrease
            return 'IMPROVING'
        else:
            return 'STABLE'


# ============================================================================
# USAGE EXAMPLE: Test on Synthetic Data
# ============================================================================

if __name__ == "__main__":
    
    print("="*80)
    print("FINANCIAL STRESS INDEX - EXAMPLE CALCULATIONS")
    print("="*80)
    
    index_calculator = FinancialStressIndex()
    
    # ========================================
    # Example 1: Non-defaulter (Week 1)
    # ========================================
    print("\n[EXAMPLE 1] Non-Defaulter - Week 1 (Healthy)")
    print("-" * 80)
    
    healthy_signals = {
        'salary_delay_days': 0,
        'atm_withdrawal_count': 2,
        'failed_debit_attempts': 0,
        'payment_ratio': 1.0,
        'discretionary_spending': 3000,
        'lending_app_transactions': 0,
    }
    
    result1 = index_calculator.calculate_stress_index(healthy_signals)
    print(f"Signals: {healthy_signals}")
    print(f"\nStress Index: {result1['stress_index']:.1f} / 100")
    print(f"Risk Level: {result1['risk_level']}")
    print(f"Interpretation: {result1['interpretation']}")
    print(f"\nComponent Breakdown:")
    for component, score in result1['component_scores'].items():
        print(f"  {component:<25}: {score:>6.1f} points")
    
    # ========================================
    # Example 2: Defaulter - Week 3 (Escalating Stress)
    # ========================================
    print("\n" + "="*80)
    print("[EXAMPLE 2] Defaulter - Week 3 (Escalating Stress)")
    print("-" * 80)
    
    stressed_signals = {
        'salary_delay_days': 5,
        'atm_withdrawal_count': 8,
        'failed_debit_attempts': 2,
        'payment_ratio': 0.6,
        'discretionary_spending': 1000,
        'lending_app_transactions': 3,
    }
    
    result2 = index_calculator.calculate_stress_index(stressed_signals)
    print(f"Signals: {stressed_signals}")
    print(f"\nStress Index: {result2['stress_index']:.1f} / 100")
    print(f"Risk Level: {result2['risk_level']}")
    print(f"Interpretation: {result2['interpretation']}")
    print(f"\nComponent Breakdown:")
    for component, score in result2['component_scores'].items():
        print(f"  {component:<25}: {score:>6.1f} points")
    
    # ========================================
    # Example 3: Defaulter - Week 5 (Critical)
    # ========================================
    print("\n" + "="*80)
    print("[EXAMPLE 3] Defaulter - Week 5 (Critical)")
    print("-" * 80)
    
    critical_signals = {
        'salary_delay_days': 10,
        'atm_withdrawal_count': 15,
        'failed_debit_attempts': 4,
        'payment_ratio': 0.0,
        'discretionary_spending': 0,
        'lending_app_transactions': 7,
    }
    
    result3 = index_calculator.calculate_stress_index(critical_signals)
    print(f"Signals: {critical_signals}")
    print(f"\nStress Index: {result3['stress_index']:.1f} / 100")
    print(f"Risk Level: {result3['risk_level']}")
    print(f"Interpretation: {result3['interpretation']}")
    print(f"\nComponent Breakdown:")
    for component, score in result3['component_scores'].items():
        print(f"  {component:<25}: {score:>6.1f} points")
    
    # ========================================
    # Example 4: 5-week progression
    # ========================================
    print("\n" + "="*80)
    print("[EXAMPLE 4] 5-Week Stress Progression (Defaulter)")
    print("-" * 80)
    
    weekly_progression = [
        {'salary_delay_days': 0, 'atm_withdrawal_count': 2, 'failed_debit_attempts': 0, 'payment_ratio': 1.0, 'discretionary_spending': 3000, 'lending_app_transactions': 0},
        {'salary_delay_days': 2, 'atm_withdrawal_count': 4, 'failed_debit_attempts': 0, 'payment_ratio': 0.8, 'discretionary_spending': 2000, 'lending_app_transactions': 1},
        {'salary_delay_days': 5, 'atm_withdrawal_count': 8, 'failed_debit_attempts': 2, 'payment_ratio': 0.6, 'discretionary_spending': 1000, 'lending_app_transactions': 3},
        {'salary_delay_days': 8, 'atm_withdrawal_count': 12, 'failed_debit_attempts': 3, 'payment_ratio': 0.3, 'discretionary_spending': 500, 'lending_app_transactions': 5},
        {'salary_delay_days': 10, 'atm_withdrawal_count': 15, 'failed_debit_attempts': 4, 'payment_ratio': 0.0, 'discretionary_spending': 0, 'lending_app_transactions': 7},
    ]
    
    stress_indices = index_calculator.calculate_stress_index_from_weekly_data(weekly_progression)
    trend = index_calculator.calculate_stress_trend(stress_indices)
    
    print(f"{'Week':<8}{'Salary Delay':<15}{'ATM Count':<12}{'Payment %':<12}{'Stress Index':<15}{'Risk Level':<15}")
    print("-" * 80)
    
    for week_num, (signals, stress_idx) in enumerate(zip(weekly_progression, stress_indices), 1):
        risk_level = 'CRITICAL' if stress_idx >= 81 else 'HIGH' if stress_idx >= 61 else 'MEDIUM_HIGH' if stress_idx >= 41 else 'MEDIUM' if stress_idx >= 21 else 'LOW'
        print(f"Week {week_num:<2} {signals['salary_delay_days']:<14.0f} {signals['atm_withdrawal_count']:<11.0f} {signals['payment_ratio']*100:<11.0f}% {stress_idx:<14.1f} {risk_level:<15}")
    
    print(f"\nTrend: {trend} ({'Customer at risk of default' if trend == 'ESCALATING' else 'Situation stable/improving'})")
    
    print("\n" + "="*80)
    print("KEY POINTS:")
    print("="*80)
    print(f"""
✓ This stress index DERIVES from real behavioral signals
✓ No artificial scoring - works on real bank data
✓ Clear interpretation of each component
✓ Threshold-based risk levels (LOW, MEDIUM, HIGH, CRITICAL)
✓ Can track stress trends over time (ESCALATING, STABLE, IMPROVING)

The index can be saved and reused:
    - Load: index = FinancialStressIndex()
    - Calculate: stress = index.calculate_stress_index(weekly_signals)
    - Trend: trend = index.calculate_stress_trend(stress_list)
""")
