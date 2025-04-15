from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class JobDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resumes = db.relationship(
        "Resume", backref="job", lazy=True, cascade="all, delete-orphan"
    )


class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text, nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)  # Overall score only
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    job_id = db.Column(db.Integer, db.ForeignKey("job_description.id"), nullable=False)

    # Optional: For future expansion (currently unused)
    # Can store section scores later if needed
    analysis_data = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"<Resume {self.filename} (Score: {self.similarity_score}%)>"
