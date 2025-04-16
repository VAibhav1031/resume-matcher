from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash,
    url_for,
    send_from_directory,
    session,
    abort,
)
from werkzeug.utils import secure_filename
import traceback
from datetime import datetime, timedelta
import os
import numpy as np
from json import JSONEncoder
from matcher.models import db, JobDescription, Resume, User
from matcher.resume_utils import extract_text
from matcher.job_matcher import match_resume_to_job
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# ======================
# CONFIGURATION
# ======================
app.secret_key = os.environ.get("SECRET_KEY") or "dev-secret-" + os.urandom(16).hex()
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///matcher.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Initialize extensions
csrf = CSRFProtect(app)
db.init_app(app)
migrate = Migrate(app, db)


class NumpyEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.generic):
            return obj.item()
        return super().default(obj)


app.json_encoder = NumpyEncoder

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

# ======================
# HELPER FUNCTIONS
# ======================


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_numpy_types(data):
    if isinstance(data, np.generic):
        return data.item()
    if isinstance(data, dict):
        return {k: convert_numpy_types(v) for k, v in data.items()}
    if isinstance(data, list):
        return [convert_numpy_types(item) for item in data]
    return data


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None


# ======================
# AUTHENTICATION ROUTES
# ======================


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_email"] = user.email
            flash("Login successful!", "success")
            next_page = request.args.get("next", url_for("index"))
            return redirect(next_page)
        flash("Invalid email or password", "error")
    return render_template("auth/login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must be at least 8 characters", "error")
            return redirect(url_for("register"))

        try:
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except IntegrityError:
            db.session.rollback()
            flash("Email already registered", "error")
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "error")
            app.logger.error(f"Registration error: {str(e)}")

    return render_template("auth/register.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        # Always show the same message regardless of whether email exists
        flash(
            "If an account exists with this email, you'll receive a password reset link shortly.",
            "info",
        )
        return redirect(url_for("login"))

    return render_template("auth/forgot_password.html")


# ======================
# PROTECTED ROUTES
# ======================


@app.route("/")
@login_required
def index():
    user = get_current_user()
    latest_job = (
        JobDescription.query.filter_by(user_id=user.id)
        .order_by(JobDescription.created_at.desc())
        .first()
    )
    resumes = (
        Resume.query.filter_by(user_id=user.id)
        .order_by(Resume.uploaded_at.desc())
        .all()
        if latest_job
        else []
    )
    return render_template("index.html", latest_job=latest_job, resumes=resumes)


@app.route("/history")
@login_required
def history():
    search_query = request.args.get("search", "")
    jobs = JobDescription.query
    if search_query:
        jobs = jobs.filter(JobDescription.content.ilike(f"%{search_query}%"))
    jobs = jobs.order_by(JobDescription.created_at.desc()).all()
    resumes = Resume.query.all()
    return render_template("history.html", jobs=jobs, resumes=resumes)


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    try:
        # Process job description
        input_type = request.form.get("input-type")
        job_text = ""

        if input_type == "text":
            job_text = request.form.get("job_description", "").strip()
            if not job_text:
                flash("Job description cannot be empty", "error")
                return redirect(url_for("index"))
        else:
            file = request.files.get("job_file")
            if not file or file.filename == "":
                flash("No valid job file uploaded", "error")
                return redirect(url_for("index"))

            if not allowed_file(file.filename):
                flash("Invalid file type for job description", "error")
                return redirect(url_for("index"))

            try:
                job_text = extract_text(file)
            except Exception as e:
                flash(f"Error reading job description: {str(e)}", "error")
                return redirect(url_for("index"))

        # Save job to database
        job = JobDescription(content=job_text, user_id=session["user_id"])
        db.session.add(job)
        db.session.flush()

        # Process resumes
        files = request.files.getlist("resume")
        valid_files = [f for f in files if f and allowed_file(f.filename)]
        processed_resumes = []

        if not valid_files:
            db.session.rollback()
            flash("No valid resume files uploaded", "error")
            return redirect(url_for("index"))

        for file in valid_files:
            try:
                # Save file
                orig_filename = secure_filename(file.filename)
                timestamp = datetime.now().timestamp()
                filename = f"{timestamp}_{orig_filename}"
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(save_path)

                # Process content
                resume_text = extract_text(save_path)
                raw_result = match_resume_to_job(resume_text, job_text)
                result = convert_numpy_types(raw_result)

                # Save to database
                resume = Resume(
                    filename=filename,
                    text=resume_text,
                    similarity_score=result["overall_score"],
                    job_id=job.id,
                    uploaded_at=datetime.now(),
                    user_id=session["user_id"],
                )
                db.session.add(resume)
                db.session.flush()
                processed_resumes.append(resume.id)

                # Store in session
                session[f"resume_result_{resume.id}"] = result

            except Exception as e:
                db.session.rollback()
                app.logger.error(
                    f"Error processing {file.filename}: {str(e)}\n{
                        traceback.format_exc()
                    }"
                )
                flash(f"Failed to process {file.filename}", "error")
                continue

        db.session.commit()

        # SMART REDIRECT LOGIC
        if len(processed_resumes) == 1:
            flash("Resume processed successfully!", "success")
            return redirect(url_for("results", resume_id=processed_resumes[0]))
        else:
            flash(
                f"{
                    len(processed_resumes)
                } resumes processed! Select one to view results",
                "success",
            )
            return redirect(url_for("index"))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Upload error: {str(e)}\n{traceback.format_exc()}")
        flash("An unexpected error occurred", "error")
        return redirect(url_for("index"))


@app.route("/results/<int:resume_id>")
@login_required
def results(resume_id):
    """Display detailed matching results for a specific resume"""
    try:
        # 1. Get the resume from database
        resume = Resume.query.get_or_404(resume_id)

        # Verify ownership
        if resume.user_id != session["user_id"]:
            flash("You don't have permission to view this resume", "error")
            return redirect(url_for("index"))

        # 2. Try getting pre-computed results from session
        result = session.get(f"resume_result_{resume_id}")

        # 3. If not in session (page reload), recompute
        if not result:
            job = JobDescription.query.get(resume.job_id)
            raw_result = match_resume_to_job(resume.text, job.content)

            # Convert numpy types to native Python types
            result = {
                "overall_score": float(raw_result["overall_score"]),
                "section_scores": {
                    k: float(v) for k, v in raw_result["section_scores"].items()
                },
                "matched_keywords": raw_result["matched_keywords"],
                "visualization": raw_result["visualization"],
            }

        # 4. Render the template with results
        return render_template("results.html", result=result)

    except Exception as e:
        flash("Failed to load results", "error")
        app.logger.error(f"Results error: {str(e)}\n{traceback.format_exc()}")
        return redirect(url_for("index"))


@app.route("/delete_job/<int:job_id>", methods=["POST"])
@login_required
def delete_job(job_id):
    job = JobDescription.query.get(job_id)
    if job:
        if job.user_id != session["user_id"]:
            flash("You don't have permission to delete this job", "error")
            return redirect(url_for("history"))

        Resume.query.filter_by(job_id=job.id).delete()
        db.session.delete(job)
        db.session.commit()
        flash("Job and associated resumes deleted successfully", "success")
    else:
        flash("Job not found", "error")
    return redirect(url_for("history"))


@app.route("/delete_resume/<int:resume_id>", methods=["POST"])
@login_required
def delete_resume(resume_id):
    resume = Resume.query.get(resume_id)
    if resume:
        if resume.user_id != session["user_id"]:
            flash("You don't have permission to delete this resume", "error")
            return redirect(url_for("index"))

        try:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], resume.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(resume)
            db.session.commit()
            flash("Resume deleted successfully", "success")
        except Exception as e:
            flash(f"Error deleting resume: {str(e)}", "error")
    else:
        flash("Resume not found", "error")
    return redirect(url_for("index"))


@app.route("/download/<filename>")
@login_required
def download_resume(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"], filename, as_attachment=True
    )


# ======================
# APPLICATION STARTUP
# ======================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Create initial admin user if none exists
        if not User.query.filter_by(email="admin@example.com").first():
            admin = User(email="admin@example.com")
            admin.set_password("Admin@123")
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
