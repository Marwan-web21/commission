import streamlit as st
import pandas as pd

st.title("Sales Commission Calculator")

# Define the roles
roles = ["Sales", "Supervisor", "Team Leader", "Sales Manager", "General Manager"]

# Role selection (enable/disable roles)
st.sidebar.header("Enable Roles")
active_roles = {role: st.sidebar.checkbox(role, value=True) for role in roles}

# Input sales entries
st.header("Enter Sales Data")
sales_data = []
num_entries = st.number_input("Number of Sales Entries", min_value=1, step=1)

for i in range(int(num_entries)):
    st.subheader(f"Sale #{i+1}")
    net_commission = st.number_input(f"Net Commission for Sale #{i+1}", key=f"net_{i}", min_value=0.0)

    people = {}
    for role in roles:
        if active_roles[role]:
            name = st.text_input(f"{role} Name for Sale #{i+1}", key=f"{role}_{i}")
            percent = st.number_input(f"{role} % for Sale #{i+1}", key=f"{role}_pct_{i}", min_value=0.0, max_value=1.0, step=0.01)
            people[role] = {"name": name, "percent": percent}

    sales_data.append({"net_commission": net_commission, "people": people})

# Process and generate report
if st.button("Generate Report"):
    results = {}
    total_commission = 0.0
    total_distributed = 0.0

    for sale in sales_data:
        net = sale["net_commission"]
        total_commission += net
        for role, info in sale["people"].items():
            name = info["name"]
            pct = info["percent"]
            if name:
                amount = round(net * pct, 2)
                total_distributed += amount
                if name not in results:
                    results[name] = 0
                results[name] += amount

    # Prepare DataFrame
    report = [{"Name": name, "Total Commission": round(value, 2)} for name, value in results.items()]
    df = pd.DataFrame(report)

    # Net left to company
    company_left = round(total_commission - total_distributed, 2)
    company_pct = round((company_left / total_commission) * 100, 2) if total_commission > 0 else 0

    st.subheader("Commission Report")
    st.table(df)

    st.write(f"**Total Commission Payout:** {total_distributed} ")
    st.write(f"**Company Net Commission:** {company_left} ({company_pct}%)")

    st.download_button(
        label="Download Report as CSV",
        data=df.to_csv(index=False),
        file_name="commission_report.csv",
        mime="text/csv"
    )
