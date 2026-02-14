"""
PRIORITY 1: Generate ALL Required Synthetic Data (₹ In Indian Rupees)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generates 7 complete datasets matching PRIORITY 1 requirements:
1. Transaction History (80K+ daily transactions)
2. EMI/Payment Records (10K loans with monthly payments)
3. Savings Balance History (50K weekly snapshots)
4. Customer Master Data (10K demographics)
5. Failed Transactions Log (5K-10K failures)
6. UPI/Lending Transactions (20K payday loans)
7. Utility Bill Payments (20K utility records)

All in INDIAN RUPEES (₹) with realistic patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import random
warnings.filterwarnings('ignore')

print("=" * 80)
print("GENERATING PRIORITY 1 DATASETS (INDIAN RUPEES)")
print("=" * 80)

# Configuration
N_CUSTOMERS = 10000
DEFAULT_RATE = 0.22  # 22% default rate
DEFAULT_COUNT = int(N_CUSTOMERS * DEFAULT_RATE)
NON_DEFAULT_COUNT = N_CUSTOMERS - DEFAULT_COUNT

# Use fixed random seed for reproducibility
np.random.seed(42)

# ============================================================================
# Create is_default CORRECTLY (as boolean, not index-based)
# ============================================================================
print("\n[1/7] Creating customer is_default labels (boolean)...")

is_default_array = np.concatenate([
    np.ones(DEFAULT_COUNT, dtype=int),      # 2,200 defaulters
    np.zeros(NON_DEFAULT_COUNT, dtype=int)  # 7,800 non-defaulters
])
np.random.shuffle(is_default_array)

customer_ids = np.arange(1, N_CUSTOMERS + 1)
print(f"✓ Created: {DEFAULT_COUNT} defaulters + {NON_DEFAULT_COUNT} non-defaulters")
print(f"  Defaulters: {is_default_array.sum()} (binary=1)")
print(f"  Non-defaulters: {(1-is_default_array).sum()} (binary=0)")

# ============================================================================
# DATASET 1: CUSTOMER MASTER DATA
# ============================================================================
print("\n[2/7] Generating Customer Master Data...")

geographies = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 
               'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow']
segments = ['PREMIUM', 'STANDARD', 'RISK']
products_held = [['loan', 'credit_card'], ['loan'], ['credit_card'], 
                 ['loan', 'credit_card', 'savings'], ['loan', 'savings']]

customer_master = pd.DataFrame({
    'customer_id': customer_ids,
    'age': np.random.randint(25, 60, N_CUSTOMERS),
    'salary_deposit_day': np.random.choice([25, 30], N_CUSTOMERS),
    'geography': np.random.choice(geographies, N_CUSTOMERS),
    'customer_segment': np.random.choice(segments, N_CUSTOMERS),
    'products_held': [str(random.choice(products_held)) for _ in range(N_CUSTOMERS)],
    'is_default': is_default_array
})

# Monthly salary for defaulters: lower and more variable
customer_master['monthly_salary_rupees'] = np.where(
    is_default_array == 1,
    np.random.randint(25000, 70000, N_CUSTOMERS),  # Defaulters: 25K-70K/month
    np.random.randint(40000, 150000, N_CUSTOMERS)  # Non-defaulters: 40K-150K/month
)

customer_master.to_csv('customer_master.csv', index=False)
print(f"✓ Generated: customer_master.csv ({len(customer_master)} rows)")
print(f"  Sample salary ranges:")
print(f"  - Defaulters: ₹{customer_master[is_default_array==1]['monthly_salary_rupees'].min():,} - ₹{customer_master[is_default_array==1]['monthly_salary_rupees'].max():,}")
print(f"  - Non-defaulters: ₹{customer_master[is_default_array==0]['monthly_salary_rupees'].min():,} - ₹{customer_master[is_default_array==0]['monthly_salary_rupees'].max():,}")

# ============================================================================
# DATASET 2: EMI/PAYMENT RECORDS
# ============================================================================
print("\n[3/7] Generating EMI/Payment Records...")

emi_records = []
base_date = datetime(2024, 1, 1)

for idx, cust_id in enumerate(customer_ids):
    is_default = is_default_array[idx]
    salary = customer_master.loc[idx, 'monthly_salary_rupees']
    salary_day = customer_master.loc[idx, 'salary_deposit_day']
    
    # EMI amount: 30-50% of salary for non-defaulters, 40-60% for defaulters
    if is_default == 0:
        emi_amount = int(salary * np.random.uniform(0.30, 0.45))
    else:
        emi_amount = int(salary * np.random.uniform(0.40, 0.60))
    
    num_loans = np.random.randint(1, 3)  # 1-2 loans per customer
    
    for loan_num in range(num_loans):
        loan_id = f"loan_{cust_id}_{loan_num}"
        
        # Generate 5 months of EMI records
        for month in range(5):
            emi_due_date = base_date + timedelta(days=30*month)
            emi_due_date = emi_due_date.replace(day=salary_day)
            
            if is_default == 1:
                # Defaulters show pattern: on-time → late → failed → missed
                if month <= 1:
                    payment_status = 'ON_TIME'
                    actual_payment_date = emi_due_date
                    days_overdue = 0
                    failed_reason = None
                elif month == 2:
                    payment_status = 'LATE'
                    days_overdue = np.random.randint(5, 15)
                    actual_payment_date = emi_due_date + timedelta(days=days_overdue)
                    failed_reason = None
                elif month == 3:
                    payment_status = 'FAILED_DEBIT'
                    days_overdue = np.random.randint(10, 30)
                    actual_payment_date = emi_due_date + timedelta(days=days_overdue)
                    failed_reason = np.random.choice(['INSUFFICIENT_FUNDS', 'AUTO_DEBIT_FAILURE', 'DECLINED_CARD'])
                else:
                    payment_status = 'MISSED'
                    days_overdue = np.random.randint(30, 90)
                    actual_payment_date = emi_due_date + timedelta(days=days_overdue)
                    failed_reason = 'MISSED_PAYMENT'
            else:
                # Non-defaulters: mostly on-time with occasional late
                if np.random.random() > 0.95:  # 5% late
                    payment_status = 'LATE'
                    days_overdue = np.random.randint(1, 5)
                    actual_payment_date = emi_due_date + timedelta(days=days_overdue)
                    failed_reason = None
                else:
                    payment_status = 'ON_TIME'
                    actual_payment_date = emi_due_date
                    days_overdue = 0
                    failed_reason = None
            
            emi_records.append({
                'customer_id': cust_id,
                'loan_id': loan_id,
                'emi_due_date': emi_due_date.strftime('%Y-%m-%d'),
                'emi_amount': emi_amount,
                'actual_payment_date': actual_payment_date.strftime('%Y-%m-%d'),
                'payment_status': payment_status,
                'days_overdue': days_overdue,
                'payment_failed_reason': failed_reason
            })

emi_df = pd.DataFrame(emi_records)
emi_df.to_csv('emi_payment_records.csv', index=False)
print(f"✓ Generated: emi_payment_records.csv ({len(emi_df)} rows)")
print(f"  Payment statuses: {emi_df['payment_status'].value_counts().to_dict()}")
print(f"  Average EMI: ₹{emi_df['emi_amount'].mean():,.0f}")

# ============================================================================
# DATASET 3: TRANSACTION HISTORY (Daily transactions)
# ============================================================================
print("\n[4/7] Generating Transaction History...")

transactions = []
merchant_categories = ['SALARY', 'UTILITY', 'DINING', 'ENTERTAINMENT', 'ATM', 'UPI_LENDING', 'SHOPPING', 'TRANSFER']

for idx, cust_id in enumerate(customer_ids):
    is_default = is_default_array[idx]
    salary = customer_master.loc[idx, 'monthly_salary_rupees']
    salary_day = customer_master.loc[idx, 'salary_deposit_day']
    
    # Generate transactions for 5 weeks
    for week in range(5):
        week_start = base_date + timedelta(days=7*week)
        
        # Salary deposit (on salary day)
        salary_date = week_start.replace(day=salary_day)
        if is_default == 1 and week >= 2:
            # Defaulters: salary comes late (after day 10-20)
            salary_date = salary_date + timedelta(days=np.random.randint(10, 20))
        
        if salary_date >= week_start and salary_date < week_start + timedelta(days=7):
            transactions.append({
                'customer_id': cust_id,
                'transaction_date': salary_date.strftime('%Y-%m-%d'),
                'transaction_type': 'CREDIT',
                'amount': int(salary * np.random.uniform(0.95, 1.05)),  # Slight variation
                'merchant_category': 'SALARY',
                'reference_id': f"TXN_{cust_id}_{salary_date.strftime('%Y%m%d')}_SALARY"
            })
        
        # Utility bills (random day, fixed amount)
        if is_default == 1:
            # Defaulters: skip utilities or pay late
            if np.random.random() > 0.4:
                continue
            utility_amount = np.random.randint(1500, 5000)
        else:
            utility_amount = np.random.randint(1500, 3500)
        
        utility_date = week_start + timedelta(days=np.random.randint(0, 7))
        transactions.append({
            'customer_id': cust_id,
            'transaction_date': utility_date.strftime('%Y-%m-%d'),
            'transaction_type': 'DEBIT',
            'amount': utility_amount,
            'merchant_category': 'UTILITY',
            'reference_id': f"TXN_{cust_id}_{utility_date.strftime('%Y%m%d')}_UTIL"
        })
        
        # Dining & Entertainment
        if is_default == 1 and week >= 3:
            # Defaulters reduce discretionary spending in week 3+
            num_transactions = np.random.randint(0, 2)
        else:
            num_transactions = np.random.randint(2, 5)
        
        for _ in range(num_transactions):
            tx_date = week_start + timedelta(days=np.random.randint(0, 7))
            category = np.random.choice(['DINING', 'ENTERTAINMENT', 'SHOPPING'])
            amount = np.random.randint(500, 5000)
            
            transactions.append({
                'customer_id': cust_id,
                'transaction_date': tx_date.strftime('%Y-%m-%d'),
                'transaction_type': 'DEBIT',
                'amount': amount,
                'merchant_category': category,
                'reference_id': f"TXN_{cust_id}_{tx_date.strftime('%Y%m%d')}_{category}"
            })
        
        # ATM Withdrawals
        num_atm = np.random.randint(0, 3) if is_default == 0 else np.random.randint(2, 8)
        for _ in range(num_atm):
            atm_date = week_start + timedelta(days=np.random.randint(0, 7))
            atm_amount = np.random.randint(2000, 10000)
            
            transactions.append({
                'customer_id': cust_id,
                'transaction_date': atm_date.strftime('%Y-%m-%d'),
                'transaction_type': 'ATM',
                'amount': atm_amount,
                'merchant_category': 'ATM',
                'reference_id': f"TXN_{cust_id}_{atm_date.strftime('%Y%m%d')}_ATM"
            })

transactions_df = pd.DataFrame(transactions)
transactions_df.to_csv('transaction_history.csv', index=False)
print(f"✓ Generated: transaction_history.csv ({len(transactions_df)} rows)")
print(f"  Categories: {transactions_df['merchant_category'].value_counts().to_dict()}")

# ============================================================================
# DATASET 4: SAVINGS BALANCE HISTORY
# ============================================================================
print("\n[5/7] Generating Savings Balance History...")

savings_records = []

for idx, cust_id in enumerate(customer_ids):
    is_default = is_default_array[idx]
    salary = customer_master.loc[idx, 'monthly_salary_rupees']
    
    # Starting balance
    if is_default == 0:
        balance = np.random.randint(int(salary*2), int(salary*5))  # 2-5 months
    else:
        balance = np.random.randint(int(salary*0.5), int(salary*1.5))  # 0.5-1.5 months
    
    # Weekly snapshots for 5 weeks
    for week in range(5):
        snapshot_date = base_date + timedelta(days=7*week)
        
        if is_default == 1:
            # Defaulters: rapid balance drawdown
            balance = balance - np.random.randint(int(salary*0.1), int(salary*0.3))
        else:
            # Non-defaulters: stable or slight increase
            balance = balance + np.random.randint(-int(salary*0.05), int(salary*0.1))
        
        balance = max(0, balance)  # Can't go negative
        
        savings_records.append({
            'customer_id': cust_id,
            'balance_date': snapshot_date.strftime('%Y-%m-%d'),
            'account_balance': int(balance)
        })

savings_df = pd.DataFrame(savings_records)
savings_df.to_csv('savings_balance_history.csv', index=False)
print(f"✓ Generated: savings_balance_history.csv ({len(savings_df)} rows)")
print(f"  Average balance:")
print(f"  - Defaulters: ₹{savings_df[savings_df['customer_id'].isin(customer_ids[is_default_array==1])]['account_balance'].mean():,.0f}")
print(f"  - Non-defaulters: ₹{savings_df[savings_df['customer_id'].isin(customer_ids[is_default_array==0])]['account_balance'].mean():,.0f}")

# ============================================================================
# DATASET 5: FAILED TRANSACTIONS
# ============================================================================
print("\n[6/7] Generating Failed Transactions Log...")

failed_txns = []
failure_types = ['AUTO_DEBIT_FAILURE', 'DECLINED_CARD', 'INSUFFICIENT_FUNDS']
reason_codes = ['INSUFFICIENT_FUNDS', 'CARD_BLOCKED', 'LIMIT_EXCEEDED', 'NETWORK_ERROR', 'DUPLICATE_TXN']

for idx, cust_id in enumerate(customer_ids):
    is_default = is_default_array[idx]
    salary = customer_master.loc[idx, 'monthly_salary_rupees']
    
    # Defaulters have 5-15 failed txns, non-defaulters have 0-2
    num_failures = np.random.randint(5, 15) if is_default == 1 else np.random.randint(0, 2)
    
    for _ in range(num_failures):
        failure_date = base_date + timedelta(days=np.random.randint(0, 35))
        amount_attempted = np.random.randint(int(salary*0.1), int(salary*0.8))
        
        failed_txns.append({
            'customer_id': cust_id,
            'failure_date': failure_date.strftime('%Y-%m-%d'),
            'failure_type': np.random.choice(failure_types),
            'amount_attempted': amount_attempted,
            'reason_code': np.random.choice(reason_codes)
        })

failed_df = pd.DataFrame(failed_txns)
failed_df.to_csv('failed_transactions.csv', index=False)
print(f"✓ Generated: failed_transactions.csv ({len(failed_df)} rows)")
print(f"  Failure types: {failed_df['failure_type'].value_counts().to_dict()}")

# ============================================================================
# DATASET 6: UPI/LENDING TRANSACTIONS
# ============================================================================
print("\n[7/7] Generating UPI/Lending Transactions...")

upi_records = []
app_names = ['PayTM', 'PhonePe', 'GooglePay', 'Cashapp', 'Insta-borrow', 'MoneyView']
txn_types = ['PAYMENT', 'PARMI_LOAN']

for idx, cust_id in enumerate(customer_ids):
    is_default = is_default_array[idx]
    salary = customer_master.loc[idx, 'monthly_salary_rupees']
    
    # Defaulters use more lending apps (sign of financial stress)
    num_txns = np.random.randint(15, 40) if is_default == 1 else np.random.randint(3, 15)
    
    for _ in range(num_txns):
        txn_date = base_date + timedelta(days=np.random.randint(0, 35))
        amount = np.random.randint(1000, 30000)
        app = np.random.choice(app_names)
        
        # Defaulters use more loans (PARMI_LOAN), non-defaulters use payments
        if is_default == 1:
            txn_type = np.random.choice(txn_types, p=[0.3, 0.7])  # 70% loans
        else:
            txn_type = np.random.choice(txn_types, p=[0.9, 0.1])  # 10% loans
        
        upi_records.append({
            'customer_id': cust_id,
            'transaction_date': txn_date.strftime('%Y-%m-%d'),
            'app_name': app,
            'amount': amount,
            'transaction_type': txn_type
        })

upi_df = pd.DataFrame(upi_records)
upi_df.to_csv('upi_lending_transactions.csv', index=False)
print(f"✓ Generated: upi_lending_transactions.csv ({len(upi_df)} rows)")
print(f"  Transaction types: {upi_df['transaction_type'].value_counts().to_dict()}")
print(f"  Avg transaction: ₹{upi_df['amount'].mean():,.0f}")

# ============================================================================
# DATASET 7: UTILITY BILL PAYMENTS
# ============================================================================
print("\n[8/7] Generating Utility Bill Payments...")

utility_records = []
bill_types = ['ELECTRICITY', 'WATER', 'GAS', 'INTERNET', 'INSURANCE', 'PHONE']

for idx, cust_id in enumerate(customer_ids):
    is_default = is_default_array[idx]
    
    # Generate 5 bills per customer
    for bill_month in range(5):
        num_bills = np.random.randint(2, 5)
        
        for _ in range(num_bills):
            bill_type = np.random.choice(bill_types)
            bill_due_date = base_date + timedelta(days=30*bill_month + np.random.randint(0, 28))
            amount = np.random.randint(1000, 5000)
            
            if is_default == 1:
                # Defaulters: increasingly late payments
                days_late = np.random.randint(5, 60)
                actual_payment_date = (bill_due_date + timedelta(days=days_late)).strftime('%Y-%m-%d')
            else:
                # Non-defaulters: mostly on-time
                if np.random.random() > 0.95:
                    days_late = np.random.randint(0, 7)
                else:
                    days_late = 0
                actual_payment_date = (bill_due_date + timedelta(days=days_late)).strftime('%Y-%m-%d')
            
            utility_records.append({
                'customer_id': cust_id,
                'bill_type': bill_type,
                'bill_due_date': bill_due_date.strftime('%Y-%m-%d'),
                'actual_payment_date': actual_payment_date,
                'amount': amount,
                'days_late': days_late
            })

utility_df = pd.DataFrame(utility_records)
utility_df.to_csv('utility_bill_payments.csv', index=False)
print(f"✓ Generated: utility_bill_payments.csv ({len(utility_df)} rows)")
print(f"  Bill types: {utility_df['bill_type'].value_counts().to_dict()}")
print(f"  Average bill: ₹{utility_df['amount'].mean():,.0f}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("✓ ALL PRIORITY 1 DATASETS GENERATED SUCCESSFULLY")
print("=" * 80)
print("\nDataset Summary:")
print(f"  1. customer_master.csv ............ {len(customer_master):,} rows (Customer demographics)")
print(f"  2. emi_payment_records.csv ....... {len(emi_df):,} rows (Monthly EMI payments)")
print(f"  3. transaction_history.csv ....... {len(transactions_df):,} rows (Daily transactions)")
print(f"  4. savings_balance_history.csv ... {len(savings_df):,} rows (Weekly savings)")
print(f"  5. failed_transactions.csv ....... {len(failed_df):,} rows (Payment failures)")
print(f"  6. upi_lending_transactions.csv .. {len(upi_df):,} rows (UPI/Lending activity)")
print(f"  7. utility_bill_payments.csv ..... {len(utility_df):,} rows (Utility delays)")

print("\nKey Features:")
print(f"  • Currency: Indian Rupees (₹) throughout")
print(f"  • Customers: {N_CUSTOMERS:,} (2,200 defaulters, 7,800 non-defaulters)")
print(f"  • is_default: CORRECTLY stored as BOOLEAN (0/1), NOT as index")
print(f"  • Period: 5 weeks of transaction history")
print(f"  • Stress Patterns: Clear escalation for defaulters")
print(f"  • All datasets linked by customer_id")

print("\n" + "=" * 80)
