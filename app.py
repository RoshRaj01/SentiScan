from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from config import DB_URL
from bson.objectid import ObjectId
import bcrypt
import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with something strong in production

# Connect to MongoDB and use the "SentiScan" database
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


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
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
        email = request.form.get('email')
        password = request.form.get('password')

        user = user_collection.find_one({"email": email})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user_id'] = str(user['_id'])
            session['username'] = user['name']
            flash("Logged in successfully!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route('/home')
def home():
    if 'user_id' in session:
        return render_template("home.html", username=session.get('username'))
    return redirect(url_for('login'))


@app.route('/analyze', methods=['POST'])
def analyze_text():
    data = request.get_json()
    user_input = data.get('text')
    predicted_emotion = "Happy"  # Stub prediction for demo

    analysis_collection.insert_one({
        "user_id": session.get('user_id'),
        "text": user_input,
        "predicted_emotion": predicted_emotion,
        "timestamp": datetime.datetime.utcnow()
    })

    return jsonify({
        'message': 'Text analyzed successfully',
        'predicted_emotion': predicted_emotion
    })


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


if __name__ == '__main__':
    app.run(debug=True)
