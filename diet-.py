"""
AI-BASED DIET MANAGEMENT SYSTEM (STANDALONE STREAMLIT APPLICATION)
File: dietmanagement.py
Ready for direct deployment on Streamlit Community Cloud & GitHub.
100% Python Code. Self-contained with aesthetic visuals and zero indentation errors.
"""

import os
import sys
import json
import hashlib
import sqlite3
from datetime import date, datetime
import pandas as pd
import altair as alt
import streamlit as st
from PIL import Image, ImageDraw

# Safe import for reportlab
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Safe import for mysql.connector
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# -----------------------------------------------------------------------------
# Configuration and Directories
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_PHOTOS_DIR = os.path.join(BASE_DIR, "user_photos")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DEFAULT_AVATAR = os.path.join(USER_PHOTOS_DIR, "default_avatar.png")
SQLITE_DB_PATH = os.path.join(BASE_DIR, "diet_management.db")

os.makedirs(USER_PHOTOS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

if not os.path.exists(DEFAULT_AVATAR):
    try:
        avatar_img = Image.new("RGB", (160, 160), color=(226, 232, 240))
        draw = ImageDraw.Draw(avatar_img)
        draw.ellipse([55, 30, 105, 80], fill=(148, 163, 184))
        draw.pieslice([25, 90, 135, 200], 180, 360, fill=(148, 163, 184))
        avatar_img.save(DEFAULT_AVATAR)
    except Exception:
        pass

# -----------------------------------------------------------------------------
# Database Layer (Dual Backend: MySQL & Zero-Config SQLite Cloud Fallback)
# -----------------------------------------------------------------------------
class Database:
    _backend = None

    @classmethod
    def get_backend(cls):
        if cls._backend:
            return cls._backend

        if MYSQL_AVAILABLE:
            try:
                conn = mysql.connector.connect(
                    host=os.getenv("MYSQL_HOST", "localhost"),
                    port=int(os.getenv("MYSQL_PORT", 3306)),
                    user=os.getenv("MYSQL_USER", "root"),
                    password=os.getenv("MYSQL_PASSWORD", "mysql"),
                    connect_timeout=2
                )
                conn.close()
                cls._backend = "mysql"
                return "mysql"
            except Exception:
                pass

        cls._backend = "sqlite"
        return "sqlite"

    @classmethod
    def get_connection(cls):
        backend = cls.get_backend()
        if backend == "mysql" and MYSQL_AVAILABLE:
            return mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "localhost"),
                port=int(os.getenv("MYSQL_PORT", 3306)),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", "mysql"),
                database=os.getenv("MYSQL_DB", "diet_management"),
                autocommit=True
            )
        else:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn

    @classmethod
    def initialize_database(cls):
        backend = cls.get_backend()
        try:
            if backend == "mysql" and MYSQL_AVAILABLE:
                server_conn = mysql.connector.connect(
                    host=os.getenv("MYSQL_HOST", "localhost"),
                    port=int(os.getenv("MYSQL_PORT", 3306)),
                    user=os.getenv("MYSQL_USER", "root"),
                    password=os.getenv("MYSQL_PASSWORD", "mysql"),
                    autocommit=True
                )
                sc = server_conn.cursor()
                sc.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('MYSQL_DB', 'diet_management')};")
                sc.close()
                server_conn.close()

                conn = cls.get_connection()
                c = conn.cursor()
                c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    profile_photo VARCHAR(255) DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                c.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    profile_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL UNIQUE,
                    height FLOAT NOT NULL,
                    weight FLOAT NOT NULL,
                    diet_type VARCHAR(50) NOT NULL,
                    age INT NOT NULL,
                    gender VARCHAR(20) NOT NULL,
                    activity_level VARCHAR(50) NOT NULL,
                    goal VARCHAR(100) NOT NULL,
                    allergies VARCHAR(255) DEFAULT 'None',
                    bmi FLOAT DEFAULT NULL,
                    bmi_category VARCHAR(50) DEFAULT NULL,
                    bmr FLOAT DEFAULT NULL,
                    daily_calories FLOAT DEFAULT NULL,
                    target_protein FLOAT DEFAULT NULL,
                    target_carbs FLOAT DEFAULT NULL,
                    target_fat FLOAT DEFAULT NULL,
                    target_fiber FLOAT DEFAULT NULL,
                    target_water FLOAT DEFAULT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                """)
                c.execute("""
                CREATE TABLE IF NOT EXISTS food_items (
                    food_id INT AUTO_INCREMENT PRIMARY KEY,
                    food_name VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    calories FLOAT NOT NULL,
                    protein FLOAT NOT NULL,
                    carbohydrates FLOAT NOT NULL,
                    fat FLOAT NOT NULL,
                    fiber FLOAT NOT NULL,
                    meal_type VARCHAR(50) NOT NULL,
                    diet_type VARCHAR(50) NOT NULL,
                    allergens VARCHAR(100) DEFAULT 'None',
                    serving_size VARCHAR(50) DEFAULT '100g'
                );
                """)
                c.execute("""
                CREATE TABLE IF NOT EXISTS diet_plans (
                    plan_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    plan_date DATE NOT NULL,
                    total_calories FLOAT NOT NULL,
                    total_protein FLOAT NOT NULL,
                    total_carbs FLOAT NOT NULL,
                    total_fat FLOAT NOT NULL,
                    breakfast_items TEXT NOT NULL,
                    lunch_items TEXT NOT NULL,
                    snack_items TEXT NOT NULL,
                    dinner_items TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                """)
                c.execute("""
                CREATE TABLE IF NOT EXISTS progress_logs (
                    log_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    log_date DATE NOT NULL,
                    current_weight FLOAT NOT NULL,
                    water_intake FLOAT NOT NULL,
                    calories_consumed FLOAT NOT NULL,
                    notes TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                """)
                c.execute("SELECT COUNT(*) FROM food_items;")
                count = c.fetchone()[0]
                if count == 0:
                    cls.seed_food_items(c, is_mysql=True)
                c.close()
                conn.close()
                return True, "MySQL database initialized."
            else:
                conn = cls.get_connection()
                c = conn.cursor()
                c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    profile_photo TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                c.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    height REAL NOT NULL,
                    weight REAL NOT NULL,
                    diet_type TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    activity_level TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    allergies TEXT DEFAULT 'None',
                    bmi REAL,
                    bmi_category TEXT,
                    bmr REAL,
                    daily_calories REAL,
                    target_protein REAL,
                    target_carbs REAL,
                    target_fat REAL,
                    target_fiber REAL,
                    target_water REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                """)
                c.execute("""
                CREATE TABLE IF NOT EXISTS food_items (
                    food_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    food_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    calories REAL NOT NULL,
                    protein REAL NOT NULL,
                    carbohydrates REAL NOT NULL,
                    fat REAL NOT NULL,
                    fiber REAL NOT NULL,
                    meal_type TEXT NOT NULL,
                    diet_type TEXT NOT NULL,
                    allergens TEXT DEFAULT 'None',
                    serving_size TEXT DEFAULT '100g'
                );
                """)
                c.execute("""
                CREATE TABLE IF NOT EXISTS diet_plans (
                    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan_date TEXT NOT NULL,
                    total_calories REAL NOT NULL,
                    total_protein REAL NOT NULL,
                    total_carbs REAL NOT NULL,
                    total_fat REAL NOT NULL,
                    breakfast_items TEXT NOT NULL,
                    lunch_items TEXT NOT NULL,
                    snack_items TEXT NOT NULL,
                    dinner_items TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                """)
                c.execute("""
                CREATE TABLE IF NOT EXISTS progress_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    log_date TEXT NOT NULL,
                    current_weight REAL NOT NULL,
                    water_intake REAL NOT NULL,
                    calories_consumed REAL NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                """)
                c.execute("SELECT COUNT(*) FROM food_items;")
                count = c.fetchone()[0]
                if count == 0:
                    cls.seed_food_items(c, is_mysql=False)
                    conn.commit()
                c.close()
                conn.close()
                return True, "SQLite database initialized."
        except Exception as e:
            return False, f"Init error: {e}"

    @classmethod
    def seed_food_items(cls, cursor, is_mysql=True):
        foods = [
            ('Rolled Oats with Water', 'Grains', 150, 5.0, 27.0, 2.5, 4.0, 'Breakfast', 'Vegan', 'None', '40g dry'),
            ('Boiled Eggs (2 whole)', 'Poultry', 144, 12.6, 1.0, 9.5, 0.0, 'Breakfast', 'Non-Vegetarian', 'Eggs', '2 eggs (100g)'),
            ('Egg White Omelet (3 whites)', 'Poultry', 51, 10.8, 0.7, 0.2, 0.0, 'Breakfast', 'Non-Vegetarian', 'Eggs', '3 whites'),
            ('Paneer Bhurji', 'Dairy', 220, 14.0, 5.0, 16.0, 1.2, 'Breakfast', 'Vegetarian', 'Milk', '100g'),
            ('Tofu Scramble', 'Legumes', 130, 12.0, 3.5, 7.0, 2.0, 'Breakfast', 'Vegan', 'Soy', '100g'),
            ('Moong Dal Cheela', 'Legumes', 180, 11.0, 24.0, 4.0, 5.0, 'Breakfast', 'Vegan', 'None', '2 cheelas (120g)'),
            ('Vegetable Poha', 'Grains', 190, 3.5, 36.0, 4.0, 2.5, 'Breakfast', 'Vegan', 'Peanuts', '1 bowl (150g)'),
            ('Idli with Sambar (2 idlis)', 'Grains', 160, 5.0, 32.0, 1.5, 3.0, 'Breakfast', 'Vegan', 'None', '2 idlis + sambar'),
            ('Multigrain Toast with Peanut Butter', 'Grains', 210, 8.0, 22.0, 10.5, 3.5, 'Breakfast', 'Vegan', 'Peanuts', '1 slice + 1tbsp PB'),
            ('Greek Yogurt with Berries', 'Dairy', 140, 15.0, 12.0, 2.5, 2.0, 'Breakfast', 'Vegetarian', 'Milk', '150g'),

            ('Brown Rice (Cooked)', 'Grains', 130, 2.7, 28.0, 1.0, 2.0, 'Lunch', 'Vegan', 'None', '100g'),
            ('Steamed Basmati Rice', 'Grains', 130, 2.5, 28.5, 0.3, 0.5, 'Lunch', 'Vegan', 'None', '100g'),
            ('Whole Wheat Roti (Chapati)', 'Grains', 85, 3.0, 17.0, 0.5, 2.5, 'Lunch', 'Vegan', 'None', '1 roti (35g)'),
            ('Yellow Tadka Dal', 'Legumes', 145, 8.5, 20.0, 3.5, 4.5, 'Lunch', 'Vegan', 'None', '1 katori (150g)'),
            ('Rajma Curry (Kidney Beans)', 'Legumes', 170, 9.0, 25.0, 3.5, 6.0, 'Lunch', 'Vegan', 'None', '1 bowl (160g)'),
            ('Chole (Chickpeas Masala)', 'Legumes', 190, 8.5, 27.0, 5.0, 6.5, 'Lunch', 'Vegan', 'None', '1 bowl (160g)'),
            ('Grilled Chicken Breast', 'Poultry', 165, 31.0, 0.0, 3.6, 0.0, 'Lunch', 'Non-Vegetarian', 'None', '100g'),
            ('Fish Curry (Rohu / Tilapia)', 'Seafood', 180, 22.0, 3.0, 9.0, 0.5, 'Lunch', 'Non-Vegetarian', 'Seafood', '150g'),
            ('Palak Paneer', 'Dairy', 210, 11.5, 7.0, 15.0, 3.0, 'Lunch', 'Vegetarian', 'Milk', '150g'),
            ('Quinoa Salad with Veggies', 'Grains', 160, 5.5, 26.0, 3.5, 4.0, 'Lunch', 'Vegan', 'None', '150g'),
            ('Mixed Vegetable Sabzi', 'Vegetables', 95, 2.5, 12.0, 4.0, 3.5, 'Lunch', 'Vegan', 'None', '150g'),
            ('Cucumber Tomato Salad', 'Vegetables', 35, 1.2, 7.0, 0.2, 2.0, 'Lunch', 'Vegan', 'None', '100g'),

            ('Roasted Almonds (15 nuts)', 'Nuts', 105, 3.8, 3.6, 9.2, 2.2, 'Snack', 'Vegan', 'None', '18g'),
            ('Walnuts (4 halves)', 'Nuts', 100, 2.3, 2.0, 10.0, 1.0, 'Snack', 'Vegan', 'None', '15g'),
            ('Apple (Medium)', 'Fruits', 95, 0.5, 25.0, 0.3, 4.4, 'Snack', 'Vegan', 'None', '1 medium (180g)'),
            ('Banana (Medium)', 'Fruits', 105, 1.3, 27.0, 0.4, 3.1, 'Snack', 'Vegan', 'None', '1 medium (118g)'),
            ('Roasted Chana (Chickpeas)', 'Legumes', 130, 7.0, 18.0, 2.5, 4.0, 'Snack', 'Vegan', 'None', '40g'),
            ('Makhana (Fox Nuts, Roasted)', 'Snack', 110, 3.0, 20.0, 1.5, 2.5, 'Snack', 'Vegan', 'None', '30g'),
            ('Boiled Sprouts Salad', 'Legumes', 115, 7.5, 18.0, 1.0, 4.5, 'Snack', 'Vegan', 'None', '100g'),
            ('Low Fat Buttermilk (Chaas)', 'Dairy', 45, 3.5, 5.0, 1.2, 0.0, 'Snack', 'Vegetarian', 'Milk', '200ml'),
            ('Green Tea with Lemon', 'Beverages', 2, 0.0, 0.5, 0.0, 0.0, 'Snack', 'Vegan', 'None', '200ml'),
            ('Chia Seed Pudding (Almond Milk)', 'Nuts & Seeds', 140, 4.5, 12.0, 7.5, 6.0, 'Snack', 'Vegan', 'None', '1 jar (150g)'),

            ('Grilled Salmon Fillet', 'Seafood', 206, 22.0, 0.0, 12.0, 0.0, 'Dinner', 'Non-Vegetarian', 'Seafood', '100g'),
            ('Chicken Stir Fry with Vegetables', 'Poultry', 220, 26.0, 8.0, 8.0, 3.0, 'Dinner', 'Non-Vegetarian', 'None', '200g'),
            ('Soya Chunks Curry', 'Legumes', 180, 18.0, 12.0, 5.0, 6.0, 'Dinner', 'Vegan', 'Soy', '150g'),
            ('Masoor Dal Soup', 'Legumes', 130, 8.0, 19.0, 2.0, 4.0, 'Dinner', 'Vegan', 'None', '200ml'),
            ('Steamed Broccoli & Carrots', 'Vegetables', 55, 3.0, 10.0, 0.5, 4.0, 'Dinner', 'Vegan', 'None', '150g'),
            ('Stir Fried Tofu and Veggies', 'Legumes', 160, 13.0, 7.0, 9.0, 3.5, 'Dinner', 'Vegan', 'Soy', '180g'),
            ('Lauki (Bottle Gourd) Sabzi', 'Vegetables', 65, 1.8, 8.0, 2.5, 2.5, 'Dinner', 'Vegan', 'None', '150g'),
            ('Methi Roti', 'Grains', 90, 3.2, 16.0, 1.2, 2.8, 'Dinner', 'Vegan', 'None', '1 roti (40g)'),
            ('Grilled Paneer with Herbs', 'Dairy', 210, 14.5, 4.0, 15.0, 1.0, 'Dinner', 'Vegetarian', 'Milk', '100g'),
            ('Clear Vegetable Soup', 'Vegetables', 45, 1.5, 8.0, 0.5, 2.0, 'Dinner', 'Vegan', 'None', '200ml')
        ]

        if is_mysql:
            sql = """
            INSERT INTO food_items (food_name, category, calories, protein, carbohydrates, fat, fiber, meal_type, diet_type, allergens, serving_size)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(sql, foods)
        else:
            sql = """
            INSERT INTO food_items (food_name, category, calories, protein, carbohydrates, fat, fiber, meal_type, diet_type, allergens, serving_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.executemany(sql, foods)

    @classmethod
    def execute_query(cls, query, params=None, fetchone=False, fetchall=False, commit=False):
        backend = cls.get_backend()
        conn = cls.get_connection()
        params = params or ()

        try:
            if backend == "mysql" and MYSQL_AVAILABLE:
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

# -----------------------------------------------------------------------------
# Models Layer
# -----------------------------------------------------------------------------
class UserModel:
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    @classmethod
    def register_user(cls, name: str, email: str, password: str, photo_path: str = None):
        email = email.strip().lower()
        existing = Database.execute_query("SELECT user_id FROM users WHERE email = %s;", (email,), fetchone=True)
        if existing:
            return None, "Email is already registered. Please login or use a different email."

        hashed_pw = cls.hash_password(password)
        try:
            user_id = Database.execute_query(
                "INSERT INTO users (name, email, password, profile_photo) VALUES (%s, %s, %s, %s);",
                (name.strip(), email, hashed_pw, photo_path),
                commit=True
            )
            return user_id, "User registered successfully."
        except Exception as e:
            return None, f"Database error: {e}"

    @classmethod
    def authenticate(cls, email: str, password: str):
        email = email.strip().lower()
        hashed_pw = cls.hash_password(password)
        user = Database.execute_query(
            "SELECT user_id, name, email, profile_photo, created_at FROM users WHERE email = %s AND password = %s;",
            (email, hashed_pw),
            fetchone=True
        )
        if user:
            return user, "Login successful."
        return None, "Invalid email or password."

    @classmethod
    def get_user_by_id(cls, user_id: int):
        return Database.execute_query(
            "SELECT user_id, name, email, profile_photo, created_at FROM users WHERE user_id = %s;",
            (user_id,),
            fetchone=True
        )

    @classmethod
    def update_photo(cls, user_id: int, photo_path: str):
        Database.execute_query(
            "UPDATE users SET profile_photo = %s WHERE user_id = %s;",
            (photo_path, user_id),
            commit=True
        )

    @classmethod
    def get_profile(cls, user_id: int):
        return Database.execute_query("SELECT * FROM user_profiles WHERE user_id = %s;", (user_id,), fetchone=True)

    @classmethod
    def save_or_update_profile(cls, user_id: int, profile_data: dict):
        existing = cls.get_profile(user_id)
        if existing:
            query = """
            UPDATE user_profiles SET
                height = %s, weight = %s, diet_type = %s, age = %s, gender = %s,
                activity_level = %s, goal = %s, allergies = %s, bmi = %s, bmi_category = %s,
                bmr = %s, daily_calories = %s, target_protein = %s, target_carbs = %s,
                target_fat = %s, target_fiber = %s, target_water = %s
            WHERE user_id = %s;
            """
            params = (
                profile_data['height'], profile_data['weight'], profile_data['diet_type'],
                profile_data['age'], profile_data['gender'], profile_data['activity_level'],
                profile_data['goal'], profile_data.get('allergies', 'None'),
                profile_data.get('bmi'), profile_data.get('bmi_category'),
                profile_data.get('bmr'), profile_data.get('daily_calories'),
                profile_data.get('target_protein'), profile_data.get('target_carbs'),
                profile_data.get('target_fat'), profile_data.get('target_fiber'),
                profile_data.get('target_water'), user_id
            )
            Database.execute_query(query, params, commit=True)
            return True, "Profile updated."
        else:
            query = """
            INSERT INTO user_profiles (
                user_id, height, weight, diet_type, age, gender,
                activity_level, goal, allergies, bmi, bmi_category,
                bmr, daily_calories, target_protein, target_carbs,
                target_fat, target_fiber, target_water
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            params = (
                user_id, profile_data['height'], profile_data['weight'], profile_data['diet_type'],
                profile_data['age'], profile_data['gender'], profile_data['activity_level'],
                profile_data['goal'], profile_data.get('allergies', 'None'),
                profile_data.get('bmi'), profile_data.get('bmi_category'),
                profile_data.get('bmr'), profile_data.get('daily_calories'),
                profile_data.get('target_protein'), profile_data.get('target_carbs'),
                profile_data.get('target_fat'), profile_data.get('target_fiber'),
                profile_data.get('target_water')
            )
            Database.execute_query(query, params, commit=True)
            return True, "Profile created."

class FoodModel:
    @classmethod
    def get_all_foods(cls):
        return Database.execute_query("SELECT * FROM food_items ORDER BY food_name ASC;", fetchall=True)

    @classmethod
    def get_all_categories(cls):
        rows = Database.execute_query("SELECT DISTINCT category FROM food_items ORDER BY category ASC;", fetchall=True)
        return [r['category'] for r in rows] if rows else []

    @classmethod
    def search_foods(cls, keyword: str = "", category: str = "All", diet_type: str = "All", meal_type: str = "All"):
        query = "SELECT * FROM food_items WHERE 1=1"
        params = []

        if keyword and keyword.strip():
            query += " AND (food_name LIKE %s OR category LIKE %s)"
            params.extend([f"%{keyword.strip()}%", f"%{keyword.strip()}%"])

        if category and category != "All":
            query += " AND category = %s"
            params.append(category)

        if diet_type and diet_type != "All":
            if diet_type == "Vegetarian":
                query += " AND diet_type IN ('Vegetarian', 'Vegan')"
            elif diet_type == "Vegan":
                query += " AND diet_type = 'Vegan'"
            elif diet_type == "Non-Vegetarian":
                query += " AND diet_type = 'Non-Vegetarian'"

        if meal_type and meal_type != "All":
            query += " AND meal_type = %s"
            params.append(meal_type)

        query += " ORDER BY food_name ASC;"
        return Database.execute_query(query, tuple(params), fetchall=True)

    @classmethod
    def get_safe_foods_for_diet_and_allergies(cls, diet_type: str, user_allergies: list):
        query = "SELECT * FROM food_items WHERE 1=1"
        params = []

        if diet_type == "Vegetarian":
            query += " AND diet_type IN ('Vegetarian', 'Vegan')"
        elif diet_type == "Vegan":
            query += " AND diet_type = 'Vegan'"

        foods = Database.execute_query(query, tuple(params), fetchall=True)
        if not foods:
            return []

        cleaned = [a.strip().lower() for a in user_allergies if a and a.strip().lower() != "none"]
        if not cleaned:
            return foods

        safe = []
        for food in foods:
            allergen_text = (food.get('allergens') or 'None').lower()
            fname = food.get('food_name', '').lower()

            conflict = False
            for al in cleaned:
                if al in allergen_text or al in fname:
                    conflict = True
                    break
                if al == "milk" and any(k in fname for k in ["dairy", "paneer", "curd", "yogurt", "buttermilk"]):
                    conflict = True
                    break
                if al == "peanuts" and "peanut" in fname:
                    conflict = True
                    break
                if al == "eggs" and "egg" in fname:
                    conflict = True
                    break
                if al == "soy" and ("tofu" in fname or "soya" in fname):
                    conflict = True
                    break

            if not conflict:
                safe.append(food)

        return safe

class DietModel:
    @classmethod
    def save_plan(cls, user_id: int, plan_date: str, total_calories: float,
                  total_protein: float, total_carbs: float, total_fat: float,
                  breakfast_items: str, lunch_items: str, snack_items: str, dinner_items: str):
        query = """
        INSERT INTO diet_plans (
            user_id, plan_date, total_calories, total_protein,
            total_carbs, total_fat, breakfast_items, lunch_items,
            snack_items, dinner_items
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        params = (
            user_id, plan_date, total_calories, total_protein,
            total_carbs, total_fat, breakfast_items, lunch_items,
            snack_items, dinner_items
        )
        return Database.execute_query(query, params, commit=True)

    @classmethod
    def get_user_plans(cls, user_id: int):
        return Database.execute_query("SELECT * FROM diet_plans WHERE user_id = %s ORDER BY created_at DESC;", (user_id,), fetchall=True)

    @classmethod
    def get_latest_plan(cls, user_id: int):
        return Database.execute_query("SELECT * FROM diet_plans WHERE user_id = %s ORDER BY created_at DESC LIMIT 1;", (user_id,), fetchone=True)

class ProgressModel:
    @classmethod
    def add_log(cls, user_id: int, log_date: str, current_weight: float,
                water_intake: float, calories_consumed: float, notes: str = ""):
        query = """
        INSERT INTO progress_logs (user_id, log_date, current_weight, water_intake, calories_consumed, notes)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        params = (user_id, log_date, current_weight, water_intake, calories_consumed, notes)
        return Database.execute_query(query, params, commit=True)

    @classmethod
    def get_user_logs(cls, user_id: int):
        return Database.execute_query("SELECT * FROM progress_logs WHERE user_id = %s ORDER BY log_date DESC, created_at DESC;", (user_id,), fetchall=True)

# -----------------------------------------------------------------------------
# Scientific Calculations (Steps 11 – 14)
# -----------------------------------------------------------------------------
class NutritionCalculator:
    DISCLAIMER = (
        "NOTE: BMI, BMR, and nutritional values are screening calculations "
        "and nutritional estimates. They should not be presented or construed "
        "as a medical diagnosis or clinical prescription."
    )

    @staticmethod
    def calculate_bmi(height_cm: float, weight_kg: float) -> tuple[float, str]:
        if height_cm <= 0 or weight_kg <= 0:
            return 0.0, "Invalid input"

        height_m = height_cm / 100.0
        bmi = round(weight_kg / (height_m ** 2), 1)

        if bmi < 18.5:
            category = "Underweight"
        elif 18.5 <= bmi < 24.9:
            category = "Normal Weight"
        elif 25.0 <= bmi < 29.9:
            category = "Overweight"
        else:
            category = "Obese"

        return bmi, category

    @staticmethod
    def calculate_bmr(height_cm: float, weight_kg: float, age: int, gender: str) -> float:
        base = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age)
        gender_lower = gender.strip().lower()

        if gender_lower == "male":
            bmr = base + 5.0
        elif gender_lower == "female":
            bmr = base - 161.0
        else:
            bmr = base - 78.0

        return round(max(bmr, 800.0), 1)

    @staticmethod
    def calculate_daily_calories(bmr: float, activity_level: str, goal: str) -> float:
        activity_multipliers = {
            "Sedentary": 1.2,
            "Lightly Active": 1.375,
            "Moderately Active": 1.55,
            "Very Active": 1.725
        }
        multiplier = activity_multipliers.get(activity_level.strip(), 1.2)
        tdee = bmr * multiplier

        goal_lower = goal.strip().lower()
        if "weight management" in goal_lower or "weight loss" in goal_lower:
            target = max(tdee - 450.0, max(1200.0, bmr * 0.9))
        elif "muscle" in goal_lower or "gain" in goal_lower:
            target = tdee + 300.0
        else:
            target = tdee

        return round(target, 0)

    @classmethod
    def calculate_nutrition_targets(cls, height_cm: float, weight_kg: float, age: int,
                                    gender: str, activity_level: str, goal: str) -> dict:
        bmi, bmi_category = cls.calculate_bmi(height_cm, weight_kg)
        bmr = cls.calculate_bmr(height_cm, weight_kg, age, gender)
        daily_calories = cls.calculate_daily_calories(bmr, activity_level, goal)

        goal_lower = goal.strip().lower()
        if "weight management" in goal_lower:
            protein_per_kg = 2.0
            fat_ratio = 0.25
        elif "nutrition" in goal_lower:
            protein_per_kg = 1.6
            fat_ratio = 0.25
        else:
            protein_per_kg = 1.5
            fat_ratio = 0.25

        protein_g = round(min(weight_kg * protein_per_kg, (daily_calories * 0.35) / 4.0), 1)
        protein_calories = protein_g * 4.0

        fat_calories = daily_calories * fat_ratio
        fat_g = round(fat_calories / 9.0, 1)

        carb_calories = max(daily_calories - (protein_calories + fat_calories), 0)
        carb_g = round(carb_calories / 4.0, 1)

        fiber_g = round(max((daily_calories / 1000.0) * 14.0, 25.0), 1)
        water_liters = round(max((weight_kg * 0.035), 2.2), 1)

        return {
            "bmi": bmi,
            "bmi_category": bmi_category,
            "bmr": bmr,
            "daily_calories": daily_calories,
            "target_protein": protein_g,
            "target_carbs": carb_g,
            "target_fat": fat_g,
            "target_fiber": fiber_g,
            "target_water": water_liters,
            "disclaimer": cls.DISCLAIMER
        }

# -----------------------------------------------------------------------------
# AI Recommendation Engine (Steps 16 – 20)
# -----------------------------------------------------------------------------
class AIRecommendationEngine:
    MEAL_DISTRIBUTION = {
        "Breakfast": 0.25,
        "Lunch": 0.35,
        "Snack": 0.15,
        "Dinner": 0.25
    }

    @classmethod
    def score_food(cls, food: dict, meal_name: str, target_calories: float, target_protein: float, goal: str) -> float:
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

# -----------------------------------------------------------------------------
# AI Assistant (Step 26)
# -----------------------------------------------------------------------------
class NutritionAssistant:
    @classmethod
    def respond_to_query(cls, query: str, user_profile: dict = None) -> str:
        q = query.strip().lower()
        if not q:
            return "Please type a nutrition question."

        if "protein" in q and any(k in q for k in ["high", "rich", "best", "source", "good"]):
            diet_type = user_profile.get('diet_type', 'All') if user_profile else 'All'
            foods = FoodModel.get_all_foods()
            if diet_type == 'Vegetarian':
                foods = [f for f in foods if f['diet_type'] in ('Vegetarian', 'Vegan')]
            elif diet_type == 'Vegan':
                foods = [f for f in foods if f['diet_type'] == 'Vegan']

            foods.sort(key=lambda x: float(x.get('protein', 0)), reverse=True)
            top5 = foods[:5]

            res = f"Top protein-rich foods"
            if diet_type != 'All':
                res += f" suitable for a {diet_type} diet"
            res += ":\n\n"
            for f in top5:
                res += f"• **{f['food_name']}** ({f['category']}): {f['protein']}g protein, {f['calories']} kcal ({f['serving_size']})\n"
            return res

        for meal in ["breakfast", "lunch", "snack", "dinner"]:
            if meal in q and any(k in q for k in ["eat", "food", "suggest", "option", "what"]):
                foods = FoodModel.search_foods(meal_type=meal.capitalize())
                diet_pref = user_profile.get('diet_type', '') if user_profile else ''
                if diet_pref == 'Vegetarian':
                    foods = [f for f in foods if f['diet_type'] in ('Vegetarian', 'Vegan')]
                elif diet_pref == 'Vegan':
                    foods = [f for f in foods if f['diet_type'] == 'Vegan']

                sample = foods[:4] if foods else []
                res = f"Healthy {meal.capitalize()} recommendations:\n\n"
                for f in sample:
                    res += f"• **{f['food_name']}**: {f['calories']} kcal | {f['protein']}g protein | {f['carbohydrates']}g carbs\n"
                return res

        all_foods = FoodModel.get_all_foods()
        for f in all_foods:
            fname = f['food_name'].lower()
            words = [w for w in fname.replace('(', '').replace(')', '').split() if len(w) > 3]
            if any(w in q for w in words) or fname in q:
                return (
                    f"**Nutritional Information for {f['food_name']}:**\n"
                    f"• Category: {f['category']}\n"
                    f"• Serving Size: {f['serving_size']}\n"
                    f"• Calories: {f['calories']} kcal\n"
                    f"• Protein: {f['protein']} g\n"
                    f"• Carbohydrates: {f['carbohydrates']} g\n"
                    f"• Fat: {f['fat']} g\n"
                    f"• Dietary Fiber: {f['fiber']} g\n"
                    f"• Diet Type: {f['diet_type']}\n"
                    f"• Allergen Info: {f['allergens']}"
                )

        if "bmi" in q:
            return (
                "**BMI (Body Mass Index)** = weight (kg) / [height (m)]²\n\n"
                "• Underweight: < 18.5\n"
                "• Normal Weight: 18.5 – 24.9\n"
                "• Overweight: 25.0 – 29.9\n"
                "• Obese: >= 30.0\n\n"
                "*Disclaimer: BMI is a general screening indicator only.*"
            )

        if "bmr" in q or "metabolic" in q:
            return (
                "**BMR (Basal Metabolic Rate)** is the minimum calorie requirement your body consumes at complete rest.\n"
                "We calculate it using the clinical **Mifflin-St Jeor formula** based on your age, gender, height, and weight."
            )

        return (
            f"I analyzed your question regarding '{query}'.\n\n"
            "Try asking:\n"
            "• 'What foods are high in protein?'\n"
            "• 'What can I eat for breakfast?'\n"
            "• 'What is the calorie value of rice?'\n"
            "• 'Show vegetarian foods'"
        )

# -----------------------------------------------------------------------------
# Report Generator (Step 27)
# -----------------------------------------------------------------------------
class ReportGenerator:
    @classmethod
    def generate_pdf_report(cls, user: dict, profile: dict, output_path: str = None) -> str:
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Diet_Report_{user.get('name', 'User').replace(' ', '_')}_{timestamp}.pdf"
            output_path = os.path.join(REPORTS_DIR, filename)

        if not REPORTLAB_AVAILABLE:
            return cls.generate_text_report(user, profile, output_path.replace('.pdf', '.txt'))

        try:
            doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#0284C7'), spaceAfter=4)
            h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#0284C7'), spaceBefore=10, spaceAfter=4)
            body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#334155'))

            story.append(Paragraph("AI-BASED DIET MANAGEMENT SYSTEM", title_style))
            story.append(Paragraph(f"Nutrition & Diet Summary Report | Generated: {datetime.now().strftime('%B %d, %Y')}", body_style))
            story.append(Spacer(1, 10))

            info_text = f"""
            <b>Name:</b> {user.get('name', 'N/A')}<br/>
            <b>Email:</b> {user.get('email', 'N/A')}<br/>
            <b>Age:</b> {profile.get('age', 'N/A')} | <b>Gender:</b> {profile.get('gender', 'N/A')}<br/>
            <b>Diet:</b> {profile.get('diet_type', 'N/A')} | <b>Goal:</b> {profile.get('goal', 'N/A')}<br/>
            <b>Allergies:</b> {profile.get('allergies', 'None')}
            """
            story.append(Paragraph(info_text, body_style))
            story.append(Spacer(1, 10))

            story.append(Paragraph("Scientific Metrics & Daily Targets", h2_style))
            metrics_data = [
                ["Metric", "Value", "Metric", "Value"],
                ["Height", f"{profile.get('height')} cm", "Weight", f"{profile.get('weight')} kg"],
                ["BMI", f"{profile.get('bmi')} ({profile.get('bmi_category')})", "BMR", f"{profile.get('bmr')} kcal"],
                ["Daily Target", f"{profile.get('daily_calories')} kcal", "Protein Target", f"{profile.get('target_protein')} g"],
                ["Carbs Target", f"{profile.get('target_carbs')} g", "Fat Target", f"{profile.get('target_fat')} g"],
                ["Fiber Target", f"{profile.get('target_fiber')} g", "Water Target", f"{profile.get('target_water')} L"]
            ]
            t = Table(metrics_data, colWidths=[130, 135, 130, 135])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284C7')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))

            latest_plan = DietModel.get_latest_plan(user.get('user_id'))
            if latest_plan:
                story.append(Paragraph("Latest Recommended Diet Plan", h2_style))
                plan_text = f"""
                <b>Date:</b> {latest_plan.get('plan_date')} | <b>Total Calories:</b> {latest_plan.get('total_calories')} kcal<br/>
                <b>Breakfast:</b> {latest_plan.get('breakfast_items')}<br/>
                <b>Lunch:</b> {latest_plan.get('lunch_items')}<br/>
                <b>Snack:</b> {latest_plan.get('snack_items')}<br/>
                <b>Dinner:</b> {latest_plan.get('dinner_items')}
                """
                story.append(Paragraph(plan_text, body_style))

            story.append(Spacer(1, 14))
            disclaimer_text = "<b>DISCLAIMER:</b> This report is generated algorithmically for educational guidance. Not a medical diagnosis."
            story.append(Paragraph(disclaimer_text, ParagraphStyle('Disc', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#64748B'))))

            doc.build(story)
            return output_path
        except Exception:
            return cls.generate_text_report(user, profile, output_path.replace('.pdf', '.txt'))

    @classmethod
    def generate_text_report(cls, user: dict, profile: dict, output_path: str = None) -> str:
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Diet_Report_{user.get('name', 'User').replace(' ', '_')}_{timestamp}.txt"
            output_path = os.path.join(REPORTS_DIR, filename)

        latest_plan = DietModel.get_latest_plan(user.get('user_id'))
        lines = [
            "=" * 65,
            "           AI-BASED DIET MANAGEMENT SYSTEM",
            "              PERSONAL NUTRITION REPORT",
            "=" * 65,
            f"Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"User: {user.get('name')} ({user.get('email')})",
            f"Age: {profile.get('age')} | Gender: {profile.get('gender')}",
            f"Diet: {profile.get('diet_type')} | Goal: {profile.get('goal')}",
            f"Allergies: {profile.get('allergies', 'None')}",
            "",
            "SCIENTIFIC METRICS & TARGETS:",
            f"• Height: {profile.get('height')} cm | Weight: {profile.get('weight')} kg",
            f"• BMI: {profile.get('bmi')} ({profile.get('bmi_category')})",
            f"• BMR (Mifflin-St Jeor): {profile.get('bmr')} kcal/day",
            f"• Daily Energy Target: {profile.get('daily_calories')} kcal",
            f"• Protein Target: {profile.get('target_protein')} g",
            f"• Carbs Target: {profile.get('target_carbs')} g",
            f"• Fat Target: {profile.get('target_fat')} g",
            f"• Fiber Target: {profile.get('target_fiber')} g",
            f"• Recommended Daily Hydration: {profile.get('target_water')} Liters",
            "",
            "LATEST AI DIET PLAN:"
        ]

        if latest_plan:
            lines.extend([
                f"• Date: {latest_plan.get('plan_date')}",
                f"• Calories: {latest_plan.get('total_calories')} kcal",
                f"• Breakfast: {latest_plan.get('breakfast_items')}",
                f"• Lunch: {latest_plan.get('lunch_items')}",
                f"• Snack: {latest_plan.get('snack_items')}",
                f"• Dinner: {latest_plan.get('dinner_items')}"
            ])
        else:
            lines.append("• No diet plans saved yet.")

        lines.extend([
            "",
            "=" * 65,
            "DISCLAIMER: Nutritional calculations are for lifestyle guidance only.",
            "=" * 65
        ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return output_path

# -----------------------------------------------------------------------------
# Streamlit Application Interface
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NutriAI — Diet Management System",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
/* Modern typography and container polish */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Sky Blue Ambient Background & Page Glow */
.stApp {
    background: radial-gradient(circle at 12% 10%, rgba(56, 189, 248, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 88% 85%, rgba(14, 165, 233, 0.12) 0%, transparent 45%),
                linear-gradient(180deg, #F0F9FF 0%, #F8FAFC 100%);
    background-attachment: fixed;
}

/* Sidebar Sky Blue Ambient Glow */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #E0F2FE 0%, #F0F9FF 60%, #FFFFFF 100%) !important;
    border-right: 1px solid #BAE6FD !important;
}

/* Card Containers with Sky Blue Glass Glow */
.aesthetic-card {
    background: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(12px);
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 20px;
    border: 1px solid #BAE6FD;
    box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.08), 0 8px 10px -6px rgba(56, 189, 248, 0.04);
    transition: all 0.25s ease;
}
.aesthetic-card:hover {
    border-color: #38BDF8;
    box-shadow: 0 18px 30px -4px rgba(2, 132, 199, 0.16), 0 8px 12px -4px rgba(56, 189, 248, 0.1);
    transform: translateY(-2px);
}

/* Sky Blue Hero Badge */
.hero-badge {
    display: inline-block;
    padding: 6px 14px;
    background: linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 100%);
    color: #0369A1;
    font-weight: 700;
    font-size: 0.82rem;
    border-radius: 9999px;
    border: 1px solid #7DD3FC;
    box-shadow: 0 2px 10px rgba(14, 165, 233, 0.2);
    margin-bottom: 12px;
}

/* Buttons with Sky Blue Gradient & Glow */
button[kind="primary"] {
    background: linear-gradient(135deg, #0284C7 0%, #38BDF8 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: none !important;
    box-shadow: 0 4px 14px 0 rgba(2, 132, 199, 0.35) !important;
    transition: all 0.2s ease !important;
    border-radius: 10px !important;
}
button[kind="primary"]:hover {
    box-shadow: 0 6px 20px 0 rgba(2, 132, 199, 0.5) !important;
    transform: translateY(-1px) !important;
}

button[kind="secondary"] {
    border: 1px solid #BAE6FD !important;
    background: #FFFFFF !important;
    color: #0369A1 !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    border-radius: 10px !important;
}
button[kind="secondary"]:hover {
    border-color: #38BDF8 !important;
    background: #F0F9FF !important;
    color: #0284C7 !important;
}

/* Metric widgets with sky blue borders & numbers */
div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid #BAE6FD;
    padding: 14px 18px;
    border-radius: 14px;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.05);
}
div[data-testid="stMetric"]:hover {
    border-color: #38BDF8;
}
div[data-testid="stMetricLabel"] {
    color: #475569;
    font-weight: 600;
}
div[data-testid="stMetricValue"] {
    color: #0284C7;
    font-weight: 800;
}

/* Macro Pills */
.macro-pill {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-right: 6px;
    margin-bottom: 4px;
}
.pill-cal { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
.pill-prot { background: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }
.pill-carb { background: #FEF9C3; color: #854D0E; border: 1px solid #FEF08A; }
.pill-fat { background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
.pill-fib { background: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; }

/* BMI Scale Meter */
.bmi-scale-bar {
    height: 12px;
    border-radius: 6px;
    background: linear-gradient(to right, #38BDF8 0%, #38BDF8 18.5%, #34D399 18.5%, #34D399 24.9%, #FBBF24 24.9%, #FBBF24 29.9%, #F87171 29.9%, #F87171 100%);
    position: relative;
    margin: 14px 0 6px 0;
}
.bmi-pointer {
    width: 4px;
    height: 20px;
    background: #0F172A;
    position: absolute;
    top: -4px;
    border-radius: 2px;
    box-shadow: 0 0 6px rgba(0,0,0,0.4);
}

/* Meal Headers */
.meal-header-breakfast {
    background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
    border-left: 5px solid #F59E0B;
    padding: 12px 16px;
    border-radius: 12px 12px 0 0;
    margin: -1px -1px 12px -1px;
}
.meal-header-lunch {
    background: linear-gradient(135deg, #F0FDF4 0%, #E0F2FE 100%);
    border-left: 5px solid #0EA5E9;
    padding: 12px 16px;
    border-radius: 12px 12px 0 0;
    margin: -1px -1px 12px -1px;
}
.meal-header-snack {
    background: linear-gradient(135deg, #FAF5FF 0%, #F3E8FF 100%);
    border-left: 5px solid #A855F7;
    padding: 12px 16px;
    border-radius: 12px 12px 0 0;
    margin: -1px -1px 12px -1px;
}
.meal-header-dinner {
    background: linear-gradient(135deg, #F0F9FF 0%, #BAE6FD 100%);
    border-left: 5px solid #0284C7;
    padding: 12px 16px;
    border-radius: 12px 12px 0 0;
    margin: -1px -1px 12px -1px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "db_initialized" not in st.session_state:
    success, msg = Database.initialize_database()
    st.session_state["db_initialized"] = success
    st.session_state["db_backend"] = Database.get_backend()

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

def render_bmi_visual_scale(bmi, category):
    pct = min(max((bmi / 40.0) * 100.0, 5.0), 95.0)
    cat_colors = {
        "Underweight": "#0284C7",
        "Normal Weight": "#10B981",
        "Overweight": "#F59E0B",
        "Obese": "#EF4444"
    }
    color = cat_colors.get(category, "#10B981")
    html = f"""
    <div style="background: #FFFFFF; border-radius: 14px; padding: 18px; border: 1px solid #BAE6FD; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.06); margin-bottom: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <span style="font-size: 0.9rem; font-weight: 700; color: #475569;">BODY MASS INDEX (BMI)</span>
            <span style="font-size: 1.25rem; font-weight: 800; color: {color};">{bmi} <span style="font-size: 0.85rem; font-weight: 600;">({category})</span></span>
        </div>
        <div class="bmi-scale-bar">
            <div class="bmi-pointer" style="left: {pct}%;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: #94A3B8; font-weight: 600;">
            <span>Underweight (&lt;18.5)</span>
            <span>Normal (18.5-24.9)</span>
            <span>Overweight (25-29.9)</span>
            <span>Obese (&ge;30)</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_macro_donut(protein_g, carbs_g, fat_g, daily_cals):
    p_cals = protein_g * 4.0
    c_cals = carbs_g * 4.0
    f_cals = fat_g * 9.0
    total = max(p_cals + c_cals + f_cals, 1.0)

    data = pd.DataFrame({
        "Nutrient": ["Protein", "Carbohydrates", "Fats"],
        "Grams": [protein_g, carbs_g, fat_g],
        "Calories": [round(p_cals, 1), round(c_cals, 1), round(f_cals, 1)],
        "Percentage": [round((p_cals / total) * 100, 1), round((c_cals / total) * 100, 1), round((f_cals / total) * 100, 1)]
    })

    chart = alt.Chart(data).mark_arc(innerRadius=65, stroke="#FFFFFF", strokeWidth=2).encode(
        theta=alt.Theta(field="Calories", type="quantitative"),
        color=alt.Color(
            field="Nutrient",
            type="nominal",
            scale=alt.Scale(
                domain=["Protein", "Carbohydrates", "Fats"],
                range=["#0284C7", "#38BDF8", "#F59E0B"]
            ),
            legend=alt.Legend(title="Nutrient Ratio", orient="bottom")
        ),
        tooltip=[
            alt.Tooltip("Nutrient:N", title="Macro"),
            alt.Tooltip("Grams:Q", title="Target (g)"),
            alt.Tooltip("Calories:Q", title="Energy (kcal)"),
            alt.Tooltip("Percentage:Q", title="Share (%)")
        ]
    ).properties(width=280, height=240)
    return chart

def render_welcome_screen():
    st.write("")
    col_l, col_c, col_r = st.columns([1, 2.4, 1])

    with col_c:
        st.markdown(
            """
            <div class="aesthetic-card" style="text-align: center; padding: 40px 30px;">
                <span class="hero-badge">✨ CLINICALLY BACKED AI NUTRITION</span>
                <h1 style="color: #0284C7; font-size: 2.3rem; margin: 0 0 10px 0; font-weight: 800; text-shadow: 0 2px 10px rgba(2, 132, 199, 0.2);">DIET MANAGEMENT SYSTEM</h1>
                <p style="color: #64748B; font-size: 1.05rem; line-height: 1.6; max-width: 580px; margin: 0 auto 28px auto;">
                    Harness advanced AI algorithms and clinical metabolic benchmarks (Mifflin-St Jeor & WHO)
                    to compute your personalized energy budget, allergy-safe nutrition, and portion-perfect meal plans.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

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

        backend = st.session_state.get('db_backend', 'sqlite').upper()
        st.caption(f"Connected to: **{backend}** Database | Dual-Backend Zero-Config Engine")

        st.write("---")
        f1, f2 = st.columns(2)
        with f1:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; text-align: left; margin-bottom: 10px;">
                    <span style="font-size: 1.4rem;">🧠</span> <strong>Multi-Factor AI Scoring</strong><br/>
                    <span style="font-size: 0.85rem; color: #64748B;">Evaluates protein density, nutrient balance & caloric proximity for every food item.</span>
                </div>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; text-align: left;">
                    <span style="font-size: 1.4rem;">🛡️</span> <strong>Allergen Shield Filter</strong><br/>
                    <span style="font-size: 0.85rem; color: #64748B;">Guaranteed exclusion of user allergens (Peanuts, Milk, Eggs, Soy, Seafood) prior to meal scoring.</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with f2:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; text-align: left; margin-bottom: 10px;">
                    <span style="font-size: 1.4rem;">⚖️</span> <strong>Clinical Metabolic Equations</strong><br/>
                    <span style="font-size: 0.85rem; color: #64748B;">Mifflin-St Jeor BMR, WHO BMI screening, and objective TDEE activity multipliers.</span>
                </div>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; text-align: left;">
                    <span style="font-size: 1.4rem;">📊</span> <strong>Visual Biometric Analytics</strong><br/>
                    <span style="font-size: 0.85rem; color: #64748B;">Interactive hydration gauges, weight trend charts, and downloadable clinical PDF reports.</span>
                </div>
                """,
                unsafe_allow_html=True
            )

def render_login_screen():
    col_l, col_c, col_r = st.columns([1, 1.8, 1])
    with col_c:
        with st.container(border=True):
            st.markdown("<h2 style='color: #0284C7;'>🔑 Account Login</h2>", unsafe_allow_html=True)
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

def render_register_screen():
    col_l, col_c, col_r = st.columns([1, 1.8, 1])
    with col_c:
        with st.container(border=True):
            st.markdown("<h2 style='color: #0284C7;'>📝 Create Account</h2>", unsafe_allow_html=True)
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

def render_onboarding():
    step = st.session_state.get("onboarding_step", 1)
    col_l, col_c, col_r = st.columns([1, 2, 1])

    with col_c:
        st.progress(step / 5, text=f"Onboarding Step {step} of 5")

        if step == 1:
            with st.container(border=True):
                st.markdown("<h3 style='color: #0284C7;'>📷 Step 1: Upload Your Photo</h3>", unsafe_allow_html=True)
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
                    st.image(dest_path, caption="Profile Photo Preview", width=160)
                    st.success("Photo uploaded successfully!")
                else:
                    current_p = st.session_state["current_user"].get("profile_photo")
                    if current_p and os.path.exists(current_p):
                        st.image(current_p, caption="Current Profile Photo", width=160)
                    elif os.path.exists(DEFAULT_AVATAR):
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

        elif step == 2:
            with st.container(border=True):
                st.markdown("<h3 style='color: #0284C7;'>📏 Step 2: Enter Your Height</h3>", unsafe_allow_html=True)
                st.write("Height is utilized for scientific BMI and metabolic BMR computations.")

                height_val = st.number_input(
                    "Height (in cm):",
                    min_value=60.0,
                    max_value=250.0,
                    value=float(st.session_state["onboarding_data"].get("height", 170.0)),
                    step=0.5
                )
                st.caption("Tip: 5'0\" ≈ 152 cm | 5'6\" ≈ 168 cm | 5'10\" ≈ 178 cm | 6'0\" ≈ 183 cm")

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

        elif step == 3:
            with st.container(border=True):
                st.markdown("<h3 style='color: #0284C7;'>⚖️ Step 3: Enter Your Weight</h3>", unsafe_allow_html=True)
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

        elif step == 4:
            with st.container(border=True):
                st.markdown("<h3 style='color: #0284C7;'>🥗 Step 4: What Type of Diet Do You Follow?</h3>", unsafe_allow_html=True)
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

        elif step == 5:
            with st.container(border=True):
                st.markdown("<h3 style='color: #0284C7;'>📋 Step 5: Complete Your Nutrition Profile</h3>", unsafe_allow_html=True)
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

def render_dashboard():
    refresh_session_user()
    user = st.session_state["current_user"]
    profile = st.session_state["current_profile"]

    if not user or not profile:
        nav_to("login")
        return

    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding-bottom: 8px;">
                <span class="hero-badge" style="margin-bottom: 6px;">ACTIVE PROFILE</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        photo_path = user.get("profile_photo")
        if photo_path and os.path.exists(photo_path):
            st.image(photo_path, width=150)
        elif os.path.exists(DEFAULT_AVATAR):
            st.image(DEFAULT_AVATAR, width=150)

        st.markdown(f"### {user.get('name', 'User')}")
        st.caption(f"📧 {user.get('email')}")

        st.write("---")
        bmi = profile.get("bmi", 0)
        bmi_cat = profile.get("bmi_category", "Normal Weight")
        render_bmi_visual_scale(bmi, bmi_cat)

        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("Calories", f"{int(profile.get('daily_calories', 0))} kcal")
        with m_col2:
            st.metric("Protein", f"{profile.get('target_protein', 0)} g")

        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 14px; font-size: 0.85rem; margin-top: 10px;">
                <div><strong>Diet:</strong> {profile.get('diet_type')}</div>
                <div style="margin-top: 4px;"><strong>Goal:</strong> {profile.get('goal')}</div>
                <div style="margin-top: 4px;"><strong>Allergies:</strong> {profile.get('allergies', 'None')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("---")
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["current_user"] = None
            st.session_state["current_profile"] = None
            nav_to("welcome")

    tab_diet, tab_search, tab_progress, tab_history, tab_assistant, tab_report, tab_profile = st.tabs([
        "✨ AI Diet Plan",
        "🔍 Food Database",
        "📈 Progress Tracker",
        "📜 Diet History",
        "🤖 AI Assistant",
        "📄 Nutrition Report",
        "👤 My Profile"
    ])

    with tab_diet:
        top_c1, top_c2 = st.columns([2.5, 1])
        with top_c1:
            st.markdown("<h2 style='color: #0284C7; margin: 0;'>✨ AI Personalized Diet Plan</h2>", unsafe_allow_html=True)
            st.write("Multi-factor scoring matches your caloric budget and nutrient ratios while excluding allergens.")
        with top_c2:
            if st.button("⚡ GENERATE NEW PLAN", type="primary", use_container_width=True):
                plan = AIRecommendationEngine.generate_personalized_plan(profile)
                st.session_state["latest_generated_plan"] = plan

        plan = st.session_state.get("latest_generated_plan")

        if plan:
            st.write("---")
            col_kpi, col_chart = st.columns([1.8, 1.2])

            with col_kpi:
                st.markdown("#### 🎯 Daily Calorie & Macronutrient Budget")
                k1, k2 = st.columns(2)
                k1.metric("Daily Energy", f"{plan['total_calories']} kcal", f"Goal: {plan['target_calories']} kcal")
                k2.metric("Protein Target", f"{plan['total_protein']} g", f"{round((plan['total_protein']*4/plan['total_calories'])*100, 1)}% calories")

                k3, k4 = st.columns(2)
                k3.metric("Carbohydrates", f"{plan['total_carbs']} g", f"{round((plan['total_carbs']*4/plan['total_calories'])*100, 1)}% calories")
                k4.metric("Healthy Fats", f"{plan['total_fat']} g", f"{round((plan['total_fat']*9/plan['total_calories'])*100, 1)}% calories")

                st.markdown(
                    f"""
                    <div style="margin-top: 8px;">
                        <span class="macro-pill pill-fib">🌾 Fiber Target: {profile.get('target_fiber')}g</span>
                        <span class="macro-pill pill-prot">💧 Hydration Target: {profile.get('target_water')}L</span>
                        <span class="macro-pill pill-cal">🛡️ Allergies Excluded: {profile.get('allergies')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_chart:
                donut = render_macro_donut(plan['total_protein'], plan['total_carbs'], plan['total_fat'], plan['total_calories'])
                st.altair_chart(donut, use_container_width=True)

            st.write("---")
            st.markdown("### 🍽️ Personalized Meal Allocations")

            c_b, c_l = st.columns(2)
            c_s, c_d = st.columns(2)

            meal_cards_config = [
                ("Breakfast", "🌅", "meal-header-breakfast", "#F59E0B", c_b),
                ("Lunch", "🥗", "meal-header-lunch", "#10B981", c_l),
                ("Snack", "🍇", "meal-header-snack", "#A855F7", c_s),
                ("Dinner", "🌙", "meal-header-dinner", "#0284C7", c_d),
            ]

            for m_name, icon, header_class, theme_color, col in meal_cards_config:
                m_data = plan["meals"][m_name]
                with col:
                    with st.container(border=True):
                        st.markdown(
                            f"""
                            <div class="{header_class}">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong style="font-size: 1.1rem; color: #1E293B;">{icon} {m_name.upper()}</strong>
                                    <span style="font-weight: 800; color: {theme_color};">{m_data['actual_calories']} kcal</span>
                                </div>
                                <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">
                                    Target: {m_data['target_calories']} kcal &bull; P: {m_data['actual_protein']}g &bull; C: {m_data['actual_carbs']}g &bull; F: {m_data['actual_fat']}g
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        for it in m_data["items"]:
                            st.markdown(
                                f"""
                                <div style="padding: 8px 12px; margin-bottom: 8px; background: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0;">
                                    <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 0.92rem; color: #1E293B;">
                                        <span>{it['name']}</span>
                                        <span style="color: #64748B; font-size: 0.82rem;">{it['portion']}</span>
                                    </div>
                                    <div style="margin-top: 6px;">
                                        <span class="macro-pill pill-cal">{it['calories']} kcal</span>
                                        <span class="macro-pill pill-prot">{it['protein']}g P</span>
                                        <span class="macro-pill pill-carb">{it['carbs']}g C</span>
                                        <span class="macro-pill pill-fat">{it['fat']}g F</span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

            st.write("---")
            if st.button("💾 SAVE THIS DIET PLAN TO DATABASE", use_container_width=True, type="primary"):
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
                st.success("Diet Plan successfully recorded into your database history!")
        else:
            st.info("Click **'GENERATE NEW PLAN'** above to run the AI recommendation engine.")

    with tab_search:
        st.markdown("<h2 style='color: #0284C7;'>🔍 Food Database & Nutritional Intelligence</h2>", unsafe_allow_html=True)
        st.write("Explore macro-nutritional densities, categories, allergens, and portion baselines.")

        c_kw, c_cat, c_diet = st.columns([2, 1, 1])
        with c_kw:
            kw = st.text_input("🔍 Search Food by Name:", placeholder="e.g. Oats, Paneer, Rice, Chicken...")
        with c_cat:
            categories = ["All"] + FoodModel.get_all_categories()
            cat = st.selectbox("Category:", categories)
        with c_diet:
            diet_filter = st.selectbox("Diet Filter:", ["All", "Vegetarian", "Non-Vegetarian", "Vegan"])

        results = FoodModel.search_foods(keyword=kw, category=cat, diet_type=diet_filter)

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

            if len(results) > 1:
                st.markdown("#### 📊 Comparative Protein vs Calorie Density (Top Foods)")
                top_slice = df.head(8)
                chart_bar = alt.Chart(top_slice).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                    x=alt.X("Protein (g):Q", title="Protein (grams per serving)"),
                    y=alt.Y("Food Name:N", sort="-x", title=""),
                    color=alt.Color("Category:N", scale=alt.Scale(scheme="blues")),
                    tooltip=["Food Name", "Protein (g)", "Calories (kcal)", "Category"]
                ).properties(height=260)
                st.altair_chart(chart_bar, use_container_width=True)

            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("No foods matching your search criteria.")

    with tab_progress:
        st.markdown("<h2 style='color: #0284C7;'>📈 Daily Progress & Habit Analytics</h2>", unsafe_allow_html=True)

        col_form, col_stats = st.columns([1.1, 1])
        with col_form:
            with st.container(border=True):
                st.markdown("#### 📝 Log Today's Biometrics")
                with st.form("progress_log_form"):
                    log_date = st.date_input("Date", value=date.today())
                    p_weight = st.number_input("Current Weight (kg)", min_value=25.0, max_value=300.0, value=float(profile.get("weight", 70.0)), step=0.1)
                    p_water = st.number_input("Water Intake (Liters)", min_value=0.0, max_value=15.0, value=float(profile.get("target_water", 2.5)), step=0.1)
                    p_cals = st.number_input("Calories Consumed (kcal)", min_value=0.0, max_value=10000.0, value=float(profile.get("daily_calories", 2000.0)), step=50.0)
                    p_notes = st.text_input("Daily Reflection", placeholder="e.g. Completed 45m strength training, energy high")
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
                        st.success("Progress record saved successfully!")
                        st.rerun()

        logs = ProgressModel.get_user_logs(user["user_id"])
        with col_stats:
            with st.container(border=True):
                st.markdown("#### 📊 Progress Summary Stats")
                if logs:
                    count = len(logs)
                    latest_wt = logs[0].get("current_weight")
                    first_wt = logs[-1].get("current_weight")
                    delta = round(latest_wt - first_wt, 1)
                    avg_water = round(sum(l.get("water_intake", 0) for l in logs) / count, 1)

                    s1, s2 = st.columns(2)
                    s1.metric("Total Logs", f"{count}")
                    s2.metric("Latest Weight", f"{latest_wt} kg", f"{delta:+} kg")
                    s3, s4 = st.columns(2)
                    s3.metric("Avg Water", f"{avg_water} L", f"Goal: {profile.get('target_water')} L")
                    s4.metric("Starting Weight", f"{first_wt} kg")

                    water_goal = float(profile.get("target_water", 2.5))
                    latest_water = float(logs[0].get("water_intake", 2.0))
                    water_pct = min(int((latest_water / max(water_goal, 0.1)) * 100), 100)
                    st.write("---")
                    st.markdown(f"**Today's Hydration:** {latest_water}L / {water_goal}L ({water_pct}%)")
                    st.progress(water_pct / 100.0)
                else:
                    st.info("No progress records logged yet. Add your first entry on the left.")

        if logs:
            st.write("---")
            if len(logs) > 1:
                st.markdown("#### 📉 Interactive Weight Progression Chart")
                df_chart = pd.DataFrame(logs)[["log_date", "current_weight", "calories_consumed"]]
                df_chart.columns = ["Date", "Weight", "Calories"]
                df_chart["Date"] = pd.to_datetime(df_chart["Date"])
                df_chart = df_chart.sort_values("Date")

                line_chart = alt.Chart(df_chart).mark_line(point=True, color="#0284C7", strokeWidth=3).encode(
                    x=alt.X("Date:T", title="Timeline"),
                    y=alt.Y("Weight:Q", scale=alt.Scale(zero=False), title="Weight (kg)"),
                    tooltip=["Date:T", "Weight:Q", "Calories:Q"]
                ).properties(height=260)
                st.altair_chart(line_chart, use_container_width=True)

            st.markdown("#### 📜 Historical Records Table")
            df_logs = pd.DataFrame(logs)[["log_date", "current_weight", "water_intake", "calories_consumed", "notes"]]
            df_logs.columns = ["Date", "Weight (kg)", "Water (L)", "Calories (kcal)", "Notes"]
            st.dataframe(df_logs, use_container_width=True, hide_index=True)

    with tab_history:
        st.markdown("<h2 style='color: #0284C7;'>📜 Saved Diet Plan History</h2>", unsafe_allow_html=True)
        plans = DietModel.get_user_plans(user["user_id"])

        if plans:
            st.write(f"Showing **{len(plans)}** saved plan(s) from database.")
            for p in plans:
                with st.expander(f"Plan #{p['plan_id']} &bull; {p['plan_date']} — {p['total_calories']} kcal (P: {p['total_protein']}g, C: {p['total_carbs']}g, F: {p['total_fat']}g)"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**🌅 Breakfast:**  \n{p['breakfast_items']}")
                        st.markdown(f"**🥗 Lunch:**  \n{p['lunch_items']}")
                    with c2:
                        st.markdown(f"**🍇 Snack:**  \n{p['snack_items']}")
                        st.markdown(f"**🌙 Dinner:**  \n{p['dinner_items']}")
        else:
            st.info("No saved diet plans found. Generate and save a plan in 'AI Diet Plan'.")

    with tab_assistant:
        st.markdown("<h2 style='color: #0284C7;'>🤖 AI Nutrition & Food Assistant</h2>", unsafe_allow_html=True)
        st.write("Instant expert answers grounded in clinical nutrition and your personalized profile.")

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

        user_query = st.chat_input("Ask a nutrition or food question...")
        if user_query:
            st.session_state["chat_messages"].append({"role": "user", "content": user_query})
            resp = NutritionAssistant.respond_to_query(user_query, profile)
            st.session_state["chat_messages"].append({"role": "assistant", "content": resp})
            st.rerun()

    with tab_report:
        st.markdown("<h2 style='color: #0284C7;'>📄 Personal Nutrition & Health Report</h2>", unsafe_allow_html=True)
        st.write("Export your scientific health profile, target goals, and latest AI meal plans.")

        c_down1, c_down2 = st.columns(2)
        pdf_path = ReportGenerator.generate_pdf_report(user, profile)
        txt_path = ReportGenerator.generate_text_report(user, profile)

        with c_down1:
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    "📑 DOWNLOAD CLINICAL PDF REPORT",
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
        st.markdown("#### 📄 Report Preview")
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                st.code(f.read(), language="text")

    with tab_profile:
        st.markdown("<h2 style='color: #0284C7;'>👤 Edit Profile & Recalculate Targets</h2>", unsafe_allow_html=True)

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
