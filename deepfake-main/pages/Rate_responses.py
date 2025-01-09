import streamlit as st
import streamlit_survey as ss
import time

from sqlalchemy import create_engine, text
import pymysql
from sshtunnel import SSHTunnelForwarder

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
            font-size: 198px;
        }
        
        /* Custom class for markdown labels */
        .slider-label {
            font-size: 18px !important;  /* Set desired slider label size */
        }

            /* Center the main content with padding and border */
    .main-content {
        margin: 0 auto;             /* Center the content horizontally */
        padding: 20px;             /* Add space inside the container */
        max-width: 800px;          /* Set maximum width for the content */
        border: 2px solid red ; /* Add a light #E0E0E0 border around the content */
        border-radius: 10px;       /* Round the corners of the border */
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); /* Add a subtle shadow */
        background-color: #F9F9F9; /* Set a light background color */
    }

    /* Adjust the audio player and center it */
    audio {
        display: block;           /* Make it a block-level element */
        margin: 20px auto;        /* Center the audio player horizontally */
        width: 400px !important;  /* Set the width of the audio player */
    }
        </style>
        """, unsafe_allow_html=True)


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
            set_keepalive=30  # Keep SSH connection alive
        )
        tunnel.start()
        return tunnel
    except Exception as e:
        st.error(f"SSH tunnel connection failed: {e}")
        raise


# Establish a database connection with retry logic and pooling
def get_connection(tunnel, retries=10, delay=20):
    attempt = 0
    while attempt < retries:
        try:
            conn = pymysql.connect(
                host='127.0.0.1',
                user=db_user,
                password=db_password,
                database=db_name,
                port=tunnel.local_bind_port,
                connect_timeout=10600,  # Increased
                read_timeout=9600,  # Increased
                write_timeout=9600,  # Increased
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
        pool_pre_ping=True,  # Ensure connections are alive before query
        pool_recycle=3600,  # Recycle connections every 1 hour
        pool_size=3000,  # Number of connections in the pool
        max_overflow=3000  # Allow overflow for multiple requests
    )
    return pool


# SSH Tunnel Initialization
tunnel = start_ssh_tunnel()
pool = get_sqlalchemy_engine(tunnel)


# Insert a rating into the database
def insert_rating(participant_id, audio_clip_id, realness, confidence, speech_speed_influence, speech_pace_engagement,
                  speech_smoothness, speaker_competence_doubt, pitch_sincerity_effect,
                  loudness_attention_effectiveness,
                  volume_emotional_impact,
                  intonation_honesty_influence,
                  speaker_trustworthiness,
                  speech_genuineness):
    insert_query = text("""INSERT INTO ratings (participant_id, audio_clip_id, realness, confidence, 
    speech_speed_influence, speech_pace_engagement, speech_smoothness, speaker_competence_doubt, 
    pitch_sincerity_effect, loudness_attention_effectiveness, volume_emotional_impact, intonation_honesty_influence, 
    speaker_trustworthiness, speech_genuineness) VALUES (:participant_id, :audio_clip_id, :realness, :confidence, 
    :speech_speed_influence, :speech_pace_engagement, :speech_smoothness, :speaker_competence_doubt, 
    :pitch_sincerity_effect, :loudness_attention_effectiveness, :volume_emotional_impact, 
    :intonation_honesty_influence, :speaker_trustworthiness, :speech_genuineness)""")

    try:
        with pool.connect() as db_conn:
            db_conn.execute(insert_query,
                            {'participant_id': participant_id, 'audio_clip_id': audio_clip_id, 'realness': realness,
                             'confidence': confidence, 'speech_speed_influence': speech_speed_influence,
                             'speech_pace_engagement': speech_pace_engagement,
                             'speech_smoothness': speech_smoothness,
                             'speaker_competence_doubt': speaker_competence_doubt,
                             'pitch_sincerity_effect': pitch_sincerity_effect,
                             'loudness_attention_effectiveness': loudness_attention_effectiveness,
                             'volume_emotional_impact': volume_emotional_impact,
                             'intonation_honesty_influence': intonation_honesty_influence,
                             'speaker_trustworthiness': speaker_trustworthiness,
                             'speech_genuineness': speech_genuineness})
            # db_conn.commit()

    except SQLAlchemyError as e:
        st.error(f"Database insertion failed: {e}")
        raise


st.title("Welcome, Audio Explorer! 🎧‍")
st.write("Listen to each clip and share your thoughts")

# Start Survey
survey = ss.StreamlitSurvey("rate_survey")


# Insert new participant and get ID
def insert_participant_and_get_id():
    try:
        with pool.connect() as connection:
            insert_query = text(
                "INSERT INTO participants (age_group, gender, education, occupation, country_of_residence, "
                "nationality, race, native_tongue, languages_spoken, political_party, political_inclination, "
                "listening_habits, tech_savy, ai_experience, media_consumption) VALUES (NULL, NULL, NULL, NULL, NULL, "
                "NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)")
            connection.execute(insert_query)
            # connection.commit()
            last_id_query = text("SELECT LAST_INSERT_ID()")
            last_id_result = connection.execute(last_id_query)
            return last_id_result.scalar()
    except SQLAlchemyError as e:
        st.error(f"Failed to insert participant: {e}")
        raise


# Mark a prompt as rated
def mark_as_rated(audio_clip_id):
    try:
        with pool.connect() as db_conn:
            query = text("UPDATE audio_clips SET rated = 1 WHERE audio_clip_id = :audio_clip_id")
            db_conn.execute(query, {'audio_clip_id': audio_clip_id})
            # db_conn.commit()
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

    # Map the selection to 1 if "Real" is selected, otherwise 0
    res_q0 = 1 if st.session_state.key_q0 == "Real" else 0

    # Map the selection to 1 if "Engaging" is selected, otherwise 0
    res_q3 = 1 if st.session_state.key_q3 == "Engaging" else 0

    # Map the selection to 1 if Speaker's competence doubt is selected, otherwise 0
    res_q5 = 1 if st.session_state.key_q5 == "Yes" else 0

    res_q1 = st.session_state.key_q1
    res_q2 = st.session_state.key_q2
    res_q4 = st.session_state.key_q4
    res_q6 = st.session_state.key_q6
    res_q7 = st.session_state.key_q7
    res_q8 = st.session_state.key_q8
    res_q9 = st.session_state.key_q9
    res_q10 = st.session_state.key_q10
    res_q11 = st.session_state.key_q11

    print("Results", [res_q0, res_q1, res_q2, res_q3, res_q4, res_q5, res_q6, res_q7, res_q8, res_q9, res_q10, res_q11])

    if all([res_q0, res_q1, res_q2, res_q3, res_q4, res_q5, res_q6, res_q7, res_q8, res_q9, res_q10, res_q11]):
        st.session_state['count'] += 1

    insert_rating(
        participant_id,
        sample_row[0],  # audio_clip_id
        res_q0,
        res_q1,
        res_q2,
        res_q3,
        res_q4,
        res_q5,
        res_q6,
        res_q7,
        res_q8,
        res_q9,
        res_q10,
        res_q11
    )

    # Closed for testing
    # TODO open when more audios
    # mark_as_rated(sample_row[0])


if 'count' not in st.session_state:
    st.session_state['count'] = 0

slider_options = [None] + list(range(1, 5))
with st.form(key="form_rating", clear_on_submit=True):
    try:
        with pool.connect() as db_conn:

            # TODO originally the number is 42, change it back when there are enough audio clips
            query = text(
                "SELECT * FROM audio_clips WHERE rated = 0 AND audio_clip_id >= FLOOR(2 + (RAND() * (SELECT MAX("
                "audio_clip_id) - 2 FROM audio_clips))) LIMIT 1;")
            result = db_conn.execute(query)

        sample_row = result.fetchone()
        url = sample_row[1]

        st.subheader("Listen to the audio clip")
        st.video(url)

        st.markdown('<h4>Please answer the following questions about the audio clip.</h4>', unsafe_allow_html=True)

        st.divider()  # Add a divider line
      #  st.markdown('<h4>Speech Speed and Pace</h4>', unsafe_allow_html=True)
        st.markdown(
            '<div class="slider-label">How clear and persuasive was the speech? </div>',
            unsafe_allow_html=True)
        q1 = st.select_slider(
            "1 (Not clear at all) to 5 (Extremely clear) (default value None means no rating)",
             options=slider_options,
            value=None,
            key="key_q1"
        )
        #st.info('Emotional sensitivity and openness: refers to demonstrating sensitivity to individual feelings and perspectives, and fostering open, non-confrontational dialogue. [Source](https://arxiv.org/pdf/2402.11886)', icon="ℹ️")


        st.markdown('<div class="slider-label">Was the pace of the speech engaging or distracting?</div>', unsafe_allow_html=True)
        q2 = st.radio(
            "Was the pace of the speech engaging or distracting?",
            options=["Engaging", "Distracting"],
            horizontal=True,
            index=None,
            key="key_q2",
            label_visibility="collapsed"
        )
        
       # st.markdown('<h4>Speech Clarity and Persuasiveness</h4>', unsafe_allow_html=True)
        st.markdown(
            '<div class="slider-label">The speaker seemed trustworthy?</div>',
            unsafe_allow_html=True)
        q3 = st.select_slider(
            "1 (Not at all) to 5 (Very much) (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q3"
        )

        st.markdown('<div class="slider-label">The speech made you doubt the speakers competence?</div>',unsafe_allow_html=True)
        q4 = st.radio(
            "The speech made you doubt the speaker’s competence?",
            options=["Yes", "No"],
            horizontal=True,
            index=None,
            key="key_q4",
            label_visibility="collapsed"
        )

        st.markdown(
            '<div class="slider-label">The speech speed affected my understanding</div>',
            unsafe_allow_html=True)
        q5 = st.select_slider(
          "1 (Very negatively) to 5 (Very positively) (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q5",
            label_visibility="collapsed"
        )


        st.markdown(
            '<div class="slider-label">Variations in pitch affected the speaker’s sincerity?</div>',
            unsafe_allow_html=True)
        q6 = st.select_slider(
            "1 (Not at all) to 5 (Very much) (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q6",
            label_visibility="collapsed"
        )

     #   st.divider()  # Add a divider line
      #  st.markdown('<h4>Pitch, Loudness, and Emotional Impact</h4>', unsafe_allow_html=True)
        st.markdown(
            '<div class="slider-label"> Changes in loudness and emphasis grabbed my attention.</div>',
            unsafe_allow_html=True)

        q7 = st.select_slider(
            "1 (Not at all) to 5 (Completely) (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q7"
        )

        st.markdown(
            '<div class="slider-label">The speech felt genuine.</div>',
            unsafe_allow_html=True)
        q8 = st.select_slider(
            "1 (Not at all) to 5 (Completely) (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q8"
        )

        st.markdown(
            '<div class="slider-label">Do you think the speech is real or fake?</div>',
            unsafe_allow_html=True)
        q9 = st.radio(
            "Do you think the speech is real or fake?",
            options=["Real", "Fake"],
            horizontal=True,
            index=None,
            key="key_q9",
            label_visibility="collapsed"
        )

        st.markdown('<div class="slider-label">How confident are you that this audio clip is real/fake?</div>',
                    unsafe_allow_html=True)
        q11 = st.select_slider(
            "1 (Not at all) to 5 (Completely) (default value None means no rating)",
            options=slider_options,
            value=None,
            key="key_q11",
        )

        st.markdown("<h4>Optional Open-Ended Question</h4>", unsafe_allow_html=True)
        q12 =   st.text_area(
        "Do you think this audio was generated by AI? If so, why?",
        help="Share your thoughts about whether this audio might be AI-generated and provide reasons for your opinion.",
        key="key_q12"
        )


        st.divider()  # Add a divider line

        st.warning("Please pick a single option for each criterion. Only complete submissions will be counted.")

        st.form_submit_button("**Submit and View Next**", on_click=save_to_db)

        if all([q0, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11]):
            st.session_state['count'] += 1

    except SQLAlchemyError as e:
        st.error(f"Database query failed: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
# test
# if st.session_state['count'] < 10:
if st.session_state['count'] < 1:
    st.write("Please rate 10 audios to finish the survey.")
    st.write(f"You have rated {st.session_state['count']} audios so far.")

else:
    st.write("You have rated 10 audios and you can finish your participation now.")
    st.switch_page("pages/Demographics.py")
