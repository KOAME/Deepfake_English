import streamlit as st
import streamlit_survey as ss
import json
import pandas as pd
from sqlalchemy import create_engine, text
import pymysql
import sqlalchemy
import os
import pymysql
from sshtunnel import SSHTunnelForwarder
from fabric import Connection


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

### Set up SSH connection and port forwarding
conn = Connection(
    host=ssh_host,
    port=ssh_port,
    user=ssh_user,
    connect_kwargs={"password": ssh_password},
    connect_timeout=3600
)

# Create SSH Tunnel
tunnel = SSHTunnelForwarder(
    (ssh_host, ssh_port),
    ssh_username=ssh_user,
    ssh_password=ssh_password,
    remote_bind_address=(db_host, db_port)
)
tunnel.start()

# Function to create a new database connection
def getconn():
    conn = pymysql.connect(
        host='127.0.0.1',
        user=db_user,
        password=db_password,
        database=db_name,
        port=tunnel.local_bind_port,
        connect_timeout=3600
    )
    return conn

# Create a SQLAlchemy engine
pool = create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

def update_participant(participant_id, age, gender_identity, country_of_residence, ancestry, ethnicity, political_party, political_spectrum):
    update_query = text("""
    UPDATE df_participants
    SET age = :age,
        gender_identity = :gender_identity,
        country_of_residence = :country_of_residence,
        ancestry = :ancestry,
        ethnicity = :ethnicity,
        political_party = :political_party,
        political_spectrum = :political_spectrum
    WHERE participant_id = :participant_id
    """)
    with pool.connect() as connection:
        connection.execute(update_query, {
            'participant_id': participant_id,
            'age': age,
            'gender_identity': gender_identity,
            'country_of_residence': country_of_residence,
            'ancestry': ancestry,
            'ethnicity': ethnicity,
            'political_party': political_party,
            'political_spectrum': political_spectrum
        })

##start survey
survey = ss.StreamlitSurvey("demographics_survey")

#load data
df_countries = pd.read_csv("https://raw.githubusercontent.com/DALIAALISIDDIG/Aligniverse_Gender_English/refs/heads/main/aligniverse_gender-main/UNSD_Methodology_ancestry.csv", sep = ";")

age_groups = ["I wish not to declare","18-30", "31-40", "41-50","51-60", "60<"]
pronouns = [
    "I wish not to declare",
    "she/her/hers",
    "he/him/his",
    "they/them/theirs",
    "ze/hir/hirs",
    "xe/xem/xyrs",
    "ey/em/eirs",
    "ve/ver/vis",
    "per/pers/perself"
]
racial_groups = [
    "I wish not to declare",
    "American Indian or Alaska Native",
    "Asian",
    "Black or African American",
    "Hispanic or Latino",
    "Middle Eastern or North African",
    "Native Hawaiian or Pacific Islander",
    "White"
]

political_parties = [
    "I wish not to declare",
    "Democrats",
    "Republicans"
]

list_countries = sorted(df_countries["Country or Area"].to_list())
list_countries.insert(0, "I wish not to declare")

st.title("You at Aligniverse")
st.write("Your ratings will contribute to the development of an open-source dataset, which AI practitioners can utilize to align their LLMs. For the creation of this dataset, it's important for us to gather some information about you to determine the specific demographic group you represent. Since demographic data will be aggregated, identifying individual participants will not be possible.")

q1_demo = survey.selectbox("Which age group do you belong to?", options=age_groups, id="Q1_demo", index=None)
q2_demo = survey.selectbox("What pronouns do you use to identify yourself?", options=pronouns, id="Q2_demo", index=None)

q3_demo = survey.multiselect("Which is your country of residence?", options=list_countries, id="Q3_demo", max_selections = 3)
q3_demo_str = json.dumps(q3_demo)

q4_demo = survey.multiselect("Where do your ancestors (e.g., great-grandparents) come from?", options=list_countries, id="Q4_demo", max_selections = 3)
q4_demo_str = json.dumps(q4_demo)

q5_demo = survey.multiselect("Which racial group(s) do you identify with?", options=racial_groups, id="Q5_demo", max_selections = 3)
q5_demo_str = json.dumps(q5_demo)

q6_demo = survey.selectbox("Which political party would you be most likely to vote for?", options=political_parties, id="Q6_demo", index=None)

q7_demo = survey.select_slider("Where do you see yourself on the political spectrum?", options=["Liberal", "Rather liberal", "Centre", "Rather conservative", "Conservative"], id="Q7_demo")

def get_last_id():
    with pool.connect() as connection:
        last_id_query = text("SELECT LAST_INSERT_ID()")
        last_id_result = connection.execute(last_id_query)
        last_id = last_id_result.scalar()
        return last_id

if 'participant_id' not in st.session_state:
    last_id = get_last_id()
    st.session_state['participant_id'] = last_id

if not all([q1_demo, q2_demo, q3_demo, q4_demo, q5_demo, q6_demo, q7_demo]):
    st.write("Please select at least one option for every question. You always have the option not to declare.")

elif all([q1_demo, q2_demo, q3_demo, q4_demo, q5_demo, q6_demo, q7_demo]):
    if st.button("Submit"):
        update_participant(
            st.session_state['participant_id'], #participant
            q1_demo, #age
            q2_demo, #gender identity
            q3_demo_str, #country of residence
            q4_demo_str, #ancestry
            q5_demo_str,  #ethnicity
            q6_demo, #political party
            q7_demo #political spectrum
        )
        st.switch_page("pages/End_participation.py")
