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
if 'public_url' not in st.session_state:
    st.session_state.public_url = ""
if 'keywords' not in st.session_state:
    st.session_state.keywords = []
if 'default_score' not in st.session_state:
    st.session_state.default_score = 0.75  # Default similarity score

# Sidebar configuration
st.sidebar.title("Server Configuration")
input_url = st.sidebar.text_input(
    "Enter your server URL:",
    value=st.session_state.public_url,
    help="Example: http://localhost:8000 or https://your-tunnel.loca.lt"
)

# Update session state if URL changes
if input_url != st.session_state.public_url:
    st.session_state.public_url = input_url

# Main interface
if not st.session_state.public_url:
    st.warning("Please enter your server URL in the sidebar to begin.")
else:
    # RAG System Configuration
    st.sidebar.title("RAG System Configuration")

    # Parameters
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.5)
    k = st.sidebar.slider("Top k Results", 1, 20, 10)
    chunk_overlap = st.sidebar.slider("Chunk Overlap", 0, 100, 50)
    
    # Default Score Configuration
    st.sidebar.markdown("### Default Score Configuration")
    st.session_state.default_score = st.sidebar.slider(
        "Default Similarity Score",
        0.0, 1.0, st.session_state.default_score,
        help="Set default similarity score for chunks without scores"
    )
    
    # Reranking Configuration
    st.sidebar.markdown("### Reranking Configuration")
    rerank_method = st.sidebar.radio(
        "Reranking Method",
        options=["semantic", "keywords"],
        help="Choose between semantic similarity or keyword-based reranking"
    )

    # Keyword input section (shown only when keywords method is selected)
    if rerank_method == "keywords":
        st.sidebar.markdown("### Keyword Configuration")
        keyword_input = st.sidebar.text_input(
            "Enter keywords (comma-separated):",
            help="Enter keywords to influence document ranking"
        )
        if keyword_input:
            keywords = [k.strip() for k in keyword_input.split(",") if k.strip()]
            if keywords != st.session_state.keywords:
                st.session_state.keywords = keywords
        
        if st.session_state.keywords:
            st.sidebar.markdown("**Current Keywords:**")
            for keyword in st.session_state.keywords:
                st.sidebar.markdown(f"- {keyword}")

    # Update parameters button
    if st.sidebar.button("Update Parameters"):
        try:
            params = {
                "temperature": temperature,
                "recall_num": k,
            }

            response = make_request_with_retry(
                requests.post,
                f"{st.session_state.public_url}/api/chatbots/chatbot_id/configure",  # Updated API endpoint
                data=params
            )

            if response.status_code == 200:
                st.sidebar.success("Parameters updated successfully!")
            else:
                st.sidebar.error(f"Failed to update parameters: {response.text}")
        except Exception as e:
            st.sidebar.error(f"Error: {str(e)}")

    # Main content
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
                        f"{st.session_state.public_url}/api/query/user_id/chatbot_id",  # Updated API endpoint
                        data={"query": user_query}
                    )

                    if response.status_code == 202:
                        result = response.json()

                        # Display answer
                        st.markdown("### Answer")
                        st.write(result.get('answer', "No answer available."))

                        # Display retrieved documents
                        chunks = result.get('documents', [])
                        if chunks:
                            st.markdown("### Retrieved Documents")
                            for chunk in chunks:
                                with st.expander(f"Document ID: {chunk['doc_id']}"):
                                    st.markdown(f"**Similarity Score**: {chunk['similarity_score']}")
                                    st.markdown(f"**Content Preview**: {chunk['content_preview']}")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Error processing query: {str(e)}")

    # Conversation History
    st.sidebar.markdown("---")
    if st.sidebar.checkbox("Show Conversation History"):
        try:
            history_response = make_request_with_retry(
                requests.get,
                f"{st.session_state.public_url}/api/task/task_id/status"  # Updated API endpoint
            )

            if history_response.status_code == 200:
                history = history_response.json().get("conversation_history", [])
                if history:
                    st.markdown("### Conversation History")
                    for i, conv in enumerate(reversed(history), 1):
                        with st.expander(f"Q{i}: {conv['query'][:50]}...", expanded=False):
                            st.markdown(f"**Question**: {conv['query']}")
                            st.markdown(f"**Answer**: {conv['answer']}")
                            st.markdown(f"**Time**: {conv['timestamp']}")
                else:
                    st.info("No conversation history available.")
        except Exception as e:
            st.error(f"Error fetching conversation history: {str(e)}")
