from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_principal import Principal, Permission, RoleNeed, identity_loaded, UserNeed, Identity, AnonymousIdentity, identity_changed
from datetime import datetime, date
from models import db, Student, Attendance, User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, ValidationError
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy.orm import Session
import pdfkit
import calendar
from werkzeug.exceptions import HTTPException
from flask_restful import Api, Resource, reqparse
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
api = Api(app)

# Konfigurasi Logging
if not app.debug:
    handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder untuk menyimpan file yang diupload
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
principals = Principal(app)

walikelas_permission = Permission(RoleNeed('walikelas'))
sekretaris_permission = Permission(RoleNeed('sekretaris'))

@login_manager.user_loader
def load_user(user_id):
    with Session(db.engine) as session:
        return session.get(User, int(user_id))

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))
        if current_user.role == 'walikelas':
            identity.provides.add(RoleNeed('walikelas'))
        elif current_user.role == 'sekretaris':
            identity.provides.add(RoleNeed('sekretaris'))

with app.app_context():
    db.create_all()

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if not user:
            raise ValidationError('Invalid username')

    def validate_password(self, password):
        user = User.query.filter_by(username=self.username.data).first()
        if user and not user.check_password(password.data):
            raise ValidationError('Invalid password')

class StudentForm(FlaskForm):
    nama = StringField('Nama', validators=[DataRequired(), Length(min=2, max=50)])
    kelas = StringField('Kelas', validators=[DataRequired(), Length(min=1, max=20)])
    submit = SubmitField('Submit')

    def validate_nama(self, nama):
        student = Student.query.filter_by(nama=nama.data).first()
        if student:
            raise ValidationError('Nama siswa sudah ada. Silakan gunakan nama yang berbeda.')

@app.route('/')
def home():
    app.logger.info('Home page accessed')
    if current_user.is_authenticated:
        return redirect(url_for('total_rekap'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            identity_changed.send(app, identity=Identity(user.id))
            app.logger.info(f'User {user.username} logged in')
            return redirect(url_for('total_rekap'))
        else:
            flash('Invalid username or password', 'danger')
            app.logger.warning(f'Failed login attempt for username: {form.username.data}')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    app.logger.info(f'User {current_user.username} logged out')
    logout_user()
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)
    identity_changed.send(app, identity=AnonymousIdentity())
    return redirect(url_for('login'))

@app.route('/index', methods=['GET', 'POST'])
@login_required
@walikelas_permission.union(sekretaris_permission).require(http_exception=403)
def index():
    students = Student.query.all()
    today = date.today()
    if request.method == 'POST':
        # Hapus data absensi sebelumnya
        Attendance.query.filter_by(tanggal=today).delete()
        db.session.commit()
        app.logger.info(f'User {current_user.username} cleared attendance for today')

        for student in students:
            status = request.form.get(f'status-{student.id}', 'H')
            attendance = Attendance(
                student_id=student.id,
                tanggal=today,
                status=status
            )
            db.session.add(attendance)
        db.session.commit()
        app.logger.info(f'User {current_user.username} updated attendance for today')
        return redirect(url_for('rekap'))
    return render_template('index.html', students=students, today=today)

@app.route('/rekap', methods=['GET', 'POST'])
def rekap():
    date_value = request.args.get('date', datetime.now().date(), type=lambda x: datetime.strptime(x, '%Y-%m-%d').date())
    students = Student.query.all()
    attendances = Attendance.query.filter_by(tanggal=date_value).all()

    if request.method == 'POST' and current_user.is_authenticated and (current_user.role == 'walikelas' or current_user.role == 'sekretaris'):
        # Hapus data absensi pada tanggal yang ditentukan
        Attendance.query.filter_by(tanggal=date_value).delete()
        db.session.commit()
        app.logger.info(f'User {current_user.username} cleared attendance for {date_value}')

        for student in students:
            status = request.form.get(f'status-{student.id}', 'H')
            attendance = Attendance(
                student_id=student.id,
                tanggal=date_value,
                status=status
            )
            db.session.add(attendance)
        db.session.commit()
        app.logger.info(f'User {current_user.username} updated attendance for {date_value}')
        return redirect(url_for('rekap', date=date_value))

    if not attendances:
        flash(f'Tidak ada data kehadiran untuk tanggal {date_value}. Hari libur.')
        totals = {}
    else:
        totals = {student.id: student.total_attendance_by_month(date_value.year, date_value.month) for student in students}

    return render_template('rekap.html', students=students, totals=totals, date=date_value)

@app.route('/total_rekap', methods=['GET'])
def total_rekap():
    students = Student.query.all()
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    month_name = calendar.month_name[month]
    totals = {student.id: student.total_attendance_by_month(year, month) for student in students}
    return render_template('total_rekap.html', students=students, totals=totals, year=year, month=month, month_name=month_name, calendar=calendar)

@app.route('/rekap/pdf', methods=['GET'])
def rekap_pdf():
    students = Student.query.all()
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    totals = {student.id: student.total_attendance_by_month(year, month) for student in students}
    rendered = render_template('total_rekap_pdf.html', students=students, totals=totals, year=year, month=month, calendar=calendar)

    path_to_wkhtmltopdf = '/usr/local/bin/wkhtmltopdf'  # Sesuaikan dengan lokasi wkhtmltopdf di sistem Anda
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    pdf = pdfkit.from_string(rendered, False, configuration=config)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=rekap_absensi_{year}_{month}.pdf'
    return response

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
@walikelas_permission.union(sekretaris_permission).require(http_exception=403)
def update(id):
    attendance = Attendance.query.get_or_404(id)
    if request.method == 'POST':
        status = request.form['status']
        attendance.status = status
        db.session.commit()
        app.logger.info(f'User {current_user.username} updated attendance for student {attendance.student_id} on {attendance.tanggal}')
        return redirect(url_for('rekap'))
    return render_template('update.html', attendance=attendance)

@app.route('/delete_all', methods=['POST'])
@login_required
@walikelas_permission.require(http_exception=403)
def delete_all():
    Attendance.query.delete()
    db.session.commit()
    app.logger.info(f'User {current_user.username} deleted all attendance records')
    return redirect(url_for('rekap'))

@app.route('/students', methods=['GET'])
@login_required
@walikelas_permission.union(sekretaris_permission).require(http_exception=403)
def students():
    page = request.args.get('page', 1, type=int)
    show_all = request.args.get('show_all', 'false') == 'true'
    search_query = request.args.get('search', '')

    if search_query:
        students_query = Student.query.filter(Student.nama.ilike(f'%{search_query}%'))
    else:
        students_query = Student.query

    if show_all:
        students = students_query.all()
        app.logger.info(f'User {current_user.username} viewed all students')
        return render_template('students.html', students=students, show_all=show_all, search_query=search_query)
    else:
        students = students_query.paginate(page=page, per_page=10)
        app.logger.info(f'User {current_user.username} viewed students page {page}')
        return render_template('students.html', students=students.items, pagination=students, search_query=search_query, show_all=show_all)

def get_total_attendance(student_id, year, month):
    return Attendance.query.filter_by(student_id=student_id).filter(db.extract('year', Attendance.tanggal) == year, db.extract('month', Attendance.tanggal) == month).count()

@app.context_processor
def utility_processor():
    def total_attendance(student_id, year=datetime.now().year, month=datetime.now().month):
        return get_total_attendance(student_id, year, month)
    return dict(total_attendance=total_attendance)

@app.errorhandler(404)
def page_not_found(e):
    app.logger.warning(f"Page not found: {request.url}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()  # Rollback jika terjadi kesalahan dalam transaksi basis data
    app.logger.error(f"Server error: {str(error)}")
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    # Now you're handling non-HTTP exceptions only
    app.logger.error(f"Unhandled Exception: {str(e)}")
    return render_template("500.html"), 500

@app.route('/student/add', methods=['GET', 'POST'])
@login_required
@walikelas_permission.require(http_exception=403)
def add_student():
    if request.method == 'POST':
        nama = request.form['nama']
        kelas = request.form['kelas']
        student = Student(nama=nama, kelas=kelas)
        db.session.add(student)
        db.session.commit()
        app.logger.info(f'User {current_user.username} added student {student.nama}')
        return redirect(url_for('students'))
    return render_template('add_student.html')

@app.route('/student/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@walikelas_permission.require(http_exception=403)
def edit_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        student.nama = request.form['nama']
        student.kelas = request.form['kelas']
        db.session.commit()
        app.logger.info(f'User {current_user.username} edited student {student.nama}')
        return redirect(url_for('students'))
    return render_template('edit_student.html', student=student)

@app.route('/student/delete/<int:id>', methods=['POST'])
@login_required
@walikelas_permission.require(http_exception=403)
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    app.logger.info(f'User {current_user.username} deleted student {student.nama}')
    return redirect(url_for('students'))

# Endpoint API untuk mengambil data siswa
class StudentAPI(Resource):
    def get(self, student_id=None):
        if student_id:
            student = Student.query.get_or_404(student_id)
            return jsonify({
                'id': student.id,
                'nama': student.nama,
                'kelas': student.kelas,
                'total_kehadiran': student.total_attendance_by_month(datetime.now().year, datetime.now().month)
            })
        else:
            students = Student.query.all()
            return jsonify([{
                'id': student.id,
                'nama': student.nama,
                'kelas': student.kelas,
                'total_kehadiran': student.total_attendance_by_month(datetime.now().year, datetime.now().month)
            } for student in students])

api.add_resource(StudentAPI, '/api/students', '/api/students/<int:student_id>')

# Endpoint untuk meng-upload file Excel
@app.route('/upload', methods=['GET', 'POST'])
@login_required
@walikelas_permission.require(http_exception=403)
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            import_students_from_excel(filepath)
            flash('File successfully uploaded and data imported', 'success')
            app.logger.info(f'User {current_user.username} uploaded and imported data from {filename}')
            return redirect(url_for('students'))
    return render_template('upload.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx'}

def import_students_from_excel(filepath):
    df = pd.read_excel(filepath)
    for _, row in df.iterrows():
        student = Student(nama=row['Nama'], kelas=row['Kelas'])
        db.session.add(student)
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
