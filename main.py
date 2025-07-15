import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import uuid
import os

st.set_page_config(layout="wide")
if "page" not in st.session_state:
    st.session_state.page = "home"
if "teams" not in st.session_state:
    st.session_state.teams = {}  # team_id: {"name": str, "photo": bytes, "members": [...]}
if "deals" not in st.session_state:
    st.session_state.deals = []  # list of dicts

# ------------- Utility Functions ----------------
def save_team(name, photo, members):
    team_id = str(uuid.uuid4())
    st.session_state.teams[team_id] = {
        "name": name,
        "photo": photo.read() if photo else None,
        "members": members
    }

def add_deal(team_id, net_commission, role_data):
    st.session_state.deals.append({
        "team_id": team_id,
        "net_commission": net_commission,
        "roles": role_data
    })

# ------------- Sidebar Navigation ---------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "📁 Portfolios", "🧮 Commission Calculator", "📊 Teams Report"])
st.session_state.page = page

# ------------- Page: HOME -----------------------
if page == "🏠 Home":
    st.markdown("<h1 style='text-align:center;'>💼 Welcome to Commission Tracker</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🧮 Commission Calculator")
        st.write("Track and distribute commissions easily.")
    with col2:
        st.markdown("### 📁 Teams Portfolio")
        st.write("Manage teams, assign roles and track performance.")

# ------------- Page: PORTFOLIOS -----------------
elif page == "📁 Portfolios":
    st.title("📁 Manage Portfolios")
    with st.expander("➕ Add New Team", expanded=True):
        team_name = st.text_input("Team Name")
        team_photo = st.file_uploader("Upload Team Logo (optional)", type=["png", "jpg", "jpeg"])
        members = []

        st.markdown("#### Add Team Members")
        role_types = ["Sales", "Supervisor", "Team Leader"]
        add_member = st.button("➕ Add Sales")
        if "new_members" not in st.session_state:
            st.session_state.new_members = []

        for i, mem in enumerate(st.session_state.new_members):
            st.text_input(f"Name for Member {i+1}", key=f"member_{i}_name")
            st.selectbox("Role", role_types, key=f"member_{i}_role")

        if add_member:
            st.session_state.new_members.append({})

        if st.button("✅ Save Team"):
            saved_members = []
            for i in range(len(st.session_state.new_members)):
                name = st.session_state.get(f"member_{i}_name", "")
                role = st.session_state.get(f"member_{i}_role", "Sales")
                if name:
                    saved_members.append({"name": name, "role": role})
            save_team(team_name, team_photo, saved_members)
            st.success("Team saved!")
            st.rerun()

    st.markdown("### Your Teams")
    cols = st.columns(3)
    for i, (tid, team) in enumerate(st.session_state.teams.items()):
        col = cols[i % 3]
        with col:
            if team["photo"]:
                st.image(Image.open(pd.io.common.BytesIO(team["photo"])), width=100)
            st.markdown(f"**{team['name']}**")
            if st.button("View", key=f"view_{tid}"):
                st.session_state.selected_team = tid
                st.session_state.page = "📊 Teams Report"
                st.rerun()

# ------------- Page: TEAMS REPORT ----------------
elif page == "📊 Teams Report":
    st.title("📊 Team Performance")
    team_id = st.session_state.get("selected_team")
    if not team_id:
        st.warning("No team selected.")
    else:
        team = st.session_state.teams[team_id]
        st.image(Image.open(pd.io.common.BytesIO(team["photo"])), width=120)
        st.subheader(f"Team: {team['name']}")

        team_deals = [d for d in st.session_state.deals if d["team_id"] == team_id]
        total_commission = sum(d["net_commission"] for d in team_deals)
        distributed = 0
        results = {}

        for d in team_deals:
            net = d["net_commission"]
            for role, info in d["roles"].items():
                name, pct = info["name"], info["percent"] / 100
                if name:
                    amount = round(net * pct, 2)
                    results[name] = results.get(name, 0) + amount
                    distributed += amount

        company_share = total_commission - distributed
        pct_left = (company_share / total_commission * 100) if total_commission else 0

        df = pd.DataFrame([{"Name": k, "Commission": round(v, 2)} for k, v in results.items()])
        st.table(df)
        st.write(f"**Company Net Commission:** {company_share} ({round(pct_left, 2)}%)")

        # Pie chart
        if not df.empty:
            chart_data = df.set_index("Name")
            chart_data.loc["Company"] = company_share
            st.pyplot(chart_data.plot.pie(y="Commission", autopct="%1.1f%%", figsize=(5, 5)).figure)

# ------------- Page: COMMISSION CALCULATOR -----------------
elif page == "🧮 Commission Calculator":
    st.title("🧮 Commission Calculator")

    selected_team = st.selectbox("Select Team", options=st.session_state.teams.keys(), format_func=lambda x: st.session_state.teams[x]["name"])
    net_commission = st.number_input("Net Commission Amount", min_value=0.0, step=10.0)
    st.markdown("#### Select Roles Involved")
    roles_enabled = {}
    role_fields = {}

    for role in ["Sales", "Supervisor", "Team Leader", "Sales Manager", "General Manager"]:
        roles_enabled[role] = st.checkbox(role, value=True if role == "Sales" else False)

    st.markdown("#### Fill Role Information")
    for role, enabled in roles_enabled.items():
        if enabled:
            name = st.text_input(f"{role} Name")
            pct = st.number_input(f"{role} % Share", min_value=0.0, max_value=100.0)
            role_fields[role] = {"name": name, "percent": pct}

    # Validation
    total_pct = sum([v["percent"] for k, v in role_fields.items() if roles_enabled[k]])
    if total_pct > 100:
        st.warning("⚠️ Total percentage exceeds 100%")
    elif st.button("➕ Add Deal"):
        add_deal(selected_team, net_commission, role_fields)
        st.success("Deal added successfully!")
        st.rerun()
