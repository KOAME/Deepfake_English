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
# DB Helpers
# --------------------------------------------------------------------------------
def insert_participant_and_get_id():
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
    scam: str,
    open_ended_response: str,
    check_1: bool,
    group_no: int
):
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
            :group_no
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
                    "group_no": group_no,
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

if "step" not in st.session_state:
    st.session_state["step"] = 1  # 1 = first page, 2 = second page

group_no = 3

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

    # ---- Step-1 answers are frozen into ans_* when clicking Next
    realness_scale = st.session_state.get("ans_realness_scale")

    rf = st.session_state.get("ans_real_fake")
    realness_perception = 1 if rf == "Real" else (0 if rf == "Fake" else None)

    confident = st.session_state.get("ans_confident")
    difficult_to_decide = st.session_state.get("ans_difficulty")

    # ---- Step-2 answers are read from the step-2 widgets
    trust_content = st.session_state.get("key_trust_content")
    trust_media = st.session_state.get("key_trust_media")

    scam = st.session_state.get("key_scam")

    check_val = st.session_state.get("key_check")
    check_1 = True if check_val == 4 else False

    open_ended_response = st.session_state.get("key_open_ended")

    required = [
        realness_scale,
        realness_perception,
        confident,
        difficult_to_decide,
        trust_content,
        trust_media,
        scam,
        check_val,
    ]

    if not all(v is not None for v in required):
        st.error("You missed required questions. Please answer everything before submitting.")
        # Helpful debug so you see exactly what is missing
        st.write("DEBUG required:", {
            "realness_scale": realness_scale,
            "realness_perception": realness_perception,
            "confident": confident,
            "difficult_to_decide": difficult_to_decide,
            "trust_content": trust_content,
            "trust_media": trust_media,
            "scam": scam,
            "check_val": check_val,
        })
        return False

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
        group_no=group_no,
    )

    st.session_state["count"] += 1
    return True

with st.form(key="form_rating", clear_on_submit=False):
    try:
        # Fetch clip only when starting a new item
        if st.session_state["step"] == 1 or "audio_clip_id" not in st.session_state:
            with pool.connect() as db_conn:
                query = text(
                    """
                    SELECT audio_clip_id, url, topic
                    FROM deepfakes.audio_clips
                    WHERE group_no = 4
                    ORDER BY RAND()
                    LIMIT 1;
                    """
                )
                row = db_conn.execute(query, {"group_no": group_no}).fetchone()

            if not row:
                st.error("No audio found.")
                st.stop()

            audio_clip_id, url, topic = row
            st.session_state["audio_clip_id"] = audio_clip_id
            st.session_state["url"] = url

        url = st.session_state["url"]

        # ==================================================
        # STEP 1 — Audio + Q1–Q4
        # ==================================================
        if st.session_state["step"] == 1:
             st.warning(
            "⚠️ Use Google Chrome. Answer every question before submitting. "
            "If you skip any required question, you may lose answers for this clip."
            )
            st.markdown(
                "<h4>🔊 Listen to the audio clip and answer the questions below.</h4>",
                unsafe_allow_html=True,
            )
            st.audio(url, format="audio/wav")
            st.info("❗If the audio isn't playing, refresh the page or try a different browser.")
            st.markdown(f"⬇️ **Download the audio if the player fails:** [{url}]({url})")

            st.divider()

            st.markdown("<h5>❓Do you think the speech is real or fake?</h5>", unsafe_allow_html=True)
            st.radio("", ["Real", "Fake"], horizontal=True, index=None, key="key_real_fake")

            st.markdown("<h5>❓On a scale from fake to real, how would you rate this audio?</h5>", unsafe_allow_html=True)
            ten_radio("key_realness_scale", "Definitely Fake", "Definitely Real")

            st.markdown("<h5>❓How confident are you in your judgement?</h5>", unsafe_allow_html=True)
            ten_radio("key_confident", "Not confident", "Extremely confident")

            st.markdown(
                "<h5>❓How difficult was it for you to decide whether the audio was real or fake?</h5>",
                unsafe_allow_html=True,
            )
            ten_radio("key_difficulty", "Very easy", "Very difficult")

            next_clicked = st.form_submit_button("Next ➜")

            if next_clicked:
                required_step1 = [
                    st.session_state.get("key_real_fake"),
                    st.session_state.get("key_realness_scale"),
                    st.session_state.get("key_confident"),
                    st.session_state.get("key_difficulty"),
                ]
                if not all(v is not None for v in required_step1):
                    st.error("Please answer all questions before continuing.")
                else:
                    # Freeze step-1 answers so they persist reliably into step-2 submission
                    st.session_state["ans_real_fake"] = st.session_state.get("key_real_fake")
                    st.session_state["ans_realness_scale"] = st.session_state.get("key_realness_scale")
                    st.session_state["ans_confident"] = st.session_state.get("key_confident")
                    st.session_state["ans_difficulty"] = st.session_state.get("key_difficulty")

                    st.session_state["step"] = 2
                    st.rerun()

        # ==================================================
        # STEP 2 — Remaining questions + FAKE notice
        # ==================================================
        else:
            st.toast("🚨 Warning: You listened to a fake (AI-generated) audio clip", icon="🚨")

            st.markdown(
                """
                <div style="
                    background:#fff0f0;
                    border:3px solid red;
                    padding:16px;
                    font-size:24px;
                    font-weight:900;
                    text-align:center;
                    border-radius:12px;
                    margin-bottom:20px;">
                    🚨 Warning: You listened to a fake (AI-generated) audio clip
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<h5>❓How much do you trust political audio content online?</h5>", unsafe_allow_html=True)
            ten_radio("key_trust_content", "Not at all", "Completely")

            st.markdown("<h5>❓How much do you trust online news media?</h5>", unsafe_allow_html=True)
            ten_radio("key_trust_media", "Not at all", "Completely")

            st.markdown("<h7>I am carefully rating, select 4 if yes.</h7>", unsafe_allow_html=True)
            st.radio("", list(range(1, 11)), horizontal=True, index=None, key="key_check")

            st.markdown("<h5>❓Have you fallen for misleading info online?</h5>", unsafe_allow_html=True)
            st.radio("", ["Yes", "No", "Not sure"], horizontal=True, index=None, key="key_scam")

            st.markdown("<h5>Optional</h5>", unsafe_allow_html=True)
            st.text_area("Anything stand out?", key="key_open_ended")

            submitted = st.form_submit_button("**Submit and View Next**")

            if submitted:
                ok = save_to_db()
                if not ok:
                    st.stop()

                # reset UI state for next clip (only after successful DB insert)
                st.session_state["step"] = 1

                for k in [
                    # step-2 widget keys
                    "key_trust_content", "key_trust_media", "key_check", "key_scam", "key_open_ended",
                    # frozen step-1 answers
                    "ans_real_fake", "ans_realness_scale", "ans_confident", "ans_difficulty",
                    # clip cache
                    "audio_clip_id", "url",
                    # step-1 widget keys (optional cleanup)
                    "key_real_fake", "key_realness_scale", "key_confident", "key_difficulty",
                ]:
                    st.session_state.pop(k, None)

                st.rerun()

    except Exception as e:
        st.error(f"Unexpected error: {e}")

# Finish / route
if st.session_state["count"] < 1:
    st.write("Please rate the audio and answer all required questions to finish the survey.")
    st.write(f"You have rated {st.session_state['count']} audios so far.")
else:
    st.write("You have rated the audio and you can finish your participation now.")
    st.switch_page("pages/Demographics.py")
