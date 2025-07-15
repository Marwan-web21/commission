import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import uuid
import os

st.set_page_config(layout="wide")

# ---------- Session State Defaults ----------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "teams" not in st.session_state:
    st.session_state.teams = {}  # team_id: {name, photo, members: [{name, role}]}
if "deals" not in st.session_state:
    st.session_state.deals = []
if "new_team_members" not in st.session_state:
    st.session_state.new_team_members = []

# ---------- Helper Functions ----------
def save_team(name, photo, members):
    team_id = str(uuid.uuid4())
    st.session_state.teams[team_id] = {
        "name": name,
        "photo": photo.read() if photo else None,
        "members": members
    }
    return team_id

def add_deal(team_id, net_commission, role_data):
    st.session_state.deals.append({
        "team_id": team_id,
        "net_commission": net_commission,
        "roles": role_data
    })

# ---------- Sidebar Navigation ----------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "📁 Portfolios", "🧮 Commission Calculator", "📊 Teams Report"])
st.session_state.page = page

# ---------- Home ----------
if page == "🏠 Home":
    st.title("💼 Welcome to Commission Tracker")
    st.write("Choose an option from the left menu to get started.")

# ---------- Portfolios ----------
elif page == "📁 Portfolios":
    st.title("📁 Team Portfolios")

    with st.expander("➕ Create a New Team", expanded=True):
        team_name = st.text_input("Team Name")
        team_photo = st.file_uploader("Upload Team Logo (optional)", type=["png", "jpg", "jpeg"])

        st.subheader("Add Team Members")
        add_member_btn = st.button("➕ Add Member")
        if add_member_btn:
            st.session_state.new_team_members.append({"name": "", "role": "Sales"})

        updated_members = []
        for i, member in enumerate(st.session_state.new_team_members):
            cols = st.columns([3, 2, 1])
            with cols[0]:
                name = st.text_input("Member Name", key=f"member_{i}_name")
            with cols[1]:
                role = st.selectbox("Role", ["Sales", "Supervisor", "Team Leader"], key=f"member_{i}_role")
            with cols[2]:
                if st.button("❌ Remove", key=f"remove_{i}"):
                    st.session_state.new_team_members.pop(i)
                    st.rerun()
            if name:
                updated_members.append({"name": name, "role": role})

        if st.button("✅ Save Team"):
            team_id = save_team(team_name, team_photo, updated_members)
            st.session_state.new_team_members.clear()
            st.success(f"Team '{team_name}' added successfully!")

    st.markdown("---")
    st.markdown("### 🧑‍🤝‍🧑 Your Teams")
    for team_id, team in st.session_state.teams.items():
        with st.expander(team["name"]):
            cols = st.columns([1, 3])
            with cols[0]:
                if team["photo"]:
                    st.image(Image.open(pd.io.common.BytesIO(team["photo"])), width=100)
            with cols[1]:
                for role in ["Sales", "Supervisor", "Team Leader"]:
                    names = [m["name"] for m in team["members"] if m["role"] == role]
                    if names:
                        st.markdown(f"**{role}s:**")
                        st.write(", ".join(names))

            # Mini-report
            st.markdown("#### 📊 Team Report")
            team_deals = [d for d in st.session_state.deals if d["team_id"] == team_id]
            total = sum([d["net_commission"] for d in team_deals])
            st.write(f"Total Deals: {len(team_deals)}")
            st.write(f"Total Net Commission: {total:.2f}")

# ---------- Commission Calculator ----------
elif page == "🧮 Commission Calculator":
    st.title("🧮 Commission Calculator")
    if not st.session_state.teams:
        st.warning("No teams available. Please add one in the Portfolio section.")
    else:
        selected_team = st.selectbox("Select Team", list(st.session_state.teams.keys()), format_func=lambda k: st.session_state.teams[k]["name"])
        team_members = st.session_state.teams[selected_team]["members"]

        net = st.number_input("Net Commission", min_value=0.0)
        st.markdown("#### Select Roles Involved")

        role_inputs = {}
        total_pct = 0
        for role in ["Sales", "Supervisor", "Team Leader"]:
            enabled = st.checkbox(f"Include {role}", value=(role == "Sales"))
            if enabled:
                role_names = [m["name"] for m in team_members if m["role"] == role]
                if role_names:
                    name = st.selectbox(f"Select {role}", role_names, key=f"select_{role}")
                    pct = st.number_input(f"{role} % Share", min_value=0.0, max_value=100.0, key=f"pct_{role}")
                    total_pct += pct
                    role_inputs[role] = {"name": name, "percent": pct}

        if total_pct > 100:
            st.error("Total percentage exceeds 100%!")
        elif st.button("✅ Add Deal"):
            add_deal(selected_team, net, role_inputs)
            st.success("Deal added successfully!")
            st.rerun()

# ---------- Teams Report ----------
elif page == "📊 Teams Report":
    st.title("📈 Teams Report Summary")
    for team_id, team in st.session_state.teams.items():
        with st.expander(team["name"]):
            team_deals = [d for d in st.session_state.deals if d["team_id"] == team_id]
            total_commission = sum(d["net_commission"] for d in team_deals)
            distributed = 0
            breakdown = {}

            for d in team_deals:
                for role, info in d["roles"].items():
                    name = info["name"]
                    pct = info["percent"] / 100
                    amount = round(d["net_commission"] * pct, 2)
                    distributed += amount
                    breakdown[name] = breakdown.get(name, 0) + amount

            company_share = total_commission - distributed
            st.write(f"Net Commission: {total_commission:.2f}")
            st.write(f"Distributed: {distributed:.2f}")
            st.write(f"Company Net: {company_share:.2f} ({(company_share/total_commission*100 if total_commission else 0):.2f}%)")

            df = pd.DataFrame([{"Name": k, "Commission": round(v, 2)} for k, v in breakdown.items()])
            st.table(df)
            if not df.empty:
                chart = df.set_index("Name")
                chart.loc["Company"] = company_share
                st.pyplot(chart.plot.pie(y="Commission", autopct="%1.1f%%", figsize=(5,5)).figure)
