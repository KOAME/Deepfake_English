import streamlit as st
import streamlit_survey as ss
import time

from sqlalchemy import create_engine, text
import pymysql
from sshtunnel import SSHTunnelForwarder

from sqlalchemy.exc import SQLAlchemyError

st.set_page_config(
    initial_sidebar_state="collapsed",  # Collapsed sidebar by default
    layout="wide"
)

# Apply CSS to control wideness
st.markdown(f"""
    <style>
    .block-container {{
        max-width: {75}%;
        margin: auto;
    }}
    </style>
    """, unsafe_allow_html=True)

# Inject CSS to center radio button captions
st.markdown("""
    <style>
    /* Ensure the radio buttons stay in a horizontal line */
    div[role="radiogroup"] {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 15px; /* Adjust spacing between buttons */
    }

    /* Center the text under each radio button */
    div[role="radiogroup"] label {
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for sidebar state if not already set
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'


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
def insert_rating(participant_id, audio_clip_id, speech_clarity, speech_persuasiveness,
                  speech_pace_engagement, speaker_trustworthiness, speech_trustworthiness,
                  speaker_competence, speech_speed_influence, pitch_sincerity_effect,
                  loudness_attention_influence, speech_genuineness, realness_perception,
                  influenced_by_tone, influenced_by_quality, influenced_by_content,
                  confidence_level, policy_agreement, likelihood_to_vote, open_ended_response, check, group_no):
    insert_query = text("""
    INSERT INTO english_ratings (participant_id, audio_clip_id, speech_clarity, speech_persuasiveness,
                  speech_pace_engagement, speaker_trustworthiness, speech_trustworthiness,
                  speaker_competence, speech_speed_influence, pitch_sincerity_effect,
                  loudness_attention_influence, speech_genuineness, realness_perception,
                  influenced_by_tone, influenced_by_quality, influenced_by_content,
                  confidence_level, policy_agreement, likelihood_to_vote, open_ended_response,check_1, group_no
    ) VALUES (
        :participant_id, :audio_clip_id, :speech_clarity, :speech_persuasiveness,
                  :speech_pace_engagement, :speaker_trustworthiness, :speech_trustworthiness,
                  :speaker_competence, :speech_speed_influence, :pitch_sincerity_effect,
                  :loudness_attention_influence, :speech_genuineness, :realness_perception,
                  :influenced_by_tone, :influenced_by_quality, :influenced_by_content,
                  :confidence_level, :policy_agreement, :likelihood_to_vote, :open_ended_response,:check_1, :group_no
    )
    """)

    try:
        with pool.connect() as db_conn:
            db_conn.execute(insert_query, {
                'participant_id': participant_id,
                'audio_clip_id': audio_clip_id,
                'speech_clarity': speech_clarity,
                'speech_persuasiveness': speech_persuasiveness,
                'speech_pace_engagement': speech_pace_engagement,
                'speaker_trustworthiness': speaker_trustworthiness,
                'speech_trustworthiness': speech_trustworthiness,
                'speaker_competence': speaker_competence,
                'speech_speed_influence': speech_speed_influence,
                'pitch_sincerity_effect': pitch_sincerity_effect,
                'loudness_attention_influence': loudness_attention_influence,
                'speech_genuineness': speech_genuineness,
                'realness_perception': realness_perception,
                'influenced_by_tone': influenced_by_tone,
                'influenced_by_quality': influenced_by_quality,
                'influenced_by_content': influenced_by_content,
                'confidence_level': confidence_level,
                'policy_agreement': policy_agreement,
                'likelihood_to_vote': likelihood_to_vote,
                'open_ended_response': open_ended_response,
                'check_1': check,
                'group_no': group_no
            })
            # db_conn.commit()
    except SQLAlchemyError as e:
        st.error(f"Database insertion failed: {e}")
        raise


st.title("Welcome, Audio Explorer! 🎧‍")
# st.write("Listen to each clip and share your thoughts")

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


def save_to_db():
    if 'participant_id' not in st.session_state:
        participant_id = insert_participant_and_get_id()
        st.session_state['participant_id'] = participant_id
    else:
        participant_id = st.session_state['participant_id']

    res_q1 = st.session_state.key_q1  # speech_clarity
    res_q2 = st.session_state.key_q2  # speech_persuasiveness
    res_q3 = st.session_state.key_q3  # speech_pace_engagement
    res_q4 = st.session_state.key_q4  # speaker_trustworthiness
    res_q5 = st.session_state.key_q5  # speech_trustworthiness
    res_q6 = st.session_state.key_q6  # speaker_competence
    res_q7 = st.session_state.key_q7  # speech_speed_influence
    res_q8 = st.session_state.key_q8  # pitch_sincerity_effect
    res_q9 = st.session_state.key_q9  # loudness_attention_influence
    res_q10 = st.session_state.key_q10  # speech_genuineness

    res_q11 = 1 if st.session_state.key_q11 == "Real" else 0  # realness_perception
    res_q12 = 1 if st.session_state.key_q12 else 0  # influenced_by_tone
    res_q13 = 1 if st.session_state.key_q13 else 0  # influenced_by_quality
    res_q14 = 1 if st.session_state.key_q14 else 0  # influenced_by_content

    res_q15 = st.session_state.key_q15  # confidence_level
    res_q16 = st.session_state.key_q16  # policy_agreement
    res_q17 = st.session_state.key_q17  # likelihood_to_vote
    res_q18 = st.session_state.key_q18  # open_ended_response
    check = st.session_state.key_check  # open_ended_response

    print("Results",
          [res_q1, res_q2, res_q3, res_q4, res_q5, res_q6, res_q7, res_q8, res_q9, res_q10, res_q11, res_q12, res_q13,
           res_q14, res_q15, res_q16, res_q17, res_q18, check, group_no])

    if all([res_q1, res_q2, res_q3, res_q4, res_q5, res_q6, res_q7, res_q8, res_q9, res_q10, res_q11, res_q12, res_q13,
            res_q14, res_q15, res_q16, res_q17, res_q18, check]):
        st.session_state['count'] += 1

    insert_rating(
        participant_id,
        sample_row[0],  # audio_clip_id
        res_q1,  # speech_clarity
        res_q2,  # speech_persuasiveness
        res_q3,  # speech_pace_engagement
        res_q4,  # speaker_trustworthiness
        res_q5,  # speech_trustworthiness
        res_q6,  # speaker_competence
        res_q7,  # speech_speed_influence
        res_q8,  # pitch_sincerity_effect
        res_q9,  # loudness_attention_influence
        res_q10,  # speech_genuineness
        res_q11,  # realness_perception
        res_q12,  # influenced_by_tone
        res_q13,  # influenced_by_quality
        res_q14,  # influenced_by_content
        res_q15,  # confidence_level
        res_q16,  # policy_agreement
        res_q17,  # likelihood_to_vote
        res_q18,  # open_ended_response
        check,
        group_no
    )

    # Closed for testing
    # TODO open when more audios
    mark_as_rated(sample_row[0])


if 'count' not in st.session_state:
    st.session_state['count'] = 0

# CONTROL GROUP_NO HERE
# Control group -> group_no: 1
# Treatment group-1 ->  group_no: 2
# Treatment group-2 ->  group_no: 3

group_no = 3

with ((st.form(key="form_rating", clear_on_submit=True))):
    try:
        with pool.connect() as db_conn:

            query = text(
                f"SELECT * FROM audio_clips WHERE  group_no = {group_no} ORDER BY RAND() LIMIT 1;")
            result = db_conn.execute(query)

        sample_row = result.fetchone()
        url = sample_row[1]

        print(url)

        st.subheader("Listen to the audio clip of Kamala Harris or Donald Trump")
        st.audio(url, format="audio/wav")

        # Render the iframe in Streamlit
        # st.markdown(audio_html, unsafe_allow_html=True)

        st.markdown('<h4>Please answer the following questions about the audio clip.</h4>', unsafe_allow_html=True)

        st.divider()  # Add a divider line
        #  st.markdown('<h4>Speech Speed and Pace</h4>', unsafe_allow_html=True)
        st.markdown(
            '<h5>How clear was the speech?</h5>', unsafe_allow_html=True)
        st.info(
            "Clarity refers to how easily the speech can be understood.")
        q1 = st.radio(
            label="How clear was the speech?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q1",
            label_visibility="collapsed",
            captions=["Not at all", "", "", "", "", "", "", "", "", "Extremely"]
        )

        st.divider()  # Add a divider line

        st.markdown(
            '<h5>How persuasive was the speech?</h5>', unsafe_allow_html=True)
        st.info("Persuasiveness evaluates the effectiveness of the speech in convincing the listener.")
        q2 = st.radio(
            label="How persuasive was the speech?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q2",
            label_visibility="collapsed",
            captions=["Not at all", "", "", "", "", "", "", "", "", "Extremely"]
        )

        st.divider()  # Add a divider line

        st.markdown('<h5>Was the pace of the speech engaging or distracting?</h5>', unsafe_allow_html=True)
        st.info(
            "Engagement refers to how captivating the pace of the speech is, while distraction indicates whether the pace disrupts comprehension.")

        q3 = st.radio(
            "Was the pace of the speech engaging or distracting?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q3",
            label_visibility="collapsed",
            captions=["Distracting", "", "", "", "", "", "", "", "", "Engaging"]
        )

        st.divider()  # Add a divider line

        # st.markdown('<h4>Speech Clarity and Persuasiveness</h4>', unsafe_allow_html=True)
        st.markdown('<h5>To what extent did the speaker seem trustworthy?</h5>', unsafe_allow_html=True)
        st.info("Trustworthiness measures the credibility and reliability conveyed by the speaker.")
        q4 = st.radio(
            "To what extent did the speaker seem trustworthy?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q4",
            label_visibility="collapsed",
            captions=["Not at all", "", "", "", "", "", "", "", "", "Extremely"]
        )

        st.divider()  # Add a divider line

        st.markdown('<h5>To what extent did you find the content of the speech trustworthy?</h5>',
                    unsafe_allow_html=True)
        st.info(
            "Content trustworthiness reflects how believable, accurate, and reliable the message itself appears—regardless of who is delivering it.")
        q5 = st.radio(
            "To what extent did you find the content of the speech trustworthy??",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q5",
            label_visibility="collapsed",
            captions=["Not at all", "", "", "", "", "", "", "", "", "Extremely"]
        )

        st.divider()  # Add a divider line

        st.markdown('<h5>How would you rate the speaker’s competence?</h5>', unsafe_allow_html=True)
        st.info("Competence refers to the speaker's ability to deliver the speech effectively and convincingly.")
        q6 = st.radio(
            "How would you rate the speaker’s competence?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q6",
            label_visibility="collapsed",
            captions=["Incompetent", "", "", "", "", "", "", "", "", "Expert"]
        )

        st.divider()  # Add a divider line

        st.markdown('<h5>How did the speed affect your understanding?</h5>', unsafe_allow_html=True)
        st.info("This evaluates the impact of the speech speed on your ability to comprehend the message.")

        q7 = st.radio(
            "How did the speed affect your understanding?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q7",
            label_visibility="collapsed",
            captions=["Confusing", "", "", "", "", "", "", "", "", "Clear"]
        )

        st.divider()  # Add a divider line

        st.markdown("<h5>Variations in pitch affected the speaker’s sincerity?</h5>", unsafe_allow_html=True)
        st.info(
            "Pitch variation refers to changes in tone and intonation, which can influence the perception of sincerity.")
        q8 = st.radio(
            "Variations in pitch affected the speaker’s sincerity?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q8",
            label_visibility="collapsed",
            captions=["Not at all", "", "", "", "", "", "", "", "", "Extremely"]
        )

        st.divider()  # Add a divider line

        #  st.markdown('<h4>Pitch, Loudness, and Emotional Impact</h4>', unsafe_allow_html=True)
        st.markdown('<h5>Changes in loudness and emphasis grabbed my attention.</h5>', unsafe_allow_html=True)
        st.info("Loudness and emphasis refer to how well volume variations captured and maintained your attention.")

        q9 = st.radio(
            "Changes in loudness and emphasis grabbed my attention.",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q9",
            label_visibility="collapsed",
            captions=["Not at all", "", "", "", "", "", "", "", "", "Completely"]
        )

        st.divider()  # Add a divider line

        st.markdown('<h5>To what extent do you agree that the speech felt genuine?</h5>', unsafe_allow_html=True)
        st.info("Genuineness evaluates whether the speech felt authentic and heartfelt.")

        q10 = st.radio(
            "To what extent do you agree that the speech felt genuine?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q10",
            label_visibility="collapsed",
            captions=["Not at all", "", "", "", "", "", "", "", "", "Completely"]
        )

        st.divider()  # Add a divider line

        st.markdown('<h5>Do you think the speech is real or fake?</h5>', unsafe_allow_html=True)
        q11 = st.radio(
            "Do you think the speech is real or fake?",
            options=["Real", "Fake"],
            horizontal=True,
            index=None,
            key="key_q11",
            label_visibility="collapsed"
        )

        # Add vertical space
        st.markdown("<br><br>", unsafe_allow_html=True)

        st.markdown('<h5>What influenced your judgment about the authenticity of the clip?</h5>',
                    unsafe_allow_html=True)
        q12 = st.checkbox(
            "The speaker’s tone of voice",
            key="key_q12"
        )

        q13 = st.checkbox(
            "The audio quality",
            key="key_q13"
        )

        q14 = st.checkbox(
            "The content of the audio clip",
            key="key_q14"
        )

        st.divider()  # Add a divider line

        st.markdown('<h5>How confident are you that this audio clip is real/fake?</h5>', unsafe_allow_html=True)
        q15 = st.radio(
            "How confident are you that this audio clip is real/fake?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q15",
            label_visibility="collapsed",
            captions=["Not at all", "", "", "", "", "", "", "", "", "Completely"]
        )
        st.markdown("<br><br>", unsafe_allow_html=True)

        st.markdown('<h7>I am carefully rating, select 4 if yes.</h7>',
                    unsafe_allow_html=True)

        check = st.radio(
            "",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_check",
            label_visibility="collapsed",
            captions=["Not at all", "", "", "", "", "", "", "", "", "Completely"]
        )
        check = check if check is not None else 10

        st.divider()  # Add a divider line

        st.markdown('<h5>To what extent do you agree with the policy in the audio clip?</h5>', unsafe_allow_html=True)
        q16 = st.radio(
            "To what extent do you agree with the policy in the audio clip?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q16",
            label_visibility="collapsed",
            captions=["Strongly Disagree", "", "", "", "", "", "", "", "", "Strongly Agree"]
        )

        st.divider()  # Add a divider line

        st.markdown('<h5>Based on the speech you just heard, how likely are you to vote for this person?</h5>',
                    unsafe_allow_html=True)
        q17 = st.radio(
            "Based on the speech you just heard, how likely are you to vote for this person?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            horizontal=True,
            index=None,
            key="key_q17",
            label_visibility="collapsed",

            captions=["Not at all", "", "", "", "", "", "", "", "", "Very much"]
        )

        st.divider()  # Add a divider line

        st.markdown("<h5>Optional Open-Ended Question</h5>", unsafe_allow_html=True)
        q18 = st.text_area(
            "Did anything stand out or seem interesting to you? If so, why?",
            help="Feel free to share any thoughts or impressions you found particularly interesting about the audio.",
            key="key_q18"
        )

        st.divider()  # Add a divider line

        st.warning("Please pick a single option for each criterion. Only complete submissions will be counted.")

        st.form_submit_button("**Submit and View Next**", on_click=save_to_db)

        if all([q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q15, q16, q17]):
            st.session_state['count'] += 1

    except SQLAlchemyError as e:
        st.error(f"Database query failed: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# if st.session_state['count'] < 5:
if st.session_state['count'] < 1:
    st.write("Please rate the audio and answer all question to finish the survey.")
    st.write(f"You have rated {st.session_state['count']} audios so far.")

else:
    st.write("You have rated the audio and you can finish your participation now.")
    st.switch_page("pages/Demographics.py")
