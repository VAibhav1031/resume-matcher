from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class JobDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Adding cascade="all, delete-orphan" to handle deletion of associated resumes
    resumes = db.relationship(
        "Resume", backref="job", lazy=True, cascade="all, delete-orphan"
    )


class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text, nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    job_id = db.Column(db.Integer, db.ForeignKey(
        "job_description.id"), nullable=False)
