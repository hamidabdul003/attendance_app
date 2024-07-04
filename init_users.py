from app import app
from models import db, User

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='walikelas').first():
        walikelas = User(username='walikelas', role='walikelas')
        walikelas.set_password('password')
        db.session.add(walikelas)
    if not User.query.filter_by(username='sekretaris').first():
        sekretaris = User(username='sekretaris', role='sekretaris')
        sekretaris.set_password('password')
        db.session.add(sekretaris)
    if not User.query.filter_by(username='orangtua').first():
        orangtua = User(username='orangtua', role='orangtua')
        orangtua.set_password('password')
        db.session.add(orangtua)
    db.session.commit()
