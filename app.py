import os
import sys

# 1. Enforce UTF-8 for Windows PowerShell and console output
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import streamlit as st
import json
from google import genai

# ---------------------------------------------------------
# 2. Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="RISE Institutions - AI Student FAQ Assistant",
    page_icon="🎓",
    layout="wide"
)

# ---------------------------------------------------------
# 3. Knowledge Base Loader
# ---------------------------------------------------------
@st.cache_data
def load_faq_knowledge_base():
    """Reads and caches institutional FAQ knowledge from faqs.json."""
    if not os.path.exists("faqs.json"):
        return []
    try:
        with open("faqs.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading faqs.json: {e}")
        return []

faq_data = load_faq_knowledge_base()
faq_context = json.dumps(faq_data, indent=2, ensure_ascii=True)

# ---------------------------------------------------------
# 4. Sidebar Configuration & Persistent Key Storage
# ---------------------------------------------------------
if "api_key" not in st.session_state:
    st.session_state.api_key = "AQ.Ab8RN6L3Wt50Va0zv4CltoTQrIzxt10t8aJ_1t2A3Dn9NCBPUw"

with st.sidebar:
    st.title("🎓 Campus Desk")
    st.caption("RISE Krishna Sai Group of Institutions, Ongole")
    st.markdown("---")
    
    user_key = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="AQ.Ab8...",
        help="Preloaded with your verified API key."
    )
    if user_key:
        st.session_state.api_key = user_key.strip()

    st.markdown("---")
    st.subheader("Key Institutional Topics")
    st.markdown("""
    - **Affiliation:** Autonomous & JNTUK, NAAC A+
    - **EAPCET Codes:** RPRA / RGON
    - **Minimum Attendance:** 75% Aggregate
    - **Hostel & Transport:** On-campus & Prakasam routes
    """)
    
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------
# 5. Chat History Initialization
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "**Welcome to the RISE Krishna Sai AI Assistant!**\n\n"
                "I can answer your queries about B.Tech/PG courses, counseling codes, "
                "attendance regulations, placements, bus routes, library access, or campus life. "
                "What would you like to know?"
            )
        }
    ]

# ---------------------------------------------------------
# 6. Header & Quick-Access Buttons
# ---------------------------------------------------------
st.title("🎓 RISE Krishna Sai AI Student Assistant")
st.markdown("Ask anything about campus guidelines, academic regulations, or facilities.")

quick_cols = st.columns(4)
chip_prompt = None

if quick_cols[0].button("📋 Attendance Rule", use_container_width=True):
    chip_prompt = "What is the minimum attendance requirement for semester exams?"
if quick_cols[1].button("🏢 Top Recruiters", use_container_width=True):
    chip_prompt = "Which placement companies visit RISE and what are the packages?"
if quick_cols[2].button("🚌 Bus Routes", use_container_width=True):
    chip_prompt = "Does the college provide bus transport to Singarayakonda and Ongole?"
if quick_cols[3].button("🏛️ Counseling Codes", use_container_width=True):
    chip_prompt = "What are the EAPCET counseling codes for RISE colleges?"

# ---------------------------------------------------------
# 7. Render Existing Chat Messages
# ---------------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------
# 8. User Interaction & Flexible Response Generation
# ---------------------------------------------------------
user_query = st.chat_input("Type your question here (e.g., 'What are the library hours?')")
active_prompt = chip_prompt if chip_prompt else user_query

if active_prompt:
    # 1. Display and save student prompt
    st.session_state.messages.append({"role": "user", "content": active_prompt})
    with st.chat_message("user"):
        st.markdown(active_prompt)

    clean_key = st.session_state.api_key.strip()
    if not clean_key:
        warning_reply = "⚠️ Please enter your **Gemini API Key** in the sidebar to activate the assistant."
        with st.chat_message("assistant"):
            st.warning(warning_reply)
        st.session_state.messages.append({"role": "assistant", "content": warning_reply})
    else:
        # 2. Flexible instruction: checks FAQ first, answers helpfully if missing
        full_prompt = f"""
You are the helpful, intelligent AI Academic Assistant for RISE Krishna Sai Group of Institutions (Valluru, Ongole, Andhra Pradesh).

OPERATING INSTRUCTIONS:
1. Always prioritize the OFFICIAL FAQ DATASET below for specific institution facts (departments, placement recruiters, EAPCET codes, JNTUK regulations, bus routes).
2. If a specific student query (e.g., exact daily library hours, dress code, fee payment deadlines, or general study tips) is NOT explicitly mentioned in the dataset:
   - DO NOT refuse to answer.
   - Provide a helpful, practical response based on standard engineering college conventions in Andhra Pradesh (e.g., central libraries are typically open 8:00 AM to 6:00 PM on working days and extended during exams).
   - Add a brief friendly note advising the student to verify exact operational timings with the college office or central library circulation desk.
3. Structure your response clearly using bullet points and bold highlights.

OFFICIAL FAQ DATASET:
{faq_context}

STUDENT QUESTION:
{active_prompt}
"""
        with st.chat_message("assistant"):
            with st.spinner("Finding answer..."):
                try:
                    # Initialize client with active key
                    client = genai.Client(api_key=clean_key)
                    
                    # Direct generation using the verified fast model
                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=full_prompt
                    )
                    
                    if response and response.text:
                        bot_reply = response.text
                        st.markdown(bot_reply)
                        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                    else:
                        empty_warn = "⚠️ No response returned. Please rephrase your question."
                        st.warning(empty_warn)
                        st.session_state.messages.append({"role": "assistant", "content": empty_warn})

                except Exception as e:
                    error_msg = f"❌ **API Error:** `{type(e).__name__}`: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})