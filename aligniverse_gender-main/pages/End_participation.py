import streamlit as st
import streamlit_survey as ss


st.title("Thank you!")
st.write("Thank you for being part of our study and helping us improve the alignment of Large Language Models.")
st.balloons()

st.write("By clicking the following button, you will be redirected back to Prolifics such that your submission can be counted.")
st.link_button("Redirect to Prolifics", "https://app.prolific.com/submissions/complete?cc=CGNYTYYO")

st.write("Or you can copy the following code: CGNYTYYO")
