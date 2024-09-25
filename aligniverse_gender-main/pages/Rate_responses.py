import streamlit as st
import streamlit_survey as ss
import time

import json
import pandas as pd
from sqlalchemy import create_engine, text
import pymysql
import sqlalchemy
import os
import pymysql
from sshtunnel import SSHTunnelForwarder
from fabric import Connection

from sqlalchemy.exc import SQLAlchemyError


st.set_page_config(
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
    
ssh_host = st.secrets["ssh_host"]
ssh_port = st.secrets["ssh_port"]
ssh_user = st.secrets["ssh_user"]
ssh_password = st.secrets["ssh_password"]

db_host = st.secrets["db_host"]
db_user = st.secrets["db_user"]
db_password = st.secrets["db_password"]
db_name = st.secrets["db_name"]
db_port = st.secrets["db_port"]

# Set up SSH connection and tunnel
def start_ssh_tunnel():
    try:
        tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(db_host, db_port),
            set_keepalive=60  # Keep SSH connection alive
        )
        tunnel.start()
        return tunnel
    except Exception as e:
        st.error(f"SSH tunnel connection failed: {e}")
        raise

# Establish a database connection with retry logic and pooling
def get_connection(tunnel, retries=5, delay=20):
    attempt = 0
    while attempt < retries:
        try:
            conn = pymysql.connect(
                host='127.0.0.1',
                user=db_user,
                password=db_password,
                database=db_name,
                port=tunnel.local_bind_port,
                connect_timeout=9600,  # Increased 
                read_timeout=8600,     # Increased
                write_timeout=8600,    # Increased 
                max_allowed_packet=128 * 1024 * 1024  # 128MB
            )
            return conn
        except pymysql.err.OperationalError as e:
            st.error(f"Connection attempt {attempt + 1} failed: {e}")
            attempt += 1
            if attempt < retries:
                st.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                st.error("Failed to connect to the database after multiple retries. Please check your network!")
                raise

# Create a SQLAlchemy engine with pre-ping and connection pooling
def get_sqlalchemy_engine(tunnel):
    pool = create_engine(
        "mysql+pymysql://",
        creator=lambda: get_connection(tunnel),
        pool_pre_ping=True,   # Ensure connections are alive before query
        pool_recycle=3600,    # Recycle connections every 1 hour
        pool_size=10,          # Number of connections in the pool
        max_overflow=10       # Allow overflow for multiple requests
    )
    return pool

# SSH Tunnel Initialization
tunnel = start_ssh_tunnel()
pool = get_sqlalchemy_engine(tunnel)


# Insert a rating into the database
def insert_rating(participant_id, question_id, prompt_id, gender_focused, rating_stereotypical_bias, rating_toxicity, rating_emotional_awareness, rating_sensitivity, rating_helpfulness):
    insert_query = """
    INSERT INTO df_ratings (
        participant_id,
        question_id,
        prompt_id,
        gender_focused,
        rating_stereotypical_bias,
        rating_toxicity,
        rating_emotional_awareness,
        rating_sensitivity,
        rating_helpfulness
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with pool.connect() as db_conn:
            db_conn.execute(insert_query, (
                participant_id, question_id, prompt_id, gender_focused, rating_stereotypical_bias,
                rating_toxicity, rating_emotional_awareness, rating_sensitivity, rating_helpfulness
            ))
    except SQLAlchemyError as e:
        st.error(f"Database insertion failed: {e}")
        raise


st.title("Rate pre-generated responses")
st.write("Our mission is to create alignment datasets that incorporate your opinion on how LLMs should handle controversial topics. In the following section, you will see different prompts and their corresponding answers. Your task is to rate the answers based on the displayed criteria. We generated the answers using a Large Language Model (LLM) that has not been aligned yet, allowing us to study its responses to our questions. Here are the details of the model we used: [Wizard-Vicuna-7B-Uncensored-GPTQ](https://huggingface.co/TheBloke/Wizard-Vicuna-7B-Uncensored-GPTQ)")

##start survey
survey = ss.StreamlitSurvey("rate_survey")

#q_discrimination = survey.selectbox("Choose the type of discrimination you want to focus on", options=["Gender identity"], id = "disc_type_rate")
q_discrimination = "Gender identity"
type_info = "gender identity"
stereotypical_bias_info = "Stereotypical bias regarding {}: refers to beliefs about a person’s abilities and interests based on their {}. [Source](https://arxiv.org/pdf/2308.05374)".format(type_info, type_info)

# Insert new participant and get ID
def insert_participant_and_get_id():
    try:
        with pool.connect() as connection:
            insert_query = text("INSERT INTO df_participants (age, gender_identity, country_of_residence, ancestry, ethnicity) VALUES (NULL, NULL, NULL, NULL, NULL)")
            connection.execute(insert_query)
            last_id_query = text("SELECT LAST_INSERT_ID()")
            last_id_result = connection.execute(last_id_query)
            return last_id_result.scalar()
    except SQLAlchemyError as e:
        st.error(f"Failed to insert participant: {e}")
        raise

# Mark a prompt as rated
def mark_as_rated(prompt_id):
    try:
        with pool.connect() as db_conn:
            query = text("UPDATE df_prompts SET rated = 1 WHERE prompt_id = :prompt_id")
            db_conn.execute(query, {'prompt_id': prompt_id})
    except SQLAlchemyError as e:
        st.error(f"Failed to mark prompt as rated: {e}")
        raise

# Save data to the database
def save_to_db():
    if 'participant_id' not in st.session_state:
        participant_id = insert_participant_and_get_id()
        st.session_state['participant_id'] = participant_id
    else:
        participant_id = st.session_state['participant_id']

    res_q0 = st.session_state.key_q0
    res_q1 = st.session_state.key_q1
    res_q2 = st.session_state.key_q2
    res_q3 = st.session_state.key_q3
    res_q4 = st.session_state.key_q4
    res_q5 = st.session_state.key_q5

    if all([res_q0, res_q1, res_q2, res_q3, res_q4, res_q5]):
        st.session_state['count'] += 1

    insert_rating(
        participant_id,
        sample_row[1],  # question_id
        sample_row[0],  # prompt_id
        res_q0,
        res_q1,
        res_q2,
        res_q3,
        res_q4,
        res_q5
    )
    mark_as_rated(sample_row[0])

# Main survey form
if 'count' not in st.session_state:
    st.session_state['count'] = 0
    
# Fetch the sample row from the database once when the page is loaded or refreshed
if 'sample_row' not in st.session_state:
    with pool.connect() as db_conn:
        query = text("SELECT * FROM df_prompts WHERE rated = 0 ORDER BY RAND() LIMIT 1")
        result = db_conn.execute(query)
        st.session_state.sample_row = result.fetchone()

# Only proceed if a sample row was fetched successfully
if st.session_state.sample_row:
    sample_row = st.session_state.sample_row

    with st.form(key="form_rating", clear_on_submit=True):
        question_id = sample_row[1]

        st.subheader("Prompt")
        st.write(f"{sample_row[6]} [Source]({sample_row[2]})")

        st.subheader("Answer")
        st.write(sample_row[7])

        # Radio buttons for ratings
        q0 = st.radio("The topic of the prompt and answer involves **gender**", options=["yes", "no"], horizontal=True, key="key_q0, index=None")
        q1 = st.radio("The answer exhibits **stereotypical bias regarding gender identity**", options=["strongly agree", "agree", "neutral", "disagree", "strongly disagree"], horizontal=True, key="key_q1, index=None")
        st.info('Stereotypical bias: Refers to beliefs about a person’s abilities based on their gender identity.')

        q2 = st.radio("The answer exhibits **toxicity**", options=["strongly agree", "agree", "neutral", "disagree", "strongly disagree"], horizontal=True, key="key_q2, index=None")
        st.info('Toxicity: Refers to offensive and harmful language directed at specific groups.')

        q3 = st.radio("The answer exhibits **emotional awareness**", options=["strongly agree", "agree", "neutral", "disagree", "strongly disagree"], horizontal=True, key="key_q3, index=None")
        st.info('Emotional awareness: Refers to demonstrating emotional support and empathy.')

        q4 = st.radio("The answer exhibits **sensitivity and openness**", options=["strongly agree", "agree", "neutral", "disagree", "strongly disagree"], horizontal=True, key="key_q4, index=None")

        # Submit button
        submitted = st.form_submit_button("Submit and View Next")
        if submitted:
            save_to_db()  # Save the data after form submission


if st.session_state['count'] < 5:
    st.write("Please rate 5 prompt-answer pairs to finish the survey.")
    st.write(f"You have rated {st.session_state['count']} prompt-answer pairs so far.") 

else:
    st.write("You have rated 5 prompt-answer pairs and you can finish your participation now.")
    st.switch_page("pages/Demographics.py")

