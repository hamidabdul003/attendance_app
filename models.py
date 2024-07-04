from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100))
    kelas = db.Column(db.String(10))
    attendances = db.relationship('Attendance', backref='student', lazy=True)

    def total_attendance_by_month(self, year, month):
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        hadir = Attendance.query.filter_by(student_id=self.id, status='H').filter(Attendance.tanggal >= start_date).filter(Attendance.tanggal < end_date).count()
        alfa = Attendance.query.filter_by(student_id=self.id, status='A').filter(Attendance.tanggal >= start_date).filter(Attendance.tanggal < end_date).count()
        izin = Attendance.query.filter_by(student_id=self.id, status='I').filter(Attendance.tanggal >= start_date).filter(Attendance.tanggal < end_date).count()
        sakit = Attendance.query.filter_by(student_id=self.id, status='S').filter(Attendance.tanggal >= start_date).filter(Attendance.tanggal < end_date).count()
        return hadir, alfa, izin, sakit

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(1), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
    
    def has_role(self, role):
        return self.role == role
