"""
AI-BASED DIET MANAGEMENT SYSTEM (STREAMLIT WEB APPLICATION)
Deployable on GitHub & Streamlit Community Cloud.
Implemented 100% in Python using Streamlit native components.
"""

import os
import shutil
from datetime import date, datetime
import pandas as pd
import streamlit as st
from PIL import Image

from config import USER_PHOTOS_DIR, DEFAULT_AVATAR, REPORTS_DIR
from database import Database
from models.user_model import UserModel
from models.food_model import FoodModel
from models.diet_model import DietModel
from models.progress_model import ProgressModel
from core.calculations import NutritionCalculator
from core.recommendation import AIRecommendationEngine
from core.ai_assistant import NutritionAssistant
from core.report_generator import ReportGenerator

# -------------------------------------------------------------
# App Configuration & Initial Setup
# -------------------------------------------------------------
st.set_page_config(
    page_title="AI Diet Management System",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-initialize database on startup (MySQL or SQLite fallback)
if "db_initialized" not in st.session_state:
    success, msg = Database.initialize_database()
    st.session_state["db_initialized"] = success
    st.session_state["db_backend"] = Database.get_backend()

# Session State Keys
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None
if "current_profile" not in st.session_state:
    st.session_state["current_profile"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "welcome"
if "onboarding_step" not in st.session_state:
    st.session_state["onboarding_step"] = 1
if "onboarding_data" not in st.session_state:
    st.session_state["onboarding_data"] = {}
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {"role": "assistant", "content": "Hello! I am your AI Nutrition Assistant. Ask me about protein sources, calories in foods, breakfast ideas, or diet strategies."}
    ]

def nav_to(page_name):
    st.session_state["page"] = page_name
    st.rerun()

def refresh_session_user():
    if st.session_state["current_user"]:
        uid = st.session_state["current_user"]["user_id"]
        st.session_state["current_user"] = UserModel.get_user_by_id(uid)
        st.session_state["current_profile"] = UserModel.get_profile(uid)

# -------------------------------------------------------------
# SCREEN 1: WELCOME SCREEN (Step 1)
# -------------------------------------------------------------
def render_welcome_screen():
    st.write("")
    st.write("")
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h1 style='text-align: center; color: #0F766E;'>🥗 DIET MANAGEMENT SYSTEM</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color: #64748B;'>Personalized AI Nutrition & Health Engineering</h4>", unsafe_allow_html=True)
        st.markdown(
            """
            <p style='text-align: center; color: #334155;'>
            Scientifically calculate your clinical BMI, metabolic BMR, and personalized daily energy targets.
            Generate AI-recommended diet plans tailored precisely to your preferences and food allergies.
            </p>
            """,
            unsafe_allow_html=True
        )
        st.write("---")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🚀 GET STARTED", use_container_width=True, type="primary"):
                nav_to("register")
        with c2:
            if st.button("🔑 LOGIN", use_container_width=True):
                nav_to("login")
        with c3:
            if st.button("📝 REGISTER", use_container_width=True):
                nav_to("register")

        st.caption(f"Connected to: **{st.session_state.get('db_backend', 'sqlite').upper()}** Database | Following WHO & Mifflin-St Jeor Standards")

# -------------------------------------------------------------
# SCREEN 2: LOGIN SCREEN
# -------------------------------------------------------------
def render_login_screen():
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h2 style='color: #0F766E;'>🔑 Account Login</h2>", unsafe_allow_html=True)
        st.write("Enter your credentials to access your diet portal.")

        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="name@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("LOGIN", use_container_width=True, type="primary")

            if submit:
                if not email or not password:
                    st.warning("Please enter both email and password.")
                else:
                    user, msg = UserModel.authenticate(email, password)
                    if user:
                        st.session_state["current_user"] = user
                        profile = UserModel.get_profile(user["user_id"])
                        if profile:
                            st.session_state["current_profile"] = profile
                            nav_to("dashboard")
                        else:
                            st.info("Please complete your profile setup.")
                            st.session_state["onboarding_step"] = 1
                            nav_to("onboarding")
                    else:
                        st.error(msg)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back to Welcome", use_container_width=True):
                nav_to("welcome")
        with c2:
            if st.button("Need an account? Register", use_container_width=True):
                nav_to("register")

# -------------------------------------------------------------
# SCREEN 3: REGISTRATION SCREEN (Step 4)
# -------------------------------------------------------------
def render_register_screen():
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h2 style='color: #0F766E;'>📝 Create Account</h2>", unsafe_allow_html=True)
        st.write("Step 1: Sign up to begin your personalized nutrition journey.")

        with st.form("register_form"):
            name = st.text_input("Full Name", placeholder="e.g. Alex Morgan")
            email = st.text_input("Email Address", placeholder="alex@example.com")
            password = st.text_input("Password", type="password", placeholder="At least 4 characters")
            confirm_pw = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
            submit = st.form_submit_button("REGISTER & CONTINUE", use_container_width=True, type="primary")

            if submit:
                if not name or not email or not password or not confirm_pw:
                    st.warning("All fields are required. Please fill in all details.")
                elif "@" not in email or "." not in email:
                    st.warning("Please enter a valid email address.")
                elif len(password) < 4:
                    st.warning("Password must be at least 4 characters long.")
                elif password != confirm_pw:
                    st.error("Passwords do not match. Please verify and try again.")
                else:
                    user_id, msg = UserModel.register_user(name, email, password)
                    if user_id:
                        st.success("Registration Successful! Continuing to Profile Setup...")
                        st.session_state["current_user"] = UserModel.get_user_by_id(user_id)
                        st.session_state["onboarding_data"] = {"user_id": user_id, "name": name, "email": email}
                        st.session_state["onboarding_step"] = 1
                        nav_to("onboarding")
                    else:
                        st.error(msg)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back to Welcome", use_container_width=True):
                nav_to("welcome")
        with c2:
            if st.button("Already registered? Login", use_container_width=True):
                nav_to("login")

# -------------------------------------------------------------
# ONBOARDING WIZARD (Steps 5 – 10)
# -------------------------------------------------------------
def render_onboarding():
    step = st.session_state.get("onboarding_step", 1)
    col_l, col_c, col_r = st.columns([1, 2, 1])

    with col_c:
        st.progress(step / 5, text=f"Step {step} of 5")

        # STEP 1: PHOTO UPLOAD (Step 5)
        if step == 1:
            st.markdown("<h2 style='color: #0F766E;'>📷 Upload Your Photo</h2>", unsafe_allow_html=True)
            st.write("Upload a visual profile photograph for your diet dashboard identity.")

            photo_file = st.file_uploader("Select Photo (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"])
            user_id = st.session_state["current_user"]["user_id"]

            if photo_file:
                ext = os.path.splitext(photo_file.name)[1]
                dest_path = os.path.join(USER_PHOTOS_DIR, f"user_{user_id:03d}{ext}")
                with open(dest_path, "wb") as f:
                    f.write(photo_file.getbuffer())
                UserModel.update_photo(user_id, dest_path)
                st.session_state["current_user"]["profile_photo"] = dest_path
                st.image(dest_path, caption="Profile Photo Preview", width=180)
                st.success("Photo uploaded successfully!")
            else:
                current_p = st.session_state["current_user"].get("profile_photo")
                if current_p and os.path.exists(current_p):
                    st.image(current_p, caption="Current Profile Photo", width=180)
                else:
                    st.image(DEFAULT_AVATAR, caption="Default Avatar", width=140)

            st.info(
                "**IMPORTANT ETHICAL & MEDICAL NOTICE:**\n"
                "The photograph is strictly used as your visual account identity. "
                "The system does NOT claim or attempt to infer body composition, BMI, "
                "health conditions, or nutritional advice from images."
            )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Skip for Now", use_container_width=True):
                    if not st.session_state["current_user"].get("profile_photo"):
                        UserModel.update_photo(user_id, DEFAULT_AVATAR)
                    st.session_state["onboarding_step"] = 2
                    st.rerun()
            with c2:
                if st.button("CONTINUE →", use_container_width=True, type="primary"):
                    if not st.session_state["current_user"].get("profile_photo"):
                        UserModel.update_photo(user_id, DEFAULT_AVATAR)
                    st.session_state["onboarding_step"] = 2
                    st.rerun()

        # STEP 2: HEIGHT INPUT (Step 6)
        elif step == 2:
            st.markdown("<h2 style='color: #0F766E;'>📏 Enter Your Height</h2>", unsafe_allow_html=True)
            st.write("Height is utilized for scientific BMI and metabolic BMR computations.")

            height_val = st.number_input(
                "Height (in cm):",
                min_value=60.0,
                max_value=250.0,
                value=float(st.session_state["onboarding_data"].get("height", 170.0)),
                step=0.5
            )
            st.caption("Quick tip: 5'0\" ≈ 152 cm | 5'6\" ≈ 168 cm | 5'10\" ≈ 178 cm | 6'0\" ≈ 183 cm")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Back", use_container_width=True):
                    st.session_state["onboarding_step"] = 1
                    st.rerun()
            with c2:
                if st.button("CONTINUE →", use_container_width=True, type="primary"):
                    st.session_state["onboarding_data"]["height"] = height_val
                    st.session_state["onboarding_step"] = 3
                    st.rerun()

        # STEP 3: WEIGHT INPUT (Step 7)
        elif step == 3:
            st.markdown("<h2 style='color: #0F766E;'>⚖️ Enter Your Weight</h2>", unsafe_allow_html=True)
            st.write("Weight is used for BMI calculation and daily energy expenditure targets.")

            weight_val = st.number_input(
                "Current Weight (in kg):",
                min_value=25.0,
                max_value=300.0,
                value=float(st.session_state["onboarding_data"].get("weight", 68.0)),
                step=0.5
            )
            st.caption("Enter your current morning weight in kilograms (e.g. 68.5 kg).")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Back", use_container_width=True):
                    st.session_state["onboarding_step"] = 2
                    st.rerun()
            with c2:
                if st.button("CONTINUE →", use_container_width=True, type="primary"):
                    st.session_state["onboarding_data"]["weight"] = weight_val
                    st.session_state["onboarding_step"] = 4
                    st.rerun()

        # STEP 4: DIET PREFERENCE (Step 8)
        elif step == 4:
            st.markdown("<h2 style='color: #0F766E;'>🥗 What Type of Diet Do You Follow?</h2>", unsafe_allow_html=True)
            st.write("The AI recommendation engine strictly filters food choices based on this selection.")

            diet_options = ["Vegetarian", "Non-Vegetarian", "Vegan"]
            diet_choice = st.radio(
                "Select Diet Preference:",
                diet_options,
                index=0,
                captions=[
                    "🌱 Plant foods, grains, legumes, dairy & dairy products (no meat or seafood)",
                    "🍗 Complete diet including poultry, fish, eggs, dairy, and plant foods",
                    "🌿 100% plant-based (no meat, poultry, seafood, dairy, or eggs)"
                ]
            )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Back", use_container_width=True):
                    st.session_state["onboarding_step"] = 3
                    st.rerun()
            with c2:
                if st.button("CONTINUE →", use_container_width=True, type="primary"):
                    st.session_state["onboarding_data"]["diet_type"] = diet_choice
                    st.session_state["onboarding_step"] = 5
                    st.rerun()

        # STEP 5: ADDITIONAL INFO & PROFILE CREATION (Steps 9 & 10)
        elif step == 5:
            st.markdown("<h2 style='color: #0F766E;'>📋 Complete Your Nutrition Profile</h2>", unsafe_allow_html=True)
            st.write("Specify your age, gender, activity level, fitness goal, and food allergies.")

            with st.form("details_form"):
                ca, cg = st.columns(2)
                with ca:
                    age_val = st.number_input("Age (years)", min_value=8, max_value=120, value=25)
                with cg:
                    gender_val = st.selectbox("Gender", ["Male", "Female", "Other"])

                act_val = st.selectbox(
                    "Activity Level",
                    ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"],
                    index=2
                )

                goal_val = st.selectbox(
                    "Primary Fitness Goal",
                    ["Maintain general fitness", "Healthy weight management", "Improve nutrition"],
                    index=0
                )

                allergy_choices = st.multiselect(
                    "Food Allergies / Dietary Intolerances",
                    ["Peanuts", "Milk", "Eggs", "Soy", "Seafood", "None"],
                    default=["None"]
                )
                other_allergy = st.text_input("Other allergies (optional, comma-separated):", placeholder="e.g. Gluten, Tree nuts")

                submit = st.form_submit_button("CREATE PROFILE & VIEW DASHBOARD →", use_container_width=True, type="primary")

                if submit:
                    allergens_list = [a for a in allergy_choices if a != "None"]
                    if other_allergy.strip():
                        allergens_list.extend([x.strip() for x in other_allergy.split(",") if x.strip()])
                    allergies_str = ", ".join(allergens_list) if allergens_list else "None"

                    data = st.session_state["onboarding_data"]
                    height = float(data.get("height", 170.0))
                    weight = float(data.get("weight", 68.0))
                    diet_type = data.get("diet_type", "Vegetarian")
                    user_id = st.session_state["current_user"]["user_id"]

                    targets = NutritionCalculator.calculate_nutrition_targets(
                        height_cm=height,
                        weight_kg=weight,
                        age=int(age_val),
                        gender=gender_val,
                        activity_level=act_val,
                        goal=goal_val
                    )

                    profile_payload = {
                        "height": height,
                        "weight": weight,
                        "diet_type": diet_type,
                        "age": int(age_val),
                        "gender": gender_val,
                        "activity_level": act_val,
                        "goal": goal_val,
                        "allergies": allergies_str,
                        "bmi": targets["bmi"],
                        "bmi_category": targets["bmi_category"],
                        "bmr": targets["bmr"],
                        "daily_calories": targets["daily_calories"],
                        "target_protein": targets["target_protein"],
                        "target_carbs": targets["target_carbs"],
                        "target_fat": targets["target_fat"],
                        "target_fiber": targets["target_fiber"],
                        "target_water": targets["target_water"]
                    }

                    UserModel.save_or_update_profile(user_id, profile_payload)
                    refresh_session_user()
                    st.success("Profile created successfully! Loading Dashboard...")
                    nav_to("dashboard")

# -------------------------------------------------------------
# DASHBOARD (Steps 21 – 27)
# -------------------------------------------------------------
def render_dashboard():
    refresh_session_user()
    user = st.session_state["current_user"]
    profile = st.session_state["current_profile"]

    if not user or not profile:
        nav_to("login")
        return

    # Sidebar Profile Card
    with st.sidebar:
        st.markdown("### 👤 User Profile Card")

        photo_path = user.get("profile_photo")
        if photo_path and os.path.exists(photo_path):
            st.image(photo_path, width=140)
        else:
            st.image(DEFAULT_AVATAR, width=140)

        st.markdown(f"**Welcome, {user.get('name', 'User')}**")
        st.caption(f"Email: {user.get('email')}")

        st.write("---")
        bmi = profile.get("bmi", 0)
        bmi_cat = profile.get("bmi_category", "Normal")
        st.metric("Body Mass Index (BMI)", f"{bmi}", f"{bmi_cat}")
        st.metric("Daily Energy Target", f"{profile.get('daily_calories', 0)} kcal")
        st.metric("Protein Target", f"{profile.get('target_protein', 0)} g")

        st.markdown(f"**Diet:** {profile.get('diet_type')}")
        st.markdown(f"**Goal:** {profile.get('goal')}")
        st.markdown(f"**Allergies:** {profile.get('allergies', 'None')}")

        st.write("---")
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["current_user"] = None
            st.session_state["current_profile"] = None
            nav_to("welcome")

    # Main Tabs
    tab_diet, tab_search, tab_progress, tab_history, tab_assistant, tab_report, tab_profile = st.tabs([
        "✨ AI Diet Plan",
        "🔍 Food Database",
        "📈 Progress Tracker",
        "📜 Diet History",
        "🤖 AI Assistant",
        "📄 Nutrition Report",
        "👤 My Profile"
    ])

    # TAB 1: AI DIET PLAN
    with tab_diet:
        st.markdown("<h3 style='color: #0F766E;'>✨ AI Personalized Diet Plan Generator</h3>", unsafe_allow_html=True)
        st.caption(
            f"Targets: **{profile.get('daily_calories')} kcal** | "
            f"Protein: **{profile.get('target_protein')}g** | Diet: **{profile.get('diet_type')}** | "
            f"Allergies: **{profile.get('allergies')}**"
        )

        c_gen, c_save = st.columns([2, 1])
        with c_gen:
            if st.button("⚡ GENERATE MY DIET PLAN", type="primary", use_container_width=True):
                plan = AIRecommendationEngine.generate_personalized_plan(profile)
                st.session_state["latest_generated_plan"] = plan

        plan = st.session_state.get("latest_generated_plan")

        if plan:
            st.write("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Calories", f"{plan['total_calories']} kcal", f"Target: {plan['target_calories']}")
            m2.metric("Total Protein", f"{plan['total_protein']} g")
            m3.metric("Carbohydrates", f"{plan['total_carbs']} g")
            m4.metric("Healthy Fats", f"{plan['total_fat']} g")

            col_b, col_l = st.columns(2)
            col_s, col_d = st.columns(2)

            meal_cols = {"Breakfast": col_b, "Lunch": col_l, "Snack": col_s, "Dinner": col_d}
            meal_icons = {"Breakfast": "🍳", "Lunch": "🥗", "Snack": "🍎", "Dinner": "🍲"}

            for m_name, col in meal_cols.items():
                m_data = plan["meals"][m_name]
                with col:
                    with st.container(border=True):
                        st.markdown(f"#### {meal_icons[m_name]} {m_name.upper()}")
                        st.caption(f"**{m_data['actual_calories']} kcal** | Protein: {m_data['actual_protein']}g | Carbs: {m_data['actual_carbs']}g | Fat: {m_data['actual_fat']}g")
                        st.write("---")
                        for it in m_data["items"]:
                            st.markdown(f"• **{it['name']}** ({it['portion']})  \n*{it['calories']} kcal | P: {it['protein']}g | C: {it['carbs']}g | F: {it['fat']}g*")

            st.write("---")
            if st.button("💾 SAVE THIS DIET PLAN TO DATABASE", use_container_width=True):
                today_str = date.today().isoformat()
                def format_items(key):
                    return "; ".join([f"{x['name']} ({x['portion']}, {x['calories']} kcal)" for x in plan['meals'][key]['items']])

                DietModel.save_plan(
                    user_id=user["user_id"],
                    plan_date=today_str,
                    total_calories=plan["total_calories"],
                    total_protein=plan["total_protein"],
                    total_carbs=plan["total_carbs"],
                    total_fat=plan["total_fat"],
                    breakfast_items=format_items("Breakfast"),
                    lunch_items=format_items("Lunch"),
                    snack_items=format_items("Snack"),
                    dinner_items=format_items("Dinner")
                )
                st.success("Plan successfully saved to database! You can view it under 'Diet History'.")
        else:
            st.info("Click **'GENERATE MY DIET PLAN'** above to compute and balance your meals.")

    # TAB 2: FOOD DATABASE SEARCH
    with tab_search:
        st.markdown("<h3 style='color: #0F766E;'>🔍 Food Database Explorer</h3>", unsafe_allow_html=True)
        c_kw, c_cat, c_diet = st.columns([2, 1, 1])
        with c_kw:
            kw = st.text_input("Search Food by Name:", placeholder="e.g. Oats, Paneer, Rice, Chicken...")
        with c_cat:
            categories = ["All"] + FoodModel.get_all_categories()
            cat = st.selectbox("Category Filter:", categories)
        with c_diet:
            diet_filter = st.selectbox("Diet Filter:", ["All", "Vegetarian", "Non-Vegetarian", "Vegan"])

        results = FoodModel.search_foods(keyword=kw, category=cat, diet_type=diet_filter)
        st.caption(f"Found **{len(results)}** food items in the database.")

        if results:
            df = pd.DataFrame(results)[[
                "food_name", "category", "calories", "protein", "carbohydrates",
                "fat", "fiber", "meal_type", "diet_type", "allergens", "serving_size"
            ]]
            df.columns = [
                "Food Name", "Category", "Calories (kcal)", "Protein (g)",
                "Carbs (g)", "Fat (g)", "Fiber (g)", "Meal Type", "Diet Type",
                "Allergens", "Serving Size"
            ]
            st.dataframe(df, use_container_width=True, hide_index=True)

    # TAB 3: PROGRESS TRACKER
    with tab_progress:
        st.markdown("<h3 style='color: #0F766E;'>📈 Daily Progress & Biometrics Tracker</h3>", unsafe_allow_html=True)
        col_form, col_stats = st.columns([1, 1])
        with col_form:
            with st.container(border=True):
                st.markdown("#### Log Today's Entry")
                with st.form("progress_log_form"):
                    log_date = st.date_input("Date", value=date.today())
                    p_weight = st.number_input("Current Weight (kg)", min_value=25.0, max_value=300.0, value=float(profile.get("weight", 70.0)), step=0.1)
                    p_water = st.number_input("Water Intake (Liters)", min_value=0.0, max_value=15.0, value=2.5, step=0.1)
                    p_cals = st.number_input("Calories Consumed (kcal)", min_value=0.0, max_value=10000.0, value=float(profile.get("daily_calories", 2000.0)), step=50.0)
                    p_notes = st.text_input("Daily Reflection / Notes", placeholder="e.g. Energy levels great, worked out")
                    p_submit = st.form_submit_button("ADD RECORD TO DATABASE", use_container_width=True, type="primary")

                    if p_submit:
                        ProgressModel.add_log(
                            user_id=user["user_id"],
                            log_date=log_date.isoformat(),
                            current_weight=p_weight,
                            water_intake=p_water,
                            calories_consumed=p_cals,
                            notes=p_notes
                        )
                        st.success("Progress log recorded successfully!")
                        st.rerun()

        logs = ProgressModel.get_user_logs(user["user_id"])
        with col_stats:
            with st.container(border=True):
                st.markdown("#### Progress Summary")
                if logs:
                    count = len(logs)
                    latest_wt = logs[0].get("current_weight")
                    first_wt = logs[-1].get("current_weight")
                    delta = round(latest_wt - first_wt, 1)
                    avg_water = round(sum(l.get("water_intake", 0) for l in logs) / count, 1)

                    s1, s2 = st.columns(2)
                    s1.metric("Total Log Entries", f"{count}")
                    s2.metric("Latest Weight", f"{latest_wt} kg", f"{delta:+} kg")
                    s3, s4 = st.columns(2)
                    s3.metric("Avg Daily Water", f"{avg_water} L")
                    s4.metric("Starting Weight", f"{first_wt} kg")
                else:
                    st.info("No progress logs recorded yet.")

        if logs:
            st.write("---")
            st.markdown("#### Historical Records")
            df_logs = pd.DataFrame(logs)[["log_date", "current_weight", "water_intake", "calories_consumed", "notes"]]
            df_logs.columns = ["Date", "Weight (kg)", "Water (L)", "Calories (kcal)", "Notes"]
            st.dataframe(df_logs, use_container_width=True, hide_index=True)

            if len(logs) > 1:
                st.markdown("#### Weight Trend")
                chart_data = df_logs.sort_values("Date")[["Date", "Weight (kg)"]].set_index("Date")
                st.line_chart(chart_data)

    # TAB 4: DIET HISTORY
    with tab_history:
        st.markdown("<h3 style='color: #0F766E;'>📜 Saved Diet Plan History</h3>", unsafe_allow_html=True)
        plans = DietModel.get_user_plans(user["user_id"])

        if plans:
            st.write(f"Showing **{len(plans)}** saved plan(s) from database.")
            for p in plans:
                with st.expander(f"Plan #{p['plan_id']} — {p['plan_date']} ({p['total_calories']} kcal | P: {p['total_protein']}g, C: {p['total_carbs']}g, F: {p['total_fat']}g)"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**🍳 Breakfast:**  \n{p['breakfast_items']}")
                        st.markdown(f"**🥗 Lunch:**  \n{p['lunch_items']}")
                    with c2:
                        st.markdown(f"**🍎 Snack:**  \n{p['snack_items']}")
                        st.markdown(f"**🍲 Dinner:**  \n{p['dinner_items']}")
        else:
            st.info("No saved diet plans found. Generate and save a plan in 'AI Diet Plan'.")

    # TAB 5: AI NUTRITION ASSISTANT
    with tab_assistant:
        st.markdown("<h3 style='color: #0F766E;'>🤖 AI Nutrition & Food Assistant</h3>", unsafe_allow_html=True)
        st.write("Ask natural nutrition questions or click a quick prompt below:")

        q_cols = st.columns(4)
        quick_questions = [
            "What foods are high in protein?",
            "What can I eat for breakfast?",
            "Show vegetarian foods",
            "What is the calorie value of rice?"
        ]
        for idx, qq in enumerate(quick_questions):
            if q_cols[idx].button(qq, key=f"qq_{idx}", use_container_width=True):
                st.session_state["chat_messages"].append({"role": "user", "content": qq})
                resp = NutritionAssistant.respond_to_query(qq, profile)
                st.session_state["chat_messages"].append({"role": "assistant", "content": resp})
                st.rerun()

        for msg in st.session_state["chat_messages"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_query = st.chat_input("Ask a nutrition question...")
        if user_query:
            st.session_state["chat_messages"].append({"role": "user", "content": user_query})
            resp = NutritionAssistant.respond_to_query(user_query, profile)
            st.session_state["chat_messages"].append({"role": "assistant", "content": resp})
            st.rerun()

    # TAB 6: NUTRITION REPORT
    with tab_report:
        st.markdown("<h3 style='color: #0F766E;'>📄 Personal Nutrition & Health Report</h3>", unsafe_allow_html=True)
        c_down1, c_down2 = st.columns(2)
        pdf_path = ReportGenerator.generate_pdf_report(user, profile)
        txt_path = ReportGenerator.generate_text_report(user, profile)

        with c_down1:
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    "📑 DOWNLOAD PDF REPORT",
                    data=pdf_bytes,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )

        with c_down2:
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    txt_content = f.read()
                st.download_button(
                    "📝 DOWNLOAD TEXT SUMMARY",
                    data=txt_content,
                    file_name=os.path.basename(txt_path),
                    mime="text/plain",
                    use_container_width=True
                )

        st.write("---")
        st.markdown("#### Report Summary Preview")
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                st.code(f.read(), language="text")

    # TAB 7: EDIT PROFILE
    with tab_profile:
        st.markdown("<h3 style='color: #0F766E;'>👤 Edit Profile & Recalculate Metrics</h3>", unsafe_allow_html=True)
        with st.form("edit_profile_form"):
            c_h, c_w = st.columns(2)
            with c_h:
                new_h = st.number_input("Height (cm)", min_value=60.0, max_value=260.0, value=float(profile.get("height", 170.0)), step=0.5)
            with c_w:
                new_w = st.number_input("Weight (kg)", min_value=25.0, max_value=300.0, value=float(profile.get("weight", 70.0)), step=0.5)

            c_a, c_g = st.columns(2)
            with c_a:
                new_age = st.number_input("Age (years)", min_value=8, max_value=120, value=int(profile.get("age", 25)))
            with c_g:
                g_opts = ["Male", "Female", "Other"]
                curr_g_idx = g_opts.index(profile.get("gender", "Male")) if profile.get("gender") in g_opts else 0
                new_g = st.selectbox("Gender", g_opts, index=curr_g_idx)

            d_opts = ["Vegetarian", "Non-Vegetarian", "Vegan"]
            curr_d_idx = d_opts.index(profile.get("diet_type", "Vegetarian")) if profile.get("diet_type") in d_opts else 0
            new_diet = st.selectbox("Diet Preference", d_opts, index=curr_d_idx)

            act_opts = ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"]
            curr_act_idx = act_opts.index(profile.get("activity_level", "Moderately Active")) if profile.get("activity_level") in act_opts else 2
            new_act = st.selectbox("Activity Level", act_opts, index=curr_act_idx)

            goal_opts = ["Maintain general fitness", "Healthy weight management", "Improve nutrition"]
            curr_goal_idx = goal_opts.index(profile.get("goal", "Maintain general fitness")) if profile.get("goal") in goal_opts else 0
            new_goal = st.selectbox("Primary Goal", goal_opts, index=curr_goal_idx)

            new_allergies = st.text_input("Allergies (comma-separated):", value=profile.get("allergies", "None"))

            save_btn = st.form_submit_button("SAVE CHANGES & RECALCULATE TARGETS", use_container_width=True, type="primary")

            if save_btn:
                targets = NutritionCalculator.calculate_nutrition_targets(
                    height_cm=new_h,
                    weight_kg=new_w,
                    age=new_age,
                    gender=new_g,
                    activity_level=new_act,
                    goal=new_goal
                )

                update_payload = {
                    "height": new_h,
                    "weight": new_w,
                    "diet_type": new_diet,
                    "age": new_age,
                    "gender": new_g,
                    "activity_level": new_act,
                    "goal": new_goal,
                    "allergies": new_allergies or "None",
                    "bmi": targets["bmi"],
                    "bmi_category": targets["bmi_category"],
                    "bmr": targets["bmr"],
                    "daily_calories": targets["daily_calories"],
                    "target_protein": targets["target_protein"],
                    "target_carbs": targets["target_carbs"],
                    "target_fat": targets["target_fat"],
                    "target_fiber": targets["target_fiber"],
                    "target_water": targets["target_water"]
                }
                UserModel.save_or_update_profile(user["user_id"], update_payload)
                refresh_session_user()
                st.success("Profile and nutrition targets successfully updated!")
                st.rerun()

# -------------------------------------------------------------
# Main Application Router
# -------------------------------------------------------------
def main():
    current_page = st.session_state.get("page", "welcome")

    if current_page == "welcome":
        render_welcome_screen()
    elif current_page == "login":
        render_login_screen()
    elif current_page == "register":
        render_register_screen()
    elif current_page == "onboarding":
        render_onboarding()
    elif current_page == "dashboard":
        render_dashboard()
    else:
        render_welcome_screen()

if __name__ == "__main__":
    main()
  """
AI Recommendation Engine Module
Implements intelligent diet analysis, multi-factor food scoring, allergy-safe filtering,
and personalized meal plan generation.
"""

from models.food_model import FoodModel

class AIRecommendationEngine:
    MEAL_DISTRIBUTION = {
        "Breakfast": 0.25,
        "Lunch": 0.35,
        "Snack": 0.15,
        "Dinner": 0.25
    }

    @classmethod
    def score_food(cls, food: dict, meal_name: str, target_calories: float, target_protein: float, goal: str) -> float:
        """
        Step 19: Score suitable foods based on:
        - Calorie suitability
        - Protein suitability
        - Nutritional value (fiber, healthy macros)
        - Meal type match
        - User goal
        """
        score = 50.0

        if food.get('meal_type') == meal_name:
            score += 25.0
        elif food.get('meal_type') in ('Any', 'All'):
            score += 15.0

        food_cals = float(food.get('calories', 100))
        ideal_item_cal = target_calories * 0.5
        cal_diff = abs(food_cals - ideal_item_cal)
        cal_score = max(0.0, 20.0 - (cal_diff / 25.0))
        score += cal_score

        protein = float(food.get('protein', 0))
        fiber = float(food.get('fiber', 0))
        fat = float(food.get('fat', 0))

        protein_ratio = protein / max(food_cals, 1.0) * 100.0
        score += min(protein_ratio * 1.5, 20.0)
        score += min(fiber * 2.0, 10.0)

        goal_lower = goal.lower()
        if "weight management" in goal_lower:
            score += (protein * 0.8) + (fiber * 1.5) - (fat * 0.4)
        elif "nutrition" in goal_lower:
            score += (fiber * 1.5) + (protein * 0.5)

        return round(score, 2)

    @classmethod
    def generate_personalized_plan(cls, user_profile: dict) -> dict:
        """
        Steps 16-20: AI Diet Plan Generation.
        1. Fetch safe foods filtered by Diet Preference and Allergies.
        2. Score foods for each meal category.
        3. Select optimal combination of complementary foods.
        4. Calculate total macronutrients and portions.
        """
        diet_type = user_profile.get('diet_type', 'Vegetarian')
        allergies_str = user_profile.get('allergies', 'None')
        allergies_list = [a.strip() for a in allergies_str.split(',') if a.strip()]
        
        target_calories = float(user_profile.get('daily_calories', 2000))
        target_protein = float(user_profile.get('target_protein', 70))
        goal = user_profile.get('goal', 'Maintain general fitness')

        safe_foods = FoodModel.get_safe_foods_for_diet_and_allergies(diet_type, allergies_list)
        if not safe_foods:
            safe_foods = FoodModel.get_all_foods()

        meal_plans = {}
        total_plan_cals = 0.0
        total_plan_protein = 0.0
        total_plan_carbs = 0.0
        total_plan_fat = 0.0

        for meal_name, cal_ratio in cls.MEAL_DISTRIBUTION.items():
            meal_target_cal = target_calories * cal_ratio
            meal_target_protein = target_protein * cal_ratio

            scored_foods = []
            for food in safe_foods:
                s = cls.score_food(food, meal_name, meal_target_cal, meal_target_protein, goal)
                scored_foods.append((s, food))

            scored_foods.sort(key=lambda x: x[0], reverse=True)

            selected_items = []
            chosen_categories = set()
            for score, food in scored_foods:
                cat = food.get('category')
                if cat not in chosen_categories:
                    selected_items.append(food)
                    chosen_categories.add(cat)
                if len(selected_items) >= 2:
                    break

            if len(selected_items) < 2 and len(scored_foods) > 1:
                selected_items.append(scored_foods[1][1])

            raw_cals = sum(float(item.get('calories', 100)) for item in selected_items)
            multiplier = meal_target_cal / max(raw_cals, 50.0)
            multiplier = max(0.7, min(multiplier, 2.2))

            items_detail = []
            meal_cal = 0.0
            meal_prot = 0.0
            meal_carb = 0.0
            meal_fat = 0.0

            for item in selected_items:
                portion = round(multiplier, 1)
                item_cal = round(float(item.get('calories', 0)) * portion, 1)
                item_prot = round(float(item.get('protein', 0)) * portion, 1)
                item_carb = round(float(item.get('carbohydrates', 0)) * portion, 1)
                item_fat = round(float(item.get('fat', 0)) * portion, 1)

                meal_cal += item_cal
                meal_prot += item_prot
                meal_carb += item_carb
                meal_fat += item_fat

                serving_info = item.get('serving_size', '100g')
                items_detail.append({
                    "name": item.get('food_name'),
                    "portion": f"{portion}x ({serving_info})",
                    "calories": item_cal,
                    "protein": item_prot,
                    "carbs": item_carb,
                    "fat": item_fat,
                    "category": item.get('category')
                })

            total_plan_cals += meal_cal
            total_plan_protein += meal_prot
            total_plan_carbs += meal_carb
            total_plan_fat += meal_fat

            meal_plans[meal_name] = {
                "target_calories": round(meal_target_cal, 1),
                "actual_calories": round(meal_cal, 1),
                "actual_protein": round(meal_prot, 1),
                "actual_carbs": round(meal_carb, 1),
                "actual_fat": round(meal_fat, 1),
                "items": items_detail
            }

        return {
            "total_calories": round(total_plan_cals, 1),
            "total_protein": round(total_plan_protein, 1),
            "total_carbs": round(total_plan_carbs, 1),
            "total_fat": round(total_plan_fat, 1),
            "target_calories": round(target_calories, 1),
            "meals": meal_plans,
            "diet_type": diet_type,
            "allergies": allergies_str
        }
      """
Unified Database Module (MySQL & SQLite Auto-Fallback)
Connects to MySQL if available; automatically falls back to local SQLite for
seamless GitHub repository cloning and Streamlit Community Cloud deployment.
"""

import os
import sqlite3
from config import DB_CONFIG, BASE_DIR

SQLITE_DB_PATH = os.path.join(BASE_DIR, "diet_management.db")

class Database:
    _backend = None

    @classmethod
    def get_backend(cls):
        if cls._backend:
            return cls._backend
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=DB_CONFIG.get("host", "localhost"),
                port=DB_CONFIG.get("port", 3306),
                user=DB_CONFIG.get("user", "root"),
                password=DB_CONFIG.get("password", "mysql"),
                connect_timeout=3
            )
            conn.close()
            cls._backend = 'mysql'
            return 'mysql'
        except Exception:
            cls._backend = 'sqlite'
            return 'sqlite'

    @classmethod
    def get_connection(cls):
        backend = cls.get_backend()
        if backend == 'mysql':
            import mysql.connector
            return mysql.connector.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=DB_CONFIG["database"],
                autocommit=True
            )
        else:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn

    @classmethod
    def execute_query(cls, query, params=None, fetchone=False, fetchall=False, commit=False):
        backend = cls.get_backend()
        conn = cls.get_connection()
        params = params or ()

        try:
            if backend == 'mysql':
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params)
                result = None
                if fetchone:
                    result = cursor.fetchone()
                elif fetchall:
                    result = cursor.fetchall()
                elif commit:
                    conn.commit()
                    result = cursor.lastrowid
                cursor.close()
                return result
            else:
                sqlite_query = query.replace("%s", "?")
                cursor = conn.cursor()
                cursor.execute(sqlite_query, params)
                result = None
                if fetchone:
                    row = cursor.fetchone()
                    result = dict(row) if row else None
                elif fetchall:
                    rows = cursor.fetchall()
                    result = [dict(r) for r in rows] if rows else []
                elif commit:
                    conn.commit()
                    result = cursor.lastrowid
                cursor.close()
                return result
        finally:
            conn.close()
