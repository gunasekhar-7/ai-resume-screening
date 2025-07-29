import streamlit as st
import os
import pandas as pd
from datetime import datetime
import tempfile
import uuid

from app import file_utils, resume_parser, matcher, storage, pdf_exporter, email_utils, voice_input


storage.init_db()

st.set_page_config(layout="wide", page_title="AI Resume Screening & Ranking Agent")
st.title("AI Resume Screening & Ranking Agent")
st.markdown(
    "Automate your recruitment. Upload a job description, resumes, and let AI rank candidates by relevance."
)


import spacy
from sentence_transformers import SentenceTransformer

@st.cache_resource
def load_nlp_models():
    # Use lightweight models for Cloud deployment
    nlp = spacy.load("en_core_web_sm")  # en_core_web_sm must be in requirements.txt
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return nlp, embedder

nlp, embedder = load_nlp_models()



# --- Session State Setup ---
for key, default in [
    ('parsed_jd', None),
    ('jd_filename', "Not Provided"),
    ('uploaded_resumes', []),
    ('parsed_resumes_data', []),
    ('ranked_results', []),
    ('current_job_title', ""),
    ('email_recipient', "")
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- Helper Functions ---
def process_jd(jd_content, jd_filename):
    st.session_state.jd_filename = jd_filename
    temp_jd_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(jd_filename)[1]) as tmp_file:
            tmp_file.write(jd_content)
            temp_jd_path = tmp_file.name

        full_text = file_utils.extract_text_from_file(temp_jd_path)
        if full_text and full_text.strip():
            st.session_state.parsed_jd = resume_parser.parse_job_description(full_text, nlp)
            st.success(f"Job Description '{jd_filename}' processed.")
            suggested_title = (
                st.session_state.parsed_jd.get('title')
                or jd_filename.replace(".txt", "").replace(".pdf", "")[:60]
            )
            st.session_state.current_job_title = st.text_input(
                "Confirm/Edit Job Title:",
                value=suggested_title,
                key="jd_title_input"
            )
        else:
            st.error(f"Could not extract text from '{jd_filename}'. Try another file.")
            st.session_state.parsed_jd = None
    except Exception as e:
        st.error(f"Error processing JD '{jd_filename}': {str(e)}")
        st.session_state.parsed_jd = None
    finally:
        if temp_jd_path and os.path.exists(temp_jd_path):
            os.remove(temp_jd_path)

def process_resumes(uploaded_files):
    st.session_state.parsed_resumes_data = []
    st.session_state.uploaded_resumes = []
    temp_dir = "temp_resumes"
    os.makedirs(temp_dir, exist_ok=True)
    for uploaded_file in uploaded_files:
        temp_path = ''
        try:
            ext = os.path.splitext(uploaded_file.name)[1]
            temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}{ext}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            resume_text = file_utils.extract_text_from_file(temp_path)
            if resume_text:
                parsed = resume_parser.parse_resume(resume_text, nlp)
                parsed['filename'] = uploaded_file.name
                st.session_state.parsed_resumes_data.append(parsed)
                st.session_state.uploaded_resumes.append({
                    'filename': uploaded_file.name,
                    'content': uploaded_file.getbuffer()
                })
                st.success(f"Processed resume: {uploaded_file.name}")
            else:
                st.warning(f"Could not extract text from: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
    # Clean up dir if empty
    if not os.listdir(temp_dir):
        os.rmdir(temp_dir)

def get_display_data(ranked):
    table = []
    for idx, res in enumerate(ranked, 1):
        data = res.get('parsed_data', {})
        skills = data.get('skills', [])
        edu = data.get('education', [])
        table.append({
            "Rank": idx,
            "Filename": res['filename'],
            "Score (%)": res['score'],
            "Name": data.get('contact_info', {}).get('name', 'N/A'),
            "Total Exp (Years)": data.get('total_experience_years', 'N/A'),
            "Key Skills": ", ".join(skills[:5]) + ("..." if len(skills) > 5 else ""),
            "Education": edu[0].get('degree', 'N/A') if edu else 'N/A'
        })
    return table

# ----- Step 1: Job Description -----
st.header("1. Provide Job Description")
jd_method = st.radio(
    "Choose how to provide the Job Description:",
    ("Upload File", "Voice Input"),
    horizontal=True
)
if jd_method == "Upload File":
    jd_file = st.file_uploader(
        "Upload JD (PDF, DOCX, or TXT)",
        type=["pdf", "docx", "txt"],
        key="jd_uploader"
    )
    if jd_file and jd_file != st.session_state.get('last_jd_uploaded'):
        st.session_state.last_jd_uploaded = jd_file
        process_jd(jd_file.read(), jd_file.name)
else:
    st.info("Press 'Record' and narrate the job description, then wait for processing.")
    if st.button("Record Job Description"):
        with st.spinner("Listening..."):
            text = voice_input.get_jd_from_voice()
        if text:
            process_jd(text.encode("utf-8"), "Voice_Input_JD.txt")
        else:
            st.error("Voice input failed. Please try again.")

# Display JD summary if available
if st.session_state.parsed_jd:
    st.subheader("Job Description Summary")
    col1, col2, col3 = st.columns(3)
    col1.write("**Required Skills:**")
    col1.write(", ".join(st.session_state.parsed_jd.get('required_skills', ['N/A'])))
    col2.write("**Experience:**")
    col2.write(f"{st.session_state.parsed_jd.get('experience_requirements', 'N/A')} years")
    col3.write("**Education:**")
    col3.write(", ".join(st.session_state.parsed_jd.get('education_requirements', ['N/A'])))
    st.markdown("---")
else:
    st.info("Please provide a job description to proceed.")

# ----- Step 2: Upload Resumes -----
st.header("2. Upload Candidate Resumes")
resume_files = st.file_uploader(
    "Upload one or more resumes (PDF, DOCX, or TXT)",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
    key="resume_uploader"
)
if resume_files and st.session_state.parsed_jd:
    cur_names = {f.name for f in resume_files}
    prev_names = {f['filename'] for f in st.session_state.uploaded_resumes}
    # Only re-parse if new files uploaded
    if cur_names != prev_names or not st.session_state.parsed_resumes_data:
        process_resumes(resume_files)
elif not st.session_state.parsed_jd:
    st.info("Please provide a job description before uploading resumes.")

# ----- Step 3: Run Screening -----
st.header("3. Run Screening & View Results")
can_run = st.session_state.parsed_jd and st.session_state.parsed_resumes_data
if st.button("Run Screening & Rank Resumes", disabled=not can_run):
    with st.spinner("AI screening and ranking..."):
        st.session_state.ranked_results = matcher.rank_resumes(
            st.session_state.parsed_resumes_data,
            st.session_state.parsed_jd,
	    embedder=embedder
        )
    st.success("Screening complete! See below for results.")
    title = st.session_state.current_job_title or "Untitled"
    session_id = storage.save_results(st.session_state.ranked_results, title)
    if session_id:
        st.info(f"Results saved to database for session ID: {session_id}")

# Results table if available
if st.session_state.ranked_results:
    st.subheader("Ranked Candidates Table")
    results_df = pd.DataFrame(get_display_data(st.session_state.ranked_results))
    st.dataframe(results_df, use_container_width=True)
else:
    st.info("After uploading resumes and JD, click 'Run Screening' to see results.")

# ----- Step 4: Export & Share Results -----
if st.session_state.ranked_results:
    st.header("4. Export & Share Results")
    col_export, col_email = st.columns(2)

    with col_export:
        st.download_button(
            "Download Results as CSV",
            data=results_df.to_csv(index=False).encode('utf-8'),
            file_name=f"ranked_{st.session_state.current_job_title or 'screening'}_{datetime.now():%Y%m%d_%H%M%S}.csv",
            mime="text/csv"
        )
        if st.button("Generate PDF Report"):
            with st.spinner("Generating PDF..."):
                pdf_path = f"Report_{uuid.uuid4()}.pdf"
                path = pdf_exporter.export_results_to_pdf(
                    st.session_state.ranked_results,
                    st.session_state.parsed_jd,
                    pdf_path,
                    st.session_state.current_job_title
                )
                if path and os.path.exists(path):
                    with open(path, "rb") as pdf_file:
                        st.download_button(
                            "Download PDF Report",
                            data=pdf_file.read(),
                            file_name=os.path.basename(path),
                            mime="application/pdf"
                        )
                    os.remove(path)
                else:
                    st.error("Failed to generate PDF.")

    with col_email:
        recipient = st.text_input(
            "Recipient email for report:",
            st.session_state.email_recipient
        )
        if recipient:
            st.session_state.email_recipient = recipient
        subject = f"Resume Screening for {st.session_state.current_job_title or 'Role'}"
        body = f"""
        Please find attached the AI screening report for {st.session_state.current_job_title or 'the specified role'}.
        Generated by AI Resume Screening & Ranking Agent.
        """
        if st.button("Email PDF Report"):
            with st.spinner("Preparing and sending email..."):
                tmp_pdf = f"Email_Report_{uuid.uuid4()}.pdf"
                pdf_path = pdf_exporter.export_results_to_pdf(
                    st.session_state.ranked_results,
                    st.session_state.parsed_jd,
                    tmp_pdf,
                    st.session_state.current_job_title
                )
                if pdf_path and os.path.exists(pdf_path):
                    sent = email_utils.send_email_report(
                        to_email=recipient,
                        subject=subject,
                        body=body,
                        attachment_path=pdf_path
                    )
                    if sent:
                        st.success(f"Emailed report to {recipient}")
                    else:
                        st.error("Failed to send email.")
                    os.remove(pdf_path)
                else:
                    st.error("Could not generate report for email.")

import datetime

# --- 5. Historical Results ---
st.header("5. Historical Screening")

# Fetch a sample Session ID for description
hist_any = storage.fetch_results(limit=1)
if hist_any and 'session_id' in hist_any[0]:
    sample_session_id = hist_any[0]['session_id']
    st.info(
        f"**Session ID** is a unique identifier for each candidate screening and ranking event you run. "
        f"For example, Session ID `{sample_session_id}` in the table below identifies one particular screening session. "
        "Use the Session ID to reference, review, or delete results from a specific screening session."
    )
else:
    st.info(
        "**Session ID** is a unique identifier for each candidate screening and ranking event you run. "
        "For example, Session ID `1234` in the table below identifies one particular screening session. "
        "Use the Session ID to reference, review, or delete results from a specific screening session."
    )

def refresh_history():
    st.session_state["history_data"] = storage.fetch_results()

# Initialize state (safely, and do **not** overwrite datetime/date)
if "history_data" not in st.session_state:
    st.session_state["history_data"] = storage.fetch_results()
if "del_start_date" not in st.session_state:
    st.session_state["del_start_date"] = datetime.date.today()
if "del_end_date" not in st.session_state:
    st.session_state["del_end_date"] = datetime.date.today()
if "del_session_id" not in st.session_state:
    st.session_state["del_session_id"] = None

if st.button("Refresh Historical Results"):
    refresh_history()

hist = st.session_state["history_data"]

if hist and len(hist) > 0:
    hist_df = pd.DataFrame(hist)[['job_title', 'timestamp', 'filename', 'score', 'session_id']].rename(
        columns={
            'job_title': 'Job Title',
            'timestamp': 'Date',
            'filename': 'Resume Filename',
            'score': 'Score (%)',
            'session_id': 'Session ID'
        }
    )
    st.dataframe(hist_df, use_container_width=True)   # SHOW Session ID in the UI

    # --- Date Range Deletion ---
    st.markdown("### Delete Screening History by Date Range")

    # Use session_state to keep values persistent
    start_date = st.date_input(
        "Start Date",
        value=st.session_state["del_start_date"],
        key="del_start_date"
    )
    if start_date != st.session_state["del_start_date"]:
        st.session_state["del_start_date"] = start_date

    end_date = st.date_input(
        "End Date",
        value=st.session_state["del_end_date"],
        key="del_end_date"
    )
    if end_date != st.session_state["del_end_date"]:
        st.session_state["del_end_date"] = end_date

    if st.button("Delete Records in Selected Date Range"):
        deleted_count = storage.delete_results_by_date_range(
            str(st.session_state["del_start_date"]),
            str(st.session_state["del_end_date"])
        )
        if deleted_count > 0:
            st.success(f"Deleted {deleted_count} session(s) from {st.session_state['del_start_date']} to {st.session_state['del_end_date']}. Click refresh to update.")
        else:
            st.info("No sessions found in that range.")

    # --- Single Session Deletion ---
    st.markdown("### Delete by Session ID")
    session_ids = hist_df['Session ID'].unique().tolist()
    selected_session = (
        st.session_state["del_session_id"]
        if st.session_state["del_session_id"] in session_ids
        else (session_ids[0] if session_ids else None)
    )
    session_to_delete = st.selectbox(
        "Select Session ID to delete",
        session_ids,
        index=session_ids.index(selected_session) if selected_session in session_ids else 0,
        key="del_session_id"
    )
    if session_to_delete != st.session_state["del_session_id"]:
        st.session_state["del_session_id"] = session_to_delete

    if st.button("Delete This Session"):
        success = storage.delete_result_by_session_id(int(st.session_state["del_session_id"]))
        if success:
            st.success(f"Session {st.session_state['del_session_id']} deleted. Click refresh to update.")
        else:
            st.error("Failed to delete session. Try again.")
else:
    st.info("No historical results yet.")
