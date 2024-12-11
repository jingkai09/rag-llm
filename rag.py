import os
import streamlit as st
import requests
from datetime import datetime
import time
from requests.exceptions import RequestException

# Maximum number of retry attempts
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def make_request_with_retry(method, url, **kwargs):
    """Helper function to make requests with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            response = method(url, **kwargs)
            if response.status_code != 502:  # If not a 502 error, return response
                return response
            
            # If we got a 502, wait and retry
            if attempt < MAX_RETRIES - 1:  # Don't show message on last attempt
                with st.spinner(f'Server returned 502 error. Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})'):
                    time.sleep(RETRY_DELAY)
        except RequestException as e:
            if attempt < MAX_RETRIES - 1:
                with st.spinner(f'Connection error. Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})'):
                    time.sleep(RETRY_DELAY)
            else:
                raise e
    
    # If we've exhausted all retries, return the last response
    return response

# Initialize session state for URL if not exists
if 'public_url' not in st.session_state:
    st.session_state.public_url = ""

# Initial parameters
temperature = 0.50
k = 10
overlapping = 50
rerank_method = "similarity"
keywords = ""

# URL Input at the top of the sidebar
st.sidebar.title("Server Configuration")
input_url = st.sidebar.text_input(
    "Enter your localtunnel URL:",
    value=st.session_state.public_url,
    help="Example: https://your-tunnel.loca.lt"
)

# Update session state if URL changes
if input_url != st.session_state.public_url:
    st.session_state.public_url = input_url

# Only show the rest of the interface if URL is provided
if not st.session_state.public_url:
    st.warning("Please enter your localtunnel URL in the sidebar to begin.")
else:
    # Sidebar for Parameters
    st.sidebar.title("RAG System Configuration")
    st.sidebar.write("Select the reranking method:")

    rerank_method = st.sidebar.selectbox(
        "Rerank Method",
        ["similarity", "importance"],
        index=0
    )

    # Configure the RAG pipeline parameters in the sidebar
    st.sidebar.subheader("Configure the RAG pipeline parameters:")
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.5)
    k = st.sidebar.slider("Top k", 1, 20, 10)
    overlapping = st.sidebar.slider("Chunk Overlap", 0, 100, 50)

    # Keywords input (comma-separated) in the sidebar
    keywords = st.sidebar.text_input("Enter Keywords (Optional)", "")

    # Set parameters on the server
    if st.sidebar.button("Update Parameters"):
        if not keywords:
            keywords = ""
        try:
            response = make_request_with_retry(
                requests.post,
                f"{st.session_state.public_url}/set-parameters",
                json={
                    "temperature": temperature,
                    "k": k,
                    "chunk_overlap": overlapping,
                    "rerank_method": rerank_method,
                    "keywords": keywords
                }
            )
            
            if response.status_code == 200:
                st.sidebar.success("Parameters updated successfully.")
            else:
                st.sidebar.error(f"Failed to update parameters. Status code: {response.status_code} - {response.text}")
        except RequestException as e:
            st.sidebar.error(f"Error communicating with the server: {e}")

    # Main content: Ask a Question
    st.title("RAG with LLM")

    user_query = st.text_input("Enter your query:")

    # Button to submit query
    if st.button("Submit Query"):
        if user_query:
            with st.spinner('Processing your query...'):
                try:
                    response = make_request_with_retry(
                        requests.post,
                        f"{st.session_state.public_url}/query",
                        params={"query": user_query, "keywords": keywords}
                    )

                    st.subheader("Response from server:")
                    if response.status_code == 200 and response.content:
                        try:
                            result = response.json()

                            if 'answer' in result:
                                st.write(f"**Answer to your query:** {result['answer']}")
                            else:
                                st.error("No valid answer received.")

                            if 'chunks' in result:
                                st.write(f"**Retrieved Chunks:**")
                                for rank, chunk in enumerate(result["chunks"], 1):
                                    chunk_index = chunk.get('index', 'N/A')  # Get chunk index, default to 'N/A' if not present
                                    with st.expander(f"Rank #{rank} (Chunk Index: {chunk_index})", expanded=False):
                                        st.markdown(f"**Source**: {chunk['source']}")
                                        st.markdown(f"**Score**: {chunk['score']}")
                                        st.write(f"**Content**: {chunk['content'][:500]}...")
                                        st.markdown("---")
                        except ValueError:
                            st.error("Error parsing response.")
                    else:
                        st.warning("Received an empty response or error from the server.")
                except RequestException as e:
                    st.error(f"Error processing the query: {e}")

    # Sidebar: Option to display conversation history
    st.sidebar.subheader("Conversation History")
    show_history = st.sidebar.checkbox("Show Conversation History")

    # Display conversation history
    if show_history:
        try:
            history_response = make_request_with_retry(
                requests.get,
                f"{st.session_state.public_url}/conversation-history"
            )

            if history_response.status_code == 200:
                try:
                    history = history_response.json().get("conversation_history", [])
                    
                    if history:
                        st.subheader("Latest Conversation History:")
                        
                        # Get the last 10 conversations (or all if less than 10)
                        latest_history = history[-10:]
                        
                        # Display conversations in reverse chronological order (newest first)
                        for history_idx, convo in enumerate(reversed(latest_history), 1):
                            with st.expander(f"History #{history_idx}: {convo.get('query', 'No query available')[:50]}...", expanded=False):
                                if isinstance(convo, dict):
                                    query = convo.get('query', 'No query available')
                                    answer = convo.get('answer', 'No answer available')
                                    timestamp = convo.get('timestamp', 'No timestamp available')

                                    if isinstance(timestamp, (int, float)):
                                        timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

                                    st.write(f"**Full Query:** {query}")
                                    st.write(f"**Answer:** {answer}")
                                    st.write(f"**Timestamp:** {timestamp}")
                                else:
                                    st.warning("Invalid conversation entry: Not a valid dictionary")
                    else:
                        st.write("No conversation history available.")
                except ValueError as parse_error:
                    st.error(f"Error parsing the conversation history response: {parse_error}")
            else:
                st.warning(f"Failed to fetch conversation history. Status code: {history_response.status_code}")
        except RequestException as request_error:
            st.error(f"Error fetching conversation history: {request_error}")
