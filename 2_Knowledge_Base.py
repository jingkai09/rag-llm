import streamlit as st
from datetime import datetime
import requests
import time
from requests.exceptions import RequestException

# Configuration
MAX_RETRIES = 5
RETRY_DELAY = 2

def make_request_with_retry(method, url, **kwargs):
    """Helper function to make requests with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            response = method(url, **kwargs)
            if response.status_code != 502:
                return response
            if attempt < MAX_RETRIES - 1:
                with st.spinner(f'Server returned 502 error. Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})'):
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
    page_title="Knowledge Base Management",
    page_icon="📚",
    layout="wide"
)

# Check if setup is complete
if not st.session_state.get('server_url') or not st.session_state.get('user_id') or not st.session_state.get('chatbot_id'):
    st.error("⚠️ Please complete the setup first!")
    if st.button("Go to Setup"):
        st.switch_page("pages/1_Setup.py")
    st.stop()

st.title("📚 Knowledge Base Management")

# Chatbot Configuration
st.header("1. Chatbot Configuration")
col1, col2, col3 = st.columns(3)

with col1:
    temperature = st.slider("Temperature", 0.0, 1.0, 0.5)
with col2:
    max_tokens = st.slider("Max Tokens", 100, 4000, 2000)
with col3:
    k = st.slider("Top k Results", 1, 20, 10)

if st.button("Update Configuration"):
    try:
        response = make_request_with_retry(
            requests.post,
            f"{st.session_state.server_url}/chatbots/{st.session_state.chatbot_id}/configure",
            data={
                "temperature": temperature,
                "max_tokens": max_tokens,
                "k": k
            }
        )
        if response.status_code == 200:
            st.success("Configuration updated successfully!")
        else:
            st.error(f"Failed to update configuration: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Knowledge Base Creation
st.header("2. Knowledge Base Creation")
col4, col5 = st.columns(2)

with col4:
    kb_name = st.text_input("Knowledge Base Name")
    kb_desc = st.text_area("Knowledge Base Description")
    if st.button("Create Knowledge Base"):
        try:
            response = make_request_with_retry(
                requests.post,
                f"{st.session_state.server_url}/knowledge-bases",
                data={
                    "chatbot_id": st.session_state.chatbot_id,
                    "name": kb_name,
                    "description": kb_desc
                }
            )
            if response.status_code == 200:
                st.success(f"Knowledge base created successfully! ID: {response.json()['id']}")
                st.session_state['kb_id'] = response.json()['id']
            else:
                st.error(f"Failed to create knowledge base: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col5:
    kb_id = st.text_input("Or enter existing Knowledge Base ID", 
                         value=st.session_state.get('kb_id', ''))
    if kb_id:
        st.session_state['kb_id'] = kb_id

# Document Upload
if st.session_state.get('kb_id'):
    st.header("3. Document Upload")
    uploaded_file = st.file_uploader("Choose a file", type=['txt', 'csv', 'pdf'])
    
    if uploaded_file:
        if st.button("Upload Document"):
            try:
                files = {"file": uploaded_file}
                response = make_request_with_retry(
                    requests.post,
                    f"{st.session_state.server_url}/knowledge-bases/{st.session_state['kb_id']}/documents",
                    files=files
                )
                if response.status_code == 200:
                    st.success("Document uploaded and processed successfully!")
                else:
                    st.error(f"Failed to upload document: {response.text}")
            except Exception as e:
                st.error(f"Error uploading document: {str(e)}")

    if st.button("Go to Chat"):
        st.switch_page("pages/3_Chat.py")
