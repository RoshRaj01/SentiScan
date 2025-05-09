from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from config import DB_URL
import bcrypt
import os
from openai import OpenAI
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime
import traceback
import datetime
import json
import re

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

client = MongoClient(DB_URL)
db = client['SentiScan']

# Explicitly create collections if they don't exist
if 'user' not in db.list_collection_names():
    db.create_collection('user')

if 'analysis' not in db.list_collection_names():
    db.create_collection('analysis')

# Reference the collections
user_collection = db['user']
analysis_collection = db['analysis']


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        print("its working")
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        if user_collection.find_one({"email": email}):
            flash("User with this email already exists!", "danger")
            return redirect(url_for('register'))

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_collection.insert_one({
            "name": name,
            "phone": phone,
            "email": email,
            "password": hashed,
            "created_at": datetime.datetime.utcnow()
        })

        flash("Account Created Successfully!", "success")
        return redirect(url_for('login'))

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email') # either an email or phone_number
        password = request.form.get('password')

        if '@' in email:
            user = user_collection.find_one({"email": email})
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
                session['user_id'] = str(user['_id'])
                session['username'] = user['name']
                flash("Logged in successfully!", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid email or password", "danger")
                return redirect(url_for('login'))
        else:
            user = user_collection.find_one({"phone": email})
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
                session['user_id'] = str(user['_id'])
                session['username'] = user['name']
                flash("Logged in successfully!", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid email or password", "danger")
                return redirect(url_for('login'))

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for('login'))


@app.route('/home')
def home():
    if 'user_id' in session:
        user = user_collection.find_one({'_id': ObjectId(session['user_id'])})
        if user:
            return render_template("home.html", user={
                "name": user.get("name"),
                "email": user.get("email")
            })
    return redirect(url_for('login'))


@app.route('/admin')
def admin():
    total_users = user_collection.count_documents({})

    pipeline = [
        {"$group": {"_id": "$predicted_emotion", "count": {"$sum": 1}}}
    ]
    emotions_cursor = analysis_collection.aggregate(pipeline)
    emotions = {doc['_id']: doc['count'] for doc in emotions_cursor}

    usage_summary = {
        "avgSessions": 3.4,
        "avgDuration": "5m 12s"
    }

    return render_template('admin.html', total_users=total_users, emotions=emotions, usage_summary=usage_summary)


@app.route('/analyze', methods=['POST'])
def analyze_text():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json()
        user_input = data.get('text')

        if not user_input:
            return jsonify({'error': 'No text input provided'}), 400

        user = user_collection.find_one({'_id': ObjectId(session['user_id'])})
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user_name = user.get("name", "anonymous")

        prompt = f"""
        Analyze the following text and return ONLY a JSON object with the following:
        {{
          "content": "...",
          "sentiment_score": float (between -1 and 1),
          "key_words": ["..."],
          "sentiment_label": "Positive" | "Negative" | "Neutral",
          "confidence_score": float (between 0 and 1),
          "emotion_analysis": "Joy" | "Sadness" | "Anger" | etc.
        }}

        Text: "{user_input}"
        """

        # 🔧 Use the OpenAI client properly
        chat_response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sentiment analysis expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        raw_response = chat_response.choices[0].message.content
        print("🔵 OpenAI Response:\n", raw_response)

        # ✅ Extract only the JSON block
        json_match = re.search(r'{.*}', raw_response, re.DOTALL)
        if not json_match:
            return jsonify({"error": "Invalid OpenAI response format"}), 500

        result = json.loads(json_match.group())

        # ✅ Build MongoDB record with user name as key
        record = {
            user_name: {
                "text": result.get("content", user_input),
                "sentiment_score": result.get("sentiment_score"),
                "key_words": result.get("key_words"),
                "sentiment_label": result.get("sentiment_label"),
                "confidence_score": result.get("confidence_score"),
                "emotion_analysis": result.get("emotion_analysis"),
                "date": datetime.utcnow()
            }
        }

        analysis_collection.insert_one(record)

        return jsonify({
            "predicted_emotion": result.get("emotion_analysis"),
            "predicted_polarity": result.get("sentiment_label")
        })

    except Exception as e:
        print("❌ Error in /analyze route:")
        traceback.print_exc()
        return jsonify({"error": "Something went wrong on the server."}), 500



if __name__ == '__main__':
    app.run(debug=True)
