import os
import streamlit as st
import requests
from datetime import datetime
import time
from requests.exceptions import RequestException

# Configuration
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

def make_request_with_retry(method, url, **kwargs):
    """Helper function to make requests with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            response = method(url, **kwargs)
            if response.status_code != 502:  # If not a 502 error, return response
                return response

            if attempt < MAX_RETRIES - 1:
                with st.spinner(f'Server returned 502 error. Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})'):
                    time.sleep(RETRY_DELAY)
        except RequestException as e:
            if attempt < MAX_RETRIES - 1:
                with st.spinner(f'Connection error. Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})'):
                    time.sleep(RETRY_DELAY)
            else:
                raise e
    return response

# Page configuration
st.set_page_config(
    page_title="RAG System",
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

# Sidebar configuration
with st.sidebar:
    st.title("Server Configuration")
    input_url = st.text_input(
        "Server URL:",
        value=st.session_state.server_url,
        help="Example: http://localhost:8000"
    )

    # Update session state if URL changes
    if input_url != st.session_state.server_url:
        st.session_state.server_url = input_url

    # User Management
    if st.session_state.server_url:
        st.title("User Management")
        
        # Create new user
        with st.expander("Create New User"):
            new_user_name = st.text_input("Enter username")
            if st.button("Create User"):
                try:
                    response = make_request_with_retry(
                        requests.post,
                        f"{st.session_state.server_url}/users",
                        data={"name": new_user_name}
                    )
                    if response.status_code == 200:
                        st.success(f"User created successfully! User ID: {response.json()['id']}")
                        st.session_state.user_id = response.json()['id']
                    else:
                        st.error(f"Failed to create user: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        # Select existing user
        st.session_state.user_id = st.text_input("Enter User ID", value=st.session_state.user_id or "")

        # Chatbot Management
        if st.session_state.user_id:
            st.title("Chatbot Management")
            
            # Create new chatbot
            with st.expander("Create New Chatbot"):
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
                            st.success(f"Chatbot created successfully! ID: {response.json()['id']}")
                            st.session_state.chatbot_id = response.json()['id']
                        else:
                            st.error(f"Failed to create chatbot: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

            # Select existing chatbot
            st.session_state.chatbot_id = st.text_input("Enter Chatbot ID", value=st.session_state.chatbot_id or "")

        # Chatbot Configuration
        if st.session_state.chatbot_id:
            st.title("Chatbot Configuration")
            
            temperature = st.slider("Temperature", 0.0, 1.0, 0.5)
            max_tokens = st.slider("Max Tokens", 100, 4000, 2000)
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

# Main content
if not st.session_state.server_url:
    st.warning("Please enter your server URL in the sidebar to begin.")
elif not st.session_state.user_id:
    st.warning("Please create or select a user to continue.")
elif not st.session_state.chatbot_id:
    st.warning("Please create or select a chatbot to continue.")
else:
    st.title("RAG with LLM")
    st.markdown("---")

    # Query interface
    user_query = st.text_input("Enter your question:", key="query_input")

    if st.button("Submit Query", key="submit_button"):
        if user_query:
            with st.spinner('Processing your query...'):
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

                        # Display answer
                        st.markdown("### Answer")
                        st.write(result['answer'])

                        # Display document details
                        if 'documents' in result and result['documents']:
                            st.markdown("### Retrieved Documents")
                            for doc in result['documents']:
                                with st.expander(f"Document: {doc['name']}", expanded=False):
                                    st.markdown(f"**Preview**: {doc['preview']}")
                                    if 'keywords' in doc and doc['keywords']:
                                        st.markdown(f"**Keywords**: {', '.join(doc['keywords'])}")

                        # Display metadata
                        if 'metadata' in result:
                            st.markdown("### Query Metadata")
                            st.json(result['metadata'])
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Error processing query: {str(e)}")

    # Knowledge Base Management
    st.markdown("---")
    st.markdown("### Knowledge Base Management")
    
    with st.expander("Create New Knowledge Base"):
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
                else:
                    st.error(f"Failed to create knowledge base: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
