import streamlit as st
import streamlit_survey as ss
import time

from sqlalchemy import create_engine, text
import pymysql
from sshtunnel import SSHTunnelForwarder
from sqlalchemy.exc import SQLAlchemyError

# --------------------------------------------------------------------------------
# Page & Layout
# --------------------------------------------------------------------------------
group_no = 2

st.set_page_config(initial_sidebar_state="collapsed", layout="wide")

st.markdown(
    """
    <style>
    .block-container { max-width: 75%; margin: auto; }
    div[role="radiogroup"] {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 15px;
    }
    div[role="radiogroup"] label {
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "collapsed"

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

if st.session_state.sidebar_state == "collapsed":
    collapse_sidebar()

# --------------------------------------------------------------------------------
# Secrets
# --------------------------------------------------------------------------------
ssh_host = st.secrets["ssh_host"]
ssh_port = st.secrets["ssh_port"]
ssh_user = st.secrets["ssh_user"]
ssh_password = st.secrets["ssh_password"]

db_host = st.secrets["db_host"]
db_user = st.secrets["db_user"]
db_password = st.secrets["db_password"]
db_name = st.secrets["db_name"]
db_port = st.secrets["db_port"]

# --------------------------------------------------------------------------------
# SSH + DB
# --------------------------------------------------------------------------------
def start_ssh_tunnel():
    try:
        tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(db_host, db_port),
            set_keepalive=30,
        )
        tunnel.start()
        return tunnel
    except Exception as e:
        st.error(f"SSH tunnel connection failed: {e}")
        raise

def get_connection(tunnel, retries=10, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            conn = pymysql.connect(
                host="127.0.0.1",
                user=db_user,
                password=db_password,
                database=db_name,
                port=tunnel.local_bind_port,
                connect_timeout=60,
                read_timeout=60,
                write_timeout=60,
                max_allowed_packet=128 * 1024 * 1024,
            )
            return conn
        except pymysql.err.OperationalError as e:
            attempt += 1
            if attempt < retries:
                st.info(f"DB connection failed (attempt {attempt}/{retries}). Retrying in {delay}s…")
                time.sleep(delay)
            else:
                st.error(f"Failed to connect to DB after {retries} attempts: {e}")
                raise

def get_sqlalchemy_engine(tunnel):
    engine = create_engine(
        "mysql+pymysql://",
        creator=lambda: get_connection(tunnel),
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
    )
    return engine

tunnel = start_ssh_tunnel()
pool = get_sqlalchemy_engine(tunnel)

# --------------------------------------------------------------------------------
# DB Helpers (NEW, MINIMAL)
# --------------------------------------------------------------------------------
def insert_participant_and_get_id():
    """
    If you still want participant_id, you need a participants table.
    Keep your existing implementation if participants_phase2 still exists.
    """
    try:
        with pool.begin() as connection:
            insert_query = text(
                """
                INSERT INTO participants_phase3 (
                    age_group, gender, education, occupation, country_of_residence,
                    nationality, race, native_tongue, languages_spoken, political_party,
                    political_inclination, listening_habits, tech_savy, ai_experience, media_consumption
                )
                VALUES (NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
                """
            )
            connection.execute(insert_query)
            last_id_result = connection.execute(text("SELECT LAST_INSERT_ID()"))
            return last_id_result.scalar()
    except SQLAlchemyError as e:
        st.error(f"Failed to insert participant: {e}")
        raise

def insert_rating_phase3(
    participant_id: int,
    audio_clip_id: int,
    realness_scale: int,
    realness_perception: int,
    confident: int,
    difficult_to_decide: int,
    trust_content: int,
    trust_media: int,
    scam: int,
    open_ended_response: str,
    check_1: bool,
    group_no,
):
    """
    Matches exactly: deepfakes.english_ratings_phase3
    """
    insert_query = text(
        """
        INSERT INTO deepfakes.english_ratings_phase3 (
            participant_id,
            audio_clip_id,
            realness_scale,
            realness_perception,
            confident,
            difficult_to_decide,
            trust_content,
            trust_media,
            scam,
            open_ended_response,
            check_1,
            group_no
        )
        VALUES (
            :participant_id,
            :audio_clip_id,
            :realness_scale,
            :realness_perception,
            :confident,
            :difficult_to_decide,
            :trust_content,
            :trust_media,
            :scam,
            :open_ended_response,
            :check_1,
            :group_no,
        )
        """
    )
    try:
        with pool.begin() as db_conn:
            db_conn.execute(
                insert_query,
                {
                    "participant_id": participant_id,
                    "audio_clip_id": audio_clip_id,
                    "realness_scale": realness_scale,
                    "realness_perception": realness_perception,
                    "confident": confident,
                    "difficult_to_decide": difficult_to_decide,
                    "trust_content": trust_content,
                    "trust_media": trust_media,
                    "scam": scam,
                    "open_ended_response": open_ended_response,
                    "check_1": check_1,
                    "group_no":group_no
                },
            )
    except SQLAlchemyError as e:
        st.error(f"Database insertion failed: {e}")
        raise

# --------------------------------------------------------------------------------
# UI + Logic
# --------------------------------------------------------------------------------
st.title("Welcome, Audio Explorer! 🎧")
survey = ss.StreamlitSurvey("rate_survey")

if "count" not in st.session_state:
    st.session_state["count"] = 0

# CONTROL GROUP_NO HERE (keep if you still sample by group_no)

def ten_radio(key: str, left_label: str | None = None, right_label: str | None = None):
    val = st.radio(
        "",
        options=list(range(1, 11)),
        horizontal=True,
        index=None,
        key=key,
        label_visibility="collapsed",
    )
    if left_label and right_label:
        st.info(f"1 = {left_label}, 10 = {right_label}")
    return val

def save_to_db():
    # participant id
    if "participant_id" not in st.session_state:
        st.session_state["participant_id"] = insert_participant_and_get_id()
    participant_id = st.session_state["participant_id"]

    # --- map UI to DB types ---
    realness_scale = st.session_state.get("key_realness_scale")

    rf = st.session_state.get("key_real_fake")
    # Store as 1=Real, 0=Fake (consistent with your earlier coding)
    realness_perception = 1 if rf == "Real" else (0 if rf == "Fake" else None)

    confident = st.session_state.get("key_confident")
    difficult_to_decide = st.session_state.get("key_difficulty")

    trust_content = st.session_state.get("key_trust_content")
    trust_media = st.session_state.get("key_trust_media")

    scam_raw = st.session_state.get("key_scam")  # "Yes" / "No" / "Not sure" / None
    SCAM_MAP = {"Yes": 1, "No": 0, "Not sure": 2}
    scam = SCAM_MAP.get(scam_raw)  # -> 1/0/2/None

    check_val = st.session_state.get("key_check")
    # Your text says “select 4 if yes” so enforce boolean True if ==4
    check_1 = True if check_val == 4 else False
    open_ended_response = st.session_state.get("key_open_ended")
    group_no=group_no


    required = [
        realness_scale,
        realness_perception,
        confident,
        difficult_to_decide,
        trust_content,
        trust_media,
        scam,
        check_val,  # so they must answer the attention check
    ]
    if not all(v is not None for v in required):
        st.error("You missed required questions. Please answer everything before submitting.")
        return

    insert_rating_phase3(
        participant_id=participant_id,
        audio_clip_id=st.session_state["audio_clip_id"],
        realness_scale=realness_scale,
        realness_perception=realness_perception,
        confident=confident,
        difficult_to_decide=difficult_to_decide,
        trust_content=trust_content,
        trust_media=trust_media,
        scam=scam,
        open_ended_response=open_ended_response,
        check_1=check_1,
    )

    st.session_state["count"] += 1

with st.form(key="form_rating", clear_on_submit=True):
    try:
        # Fetch one clip for the chosen group
        with pool.connect() as db_conn:
            query = text(
                """
                SELECT audio_clip_id, url, topic
                FROM deepfakes.audio_clips
                WHERE group_no = :group_no
                ORDER BY RAND()
                LIMIT 1;
                """
            )
            sample_row = db_conn.execute(query, {"group_no": group_no}).fetchone()

        if not sample_row:
            st.error("No audio found for this group. Please try again later.")
            st.stop()

        audio_clip_id, url, topic = sample_row
        st.session_state["audio_clip_id"] = audio_clip_id
        st.session_state["current_topic"] = topic if topic else "this topic"

        st.warning(
            "⚠️ Use Google Chrome. Answer every question before submitting. "
            "If you skip any required question, you may lose answers for this clip."
        )

        st.markdown(
            "<h4>🔊 Listen to the audio clip and answer the questions below.</h4>",
            unsafe_allow_html=True,
        )
        st.audio(url, format="audio/wav")
        st.info("If the audio isn't playing, refresh the page or try a different browser.")

        st.divider()


        # Q1: Real/Fake binary
        st.markdown("<h5>❓Do you think the speech is real or fake?</h5>", unsafe_allow_html=True)
        st.radio(
            "",
            options=["Real", "Fake"],
            horizontal=True,
            index=None,
            key="key_real_fake",
            label_visibility="collapsed",
        )
        
        # Q2: Fake→Real scale
        st.markdown("<h5>❓On a scale from fake to real, how would you rate this audio?</h5>", unsafe_allow_html=True)
        ten_radio("key_realness_scale", "Definitely Fake", "Definitely Real")


        # Q3: Confidence retrospective
        st.markdown(
            "<h5>❓How confident are you that your judgement about the authenticity of the audio was correct?</h5>",
            unsafe_allow_html=True,
        )
        ten_radio("key_confident", "Not confident at all", "Extremely confident")
        # Q4: Difficulty
        st.markdown(
            "<h5>❓How difficult was it for you to decide whether the audio was real or fake?</h5>",
            unsafe_allow_html=True,
        )
        ten_radio("key_difficulty", "Very easy", "Very difficult")
        
        # Q5: Trust political audio content online
        st.markdown(
            "<h5>❓How much do you trust political audio content you encounter online?</h5>",
            unsafe_allow_html=True,
        )
        ten_radio("key_trust_content", "Not at all", "Completely")

        # Q6: Trust online news/political media
        st.markdown(
            "<h5>❓How much do you trust online news and political media in general?</h5>",
            unsafe_allow_html=True,
        )
        ten_radio("key_trust_media", "Not at all", "Completely")



        # Attention check
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<h7>I am carefully rating, select 4 if yes.</h7>', unsafe_allow_html=True)
        st.radio(
            "",
            options=list(range(1, 11)),
            horizontal=True,
            index=None,
            key="key_check",
            label_visibility="collapsed",
        )
        # Q7: Scam / misleading info experience
        st.markdown(
            "<h5>❓Have you ever personally fallen for false or misleading information online (for example, a scam, hoax, or manipulated media)?</h5>",
            unsafe_allow_html=True,
        )
        st.radio(
            "",
            options=["Yes", "No", "Not sure"],
            horizontal=True,
            index=None,
            key="key_scam",
            label_visibility="collapsed",
        )
        # Optional open-ended
        st.markdown("<h5>Optional Open-Ended Question</h5>", unsafe_allow_html=True)
        st.text_area(
            "Did anything stand out or seem interesting to you? If so, why?",
            key="key_open_ended",
        )

        st.divider()
        st.form_submit_button("**Submit and View Next**", on_click=save_to_db)

    except SQLAlchemyError as e:
        st.error(f"Database query failed: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# Finish / route
if st.session_state["count"] < 1:
    st.write("Please rate the audio and answer all required questions to finish the survey.")
    st.write(f"You have rated {st.session_state['count']} audios so far.")
else:
    st.write("You have rated the audio and you can finish your participation now.")
    st.switch_page("pages/Demographics.py")
