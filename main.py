# from flask import Flask, render_template, request, redirect, flash
# import os
# from matcher.resume_utils import extract_text  # <- added
#
# app = Flask(__name__)
# app.secret_key = "supersecret"  # Required for flash messages
# app.config["UPLOAD_FOLDER"] = "uploads"
# app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max upload
#
# # Allowed file extensions
# ALLOWED_EXTENSIONS = {"pdf", "docx"}
#
#
# def allowed_file(filename):
#     return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
#
#
# @app.route("/")
# def index():
#     return render_template("index.html")
#
#
# @app.route("/upload", methods=["POST"])
# def upload_resume():
#     if "resume" not in request.files:
#         flash("No file part")
#         return redirect("/")
#
#     file = request.files["resume"]
#
#     if file.filename == "":
#         flash("No selected file")
#         return redirect("/")
#
#     if file and allowed_file(file.filename):
#         save_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
#         file.save(save_path)
#
#         # 🔍 Parse the uploaded file
#         try:
#             resume_text = extract_text(save_path)
#             print(
#                 f"--- Resume Text ({file.filename}) ---\n{resume_text[:500]}...\n")
#         except Exception as e:
#             flash(f"Error reading file: {e}")
#             return redirect("/")
#
#         flash(f"Resume '{file.filename}' uploaded and parsed successfully.")
#         return redirect("/")
#     else:
#         flash("Invalid file type. Only PDF and DOCX allowed.")
#         return redirect("/")
#
#
# if __name__ == "__main__":
#     app.run(debug=True)

from flask import Flask, render_template, request, redirect, flash
import os
from matcher.resume_utils import extract_text
from matcher.job_matcher import get_embeddings  # Import the embedding function

app = Flask(__name__)
app.secret_key = "supersecret"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max upload

ALLOWED_EXTENSIONS = {"pdf", "docx"}

# Job description (hard-coded for now)
job_description = """
Role: Software Engineer
Skills:
- Python
- Machine Learning
- Data Structures & Algorithms
- Problem Solving
- SQL and Database Management

Responsibilities:
- Develop, test, and deploy software solutions.
- Collaborate with cross-functional teams to define system requirements.
- Write clean, efficient, and maintainable code.
"""


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html", job_description=job_description)


@app.route("/upload", methods=["POST"])
def upload_resume():
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

            # Get sentence embeddings for the resume
            resume_embeddings = get_embeddings(resume_text)

            # ======== Dummy Matching Logic (replace with your actual logic) ========
            # Let's say you have precomputed embeddings for existing resumes
            matched_resumes = [
                {"filename": "resume1.pdf", "score": 92.5},
                {"filename": "resume2.pdf", "score": 88.3},
                {"filename": file.filename, "score": 100.0},  # Self match
            ]

            # Render the results page with matched resumes
            return render_template("results.html", matched_resumes=matched_resumes)

        except Exception as e:
            flash(f"Error reading file: {e}")
            return redirect("/")

    else:
        flash("Invalid file type. Only PDF and DOCX allowed.")
        return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
