# pages/3_Chat.py
import streamlit as st
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
    page_title="RAG Chat",
    page_icon="💬",
    layout="wide"
)

# Check if setup is complete
if not st.session_state.get('server_url') or not st.session_state.get('chatbot_id') or not st.session_state.get('kb_id'):
    st.error("⚠️ Please complete the setup and knowledge base configuration first!")
    if st.button("Go to Setup"):
        st.switch_page("pages/1_Setup.py")
    st.stop()

st.title("💬 RAG Chat")

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "documents" in message:
            with st.expander("View Sources"):
                for doc in message["documents"]:
                    st.markdown(f"**Document**: {doc['name']}")
                    st.markdown(f"**Preview**: {doc['preview']}")
                    if 'keywords' in doc and doc['keywords']:
                        st.markdown(f"**Keywords**: {', '.join(doc['keywords'])}")

# Chat input
user_query = st.chat_input("Enter your question...")

if user_query:
    # Display user message
    with st.chat_message("user"):
        st.write(user_query)
    
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner('Thinking...'):
            try:
                response = make_request_with_retry(
                    requests.post,
                    f"{st.session_state.server_url}/query",
                    data={
                        "query": user_query,
                        "chatbot_id": st.session_state.chatbot_id,
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    st.write(result['answer'])
                    
                    # Add bot response to chat history with documents
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": result['answer'],
                        "documents": result.get('documents', [])
                    })
                    
                    # Display source documents in expander
                    if 'documents' in result and result['documents']:
                        with st.expander("View Sources"):
                            for doc in result['documents']:
                                st.markdown(f"**Document**: {doc['name']}")
                                st.markdown(f"**Preview**: {doc['preview']}")
                                if 'keywords' in doc and doc['keywords']:
                                    st.markdown(f"**Keywords**: {', '.join(doc['keywords'])}")
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(
