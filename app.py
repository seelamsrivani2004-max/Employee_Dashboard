from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# -------------------- DATABASE SETUP --------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

DB_PATH = os.path.join(INSTANCE_DIR, "employee.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# -------------------- MODELS --------------------
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="Employee")
    department = db.Column(db.String(50))
    position = db.Column(db.String(50))
    status = db.Column(db.String(10), default="Active")


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    date = db.Column(db.String(20))
    login_time = db.Column(db.String(20))
    logout_time = db.Column(db.String(20))

    employee = db.relationship('Employee', backref=db.backref('attendance_logs', lazy=True))


class AppUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    app_name = db.Column(db.String(120))
    duration = db.Column(db.Float)
    date = db.Column(db.String(20))

    employee = db.relationship('Employee', backref=db.backref('app_usages', lazy=True))


# -------------------- INITIAL DATA --------------------
with app.app_context():
    db.create_all()

    if not Employee.query.filter_by(name="admin").first():
        admin = Employee(
            name="admin",
            email="admin@company.com",
            employee_id="ADMIN001",
            password=generate_password_hash("admin123"),
            role="Admin",
            department="Management",
            position="Administrator"
        )
        db.session.add(admin)
        db.session.commit()

    # Add sample employees if not already present
    sample_employees = [
        ("Alice", "Emp123", "HR", "HR Manager"),
        ("Bob", "Emp456", "IT", "Developer"),
        ("Charlie", "Emp789", "Sales", "Sales Executive"),
        ("David", "Emp012", "Marketing", "Marketing Manager"),
        ("Eve", "Emp345", "Finance", "Accountant"),
        ("Frank", "Emp678", "HR", "HR Assistant"),
        ("Grace", "Emp901", "IT", "System Administrator"),
        ("Hank", "Emp234", "Sales", "Sales Associate"),

        ("Ivy", "Emp567", "Marketing", "Marketing Coordinator"),
        ("Jack", "Emp890", "Finance", "Financial Analyst"),

        ("Kate", "Emp123", "HR", "HR Manager"),
        ("Leo", "Emp456", "IT", "Developer"),
        ("Mia", "Emp789", "Sales", "Sales Executive"),
        ("Nate", "Emp012", "Marketing", "Marketing Manager"),
        ("Olivia", "Emp345", "Finance", "Accountant"),

        ("Pete", "Emp678", "HR", "HR Assistant"),
        ("Ajay","Ajay123","Manager","Manager"),
        ("Srivani","Srivani123","IT","Java DEveloper"),
        ("Srilekha","Srilekha123","IT","Python Developer"),
        ("Ashmitha","Ashmitha123","IT","Tester"),
        ("Pooja","Pooja123","IT","Frontend Developer"),
        ("Deeven","Deeven123","IT","Data Analyst"),
        ("Akash","Akash123","IT","Manager")

    ]

    for name, pwd, dept, pos in sample_employees:
        if not Employee.query.filter_by(name=name).first():
            emp = Employee(
                name=name,
                email=f"{name.lower()}@company.com",
                employee_id=f"EMP{random.randint(1000, 9999)}",
                password=generate_password_hash(pwd),
                department=dept,
                position=pos,
                role="Employee"
            )
            db.session.add(emp)
    db.session.commit()

    # Add sample attendance and app usage if not already present
    if not Attendance.query.first():
        employees = Employee.query.filter(Employee.role != "Admin").all()
        for emp in employees:
            for i in range(1, 4):
                att = Attendance(
                    employee_id=emp.id,
                    date=f"2025-10-0{i}",
                    login_time=f"09:0{i}:00",
                    logout_time=f"17:0{i}:00"
                )
                db.session.add(att)

                apps = ["Word", "Excel", "Chrome", "Slack"]
                for app_name in apps:
                    usage = AppUsage(
                        employee_id=emp.id,
                        app_name=app_name,
                        duration=random.randint(20, 120),
                        date=f"2025-10-0{i}"
                    )
                    db.session.add(usage)
        db.session.commit()


# -------------------- ROUTES --------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['username']  # This could be name, email, or employee_id
        password = request.form['password']
        
        # Check for user by name, email, or employee_id
        user = Employee.query.filter((Employee.name == identifier) | 
                                     (Employee.email == identifier) | 
                                     (Employee.employee_id == identifier)).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash("✅ Logged in successfully!", "success")

            # Record login time
            today = datetime.now().strftime("%Y-%m-%d")
            time_now = datetime.now().strftime("%H:%M:%S")
            att = Attendance(employee_id=user.id, date=today, login_time=time_now, logout_time=None)
            db.session.add(att)

            # --- Inject Duplicate/Random App Usage Data ---
            apps = ["Word", "Excel", "Chrome", "Slack", "Teams", "VS Code"]
            # Add 2-3 random apps usage for the logged in user
            for app_name in random.sample(apps, random.randint(2, 4)):
                usage = AppUsage(
                    employee_id=user.id,
                    app_name=app_name,
                    duration=random.randint(15, 90),
                    date=today
                )
                db.session.add(usage)
            
            db.session.commit()

            if user.role == "Admin":
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash("❌ Invalid credentials!", "danger")
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        employee_id = request.form['employee_id']
        job_title = request.form['job_title']
        password = request.form['password']

        if Employee.query.filter_by(name=full_name).first() or Employee.query.filter_by(email=email).first():
            flash("❌ User already exists!", "danger")
            return redirect(url_for('signup'))

        new_user = Employee(
            name=full_name,
            email=email,
            employee_id=employee_id,
            position=job_title,
            password=generate_password_hash(password),
            role="Employee"
        )
        db.session.add(new_user)
        db.session.commit()
        flash("✅ Signup successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/logout')
def logout():
    if 'user_id' in session:
        user_id = session['user_id']
        today = datetime.now().strftime("%Y-%m-%d")
        last_att = Attendance.query.filter_by(employee_id=user_id, date=today).order_by(Attendance.id.desc()).first()
        if last_att and not last_att.logout_time:
            last_att.logout_time = datetime.now().strftime("%H:%M:%S")
            db.session.commit()

    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = Employee.query.get(session['user_id'])
    attendance = Attendance.query.filter_by(employee_id=user.id).all()
    usage = AppUsage.query.filter_by(employee_id=user.id).all()

    # Chart Data for individual user
    app_names = list({u.app_name for u in usage})
    app_durations = [sum(u.duration for u in usage if u.app_name == app) for app in app_names]

    return render_template('dashboard.html', user=user, attendance=attendance, usage=usage, app_names=app_names, app_durations=app_durations)


@app.route('/admin')
def admin_dashboard():
    if session.get('role') != "Admin":
        flash("❌ Access denied!", "danger")
        return redirect(url_for('login'))

    employees = Employee.query.filter(Employee.role != "Admin").all()
    usage_data = AppUsage.query.all()
    attendance_data = Attendance.query.all()

    # Chart Data
    app_names = list({u.app_name for u in usage_data})
    app_durations = [sum(u.duration for u in usage_data if u.app_name == app) for app in app_names]

    return render_template(
        'admin_dashboard.html',
        employees=employees,
        usage_data=usage_data,
        attendance=attendance_data,
        app_names=app_names,
        app_durations=app_durations
    )


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = Employee.query.get(session['user_id'])
    attendance = Attendance.query.filter_by(employee_id=user.id).all()
    usage = AppUsage.query.filter_by(employee_id=user.id).all()
    return render_template('profile.html', user=user, attendance=attendance, usage=usage)


# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=True)
