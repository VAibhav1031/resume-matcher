from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class JobDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=True)
    text = db.Column(db.Text, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.now())


class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    text = db.Column(db.Text, nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.now())
