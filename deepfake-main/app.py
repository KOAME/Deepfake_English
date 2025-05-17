import streamlit as st
import streamlit_survey as ss
import streamlit_scrollable_textbox as stx
import time

import json
import pandas as pd
from sqlalchemy import create_engine, text

import pymysql
import sqlalchemy
import os
from sshtunnel import SSHTunnelForwarder
from fabric import Connection
from sqlalchemy.exc import SQLAlchemyError

# Set the page config at the top of the file
st.set_page_config(
    page_title="Audio Persuasiveness",
    page_icon="🔍",
    initial_sidebar_state="collapsed"  # Collapsed sidebar by default
)

# Initialize session state for sidebar state if not already set
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'


# Function to collapse the sidebar
def collapse_sidebar():
    st.markdown(
        """
        <style>
            [data-testid="collapsedControl"] {
                display: none;
            }
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# Apply the sidebar collapse dynamically based on session state
if st.session_state.sidebar_state == 'collapsed':
    collapse_sidebar()

##start survey
survey = ss.StreamlitSurvey("Survey Audio Persuasiveness")

st.title("Welcome, Audio Explorer! 🎧‍")

text1 = "We've got an audio snippet for Kamala Harris or Donald Trump, Your mission? listen to the audio and rate it!"
st.write(text1)

text2 = "**How to Play**: Listen to each audio clip and share your thoughts."
st.markdown(text2)

text3 = "Enjoy the journey! This challenge lasts 5-10 minutes."
st.write(text3)

st.divider()

st.subheader("Participant information and consent form")
st.write("We are committed to safeguarding your privacy. Please review the study terms.")
if st.button("Review general information and consent form"):
    # st.switch_page("pages/Study_terms.py")

    content = """GENERAL INFORMATION:
    You are invited to participate in a research study aimed at developing tools for detecting and labelling audio clips. Your participation will involve playing a game where you rate audio segments and assess their persuasiveness.

    RISKS AND BENEFITS:
    - Risks: There are no significant risks associated with participating in this study.
    - Benefits: Your participation will contribute to scientific knowledge and the development of tools to detect and mitigate the impact of manipulated audio in various contexts.

    PROCEDURE:
    You will participate in a game where you listen to various audio clips and provide ratings on their persuasiveness and authenticity. The game is designed to be engaging and will take approximately 10 minutes to complete.

    CONFIDENTIALITY:
    Your responses will be kept confidential and anonymised. All data will be securely stored, and individual responses will not be identifiable in any reports or publications resulting from this study.

    VOLUNTARY PARTICIPATION:
    Participation is voluntary. You have the right to refuse or withdraw from the study at any time without penalty.

    DATA PROTECTION:
    All collected data will be anonymised and stored securely in compliance with GDPR regulations. Personal identifiers will be removed, and only aggregated data will be used for analysis and reporting.

    CONTACT INFORMATION:
    If you have any questions or concerns about this study, please contact **orestis.p@tum.de**.

    By proceeding with this study, you acknowledge that you have read and understood this consent form and agree to participate voluntarily.
    """
    stx.scrollableTextbox(content, height=150)

## include consent questions plus information about contact
st.subheader("Consent to participate")
st.write(
    "I have been informed about the study by the study team. I have received and read the written information and consent form for the study mentioned above. I have been thoroughly informed about the purpose and procedure of the study, the chances and risks of participation, and my rights and responsibilities. My consent to participate in the study is voluntary. I have the right to withdraw my consent at any time without giving reasons, and without any disadvantages to myself arising from this.")
consent1 = survey.checkbox("I hereby consent to participate in the study.")
st.write(
    "The processing and use of personal data for the study mentioned above will be carried out exclusively as described in the study information. The collected and processed personal data include, in particular, ethnic origin.")
consent2 = survey.checkbox("I hereby consent to the described processing of my personal data.")
consent3 = survey.checkbox("I confirm that I am at least 18 years old.")

#######################################################################################################

# # SSH and Database credentials
ssh_host = st.secrets["ssh_host"]
ssh_port = st.secrets["ssh_port"]
ssh_user = st.secrets["ssh_user"]
ssh_password = st.secrets["ssh_password"]

db_host = st.secrets["db_host"]
db_user = st.secrets["db_user"]
db_password = st.secrets["db_password"]
db_name = st.secrets["db_name"]
db_port = st.secrets["db_port"]


### Set up SSH connection and port forwarding
### Set up SSH tunnel with keep-alive
def start_ssh_tunnel():
    try:
        tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(db_host, db_port),
            set_keepalive=30  # Send keep-alive packets every 60 seconds to keep connection alive
        )
        tunnel.start()
        return tunnel
    except Exception as e:
        st.error(f"SSH tunnel connection failed: {e}")
        raise


# Establish Database connection with retry logic and optimized timeouts
def get_connection(tunnel, retries=3, delay=5):
    for attempt in range(retries):
        try:
            conn = pymysql.connect(
                host='127.0.0.1',
                user=db_user,
                password=db_password,
                database=db_name,
                port=tunnel.local_bind_port,
                connect_timeout=40600,  # Increased
                read_timeout=10600,  # Increased
                write_timeout=10600,  # Increased
                max_allowed_packet=128 * 1024 * 1024  # 128MB
            )
            return conn
        except pymysql.err.OperationalError as e:
            st.error(f"Connection attempt {attempt + 1} failed: {e}")
            if "MySQL server has gone away" in str(e):
                # Specific handling for the lost connection error
                st.error("MySQL server has gone away. Trying to reconnect...")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                st.error("Failed to connect to the database after multiple retries.")
                raise

    # SQLAlchemy connection pool with pre-ping and recycling for better connection management


def get_sqlalchemy_engine(tunnel):
    pool = create_engine(
        "mysql+pymysql://",
        creator=lambda: get_connection(tunnel),
        pool_pre_ping=True,  # Ensure connection is alive before executing a query
        pool_recycle=600,  # Recycle connections every 1 hour to prevent disconnection
        pool_size=4000,  # Set pool size to handle multiple connections
        max_overflow=3000  # Allow 10 extra simultaneous connections if needed
    )
    return pool


# Database insertions
def insert_participant_and_get_id(pool):
    try:
        with pool.connect() as connection:
            insert_query = text(
                "INSERT INTO participants (age_group, gender, education, occupation, country_of_residence, "
                "nationality, race, native_tongue, languages_spoken, political_party, political_inclination, "
                "listening_habits, tech_savy, ai_experience, media_consumption) VALUES (NULL, NULL, NULL, NULL, NULL, "
                "NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)")
            result = connection.execute(insert_query)
            # connection.commit()
            last_id_query = text("SELECT LAST_INSERT_ID()")
            last_id_result = connection.execute(last_id_query)
            last_id = last_id_result.scalar()
            return last_id
    except SQLAlchemyError as e:
        st.error(f"Database insertion failed: {e}")
        raise


def insert_prolific_id(pool, participant_id, prolific_id):

    try:
        insert_query = text(
            """INSERT INTO prolific_ids (participant_id, prolific_id) VALUES (:participant_id, :prolific_id)""")

        parameters = {
            "participant_id": participant_id,
            "prolific_id": prolific_id
        }

        with pool.connect() as db_conn:
            db_conn.execute(insert_query, parameters)
            # db_conn.commit()

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
            tunnel = start_ssh_tunnel()
            pool = get_sqlalchemy_engine(tunnel)

            last_inserted_id = insert_participant_and_get_id(pool)
            insert_prolific_id(pool, last_inserted_id, prolific_id)
            st.session_state['participant_id'] = last_inserted_id
            tunnel.stop()  # Stop tunnel when done
        else:
            st.write("Please enter your Prolific ID to continue.")

if 'participant_id' in st.session_state:
    st.write("Let's check the case!")
    st.switch_page("pages/Rate_responses.py")'
