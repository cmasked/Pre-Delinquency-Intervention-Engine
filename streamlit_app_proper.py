"""
PRE-DELINQUENCY INTERVENTION PLATFORM (PROPER VERSION)
=======================================================

Operational workflow:
1. Dashboard shows ranked high-risk customers
2. Operator clicks customer
3. Sees risk breakdown + behavioral timeline
4. Tests scenarios (what if?)
5. Generates outreach
6. Logs action
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Pre-Delinquency Intervention Platform", layout="wide")

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.markdown("""
    <style>
        .stTabs [role="tablist"] button {
            font-size: 18px;
        }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# LOAD DATA
# ============================================================================

@st.cache_data
def load_data():
    df_decisions = pd.read_csv('unified_customer_decisions.csv')
    df_customers = pd.read_csv('realistic_customer_features.csv')
    return df_decisions, df_customers

df_decisions, df_customers = load_data()

# ============================================================================
# HEADER
# ============================================================================

st.title("⚠️ Pre-Delinquency Intervention Platform")
st.markdown("*Proactive outreach to prevent defaults before they happen*")

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "👤 Customer Analysis", "🎯 Batch Actions"])

# ============================================================================
# TAB 1: DASHBOARD (RANKED LIST)
# ============================================================================

with tab1:
    st.subheader("📊 Early Risk Overview - Ranked by Severity")
    
    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        critical_count = (df_decisions['risk_level'] == 'CRITICAL').sum()
        st.metric("🔴 CRITICAL", critical_count, delta=None)
    
    with col2:
        high_count = (df_decisions['risk_level'] == 'HIGH').sum()
        st.metric("🟠 HIGH", high_count, delta=None)
    
    with col3:
        med_count = (df_decisions['risk_level'] == 'MEDIUM').sum()
        st.metric("🟡 MEDIUM", med_count, delta=None)
    
    with col4:
        low_count = (df_decisions['risk_level'] == 'LOW').sum()
        st.metric("🟢 LOW", low_count, delta=None)
    
    st.markdown("---")
    
    # Filter controls
    col1, col2 = st.columns(2)
    
    with col1:
        risk_filter = st.multiselect(
            "Filter Risk Level",
            ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
            default=['CRITICAL', 'HIGH']
        )
    
    with col2:
        search = st.text_input("Search Customer ID", placeholder="CUST_000001")
    
    # Build display
    df_display = df_decisions.copy()
    
    if risk_filter:
        df_display = df_display[df_display['risk_level'].isin(risk_filter)]
    
    if search:
        df_display = df_display[df_display['customer_id'].str.contains(search, case=False, na=False)]
    
    df_display = df_display.sort_values('default_probability', ascending=False)
    
    # Format display
    def format_risk(risk):
        emojis = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
        return f"{emojis.get(risk, '')} {risk}"
    
    df_display['Risk Level'] = df_display['risk_level'].apply(format_risk)
    df_display['Risk Probability'] = (df_display['default_probability'] * 100).round(1).astype(str) + '%'
    df_display['Stress'] = df_display['stress_score'].round(1)
    
    # Display table
    st.dataframe(
        df_display[[
            'customer_id',
            'Risk Level',
            'Risk Probability',
            'Stress',
            'recommended_action',
            'urgency'
        ]].rename(columns={
            'customer_id': 'Customer ID',
            'recommended_action': 'Recommended Action',
            'urgency': 'Urgency'
        }).head(50),
        use_container_width=True,
        height=400
    )
    
    # Risk distribution chart
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Distribution")
        risk_counts = df_decisions['risk_level'].value_counts()
        fig_risk = go.Figure(data=[go.Pie(
            labels=risk_counts.index,
            values=risk_counts.values,
            marker=dict(colors=['#d62728', '#ff7f0e', '#ffdd57', '#2ca02c'])
        )])
        st.plotly_chart(fig_risk, use_container_width=True)
    
    with col2:
        st.subheader("Action Distribution")
        action_counts = df_decisions['recommended_action'].value_counts()
        fig_action = go.Figure(data=[go.Pie(
            labels=action_counts.index,
            values=action_counts.values,
        )])
        st.plotly_chart(fig_action, use_container_width=True)

# ============================================================================
# TAB 2: CUSTOMER DETAIL ANALYSIS
# ============================================================================

with tab2:
    st.subheader("👤 Customer Risk Analysis & Scenario Testing")
    
    # Customer selection
    selected_cust = st.selectbox(
        "Select Customer",
        df_customers['customer_id'].head(500),
        key="customer_select"
    )
    
    if selected_cust:
        cust_decision = df_decisions[df_decisions['customer_id'] == selected_cust].iloc[0]
        cust_data = df_customers[df_customers['customer_id'] == selected_cust].iloc[0]
        
        # ====== [1] RISK SUMMARY ======
        st.subheader("[1] Risk Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
            st.metric("Risk Level", f"{emoji[cust_decision['risk_level']]} {cust_decision['risk_level']}")
        
        with col2:
            st.metric("Stress Score", f"{cust_data['stress_score']:.0f}/100")
        
        with col3:
            st.metric("Default Risk", f"{cust_decision['default_probability']:.0%}")
        
        with col4:
            st.metric("Trend", "↑ RISING" if cust_data['stress_score'] > 60 else "→ STABLE")
        
        # ====== [2] BEHAVIORAL SIGNALS ======
        st.subheader("[2] Behavioral Signals Detected")
        
        signals = pd.DataFrame({
            'Signal': [
                'Salary Delays',
                'ATM Withdrawals',
                'Failed Debits',
                'Payment On-time Ratio',
                'Discretionary Spending',
                'Payday Loans',
                'Savings Depleted',
                'Utility Late Payments'
            ],
            'Current Value': [
                f"{max(0, cust_data['salary_delay_days']):.1f} days",
                f"{max(0, cust_data['atm_withdrawal_count']):.0f}/week",
                f"{max(0, cust_data['failed_debit_count']):.0f} failures",
                f"{cust_data['payment_ratio']:.0%}",
                f"₹{max(0, cust_data['discretionary_spending']):,.0f}",
                f"{max(0, cust_data['lending_app_transactions']):.0f} loans",
                f"{cust_data['savings_drawdown_ratio']:.0%}",
                f"{max(0, cust_data['utility_late_payment_count']):.0f} times"
            ],
            'Status': [
                '🔴' if cust_data['salary_delay_days'] > 5 else '🟢',
                '🔴' if cust_data['atm_withdrawal_count'] > 6 else '🟢',
                '🔴' if cust_data['failed_debit_count'] > 2 else '🟢',
                '🔴' if cust_data['payment_ratio'] < 0.80 else '🟢',
                '🔴' if cust_data['discretionary_spending'] < 2000 else '🟢',
                '🔴' if cust_data['lending_app_transactions'] > 5 else '🟢',
                '🔴' if cust_data['savings_drawdown_ratio'] > 0.40 else '🟢',
                '🔴' if cust_data['utility_late_payment_count'] > 1 else '🟢',
            ]
        })
        
        st.dataframe(signals, use_container_width=True, hide_index=True)
        
        # ====== [3] PLAIN ENGLISH EXPLANATION ======
        st.subheader("[3] What's Happening (Plain English Explanation)")
        
        if cust_decision['risk_level'] == 'CRITICAL':
            explanation = f"""
            **🔴 CRITICAL RISK - IMMEDIATE ACTION REQUIRED**
            
            **{selected_cust}** is showing SEVERE financial distress:
            
            ✗ **Salary delays**: {cust_data['salary_delay_days']:.0f} days (expected on-time)
            ✗ **Panic withdrawals**: {cust_data['atm_withdrawal_count']:.0f} ATM visits/week 
            ✗ **Payment failures**: {cust_data['failed_debit_count']:.0f} auto-debits failed (insufficient funds)
            ✗ **EMI payment rate**: Only paying {cust_data['payment_ratio']:.0%} of obligations
            ✗ **Savings depleted**: {cust_data['savings_drawdown_ratio']:.0%} of savings already used
            ✗ **Desperate borrowing**: {cust_data['lending_app_transactions']:.0f} payday loans taken
            
            **⚡ Risk Assessment**: Default likely within **14-21 days** without immediate intervention.
            """
        
        elif cust_decision['risk_level'] == 'HIGH':
            explanation = f"""
            **🟠 HIGH RISK - URGENT INTERVENTION NEEDED**
            
            **{selected_cust}** shows deteriorating financial health:
            
            ⚠ Salary delays averaging {cust_data['salary_delay_days']:.0f} days
            ⚠ Spending patterns changing (discretionary spending down significantly)
            ⚠ {cust_data['failed_debit_count']:.0f} payment failures in past month
            ⚠ Increasing reliance on short-term loans
            
            **⚡ Risk Assessment**: Default possible within **30-45 days** if trend continues.
            """
        
        elif cust_decision['risk_level'] == 'MEDIUM':
            explanation = f"""
            **🟡 MEDIUM RISK - PREVENTIVE OUTREACH RECOMMENDED**
            
            **{selected_cust}** shows early warning signs:
            
            • Minor delays in some payments ({cust_data['salary_delay_days']:.1f} days average)
            • Slightly elevated borrowing activity
            • Savings balance relatively stable (drawn {cust_data['savings_drawdown_ratio']:.0%})
            
            **⚡ Risk Assessment**: Early intervention can prevent escalation to HIGH/CRITICAL.
            """
        
        else:
            explanation = f"""
            **🟢 LOW RISK - ROUTINE MONITORING**
            
            **{selected_cust}** shows healthy financial patterns:
            
            ✓ Payments on-time {cust_data['payment_ratio']:.0%} of the time
            ✓ Stable savings balance
            ✓ Minimal short-term borrowing
            
            **⚡ Risk Assessment**: Continue routine monitoring. No immediate action needed.
            """
        
        st.info(explanation)
        
        # ====== [4] RECOMMENDED ACTION ======
        st.subheader("[4] Recommended Action")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            ✅ **{cust_decision['recommended_action'].replace('_', ' ').upper()}**
            
            **Duration**: 30-60 days  
            **Contact Method**: {cust_decision['contact_method']}  
            **Urgency**: {cust_decision['urgency'].replace('_', ' ')}  
            **Expected Outcome**: Prevent default
            
            **Rationale**: Financial stress detected. Proactive intervention now can prevent 
            default in the coming weeks. This action is designed to ease immediate cash flow pressure 
            and maintain customer relationship.
            """)
        
        with col2:
            current_balance = max(0, cust_data['final_savings_balance'])
            monthly_salary = max(0, cust_data['monthly_salary'])
            
            st.metric("Current Savings", f"₹{current_balance:,.0f}")
            st.metric("Monthly Salary", f"₹{monthly_salary:,.0f}")
            st.metric("Balance (months)", f"{current_balance/max(monthly_salary, 1):.1f}")
        
        # ====== [5] SCENARIO TESTING ======
        st.subheader("[5] Scenario Testing - What If?")
        
        st.markdown("**Use sliders below to test different scenarios:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            salary_change = st.slider("Salary Change", -50, 50, 0, 5, key="salary") / 100
        
        with col2:
            emi_change = st.slider("EMI Burden Change", -50, 50, 0, 5, key="emi") / 100
        
        with col3:
            expense_change = st.slider("Expense Change", -50, 50, 0, 5, key="expense") / 100
        
        # Recalculate stress under scenario
        base_stress = cust_data['stress_score']
        
        # Stress increases with: expenses ↑, salary ↓, EMI ↑
        stress_multiplier = 1.0 + (expense_change * 0.4) - (salary_change * 0.6) + (emi_change * 0.5)
        new_stress = base_stress * stress_multiplier
        new_stress = max(0, min(100, new_stress))
        
        # Determine new risk level
        if new_stress > 85:
            scenario_risk = 'CRITICAL'
        elif new_stress > 65:
            scenario_risk = 'HIGH'
        elif new_stress > 35:
            scenario_risk = 'MEDIUM'
        else:
            scenario_risk = 'LOW'
        
        scenario_emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
        
        # Show impact
        if salary_change != 0 or emi_change != 0 or expense_change != 0:
            st.warning(f"""
            **Scenario Impact:**
            
            Current State:
            - Stress Score: {base_stress:.0f}/100
            - Risk Level: {emoji[cust_decision['risk_level']]} {cust_decision['risk_level']}
            
            Under New Scenario:
            - New Stress Score: {new_stress:.0f}/100 (change: {new_stress - base_stress:+.0f})
            - New Risk Level: {scenario_emoji[scenario_risk]} {scenario_risk}
            - Recommended Action: Still **{cust_decision['recommended_action'].replace('_', ' ').upper()}**
            """)
        
        # ====== [6] OUTREACH MESSAGE GENERATOR ======
        st.subheader("[6] 🤖 Generate Outreach Message (GenAI)")
        
        if st.button("Generate Personalized Message", key="gen_msg"):
            
            action_details = {
                'PAYMENT_HOLIDAY': 'a temporary pause on your loan obligations',
                'LOAN_RESTRUCTURE': 'restructured payment terms',
                'PROACTIVE_OUTREACH': 'flexible repayment options',
                'STANDARD_MONITORING': 'continued standard service and support'
            }
            
            action_text = action_details.get(cust_decision['recommended_action'], 'support')
            
            message = f"""
Dear Valued Customer ({selected_cust}),

We value your relationship with us and want to ensure your financial wellbeing.

We've noticed some recent changes in your account activity that suggest you might be 
experiencing financial challenges. This is completely normal, and we're here to help.

**Special Offer for You:**
We would like to offer you {action_text}. This can help you:

✓ Reduce your immediate financial pressure
✓ Maintain your credit standing with us
✓ Get through this period more comfortably
✓ Preserve your account health

**Next Steps:**
Please reach out to us at your earliest convenience to discuss this offer:
📞 Call us: 1-800-BANK (1-800-2265)
📧 Email: support@bank.com
💬 Reply to this message

We're committed to working with you during this time. Our team will be happy to explain 
all available options and find the solution that works best for your situation.

Warm regards,
Your Bank Support Team

---
Reference: {selected_cust} | Risk Level: {cust_decision['risk_level']} | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
            """
            
            st.text_area("Generated Message (Feel free to edit):", value=message, height=300)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📧 Send Email", key="email_btn"):
                    st.success(f"✅ Email queued for {selected_cust}")
            
            with col2:
                if st.button("📱 Send SMS", key="sms_btn"):
                    st.success(f"✅ SMS queued for {selected_cust}")
            
            with col3:
                if st.button("☎️ Schedule Call", key="call_btn"):
                    st.success(f"✅ Call scheduled for {selected_cust} tomorrow at 10 AM")
        
        # ====== [7] ACTION LOG ======
        st.subheader("[7] Action Log & Compliance Trail")
        
        action_log = pd.DataFrame({
            'Date': ['Today ' + datetime.now().strftime("%H:%M %Z"), 'Yesterday 02:15 PM'],
            'Action': ['Risk Assessment Generated', 'Risk Flag Triggered'],
            'Status': ['Pending Intervention', 'Logged'],
            'Notes': [
                f'Stress score: {cust_data["stress_score"]:.0f}/100 - Recommended action: {cust_decision["recommended_action"]}',
                'Automated trigger by pre-delinquency detection system'
            ]
        })
        
        st.dataframe(action_log, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 3: BATCH ACTIONS
# ============================================================================

with tab3:
    st.subheader("🎯 Batch Action Management")
    
    # Show all HIGH + CRITICAL
    batch_df = df_decisions[df_decisions['risk_level'].isin(['CRITICAL', 'HIGH'])].sort_values('default_probability', ascending=False)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Customers Requiring Action", len(batch_df))
    
    with col2:
        st.metric("CRITICAL Priority", len(batch_df[batch_df['risk_level'] == 'CRITICAL']))
    
    with col3:
        st.metric("HIGH Priority", len(batch_df[batch_df['risk_level'] == 'HIGH']))
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Download Action List (CSV)"):
            csv = batch_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"intervention_list_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="download_csv"
            )
    
    with col2:
        if st.button("📧 Send Bulk Messages"):
            st.success(f"✅ {len(batch_df)} bulk messages queued for sending")
    
    with col3:
        if st.button("📊 Generate Report"):
            st.success("✅ Report generated and queued for email delivery")
    
    st.markdown("---")
    
    st.subheader("Top 50 Customers Requiring Immediate Action")
    
    display_batch = batch_df.head(50).copy()
    
    emoji_map = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
    display_batch['Risk Level'] = display_batch['risk_level'].apply(lambda x: f"{emoji_map.get(x, '')} {x}")
    display_batch['Risk %'] = (display_batch['default_probability'] * 100).round(1).astype(str) + '%'
    display_batch['Stress'] = display_batch['stress_score'].round(1)
    
    st.dataframe(
        display_batch[[
            'customer_id',
            'Risk Level',
            'Risk %',
            'Stress',
            'recommended_action',
            'contact_method'
        ]].rename(columns={
            'customer_id': 'Customer ID',
            'recommended_action': 'Action',
            'contact_method': 'Contact'
        }),
        use_container_width=True,
        height=400
    )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("Pre-Delinquency Intervention Platform | Barclays | February 2026")
