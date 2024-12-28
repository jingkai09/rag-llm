# pages/knowledge.py
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
    page_title="Knowledge Base",
    page_icon="📚",
    layout="wide"
)

# Check setup
if not st.session_state.get('server_url') or not st.session_state.get('user_id') or not st.session_state.get('chatbot_id'):
    st.error("⚠️ Complete the setup first!")
    st.info("👈 Return to Home page")
    st.stop()

st.title("Knowledge Base Management")

# Chatbot Configuration
st.subheader("Chatbot Settings")
col1, col2, col3 = st.columns(3)

with col1:
    temperature = st.slider("Temperature", 0.0, 1.0, 0.5)
with col2:
    max_tokens = st.slider("Max Tokens", 100, 4000, 2000)
with col3:
    k = st.slider("Top k Results", 1, 20, 10)

if st.button("Update Settings"):
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
            st.success("Settings updated!")
        else:
            st.error(f"Update failed: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Knowledge Base Creation
st.subheader("Knowledge Base")
col4, col5 = st.columns(2)

with col4:
    kb_name = st.text_input("Knowledge Base Name")
    kb_desc = st.text_area("Description")
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
                st.success(f"Knowledge base created! ID: {response.json()['id']}")
                st.session_state['kb_id'] = response.json()['id']
            else:
                st.error(f"Creation failed: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col5:
    kb_id = st.text_input("Or enter existing Knowledge Base ID", 
                         value=st.session_state.get('kb_id', ''))
    if kb_id:
        st.session_state['kb_id'] = kb_id

# Document Upload
if st.session_state.get('kb_id'):
    st.subheader("Document Upload")
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
                    st.success("Document uploaded successfully!")
                    st.info("👈 Select 'Chat' from the sidebar to start chatting!")
                else:
                    st.error(f"Upload failed: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
