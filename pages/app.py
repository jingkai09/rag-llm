# app.py
import streamlit as st
import requests
import time
from requests.exceptions import RequestException

# Configuration
MAX_RETRIES = 5
RETRY_DELAY = 2

def make_request_with_retry(method, url, **kwargs):
    for attempt in range(MAX_RETRIES):
        try:
            response = method(url, **kwargs)
            if response.status_code != 502:
                return response
            if attempt < MAX_RETRIES - 1:
                with st.spinner(f'Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})'):
                    time.sleep(RETRY_DELAY)
        except RequestException as e:
            if attempt < MAX_RETRIES - 1:
                with st.spinner(f'Connection error. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})'):
                    time.sleep(RETRY_DELAY)
            else:
                raise e
    return response

# Page configuration
st.set_page_config(
    page_title="RAG Setup",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'server_url' not in st.session_state:
    st.session_state.server_url = ""
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'chatbot_id' not in st.session_state:
    st.session_state.chatbot_id = None

st.title("RAG System Setup")

# Server Configuration
st.subheader("Server Configuration")
input_url = st.text_input("Server URL:", value=st.session_state.server_url, 
                         help="Example: http://localhost:8000")

if input_url != st.session_state.server_url:
    st.session_state.server_url = input_url

if not st.session_state.server_url:
    st.warning("Please enter your server URL to begin.")
    st.stop()

# User Management
st.subheader("User Setup")
col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Create New User")
    new_user_name = st.text_input("Enter username")
    if st.button("Create User"):
        try:
            response = make_request_with_retry(
                requests.post,
                f"{st.session_state.server_url}/users",
                data={"name": new_user_name}
            )
            if response.status_code == 200:
                st.success(f"User created! ID: {response.json()['id']}")
                st.session_state.user_id = response.json()['id']
            else:
                st.error(f"Failed to create user: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col2:
    st.markdown("##### Existing User")
    st.session_state.user_id = st.text_input("Enter User ID", value=st.session_state.user_id or "")

if not st.session_state.user_id:
    st.info("👆 Create a new user or enter existing User ID")
    st.stop()

# Chatbot Management
st.subheader("Chatbot Setup")
col3, col4 = st.columns(2)

with col3:
    st.markdown("##### Create New Chatbot")
    new_bot_name = st.text_input("Chatbot Name")
    new_bot_desc = st.text_area("Description")
    if st.button("Create Chatbot"):
        try:
            response = make_request_with_retry(
                requests.post,
                f"{st.session_state.server_url}/chatbots",
                data={
                    "user_id": st.session_state.user_id,
                    "name": new_bot_name,
                    "description": new_bot_desc
                }
            )
            if response.status_code == 200:
                st.success(f"Chatbot created! ID: {response.json()['id']}")
                st.session_state.chatbot_id = response.json()['id']
            else:
                st.error(f"Failed to create chatbot: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col4:
    st.markdown("##### Existing Chatbot")
    st.session_state.chatbot_id = st.text_input("Enter Chatbot ID", value=st.session_state.chatbot_id or "")

if st.session_state.chatbot_id:
    st.success("✅ Setup complete!")
    st.info("👈 Select 'Knowledge' from the sidebar to continue")
