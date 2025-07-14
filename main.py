import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="💰 Commission Calculator", layout="wide")
st.title("💼 Sales Commission Calculator")

# Define roles
roles = ["Sales", "Supervisor", "Team Leader", "Sales Manager", "General Manager"]

# Enable/disable roles
st.sidebar.header("Enable Roles")
active_roles = {role: st.sidebar.checkbox(role, value=True) for role in roles}

st.header("📝 Enter Sales Data")
num_entries = st.number_input("Number of Sales Entries", min_value=1, step=1)

sales_data = []
for i in range(int(num_entries)):
    st.subheader(f"📌 Sale #{i+1}")
    net_commission = st.number_input(f"💵 Net Commission for Sale #{i+1}", key=f"net_{i}", min_value=0.0)
    
    people = {}
    total_pct = 0.0
    for role in roles:
        if active_roles[role]:
            col1, col2 = st.columns([2, 1])
            with col1:
                name = st.text_input(f"{role} Name", key=f"{role}_name_{i}")
            with col2:
                percent = st.number_input(f"{role} %", key=f"{role}_pct_{i}", min_value=0.0, max_value=100.0)
            people[role] = {"name": name, "percent": percent}
            total_pct += percent

    # Warning if total role % > 100
    if total_pct > 100:
        st.warning(f"⚠️ Total percentage for Sale #{i+1} exceeds 100%!")

    sales_data.append({"net_commission": net_commission, "people": people})

# Button to generate report
if st.button("📊 Generate Report"):
    results = {}
    total_commission = 0.0
    total_distributed = 0.0
    sale_breakdown = []

    for idx, sale in enumerate(sales_data):
        net = sale["net_commission"]
        total_commission += net
        row = {"Sale #": f"#{idx+1}", "Net Commission": net}

        for role, info in sale["people"].items():
            name = info["name"]
            pct = info["percent"] / 100  # Convert to decimal
            if name:
                amount = round(net * pct, 2)
                total_distributed += amount
                row[f"{role} ({name})"] = amount

                if name not in results:
                    results[name] = 0.0
                results[name] += amount

        sale_breakdown.append(row)

    # Summary table
    summary_df = pd.DataFrame([{"Name": name, "Total Commission": round(amount, 2)} for name, amount in results.items()])
    st.subheader("📋 Summary Report")
    st.table(summary_df)

    # Detailed sale breakdown
    st.subheader("🧾 Detailed Per-Sale Breakdown")
    st.dataframe(pd.DataFrame(sale_breakdown).fillna(0), use_container_width=True)

    # Company net
    company_left = round(total_commission - total_distributed, 2)
    company_pct = round((company_left / total_commission) * 100, 2) if total_commission > 0 else 0
    st.success(f"🏢 Company Net Commission: {company_left} ({company_pct}%)")

    # Pie chart of distribution
    st.subheader("📈 Commission Distribution")
    chart_data = results.copy()
    chart_data["Company"] = company_left

    fig, ax = plt.subplots()
    ax.pie(chart_data.values(), labels=chart_data.keys(), autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

    # Download button
    st.download_button(
        label="⬇️ Download Summary CSV",
        data=summary_df.to_csv(index=False),
        file_name="commission_summary.csv",
        mime="text/csv"
    )
