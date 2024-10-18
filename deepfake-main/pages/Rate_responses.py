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
    st.markdown("""
        <style>
        /* Collapse the sidebar */
        [data-testid="collapsedControl"] {
            display: none;
        }
        [data-testid="stSidebar"] {
            display: none;
        }
        
        div[class*="stRadio"] > label > div[data-testid="stMarkdownContainer"] > p {
            font-size: 18px;
        }
        
        /* Custom class for markdown labels */
        .slider-label {
            font-size: 18px !important;  /* Set desired slider label size */
        }

        /* Adjust the video size */
        iframe, video {
            width: 400px !important;
            height: 225px !important;
        }
        </style>
        """, unsafe_allow_html=True)

# Apply the sidebar collapse dynamically based on session state
if st.session_state.sidebar_state == 'collapsed':
    collapse_sidebar()
    
# ssh_host = st.secrets["ssh_host"]
# ssh_port = st.secrets["ssh_port"]
# ssh_user = st.secrets["ssh_user"]
# ssh_password = st.secrets["ssh_password"]
#
# db_host = st.secrets["db_host"]
# db_user = st.secrets["db_user"]
# db_password = st.secrets["db_password"]
# db_name = st.secrets["db_name"]
# db_port = st.secrets["db_port"]

# # Set up SSH connection and tunnel
# def start_ssh_tunnel():
#     try:
#         tunnel = SSHTunnelForwarder(
#             (ssh_host, ssh_port),
#             ssh_username=ssh_user,
#             ssh_password=ssh_password,
#             remote_bind_address=(db_host, db_port),
#             set_keepalive=30  # Keep SSH connection alive
#         )
#         tunnel.start()
#         return tunnel
#     except Exception as e:
#         st.error(f"SSH tunnel connection failed: {e}")
#         raise
#
# # Establish a database connection with retry logic and pooling
# def get_connection(tunnel, retries=10, delay=20):
#     attempt = 0
#     while attempt < retries:
#         try:
#             conn = pymysql.connect(
#                 host='127.0.0.1',
#                 user=db_user,
#                 password=db_password,
#                 database=db_name,
#                 port=tunnel.local_bind_port,
#                 connect_timeout=10600,  # Increased
#                 read_timeout=9600,     # Increased
#                 write_timeout=9600,    # Increased
#                 max_allowed_packet=128 * 1024 * 1024  # 128MB
#             )
#             return conn
#         except pymysql.err.OperationalError as e:
#             st.error(f"Connection attempt {attempt + 1} failed: {e}")
#             attempt += 1
#             if attempt < retries:
#                 st.info(f"Retrying in {delay} seconds...")
#                 time.sleep(delay)
#             else:
#                 st.error("Failed to connect to the database after multiple retries. Please check your network!")
#                 raise
#
# # Create a SQLAlchemy engine with pre-ping and connection pooling
# def get_sqlalchemy_engine(tunnel):
#     pool = create_engine(
#         "mysql+pymysql://",
#         creator=lambda: get_connection(tunnel),
#         pool_pre_ping=True,   # Ensure connections are alive before query
#         pool_recycle=3600,    # Recycle connections every 1 hour
#         pool_size=3000,          # Number of connections in the pool
#         max_overflow=3000       # Allow overflow for multiple requests
#     )
#     return pool
#
# # SSH Tunnel Initialization
# tunnel = start_ssh_tunnel()
# pool = get_sqlalchemy_engine(tunnel)


# # Insert a rating into the database
# def insert_rating(participant_id, question_id, prompt_id, gender_focused, rating_stereotypical_bias, rating_toxicity, rating_emotional_awareness, rating_sensitivity, rating_helpfulness):
#     insert_query = """
#     INSERT INTO df_ratings (
#         participant_id,
#         question_id,
#         prompt_id,
#         gender_focused,
#         rating_stereotypical_bias,
#         rating_toxicity,
#         rating_emotional_awareness,
#         rating_sensitivity,
#         rating_helpfulness
#     ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """
#     try:
#         with pool.connect() as db_conn:
#             db_conn.execute(insert_query, (
#                 participant_id, question_id, prompt_id, gender_focused, rating_stereotypical_bias,
#                 rating_toxicity, rating_emotional_awareness, rating_sensitivity, rating_helpfulness
#             ))
#     except SQLAlchemyError as e:
#         st.error(f"Database insertion failed: {e}")
#         raise


st.title("Welcome, Detective! 🎧🕵️‍")
# st.write("Listen to each clip and decide: real or fake")
##start survey
survey = ss.StreamlitSurvey("rate_survey")

# # Insert new participant and get ID
# def insert_participant_and_get_id():
#     try:
#         with pool.connect() as connection:
#             insert_query = text("INSERT INTO df_participants (age, gender_identity, country_of_residence, ancestry, ethnicity) VALUES (NULL, NULL, NULL, NULL, NULL)")
#             connection.execute(insert_query)
#             last_id_query = text("SELECT LAST_INSERT_ID()")
#             last_id_result = connection.execute(last_id_query)
#             return last_id_result.scalar()
#     except SQLAlchemyError as e:
#         st.error(f"Failed to insert participant: {e}")
#         raise

# # Mark a prompt as rated
# def mark_as_rated(prompt_id):
#     try:
#         with pool.connect() as db_conn:
#             query = text("UPDATE df_prompts SET rated = 1 WHERE prompt_id = :prompt_id")
#             db_conn.execute(query, {'prompt_id': prompt_id})
#     except SQLAlchemyError as e:
#         st.error(f"Failed to mark prompt as rated: {e}")
#         raise
#
# # Save data to the database
# def save_to_db():
#     if 'participant_id' not in st.session_state:
#         participant_id = insert_participant_and_get_id()
#         st.session_state['participant_id'] = participant_id
#     else:
#         participant_id = st.session_state['participant_id']
#
#     res_q0 = st.session_state.key_q0
#     res_q1 = st.session_state.key_q1
#     res_q2 = st.session_state.key_q2
#     res_q3 = st.session_state.key_q3
#     res_q4 = st.session_state.key_q4
#     res_q5 = st.session_state.key_q5
#     res_q6 = st.session_state.key_q6
#     res_q7 = st.session_state.key_q7
#     res_q8 = st.session_state.key_q8
#     res_q9 = st.session_state.key_q9
#     res_q10 = st.session_state.key_q10
#     res_q11 = st.session_state.key_q11
#
#     if all([res_q0, res_q1, res_q2, res_q3, res_q4, res_q5, res_q6, res_q7, res_q8, res_q9, res_q10, res_q11]):
#         st.session_state['count'] += 1
#
#     insert_rating(
#         participant_id,
#         sample_row[1],  # question_id
#         sample_row[0],  # prompt_id
#         res_q0,
#         res_q1,
#         res_q2,
#         res_q3,
#         res_q4,
#         res_q5,
#         res_q6,
#         res_q7,
#         res_q8,
#         res_q9,
#         res_q10,
#         res_q11
#     )
#     mark_as_rated(sample_row[0])
#
if 'count' not in st.session_state:
    st.session_state['count'] = 0

slider_options = [None] + list(range(1, 11))
with st.form(key = "form_rating", clear_on_submit= True):
    try:
        # with pool.connect() as db_conn:
        #     query = text("SELECT * FROM df_prompts WHERE rated = 0 AND prompt_id >= FLOOR(42 + (RAND() * (SELECT MAX(prompt_id) - 42 FROM df_prompts))) LIMIT 1;")
        #     result = db_conn.execute(query)
        #
        # sample_row = result.fetchone()
        # question_id = sample_row[1]
        
        # st.subheader("Prompt")
        # st.write("{} [Source]({})".format(sample_row[6],sample_row[2]))
        #
        # st.subheader("Answer")
        # st.write(sample_row[7])

        st.subheader("Listen to the audio clip")
        st.write("Sample audio clip here.")
        st.video('https://youtu.be/DHXYWT3vkbY')

        st.markdown('<h4>Please answer the following questions about the audio clip.</h4>', unsafe_allow_html=True)

        st.divider()  # Add a divider line

        st.markdown('<h4>Audio Authenticity</h4>', unsafe_allow_html=True)
        st.markdown('<div class="slider-label">🔍 Is it Real or Fake?</div>', unsafe_allow_html=True)
        q0 = st.radio(
            label="Is it Real or Fake?",
            options=["Real", "Fake"],
            horizontal=True,
            index=None,
            key="key_q0",
            label_visibility="collapsed"
        )

        st.markdown('<div class="slider-label">🎯 How confident are you that this audio clip is real/fake?</div>', unsafe_allow_html=True)
        q1 = st.select_slider(
            "Scale: 1 - Not at all confident  to 10 - Extremely confident (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q1",
        )

        st.divider()  # Add a divider line
        st.markdown('<h4>Speech Speed and Pace</h4>', unsafe_allow_html=True)
        st.markdown('<div class="slider-label">🚀 How did the speed of the speech influence your overall impression of the message?</div>',
                    unsafe_allow_html=True)
        q2 = st.select_slider(
            "Scale: 1 - Very negatively to 10 - Very positively (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q2"
        )

        st.markdown('<div class="slider-label">🎶 Was the pace of the speech engaging or distracting?</div>',
            unsafe_allow_html=True)
        q3 = st.radio(
            "Was the pace of the speech engaging or distracting?",
            options=["Engaging", "Distracting"],
            horizontal=True,
            index=None,
            key="key_q3",
            label_visibility="collapsed"
        )

        st.markdown('<h4>Speech Clarity and Persuasiveness</h4>', unsafe_allow_html=True)
        st.markdown(
            '<div class="slider-label">🗣️ How smoothly was the speech delivered, and how did this affect its clarity and persuasiveness?</div>',
            unsafe_allow_html=True)
        q4 = st.select_slider(
            "Scale: 1 - Not clear at all to 10 - Extremely clear (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q4"
        )

        st.markdown(
            '<div class="slider-label">🧐 Were there any moments that made you question the speaker\'s competence?</div>',
            unsafe_allow_html=True)
        q5 = st.radio(
            "Were there any moments that made you question the speaker's competence?",
            options=["Yes", "No"],
            horizontal=True,
            index=None,
            key="key_q5",
            label_visibility="collapsed"
        )

        st.markdown('<h4>Pitch, Loudness, and Emotional Impact</h4>', unsafe_allow_html=True)
        st.markdown('<div class="slider-label">📈🎵 How did changes in pitch affect your feelings about the speaker\'s sincerity?</div>',
                    unsafe_allow_html=True)
        q6 = st.select_slider(
            "Scale: 1 - Not sincere at all to 10 - Extremely sincere (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q6"
        )

        st.markdown('<div class="slider-label">📈🔊 How effective were changes in loudness and emphasis in grabbing your attention?</div>', unsafe_allow_html=True)
        q7 = st.select_slider(
            "Scale: 1 - Not at all to 10 - Completely (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q7"
        )

        st.markdown('<div class="slider-label">📈🎭 Did the variations in volume and stress add to the emotional impact of the speech?</div>', unsafe_allow_html=True)
        q8 = st.select_slider(
            "Scale: 1 - Not at all to 10 - Very much (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q8"
        )

        st.markdown('<div class="slider-label">🤔 Did the intonation influence how honest the speaker seemed?</div>', unsafe_allow_html=True)
        q9 = st.select_slider(
            "Scale: 1 - Not at all to 10 - Very much (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q9"
        )

        st.divider()  # Add a divider line
        st.markdown('<h4>Speaker Trustworthiness and Genuineness</h4>', unsafe_allow_html=True)
        st.markdown('<div class="slider-label">🤝 How trustworthy did you find the speaker\'s delivery?</div>', unsafe_allow_html=True)
        q10 = st.select_slider(
            "Scale: 1 - Not at all to 10 - Very much (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q10"
        )

        st.markdown('<div class="slider-label">🤗 How genuine did the speech feel to you?</div>',
                    unsafe_allow_html=True)
        q11 = st.select_slider(
            "Scale: 1 - Not genuine at all to 10 - Very genuine (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q11"
        )

        st.divider()  # Add a divider line

        st.warning("Please pick a single option for each criterion. Only complete submissions will be counted.")
        
        # st.form_submit_button("Submit and View Next", on_click = save_to_db)
        st.form_submit_button("**Submit and View Next**")

        # Cheng: this line is just for testing purposes
        if all([q11]): st.session_state['count'] += 1

    except SQLAlchemyError as e:
        st.error(f"Database query failed: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")


if st.session_state['count'] < 10:
    st.write("Please rate 10 audios to finish the survey.")
    st.write(f"You have rated {st.session_state['count']} audios so far.")

else:
    st.write("You have rated 10 audios and you can finish your participation now.")
    # st.switch_page("pages/Demographics.py")
    # Cheng: this line is just for testing purposes
    # st.switch_page("pages/End_participation.py")
