import streamlit as st
import pandas as pd
import json
import os
from PIL import Image
from io import BytesIO

# Paths
BASE = "commission_app"
PORTFOLIO_FILE = f"{BASE}/portfolios.json"
DEALS_FILE = f"{BASE}/deals.json"
PHOTO_DIR = f"{BASE}/team_photos"
ADMIN_PASSWORD = "admin123"  # Change this to secure it

# Create folders/files if not exist
os.makedirs(PHOTO_DIR, exist_ok=True)
if not os.path.exists(PORTFOLIO_FILE):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump({"teams": []}, f)
if not os.path.exists(DEALS_FILE):
    with open(DEALS_FILE, "w") as f:
        json.dump({"deals": []}, f)

# Load data
def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# Load portfolios and deals
portfolios = load_json(PORTFOLIO_FILE)
deals = load_json(DEALS_FILE)

# Sidebar Navigation
st.sidebar.title("📁 Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "🧑‍💼 Portfolio Manager (Admin)", "🧮 Commission Calculator", "📊 Teams Report"])

# ---- HOME PAGE ----
if page == "🏠 Home":
    st.title("💼 Commission Dashboard")
    st.markdown("""
    Welcome to the premium commission management system. Select an option from the left to begin:
    - 📊 View Teams Report
    - 🧮 Calculate and Record Commission
    - 🧑‍💼 Manage Portfolios (Admin Access)
    """)

# ---- PORTFOLIO MANAGER ----
elif page == "🧑‍💼 Portfolio Manager (Admin)":
    st.title("👥 Team Portfolio Manager")
    pwd = st.text_input("🔐 Enter Admin Password", type="password")
    if pwd != ADMIN_PASSWORD:
        st.warning("Admin access required")
        st.stop()

    st.subheader("📌 Existing Teams")
    for team in portfolios["teams"]:
        st.markdown(f"### 🏷️ {team['name']}")
        cols = st.columns(3)
        for role, members in team['members'].items():
            with cols[0]:
                st.markdown(f"**{role.title()}s:**")
                for m in members:
                    st.markdown(f"- {m}")
        with cols[1]:
            if team.get("photo"):
                img_path = os.path.join(PHOTO_DIR, team['photo'])
                if os.path.exists(img_path):
                    st.image(img_path, width=100)
        with cols[2]:
            if st.button(f"❌ Delete {team['name']}"):
                portfolios["teams"].remove(team)
                save_json(PORTFOLIO_FILE, portfolios)
                st.experimental_rerun()

    st.subheader("➕ Add New Team")
    new_name = st.text_input("Team Name")
    new_members = {"Sales": [], "Supervisors": [], "Team Leaders": []}
    for role in new_members:
        names = st.text_input(f"Enter {role} (comma-separated)")
        new_members[role] = [n.strip() for n in names.split(",") if n.strip()]
    uploaded = st.file_uploader("Upload Team Photo", type=["jpg", "jpeg", "png"])

    if st.button("✅ Save Team"):
        photo_name = None
        if uploaded:
            photo_name = f"{new_name.replace(' ', '_').lower()}.png"
            img = Image.open(uploaded)
            img.save(os.path.join(PHOTO_DIR, photo_name))
        portfolios["teams"].append({"name": new_name, "members": new_members, "photo": photo_name})
        save_json(PORTFOLIO_FILE, portfolios)
        st.success("Team added!")
        st.experimental_rerun()

# ---- COMMISSION CALCULATOR ----
elif page == "🧮 Commission Calculator":
    st.title("🧾 Commission Calculator")
    team_names = [t['name'] for t in portfolios['teams']]
    selected_team = st.selectbox("Select Team", team_names)
    team = next((t for t in portfolios['teams'] if t['name'] == selected_team), None)

    with st.form("add_deal"):
        st.subheader("➕ Add New Deal")
        net_commission = st.number_input("Net Commission", min_value=0.0)
        entry = {"team": selected_team, "net": net_commission, "roles": {}, "id": len(deals['deals'])+1}

        total_pct = 0
        for role in ["Sales", "Supervisors", "Team Leaders"]:
            members = team['members'].get(role, [])
            if members:
                st.markdown(f"**{role}**")
                for m in members:
                    col1, col2 = st.columns([2,1])
                    with col1:
                        name = st.text_input(f"{role}: {m}", key=f"{role}_{m}")
                    with col2:
                        pct = st.number_input("%", key=f"pct_{role}_{m}", min_value=0.0, max_value=100.0)
                    if name:
                        entry['roles'][name] = pct
                        total_pct += pct

        if total_pct > 100:
            st.error("❌ Total % exceeds 100!")
        submitted = st.form_submit_button("✅ Save Deal")
        if submitted and total_pct <= 100:
            deals['deals'].append(entry)
            save_json(DEALS_FILE, deals)
            st.success("Deal saved!")

# ---- TEAMS REPORT ----
elif page == "📊 Teams Report":
    st.title("📈 Teams Report")
    deals = load_json(DEALS_FILE)
    summary = {}

    for deal in deals["deals"]:
        team = deal["team"]
        net = deal["net"]
        if team not in summary:
            summary[team] = {"net": 0, "paid": 0}
        summary[team]["net"] += net
        for _, pct in deal["roles"].items():
            summary[team]["paid"] += round(net * (pct / 100), 2)

    for team, vals in summary.items():
        st.markdown(f"### 🏷️ {team}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Net Commission", f"{vals['net']:.2f}")
        with col2:
            st.metric("Distributed", f"{vals['paid']:.2f}")
        with col3:
            company_share = vals['net'] - vals['paid']
            pct = (company_share / vals['net']) * 100 if vals['net'] else 0
            st.metric("Company Net", f"{company_share:.2f} ({pct:.1f}%)")
        team_data = next((t for t in portfolios['teams'] if t['name'] == team), None)
        if team_data and team_data.get("photo"):
            img_path = os.path.join(PHOTO_DIR, team_data['photo'])
            if os.path.exists(img_path):
                st.image(img_path, width=100, caption=team, use_column_width=False)
        st.divider()
