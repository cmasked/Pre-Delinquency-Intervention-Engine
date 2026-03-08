# Pre-Delinquency Intervention Engine

An early-warning system for banks to detect **financial stress weeks before loan delinquency** and trigger proactive, empathetic interventions.

This project addresses the problem that most banks act only after a missed payment, when recovery costs are high and customer trust is damaged.

---

## Problem Overview

Traditional credit systems are reactive and focus on post-delinquency collections.
This system shifts the approach to **pre-delinquency intervention** by detecting subtle behavioral and cash-flow signals that indicate emerging financial stress.

---

## System Architecture (High Level)

1. **Synthetic Transaction Generation**
   - Simulates realistic banking behavior (salary credits, UPI, ATM withdrawals, bill payments, failures)
   - Used due to privacy and regulatory constraints on real banking data

2. **Behavioral Feature Engineering**
   - Aggregates weekly/monthly stress indicators such as:
     - Salary delays
     - Savings drawdown
     - Discretionary spending drop
     - Failed auto-debits
     - ATM withdrawal spikes

3. **Machine Learning Models**
   - **XGBoost** for default risk prediction
   - Time-aware feature aggregation to capture early stress trends
   - Threshold optimization focused on recall and business impact

4. **Financial Stress Index**
   - Explainable composite score representing overall financial pressure

5. **Decision Engine**
   - Rule-based logic that converts risk signals into actions:
     - Monitor
     - Send Supportive Nudge
     - Offer Payment Holiday
     - Escalate for Restructuring

6. **Streamlit Dashboard**
   - Analyst-facing interface for:
     - Risk prioritization
     - Customer drill-down
     - Scenario testing
     - Explainability

---

## Key Capabilities

- Early detection of financial stress (2–4 weeks before default)
- Multi-signal behavioral analysis
- Explainable and regulator-friendly logic
- Automated intervention recommendations
- Human-in-the-loop decision support

---

## Tech Stack

- Python
- XGBoost
- Scikit-learn
- Streamlit
- Pandas / NumPy

---



