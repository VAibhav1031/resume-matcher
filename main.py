from flask import Flask, render_template, request, redirect, flash
import os
from matcher.resume_utils import extract_text
from matcher.job_matcher import match_resume_to_job  # correct usage!

app = Flask(__name__)
app.secret_key = "supersecret"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max upload

ALLOWED_EXTENSIONS = {"pdf", "docx"}

# Variable to store job description
job_description = None


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload_job", methods=["POST"])
def upload_job_description():
    global job_description
    job_description = request.form["job_description"]

    if not job_description:
        flash("Job description cannot be empty.")
        return redirect("/")

    flash("Job description uploaded successfully!")
    return redirect("/")


@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    global job_description

    if not job_description:
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
            # Extract text from the uploaded resume
            resume_text = extract_text(save_path)

            # Use proper match function
            similarity_score = match_resume_to_job(resume_text, job_description)

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


if __name__ == "__main__":
    app.run(debug=True)
