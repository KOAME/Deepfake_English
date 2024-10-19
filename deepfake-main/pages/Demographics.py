import streamlit as st
import streamlit_survey as ss
import json
import time

from sqlalchemy import create_engine, text
import pymysql
from sshtunnel import SSHTunnelForwarder
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

st.set_page_config(
    initial_sidebar_state="collapsed"  # Collapsed sidebar by default
)

# Initialize session state for sidebar state if not already set
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

###################################################################################
age_group_list = ["18-30", "31-40", "41-50", "51-60", "60<"]

pronoun_list = [
    "she/her/hers",
    "he/him/his",
    "they/them/theirs",
    "ze/hir/hirs",
    "xe/xem/xyrs",
    "ey/em/eirs",
    "ve/ver/vis",
    "per/pers/perself"
]

educational_background_list = [
    "High school or equivalent",
    "Associate degree",
    "Bachelor's degree",
    "Master's degree",
    "Doctorate",
    "Professional degree",
    "No degree"
]

occupation_list = [
    "Information Technology (IT) & Software",
    "Healthcare & Medical",
    "Education & Training",
    "Engineering & Architecture",
    "Business & Management",
    "Finance & Accounting",
    "Sales & Marketing",
    "Arts, Design & Media",
    "Law & Legal Services",
    "Trades & Construction",
    "Hospitality & Food Services",
    "Retail & Customer Service",
    "Transportation & Logistics",
    "Science & Research",
    "Government & Public Sector",
    "Real Estate & Property Management",
    "Manufacturing & Production",
    "Freelance & Self-employed",
    "Student",
    "Unemployed"
    "Other"
]

race_list = [
    "American Indian or Alaska Native",
    "Asian",
    "Black or African American",
    "Hispanic or Latino",
    "Middle Eastern or North African",
    "Native Hawaiian or Pacific Islander",
    "White"
]

mother_tongue_list = [
    "English", "Spanish", "Chinese (Mandarin)", "Hindi", "Arabic", "French",
    "Bengali", "Russian", "Portuguese", "Indonesian", "Japanese", "German",
    "Korean", "Turkish", "Vietnamese", "Italian", "Tamil", "Urdu", "Persian (Farsi)",
    "Punjabi", "Javanese", "Telugu", "Marathi", "Thai", "Dutch", "Swedish",
    "Greek", "Polish", "Czech", "Hungarian", "Romanian", "Ukrainian", "Hebrew",
    "Malay", "Burmese", "Hausa", "Igbo", "Yoruba", "Swahili", "Tagalog (Filipino)",
    "Nepali", "Sinhala", "Amharic", "Zulu", "Somali", "Pashto", "Kazakh", "Uzbek",
    "Khmer", "Lao", "Finnish", "Danish", "Norwegian", "Slovak", "Croatian",
    "Bulgarian", "Serbian", "Lithuanian", "Latvian", "Estonian", "Georgian",
    "Armenian", "Mongolian", "Bosnian", "Azerbaijani", "Macedonian", "Albanian",
    "Malayalam", "Kannada", "Gujarati", "Oriya (Odia)", "Other (Please Specify)",
]

languages_spoken_list = ["1", "2", "3", "4", "5", "More than 5"]

political_party_list = [
    "Democrats",
    "Republicans"
]

political_inclination_list = [
    "Liberal",
    "Rather liberal",
    "Center",
    "Rather conservative",
    "Conservative"
]

listening_habit_list = [
    "Symphonies",
    "Audiobooks",
    "Podcasts",
    "Music",
    "Nature Sounds",
    "White Noise",
    "Other"
]

tech_savy_list = [
    "Very comfortable",
    "Comfortable",
    "Somewhat comfortable",
    "Not very comfortable",
    "Not comfortable at all"
]

ai_level_list = [
    "No Experience",
    "Beginner",
    "Intermediate",
    "Advanced",
    "Expert"
]

media_consumption_list = [
    "News junkie",
    "Series binge-watcher",
    "Bookworm",
    "Social media scroller",
    "Podcast listener",
    "Casual viewer",
    "Other"
]

# Load data with error handling
try:
    df_countries = pd.read_csv(
        "https://raw.githubusercontent.com/DALIAALISIDDIG/Aligniverse_Gender_English/refs/heads/main/aligniverse_gender-main/UNSD_Methodology_ancestry.csv",
        sep=";"
    )
except Exception as e:
    st.error(
        "Failed to connect to the database after multiple retries -Data. Please Return the study and check your network!")
    st.stop()

country_list = sorted(df_countries["Country or Area"].to_list())


###################################################################################


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


# Set up SSH tunnel with retry logic
def start_ssh_tunnel():
    try:
        tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(db_host, db_port),
            set_keepalive=30  # Keeps SSH connection alive
        )
        tunnel.start()
        return tunnel
    except Exception as e:
        st.error(f"SSH tunnel connection failed: {e}")
        raise


# Establish a database connection with retries
def get_connection(tunnel, retries=3, delay=5):
    for attempt in range(retries):
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
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                st.error("Failed to connect to the database after multiple retries. Please check your network.")
                raise


# Create SQLAlchemy engine with retry and connection pooling
def create_engine_with_pool(tunnel):
    try:
        pool = create_engine(
            "mysql+pymysql://",
            creator=lambda: get_connection(tunnel),
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycles connections every hour
            pool_size=3000,  # Set pool size to handle multiple connections
            max_overflow=3000  # Allow 10 extra simultaneous connections if needed
        )
        return pool
    except Exception as e:
        st.error(f"Error creating database engine: {e}")
        st.stop()


# Start SSH Tunnel and set up DB pool
tunnel = start_ssh_tunnel()
pool = create_engine_with_pool(tunnel)


# Database operations with error handling
def update_participant(participant_id, age_group, gender, education, occupation,
                       country_of_residence,
                       nationality, race,
                       native_tongue, languages_spoken, political_party,
                       political_inclination,
                       listening_habits,
                       tech_savy,
                       ai_experience,
                       media_consumption):
    update_query = text("""
    UPDATE participants
    SET age_group = :age_group,
        gender = :gender,
        education = :education,
        occupation = :occupation,
        country_of_residence = :country_of_residence,
        nationality = :nationality,
        race = :race,
        native_tongue = :native_tongue,
        languages_spoken = :languages_spoken,
        political_party = :political_party,
        political_inclination = :political_inclination,
        listening_habits = :listening_habits,
        tech_savy = :tech_savy,
        ai_experience = :ai_experience,
        media_consumption = :media_consumption
    WHERE participant_id = :participant_id
    """)

    try:
        with pool.connect() as connection:

            connection.execute(update_query, {
                'participant_id': participant_id,
                'age_group': age_group,
                'gender': gender,
                'education': education,
                'occupation': occupation,
                'country_of_residence': country_of_residence,
                'nationality': nationality,
                'race': race,
                'native_tongue': native_tongue,
                'languages_spoken': languages_spoken,
                'political_party': political_party,
                'political_inclination': political_inclination,
                'listening_habits': listening_habits,
                'tech_savy': tech_savy,
                'ai_experience': ai_experience,
                'media_consumption': media_consumption
            })

            connection.commit()

    except SQLAlchemyError as e:
        st.error(f"Database update failed: {e}")
    except Exception as e:
        st.error(
            "Failed to connect to the database after multiple retries - Update. Please Return the study and check your network!")


# Start Survey
survey = ss.StreamlitSurvey("demographics_survey")

st.title("You at Deepfakes")
st.write(
    "Your ratings will contribute to the development of an open-source dataset, which AI practitioners can utilize to align their LLMs. For the creation of this dataset, it's important for us to gather some information about you to determine the specific demographic group you represent. Since demographic data will be aggregated, identifying individual participants will not be possible.")

# Demographics Questions

# Age Group
q_age = survey.selectbox("Which age group do you belong to?", options=age_group_list, id="q_age",
                         index=None)

# Gender
q_gender = survey.selectbox("What pronouns do you use to identify yourself?", options=pronoun_list,
                            id="q_gender",
                            index=None)

# Education
q_education = survey.selectbox("What's your educational background?", options=educational_background_list,
                               id="q_education",
                               index=None)

# Occupation
q_occupation = survey.selectbox("What's your profession?", options=occupation_list,
                                id="q_occupation", index=None)

# Country of Residence
q_residence = survey.selectbox("Which is your country of residence?", options=country_list,
                               id="q_residence", index=None)

# Nationality
q_nationality = survey.multiselect("Where do your ancestors (e.g., great-grandparents) come from?",
                                   options=country_list,
                                   id="q_nationality", max_selections=3)
q_nationality_str = json.dumps(q_nationality)

# Race
q_race = survey.multiselect("Which racial group(s) do you identify with?", options=race_list,
                            id="q_race",
                            max_selections=3)
q_race_str = json.dumps(q_race)

# Native Tongue
q_native_tongue = survey.multiselect("What's your mother tongue?", options=mother_tongue_list,
                                     id="q_native_tongue",
                                     max_selections=3)
q_native_tongue_str = json.dumps(q_native_tongue)

# Languages Spoken
q_languages_spoken = survey.selectbox("How many languages can you speak fluently?",
                                      options=languages_spoken_list, id="q_languages_spoken", index=None)

# Political Party
q_political_party = survey.selectbox("Which political party would you be most likely to vote for?",
                                     options=political_party_list,
                                     id="q_political_party", index=None)

# Political Inclination
q_political_inclination = survey.select_slider("Where do you see yourself on the political spectrum?",
                                               options=political_inclination_list,
                                               id="q_political_inclination")

# Listening Habits
q_listening_habits = survey.selectbox(
    "What's your preferred listening pleasure? Symphonies, audiobooks, or something else?",
    options=listening_habit_list, id="q_listening_habits", index=None)

# Tech Savy
q_tech_savy = survey.selectbox("How comfortable are you with technology?", options=tech_savy_list,
                               id="q_tech_savy", index=None)

# AI Experience
q_ai_experience = survey.selectbox("Have you ever explored artificial intelligence?",
                                   options=ai_level_list, id="q_ai_experience", index=None)

# Media Consumption
q_media_consumption = survey.selectbox("How do you consume media? News junkie, series binge-watcher, or bookworm?",
                                       options=media_consumption_list, id="q_media_consumption", index=None)


# Submission handler
def get_last_id():
    try:
        with pool.connect() as connection:
            last_id_query = text("SELECT LAST_INSERT_ID()")
            result = connection.execute(last_id_query)
            return result.scalar()
    except SQLAlchemyError as e:
        st.error(f"Failed to fetch participant ID: {e}")
        return None
    except Exception as e:
        st.error(
            "Failed to connect to the database after multiple retries - ID. Please Return the study and check your network!")
        return None


if 'participant_id' not in st.session_state:
    last_id = get_last_id()
    st.session_state['participant_id'] = last_id

if not all(
        [q_age, q_gender, q_education, q_occupation, q_residence, q_nationality_str, q_race_str, q_native_tongue,
         q_languages_spoken, q_political_party, q_political_inclination, q_listening_habits, q_tech_savy,
         q_ai_experience, q_media_consumption]):
    st.write("Please select at least one option for every question.")

elif all([q_age, q_gender, q_education, q_occupation, q_residence, q_nationality_str, q_race_str, q_native_tongue,
          q_languages_spoken, q_political_party, q_political_inclination, q_listening_habits, q_tech_savy,
          q_ai_experience, q_media_consumption]):

    if st.button("Submit"):
        update_participant(
            st.session_state['participant_id'],  # participant
            q_age,  # Age Group
            q_gender,  # Gender
            q_education,  # Education
            q_occupation,  # Occupation
            q_residence,  # Country of Residence
            q_nationality_str,  # Nationality
            q_race_str,  # Race
            q_native_tongue_str,  # Native Tongue
            q_languages_spoken,  # Languages Spoken
            q_political_party,  # Political Party
            q_political_inclination,  # Political Inclination
            q_listening_habits,  # Listening Habits
            q_tech_savy,  # Tech Savy
            q_ai_experience,  # AI Experience
            q_media_consumption,  # Media Consumption
        )
        # Closed for test
        st.switch_page("pages/End_participation.py")
