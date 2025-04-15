import streamlit as st
import streamlit_survey as ss
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
    

st.title("Thank you!")
st.write("Thank you for being part of our study.")
st.balloons()

st.write("By clicking the following button, you will be redirected back to Prolifics such that your submission can be counted.")
st.link_button("Redirect to Prolifics", "https://app.prolific.com/submissions/complete?cc=CXUNA9UH")

st.write("Or you can copy the following code: CXUNA9UH ")
