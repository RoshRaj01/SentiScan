from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from config import DB_URL
import bcrypt
import os
import requests
import requests.exceptions
from bson import ObjectId
from datetime import datetime, date
import traceback
import json
import re
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

client = MongoClient(DB_URL)
db = client['SentiScan']

user_collection = db['user']
analysis_collection = db['analysis']
api_usage_collection = db['api_usage']


# === HELPER FUNCTIONS ===
def get_today():
    return date.today().isoformat()


# === ROUTES ===
@app.route('/')
def index():
    return redirect(url_for('login'))


def is_password_strong(password):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
    return bool(re.match(pattern, password))

def send_confirmation_email(to_email):
    sender_email = "sentiscan.info@gmail.com"
    sender_password = "sock xjke agqo bugj"

    subject = "Welcome to SentiScan 🎉"
    body = "Hey there!\n\nYou’ve successfully created an account in *SentiScan*.\nLet’s start analysing!"

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        print(f"[✔️] Mail sent to {to_email}")

    except Exception as e:
        print(f"[❌] Failed to send mail to {to_email} - {e}")
        return False

    return True
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')

        if user_collection.find_one({"email": email}):
            flash("Email already in use. Try logging in or use another.", "danger")
            return redirect(url_for('register'))

        if user_collection.find_one({"phone": phone}):
            flash("Phone number already registered. Use another one.", "danger")
            return redirect(url_for('register'))

        if not is_password_strong(password):
            flash("Password is too weak. It must contain upper, lower, number, special character and be 8+ characters.",
                  "danger")
            return redirect(url_for('register'))

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user_collection.insert_one({
            "name": name,
            "phone": phone,
            "email": email,
            "password": hashed,
            "created_at": datetime.now(),
            "api_keys": []
        })

        send_confirmation_email(email)

        flash("Account Created Successfully!", "success")
        return redirect(url_for('login'))

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_phone = request.form.get('email')
        password = request.form.get('password')

        user = None
        if '@' in email_or_phone:
            user = user_collection.find_one({"email": email_or_phone})
        else:
            user = user_collection.find_one({"phone": email_or_phone})

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user_id'] = str(user['_id'])
            session['username'] = user['name']
            flash("Logged in successfully!", "success")
            return redirect(url_for('docs'))

        flash("Invalid credentials", "danger")
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
            return render_template("home.html", user=user)
    return redirect(url_for('login'))


@app.route('/apis')
def apis():
    if 'user_id' in session:
        user = user_collection.find_one({'_id': ObjectId(session['user_id'])})
        return render_template('apis.html', user=user)
    return redirect(url_for('login'))


@app.route('/generate_new_key', methods=['POST'])
def generate_new_key():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    model = data.get('model', 'r1')  # default r1 if not provided

    if model not in ['r1', 'r2', 'r3']:
        return jsonify({"error": "Invalid model selected."}), 400

    random_key = str(uuid.uuid4()).replace("-", "")  # shorter random
    full_key = f"ss-{model}-{random_key}"

    user_collection.update_one(
        {"_id": ObjectId(session['user_id'])},
        {"$push": {"api_keys": full_key}}
    )
    return jsonify({"api_key": full_key})


@app.route('/verify_api_key', methods=['POST'])
def verify_api_key():
    if 'user_id' not in session:
        return jsonify({"valid": False, "message": "Unauthorized. Please login again."}), 401

    data = request.get_json()
    entered_key = data.get('api_key')

    if not entered_key:
        return jsonify({"valid": False, "message": "No API key provided."}), 400

    # Fetch only the current logged-in user
    user = user_collection.find_one({"_id": ObjectId(session['user_id'])})

    if user and entered_key in user.get('api_keys', []):
        return jsonify({"valid": True, "message": "✅     API key is valid!"})
    else:
        return jsonify({"valid": False, "message": "❌ Invalid API key."})


@app.route('/delete_api_key', methods=['POST'])
def delete_api_key():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    api_key_to_delete = data.get('api_key')

    if not api_key_to_delete:
        return jsonify({"error": "No API key provided"}), 400

    user_collection.update_one(
        {"_id": ObjectId(session['user_id'])},
        {"$pull": {"api_keys": api_key_to_delete}}
    )
    return jsonify({"success": True, "message": "API key deleted successfully."})


@app.route('/usage')
def usage():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    api_key = request.args.get('api_key')  # <-- Get it from URL
    if not api_key:
        flash("API Key missing. Please select an API key to view usage.", "danger")
        return redirect(url_for('apis'))

    user = user_collection.find_one({'_id': ObjectId(session['user_id'])})
    user_name = user.get('name')
    user['max_analysis_limit'] = user.get('max_analysis_limit', 20)

    analysis_docs = list(analysis_collection.find({"user": user_name, "api_key": api_key}))

    analyses = []
    emotions = {}
    polarities = {}
    keywords = {}
    conf_sum = 0
    sent_sum = 0


    for doc in analysis_docs:
        data = {
            "text": doc.get("text", ""),
            "emotion_analysis": doc.get("emotion_analysis", ""),
            "sentiment_label": doc.get("sentiment_label", ""),
            "confidence_score": doc.get("confidence_score", 0),
            "sentiment_score": doc.get("sentiment_score", 0),
            "key_words": doc.get("key_words", []),
            "date": doc.get("date", datetime.now())
        }
        analyses.append(data)

        emotion = data.get("emotion_analysis")
        if emotion:
            emotions[emotion] = emotions.get(emotion, 0) + 1

        polarity = data.get("sentiment_label")
        if polarity:
            polarities[polarity] = polarities.get(polarity, 0) + 1

        for kw in data.get("key_words", []):
            keywords[kw] = keywords.get(kw, 0) + 1

        conf_sum += data.get("confidence_score", 0)
        sent_sum += data.get("sentiment_score", 0)

    total = len(analyses)
    conf_avg = round(conf_sum / total, 3) if total else 0
    sent_avg = round(sent_sum / total, 3) if total else 0

    return render_template(
        "usage.html",
        user=user, api_key=api_key, used=total, remaining=max(0, 20 - total), analyses=analyses, emotions=emotions,
        polarities=polarities, keywords=keywords, conf_avg=conf_avg, sent_avg=sent_avg)


@app.route('/analyze', methods=['POST'])
def analyze_text():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized. Please login again.'}), 401

        data = request.get_json()
        user_input = data.get('text')
        api_key = data.get('api_key')

        if not user_input or not api_key:
            return jsonify({'error': 'Missing text or API key'}), 400

        user = user_collection.find_one({'_id': ObjectId(session['user_id'])})

        if not user or api_key not in user.get('api_keys', []):
            return jsonify({'error': 'Invalid API Key'}), 401

        today = get_today()
        usage = api_usage_collection.find_one({'api_key': api_key, 'date': today})

        if usage and usage['count'] >= 20:
            return jsonify({'error': 'API key daily limit reached'}), 403

        # Build the prompt
        prompt = f"""
        You are a professional sentiment and emotion analysis tool.
        For the given text, respond ONLY in JSON format with the following fields:

        {{
            "content": (the original input text),
            "sentiment_score": (float between -1 and 1),
            "key_words": (important keywords extracted from the text which indicate sentiment),
            "sentiment_label": (Positive, Negative, or Neutral),
            "confidence_score": (float between 0 and 1 indicating certainty),
            "emotion_analysis": (dominant emotion like Joy, Sadness, Anger, Fear, Disgust, Surprise, Anxiety, Happiness, Love, Jealousy, Shame, Calmness, Doubt, Embarrassment, Enjoyment, Anticipation, Contempt, Envy, Excitement, Pride, Awe, Depression, etc.)
        }}

        Text: "{user_input}"
        """

        try:
            ollama_response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama3.2:1b", "prompt": prompt, "stream": False},
                timeout=20
            )
        except requests.exceptions.ConnectionError:
            return jsonify({"error": "Ollama server is unavailable. Please try again later."}), 503
        except requests.exceptions.Timeout:
            return jsonify({"error": "Ollama server timeout. Please try again."}), 504

        if ollama_response.status_code != 200:
            return jsonify({"error": "Ollama API failed"}), 500

        raw_response = ollama_response.json().get("response", "")

        json_match = re.search(r'{.*}', raw_response, re.DOTALL)
        if not json_match:
            return jsonify({"error": "Invalid response format from model"}), 500

        result = json.loads(json_match.group())

        record = {
            "user": user.get('name', 'anonymous'),
            "api_key": api_key,
            "text": result.get("content", user_input),
            "sentiment_score": result.get("sentiment_score"),
            "key_words": result.get("key_words"),
            "sentiment_label": result.get("sentiment_label"),
            "confidence_score": result.get("confidence_score"),
            "emotion_analysis": result.get("emotion_analysis"),
            "date": datetime.now()
        }

        print(record)
        analysis_collection.insert_one(record)

        if usage:
            api_usage_collection.update_one({'_id': usage['_id']}, {'$inc': {'count': 1}})
        else:
            api_usage_collection.insert_one({'api_key': api_key, 'date': today, 'count': 1})

        return jsonify({
            "predicted_emotion": result.get("emotion_analysis"),
            "predicted_polarity": result.get("sentiment_label")
        })

    except Exception as e:
        print("❌ Error in /analyze route:")
        traceback.print_exc()
        return jsonify({"error": "Server error occurred."}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        user_input = data.get('text')
        api_key = data.get('api_key')

        if not user_input or not api_key:
            return jsonify({'error': 'Missing text or API key'}), 400

        # Find the user who owns this API key
        user = user_collection.find_one({'api_keys': api_key})
        if not user:
            return jsonify({'error': 'Invalid API Key'}), 401

        today = get_today()
        usage = api_usage_collection.find_one({'api_key': api_key, 'date': today})

        if usage and usage['count'] >= 20:
            return jsonify({'error': 'API key daily limit reached'}), 403

        # Build the prompt
        prompt = f"""
        You are a professional sentiment and emotion analysis tool.
        For the given text, respond ONLY in JSON format with the following fields:

        {{
            "content": (the original input text),
            "sentiment_score": (float between -1 and 1),
            "key_words": (important keywords extracted from the text which indicate sentiment),
            "sentiment_label": (Positive, Negative, or Neutral),
            "confidence_score": (float between 0 and 1 indicating certainty),
            "emotion_analysis": (dominant emotion like Joy, Sadness, Anger, Fear, Disgust, Surprise, Anxiety, Happiness, Love, Jealousy, Shame, Calmness, Doubt, Embarrassment, Enjoyment, Anticipation, Contempt, Envy, Excitement, Pride, Awe, Depression, etc.)
        }}

        Text: "{user_input}"
        """

        try:
            ollama_response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama3.2:1b", "prompt": prompt, "stream": False},
                timeout=20
            )
        except requests.exceptions.ConnectionError:
            return jsonify({"error": "Ollama server is unavailable. Please try again later."}), 503
        except requests.exceptions.Timeout:
            return jsonify({"error": "Ollama server timeout. Please try again."}), 504

        if ollama_response.status_code != 200:
            return jsonify({"error": "Ollama API failed"}), 500

        raw_response = ollama_response.json().get("response", "")
        json_match = re.search(r'{.*}', raw_response, re.DOTALL)

        if not json_match:
            return jsonify({"error": "Invalid response format from model"}), 500

        result = json.loads(json_match.group())

        record = {
            "user": user.get('name', 'anonymous'),
            "api_key": api_key,
            "text": result.get("content", user_input),
            "sentiment_score": result.get("sentiment_score"),
            "key_words": result.get("key_words"),
            "sentiment_label": result.get("sentiment_label"),
            "confidence_score": result.get("confidence_score"),
            "emotion_analysis": result.get("emotion_analysis"),
            "date": datetime.now()
        }

        analysis_collection.insert_one(record)

        if usage:
            api_usage_collection.update_one({'_id': usage['_id']}, {'$inc': {'count': 1}})
        else:
            api_usage_collection.insert_one({'api_key': api_key, 'date': today, 'count': 1})

        return jsonify({
            "predicted_emotion": result.get("emotion_analysis"),
            "predicted_polarity": result.get("sentiment_label")
        })

    except Exception as e:
        print("❌ Error in /api/analyze route:")
        traceback.print_exc()
        return jsonify({"error": "Server error occurred."}), 500


@app.route('/docs')
def docs():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = user_collection.find_one({'_id': ObjectId(session['user_id'])})
    return render_template('docs.html', user=user)


@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get total users
    total_users = user_collection.count_documents({})

    # Analyze models from API keys
    model_counts = {"r1": 0, "r2": 0, "r3": 0}
    all_users = user_collection.find({})
    for user in all_users:
        for key in user.get('api_keys', []):
            parts = key.split('/')
            if len(parts) > 2:
                model = parts[1]
                if model in model_counts:
                    model_counts[model] += 1

    # Analyze predicted emotions
    emotions = {}
    all_analyses = analysis_collection.find()
    for doc in all_analyses:
        for user_data in doc.values():
            if isinstance(user_data, dict):
                emotion = user_data.get("emotion_analysis")
                if emotion:
                    emotions[emotion] = emotions.get(emotion, 0) + 1

    return render_template('admin.html',
                           total_users=total_users,
                           model_counts=model_counts,
                           emotions=emotions,
                           )




if __name__ == '__main__':
    app.run(debug=True)
