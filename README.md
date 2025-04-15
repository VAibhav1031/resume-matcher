# 💼 Resume Matcher

A smart web app that matches resumes against a job description and gives a compatibility score — helping recruiters save time and find the best fit faster.

## 🚀 Features

- 🔍 Match resumes using:
  - 🔤 Pasted job description
  - 📄 Uploaded job description file
- 📥 Upload multiple resumes at once (`.pdf`, `.docx`)
- 📊 Get instant match scores
- 📂 Download or delete uploaded resumes
- 🕓 View match history

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS, JavaScript, FontAwesome
- **Backend**: Python, Flask
- **Parsing**: `PyMuPDF`, `python-docx`
- **Similarity**: TF-IDF, Cosine Similarity via `scikit-learn`
- **Database**: SQLite with SQLAlchemy

## ⚙️ Setup Instructions

### Using UV Package Manager (Recommended)
[UV](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

1. **Clone the repo**
   ```bash
   git clone https://github.com/your-username/resume-matcher.git
   cd resume-matcher
   ```

2. **Install UV** (if not already installed)
   ```bash
   pip install uv
   ```

3. **Create a virtual environment and install dependencies**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync
   ```

4. **Run the app**
   ```bash
   flask run
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

### Using Traditional pip

1. **Clone the repo**
   ```bash
   git clone https://github.com/your-username/resume-matcher.git
   cd resume-matcher
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**
   ```bash
   flask run
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

## 📂 Folder Structure

```
resume-matcher/
├── instance/            # Database files
├── matcher/             # Core matching logic
│   ├── __init__.py
│   ├── job_matcher.py   # Matching algorithm
│   ├── models.py        # Database models
│   └── resume_utils.py  # PDF/DOCX parsing
├── migrations/          # Database migrations
├── static/              # Static assets
│   ├── script.js        # Frontend logic
│   ├── styles.css       # Styling
│   └── uploads/         # Uploaded files storage
├── templates/           # HTML templates
│   ├── history.html     # Match history page
│   ├── index.html       # Main app page
│   └── results.html     # Results display
├── main.py              # Flask application
├── pyproject.toml       # Project dependencies
└── README.md            # This file
```

## ✅ TODOs / Improvements

- Add login/auth for recruiters
- Dashboard for analytics and filtering
- Export top-matching resumes as reports
- Implement keyword highlighting in matched resumes
- Add machine learning models for better matching
- Integrate with job boards for automatic description import

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Created with ❤️ to simplify hiring workflows.
