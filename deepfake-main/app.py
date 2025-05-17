import streamlit as st
import streamlit_survey as ss
import streamlit_scrollable_textbox as stx
import time
import json
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Set the page config
st.set_page_config(
    page_title="Audio Persuasiveness",
    page_icon="🔍",
    initial_sidebar_state="collapsed"
)

if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

def collapse_sidebar():
    st.markdown(
        """
        <style>
            [data-testid="collapsedControl"] { display: none; }
            [data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

if st.session_state.sidebar_state == 'collapsed':
    collapse_sidebar()

# Survey setup
survey = ss.StreamlitSurvey("Survey Audio Persuasiveness")
st.title("Welcome, Audio Explorer! 🎧‍")
st.write("We've got an audio snippet for Kamala Harris or Donald Trump. Your mission? Listen to the audio and rate it!")
st.markdown("**How to Play**: Listen to each audio clip and share your thoughts.")
st.write("Enjoy the journey! This challenge lasts 5–10 minutes.")
st.divider()

# Consent
st.subheader("Participant information and consent form")
st.write("We are committed to safeguarding your privacy. Please review the study terms.")
if st.button("Review general information and consent form"):
    content = """GENERAL INFORMATION:
    You are invited to participate in a research study aimed at developing tools for detecting and labelling audio clips. Your participation will involve playing a game where you rate audio segments and assess their persuasiveness.

    ...
    By proceeding with this study, you acknowledge that you have read and understood this consent form and agree to participate voluntarily.
    """
    stx.scrollableTextbox(content, height=150)

st.subheader("Consent to participate")
st.write("I have been informed about the study by the study team...")
consent1 = survey.checkbox("I hereby consent to participate in the study.")
st.write("The processing and use of personal data...")
consent2 = survey.checkbox("I hereby consent to the described processing of my personal data.")
consent3 = survey.checkbox("I confirm that I am at least 18 years old.")

# DB credentials from secrets
db_host = st.secrets["db_host"]
db_user = st.secrets["db_user"]
db_password = st.secrets["db_password"]
db_name = st.secrets["db_name"]
db_port = st.secrets["db_port"]

def get_sqlalchemy_engine():
    engine = create_engine(
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=20,
        max_overflow=10
    )
    return engine

def insert_participant_and_get_id(pool):
    try:
        with pool.connect() as connection:
            insert_query = text(
                "INSERT INTO participants (age_group, gender, education, occupation, country_of_residence, "
                "nationality, race, native_tongue, languages_spoken, political_party, political_inclination, "
                "listening_habits, tech_savy, ai_experience, media_consumption) "
                "VALUES (NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)"
            )
            connection.execute(insert_query)
            last_id_result = connection.execute(text("SELECT LAST_INSERT_ID()"))
            return last_id_result.scalar()
    except SQLAlchemyError as e:
        st.error(f"Database insertion failed: {e}")
        raise

def insert_prolific_id(pool, participant_id, prolific_id):
    try:
        with pool.connect() as db_conn:
            insert_query = text("INSERT INTO prolific_ids (participant_id, prolific_id) VALUES (:participant_id, :prolific_id)")
            db_conn.execute(insert_query, {
                "participant_id": participant_id,
                "prolific_id": prolific_id
            })
    except SQLAlchemyError as e:
        st.error(f"Failed to insert Prolific ID: {e}")
        raise

# Main logic
if not all([consent1, consent2, consent3]):
    st.write("Please give your consent by ticking all three boxes.")
elif all([consent1, consent2, consent3]):
    prolific_id = st.text_input("Enter your unique Prolific ID:", max_chars=50, key="prolific_id")
    if st.button("Submit ID"):
        if prolific_id:
            pool = get_sqlalchemy_engine()
            last_inserted_id = insert_participant_and_get_id(pool)
            insert_prolific_id(pool, last_inserted_id, prolific_id)
            st.session_state['participant_id'] = last_inserted_id
        else:
            st.write("Please enter your Prolific ID to continue.")

if 'participant_id' in st.session_state:
    st.write("Let's check the case!")
    st.switch_page("pages/Rate_responses.py")
