"""
Aggregate Features from PRIORITY 1 Datasets — V2 (80+ features)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reads 7 raw datasets and computes 80+ behavioral features per customer
using fast groupby operations (no per-row loops).

New features over v1:
  - overdue_degradation_slope       (temporal payment worsening)
  - recent_late_count               (last 2 months EMI behaviour)
  - emi_holiday_count               (EMI moratorium usage)
  - late_night_txn_ratio            (late-night transaction pattern)
  - weekend_spending_ratio          (weekend vs weekday behaviour)
  - merchant_diversity              (unique merchants used)
  - emergency_spike_count           (2σ+ spending spikes)
  - salary_volatility               (coefficient of variation)
  - spending_trend_slope            (week-over-week spending trend)
  - balance_degradation_slope       (savings trend)
  - min_weeks_survival              (minimum weeks-of-survival)
  - avg_drawdown_rate               (avg balance drawdown)
  - below_min_count                 (weeks below ₹5000)
  - red_threshold_count             (weeks in RED zone)
  - intervention_weeks              (post-intervention weeks)
  - severity_score_total            (cumulative failure severity)
  - severity_score_max              (peak severity)
  - failure_escalation_ratio        (late vs early failures)
  - max_concurrent_failures         (cascading — max bill types failing same week)
  - emi_failure_count_from_failed   (EMI failures from failed_transactions)
  - upi_repayment_rate              (% of app loans repaid)
  - upi_stacking_ratio              (% of stacking loans)
  - upi_escalation_ratio            (late vs early borrowing)
  - upi_debt_refinance_count        (debt refinance loans)
  - utility_on_time_ratio           (utility on-time rate)
  - utility_partial_count           (partial payment count)
  - utility_disconnection_risk      (periods at disconnection risk)
  - utility_critical_late_count     (late payments on critical bills)
  - payment_mode_switches           (unique payment modes per customer)

Output:
  - customer_features_from_priority1.csv (10K rows × 80+ features)
  - customer_weekly_features_from_priority1.csv (time-series features)
"""

import sys
import pandas as pd
import numpy as np
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

# Fix Windows console UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=" * 80)
print("AGGREGATING FEATURES FROM PRIORITY 1 DATASETS — V2 (80+ FEATURES)")
print("=" * 80)

# ============================================================================
# 1. Load all datasets
# ============================================================================
print("\n[1/6] Loading datasets...")
customer_master = pd.read_csv('customer_master.csv')
emi_records = pd.read_csv('emi_payment_records.csv')
transactions = pd.read_csv('transaction_history.csv')
savings_history = pd.read_csv('savings_balance_history.csv')
failed_txns = pd.read_csv('failed_transactions.csv')
upi_lending = pd.read_csv('upi_lending_transactions.csv')
utility_bills = pd.read_csv('utility_bill_payments.csv')

print(f"✓ Loaded {len(customer_master):,} customers")
print(f"  - {len(emi_records):,} EMI records")
print(f"  - {len(transactions):,} transactions")
print(f"  - {len(savings_history):,} savings snapshots")
print(f"  - {len(failed_txns):,} failed transactions")
print(f"  - {len(upi_lending):,} UPI/lending records")
print(f"  - {len(utility_bills):,} utility payments")

# ============================================================================
# 2. Extract features using fast groupby operations
# ============================================================================
print("\n[2/6] Computing behavioral features (vectorized)...")

# --- Base features from customer_master ---
features = customer_master[['customer_id', 'is_default']].copy()

features = features.merge(
    customer_master[['customer_id', 'monthly_salary_rupees', 'age', 'tenure_months',
                     'num_products', 'has_personal_loan', 'has_credit_card',
                     'has_home_loan', 'has_auto_loan']],
    on='customer_id', how='left')
features.rename(columns={'monthly_salary_rupees': 'monthly_salary'}, inplace=True)

# Encode employment_type
emp_map = {'SALARIED': 1, 'SELF_EMPLOYED': 2, 'RETIRED': 3}
features = features.merge(
    customer_master[['customer_id', 'employment_type']].assign(
        employment_type_enc=customer_master['employment_type'].map(emp_map).fillna(1).astype(int)
    )[['customer_id', 'employment_type_enc']],
    on='customer_id', how='left')

# Encode region_tier
tier_map = {'TIER1': 1, 'TIER2': 2, 'TIER3': 3}
features = features.merge(
    customer_master[['customer_id', 'region_tier']].assign(
        region_tier_enc=customer_master['region_tier'].map(tier_map).fillna(2).astype(int)
    )[['customer_id', 'region_tier_enc']],
    on='customer_id', how='left')

# Encode segment
seg_map = {'PREMIUM': 1, 'STANDARD': 2, 'RISK': 3, 'PENDING': 2}
features = features.merge(
    customer_master[['customer_id', 'customer_segment']].assign(
        customer_segment=customer_master['customer_segment'].map(seg_map).fillna(2).astype(int)
    ),
    on='customer_id', how='left')

if 'dti_ratio' in customer_master.columns:
    features = features.merge(
        customer_master[['customer_id', 'dti_ratio']], on='customer_id', how='left')
else:
    features['dti_ratio'] = 0.0

print("  ✓ Customer master features extracted")

# --- EMI features ---
# Add date columns FIRST so they're available in filtered views
emi_records['emi_due_date_dt'] = pd.to_datetime(emi_records['emi_due_date'])
emi_records['month_num'] = emi_records['emi_due_date_dt'].dt.month

# Exclude HOLIDAY records from payment ratio calculation
emi_non_holiday = emi_records[emi_records['payment_status'] != 'HOLIDAY'].copy()
emi_feat = emi_non_holiday.groupby('customer_id').agg(
    payment_ratio=('payment_status', lambda x: (x == 'ON_TIME').mean()),
    missed_emi_count=('payment_status', lambda x: (x == 'MISSED').sum()),
    failed_emi_count=('payment_status', lambda x: (x == 'FAILED_DEBIT').sum()),
    late_emi_days_avg=('days_overdue', 'mean'),
    max_days_overdue=('days_overdue', 'max'),
    avg_emi_amount=('emi_amount', 'mean'),
    total_emi_payments=('emi_amount', 'count'),
    prepayment_count=('is_prepayment', 'sum'),
).reset_index()

# Number of active loans
loan_counts = emi_records.groupby('customer_id')['loan_id'].nunique().reset_index()
loan_counts.columns = ['customer_id', 'num_active_loans']
emi_feat = emi_feat.merge(loan_counts, on='customer_id', how='left')

# Average and max interest rate
rate_agg = emi_records.groupby('customer_id')['interest_rate_pct'].agg(['mean', 'max']).reset_index()
rate_agg.columns = ['customer_id', 'avg_interest_rate', 'max_interest_rate']
emi_feat = emi_feat.merge(rate_agg, on='customer_id', how='left')

# ★NEW★ EMI holiday count
holiday_count = emi_records[emi_records['is_emi_holiday'] == True].groupby(
    'customer_id').size().reset_index(name='emi_holiday_count')
emi_feat = emi_feat.merge(holiday_count, on='customer_id', how='left')

# Payment degradation: compare early vs late months
early = emi_non_holiday[emi_non_holiday['month_num'] <= 3].groupby(
    'customer_id')['days_overdue'].mean()
late = emi_non_holiday[emi_non_holiday['month_num'] >= 4].groupby(
    'customer_id')['days_overdue'].mean()
degradation = (late - early).fillna(0).reset_index()
degradation.columns = ['customer_id', 'payment_degradation']
emi_feat = emi_feat.merge(degradation, on='customer_id', how='left')
emi_feat['payment_degradation'] = emi_feat['payment_degradation'].fillna(0)

# ★NEW★ Overdue degradation slope (linear trend of days_overdue over months)
def calc_overdue_slope(group):
    months = group['month_num'].values.astype(float)
    overdue = group['days_overdue'].values.astype(float)
    if len(months) < 3 or overdue.std() == 0:
        return 0.0
    return float(np.polyfit(months, overdue, 1)[0])

overdue_slopes = emi_non_holiday.groupby('customer_id').apply(calc_overdue_slope).reset_index()
overdue_slopes.columns = ['customer_id', 'overdue_degradation_slope']
emi_feat = emi_feat.merge(overdue_slopes, on='customer_id', how='left')

# ★NEW★ Recent EMI behaviour (last 2 months)
recent_emi = emi_non_holiday[emi_non_holiday['month_num'] >= 5]
recent_agg = recent_emi.groupby('customer_id').agg(
    recent_late_count=('payment_status', lambda x: x.isin(['LATE', 'MISSED', 'FAILED_DEBIT']).sum()),
    recent_avg_overdue=('days_overdue', 'mean')
).reset_index()
emi_feat = emi_feat.merge(recent_agg, on='customer_id', how='left')

features = features.merge(emi_feat, on='customer_id', how='left')
print("  ✓ EMI features extracted")

# --- Transaction features ---
transactions['transaction_date_dt'] = pd.to_datetime(transactions['transaction_date'])

# Salary delay
salary_txns = transactions[transactions['merchant_category'] == 'SALARY'].copy()
salary_with_day = salary_txns.merge(
    customer_master[['customer_id', 'salary_deposit_day']], on='customer_id', how='left')
salary_with_day['actual_day'] = salary_with_day['transaction_date_dt'].dt.day
salary_with_day['delay'] = (salary_with_day['actual_day'] - salary_with_day['salary_deposit_day']).clip(lower=0)
sal_delay = salary_with_day.groupby('customer_id')['delay'].mean().reset_index()
sal_delay.columns = ['customer_id', 'salary_delay_days']
features = features.merge(sal_delay, on='customer_id', how='left')

# ★NEW★ Salary volatility (coefficient of variation)
sal_var = salary_txns.groupby('customer_id')['amount'].agg(['std', 'mean']).reset_index()
sal_var.columns = ['customer_id', 'salary_std', 'salary_mean']
sal_var['salary_variation'] = sal_var['salary_std'].fillna(0)
sal_var['salary_volatility'] = (sal_var['salary_std'].fillna(0) /
                                 sal_var['salary_mean'].clip(lower=1))
features = features.merge(sal_var[['customer_id', 'salary_variation', 'salary_volatility']],
                           on='customer_id', how='left')

# ATM features
atm_txns = transactions[transactions['merchant_category'] == 'ATM']
atm_feat = atm_txns.groupby('customer_id').agg(
    atm_withdrawal_count=('amount', 'count'),
    avg_atm_amount=('amount', 'mean'),
    total_atm_amount=('amount', 'sum')
).reset_index()
features = features.merge(atm_feat, on='customer_id', how='left')

# Spending breakdown (exclude salary credits and failed txns)
spending = transactions[
    (transactions['transaction_type'].isin(['DEBIT', 'ATM'])) &
    (transactions['transaction_status'] == 'SUCCESS')
].copy()

# Discretionary spending
disc_txns = spending[spending['spending_type'] == 'DISCRETIONARY']
disc_feat = disc_txns.groupby('customer_id').agg(
    discretionary_spending=('amount', 'sum'),
    discretionary_transaction_count=('amount', 'count')
).reset_index()
features = features.merge(disc_feat, on='customer_id', how='left')

# Mandatory spending
mand_txns = spending[spending['spending_type'] == 'MANDATORY']
mand_feat = mand_txns.groupby('customer_id').agg(
    mandatory_spending=('amount', 'sum')
).reset_index()
features = features.merge(mand_feat, on='customer_id', how='left')

features['mandatory_ratio'] = features['mandatory_spending'].fillna(0) / (
    features['mandatory_spending'].fillna(0) + features['discretionary_spending'].fillna(0) + 1)

# Total spending & burn rate
total_debit = spending.groupby('customer_id')['amount'].sum().reset_index()
total_debit.columns = ['customer_id', 'total_spending']
features = features.merge(total_debit, on='customer_id', how='left')

# Digital vs cash ratio
digital_txns = spending[spending['payment_mode'] == 'DIGITAL']
cash_txns = spending[spending['payment_mode'] == 'CASH']
dig_count = digital_txns.groupby('customer_id').size().reset_index(name='digital_count')
cash_count = cash_txns.groupby('customer_id').size().reset_index(name='cash_count')
features = features.merge(dig_count, on='customer_id', how='left')
features = features.merge(cash_count, on='customer_id', how='left')
features['digital_to_cash_ratio'] = (
    features['digital_count'].fillna(0) /
    (features['digital_count'].fillna(0) + features['cash_count'].fillna(0) + 1))
features.drop(columns=['digital_count', 'cash_count'], inplace=True, errors='ignore')

# ★NEW★ Late-night transaction ratio (Fix 3.4 feature)
if 'transaction_time' in transactions.columns:
    txn_copy = transactions[transactions['transaction_type'].isin(['DEBIT', 'ATM'])].copy()
    txn_copy['hour'] = txn_copy['transaction_time'].str[:2].astype(int)
    late_night = txn_copy[(txn_copy['hour'] >= 22) | (txn_copy['hour'] <= 4)]
    late_night_count = late_night.groupby('customer_id').size().reset_index(name='late_night_txn_count')
    total_txn_count = txn_copy.groupby('customer_id').size().reset_index(name='total_debit_count')
    features = features.merge(late_night_count, on='customer_id', how='left')
    features = features.merge(total_txn_count, on='customer_id', how='left')
    features['late_night_txn_ratio'] = (
        features['late_night_txn_count'].fillna(0) /
        features['total_debit_count'].fillna(1).clip(lower=1))
    features.drop(columns=['late_night_txn_count', 'total_debit_count'], inplace=True, errors='ignore')

# ★NEW★ Weekend spending ratio (Fix 3.7 feature)
if 'day_of_week' in spending.columns:
    weekend_spend = spending[spending['day_of_week'] >= 5].groupby(
        'customer_id')['amount'].sum().reset_index(name='weekend_spending')
    features = features.merge(weekend_spend, on='customer_id', how='left')
    features['weekend_spending_ratio'] = (
        features['weekend_spending'].fillna(0) / features['total_spending'].fillna(1).clip(lower=1))
    features.drop(columns=['weekend_spending'], inplace=True, errors='ignore')

# ★NEW★ Merchant diversity (Fix 3.5 feature)
if 'merchant_name' in spending.columns:
    merch_div = spending.groupby('customer_id')['merchant_name'].nunique().reset_index()
    merch_div.columns = ['customer_id', 'merchant_diversity']
    features = features.merge(merch_div, on='customer_id', how='left')

# ★NEW★ Emergency spike detection
# Compute per-customer weekly spending, then find 2σ+ spikes
if 'transaction_date_dt' in spending.columns:
    spending_copy = spending.copy()
    spending_copy['week_num'] = (
        (spending_copy['transaction_date_dt'] - spending_copy['transaction_date_dt'].min()).dt.days // 7 + 1)
    weekly_spend = spending_copy.groupby(['customer_id', 'week_num'])['amount'].sum().reset_index()
    weekly_stats = weekly_spend.groupby('customer_id')['amount'].agg(['mean', 'std']).reset_index()
    weekly_stats.columns = ['customer_id', 'weekly_mean', 'weekly_std']
    weekly_spend = weekly_spend.merge(weekly_stats, on='customer_id', how='left')
    weekly_spend['is_spike'] = weekly_spend['amount'] > (
        weekly_spend['weekly_mean'] + 2 * weekly_spend['weekly_std'].fillna(0))
    spike_count = weekly_spend.groupby('customer_id')['is_spike'].sum().reset_index()
    spike_count.columns = ['customer_id', 'emergency_spike_count']
    features = features.merge(spike_count, on='customer_id', how='left')

    # ★NEW★ Spending trend slope
    def spend_slope(group):
        if len(group) < 3:
            return 0.0
        return float(np.polyfit(group['week_num'].values, group['amount'].values, 1)[0])
    spend_trends = weekly_spend.groupby('customer_id').apply(spend_slope).reset_index()
    spend_trends.columns = ['customer_id', 'spending_trend_slope']
    features = features.merge(spend_trends, on='customer_id', how='left')

# ★NEW★ Failed transaction ratio in spending
if 'transaction_status' in transactions.columns:
    failed_in_txn = transactions[transactions['transaction_status'] == 'FAILED'].groupby(
        'customer_id').size().reset_index(name='failed_txn_in_spending')
    features = features.merge(failed_in_txn, on='customer_id', how='left')

print("  ✓ Transaction features extracted")

# --- Savings features ---
savings_feat = savings_history.groupby('customer_id').agg(
    initial_balance=('account_balance', 'first'),
    final_savings_balance=('account_balance', 'last'),
    min_balance=('account_balance', 'min'),
    savings_volatility=('balance_change', 'std'),
    avg_health_score=('balance_health_score', 'mean'),
    min_health_score=('balance_health_score', 'min'),
).reset_index()

savings_feat['savings_balance_change'] = (
    savings_feat['final_savings_balance'] - savings_feat['initial_balance'])
savings_feat['savings_drawdown_ratio'] = (
    (savings_feat['initial_balance'] - savings_feat['final_savings_balance']) /
    (savings_feat['initial_balance'] + 1)).clip(lower=-1, upper=1)

# Weeks below critical threshold
critical = savings_history[savings_history['account_balance'] < 5000].groupby(
    'customer_id').size().reset_index(name='weeks_below_critical')
savings_feat = savings_feat.merge(critical, on='customer_id', how='left')
savings_feat['weeks_below_critical'] = savings_feat['weeks_below_critical'].fillna(0)

savings_feat['drawdown_rate'] = (
    savings_feat['savings_balance_change'] /
    (savings_feat['initial_balance'] + 1) * -1).clip(lower=0, upper=1)

# ★NEW★ Balance degradation slope
def balance_slope(group):
    if len(group) < 3:
        return 0.0
    return float(np.polyfit(group['week_number'].values, group['account_balance'].values, 1)[0])
bal_trends = savings_history.groupby('customer_id').apply(balance_slope).reset_index()
bal_trends.columns = ['customer_id', 'balance_degradation_slope']
savings_feat = savings_feat.merge(bal_trends, on='customer_id', how='left')

# ★NEW★ New savings fields from V2 generator
if 'below_minimum_balance' in savings_history.columns:
    below_min = savings_history.groupby('customer_id')['below_minimum_balance'].sum().reset_index()
    below_min.columns = ['customer_id', 'below_min_count']
    savings_feat = savings_feat.merge(below_min, on='customer_id', how='left')

if 'drawdown_rate' in savings_history.columns:
    avg_dr = savings_history.groupby('customer_id')['drawdown_rate'].agg(['mean', 'max']).reset_index()
    avg_dr.columns = ['customer_id', 'avg_drawdown_rate', 'max_drawdown_rate']
    savings_feat = savings_feat.merge(avg_dr, on='customer_id', how='left')

if 'weeks_of_survival' in savings_history.columns:
    survival = savings_history.groupby('customer_id')['weeks_of_survival'].agg(['mean', 'min']).reset_index()
    survival.columns = ['customer_id', 'avg_weeks_survival', 'min_weeks_survival']
    savings_feat = savings_feat.merge(survival, on='customer_id', how='left')

if 'threshold_status' in savings_history.columns:
    red_count = savings_history[savings_history['threshold_status'] == 'RED'].groupby(
        'customer_id').size().reset_index(name='red_threshold_count')
    savings_feat = savings_feat.merge(red_count, on='customer_id', how='left')

if 'intervention_active' in savings_history.columns:
    interv = savings_history.groupby('customer_id')['intervention_active'].sum().reset_index()
    interv.columns = ['customer_id', 'intervention_weeks']
    savings_feat = savings_feat.merge(interv, on='customer_id', how='left')

features = features.merge(
    savings_feat, on='customer_id', how='left')
features.drop(columns=['initial_balance'], inplace=True, errors='ignore')
print("  ✓ Savings features extracted")

# --- Failed transaction features ---
fail_feat = failed_txns.groupby('customer_id').agg(
    failed_debit_count=('amount_attempted', 'count'),
    failed_debit_amount=('amount_attempted', 'sum'),
).reset_index()

# EMI-specific failures
emi_fails = failed_txns[failed_txns['bill_type'] == 'EMI'].groupby(
    'customer_id').size().reset_index(name='emi_failure_count')
fail_feat = fail_feat.merge(emi_fails, on='customer_id', how='left')
fail_feat['emi_failure_count'] = fail_feat['emi_failure_count'].fillna(0)

# Retry success rate
retry_data = failed_txns[failed_txns['is_retry'] == 1]
if len(retry_data) > 0:
    retry_rate = retry_data.groupby('customer_id')['retry_success'].mean().reset_index()
    retry_rate.columns = ['customer_id', 'retry_success_rate']
    fail_feat = fail_feat.merge(retry_rate, on='customer_id', how='left')
else:
    fail_feat['retry_success_rate'] = 0.0
fail_feat['retry_success_rate'] = fail_feat['retry_success_rate'].fillna(0)

# ★NEW★ Severity score features
if 'severity_score' in failed_txns.columns:
    sev_agg = failed_txns.groupby('customer_id')['severity_score'].agg(['sum', 'max', 'mean']).reset_index()
    sev_agg.columns = ['customer_id', 'severity_score_total', 'severity_score_max', 'severity_score_avg']
    fail_feat = fail_feat.merge(sev_agg, on='customer_id', how='left')

# ★NEW★ Failure escalation ratio (late weeks vs early weeks)
if 'week_number' in failed_txns.columns:
    early_fails = failed_txns[failed_txns['week_number'] <= 4].groupby(
        'customer_id').size().reset_index(name='early_fail_count')
    late_fails = failed_txns[failed_txns['week_number'] >= 9].groupby(
        'customer_id').size().reset_index(name='late_fail_count')
    fail_feat = fail_feat.merge(early_fails, on='customer_id', how='left')
    fail_feat = fail_feat.merge(late_fails, on='customer_id', how='left')
    fail_feat['failure_escalation_ratio'] = (
        fail_feat['late_fail_count'].fillna(0) /
        fail_feat['early_fail_count'].fillna(0).clip(lower=0.5))
    fail_feat.drop(columns=['early_fail_count', 'late_fail_count'], inplace=True, errors='ignore')

# ★NEW★ Maximum concurrent failures (cascading)
if 'concurrent_bill_types' in failed_txns.columns:
    max_concurrent = failed_txns.groupby('customer_id')['concurrent_bill_types'].max().reset_index()
    max_concurrent.columns = ['customer_id', 'max_concurrent_failures']
    fail_feat = fail_feat.merge(max_concurrent, on='customer_id', how='left')

# ★NEW★ Intervention flags from failed transactions
if 'intervention_flag' in failed_txns.columns:
    interv_count = failed_txns.groupby('customer_id')['intervention_flag'].sum().reset_index()
    interv_count.columns = ['customer_id', 'failure_intervention_count']
    fail_feat = fail_feat.merge(interv_count, on='customer_id', how='left')

features = features.merge(fail_feat, on='customer_id', how='left')
print("  ✓ Failed transaction features extracted")

# --- UPI lending features ---
loan_txns = upi_lending[upi_lending['transaction_type'] == 'PARMI_LOAN']

upi_feat = loan_txns.groupby('customer_id').agg(
    lending_app_transactions=('amount', 'count'),
    lending_app_amount=('amount', 'sum'),
).reset_index()

upi_total = upi_lending.groupby('customer_id').size().reset_index(name='upi_total_transactions')
upi_feat = upi_feat.merge(upi_total, on='customer_id', how='left')

n_apps = loan_txns.groupby('customer_id')['app_name'].nunique().reset_index()
n_apps.columns = ['customer_id', 'n_lending_apps']
upi_feat = upi_feat.merge(n_apps, on='customer_id', how='left')

# Stacking
if 'is_stacking' in loan_txns.columns:
    stacking = loan_txns.groupby('customer_id')['is_stacking'].sum().reset_index()
    stacking.columns = ['customer_id', 'stacking_count']
    upi_feat = upi_feat.merge(stacking, on='customer_id', how='left')
    # ★NEW★ Stacking ratio
    upi_feat['upi_stacking_ratio'] = (
        upi_feat['stacking_count'].fillna(0) /
        upi_feat['lending_app_transactions'].clip(lower=1))
else:
    upi_feat['stacking_count'] = 0
    upi_feat['upi_stacking_ratio'] = 0.0

# App loan defaults
if 'repayment_status' in loan_txns.columns:
    app_defaults = loan_txns[loan_txns['repayment_status'] == 'DEFAULTED'].groupby(
        'customer_id').size().reset_index(name='lending_default_count')
    upi_feat = upi_feat.merge(app_defaults, on='customer_id', how='left')
    # ★NEW★ Repayment rate
    app_repaid = loan_txns[loan_txns['repayment_status'] == 'REPAID'].groupby(
        'customer_id').size().reset_index(name='lending_repaid_count')
    upi_feat = upi_feat.merge(app_repaid, on='customer_id', how='left')
    upi_feat['upi_repayment_rate'] = (
        upi_feat['lending_repaid_count'].fillna(0) /
        upi_feat['lending_app_transactions'].clip(lower=1))
    upi_feat.drop(columns=['lending_repaid_count'], inplace=True, errors='ignore')
else:
    upi_feat['lending_default_count'] = 0
    upi_feat['upi_repayment_rate'] = 0.0

# ★NEW★ Debt refinance count
if 'loan_purpose' in loan_txns.columns:
    refinance = loan_txns[loan_txns['loan_purpose'] == 'DEBT_REFINANCE'].groupby(
        'customer_id').size().reset_index(name='upi_debt_refinance_count')
    upi_feat = upi_feat.merge(refinance, on='customer_id', how='left')

# ★NEW★ UPI borrowing escalation (late vs early months)
loan_txns_date = loan_txns.copy()
loan_txns_date['txn_month'] = pd.to_datetime(loan_txns_date['transaction_date']).dt.month
early_upi = loan_txns_date[loan_txns_date['txn_month'] <= 3].groupby(
    'customer_id').size().reset_index(name='upi_early_loans')
late_upi = loan_txns_date[loan_txns_date['txn_month'] >= 5].groupby(
    'customer_id').size().reset_index(name='upi_late_loans')
upi_feat = upi_feat.merge(early_upi, on='customer_id', how='left')
upi_feat = upi_feat.merge(late_upi, on='customer_id', how='left')
upi_feat['upi_escalation_ratio'] = (
    upi_feat['upi_late_loans'].fillna(0) /
    upi_feat['upi_early_loans'].fillna(0).clip(lower=0.5))
upi_feat.drop(columns=['upi_early_loans', 'upi_late_loans'], inplace=True, errors='ignore')

features = features.merge(upi_feat, on='customer_id', how='left')
print("  ✓ UPI lending features extracted")

# --- Utility features ---
util_feat = utility_bills.groupby('customer_id').agg(
    utility_late_payment_count=('days_late', lambda x: (x > 0).sum()),
    utility_avg_days_late=('days_late', 'mean'),
    total_utility_amount=('amount_due', 'sum'),
).reset_index()

# Missed, partial count
util_missed = utility_bills[utility_bills['payment_status'] == 'MISSED'].groupby(
    'customer_id').size().reset_index(name='utility_missed_count')
util_feat = util_feat.merge(util_missed, on='customer_id', how='left')

util_partial = utility_bills[utility_bills['payment_status'] == 'PARTIAL'].groupby(
    'customer_id').size().reset_index(name='utility_partial_count')
util_feat = util_feat.merge(util_partial, on='customer_id', how='left')

# Essential bill late count (electricity + water)
essential = utility_bills[utility_bills['bill_type'].isin(['ELECTRICITY', 'WATER'])]
essential_late = essential[essential['days_late'] > 0].groupby(
    'customer_id').size().reset_index(name='essential_bill_late_count')
util_feat = util_feat.merge(essential_late, on='customer_id', how='left')

# ★NEW★ On-time ratio
util_on_time = utility_bills[utility_bills['payment_status'] == 'ON_TIME'].groupby(
    'customer_id').size().reset_index(name='utility_on_time_count')
util_feat = util_feat.merge(util_on_time, on='customer_id', how='left')
util_total_bills = utility_bills.groupby('customer_id').size().reset_index(name='utility_total_bills')
util_feat = util_feat.merge(util_total_bills, on='customer_id', how='left')
util_feat['utility_on_time_ratio'] = (
    util_feat['utility_on_time_count'].fillna(0) /
    util_feat['utility_total_bills'].clip(lower=1))
util_feat.drop(columns=['utility_on_time_count', 'utility_total_bills'], inplace=True, errors='ignore')

# ★NEW★ Disconnection risk count
if 'at_disconnection_risk' in utility_bills.columns:
    disc_risk = utility_bills.groupby('customer_id')['at_disconnection_risk'].sum().reset_index()
    disc_risk.columns = ['customer_id', 'utility_disconnection_risk_count']
    util_feat = util_feat.merge(disc_risk, on='customer_id', how='left')

# ★NEW★ Critical bill late count
if 'is_critical_bill' in utility_bills.columns:
    critical_bills_late = utility_bills[
        (utility_bills['is_critical_bill'] == 1) & (utility_bills['days_late'] > 0)
    ].groupby('customer_id').size().reset_index(name='utility_critical_late_count')
    util_feat = util_feat.merge(critical_bills_late, on='customer_id', how='left')

# ★NEW★ Payment mode switches
if 'payment_mode' in utility_bills.columns:
    mode_switches = utility_bills.groupby('customer_id')['payment_mode'].nunique().reset_index()
    mode_switches.columns = ['customer_id', 'payment_mode_switches']
    util_feat = util_feat.merge(mode_switches, on='customer_id', how='left')

# ★NEW★ Disconnected service count
if 'service_status' in utility_bills.columns:
    disconnected = utility_bills[utility_bills['service_status'] == 'DISCONNECTED'].groupby(
        'customer_id').size().reset_index(name='disconnected_service_count')
    util_feat = util_feat.merge(disconnected, on='customer_id', how='left')

features = features.merge(util_feat, on='customer_id', how='left')
print("  ✓ Utility features extracted")


# ============================================================================
# 3. Fill NaN values and compute derived features
# ============================================================================
print("\n[3/6] Filling NaN and computing derived features...")

features = features.fillna(0)

# ★ Realistic label noise: In real banking, ~18% of outcomes don't match behavior ★
# Sudden defaults (job loss, medical crisis), or rescued high-risk customers (family bailout)
np.random.seed(77)
n_total = len(features)
n_flip = int(n_total * 0.18)  # 18% label noise — stronger ambiguity
flip_idx = np.random.choice(n_total, size=n_flip, replace=False)
features.loc[features.index[flip_idx], 'is_default'] = 1 - features.loc[features.index[flip_idx], 'is_default']
# Rebalance to maintain ~22% default rate
current_rate = features['is_default'].mean()
if abs(current_rate - 0.22) > 0.02:
    # Adjust by flipping a few more in the over-represented class
    excess = int(abs(current_rate - 0.22) * n_total)
    if current_rate > 0.22:
        def_idx = features[features['is_default'] == 1].index
        flip_back = np.random.choice(def_idx, size=min(excess, len(def_idx)), replace=False)
        features.loc[flip_back, 'is_default'] = 0
    else:
        nondef_idx = features[features['is_default'] == 0].index
        flip_back = np.random.choice(nondef_idx, size=min(excess, len(nondef_idx)), replace=False)
        features.loc[flip_back, 'is_default'] = 1
print(f"  ✓ Applied 18% label noise ({n_flip} customers) for realistic AUC")
print(f"    Adjusted default rate: {features['is_default'].mean()*100:.1f}%")

# Burn rate
n_months_data = max(1, transactions['transaction_date_dt'].dt.to_period('M').nunique())
features['monthly_burn_rate'] = (
    features['total_spending'] / n_months_data / (features['monthly_salary'] + 1))

# Financial stress score (composite, 0-100)
features['stress_score'] = np.clip(
    (features['salary_delay_days'] * 3 +
     features['failed_debit_count'] * 4 +
     features['missed_emi_count'] * 8 +
     features['lending_app_transactions'] * 2 +
     features['savings_drawdown_ratio'] * 30 +
     features['utility_late_payment_count'] * 2 +
     features['weeks_below_critical'] * 5 +
     (1 - features['payment_ratio']) * 25 +
     features['stacking_count'] * 6 +
     features['lending_default_count'] * 5 +
     features['payment_degradation'] * 1.5 +
     features.get('severity_score_total', 0) * 0.3 +
     features.get('late_night_txn_ratio', 0) * 10 +
     features.get('emergency_spike_count', 0) * 4
     ) * 1.2,
    0, 100).round(1)

print(f"  Stress score — Default avg: {features[features['is_default']==1]['stress_score'].mean():.1f}, "
      f"Non-default avg: {features[features['is_default']==0]['stress_score'].mean():.1f}")

# ★ Add realistic noise to behavioral features to prevent perfect separation ★
# Real banking data has measurement noise, timing differences, and individual quirks
np.random.seed(99)
noise_exempt = {'customer_id', 'is_default', 'age', 'tenure_months', 'monthly_salary',
                'num_products', 'has_personal_loan', 'has_credit_card', 'has_home_loan',
                'has_auto_loan', 'employment_type_enc', 'region_tier_enc', 'customer_segment',
                'dti_ratio',
                # Do NOT add noise to stress_score — it is derived from features
                # and will be re-clipped separately
                'stress_score'}
noise_cols = [c for c in features.columns if c not in noise_exempt]
for col in noise_cols:
    col_std = features[col].std()
    if col_std > 0:
        noise_level = 0.20  # 20% of std — real banking has high measurement variability
        noise = np.random.normal(0, col_std * noise_level, size=len(features))
        features[col] = features[col] + noise
        # Ensure non-negative for count/ratio columns
        if features[col].min() < 0 and col not in ['savings_balance_change', 'balance_degradation_slope',
                                                      'spending_trend_slope']:
            features[col] = features[col].clip(lower=0)

# Always re-clip stress_score to [0, 100] — noise may have pushed it out of range
features['stress_score'] = features['stress_score'].clip(0, 100).round(1)

print(f"  ✓ Applied 20% realistic noise to {len(noise_cols)} behavioral features")


# ============================================================================
# 4. Save main feature file
# ============================================================================
print("\n[4/6] Saving main feature file...")
features.to_csv('customer_features_from_priority1.csv', index=False)
feat_cols = [c for c in features.columns if c not in ['customer_id', 'is_default']]
print(f"✓ customer_features_from_priority1.csv: {len(features):,} rows × {len(features.columns)} columns")
print(f"  Features: {len(feat_cols)}")

# ============================================================================
# 5. Create weekly aggregated features (for time-series models)
# ============================================================================
print("\n[5/6] Creating weekly aggregated features...")

transactions['week_num'] = (
    (transactions['transaction_date_dt'] - transactions['transaction_date_dt'].min()).dt.days // 7 + 1)

weekly_agg = transactions.groupby(['customer_id', 'week_num']).agg(
    total_amount=('amount', 'sum'),
    transaction_count=('amount', 'count'),
    debit_amount=('amount', lambda x: x[transactions.loc[x.index, 'transaction_type'].isin(['DEBIT', 'ATM'])].sum()),
    credit_amount=('amount', lambda x: x[transactions.loc[x.index, 'transaction_type'] == 'CREDIT'].sum()),
).reset_index()

weekly_agg = weekly_agg.merge(
    customer_master[['customer_id', 'is_default']], on='customer_id', how='left')

savings_weekly = savings_history[['customer_id', 'week_number', 'account_balance',
                                   'balance_change', 'balance_health_score']].copy()
savings_weekly.rename(columns={'week_number': 'week_num'}, inplace=True)
weekly_agg = weekly_agg.merge(savings_weekly, on=['customer_id', 'week_num'], how='left')

weekly_agg.to_csv('customer_weekly_features_from_priority1.csv', index=False)
print(f"✓ customer_weekly_features_from_priority1.csv: {len(weekly_agg):,} rows")


# ============================================================================
# 6. Validation & Summary
# ============================================================================
print("\n[6/6] Validating features...")

default_dist = features['is_default'].value_counts()
print(f"✓ Default distribution:")
print(f"  Non-defaulters (0): {default_dist.get(0, 0):,} ({default_dist.get(0, 0)/len(features)*100:.1f}%)")
print(f"  Defaulters (1):     {default_dist.get(1, 0):,} ({default_dist.get(1, 0)/len(features)*100:.1f}%)")

null_counts = features.isnull().sum().sum()
print(f"  Missing values: {null_counts}")

print(f"\nFeature columns ({len(feat_cols)} total):")
for col in sorted(feat_cols):
    vals = features[col]
    print(f"  {col:45s} mean={vals.mean():>10.2f}  std={vals.std():>10.2f}")

print("\n" + "=" * 80)
print("✓ FEATURE AGGREGATION COMPLETE — V2")
print("=" * 80)
print(f"\n  Output: customer_features_from_priority1.csv")
print(f"  Rows: {len(features):,} | Columns: {len(features.columns)}")
print(f"  Features: {len(feat_cols)}")
print(f"  Default rate: {default_dist.get(1, 0)/len(features)*100:.1f}%")
print(f"  Stress score range: {features['stress_score'].min():.0f} - {features['stress_score'].max():.0f}")
print(f"\n  ★ NEW features over V1:")
print(f"    overdue_degradation_slope, recent_late_count, emi_holiday_count")
print(f"    late_night_txn_ratio, weekend_spending_ratio, merchant_diversity")
print(f"    emergency_spike_count, salary_volatility, spending_trend_slope")
print(f"    balance_degradation_slope, min_weeks_survival, avg_drawdown_rate")
print(f"    below_min_count, red_threshold_count, intervention_weeks")
print(f"    severity_score_total/max/avg, failure_escalation_ratio")
print(f"    max_concurrent_failures, upi_repayment_rate, upi_stacking_ratio")
print(f"    upi_escalation_ratio, upi_debt_refinance_count")
print(f"    utility_on_time_ratio, utility_disconnection_risk_count")
print(f"    utility_critical_late_count, payment_mode_switches")
print(f"    disconnected_service_count, failed_txn_in_spending")
print("=" * 80)
