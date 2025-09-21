
# ...existing code...

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os
import secrets # For generating patient_id
#from weasyprint import HTML # For PDF generation (requires installation: pip install weasyprint)
import uuid # For unique filenames


from datetime import datetime
from werkzeug.utils import secure_filename
 

app = Flask(__name__)
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

app.secret_key = 'supersecretkey'  # Replace with a strong, random key in production
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'smarthealth.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads') # Folder for profile pictures/other uploads

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)




from flask_migrate import Migrate
migrate = Migrate(app, db)




# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    
    # Relationships to new models
    profile = db.relationship('Profile', backref='user', uselist=False, lazy=True) # One-to-one
    medical_histories = db.relationship('MedicalHistory', backref='user', lazy=True)
    medicines = db.relationship('Medicine', backref='user', lazy=True)
    habits = db.relationship('Habit', backref='user', lazy=True)
    uploads = db.relationship('Upload', backref='user', lazy=True)
    planner_entries = db.relationship('PlannerEntry', backref='user', lazy=True)
    bmi_entries = db.relationship('BMIEntry', backref='user', lazy=True)
    emergency_contacts = db.relationship('EmergencyContact', backref='user', lazy=True)
    exercise_logs = db.relationship('ExerciseLog', backref='user', lazy=True)
    meal_plan_entries = db.relationship('MealPlanEntry', backref='user', lazy=True)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    patient_id = db.Column(db.String(20), unique=True, nullable=True)
    full_name = db.Column(db.String(200), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(250), nullable=True)
    profile_picture_url = db.Column(db.String(250), nullable=True)
    # Add these fields:
    email = db.Column(db.String(150), nullable=True)
    age = db.Column(db.String(10), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    blood_type = db.Column(db.String(10), nullable=True)
    height = db.Column(db.String(10), nullable=True)
    weight = db.Column(db.String(10), nullable=True)
    disability = db.Column(db.String(100), nullable=True)

class MedicalHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    condition = db.Column(db.String(200), nullable=False)
    diagnosis_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_filename = db.Column(db.String(250), nullable=True)  # Stores uploaded document filename

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    start_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # <-- Add this line
    taken = db.Column(db.Boolean, default=False)

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_name = db.Column(db.String(150), nullable=False)
    frequency = db.Column(db.String(50))
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    done = db.Column(db.Boolean, default=False)  # <-- Add this line

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class PlannerEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class BMIEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    bmi_value = db.Column(db.Float, nullable=False)
    date_recorded = db.Column(db.Date, default=date.today)

class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50), nullable=True)
    phone_number = db.Column(db.String(20), nullable=False)

class ExerciseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_name = db.Column(db.String(150), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    calories_burned = db.Column(db.Float, nullable=True)
    log_date = db.Column(db.Date, default=date.today)

class MealPlanEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_type = db.Column(db.String(50), nullable=False) # e.g., 'Breakfast', 'Lunch', 'Dinner', 'Snack'
    food_item = db.Column(db.String(200), nullable=False)
    calories = db.Column(db.Float, nullable=True)
    meal_date = db.Column(db.Date, default=date.today)

# Helper function for generating unique patient ID
def generate_patient_id():
    # Simple alphanumeric ID
    return 'PID-' + secrets.token_hex(4).upper()

# Routes
@app.context_processor
def inject_profile():
    user_id = session.get("user_id")
    profile = None
    if user_id:
        profile = Profile.query.filter_by(user_id=user_id).first()
    return dict(profile=profile)



@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "error")
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password)
        user = User(email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        
        # Create a default profile for the new user
        new_profile = Profile(user_id=user.id, patient_id=generate_patient_id())
        db.session.add(new_profile)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Logged in successfully.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials.", "error")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    
    # Gather counts for dashboard
    medicine_count = len(user.medicines)
    habit_count = len(user.habits)
    upload_count = len(user.uploads)
    bmi_count = len(user.bmi_entries)
    emergency_contact_count = len(user.emergency_contacts)
    exercise_log_count = len(user.exercise_logs)
    meal_plan_count = len(user.meal_plan_entries)

    return render_template('dashboard.html',
                           medicine_count=medicine_count,
                           habit_count=habit_count,
                           upload_count=upload_count,
                           bmi_count=bmi_count,
                           emergency_contact_count=emergency_contact_count,
                           exercise_log_count=exercise_log_count,
                           meal_plan_count=meal_plan_count)

# Existing Routes (Updated to fetch specific user data)
@app.route('/medical_history', methods=['GET', 'POST'])
def medical_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        condition = request.form['condition']
        date_str = request.form['date']
        diagnosis_date_str = request.form['date']
        diagnosis_date = datetime.strptime(diagnosis_date_str, '%Y-%m-%d').date()

        document_filename = None
        if 'document' in request.files:
            file = request.files['document']
            if file and file.filename != '':
                filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                document_filename = filename

        new_history = MedicalHistory(
    condition=condition,
    diagnosis_date=diagnosis_date,   # ✅ correct
    user_id=session['user_id'],
    document_filename=document_filename
)

        db.session.add(new_history)
        db.session.commit()
        flash('Medical history added!', 'success')
        return redirect(url_for('medical_history'))

    histories = MedicalHistory.query.filter_by(user_id=session['user_id']).all()
    return render_template('medical_history.html', histories=histories)
@app.route("/about")
def about():
    return render_template("about.html")


@app.route('/remove_meal/<int:meal_id>', methods=['POST'])
def remove_meal(meal_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    meal = MealPlanEntry.query.get_or_404(meal_id)
    
    if meal.user_id != session['user_id']:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('diet_planner'))

    db.session.delete(meal)
    db.session.commit()
    flash("Meal removed successfully!", "success")
    return redirect(url_for('diet_planner'))





@app.route('/medicine', methods=['GET', 'POST'])
def medicine():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        dosage = request.form.get('dosage', '')
        frequency = request.form.get('frequency', '')
        start_date_str = request.form.get('start_date', '')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        new_medicine = Medicine(
            name=name,
            dosage=dosage,
            frequency=frequency,
            start_date=start_date,
            user_id=session['user_id']
        )
        db.session.add(new_medicine)
        db.session.commit()
        flash('Medicine added!', 'success')
        return redirect(url_for('medicine'))

    medicines = Medicine.query.filter_by(user_id=session['user_id']).all()
    return render_template('medicines.html', medicines=medicines)

@app.route('/medicine/mark_taken/<int:medicine_id>', methods=['POST'])
def mark_taken(medicine_id):
    med = Medicine.query.get_or_404(medicine_id)
    med.taken = True
    db.session.commit()
    return redirect(url_for('medicine'))

@app.route('/medicine/remove/<int:medicine_id>', methods=['POST'])
def remove_medicine(medicine_id):
    med = Medicine.query.get_or_404(medicine_id)
    db.session.delete(med)
    db.session.commit()
    return redirect(url_for('medicine'))



@app.route('/habits', methods=['GET', 'POST'])
def habits():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        habit_name = request.form['habit_name']
        frequency = request.form.get('frequency', '')
        notes = request.form.get('notes', '')
        new_habit = Habit(
            habit_name=habit_name,
            frequency=frequency,
            notes=notes,
            user_id=session['user_id'],
            done=False  # Make sure your Habit model has a 'done' Boolean field
        )
        db.session.add(new_habit)
        db.session.commit()
        flash('Habit added!', 'success')
        return redirect(url_for('habits'))

    habits = Habit.query.filter_by(user_id=session['user_id']).all()
    return render_template('habits.html', habits=habits)

@app.route('/habits/mark_done/<int:habit_id>', methods=['POST'])
def mark_habit_done(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    habit.done = True
    db.session.commit()
    return redirect(url_for('habits'))

@app.route('/habits/remove/<int:habit_id>', methods=['POST'])
def remove_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    db.session.delete(habit)
    db.session.commit()
    return redirect(url_for('habits'))

@app.route('/reminder')
def reminder():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('reminder.html')

@app.route('/planner')
def planner():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Fetch planner entries for the current user
    user = User.query.get(session['user_id'])
    planner_entries = user.planner_entries
    return render_template('planner.html', planner_entries=planner_entries)

# In your Flask route for analytics




@app.route('/upload')
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    uploads = user.uploads
    # Fetch medical history documents for the current user
    medical_documents = [h for h in user.medical_histories if h.document_filename]
    return render_template('upload.html', uploads=uploads, medical_documents=medical_documents)


# --- New Routes ---

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_profile = Profile.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        if not user_profile:
            # Create a new profile if not exists
            user_profile = Profile(user_id=user_id)
            db.session.add(user_profile)

        user_profile.full_name = request.form.get('full_name')
        user_profile.email = request.form.get('email')
        user_profile.contact_number = request.form.get('contact_number')
        user_profile.age = request.form.get('age')
        user_profile.gender = request.form.get('gender')
        user_profile.blood_type = request.form.get('blood_type')
        user_profile.height = request.form.get('height')
        user_profile.weight = request.form.get('weight')
        user_profile.disability = request.form.get('disability')

        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                user_profile.profile_picture_url = url_for('uploaded_file', filename=filename)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))

    return render_template('profile.html', profile=user_profile)


# Route to serve uploaded files (e.g., profile pictures)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Serve file inline if possible (PDF, images, etc.)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)



@app.route('/remove_record/<int:record_id>', methods=['POST'])
def remove_record(record_id):
    record = MedicalHistory.query.get_or_404(record_id)
    # Optional: delete uploaded file
    if record.document_filename:
        file_path = os.path.join('static/uploads', record.document_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('medical_history'))




@app.route('/remove_note_document/<int:record_id>', methods=['POST'])
def remove_note_document(record_id):
    record = MedicalHistory.query.get_or_404(record_id)

    # Delete uploaded file if exists
    if record.document_filename:
        file_path = os.path.join('static/uploads', record.document_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    # Remove only the note/description and document filename
    record.description = None
    record.document_filename = None

    db.session.commit()
    return redirect(url_for('medical_history'))






@app.route('/bmi_calculator', methods=['GET', 'POST'])
def bmi_calculator():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    bmi_history = BMIEntry.query.filter_by(user_id=user_id).order_by(BMIEntry.date_recorded.desc()).all()
    
    if request.method == 'POST':
        try:
            height_cm = float(request.form['height_cm'])
            weight_kg = float(request.form['weight_kg'])
            
            if height_cm <= 0 or weight_kg <= 0:
                flash("Height and weight must be positive values.", "error")
                return redirect(url_for('bmi_calculator'))

            height_m = height_cm / 100
            bmi = weight_kg / (height_m ** 2) # BMI calculation: weight (kg) / (height (m))^2
            
            new_bmi_entry = BMIEntry(user_id=user_id, height_cm=height_cm, weight_kg=weight_kg, bmi_value=bmi)
            db.session.add(new_bmi_entry)
            db.session.commit()
            flash(f"BMI calculated and saved: {bmi:.2f}", "success")
            return redirect(url_for('bmi_calculator'))
        except ValueError:
            flash("Invalid input. Please enter numeric values for height and weight.", "error")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        return redirect(url_for('bmi_calculator'))

    return render_template('bmi_calculator.html', bmi_history=bmi_history)

@app.route('/emergency_contacts', methods=['GET', 'POST'])
def emergency_contacts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    contacts = EmergencyContact.query.filter_by(user_id=user_id).all()

    if request.method == 'POST':
        name = request.form['name']
        relationship = request.form['relationship']
        phone_number = request.form['phone_number']

        if not name or not phone_number:
            flash("Name and Phone Number are required.", "error")
            return redirect(url_for('emergency_contacts'))
        
        new_contact = EmergencyContact(user_id=user_id, name=name, relationship=relationship, phone_number=phone_number)
        db.session.add(new_contact)
        db.session.commit()
        flash("Emergency contact added!", "success")
        return redirect(url_for('emergency_contacts'))
    
    return render_template('emergency_contacts.html', contacts=contacts)

@app.route('/exercise_tracker', methods=['GET', 'POST'])
def exercise_tracker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    exercise_logs = ExerciseLog.query.filter_by(user_id=user_id).order_by(ExerciseLog.log_date.desc()).all()

    if request.method == 'POST':
        activity_name = request.form['activity_name']
        duration_minutes_str = request.form['duration_minutes']
        calories_burned_str = request.form.get('calories_burned')
        log_date_str = request.form.get('log_date')

        if not activity_name or not duration_minutes_str:
            flash("Activity Name and Duration are required.", "error")
            return redirect(url_for('exercise_tracker'))
        
        try:
            duration_minutes = int(duration_minutes_str)
            calories_burned = float(calories_burned_str) if calories_burned_str else None
            log_date = datetime.strptime(log_date_str, '%Y-%m-%d').date() if log_date_str else date.today()

            new_log = ExerciseLog(user_id=user_id, activity_name=activity_name,
                                  duration_minutes=duration_minutes, calories_burned=calories_burned,
                                  log_date=log_date)
            db.session.add(new_log)
            db.session.commit()
            flash("Exercise logged successfully!", "success")
            return redirect(url_for('exercise_tracker'))
        except ValueError:
            flash("Invalid input for duration or calories. Please enter numeric values.", "error")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        return redirect(url_for('exercise_tracker'))
    
    return render_template('exercise_tracker.html', exercise_logs=exercise_logs)

@app.route('/diet_planner', methods=['GET', 'POST'])
def diet_planner():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    meal_plans = MealPlanEntry.query.filter_by(user_id=user_id).order_by(MealPlanEntry.meal_date.desc(), MealPlanEntry.meal_type).all()

    if request.method == 'POST':
        meal_type = request.form['meal_type']
        food_item = request.form['food_item']
        calories_str = request.form.get('calories')
        meal_date_str = request.form.get('meal_date')

        if not meal_type or not food_item:
            flash("Meal Type and Food Item are required.", "error")
            return redirect(url_for('diet_planner'))
        
        try:
            calories = float(calories_str) if calories_str else None
            meal_date = datetime.strptime(meal_date_str, '%Y-%m-%d').date() if meal_date_str else date.today()

            new_meal = MealPlanEntry(user_id=user_id, meal_type=meal_type,
                                     food_item=food_item, calories=calories,
                                     meal_date=meal_date)
            db.session.add(new_meal)
            db.session.commit()
            flash("Meal added to planner!", "success")
            return redirect(url_for('diet_planner'))
        except ValueError:
            flash("Invalid input for calories. Please enter a numeric value.", "error")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        return redirect(url_for('diet_planner'))
    
    return render_template('diet_planner.html', meal_plans=meal_plans)

@app.route('/health_tips')
def health_tips():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Static list of health tips - could be dynamic from a DB model too
    health_tips_list = [
        # Getting Started
        "The best project you’ll ever work on is you.",
        "Small steps, big changes.",
        "Your health is an investment, not an expense.",
        "The only bad workout is the one that didn’t happen.",
        "Start where you are. Use what you have. Do what you can. – Arthur Ashe",
        "The difference between try and triumph is a little umph.",
        "Your body hears everything your mind says.",
        "Don’t wait until you’ve reached your goal to be proud of yourself. Be proud of every step you take.",
        "Motivation is what gets you started. Habit is what keeps you going.",
        "The expert in anything was once a beginner.",
        "You don’t have to be great to start, but you have to start to be great.",
        "A journey of a thousand miles begins with a single step. – Lao Tzu",
        "The hardest lift of all is lifting your butt off the couch.",
        "Today I will do what others won’t, so tomorrow I can do what others can’t.",
        "Your future self is watching you right now through memories.",
        "The only way to do great things is to love what you do. – Steve Jobs",
        "Every action you take is a vote for the person you wish to become.",
        "The clock is ticking. Are you becoming the person you want to be?",
        # Overcoming Obstacles
        "Fall seven times, stand up eight. – Japanese Proverb",
        "Your body can stand almost anything. It’s your mind you have to convince.",
        "Don’t stop when you’re tired. Stop when you’re done.",
        "Pain is temporary. Quitting lasts forever.",
        "The only disability in life is a bad attitude. – Scott Hamilton",
        "Strength doesn’t come from what you can do. It comes from overcoming the things you once thought you couldn’t.",
        "When you feel like quitting, remember why you started.",
        "The struggle you’re in today is developing the strength you need for tomorrow.",
        "It’s not about perfect. It’s about effort.",
        "Obstacles don’t have to stop you. If you run into a wall, don’t turn around and give up. Figure out how to climb it, go through it, or work around it. – Michael Jordan",
        "What hurts today makes you stronger tomorrow.",
        "The pain you feel today will be the strength you feel tomorrow.",
        "Challenges are what make life interesting. Overcoming them is what makes life meaningful. – Joshua J. Marine",
        "You may encounter many defeats, but you must not be defeated. – Maya Angelou",
        "The greatest glory in living lies not in never falling, but in rising every time we fall. – Nelson Mandela",
        "Tough times don’t last. Tough people do.",
        "Your biggest challenge isn’t someone else. It’s the voice in your head.",
        "Don’t wish it were easier. Wish you were better.",
        # Consistency and Routine
        "Consistency is harder when no one is clapping for you. You must clap for yourself.",
        "We are what we repeatedly do. Excellence, then, is not an act, but a habit. – Aristotle",
        "Small disciplines repeated with consistency every day lead to great achievements gained slowly over time. – John C. Maxwell",
        "Success isn’t always about greatness. It’s about consistency.",
        "It’s not what we do once in a while that shapes our lives. It’s what we do consistently.",
        "The secret of your future is hidden in your daily routine.",
        "Motivation gets you going, but discipline keeps you growing.",
        "Discipline is choosing between what you want now and what you want most.",
        "Daily practices, not occasional efforts, bring lasting change.",
        "Consistency beats intensity every time.",
        "Don’t expect to see a change if you don’t make one.",
        "A year from now, you’ll wish you had started today.",
        "Habits form character, and character forms destiny.",
        "The difference between who you are and who you want to be is what you do.",
        "Show up even on the days you don’t feel like it.",
        "Consistency is the true foundation of trust.",
        "Small consistent efforts lead to big consistent results.",
        "What you do every day matters more than what you do once in a while.",
        # Nutrition and Eating Right
        "Let food be thy medicine and medicine be thy food. – Hippocrates",
        "You are what you eat, so don’t be fast, cheap, easy, or fake.",
        "The food you eat can be either the safest and most powerful form of medicine or the slowest form of poison.",
        "Eat for the body you want, not for the body you have.",
        "Your diet is a bank account. Good food choices are good investments.",
        "If you keep good food in your fridge, you will eat good food.",
        "Take care of your body. It’s the only place you have to live. – Jim Rohn",
        "The first wealth is health. – Ralph Waldo Emerson",
        "Don’t dig your grave with your own knife and fork.",
        "Healthy eating isn’t about counting calories, it’s about counting chemicals.",
        "Eat to nourish your body, not just to feed your hunger.",
        "Every time you eat is an opportunity to nourish your body.",
        "The greatest wealth is health. – Virgil",
        "Your body is a temple, but only if you treat it as one.",
        "Processed foods are like one-night stands. They seem good at the time but leave you feeling lousy the next day.",
        "A healthy outside starts from the inside.",
        "An apple a day keeps the doctor away, but a healthy diet keeps the medicines away.",
        "Nutrition is not about eating more or eating less. It’s about eating right.",
        # Fitness and Exercise
        "Exercise is king. Nutrition is queen. Put them together and you’ve got a kingdom. – Jack LaLanne",
        "The only bad workout is the one that didn’t happen.",
        "Fitness is not about being better than someone else. It’s about being better than you used to be.",
        "No matter how slow you go, you’re still lapping everyone on the couch.",
        "Sweat is just fat crying.",
        "Your health is your wealth.",
        "The body achieves what the mind believes.",
        "Exercise is a celebration of what your body can do, not a punishment for what you ate.",
        "You don’t have to be extreme, just consistent.",
        "The pain of discipline weighs ounces, while the pain of regret weighs tons.",
        "Strong is the new beautiful.",
        "Train like a beast, look like a beauty.",
        "The only place where success comes before work is in the dictionary.",
        "Sore today, strong tomorrow.",
        "You can feel sore tomorrow or sorry tomorrow. You choose.",
        "Fitness is like marriage. You can’t cheat on it and expect it to work.",
        "Your body keeps an accurate journal regardless of what you write down.",
        "The hardest thing about exercise is to start doing it. Once you’re doing it regularly, the hardest thing is to stop it.",
        # Mental Well-being
        "Self-care is not selfish. You cannot serve from an empty vessel. – Eleanor Brown",
        "Mental health is not a destination, but a process.",
        "Your mind will quit a thousand times before your body will.",
        "Happiness is the highest form of health. – Dalai Lama",
        "Almost everything will work again if you unplug it for a few minutes, including you.",
        "You can’t pour from an empty cup. Take care of yourself first.",
        "The mind is like a parachute. It works best when it’s open.",
        "Breathe. Let go. And remind yourself that this very moment is the only one you know you have for sure.",
        "Your mental health is a priority. Your happiness is essential. Your self-care is a necessity.",
        "Peace is the result of retraining your mind to process life as it is, rather than as you think it should be.",
        "Rest when you’re weary. Refresh and renew yourself, your body, your mind, your spirit.",
        "Calm mind brings inner strength and self-confidence.",
        "The greatest weapon against stress is our ability to choose one thought over another.",
        "Meditation is not about stopping thoughts, but recognizing that we are more than our thoughts and our feelings.",
        "Sleep is the golden chain that ties health and our bodies together.",
        "Sometimes the most productive thing you can do is relax.",
        "Worry less, smile more.",
        "Mental strength is like a muscle – the more you train it, the stronger it gets.",
        # Humorous and Fun
        "I’m on a seafood diet. I see food and I eat it… just kidding!",
        "My doctor told me to start my exercise program gradually. So today I drove past a gym.",
        "I’m not sweating, I’m sparkling.",
        "Of course I’m an organ donor. Who wouldn’t want this body?",
        "I’m not lazy, I’m on energy-saving mode.",
        "I run because I really like food.",
        "My fitness goal is to get down to what I told people I weigh.",
        "I’m into fitness… fitness whole pizza in my mouth.",
        "The only running I do is running late.",
        "I’m not going to the gym today. Record it as ‘rest’ instead of ‘lazy.'",
        "My favorite exercise is a cross between a lunge and a crunch… I call it lunch.",
        "I’m allergic to mornings.",
        "I work out because I know I would’ve made a hot dinosaur.",
        "I’m not saying I’m Wonder Woman, I’m just saying no one has ever seen me and Wonder Woman in the same room.",
        "Stressed spelled backward is desserts. Coincidence? I think not!",
        "I’m on a 30-day diet. So far I’ve lost 15 days.",
        "Exercise? I thought you said ‘extra fries’!",
        "Life is short. Smile while you still have teeth."
    ]
    
    # Simple rotation logic (e.g., based on day of the month or a random choice)
    current_tip = health_tips_list[datetime.now().day % len(health_tips_list)]
    
    return render_template('health_tips.html', current_tip=current_tip)

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Fetch all relevant data for the user
    medical_histories = user.medical_histories
    medicines = user.medicines
    habits = user.habits
    bmi_entries = user.bmi_entries
    exercise_logs = user.exercise_logs
    meal_plan_entries = user.meal_plan_entries
    emergency_contacts = user.emergency_contacts # Added for completeness in report generation

    return render_template('reports.html', 
                           medical_histories=medical_histories,
                           medicines=medicines,
                           habits=habits,
                           bmi_entries=bmi_entries,
                           exercise_logs=exercise_logs,
                           meal_plan_entries=meal_plan_entries,
                           emergency_contacts=emergency_contacts) # Pass to template

@app.route('/generate_report_pdf')
def generate_report_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)

    # Render a separate HTML template specifically for the PDF content
    # This template should be designed to look good when printed
    html_content = render_template('report_pdf_template.html',
                                   user=user,
                                   profile=user.profile, # Pass profile data
                                   medical_histories=user.medical_histories,
                                   medicines=user.medicines,
                                   habits=user.habits,
                                   bmi_entries=user.bmi_entries,
                                   emergency_contacts=user.emergency_contacts,
                                   exercise_logs=user.exercise_logs,
                                   meal_plan_entries=user.meal_plan_entries
                                   )
    
    # Generate PDF from HTML content
    # Ensure WeasyPrint is installed (pip install weasyprint)
    pdf = HTML(string=html_content).write_pdf()

    response = app.make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=health_report_{user.email.split("@")[0]}.pdf' # More user-friendly filename
    return response

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)

    if request.method == 'POST':
        # Change Password Logic
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if current_password or new_password or confirm_password: # Only proceed if any password field is touched
            if check_password_hash(user.password, current_password):
                if new_password and new_password == confirm_password:
                    user.password = generate_password_hash(new_password)
                    db.session.commit()
                    flash("Password updated successfully!", "success")
                elif not new_password:
                    flash("New password cannot be empty.", "error")
                else:
                    flash("New password and confirmation do not match.", "error")
            else:
                flash("Incorrect current password.", "error")
        
        # Theme setting (frontend implementation required for actual visual change)
        selected_theme = request.form.get('theme')
        if selected_theme:
            session['theme'] = selected_theme # Store in session for immediate use across pages
            # In a real app, you might also save this to user.profile.theme_preference in DB
            flash(f"Theme preference set to {selected_theme}. (Visual change requires frontend CSS/JS)", "info")

        return redirect(url_for('settings'))

    return render_template('settings.html', current_theme=session.get('theme', 'light'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all() # This creates tables for all defined models. IMPORTANT: If you have existing data and add new models, you might need to delete smarthealth.db and rerun, or use a migration tool like Flask-Migrate.
    app.run(debug=True)
