import streamlit as st

# Set the title of the app
st.title('Simple Streamlit Test App')

# Add a text input box
user_input = st.text_input('Enter your name:')

# Add a button
if st.button('Submit'):
    st.write(f'Hello, {user_input}! Welcome to the Streamlit test app.')

# Add a slider
slider_value = st.slider('Select a value:', 0, 100, 50)
st.write(f'The selected value is: {slider_value}')

# Display a line chart
import numpy as np
import pandas as pd

chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['A', 'B', 'C']
)
st.line_chart(chart_data)
