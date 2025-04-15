from flask import Flask, render_template, request, redirect, flash
from matcher.models import db, JobDescription, Resume
import os
from matcher.resume_utils import extract_text
from matcher.job_matcher import match_resume_to_job
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = "supersecret"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max upload
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///matcher.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)
ALLOWED_EXTENSIONS = {"pdf", "docx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    latest_job = JobDescription.query.order_by(
        JobDescription.created_at.desc()).first()
    return render_template("index.html", latest_job=latest_job)


@app.route("/history", methods=["GET"])
def history():
    search_query = request.args.get("search", "")
    if search_query:
        jobs = JobDescription.query.filter(
            JobDescription.content.like(f"%{search_query}%")
        ).all()
    else:
        jobs = JobDescription.query.order_by(
            JobDescription.created_at.desc()).all()

    resumes = Resume.query.all()  # You can apply filters here if needed

    return render_template("history.html", jobs=jobs, resumes=resumes)


@app.route("/upload_job", methods=["POST"])
def upload_job_description():
    job_text = request.form["job_description"]

    if not job_text.strip():
        flash("Job description cannot be empty.")
        return redirect("/")

    job_entry = JobDescription(content=job_text.strip())
    db.session.add(job_entry)
    db.session.commit()

    flash("Job description uploaded successfully!")
    return redirect("/")


@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    latest_job = JobDescription.query.order_by(
        JobDescription.created_at.desc()).first()

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
        filename = file.filename
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        try:
            resume_text = extract_text(save_path)
            similarity_score = match_resume_to_job(
                resume_text, latest_job.content)

            resume_entry = Resume(
                filename=filename,
                text=resume_text,
                similarity_score=similarity_score,
                job_id=latest_job.id,
            )
            db.session.add(resume_entry)
            db.session.commit()

            flash(f"Resume uploaded! Similarity Score: {
                  similarity_score:.2f}%")
            return redirect("/")

        except Exception as e:
            flash(f"Error reading file: {e}")
            return redirect("/")

    else:
        flash("Invalid file type. Only PDF and DOCX allowed.")
        return redirect("/")


@app.route("/delete_job/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    job = JobDescription.query.get(job_id)
    if job:
        db.session.delete(job)
        db.session.commit()
        flash("Job description deleted successfully!")
    else:
        flash("Job description not found.")
    return redirect("/history")


@app.route("/delete_resume/<int:resume_id>", methods=["POST"])
def delete_resume(resume_id):
    resume = Resume.query.get(resume_id)
    if resume:
        db.session.delete(resume)
        db.session.commit()
        flash("Resume deleted successfully!")
    else:
        flash("Resume not found.")
    return redirect("/")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)
