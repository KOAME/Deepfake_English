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

# Apply CSS to control width
st.markdown(
    f"""
    <style>
    .block-container {{
        max-width: {75}%;
        margin: auto;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Inject CSS to center radio button captions
st.markdown(
    """
    <style>
    /* Horizontal radio buttons */
    div[role="radiogroup"] {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 15px;
    }
    /* Center label text */
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

# Sidebar state init
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


def get_connection(tunnel, retries=10, delay=20):
    attempt = 0
    while attempt < retries:
        try:
            conn = pymysql.connect(
                host="127.0.0.1",
                user=db_user,
                password=db_password,
                database=db_name,
                port=tunnel.local_bind_port,
                connect_timeout=10600,
                read_timeout=9600,
                write_timeout=9600,
                max_allowed_packet=128 * 1024 * 1024,
            )
            return conn
        except pymysql.err.OperationalError as e:
            st.error(f"Connection attempt {attempt + 1} failed: {e}")
            attempt += 1
            if attempt < retries:
                st.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                st.error(
                    "Failed to connect to the database after multiple retries. Please check your network!"
                )
                raise


def get_sqlalchemy_engine(tunnel):
    # Use SQLAlchemy pre-ping and pooling
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
def insert_rating(
    participant_id,
    audio_clip_id,
    speech_clarity,
    speech_persuasiveness,
    speech_pace_engagement,
    speaker_trustworthiness,
    speech_trustworthiness,
    speaker_competence,
    speech_speed_influence,
    pitch_sincerity_effect,
    loudness_attention_influence,
    realness_scale,
    realness_perception,
    influenced_by_tone,
    influenced_by_quality,
    influenced_by_content,
    confidence_level,
    policy_agreement,
    likelihood_to_vote,
    open_ended_response,
    check,
    group_no,
    share_likely_private,
    share_likely_public,
    report_misleading,
    downrank_agree,
    watermark_action,
    candidate_position_after,
    em_anger,
    em_fear,
    em_disgust,
    em_sadness,
    em_enthusiasm,
    em_pride,
    mip_topics,
    perceived_threat,
    identity_threat,
    salience_before,
    salience_after,
):
    """
    Inserts into table: english_ratings_phase2
    Columns must match your DB schema.
    """
    insert_query = text(
        """
        INSERT INTO english_ratings_phase2 (
            participant_id, audio_clip_id, speech_clarity, speech_persuasiveness,
            speech_pace_engagement, speaker_trustworthiness, speech_trustworthiness,
            speaker_competence, speech_speed_influence, pitch_sincerity_effect,
            loudness_attention_influence, realness_scale, realness_perception,
            influenced_by_tone, influenced_by_quality, influenced_by_content,
            confidence_level, policy_agreement, likelihood_to_vote, open_ended_response,
            check_1, group_no, share_likely_private, share_likely_public, report_misleading,
            downrank_agree, watermark_action, candidate_position_after,
            em_anger, em_fear, em_disgust, em_sadness, em_enthusiasm, em_pride, mip_topics,
            perceived_threat, identity_threat, salience_before, salience_after
        )
        VALUES (
            :participant_id, :audio_clip_id, :speech_clarity, :speech_persuasiveness,
            :speech_pace_engagement, :speaker_trustworthiness, :speech_trustworthiness,
            :speaker_competence, :speech_speed_influence, :pitch_sincerity_effect,
            :loudness_attention_influence, :realness_scale, :realness_perception,
            :influenced_by_tone, :influenced_by_quality, :influenced_by_content,
            :confidence_level, :policy_agreement, :likelihood_to_vote, :open_ended_response,
            :check_1, :group_no, :share_likely_private, :share_likely_public, :report_misleading,
            :downrank_agree, :watermark_action, :candidate_position_after,
            :em_anger, :em_fear, :em_disgust, :em_sadness, :em_enthusiasm, :em_pride, :mip_topics,
            :perceived_threat, :identity_threat, :salience_before, :salience_after
        )
        """
    )

    try:
        # Use a transaction so it commits automatically on success
        with pool.begin() as db_conn:
            db_conn.execute(
                insert_query,
                {
                    "participant_id": participant_id,
                    "audio_clip_id": audio_clip_id,
                    "speech_clarity": speech_clarity,
                    "speech_persuasiveness": speech_persuasiveness,
                    "speech_pace_engagement": speech_pace_engagement,
                    "speaker_trustworthiness": speaker_trustworthiness,
                    "speech_trustworthiness": speech_trustworthiness,
                    "speaker_competence": speaker_competence,
                    "speech_speed_influence": speech_speed_influence,
                    "pitch_sincerity_effect": pitch_sincerity_effect,
                    "loudness_attention_influence": loudness_attention_influence,
                    "realness_scale": realness_scale,
                    "realness_perception": realness_perception,
                    "influenced_by_tone": influenced_by_tone,
                    "influenced_by_quality": influenced_by_quality,
                    "influenced_by_content": influenced_by_content,
                    "confidence_level": confidence_level,
                    "policy_agreement": policy_agreement,
                    "likelihood_to_vote": likelihood_to_vote,
                    "open_ended_response": open_ended_response,
                    "check_1": check,
                    "group_no": group_no,
                    "share_likely_private": share_likely_private,
                    "share_likely_public": share_likely_public,
                    "report_misleading": report_misleading,
                    "downrank_agree": downrank_agree,
                    "watermark_action": watermark_action,
                    "candidate_position_after": candidate_position_after,
                    "em_anger": em_anger,
                    "em_fear": em_fear,
                    "em_disgust": em_disgust,
                    "em_sadness": em_sadness,
                    "em_enthusiasm": em_enthusiasm,
                    "em_pride": em_pride,
                    "mip_topics": mip_topics,
                    "perceived_threat": perceived_threat,
                    "identity_threat": identity_threat,
                    "salience_before": salience_before,
                    "salience_after": salience_after,
                },
            )
    except SQLAlchemyError as e:
        st.error(f"Database insertion failed: {e}")
        raise


def insert_participant_and_get_id():
    try:
        with pool.begin() as connection:
            insert_query = text(
                """
                INSERT INTO participants (
                    age_group, gender, education, occupation, country_of_residence,
                    nationality, race, native_tongue, languages_spoken, political_party,
                    political_inclination, listening_habits, tech_savy, ai_experience, media_consumption
                )
                VALUES (NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
                """
            )
            connection.execute(insert_query)
            last_id_query = text("SELECT LAST_INSERT_ID()")
            last_id_result = connection.execute(last_id_query)
            return last_id_result.scalar()
    except SQLAlchemyError as e:
        st.error(f"Failed to insert participant: {e}")
        raise


def mark_as_rated(audio_clip_id):
    try:
        with pool.begin() as db_conn:
            query = text("UPDATE audio_clips SET rated = 1 WHERE audio_clip_id = :audio_clip_id")
            db_conn.execute(query, {"audio_clip_id": audio_clip_id})
    except SQLAlchemyError as e:
        st.error(f"Failed to mark prompt as rated: {e}")
        raise

# --------------------------------------------------------------------------------
# UI + Logic
# --------------------------------------------------------------------------------
st.title("Welcome, Audio Explorer! 🎧")
survey = ss.StreamlitSurvey("rate_survey")

# progress count
if "count" not in st.session_state:
    st.session_state["count"] = 0

# CONTROL GROUP_NO HERE
# Control group -> group_no: 1
# Treatment group-1 -> group_no: 2
# Treatment group-2 -> group_no: 3
group_no = 3

def save_to_db():
    # participant id
    if "participant_id" not in st.session_state:
        participant_id = insert_participant_and_get_id()
        st.session_state["participant_id"] = participant_id
    else:
        participant_id = st.session_state["participant_id"]

    # Pull values from session_state (these keys must match widgets)
    res_q1 = st.session_state.get("key_q1")   # speech_clarity
    res_q2 = st.session_state.get("key_q2")   # speech_persuasiveness
    res_q3 = st.session_state.get("key_q3")   # speech_pace_engagement
    res_q4 = st.session_state.get("key_q4")   # speaker_trustworthiness
    res_q5 = st.session_state.get("key_q5")   # speech_trustworthiness
    res_q6 = st.session_state.get("key_q6")   # speaker_competence
    res_q7 = st.session_state.get("key_q7")   # speech_speed_influence
    res_q8 = st.session_state.get("key_q8")   # pitch_sincerity_effect
    res_q9 = st.session_state.get("key_q9")   # loudness_attention_influence
    res_q10 = st.session_state.get("key_q10") # realness_scale (1..10)

    # Real/Fake (1=Real, 0=Fake)
    q11 = st.session_state.get("key_q11")
    res_q11 = 1 if q11 == "Real" else (0 if q11 == "Fake" else None)

    res_q12 = 1 if st.session_state.get("key_q12") else 0  # influenced_by_tone
    res_q13 = 1 if st.session_state.get("key_q13") else 0  # influenced_by_quality
    res_q14 = 1 if st.session_state.get("key_q14") else 0  # influenced_by_content

    res_q15 = st.session_state.get("key_q15")              # confidence_level
    res_q16 = st.session_state.get("key_q16")              # policy_agreement
    res_q17 = st.session_state.get("key_q17")              # likelihood_to_vote
    res_q18 = st.session_state.get("key_q18")              # open_ended_response

    check_val = st.session_state.get("key_check")
    check_val = 10 if check_val is None else check_val     # default to 10

    share_likely_private = st.session_state.get("key_q19_private")
    share_likely_public  = st.session_state.get("key_q20_public")
    report_misleading    = 1 if st.session_state.get("key_q21_report") == "Yes" else 0
    downrank_agree       = st.session_state.get("key_q22_downrank")
    watermark_action     = st.session_state.get("key_q23_watermark")

    # Candidate position AFTER clip (selectbox key_q0)
    candidate_position_after = st.session_state.get("key_q0")

    # Emotions now 1..10 (not booleans)
    em_anger       = st.session_state.get("key_em_anger")
    em_fear        = st.session_state.get("key_em_fear")
    em_disgust     = st.session_state.get("key_em_disgust")      # not displayed now, but kept for schema compat
    em_sadness     = st.session_state.get("key_em_sadness")      # not displayed now, but kept for schema compat
    em_enthusiasm  = st.session_state.get("key_em_enthusiasm")
    em_pride       = st.session_state.get("key_em_pride")

    # Topics (after-clip)
    mip_selected = st.session_state.get("key_mip_topics", [])
    mip_str = ", ".join(mip_selected) if mip_selected else None

    # Threats
    perceived_threat = st.session_state.get("key_perceived_threat")
    identity_threat  = st.session_state.get("key_identity_threat")

    # Salience before/after
    salience_before = st.session_state.get("key_salience_before")
    salience_after  = st.session_state.get("key_salience_topic_after")  # note: widget key for "after"

    # Simple completeness bump (optional)
    required = [
        candidate_position_after, res_q1, res_q2, res_q3, res_q4, res_q5, res_q6, res_q7, res_q8, res_q9, res_q10,
        res_q11, res_q12, res_q13, res_q14, res_q15, res_q16, res_q17,
        share_likely_private, share_likely_public, report_misleading, downrank_agree, watermark_action,
        em_anger, em_fear, em_enthusiasm, em_pride, perceived_threat, identity_threat, salience_before, salience_after
    ]
    if all(v is not None for v in required):
        st.session_state["count"] += 1

    # Write
    insert_rating(
        participant_id=participant_id,
        audio_clip_id=st.session_state["audio_clip_id"],
        speech_clarity=res_q1,
        speech_persuasiveness=res_q2,
        speech_pace_engagement=res_q3,
        speaker_trustworthiness=res_q4,
        speech_trustworthiness=res_q5,
        speaker_competence=res_q6,
        speech_speed_influence=res_q7,
        pitch_sincerity_effect=res_q8,
        loudness_attention_influence=res_q9,
        realness_scale=res_q10,
        realness_perception=res_q11,
        influenced_by_tone=res_q12,
        influenced_by_quality=res_q13,
        influenced_by_content=res_q14,
        confidence_level=res_q15,
        policy_agreement=res_q16,
        likelihood_to_vote=res_q17,
        open_ended_response=res_q18,
        check=check_val,
        group_no=group_no,
        share_likely_private=share_likely_private,
        share_likely_public=share_likely_public,
        report_misleading=report_misleading,
        downrank_agree=downrank_agree,
        watermark_action=watermark_action,
        candidate_position_after=candidate_position_after,
        em_anger=em_anger,
        em_fear=em_fear,
        em_disgust=em_disgust,
        em_sadness=em_sadness,
        em_enthusiasm=em_enthusiasm,
        em_pride=em_pride,
        mip_topics=mip_str,
        perceived_threat=perceived_threat,
        identity_threat=identity_threat,
        salience_before=salience_before,
        salience_after=salience_after,
    )

    mark_as_rated(st.session_state["audio_clip_id"])


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
            result = db_conn.execute(query, {"group_no": group_no})
        sample_row = result.fetchone()

        if not sample_row:
            st.error("No audio found for this group. Please try again later.")
            st.stop()

        audio_clip_id, url, topic = sample_row
        st.session_state["audio_clip_id"] = audio_clip_id
        st.session_state["current_topic"] = topic if topic else "this topic"



        st.warning(
            "⚠️ Please answer **every question** carefully before submitting. "
            "If you skip or miss any question, the page will reload and your answers for this clip will be lost."
        )
        st.info("💡 Tip: Scroll carefully and make sure each question has a selected option before clicking **Submit and View Next**.")
       # st.success("######")

        # BEFORE: Most important problem(s)
        st.markdown(
            '<h5>❓What is the most important problem facing the US right now? (Select all that apply)</h5>',
            unsafe_allow_html=True,
        )
        topics_all = list(
            dict.fromkeys(
                [
                    "Immigration",
                    "National Security",
                    "Economy",
                    "Racism",
                    "Climate",
                    "Education",
                    "Gender",
                    "Government / Poor leadership",
                    "Elections / Democracy",
                    "Crime & Public safety",
                    "Healthcare",
                    "Poverty / Homelessness",
                    "Unifying the country",
                ]
            )
        )
        topics_all.append("Other")
        mip_selected_before = st.multiselect(
            "", topics_all, default=[], key="key_mip_topics_before"
        )
        # (Note: not stored in DB by your schema; keep if you add a column later.)

        # Issue salience BEFORE listening
        st.markdown(
            f'<h5>❓ How important is this topic (<i>{st.session_state["current_topic"]}</i>) to you?</h5>',
            unsafe_allow_html=True,
        )
        salience_before = st.radio(
            "",
            options=list(range(1, 11)),
            horizontal=True,
            index=None,
            key="key_salience_before",
            label_visibility="collapsed",
        )
        st.info("1 = Not important at all, 10 = Extremely important")

        st.markdown(
            f'<h5>❓ What is <i>your personal stance</i> on this topic (<i>{st.session_state["current_topic"]}</i>)?</h5>',
            unsafe_allow_html=True,
        )
        stance_before = st.selectbox(
            "Select one option:",
            options=[
                "Supports stricter policies",
                "Supports more open policies",
                "Neutral / No clear position",
                "Not sure",
            ],
            index=None,
            key="key_stance_before",
            placeholder="Choose an option...",
        )

        st.success("######")
        st.markdown(
            '<h4>🔊 Listen to the audio clip of Kamala Harris or Donald Trump and answer the following questions about the audio clip.</h4>',
            unsafe_allow_html=True,
        )
        st.audio(url, format="audio/wav")
        st.info("❗If the audio isn't playing, refresh the page or try a different browser.")
        st.success("######")

        # Emotions (use 1..10 radios)
        st.markdown(
            """
            <style>
            div[role="radiogroup"] label p {
                font-size: 1rem !important;
                font-weight: 500 !important;
                margin-bottom: 4px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<h5>🎭 While listening to the clip, I felt...</h5>", unsafe_allow_html=True)

        EMOTIONS_TO_USE = ["em_anger", "em_fear", "em_enthusiasm", "em_pride"]
        EMOTION_LABELS = {
            "em_anger": "😡 Anger",
            "em_fear": "😨 Fear",
            "em_disgust": "🤢 Disgust",
            "em_sadness": "😢 Sadness",
            "em_enthusiasm": "🤩 Enthusiasm",
            "em_pride": "🦅 Pride",
        }

        cols = st.columns(2)
        for i, emo_key in enumerate(EMOTIONS_TO_USE):
            with cols[i % 2]:
                st.markdown(f"**{EMOTION_LABELS[emo_key]}**")
                st.radio(
                    "",
                    options=list(range(1, 11)),
                    horizontal=True,
                    index=None,
                    key=f"key_{emo_key}",
                )
                st.info("1 = Not at all, 10 = Extremely")

        # Threat & Identity threat
        st.markdown(
            '<h5>❓How serious a threat do you think the issue discussed in the clip is to the country?</h5>',
            unsafe_allow_html=True,
        )
        st.radio(
            "",
            options=list(range(1, 11)),
            horizontal=True,
            index=None,
            key="key_perceived_threat",
            label_visibility="collapsed",
        )
        st.info("1 = Not at all, 10 = Extremely")

        st.markdown(
            '<h5>❓How much did the clip make you feel that your social or political group was being disrespected?</h5>',
            unsafe_allow_html=True,
        )
        st.radio(
            "",
            options=list(range(1, 11)),
            horizontal=True,
            index=None,
            key="key_identity_threat",
            label_visibility="collapsed",
        )
        st.info("1 = Not at all, 10 = Extremely")

        st.success("######")

        # Candidate position (AFTER listening) — saved as candidate_position_after
        st.markdown(
            '<h5>❓What do you think the candidate’s position on this issue is?</h5>',
            unsafe_allow_html=True,
        )
        st.selectbox(
            "Select one option:",
            options=[
                "Supports stricter policies",
                "Supports more open policies",
                "Neutral / No clear position",
                "Not sure",
            ],
            index=None,
            key="key_q0",
            placeholder="Choose an option...",
        )

        # Agreement with position (optional display; not in DB schema)
        st.markdown("<h5>❓ How much do you agree with the candidate’s position on this issue?</h5>", unsafe_allow_html=True)
        st.radio(
            "",
            options=list(range(1, 11)),
            horizontal=True,
            index=None,
            key="key_persuasion",
            label_visibility="collapsed",
        )
        st.info("1 = Strongly Disagree, 10 = Strongly Agree")

        st.success("######")

        # Speech/perception items
        def ten_radio(key):
            return st.radio(
                "",
                options=list(range(1, 11)),
                horizontal=True,
                index=None,
                key=key,
                label_visibility="collapsed",
            )

        st.markdown("<h5>❓How clear was the speech?</h5>", unsafe_allow_html=True)
        ten_radio("key_q1")
        st.info("Clarity refers to how easily the speech can be understood. 1 = Not at all, 10 = Extremely")

        st.markdown("<h5>❓How persuasive was the speech?</h5>", unsafe_allow_html=True)
        ten_radio("key_q2")
        st.info("Persuasiveness refers to how convincing the speech felt. 1 = Not at all, 10 = Extremely")

        st.markdown("<h5>❓Was the pace of the speech engaging or distracting?</h5>", unsafe_allow_html=True)
        ten_radio("key_q3")
        st.info("1 = Distracting, 10 = Engaging")

        st.markdown("<h5>❓To what extent did the speaker seem trustworthy?</h5>", unsafe_allow_html=True)
        ten_radio("key_q4")
        st.info("1 = Not at all, 10 = Extremely")

        st.markdown("<h5>❓To what extent did you find the content of the speech trustworthy?</h5>", unsafe_allow_html=True)
        ten_radio("key_q5")
        st.info("1 = Not at all, 10 = Extremely")

        st.markdown("<h5>❓How would you rate the speaker’s competence?</h5>", unsafe_allow_html=True)
        ten_radio("key_q6")
        st.info("1 = Incompetent, 10 = Expert")

        st.markdown("<h5>❓How did the speed affect your understanding?</h5>", unsafe_allow_html=True)
        ten_radio("key_q7")
        st.info("1 = Confusing, 10 = Clear")

        st.markdown("<h5>❓Variations in pitch affected the speaker’s sincerity?</h5>", unsafe_allow_html=True)
        ten_radio("key_q8")
        st.info("1 = Not at all, 10 = Extremely")

        st.markdown("<h5>❓Changes in loudness and emphasis grabbed my attention.</h5>", unsafe_allow_html=True)
        ten_radio("key_q9")
        st.info("1 = Not at all, 10 = Completely")

        st.divider()

        # Real/Fake & drivers
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("<h5>❓Do you think the speech is real or fake?</h5>", unsafe_allow_html=True)
            st.radio(
                "",
                options=["Real", "Fake"],
                horizontal=True,
                index=None,
                key="key_q11",
                label_visibility="collapsed",
            )

        with col2:
            st.markdown(
                "<h5>❓What influenced your judgment about the authenticity of the clip?</h5>",
                unsafe_allow_html=True,
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                st.checkbox("The speaker’s tone of voice", key="key_q12")
            with c2:
                st.checkbox("The audio quality", key="key_q13")
            with c3:
                st.checkbox("The content of the audio clip", key="key_q14")

        st.markdown("<h5>❓On a scale from fake to real, how would you rate this audio?</h5>", unsafe_allow_html=True)
        ten_radio("key_q10")
        st.info("1 = Definitely Fake, 10 = Definitely Real")

        st.markdown("<h5>❓ How confident are you that this audio clip is real/fake?</h5>", unsafe_allow_html=True)
        ten_radio("key_q15")
        st.info("1 = Not at all, 10 = Completely")

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<h7>I am carefully rating, select 4 if yes.</h7>', unsafe_allow_html=True)
        st.radio(
            "",
            options=list(range(1, 11)),
            horizontal=True,
            index=None,
            key="key_check",
            label_visibility="collapsed",
        )

        st.markdown("<h5>❓To what extent do you agree with the policy in the audio clip?</h5>", unsafe_allow_html=True)
        ten_radio("key_q16")
        st.info("1 = Strongly Disagree, 10 = Strongly Agree")

        st.success("######")

        # Vote likelihood + extra perceptions (not stored unless you add columns)
        st.markdown(
            "<h5>❓Based on the speech you just heard, how likely are you to vote for this person?</h5>",
            unsafe_allow_html=True,
        )
        ten_radio("key_q17")
        st.info("1 = Not at all, 10 = Very Much")

        # Additional measures (displayed only). Add DB columns if you want to store.
        st.markdown(
            "<h5>❓How consistent do you think the candidate’s statements and actions are on this issue?</h5>",
            unsafe_allow_html=True,
        )
        ten_radio("key_cons")
        st.info("1 = Not at all, 10 = Very much")

        st.markdown(
            "<h5>❓From the audio clip, to what extent do you feel the candidate’s stance aligns with your own views?</h5>",
            unsafe_allow_html=True,
        )
        ten_radio("key_align")
        st.info("1 = Strongly Opposed, 10 = Strongly Aligned")

        st.markdown(
            "<h5>❓How confident are you in your assessment of the candidate’s position?</h5>",
            unsafe_allow_html=True,
        )
        ten_radio("key_conf")
        st.info("1 = Not Confident, 10 = Strongly Confident")

        # Sharing / platform policy
        st.success("######")
        st.markdown(
            '<h5>❓How likely are you to share this clip <i>privately</i> (📩🔒 WhatsApp, DM)?</h5>',
            unsafe_allow_html=True,
        )
        ten_radio("key_q19_private")
        st.info("1 = Not at all , 10 = Very Likely")

        st.markdown(
            '<h5>❓How likely are you to share this clip <i>publicly</i> (📢 social media post/story)?</h5>',
            unsafe_allow_html=True,
        )
        ten_radio("key_q20_public")
        st.info("1 = Not at all , 10 = Very Likely")

        st.markdown("<h5>❓Would you report this clip as misleading on platform 🆇 (Twitter)?</h5>", unsafe_allow_html=True)
        st.radio(
            "",
            options=["Yes", "No"],
            horizontal=True,
            index=None,
            key="key_q21_report",
            label_visibility="collapsed",
        )

        st.markdown(
            "<h5>❓ Platforms should downrank content flagged as AI-generated even if not deceptive.</h5>",
            unsafe_allow_html=True,
        )
        ten_radio("key_q22_downrank")
        st.info("1 = Strongly Disagree, 10 = Strongly Agree")

        st.markdown("<h5>❓If a watermark indicated this was synthetic, I would…</h5>", unsafe_allow_html=True)
        st.selectbox(
            "Select one option:",
            options=["Ignore", "Be cautious but still share", "Not share", "Report as misleading"],
            index=None,
            key="key_q23_watermark",
            placeholder="Choose an option...",
        )

        # AFTER: Topics
        st.success("######")
        st.markdown(
            '<h5>❓What is the most important problem facing the US right now? (Select all that apply)</h5>',
            unsafe_allow_html=True,
        )
        mip_selected = st.multiselect("", topics_all, default=[], key="key_mip_topics")

        # AFTER: Issue salience
        st.markdown(
            f'<h5>❓ How important is this topic (<i>{st.session_state["current_topic"]}</i>) to you?</h5>',
            unsafe_allow_html=True,
        )
        st.radio(
            "",
            options=list(range(1, 11)),
            horizontal=True,
            index=None,
            key="key_salience_topic_after",
            label_visibility="collapsed",
        )
        st.info("1 = Not important at all, 10 = Extremely important")

        st.markdown(
            f'<h5>❓ What is <i>your personal stance</i> on this topic (<i>{st.session_state["current_topic"]}</i>)?</h5>',
            unsafe_allow_html=True,
        )
        stance_after = st.selectbox(
            "Select one option:",
            options=[
                "Supports stricter policies",
                "Supports more open policies",
                "Neutral / No clear position",
                "Not sure",
            ],
            index=None,
            key="key_stance_after",
            placeholder="Choose an option...",
        )

        st.markdown("<h5>Optional Open-Ended Question</h5>", unsafe_allow_html=True)
        st.text_area(
            "Did anything stand out or seem interesting to you? If so, why?",
            help="Feel free to share any thoughts or impressions you found particularly interesting about the audio.",
            key="key_q18",
        )

        st.divider()
        st.form_submit_button("**Submit and View Next**", on_click=save_to_db)

        # Optional: bump count only when a core set is answered
        core_keys = [
            # ---- Pre-clip section ----
            "key_mip_topics_before",      # important problems before
            "key_salience_before",        # topic importance before
            "key_stance_before",          # stance before listening

            # ---- Emotion section ----
            "key_em_anger",
            "key_em_fear",
            "key_em_enthusiasm",
            "key_em_pride",

            # ---- Threat perception ----
            "key_perceived_threat",
            "key_identity_threat",

            # ---- Candidate & speech perceptions ----
            "key_q0",  # candidate position
            "key_q1",  # speech clarity
            "key_q2",  # speech persuasiveness
            "key_q3",  # speech pace engagement
            "key_q4",  # speaker trustworthiness
            "key_q5",  # content trustworthiness
            "key_q6",  # speaker competence
            "key_q7",  # speed effect
            "key_q8",  # pitch sincerity
            "key_q9",  # loudness attention
            "key_q10", # realness scale
            "key_q11", # real/fake choice
            "key_q15", # confidence real/fake
            "key_q16", # policy agreement
            "key_q17", # likelihood to vote

            # ---- Sharing & governance ----
            "key_q19_private",
            "key_q20_public",
            "key_q21_report",
            "key_q22_downrank",
            "key_q23_watermark",

            # ---- Post-clip wrap-up ----
            "key_mip_topics",             # most important problem after
            "key_salience_topic_after",   # importance after
            "key_stance_after",           # stance after
        ]
        if all(st.session_state.get(k) is not None for k in core_keys):
            st.session_state["count"] += 0  # already incremented inside save_to_db when complete

    except SQLAlchemyError as e:
        st.error(f"Database query failed: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# Finish / route
if st.session_state["count"] < 1:
    st.write("Please rate the audio and answer all questions to finish the survey.")
    st.write(f"You have rated {st.session_state['count']} audios so far.")
else:
    st.write("You have rated the audio and you can finish your participation now.")
    st.switch_page("pages/Demographics.py")
