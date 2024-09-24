import streamlit as st
import streamlit_survey as ss
import streamlit_scrollable_textbox as stx

import json
import pandas as pd
from sqlalchemy import create_engine, text

import pymysql
import sqlalchemy
import os
import pymysql
from sshtunnel import SSHTunnelForwarder
from fabric import Connection


##set config
# Set the page config at the top of the file
st.set_page_config(
    page_title="Aligniverse",
    page_icon="🌍",
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
survey = ss.StreamlitSurvey("Survey Aligniverse")

st.title("Welcome to Aligniverse")
    
text1 = "Hi, great to see you today! Aligniverse is a research project with the mission to help align Large Language Models (LLMs) in a way that fosters positivity and reduces discrimination towards minority groups."
st.write(text1)

text2 = "LLMs are advanced computer programs designed to understand and generate human-like text based on the data they have been trained on. Alignment refers to the process of ensuring that these models behave in a way that is consistent with human values and ethical principles. In light of this, we need your help – how can we guide LLMs to answer controversial questions appropriately?"
st.write(text2)

text3 = "Join our study to review and evaluate LLM-generated texts on sensitive topics. We will publish the collected ratings as an alignment dataset for the community."
st.write(text3)

text4 = "Participating typically takes between 10 and 30 minutes. You can rate as many texts as you prefer, and we appreciate your willingness to contribute."
st.write(text4)

st.divider()

st.subheader("Participant information and consent form")
st.write("We are committed to safeguarding your privacy. Please review the study terms.")
if st.button("Review general information and consent form"):
    #st.switch_page("pages/Study_terms.py")
    
    content = """**Participant information and consent form for Aligniverse** 
    Dear participants, we invite you to take part in our research study. You will find all relevant information in the participant information form below. Please review it carefully, and we are available for any questions you may have.
    Our goal is to recruit about 10,000 participants across more than five locations. At the Technical University of Munich (TUM), we intend to recruit around 1,000 participants. The study was planned by TUM and will be carried out in cooperation with Eidgenössiche Technische Hochschule (ETH), with funding from our institute.
    Participation in the study is voluntary. If you do not wish to participate or if you later withdraw your consent, you will not suffer any disadvantages.
    
    **Why do we conduct this study?**
    Our mission involves collecting data to align Large Language Models (LLMs) in a way that fosters positivity and reduces discrimination, particularly towards minority groups. In light of this, we're curious about your opinion. How do you envision an LLM responding to sensitive questions? 
    Throughout the study, you will review different texts created by large language models (LLMs) that cover sensitive topics. Your task will be to evaluate these texts based on several criteria. We will publish these ratings as an alignment dataset and share it with the community. This dataset can be utilized by practitioners to improve the alignment of LLMs.
    
    **How does the study proceed?**
    Participating typically takes between 10 and 30 minutes. Rating one pre-generated text is expected to take 10 minutes. You're welcome to rate as many texts as you prefer, and we truly appreciate your willingness to contribute.
    
    **Is there a personal benefit from participating in this study?**
    You will not benefit from participating in this study. However, the results of the study may help other people in the future.
    What risks are associated with participating in the study?
    The texts shown may contain stereotypes and discrimination, which may evoke negative feelings in you. For any questions and suggestions regarding the texts, you can contact us anytime at the email address mwieland@ethz.ch. In emergencies, please contact the following organizations:
    (1) Germany: Telefonseelsorge (telephone counseling) at +49 800 111 0 111
    (2) Switzerland: Dargebotene Hand at +41 143

    **Who can I contact if I have further questions?**
    If you have further questions, please contact: Michèle Wieland, mwieland@ethz.ch
    
    **Information on data protection**
    In this study, Orestis Papakyriakopoulos is responsible for data processing. The legal basis for processing is personal consent (Art. 6 para. 1 lit. a, Art. 9 para. 2 lit. a GDPR). The data will be treated confidentially at all times. The data will be collected solely for the purpose of the study described above and will only be used within this framework. We do not collect personal data. We do collect additional sensitive personal data. These include age, gender identification, country of residence, ancestry, and ethnic affiliation. All data will be collected anonymously. This means that no one, including the study leaders, can determine to whom the data belongs. 
    The data will be stored on a server of TUM. We do not transfer your data to other institutions in Germany, the EU, or to a third country outside the EU, nor to an international organization. The research data may be used for scientific publications and/or made available to other researchers in scientific databases indefinitely. The data will be used in a form that does not allow any conclusions to be drawn about the individual study participants (anonymized). 
    Consent to the processing of your data is voluntary. You can withdraw your consent at any time without providing reasons and without any disadvantages for you. After withdrawal, no further data will be collected. The lawfulness of the processing carried out based on the consent until the withdrawal remains unaffected. You have the right to obtain information about the data, including a free copy. Furthermore, you can request the correction, blocking, restriction of processing, or deletion of the data, and, if applicable, the transfer of the data. In these cases, please contact:  Prof. Dr. Orestis Papakyriakopoulos, orestis.p(at)tum.de
    However, after anonymization, the data can no longer be attributed to an individual. Once anonymization has taken place, it is no longer possible to access, block, or delete the data. For questions regarding data processing and compliance with data protection regulations, the following data protection officer is available:
    Official Data Protection Officer of the Technical University of Munich
    Postal address: Arcisstr. 21, 80333 München
    Phone: 089/289-17052
    E-Mail: beauftragter@datenschutz.tum.de
    You also have the right to file a complaint with any data protection supervisory authority. A list of supervisory authorities in Germany can be found at: https://www.bfdi.bund.de/DE/Infothek/Anschriften_Links/anschriften_links-node.html
    """
    stx.scrollableTextbox(content, height = 150)

## include consent questions plus information about contact
st.subheader("Consent to participate")
st.write("I have been informed about the study by the study team. I have received and read the written information and consent form for the study mentioned above. I have been thoroughly informed about the purpose and procedure of the study, the chances and risks of participation, and my rights and responsibilities. My consent to participate in the study is voluntary. I have the right to withdraw my consent at any time without giving reasons, and without any disadvantages to myself arising from this.")
consent1 = survey.checkbox("I hereby consent to participate in the study.")
st.write("The processing and use of personal data for the study mentioned above will be carried out exclusively as described in the study information. The collected and processed personal data include, in particular, ethnic origin.")
consent2 = survey.checkbox("I hereby consent to the described processing of my personal data.")
consent3 = survey.checkbox("I confirm that I am at least 18 years old.")

# SSH and Database credentials
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
    connect_timeout=6600,
    read_timeout=800,
    write_timeout=800,
    max_allowed_packet=64 * 1024 * 1024  # 64MB
    
)

# Set up port forwarding
tunnel = SSHTunnelForwarder(
    (ssh_host, ssh_port),
    ssh_username=ssh_user,
    ssh_password=ssh_password,
    remote_bind_address=(db_host, db_port)
    
)
tunnel.start()

def getconn():
    conn = pymysql.connect(
        host='127.0.0.1',
        user=db_user,
        password=db_password,
        database=db_name,
        port=tunnel.local_bind_port,
        connect_timeout=6600
        read_timeout=800,
        write_timeout=800,
        max_allowed_packet=64 * 1024 * 1024  # 64MB
    )
    return conn

pool = create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

# Function to insert a participant and get the last inserted ID
def insert_participant_and_get_id():
    with pool.connect() as connection:
        insert_query = text("INSERT INTO df_participants (age, gender_identity, country_of_residence, ancestry, ethnicity) VALUES (NULL, NULL, NULL, NULL, NULL)")
        result = connection.execute(insert_query)
        last_id_query = text("SELECT LAST_INSERT_ID()")
        last_id_result = connection.execute(last_id_query)
        last_id = last_id_result.scalar()
        
        return last_id

def insert_prolific_id(participant_id, prolific_id):
    insert_query = """
    INSERT INTO df_prolific_ids (
        participant_id,
        prolific_id
    ) VALUES (%s, %s)
    """
    with pool.connect() as db_conn:
        db_conn.execute(insert_query, (
            participant_id,
            prolific_id
        ))

if not all([consent1, consent2, consent3]):
    st.write("Please give your consent by ticking all three boxes.")

elif all([consent1, consent2, consent3]):
    st.write("Please enter your unique Prolific ID such that we can record your participation.")
    prolific_id = st.text_input("Enter your unique Prolific ID:", max_chars=50)
    if st.button("Submit ID"):
        if prolific_id:
            last_inserted_id = insert_participant_and_get_id()
            insert_prolific_id(last_inserted_id, prolific_id)
            st.session_state['participant_id'] = last_inserted_id
        else:
            st.write("Please enter your Prolific ID to continue.")

if 'participant_id' in st.session_state:
    st.write("Let's create a better dataset!")
    st.switch_page("pages/Rate_responses.py")
