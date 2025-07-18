import streamlit as st
import os
import pandas as pd
from datetime import datetime
import tempfile
import uuid

from app import file_utils, resume_parser, matcher, storage, pdf_exporter, email_utils, voice_input

storage.init_db()

st.set_page_config(layout="wide", page_title="AI Resume Screening & Ranking Agent")
st.title("👨💼👩💼 AI Resume Screening & Ranking Agent")
st.markdown(
    "Automate your recruitment. Upload a job description, resumes, and let AI rank candidates by relevance."
)

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
            st.session_state.parsed_jd = resume_parser.parse_job_description(full_text)
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
                parsed = resume_parser.parse_resume(resume_text)
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

# --- UI Layout ---
col_jd, col_resumes = st.columns(2)

with col_jd:
    st.header("1. Job Description")
    method = st.radio(
        "Provide JD by:",
        ("Upload File", "Voice Input"),
        horizontal=True
    )
    if method == "Upload File":
        jd_file = st.file_uploader(
            "Upload JD (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            key="jd_uploader"
        )
        if jd_file and jd_file != st.session_state.get('last_jd_uploaded'):
            st.session_state.last_jd_uploaded = jd_file
            process_jd(jd_file.read(), jd_file.name)
    else:
        st.info("Press 'Record' and narrate the job description.")
        if st.button("Record JD"):
            with st.spinner("Listening..."):
                text = voice_input.get_jd_from_voice()
            if text:
                process_jd(text.encode("utf-8"), "Voice_Input_JD.txt")
            else:
                st.error("Voice input failed. Please try again.")

    if st.session_state.parsed_jd:
        st.subheader("JD Summary")
        col1, col2, col3 = st.columns(3)
        col1.write("**Required Skills:**")
        col1.write(", ".join(st.session_state.parsed_jd.get('required_skills', ['N/A'])))
        col2.write("**Experience:**")
        col2.write(f"{st.session_state.parsed_jd.get('experience_requirements', 'N/A')} years")
        col3.write("**Education:**")
        col3.write(", ".join(st.session_state.parsed_jd.get('education_requirements', ['N/A'])))
        st.markdown("---")

with col_resumes:
    st.header("2. Upload Resumes")
    resume_files = st.file_uploader(
        "Upload Resumes (PDF, DOCX, TXT)", 
        type=["pdf", "docx", "txt"], 
        accept_multiple_files=True,
        key="resume_uploader"
    )
    if resume_files:
        cur_names = {f.name for f in resume_files}
        prev_names = {f['filename'] for f in st.session_state.uploaded_resumes}
        # Only re-parse if new files uploaded
        if cur_names != prev_names or not st.session_state.parsed_resumes_data:
            process_resumes(resume_files)

# --- 3. Run & Display Results ---
st.header("3. Run Screening & View Results")
can_run = st.session_state.parsed_jd and st.session_state.parsed_resumes_data
col_run, _ = st.columns([2, 1])
if col_run.button("Run Screening & Rank Resumes", disabled=not can_run):
    with st.spinner("AI screening and ranking..."):
        st.session_state.ranked_results = matcher.rank_resumes(
            st.session_state.parsed_resumes_data,
            st.session_state.parsed_jd
        )
    st.success("Screening complete! See below for results.")
    # Save to DB
    title = st.session_state.current_job_title or "Untitled"
    session_id = storage.save_results(st.session_state.ranked_results, title)
    if session_id:
        st.info(f"Results saved to database for session ID: {session_id}")

if st.session_state.ranked_results:
    st.subheader("Ranked Candidates")
    results_df = pd.DataFrame(get_display_data(st.session_state.ranked_results))
    st.dataframe(results_df, use_container_width=True)

    st.subheader("4. Export & Share Results")
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

else:
    st.info("Upload a job description and resumes, then run screening to see ranked results.")

st.markdown("---")

# --- 5. Historical Results ---
st.header("5. Historical Screening")
if st.button("Refresh Historical Results"):
    hist = storage.fetch_results()
    if hist:
        hist_df = pd.DataFrame(hist)[['job_title', 'timestamp', 'filename', 'score']].rename(
            columns={
                'job_title': 'Job Title',
                'timestamp': 'Date',
                'filename': 'Resume Filename',
                'score': 'Score (%)'
            }
        )
        st.dataframe(hist_df, use_container_width=True)
    else:
        st.info("No historical results yet.")
