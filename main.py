from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash,
    url_for,
    send_from_directory,
    session,
)
from werkzeug.utils import secure_filename
import traceback
from datetime import datetime, timedelta
import os
import numpy as np
from json import JSONEncoder
from matcher.models import db, JobDescription, Resume
from matcher.resume_utils import extract_text
from matcher.job_matcher import match_resume_to_job
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

# ======================
# CUSTOM JSON ENCODER
# ======================


class NumpyEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.generic):
            return obj.item()
        return super().default(obj)


app.json_encoder = NumpyEncoder

# ======================
# CONFIGURATION
# ======================
app.secret_key = "supersecretkey"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)
app.config["SESSION_TYPE"] = "filesystem"  # Requires Flask-Session

# File upload config
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///matcher.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
csrf = CSRFProtect(app)
db.init_app(app)
migrate = Migrate(app, db)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

# ======================
# HELPER FUNCTIONS
# ======================


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_numpy_types(data):
    """Convert numpy types to native Python types"""
    if isinstance(data, np.generic):
        return data.item()
    if isinstance(data, dict):
        return {k: convert_numpy_types(v) for k, v in data.items()}
    if isinstance(data, list):
        return [convert_numpy_types(item) for item in data]
    return data


# ======================
# ROUTES (PROPER ORDER)
# ======================


@app.route("/")
def index():
    latest_job = JobDescription.query.order_by(JobDescription.created_at.desc()).first()
    resumes = (
        Resume.query.order_by(Resume.uploaded_at.desc()).all() if latest_job else []
    )
    return render_template("index.html", latest_job=latest_job, resumes=resumes)


@app.route("/history")
def history():
    search_query = request.args.get("search", "")
    jobs = JobDescription.query
    if search_query:
        jobs = jobs.filter(JobDescription.content.ilike(f"%{search_query}%"))
    jobs = jobs.order_by(JobDescription.created_at.desc()).all()
    resumes = Resume.query.all()
    return render_template("history.html", jobs=jobs, resumes=resumes)


@app.route("/upload", methods=["POST"])
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
        job = JobDescription(content=job_text)
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
def results(resume_id):
    """Display detailed matching results for a specific resume"""
    try:
        # 1. Get the resume from database
        resume = Resume.query.get_or_404(resume_id)

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
def delete_job(job_id):
    job = JobDescription.query.get(job_id)
    if job:
        Resume.query.filter_by(job_id=job.id).delete()
        db.session.delete(job)
        db.session.commit()
        flash("Job and associated resumes deleted successfully", "success")
    else:
        flash("Job not found", "error")
    return redirect(url_for("history"))  # Fixed reference


@app.route("/delete_resume/<int:resume_id>", methods=["POST"])
def delete_resume(resume_id):
    resume = Resume.query.get(resume_id)
    if resume:
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
    app.run(debug=True)
