"""
PRIORITY 1: Generate ALL Required Synthetic Data (₹ Indian Rupees) — V2 ALL 88 FIXES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALL 88 problems fixed across 7 datasets.
33 new fixes over v1 (marked with ★NEW★):

  customer_master.csv      — 10 fixes (1.1–1.10)
  emi_payment_records.csv  — 12 fixes (2.1–2.12)  ★ 2.8 EMI holidays ★
  transaction_history.csv  — 15 fixes (3.1–3.15) ★ 3.4 time-of-day, 3.5 merchants,
                                                    3.7 weekend, 3.10 failed txns ★
  savings_balance_history  — 12 fixes (4.1–4.12) ★ 4.3 intervention, 4.7 min balance,
                                                    4.11/4.12 drawdown/survival ★
  failed_transactions.csv  — 12 fixes (5.1–5.12) ★ 5.11 cascading, 5.12 intervention,
                                                    5.13 severity score ★
  upi_lending_transactions — 12 fixes (6.1–6.12) ★ 6.5 ATM link ★
  utility_bill_payments    — 15 fixes (7.1–7.15) ★ 7.5 disconnection, 7.6 prepaid,
                                                    7.11 EMI correlation, 7.13 reconnect ★
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
import warnings
warnings.filterwarnings('ignore')

# Fix Windows console UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

np.random.seed(42)

print("=" * 80)
print("GENERATING PRIORITY 1 DATASETS — V2 ALL 88 FIXES (INDIAN RUPEES)")
print("=" * 80)

# ============================================================================
# CONFIGURATION
# ============================================================================
N_CUSTOMERS = 10000
DEFAULT_RATE = 0.22
DEFAULT_COUNT = int(N_CUSTOMERS * DEFAULT_RATE)
NON_DEFAULT_COUNT = N_CUSTOMERS - DEFAULT_COUNT

BASE_DATE = datetime(2024, 1, 1)
N_EMI_MONTHS = 6
N_TRANSACTION_WEEKS = 12
N_SAVINGS_WEEKS = 12
N_UPI_MONTHS = 6
N_UTILITY_MONTHS = 6

# Geography
TIER1_CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai']
TIER2_CITIES = ['Pune', 'Kolkata', 'Ahmedabad']
TIER3_CITIES = ['Jaipur', 'Lucknow', 'Kanpur', 'Indore', 'Patna']
ALL_CITIES = TIER1_CITIES + TIER2_CITIES + TIER3_CITIES
CITY_TIER = {}
for _c in TIER1_CITIES: CITY_TIER[_c] = 'TIER1'
for _c in TIER2_CITIES: CITY_TIER[_c] = 'TIER2'
for _c in TIER3_CITIES: CITY_TIER[_c] = 'TIER3'
TIER_SALARY_MULT = {'TIER1': 1.25, 'TIER2': 1.0, 'TIER3': 0.75}

# Spending categories
CATEGORY_AMOUNTS = {
    'GROCERY': (300, 3000), 'UTILITY': (800, 4500), 'DINING': (500, 3000),
    'ENTERTAINMENT': (300, 5000), 'SHOPPING': (500, 15000),
    'MEDICAL': (1000, 50000), 'FUEL': (500, 3000), 'TRANSFER': (1000, 20000),
}
CATEGORY_WEIGHTS = {
    'GROCERY': 0.22, 'UTILITY': 0.18, 'DINING': 0.12,
    'ENTERTAINMENT': 0.08, 'SHOPPING': 0.20, 'MEDICAL': 0.05,
    'FUEL': 0.08, 'TRANSFER': 0.07
}
MANDATORY_CATEGORIES = {'GROCERY', 'UTILITY', 'MEDICAL', 'FUEL'}
DISCRETIONARY_CATEGORIES = {'DINING', 'ENTERTAINMENT', 'SHOPPING', 'TRANSFER'}

# ★NEW★ Fix 3.5: Merchant pools for repeat-merchant behavior
MERCHANT_POOLS = {
    'GROCERY': ['BigBazaar', 'DMart', 'Reliance Fresh', 'More Supermarket', 'Local Kirana'],
    'UTILITY': ['Electricity Board', 'Water Authority', 'Gas Company', 'Broadband Co'],
    'DINING': ['Swiggy', 'Zomato', 'Dominos', 'Local Restaurant', 'McDonald\'s'],
    'ENTERTAINMENT': ['Netflix', 'BookMyShow', 'Spotify', 'PVR Cinemas', 'Disney+'],
    'SHOPPING': ['Amazon', 'Flipkart', 'Myntra', 'Croma', 'Local Mall'],
    'MEDICAL': ['Apollo Pharmacy', 'MedPlus', 'City Hospital', '1mg'],
    'FUEL': ['HP Petrol', 'Indian Oil', 'Shell', 'BPCL'],
    'TRANSFER': ['NEFT Transfer', 'UPI Transfer', 'IMPS Transfer'],
    'ATM': ['SBI ATM', 'HDFC ATM', 'ICICI ATM', 'Axis ATM', 'Kotak ATM'],
}

# Lending apps with risk profiles
LENDING_APPS = ['MoneyTap', 'OKCash', 'EarlySalary', 'Cashapp', 'Insta-Borrow']
APP_APR = {'MoneyTap': 0.48, 'OKCash': 0.36, 'EarlySalary': 0.30,
           'Cashapp': 0.24, 'Insta-Borrow': 0.42}

# Utility bill types with payment priority
BILL_TYPES = ['ELECTRICITY', 'WATER', 'GAS', 'INTERNET', 'INSURANCE', 'PHONE']
BILL_PRIORITY = {'ELECTRICITY': 1, 'WATER': 2, 'GAS': 3,
                 'PHONE': 4, 'INTERNET': 5, 'INSURANCE': 6}
# ★NEW★ Fix 7.5: Disconnection thresholds (cumulative late days)
DISCONNECTION_THRESHOLDS = {'ELECTRICITY': 90, 'WATER': 60, 'GAS': 120,
                            'INTERNET': 45, 'PHONE': 30, 'INSURANCE': 365}
# ★NEW★ Fix 7.6: Critical bills
CRITICAL_BILLS = {'ELECTRICITY', 'WATER'}

# Seasonal multipliers
SEASON_ELEC = {1: 1.0, 2: 0.95, 3: 1.1, 4: 1.4, 5: 1.5, 6: 1.3}
SEASON_WATER = {1: 1.0, 2: 1.0, 3: 1.2, 4: 1.5, 5: 1.3, 6: 0.8}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def calculate_emi(principal, annual_rate, tenure_months):
    r = annual_rate / 12
    if r <= 0:
        return int(principal / max(tenure_months, 1))
    emi = principal * (r * (1 + r)**tenure_months) / ((1 + r)**tenure_months - 1)
    return int(round(emi))


def month_stress(base_stress, is_def, month_idx, n_months):
    if is_def:
        progress = month_idx / max(n_months - 1, 1)
        return np.clip(base_stress * (0.4 + 0.6 * progress), 0, 1)
    else:
        return np.clip(base_stress * (0.85 + 0.3 * np.random.random()), 0, 0.5)


def week_stress(base_stress, is_def, week_idx, n_weeks):
    month_equiv = week_idx / 4.33
    n_months_equiv = n_weeks / 4.33
    return month_stress(base_stress, is_def, month_equiv, n_months_equiv)


def safe_day(year, month, day):
    last = calendar.monthrange(year, month)[1]
    return datetime(year, month, min(day, last))


def random_time(stress_level, is_defaulter):
    """★NEW★ Fix 3.4: Generate realistic time-of-day based on stress."""
    if is_defaulter and stress_level > 0.6:
        # Stressed: more late-night activity (22:00-02:00)
        if np.random.random() < 0.25:
            hour = np.random.choice([22, 23, 0, 1, 2])
        else:
            hour = int(np.clip(np.random.normal(14, 4), 6, 23))
    else:
        # Normal: peak 8AM-8PM
        hour = int(np.clip(np.random.normal(13, 3), 7, 22))
    minute = np.random.randint(0, 60)
    second = np.random.randint(0, 60)
    return f"{hour:02d}:{minute:02d}:{second:02d}"


# ============================================================================
# STEP 0: Create Default Labels & Stress Scores
# ============================================================================
print("\n[0/8] Creating customer labels and stress profiles...")

is_default = np.concatenate([
    np.ones(DEFAULT_COUNT, dtype=int),
    np.zeros(NON_DEFAULT_COUNT, dtype=int)
])
np.random.shuffle(is_default)
customer_ids = np.arange(1, N_CUSTOMERS + 1)

# ─────────────────────────────────────────────────────────────────────────
# REALISTIC STRESS DISTRIBUTIONS — heavy overlap in the 0.25–0.65 grey zone
# Real banking: many customers sit in an ambiguous middle band
# ─────────────────────────────────────────────────────────────────────────
stress_scores = np.zeros(N_CUSTOMERS)
for i in range(N_CUSTOMERS):
    if is_default[i] == 1:
        # Most defaulters are high-stress, but some are in the grey zone
        # Beta(2,2) centred ~0.5, shifted up so mean ~0.60
        stress_scores[i] = np.clip(np.random.beta(2.2, 1.6) * 0.70 + 0.18, 0.10, 1.0)
    else:
        # Most non-defaulters are low-stress, but some are in the grey zone
        # Beta(2,2.5) centred ~0.44, kept lower
        stress_scores[i] = np.clip(np.random.beta(2, 2.8) * 0.62, 0.0, 0.62)

default_idx = np.where(is_default == 1)[0]
non_default_idx = np.where(is_default == 0)[0]

# ── Surprise defaults: 22% of defaulters look like good customers ──
# (sudden job loss, medical emergency, divorce — external shocks)
n_surprise_def = int(len(default_idx) * 0.22)
surprise_def = np.random.choice(default_idx, size=n_surprise_def, replace=False)
stress_scores[surprise_def] = np.clip(
    np.random.beta(1.8, 3.5, size=n_surprise_def) * 0.50, 0.03, 0.42)

# ── Resilient non-defaulters: 12% look like they should default but don't ──
# (family support, savings buffer, employer bailout)
n_resilient = int(len(non_default_idx) * 0.12)
resilient = np.random.choice(non_default_idx, size=n_resilient, replace=False)
stress_scores[resilient] = np.clip(
    np.random.beta(2.5, 1.8, size=n_resilient) * 0.62 + 0.28, 0.38, 0.88)

# ── Life-event noise: all customers get a random ±0.08 jitter ──
# (seasonality, measurement error, behavioural inconsistency)
life_noise = np.random.normal(0, 0.06, N_CUSTOMERS)
stress_scores = np.clip(stress_scores + life_noise, 0.01, 0.99)

print(f"✓ Defaulters: {is_default.sum()} ({is_default.mean()*100:.1f}%)")
print(f"  Stress — Default avg: {stress_scores[is_default==1].mean():.3f}, "
      f"Non-default avg: {stress_scores[is_default==0].mean():.3f}")


# ============================================================================
# STEP 1: CUSTOMER MASTER DATA (Fixes 1.1-1.10)
# ============================================================================
print("\n[1/8] Generating Customer Master Data...")

ages = np.random.randint(22, 63, N_CUSTOMERS)

employment_types = np.array([
    np.random.choice(['SALARIED', 'SELF_EMPLOYED', 'RETIRED'], p=[0.70, 0.20, 0.10])
    for _ in range(N_CUSTOMERS)
])
for i in range(N_CUSTOMERS):
    if employment_types[i] == 'RETIRED' and ages[i] < 50:
        employment_types[i] = 'SALARIED'

occupations = []
for i in range(N_CUSTOMERS):
    if employment_types[i] == 'RETIRED':
        occupations.append('RETIRED')
    elif employment_types[i] == 'SELF_EMPLOYED':
        occupations.append(np.random.choice(['BUSINESS_OWNER', 'FREELANCER', 'TRADER']))
    else:
        occupations.append(np.random.choice([
            'IT_SERVICE', 'MANUFACTURING', 'GOVERNMENT',
            'HEALTHCARE', 'EDUCATION', 'FINANCE'
        ]))
occupations = np.array(occupations)

city_probs = []
for c in ALL_CITIES:
    if c in TIER1_CITIES: city_probs.append(0.45 / len(TIER1_CITIES))
    elif c in TIER2_CITIES: city_probs.append(0.30 / len(TIER2_CITIES))
    else: city_probs.append(0.25 / len(TIER3_CITIES))
geographies = np.random.choice(ALL_CITIES, N_CUSTOMERS, p=city_probs)
region_tiers = np.array([CITY_TIER[c] for c in geographies])

base_salary = 20000 + (ages - 20) * 1200
region_mult = np.array([TIER_SALARY_MULT[t] for t in region_tiers])
lognormal_noise = np.random.lognormal(0, 0.25, N_CUSTOMERS)
emp_mult = np.where(employment_types == 'RETIRED', 0.60,
           np.where(employment_types == 'SELF_EMPLOYED', 1.15, 1.0))
default_mult = np.where(is_default == 1, 0.72, 1.0)

salaries = (base_salary * region_mult * lognormal_noise * emp_mult * default_mult).astype(int)
salaries = np.clip((salaries // 500) * 500, 18000, 250000)

salary_days = np.random.choice([1, 5, 10, 15, 25, 28], N_CUSTOMERS,
                                p=[0.08, 0.12, 0.12, 0.15, 0.35, 0.18])

tenure_months = np.zeros(N_CUSTOMERS, dtype=int)
for i in range(N_CUSTOMERS):
    r = np.random.random()
    if r < 0.30: tenure_months[i] = np.random.randint(1, 25)
    elif r < 0.80: tenure_months[i] = np.random.randint(25, 97)
    else: tenure_months[i] = np.random.randint(97, 145)

ref_date = datetime(2024, 6, 30)
account_opening_dates = [
    (ref_date - timedelta(days=int(t * 30.44))).strftime('%Y-%m-%d')
    for t in tenure_months
]

has_personal_loan = (np.random.random(N_CUSTOMERS) < (0.25 + 0.35 * stress_scores)).astype(int)
has_credit_card = (np.random.random(N_CUSTOMERS) < 0.65).astype(int)
has_home_loan = ((np.random.random(N_CUSTOMERS) < np.where(ages > 28, 0.25, 0.05))
                 & (stress_scores < 0.6)).astype(int)
has_savings = np.ones(N_CUSTOMERS, dtype=int)
has_auto_loan = ((np.random.random(N_CUSTOMERS) < 0.12) & (salaries > 40000)).astype(int)
num_products = has_personal_loan + has_credit_card + has_home_loan + has_savings + has_auto_loan

# ★NEW★ Fix 3.5: Assign 2-3 preferred merchants per category per customer
customer_merchants = {}
for i in range(N_CUSTOMERS):
    prefs = {}
    for cat, pool in MERCHANT_POOLS.items():
        n = min(3, len(pool))
        prefs[cat] = list(np.random.choice(pool, n, replace=False))
    customer_merchants[int(customer_ids[i])] = prefs

customer_master = pd.DataFrame({
    'customer_id': customer_ids,
    'age': ages,
    'monthly_salary_rupees': salaries,
    'salary_deposit_day': salary_days,
    'geography': geographies,
    'region_tier': region_tiers,
    'employment_type': employment_types,
    'occupation': occupations,
    'account_opening_date': account_opening_dates,
    'tenure_months': tenure_months,
    'has_personal_loan': has_personal_loan,
    'has_credit_card': has_credit_card,
    'has_home_loan': has_home_loan,
    'has_savings_account': has_savings,
    'has_auto_loan': has_auto_loan,
    'num_products': num_products,
    'customer_segment': 'PENDING',
    'is_default': is_default
})

print(f"✓ customer_master.csv: {len(customer_master)} rows")
print(f"  Salary — Defaulter avg: ₹{salaries[is_default==1].mean():,.0f}, "
      f"Non-defaulter avg: ₹{salaries[is_default==0].mean():,.0f}")
print(f"  Age-salary correlation: {np.corrcoef(ages, salaries)[0,1]:.3f}")


# ============================================================================
# STEP 2: EMI PAYMENT RECORDS (Fixes 2.1-2.12, ★ 2.8 EMI holidays ★)
# ============================================================================
print("\n[2/8] Generating EMI Payment Records...")

emi_records = []
# Track per-customer EMI late months for cross-dataset linking (Fix 7.11)
customer_emi_late_months = {}

for i in range(N_CUSTOMERS):
    cid = int(customer_ids[i])
    salary = int(salaries[i])
    is_def = int(is_default[i])
    stress = stress_scores[i]

    customer_emi_late_months[cid] = set()

    n_loans = (int(np.random.choice([2, 3, 4], p=[0.3, 0.5, 0.2])) if stress > 0.7
               else int(np.random.choice([1, 2, 3], p=[0.3, 0.5, 0.2])) if stress > 0.4
               else int(np.random.choice([1, 2], p=[0.6, 0.4])))

    if has_home_loan[i] and n_loans < 2:
        n_loans = 2

    max_total_emi = int(salary * 0.65)
    remaining_budget = max_total_emi

    for loan_idx in range(n_loans):
        loan_id = f"L{cid:05d}_{loan_idx+1}"

        if loan_idx == 0 and has_home_loan[i]:
            loan_type, principal = 'HOME_LOAN', np.random.randint(500000, 3000001)
            annual_rate = np.random.uniform(0.070, 0.095)
            tenure = int(np.random.choice([120, 180, 240]))
        elif has_personal_loan[i] and loan_idx < 2:
            loan_type, principal = 'PERSONAL_LOAN', np.random.randint(50000, 500001)
            annual_rate = np.random.uniform(0.10, 0.18)
            tenure = int(np.random.choice([12, 24, 36, 48, 60]))
        elif has_auto_loan[i]:
            loan_type, principal = 'AUTO_LOAN', np.random.randint(200000, 800001)
            annual_rate = np.random.uniform(0.08, 0.12)
            tenure = int(np.random.choice([36, 48, 60, 72]))
        else:
            loan_type, principal = 'PERSONAL_LOAN', np.random.randint(30000, 300001)
            annual_rate = np.random.uniform(0.12, 0.20)
            tenure = int(np.random.choice([12, 24, 36]))

        if stress > 0.6:
            annual_rate = min(annual_rate + 0.04, 0.24)

        emi_amount = calculate_emi(principal, annual_rate, tenure)
        original_emi = emi_amount

        if emi_amount > remaining_budget:
            emi_amount = max(remaining_budget, 2000)
            r_m = annual_rate / 12
            if r_m > 0:
                principal = int(emi_amount * ((1 + r_m)**tenure - 1) / (r_m * (1 + r_m)**tenure))
            original_emi = emi_amount
        remaining_budget = max(0, remaining_budget - emi_amount)

        emi_due_day = int(np.random.choice([5, 10, 15, 20, 25]))

        # ★NEW★ Fix 2.8: EMI holiday — some defaulters get 1-2 month moratorium
        has_emi_holiday = is_def and np.random.random() < 0.15
        holiday_months = set()
        if has_emi_holiday:
            start_h = np.random.choice([4, 5])
            holiday_months = {start_h, start_h + 1} if start_h < 6 else {start_h}

        if is_def and stress > 0.8:
            loan_status = np.random.choice(['ACTIVE', 'DEFAULTED'], p=[0.3, 0.7])
        elif is_def:
            loan_status = np.random.choice(['ACTIVE', 'DEFAULTED', 'RESTRUCTURED'], p=[0.4, 0.4, 0.2])
        else:
            loan_status = np.random.choice(['ACTIVE', 'PAID_OFF'], p=[0.8, 0.2])

        for month_idx in range(N_EMI_MONTHS):
            month_num = month_idx + 1
            emi_date = safe_day(2024, month_num, emi_due_day)

            # ★NEW★ Fix 2.8: Check EMI holiday
            is_holiday = month_num in holiday_months
            current_emi = 0 if is_holiday else emi_amount

            if is_holiday:
                status, days_late = 'HOLIDAY', 0
            elif is_def:
                if month_idx <= 1:
                    rv = np.random.random()
                    if rv < 0.82: status, days_late = 'ON_TIME', 0
                    else: status, days_late = 'LATE', int(np.random.randint(1, 5))
                elif month_idx == 2:
                    rv = np.random.random()
                    if rv < 0.50: status, days_late = 'ON_TIME', 0
                    elif rv < 0.85: status, days_late = 'LATE', int(np.random.randint(3, 15))
                    else: status, days_late = 'MISSED', int(np.random.randint(15, 35))
                elif month_idx == 3:
                    rv = np.random.random()
                    if rv < 0.22: status, days_late = 'ON_TIME', 0
                    elif rv < 0.55: status, days_late = 'LATE', int(np.random.randint(7, 22))
                    elif rv < 0.80: status, days_late = 'MISSED', int(np.random.randint(20, 50))
                    else: status, days_late = 'FAILED_DEBIT', int(np.random.randint(10, 40))
                elif month_idx == 4:
                    rv = np.random.random()
                    if rv < 0.08: status, days_late = 'ON_TIME', 0
                    elif rv < 0.25: status, days_late = 'LATE', int(np.random.randint(10, 30))
                    elif rv < 0.60: status, days_late = 'MISSED', int(np.random.randint(30, 60))
                    else: status, days_late = 'FAILED_DEBIT', int(np.random.randint(20, 60))
                else:
                    rv = np.random.random()
                    if rv < 0.04: status, days_late = 'LATE', int(np.random.randint(15, 45))
                    elif rv < 0.40: status, days_late = 'MISSED', int(np.random.randint(45, 90))
                    else: status, days_late = 'FAILED_DEBIT', int(np.random.randint(30, 90))
            else:
                # Non-defaulters: mostly on time with realistic life-event variability
                # Some months are genuinely bad (medical, travel, salary delay)
                personal_stress = np.random.random()
                if personal_stress < 0.04:            # rare bad month (~4% of months)
                    rv = np.random.random()
                    if rv < 0.45: status, days_late = 'LATE', int(np.random.randint(2, 9))
                    elif rv < 0.75: status, days_late = 'LATE', int(np.random.randint(9, 20))
                    else: status, days_late = 'MISSED', int(np.random.randint(5, 25))
                elif personal_stress < 0.12:          # slightly off month (~8%)
                    rv = np.random.random()
                    if rv < 0.70: status, days_late = 'ON_TIME', 0
                    else: status, days_late = 'LATE', int(np.random.randint(1, 5))
                else:                                 # normal month (~88%)
                    if np.random.random() < 0.97: status, days_late = 'ON_TIME', 0
                    else: status, days_late = 'LATE', int(np.random.randint(1, 4))

            if status == 'ON_TIME': days_late = 0

            # Track which months had late EMI (for Fix 7.11 cross-dataset linking)
            if status in ('LATE', 'MISSED', 'FAILED_DEBIT'):
                customer_emi_late_months[cid].add(month_num)

            if status in ('ON_TIME', 'HOLIDAY'):
                actual_date = emi_date
                amount_paid = current_emi
                reason = None
            elif status == 'LATE':
                actual_date = emi_date + timedelta(days=days_late)
                amount_paid = current_emi
                reason = None
            elif status == 'MISSED':
                actual_date = emi_date + timedelta(days=days_late)
                amount_paid = 0
                reason = 'MISSED_PAYMENT'
            else:
                actual_date = emi_date + timedelta(days=max(1, days_late))
                amount_paid = 0
                reason = np.random.choice(
                    ['INSUFFICIENT_FUNDS', 'AUTO_DEBIT_FAILURE', 'ACCOUNT_BLOCKED'],
                    p=[0.70, 0.20, 0.10])

            is_prepayment = 0
            if not is_def and stress < 0.15 and np.random.random() < 0.04:
                is_prepayment = 1
                amount_paid = current_emi * 2

            emi_records.append({
                'customer_id': cid,
                'loan_id': loan_id,
                'loan_type': loan_type,
                'loan_principal': principal,
                'interest_rate_pct': round(annual_rate * 100, 2),
                'loan_tenure_months': tenure,
                'emi_amount': current_emi,
                'original_emi_amount': original_emi,  # ★NEW★ Fix 2.8
                'is_emi_holiday': is_holiday,          # ★NEW★ Fix 2.8
                'emi_due_date': emi_date.strftime('%Y-%m-%d'),
                'emi_due_day': emi_due_day,
                'actual_payment_date': actual_date.strftime('%Y-%m-%d'),
                'amount_paid': amount_paid,
                'payment_status': status,
                'days_overdue': days_late,
                'payment_failed_reason': reason,
                'is_prepayment': is_prepayment,
                'loan_status': loan_status
            })

    if (i + 1) % 2500 == 0:
        print(f"  EMI: processed {i+1}/{N_CUSTOMERS} customers...")

emi_df = pd.DataFrame(emi_records)
emi_df.to_csv('emi_payment_records.csv', index=False)
print(f"✓ emi_payment_records.csv: {len(emi_df):,} rows")
print(f"  Statuses: {emi_df['payment_status'].value_counts().to_dict()}")
print(f"  EMI holidays: {emi_df['is_emi_holiday'].sum():,} records")

_loan_emis = emi_df.groupby(['customer_id', 'loan_id'])['original_emi_amount'].first().reset_index()
customer_monthly_emi = _loan_emis.groupby('customer_id')['original_emi_amount'].sum().to_dict()


# ============================================================================
# STEP 3: TRANSACTION HISTORY (Fixes 3.1-3.15, ★ 3.4/3.5/3.7/3.10 ★)
# ============================================================================
print("\n[3/8] Generating Transaction History...")

transactions = []
cats_list = list(CATEGORY_WEIGHTS.keys())
cats_probs = list(CATEGORY_WEIGHTS.values())

covered_months = set()
for w in range(N_TRANSACTION_WEEKS):
    for d in range(7):
        dt = BASE_DATE + timedelta(days=7 * w + d)
        covered_months.add((dt.year, dt.month))
covered_months = sorted(covered_months)

for i in range(N_CUSTOMERS):
    cid = int(customer_ids[i])
    salary = int(salaries[i])
    is_def = int(is_default[i])
    stress = stress_scores[i]
    sal_day = int(salary_days[i])
    city = str(geographies[i])
    cust_merchants = customer_merchants[cid]

    # Salary deposits
    for year_m, month_m in covered_months:
        last_day = calendar.monthrange(year_m, month_m)[1]
        actual_sal_day = min(sal_day, last_day)
        sal_date_base = datetime(year_m, month_m, actual_sal_day)

        w_approx = max(0, (sal_date_base - BASE_DATE).days // 7)
        w_st = week_stress(stress, is_def, w_approx, N_TRANSACTION_WEEKS)

        delay = 0
        if is_def and w_st > 0.5:
            if np.random.random() < 0.55: delay = np.random.randint(2, 15)
        elif is_def and w_st > 0.3:
            if np.random.random() < 0.15: delay = np.random.randint(1, 5)
        sal_date = sal_date_base + timedelta(days=delay)

        sal_var = (np.random.uniform(0.80, 0.97) if is_def and w_st > 0.6
                   else np.random.uniform(0.93, 1.02) if is_def
                   else np.random.uniform(0.97, 1.03))

        transactions.append({
            'customer_id': cid,
            'transaction_date': sal_date.strftime('%Y-%m-%d'),
            'transaction_time': '09:00:00',                    # ★NEW★ Fix 3.4
            'transaction_type': 'CREDIT',
            'amount': int(salary * sal_var),
            'merchant_category': 'SALARY',
            'merchant_name': 'Employer',                       # ★NEW★ Fix 3.5
            'spending_type': 'INCOME',
            'payment_mode': 'DIGITAL',
            'day_of_week': sal_date.weekday(),                 # ★NEW★ Fix 3.7
            'transaction_status': 'SUCCESS',                   # ★NEW★ Fix 3.10
            'reference_id': f"SAL_{cid}_{sal_date.strftime('%Y%m%d')}"
        })

    # Weekly spending
    for week_idx in range(N_TRANSACTION_WEEKS):
        week_start = BASE_DATE + timedelta(days=7 * week_idx)
        w_st = week_stress(stress, is_def, week_idx, N_TRANSACTION_WEEKS)

        disc_mult = max(0.2, 1.0 - 0.65 * w_st)
        base_txn = max(2, int(3 + 3.5 * (salary / 100000)))
        n_txns = (max(1, base_txn - np.random.randint(1, 3)) if is_def and w_st > 0.6
                  else base_txn + np.random.randint(0, 2))

        for _ in range(n_txns):
            if w_st > 0.5 and np.random.random() < 0.60:
                cat = np.random.choice(['GROCERY', 'UTILITY', 'FUEL', 'MEDICAL'],
                                       p=[0.45, 0.25, 0.15, 0.15])
            else:
                cat = np.random.choice(cats_list, p=cats_probs)

            lo, hi = CATEGORY_AMOUNTS[cat]
            raw_amt = np.random.randint(lo, hi + 1)
            salary_scale = min(salary / 50000, 2.5)
            amount = max(lo, int(raw_amt * salary_scale * 0.6))
            if cat in DISCRETIONARY_CATEGORIES:
                amount = max(int(lo * 0.5), int(amount * disc_mult))

            # ★NEW★ Fix 3.7: Weekday vs weekend behavior
            day_of_week = np.random.randint(0, 7)
            if day_of_week >= 5:  # Weekend
                if cat in DISCRETIONARY_CATEGORIES:
                    amount = int(amount * np.random.uniform(1.15, 1.40))
                elif cat == 'FUEL':
                    amount = int(amount * 0.6)
            tx_date = week_start + timedelta(days=day_of_week)

            # ★NEW★ Fix 3.5: Merchant from preferred pool (75% repeat)
            if cat in MERCHANT_POOLS:
                merch_pool = cust_merchants.get(cat, MERCHANT_POOLS.get(cat, ['Unknown']))
                if np.random.random() < 0.75:
                    merchant = np.random.choice(merch_pool)
                else:
                    merchant = np.random.choice(MERCHANT_POOLS[cat])
            else:
                merchant = cat

            mode = (np.random.choice(['DIGITAL', 'CASH'], p=[0.42, 0.58]) if w_st > 0.5
                    else np.random.choice(['DIGITAL', 'CASH'], p=[0.85, 0.15]))
            spend_type = 'MANDATORY' if cat in MANDATORY_CATEGORIES else 'DISCRETIONARY'

            # ★NEW★ Fix 3.10: Some transactions can fail for stressed customers
            txn_status = 'SUCCESS'
            if is_def and w_st > 0.7 and np.random.random() < 0.03:
                txn_status = 'FAILED'

            transactions.append({
                'customer_id': cid,
                'transaction_date': tx_date.strftime('%Y-%m-%d'),
                'transaction_time': random_time(w_st, is_def),  # ★NEW★ Fix 3.4
                'transaction_type': 'DEBIT',
                'amount': amount,
                'merchant_category': cat,
                'merchant_name': merchant,                       # ★NEW★ Fix 3.5
                'spending_type': spend_type,
                'payment_mode': mode,
                'day_of_week': day_of_week,                      # ★NEW★ Fix 3.7
                'transaction_status': txn_status,                # ★NEW★ Fix 3.10
                'reference_id': f"TXN_{cid}_{tx_date.strftime('%Y%m%d')}_{cat[:4]}_{np.random.randint(10,99)}"
            })

        # ATM withdrawals
        if w_st > 0.7:
            n_atm, atm_lo, atm_hi = np.random.randint(5, 11), 4000, 12000
        elif w_st > 0.4:
            n_atm, atm_lo, atm_hi = np.random.randint(2, 6), 3000, 8000
        else:
            n_atm, atm_lo, atm_hi = np.random.randint(0, 3), 2000, 5000

        for _ in range(n_atm):
            atm_date = week_start + timedelta(days=np.random.randint(0, 7))
            atm_merchant = np.random.choice(cust_merchants.get('ATM', MERCHANT_POOLS['ATM']))
            transactions.append({
                'customer_id': cid,
                'transaction_date': atm_date.strftime('%Y-%m-%d'),
                'transaction_time': random_time(w_st, is_def),   # ★NEW★ Fix 3.4
                'transaction_type': 'ATM',
                'amount': np.random.randint(atm_lo, atm_hi + 1),
                'merchant_category': 'ATM',
                'merchant_name': atm_merchant,                    # ★NEW★ Fix 3.5
                'spending_type': 'CASH_WITHDRAWAL',
                'payment_mode': 'CASH',
                'day_of_week': atm_date.weekday(),                # ★NEW★ Fix 3.7
                'transaction_status': 'SUCCESS',
                'reference_id': f"ATM_{cid}_{atm_date.strftime('%Y%m%d')}_{np.random.randint(100,999)}"
            })

        # Emergency spending spike (Fix 3.13)
        if is_def and week_idx in [4, 5, 6, 7] and np.random.random() < 0.10:
            emrg_date = week_start + timedelta(days=np.random.randint(0, 7))
            transactions.append({
                'customer_id': cid,
                'transaction_date': emrg_date.strftime('%Y-%m-%d'),
                'transaction_time': random_time(w_st, is_def),
                'transaction_type': 'DEBIT',
                'amount': np.random.randint(15000, 60001),
                'merchant_category': 'MEDICAL',
                'merchant_name': np.random.choice(MERCHANT_POOLS['MEDICAL']),
                'spending_type': 'MANDATORY',
                'payment_mode': 'DIGITAL',
                'day_of_week': emrg_date.weekday(),
                'transaction_status': 'SUCCESS',
                'reference_id': f"EMRG_{cid}_{emrg_date.strftime('%Y%m%d')}"
            })

    if (i + 1) % 2500 == 0:
        print(f"  Transactions: processed {i+1}/{N_CUSTOMERS} customers...")

# NOTE: transactions list will be extended by Step 6 (UPI ATM link)
# so we save later after Step 6

print(f"  Transactions so far: {len(transactions):,} rows (before UPI ATM link)")


# ============================================================================
# STEP 4: SAVINGS BALANCE HISTORY (Fixes 4.1-4.12, ★ 4.3/4.7/4.11/4.12 ★)
# ============================================================================
print("\n[4/8] Generating Savings Balance History...")

savings_records = []

for i in range(N_CUSTOMERS):
    cid = int(customer_ids[i])
    salary = int(salaries[i])
    is_def = int(is_default[i])
    stress = stress_scores[i]
    monthly_emi = customer_monthly_emi.get(cid, int(salary * 0.3))

    if is_def:
        balance = int(salary * np.random.uniform(0.5, 2.0))
    else:
        balance = int(salary * np.random.uniform(2.5, 7.0))
    initial_balance = balance
    normal_balance = initial_balance  # ★NEW★ Fix 4.10: customer-specific normal

    # ★NEW★ Fix 4.3: Post-intervention recovery
    has_intervention = is_def and np.random.random() < 0.18
    intervention_week = np.random.randint(5, 9) if has_intervention else None

    prev_balance = balance

    for week_idx in range(N_SAVINGS_WEEKS):
        snapshot_date = BASE_DATE + timedelta(days=7 * week_idx)
        w_st = week_stress(stress, is_def, week_idx, N_SAVINGS_WEEKS)

        is_salary_week = (week_idx % 4 == 0)
        if is_def and w_st > 0.6:
            sal_credit = int(salary * np.random.uniform(0.80, 0.97)) if is_salary_week else 0
        else:
            sal_credit = int(salary * np.random.uniform(0.97, 1.03)) if is_salary_week else 0

        base_spend = int(salary * 0.22)
        spend_var = (np.random.uniform(0.75, 1.4) * (1 + 0.25 * w_st) if is_def
                     else np.random.uniform(0.85, 1.15))
        weekly_spending = int(base_spend * spend_var)

        emi_deducted = int(monthly_emi) if is_salary_week else 0

        # Lumpy events (Fix 4.1)
        event_cost = 0
        if is_def and week_idx in [3, 4, 7, 8, 10] and np.random.random() < 0.12:
            event_cost = np.random.randint(15000, 55001)

        # Volatility (Fix 4.4)
        volatility = (int(max(1, balance) * np.random.uniform(-0.12, 0.06)) if is_def
                      else int(max(1, balance) * np.random.uniform(-0.02, 0.03)))

        # ★NEW★ Fix 4.3: Post-intervention — slower decline, possible relief
        if has_intervention and intervention_week and week_idx + 1 >= intervention_week:
            event_cost = int(event_cost * 0.2)
            weekly_spending = int(weekly_spending * 0.7)
            if week_idx + 1 == intervention_week:
                sal_credit += int(salary * 0.5)  # Relief injection

        balance_change = sal_credit - weekly_spending - emi_deducted - event_cost + volatility
        balance = max(0, balance + balance_change)

        # ★NEW★ Fix 4.7: Minimum balance enforcement flag
        below_minimum = balance < 5000

        # ★NEW★ Fix 4.11: Drawdown rate
        drawdown_rate = max(0, (prev_balance - balance) / max(prev_balance, 1))

        # ★NEW★ Fix 4.12: Weeks of survival
        avg_weekly_spend = max(1, salary * 0.22)
        weeks_of_survival = round(balance / avg_weekly_spend, 1)

        # Balance health score (Fix 4.10)
        health = min(100, max(0, int(100 * balance / max(normal_balance, 1))))

        # ★NEW★ Fix 4.10: Threshold status using customer-specific range
        threshold_yellow = normal_balance * 0.15
        threshold_red = normal_balance * 0.05
        threshold_status = ('RED' if balance < threshold_red
                            else 'YELLOW' if balance < threshold_yellow
                            else 'GREEN')

        savings_records.append({
            'customer_id': cid,
            'balance_date': snapshot_date.strftime('%Y-%m-%d'),
            'week_number': week_idx + 1,
            'account_balance': int(balance),
            'balance_change': int(balance_change),
            'salary_credited': sal_credit,
            'weekly_spending': weekly_spending,
            'emi_deducted': emi_deducted,
            'balance_health_score': health,
            'below_minimum_balance': int(below_minimum),           # ★NEW★ Fix 4.7
            'drawdown_rate': round(drawdown_rate, 4),              # ★NEW★ Fix 4.11
            'weeks_of_survival': weeks_of_survival,                # ★NEW★ Fix 4.12
            'threshold_status': threshold_status,                  # ★NEW★ Fix 4.10
            'intervention_active': int(has_intervention and intervention_week
                                       and week_idx + 1 >= intervention_week),  # ★NEW★ Fix 4.3
        })

        prev_balance = balance

    if (i + 1) % 2500 == 0:
        print(f"  Savings: processed {i+1}/{N_CUSTOMERS} customers...")

savings_df = pd.DataFrame(savings_records)
savings_df.to_csv('savings_balance_history.csv', index=False)
print(f"✓ savings_balance_history.csv: {len(savings_df):,} rows")
print(f"  New fields: drawdown_rate, weeks_of_survival, below_minimum_balance, "
      f"threshold_status, intervention_active")


# ============================================================================
# STEP 5: FAILED TRANSACTIONS (Fixes 5.1-5.13, ★ 5.11/5.12/5.13 ★)
# ============================================================================
print("\n[5/8] Generating Failed Transactions...")

failed_records = []

# ★NEW★ Fix 5.13: Severity base scores
SEVERITY_BASE = {'EMI': 10, 'UTILITY': 4, 'INSURANCE': 6, 'OTHER': 2}
SEVERITY_REASON = {'INSUFFICIENT_FUNDS': 1.0, 'ACCOUNT_FROZEN': 0.6,
                   'INVALID_ACCOUNT': 0.3, 'ACCOUNT_CLOSED': 1.5,
                   'NETWORK_ERROR': 0.2}

for i in range(N_CUSTOMERS):
    cid = int(customer_ids[i])
    salary = int(salaries[i])
    is_def = int(is_default[i])
    stress = stress_scores[i]
    cumulative_fails = 0

    if is_def:
        for week_idx in range(N_TRANSACTION_WEEKS):
            w_st = week_stress(stress, is_def, week_idx, N_TRANSACTION_WEEKS)
            if w_st < 0.30: n_fails = 0
            elif w_st < 0.50: n_fails = int(np.random.choice([0, 1], p=[0.65, 0.35]))
            elif w_st < 0.70: n_fails = int(np.random.choice([0, 1, 2], p=[0.25, 0.50, 0.25]))
            else: n_fails = int(np.random.choice([1, 2, 3, 4], p=[0.20, 0.30, 0.30, 0.20]))

            # ★NEW★ Fix 5.11: Cascading — if EMI failed this week, utility likely fails too
            had_emi_fail_this_week = False
            week_bill_types_failed = set()

            for fail_idx in range(n_fails):
                fail_date = BASE_DATE + timedelta(days=7 * week_idx + np.random.randint(0, 7))
                bill_type = np.random.choice(
                    ['EMI', 'UTILITY', 'INSURANCE', 'OTHER'],
                    p=[0.55, 0.25, 0.10, 0.10])

                # Fix 5.11: If EMI already failed, boost utility failure probability
                if had_emi_fail_this_week and bill_type == 'OTHER':
                    bill_type = 'UTILITY'  # Cascade from EMI to utility

                if bill_type == 'EMI': had_emi_fail_this_week = True
                week_bill_types_failed.add(bill_type)

                if bill_type == 'EMI':
                    amt = np.random.randint(max(2000, int(salary * 0.20)),
                                            max(3000, int(salary * 0.55)) + 1)
                elif bill_type == 'UTILITY':
                    amt = np.random.randint(800, min(4500, max(900, int(salary * 0.12))) + 1)
                elif bill_type == 'INSURANCE':
                    amt = np.random.randint(2000, min(10000, max(2500, int(salary * 0.18))) + 1)
                else:
                    amt = np.random.randint(500, min(5000, max(600, int(salary * 0.08))) + 1)

                reason = np.random.choice(
                    ['INSUFFICIENT_FUNDS', 'ACCOUNT_FROZEN', 'INVALID_ACCOUNT', 'ACCOUNT_CLOSED'],
                    p=[0.70, 0.15, 0.10, 0.05])
                is_retry = 1 if np.random.random() < 0.50 else 0
                retry_success = 1 if (is_retry and np.random.random() < 0.35) else 0

                cumulative_fails += 1

                # ★NEW★ Fix 5.13: Severity score
                base_sev = SEVERITY_BASE.get(bill_type, 2)
                reason_mult = SEVERITY_REASON.get(reason, 1.0)
                recency_mult = 1.0 + (week_idx / N_TRANSACTION_WEEKS) * 0.5
                severity = round(base_sev * reason_mult * recency_mult * (1 + fail_idx * 0.3), 1)

                # ★NEW★ Fix 5.12: Intervention response flag
                intervention_flag = 0
                if cumulative_fails > 8 and np.random.random() < 0.10:
                    intervention_flag = 1

                failed_records.append({
                    'customer_id': cid,
                    'failure_date': fail_date.strftime('%Y-%m-%d'),
                    'failure_type': np.random.choice(
                        ['AUTO_DEBIT_FAILURE', 'DECLINED_CARD', 'MANDATE_FAILURE']),
                    'bill_type': bill_type,
                    'amount_attempted': amt,
                    'reason_code': reason,
                    'is_retry': is_retry,
                    'retry_success': retry_success,
                    'week_number': week_idx + 1,                    # ★NEW★ temporal
                    'severity_score': severity,                     # ★NEW★ Fix 5.13
                    'intervention_flag': intervention_flag,         # ★NEW★ Fix 5.12
                    'concurrent_bill_types': len(week_bill_types_failed),  # ★NEW★ Fix 5.11
                })

                # Multiple attempts same day (Fix 5.10)
                if w_st > 0.8 and np.random.random() < 0.30:
                    failed_records.append({
                        'customer_id': cid,
                        'failure_date': fail_date.strftime('%Y-%m-%d'),
                        'failure_type': 'AUTO_DEBIT_FAILURE',
                        'bill_type': bill_type,
                        'amount_attempted': amt,
                        'reason_code': 'INSUFFICIENT_FUNDS',
                        'is_retry': 1,
                        'retry_success': 0,
                        'week_number': week_idx + 1,
                        'severity_score': round(severity * 1.3, 1),
                        'intervention_flag': 0,
                        'concurrent_bill_types': len(week_bill_types_failed),
                    })
    else:
        n_fails = int(np.random.choice([0, 0, 0, 1, 1, 2]))
        for _ in range(n_fails):
            fail_week = np.random.randint(0, N_TRANSACTION_WEEKS)
            fail_date = BASE_DATE + timedelta(days=7 * fail_week + np.random.randint(0, 7))
            amt = np.random.randint(500, max(600, int(salary * 0.12)) + 1)
            reason = np.random.choice(['INSUFFICIENT_FUNDS', 'NETWORK_ERROR', 'INVALID_ACCOUNT'])
            failed_records.append({
                'customer_id': cid,
                'failure_date': fail_date.strftime('%Y-%m-%d'),
                'failure_type': np.random.choice(['AUTO_DEBIT_FAILURE', 'DECLINED_CARD']),
                'bill_type': np.random.choice(['UTILITY', 'OTHER']),
                'amount_attempted': amt,
                'reason_code': reason,
                'is_retry': 1 if np.random.random() < 0.70 else 0,
                'retry_success': 1 if np.random.random() < 0.80 else 0,
                'week_number': fail_week + 1,
                'severity_score': round(np.random.uniform(1, 4), 1),
                'intervention_flag': 0,
                'concurrent_bill_types': 1,
            })

failed_df = pd.DataFrame(failed_records)
failed_df.to_csv('failed_transactions.csv', index=False)
print(f"✓ failed_transactions.csv: {len(failed_df):,} rows")
print(f"  New fields: week_number, severity_score, intervention_flag, concurrent_bill_types")


# ============================================================================
# STEP 6: UPI LENDING TRANSACTIONS (Fixes 6.1-6.12, ★ 6.5 ATM link ★)
# ============================================================================
print("\n[6/8] Generating UPI/Lending Transactions...")

upi_records = []

for i in range(N_CUSTOMERS):
    cid = int(customer_ids[i])
    salary = int(salaries[i])
    is_def = int(is_default[i])
    stress = stress_scores[i]

    n_apps = (int(np.random.choice([3, 4, 5], p=[0.3, 0.4, 0.3])) if stress > 0.7
              else int(np.random.choice([1, 2, 3], p=[0.3, 0.5, 0.2])) if stress > 0.4
              else int(np.random.choice([1, 2], p=[0.7, 0.3])))

    preferred = (['OKCash', 'MoneyTap', 'Insta-Borrow', 'EarlySalary', 'Cashapp'] if stress > 0.6
                 else ['Cashapp', 'EarlySalary', 'MoneyTap', 'OKCash', 'Insta-Borrow'])
    customer_apps = preferred[:n_apps]

    for month_idx in range(N_UPI_MONTHS):
        month_num = month_idx + 1
        m_st = month_stress(stress, is_def, month_idx, N_UPI_MONTHS)

        n_payments = np.random.randint(3, 12)
        for _ in range(n_payments):
            tx_date = safe_day(2024, month_num, np.random.randint(1, 29))
            upi_records.append({
                'customer_id': cid,
                'transaction_date': tx_date.strftime('%Y-%m-%d'),
                'app_name': np.random.choice(customer_apps),
                'amount': np.random.randint(50, 5001),
                'transaction_type': 'PAYMENT',
                'interest_rate_pct': 0.0,
                'repayment_due_date': None,
                'repayment_status': None,
                'is_stacking': 0,
                'loan_purpose': None
            })

        # App loans
        if m_st > 0.70: n_loans = np.random.randint(3, 9)
        elif m_st > 0.45: n_loans = np.random.randint(1, 5)
        elif m_st > 0.20: n_loans = int(np.random.choice([0, 1], p=[0.55, 0.45]))
        else: n_loans = int(np.random.choice([0, 0, 1]))

        prev_maturity = None
        for _ in range(n_loans):
            tx_date = safe_day(2024, month_num, np.random.randint(1, 29))
            app = np.random.choice(customer_apps)
            max_loan = max(3000, int(salary * 0.40))
            loan_amt = np.random.randint(1000, max_loan + 1)
            apr = APP_APR.get(app, 0.30)

            mat_days = int(np.random.choice([7, 14, 30, 60, 90]))
            mat_date = tx_date + timedelta(days=mat_days)

            if is_def and m_st > 0.6:
                rep = np.random.choice(['REPAID', 'DEFAULTED', 'PENDING'], p=[0.25, 0.45, 0.30])
            elif is_def:
                rep = np.random.choice(['REPAID', 'DEFAULTED', 'PENDING'], p=[0.55, 0.20, 0.25])
            else:
                rep = np.random.choice(['REPAID', 'PENDING'], p=[0.85, 0.15])

            is_stacking = 0
            if prev_maturity is not None and tx_date < prev_maturity:
                is_stacking = 1
            prev_maturity = mat_date

            purpose = (np.random.choice(
                ['SALARY_GAP', 'EMERGENCY', 'DEBT_REFINANCE', 'CONSUMPTION'],
                p=[0.25, 0.30, 0.30, 0.15]) if is_def
                else np.random.choice(
                    ['SALARY_GAP', 'EMERGENCY', 'CONSUMPTION'],
                    p=[0.35, 0.30, 0.35]))

            upi_records.append({
                'customer_id': cid,
                'transaction_date': tx_date.strftime('%Y-%m-%d'),
                'app_name': app,
                'amount': loan_amt,
                'transaction_type': 'PARMI_LOAN',
                'interest_rate_pct': round(apr * 100, 1),
                'repayment_due_date': mat_date.strftime('%Y-%m-%d'),
                'repayment_status': rep,
                'is_stacking': is_stacking,
                'loan_purpose': purpose
            })

            # ★NEW★ Fix 6.5: Link to ATM withdrawal — 70% of app loans followed by cash out
            if np.random.random() < 0.70:
                atm_date = tx_date + timedelta(days=int(np.random.choice([0, 1])))
                # Clamp to same month
                if atm_date.month != tx_date.month:
                    atm_date = tx_date
                atm_amt = int(loan_amt * np.random.uniform(0.80, 1.0))
                atm_merchant = np.random.choice(MERCHANT_POOLS['ATM'])
                transactions.append({
                    'customer_id': cid,
                    'transaction_date': atm_date.strftime('%Y-%m-%d'),
                    'transaction_time': random_time(m_st, is_def),
                    'transaction_type': 'ATM',
                    'amount': atm_amt,
                    'merchant_category': 'ATM',
                    'merchant_name': atm_merchant,
                    'spending_type': 'CASH_WITHDRAWAL',
                    'payment_mode': 'CASH',
                    'day_of_week': atm_date.weekday(),
                    'transaction_status': 'SUCCESS',
                    'reference_id': f"UPI_ATM_{cid}_{atm_date.strftime('%Y%m%d')}_{np.random.randint(100,999)}"
                })

    if (i + 1) % 2500 == 0:
        print(f"  UPI: processed {i+1}/{N_CUSTOMERS} customers...")

upi_df = pd.DataFrame(upi_records)
upi_df.to_csv('upi_lending_transactions.csv', index=False)
print(f"✓ upi_lending_transactions.csv: {len(upi_df):,} rows")
print(f"  Types: {upi_df['transaction_type'].value_counts().to_dict()}")

# NOW save transactions (after UPI ATM link additions from Fix 6.5)
transactions_df = pd.DataFrame(transactions)
transactions_df.to_csv('transaction_history.csv', index=False)
print(f"✓ transaction_history.csv: {len(transactions_df):,} rows (incl. UPI-linked ATMs)")
print(f"  New fields: transaction_time, merchant_name, day_of_week, transaction_status")


# ============================================================================
# STEP 7: UTILITY BILL PAYMENTS (Fixes 7.1-7.15, ★ 7.5/7.6/7.11/7.13 ★)
# ============================================================================
print("\n[7/8] Generating Utility Bill Payments...")

utility_records = []

for i in range(N_CUSTOMERS):
    cid = int(customer_ids[i])
    salary = int(salaries[i])
    is_def = int(is_default[i])
    stress = stress_scores[i]
    emi_late_months = customer_emi_late_months.get(cid, set())

    n_bill_types = np.random.randint(3, 6)
    customer_bills = list(np.random.choice(BILL_TYPES, n_bill_types, replace=False))
    total_utility = salary * 0.10

    # ★NEW★ Fix 7.6: Pre-paid vs post-paid
    is_prepaid = np.random.random() < (0.30 if is_def else 0.65)

    # ★NEW★ Fix 7.5: Track cumulative late days per bill type for disconnection
    cumulative_late = {bt: 0 for bt in BILL_TYPES}

    for month_idx in range(N_UTILITY_MONTHS):
        month_num = month_idx + 1
        m_st = month_stress(stress, is_def, month_idx, N_UTILITY_MONTHS)

        # ★NEW★ Fix 7.11: Check if EMI was late this month
        emi_was_late = month_num in emi_late_months

        for bill_type in customer_bills:
            base_amt = total_utility / len(customer_bills)

            if bill_type == 'ELECTRICITY':
                seasonal = SEASON_ELEC.get(month_num, 1.0)
                amount_due = max(300, int(base_amt * seasonal * np.random.uniform(0.85, 1.15)))
                due_day = np.random.choice([5, 10, 15])
            elif bill_type == 'WATER':
                seasonal = SEASON_WATER.get(month_num, 1.0)
                amount_due = max(200, int(base_amt * 0.6 * seasonal * np.random.uniform(0.80, 1.20)))
                due_day = np.random.choice([8, 12, 18])
            elif bill_type == 'GAS':
                amount_due = max(200, int(base_amt * 0.5 * np.random.uniform(0.80, 1.20)))
                due_day = np.random.choice([10, 15, 20])
            elif bill_type == 'INTERNET':
                amount_due = int(np.random.choice([599, 799, 999, 1499]))
                due_day = np.random.choice([1, 5, 15, 20])
            elif bill_type == 'INSURANCE':
                if month_num not in [1, 4]: continue
                amount_due = max(1000, int(salary * np.random.uniform(0.03, 0.08)))
                due_day = 25
            elif bill_type == 'PHONE':
                amount_due = int(np.random.choice([299, 399, 599, 899]))
                due_day = np.random.choice([1, 10, 20])
            else:
                amount_due = max(300, int(base_amt * 0.5))
                due_day = 15

            bill_due_date = safe_day(2024, month_num, due_day)
            priority = BILL_PRIORITY.get(bill_type, 5)
            is_critical = bill_type in CRITICAL_BILLS  # ★NEW★

            if is_def:
                # ★NEW★ Fix 7.11: If EMI was late, increase utility late probability
                emi_late_boost = 0.15 if emi_was_late else 0.0

                if month_idx <= 1:
                    rv = np.random.random()
                    threshold_on_time = 0.68 - emi_late_boost
                    if rv < threshold_on_time:
                        days_late, pay_status = 0, 'ON_TIME'
                    else:
                        days_late = np.random.randint(1, 6)
                        pay_status = 'LATE'
                elif month_idx <= 3:
                    rv = np.random.random()
                    threshold_on_time = 0.32 - emi_late_boost
                    if rv < threshold_on_time:
                        days_late, pay_status = 0, 'ON_TIME'
                    elif rv < 0.65:
                        days_late = np.random.randint(3, 18)
                        pay_status = 'LATE'
                    elif rv < 0.85 and priority > 3:
                        days_late, pay_status = 0, 'MISSED'
                    else:
                        days_late = np.random.randint(8, 25)
                        pay_status = 'LATE'
                else:
                    if priority <= 2:
                        rv = np.random.random()
                        threshold_on_time = 0.18 - emi_late_boost
                        if rv < threshold_on_time:
                            days_late, pay_status = 0, 'ON_TIME'
                        elif rv < 0.45:
                            days_late = np.random.randint(10, 35)
                            pay_status = 'LATE'
                        elif rv < 0.72:
                            days_late = np.random.randint(5, 20)
                            pay_status = 'PARTIAL'
                        else:
                            days_late, pay_status = 0, 'MISSED'
                    else:
                        rv = np.random.random()
                        if rv < 0.12:
                            days_late = np.random.randint(15, 45)
                            pay_status = 'LATE'
                        else:
                            days_late, pay_status = 0, 'MISSED'
            else:
                rv = np.random.random()
                if rv < 0.95:
                    days_late, pay_status = 0, 'ON_TIME'
                else:
                    days_late = np.random.randint(1, 4)
                    pay_status = 'LATE'

            if pay_status == 'ON_TIME': amount_paid = amount_due
            elif pay_status == 'LATE': amount_paid = amount_due
            elif pay_status == 'PARTIAL': amount_paid = int(amount_due * np.random.uniform(0.30, 0.70))
            else: amount_paid = 0

            actual_date = bill_due_date + timedelta(days=days_late)

            if is_def and month_idx >= 3:
                pay_mode = np.random.choice(['AUTO_DEBIT', 'MANUAL', 'CASH'], p=[0.15, 0.55, 0.30])
            else:
                pay_mode = np.random.choice(['AUTO_DEBIT', 'MANUAL'], p=[0.70, 0.30])

            season_label = ('SUMMER' if month_num in [4, 5, 6]
                            else 'WINTER' if month_num in [11, 12, 1]
                            else 'MODERATE')

            # ★NEW★ Fix 7.5: Cumulative late days and disconnection risk
            cumulative_late[bill_type] += days_late
            disconnect_threshold = DISCONNECTION_THRESHOLDS.get(bill_type, 365)
            at_disconnection_risk = cumulative_late[bill_type] > disconnect_threshold

            # ★NEW★ Fix 7.13: Service status with reconnection
            if at_disconnection_risk and np.random.random() < 0.40:
                service_status = 'DISCONNECTED'
            elif at_disconnection_risk and np.random.random() < 0.10:
                service_status = 'RECONNECTED'
                cumulative_late[bill_type] = int(cumulative_late[bill_type] * 0.5)
            else:
                service_status = 'ACTIVE'

            utility_records.append({
                'customer_id': cid,
                'bill_type': bill_type,
                'bill_due_date': bill_due_date.strftime('%Y-%m-%d'),
                'actual_payment_date': actual_date.strftime('%Y-%m-%d'),
                'amount_due': amount_due,
                'amount_paid': amount_paid,
                'days_late': days_late,
                'payment_status': pay_status,
                'payment_mode': pay_mode,
                'season': season_label,
                'is_prepaid': int(is_prepaid),                     # ★NEW★ Fix 7.6
                'is_critical_bill': int(is_critical),              # ★NEW★
                'cumulative_late_days': cumulative_late[bill_type], # ★NEW★ Fix 7.5
                'at_disconnection_risk': int(at_disconnection_risk),  # ★NEW★ Fix 7.5
                'service_status': service_status,                  # ★NEW★ Fix 7.13
            })

    if (i + 1) % 2500 == 0:
        print(f"  Utility: processed {i+1}/{N_CUSTOMERS} customers...")

utility_df = pd.DataFrame(utility_records)
utility_df.to_csv('utility_bill_payments.csv', index=False)
print(f"✓ utility_bill_payments.csv: {len(utility_df):,} rows")
print(f"  Statuses: {utility_df['payment_status'].value_counts().to_dict()}")
print(f"  New fields: is_prepaid, is_critical_bill, cumulative_late_days, "
      f"at_disconnection_risk, service_status")


# ============================================================================
# STEP 8: POST-PROCESSING — Derive segment, calculate DTI
# ============================================================================
print("\n[8/8] Post-processing: deriving segments & DTI...")

customer_total_emi = emi_df.groupby('customer_id')['original_emi_amount'].mean().reset_index()
customer_total_emi.columns = ['customer_id', 'avg_monthly_emi']
customer_master = customer_master.merge(customer_total_emi, on='customer_id', how='left')
customer_master['avg_monthly_emi'] = customer_master['avg_monthly_emi'].fillna(0)
customer_master['dti_ratio'] = np.round(
    customer_master['avg_monthly_emi'] / customer_master['monthly_salary_rupees'], 4)

cust_pay_ratio = emi_df[emi_df['payment_status'] != 'HOLIDAY'].groupby('customer_id').apply(
    lambda x: (x['payment_status'] == 'ON_TIME').mean()
).reset_index()
cust_pay_ratio.columns = ['customer_id', '_pay_ratio']
customer_master = customer_master.merge(cust_pay_ratio, on='customer_id', how='left')
customer_master['_pay_ratio'] = customer_master['_pay_ratio'].fillna(0)

customer_master['customer_segment'] = np.where(
    customer_master['_pay_ratio'] > 0.90, 'PREMIUM',
    np.where(customer_master['_pay_ratio'] > 0.65, 'STANDARD', 'RISK'))
customer_master.drop(columns=['_pay_ratio'], inplace=True)

customer_master.to_csv('customer_master.csv', index=False)
print(f"✓ customer_master.csv UPDATED with DTI and derived segments")
print(f"  Segments: {customer_master['customer_segment'].value_counts().to_dict()}")
print(f"  DTI — Default avg: {customer_master[customer_master['is_default']==1]['dti_ratio'].mean():.3f}, "
      f"Non-default avg: {customer_master[customer_master['is_default']==0]['dti_ratio'].mean():.3f}")


# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("ALL PRIORITY 1 DATASETS GENERATED — V2 ALL 88 FIXES")
print("=" * 80)
print(f"\n  1. customer_master.csv ............ {len(customer_master):>10,} rows")
print(f"  2. emi_payment_records.csv ....... {len(emi_df):>10,} rows")
print(f"  3. transaction_history.csv ....... {len(transactions_df):>10,} rows")
print(f"  4. savings_balance_history.csv ... {len(savings_df):>10,} rows")
print(f"  5. failed_transactions.csv ....... {len(failed_df):>10,} rows")
print(f"  6. upi_lending_transactions.csv .. {len(upi_df):>10,} rows")
print(f"  7. utility_bill_payments.csv ..... {len(utility_df):>10,} rows")

print(f"\n  ★ 33 NEW FIXES over V1:")
print(f"  EMI:          2.8 EMI holidays/modification")
print(f"  Transactions: 3.4 time-of-day, 3.5 merchant names/repeat,")
print(f"                3.7 weekend vs weekday, 3.10 failed txn status")
print(f"  Savings:      4.3 post-intervention recovery, 4.7 minimum balance,")
print(f"                4.10 threshold status, 4.11 drawdown rate, 4.12 survival weeks")
print(f"  Failed:       5.11 cascading failures, 5.12 intervention flag,")
print(f"                5.13 severity score")
print(f"  UPI:          6.5 ATM withdrawal linked to app loans")
print(f"  Utility:      7.5 disconnection risk, 7.6 prepaid/postpaid,")
print(f"                7.11 EMI correlation, 7.13 reconnection tracking")
print("=" * 80)
