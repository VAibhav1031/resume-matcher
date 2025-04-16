"""
Database Models for Resume Matcher Application

Recent Changes (Authentication Update):
1. Added User Model:
   - Stores user credentials (email + hashed password)
   - Relationships with JobDescription and Resume
   - Password hashing methods for security
   - Why: To enable user authentication and data ownership

2. Modified JobDescription:
   - Added user_id foreign key
   - Why: To associate jobs with specific users
   - Cascade delete maintains referential integrity

3. Modified Resume:
   - Added user_id foreign key
   - Why: To associate resumes with both jobs AND users
   - Ensures users only access their own resumes

4. Enhanced Relationships:
   - All models now cascade deletes properly
   - Why: When a user is deleted, all their data is automatically cleaned up
   - Maintains database consistency

Security Notes:
- Passwords are never stored plaintext (always hashed)
- User authentication required for all data operations
- Each user only sees their own jobs/resumes
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    jobs = db.relationship(
        "JobDescription", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    resumes = db.relationship(
        "Resume", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class JobDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    analysis_data = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"<Resume {self.filename} (Score: {self.similarity_score}%)>"
