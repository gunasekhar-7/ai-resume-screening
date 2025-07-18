🤖 AI Resume Screening & Ranking Agent
An intelligent HR-tech solution for automating resume screening, ranking, and reporting with advanced NLP and a recruiter-friendly user interface.



🚀 Features
Batch Resume Upload: Screen multiple resumes (PDF/DOCX/TXT) in a single run.

Flexible Job Description Input: Upload a job description file or use voice input via microphone.

Automated Extraction: Parses skills, education, experience, and contact info from resumes and job descriptions.

AI-powered Matching: Uses transformer-based embeddings and smart scoring to rank candidates by relevance.

Reporting: Exports results to CSV or generates a detailed, styled PDF report summarizing ranked candidates.

Email Integration: Email PDF reports directly from the app.

History: Stores screening sessions in SQLite for future reference.

Modern UI: Simple, guided Streamlit interface with real-time feedback.




📁 Project Structure
text
ai-resume-screening/
├── app/
│   ├── resume_parser.py      # NLP-based info extraction
│   ├── matcher.py           # AI scoring & ranking logic
│   ├── file_utils.py        # Text extraction from files
│   ├── pdf_exporter.py      # Export ranking report to PDF
│   ├── email_utils.py       # Email PDF reports
│   ├── storage.py           # Save session/results to SQLite
│   ├── voice_input.py       # Voice input for job descriptions
│   └── ui.py                # Streamlit interface
├── data/
│   ├── resumes/             # Sample resumes
│   └── job_description.txt  # Sample job description
├── requirements.txt
├── main.py                  # Entry point (optional)
└── README.md





⚙️ Tech Stack

Category	 | Tool/Library
-----------------|------------------------------------------------
NLP		 | spaCy (en_core_web_lg), sentence-transformers
File Handling	 | PyMuPDF, docx2txt
ML Models	 | MiniLM-L6-v2 (semantic embedding)
Logic		 | Smart weights, fuzzy matching, section parsing
Frontend	 | Streamlit
Reporting	 | fpdf
Email		 | yagmail, dotenv
Voice Input	 | SpeechRecognition, sounddevice, soundfile
Storage	sqlite3  | (builtin)



💻 Getting Started
🔧 Local Setup
bash
git clone https://github.com/gunasekhar-7/ai-resume-screening.git
cd ai-resume-agent2

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_lg


🚦 Usage Guide
Run the app:

bash
streamlit run app/ui.py
Step 1: Upload a job description (file or record via voice).

Step 2: Upload resume files (batch upload supported).

Step 3: Click "Run Screening" to analyze and rank candidates.

Export/Share: Download results (CSV/PDF) or email a report.

Historical: Review past screening sessions from the database.



🛠️ Customization
Extend Skills & Weights:
Update skill sets and matching logic in resume_parser.py and matcher.py for new job types or industries.

UI Theme & Branding:
Edit ui.py for custom colors, branding, or workflow tweaks.

Integrations:
Build REST APIs, integrate with recruiter workflows, or add more export formats.




🔒 Security & Privacy
Use only app-specific passwords for email sending.

All screening data is stored locally in SQLite; results can be deleted after use.

Protect your .env file; never check it into public git repositories.



🧪 Testing
Upload example resumes and job descriptions (see /data/).

Verify ranking, extraction fields, PDF/CSV export, and email reporting.

Try edge cases (missing skills, empty files) for validation.



🙏 Acknowledgments
Thanks to the open-source AI/NLP community, especially spaCy, SentenceTransformers, Streamlit, and supporting libraries for enabling modern HR technology solutions.