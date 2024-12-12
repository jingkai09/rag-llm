# client.py
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

    # Update parameters button
    if st.sidebar.button("Update Parameters"):
        try:
            response = make_request_with_retry(
                requests.post,
                f"{st.session_state.public_url}/set-parameters",
                json={
                    "temperature": temperature,
                    "k": k,
                    "chunk_overlap": chunk_overlap
                }
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
                        f"{st.session_state.public_url}/query",
                        params={"query": user_query}
                    )

                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display answer
                        st.markdown("### Answer")
                        st.write(result['answer'])
                        
                        # Display keywords
                        if 'keywords' in result and result['keywords']:
                            st.markdown("### Keywords")
                            keyword_html = "<div style='display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;'>"
                            for keyword in result['keywords']:
                                keyword_html += f"<span style='background-color: #f0f2f6; padding: 4px 12px; border-radius: 16px; font-size: 0.9em;'>{keyword}</span>"
                            keyword_html += "</div>"
                            st.markdown(keyword_html, unsafe_allow_html=True)
                        
                        # Display chunks
                        if 'chunks' in result and result['chunks']:
                            st.markdown("### Retrieved Chunks")
                            for i, chunk in enumerate(result['chunks'], 1):
                                with st.expander(f"Chunk {i} (ID: {chunk.get('id', 'N/A')} | Score: {chunk['score']:.4f})", expanded=False):
                                    # Display chunk ID if available
                                    if 'id' in chunk:
                                        st.markdown(f"**Chunk ID**: {chunk['id']}")
                                    
                                    st.markdown(f"**Source**: {chunk['source']}")
                                    
                                    # Highlight keywords in content
                                    content = chunk['content']
                                    if 'keywords' in result:
                                        for keyword in result['keywords']:
                                            content = content.replace(
                                                keyword,
                                                f"<mark>{keyword}</mark>"
                                            )
                                    st.markdown(f"**Content**: {content}", unsafe_allow_html=True)
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
                f"{st.session_state.public_url}/conversation-history"
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
