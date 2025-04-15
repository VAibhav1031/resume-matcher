from flask import Flask, render_template, request, redirect, flash
from matcher.models import db, JobDescription, Resume
import os
from matcher.resume_utils import extract_text
from matcher.job_matcher import match_resume_to_job

app = Flask(__name__)
app.secret_key = "supersecret"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max upload
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///matcher.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

ALLOWED_EXTENSIONS = {"pdf", "docx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    latest_job = JobDescription.query.order_by(
        JobDescription.uploaded_at.desc()
    ).first()
    return render_template("index.html", latest_job=latest_job)


@app.route("/upload_job", methods=["POST"])
def upload_job_description():
    job_text = request.form["job_description"]

    if not job_text:
        flash("Job description cannot be empty.")
        return redirect("/")

    job_entry = JobDescription(text=job_text)
    db.session.add(job_entry)
    db.session.commit()

    flash("Job description uploaded successfully!")
    return redirect("/")


@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    latest_job = JobDescription.query.order_by(
        JobDescription.uploaded_at.desc()
    ).first()

    if not latest_job:
        flash("Please upload a job description first.")
        return redirect("/")

    if "resume" not in request.files:
        flash("No file part")
        return redirect("/")

    file = request.files["resume"]

    if file.filename == "":
        flash("No selected file")
        return redirect("/")

    if file and allowed_file(file.filename):
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(save_path)

        try:
            resume_text = extract_text(save_path)
            similarity_score = match_resume_to_job(resume_text, latest_job.text)

            resume_entry = Resume(
                filename=file.filename,
                text=resume_text,
                similarity_score=similarity_score,
            )
            db.session.add(resume_entry)
            db.session.commit()

            flash(
                f"Resume uploaded successfully! Similarity Score: {
                    similarity_score:.2f
                }%"
            )
            return redirect("/")

        except Exception as e:
            flash(f"Error reading file: {e}")
            return redirect("/")

    else:
        flash("Invalid file type. Only PDF and DOCX allowed.")
        return redirect("/")


# Ensure DB tables are created before first request


@app.before_first_request
def create_tables():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
