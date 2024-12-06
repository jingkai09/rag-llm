import os
import streamlit as st
import requests
from datetime import datetime
import time

# Initial parameters
temperature = 0.50
k = 10
overlapping = 50  # Default value for chunk overlapping
rerank_method = "similarity"  # Default rerank method (can be changed)
keywords = ""  # Default empty keywords

# Fetch public URL from environment variable
public_url = "https://salty-steaks-wink.loca.lt"

# Sidebar for Parameters
st.sidebar.title("RAG System Configuration")
st.sidebar.write("Select the reranking method:")

rerank_method = st.sidebar.selectbox(
    "Rerank Method",
    ["similarity", "importance"],
    index=0  # Default to similarity
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
        keywords = ""  # Ensure keywords are never None
    try:
        # Retry logic for POST request
        retry_attempts = 5  # Number of retry attempts
        for attempt in range(retry_attempts):
            try:
                response = requests.post(f"{public_url}/set-parameters", json={
                    "temperature": temperature,
                    "k": k,
                    "chunk_overlap": overlapping,
                    "rerank_method": rerank_method,
                    "keywords": keywords
                })
                response.raise_for_status()  # Will raise an error for bad responses (status codes 4xx or 5xx)

                if response.status_code == 200:
                    st.sidebar.success("Parameters updated successfully.")
                    break  # Exit loop if request is successful
                else:
                    st.sidebar.error(f"Failed to update parameters. Status code: {response.status_code} - {response.text}")
                    break  # Exit loop if an error other than 502 occurs
            except requests.exceptions.RequestException as e:
                if e.response and e.response.status_code == 502:
                    # Retry on 502 error
                    st.sidebar.warning(f"Received 502 error. Retrying... ({attempt + 1}/{retry_attempts})")
                    time.sleep(3)  # Wait before retrying
                else:
                    # Handle other types of request errors (e.g., connection issues)
                    st.sidebar.error(f"Error communicating with the server: {e}")
                    break  # Exit loop for other errors

    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Error communicating with the server: {e}")

# Main content: Ask a Question
st.title("RAG with LLM")

user_query = st.text_input("Enter your query:")

# Button to submit query
if st.button("Submit Query"):
    if user_query:
        with st.spinner('Processing your query...'):
            try:
                # Retry logic for POST request
                retry_attempts = 5  # Number of retry attempts
                for attempt in range(retry_attempts):
                    try:
                        # Pass the query and keywords to the server
                        response = requests.post(f"{public_url}/query", params={"query": user_query, "keywords": keywords})
                        response.raise_for_status()

                        st.subheader("Response from server:")
                        if response.status_code == 200 and response.content:
                            try:
                                result = response.json()

                                # Display the query answer
                                if 'answer' in result:
                                    st.write(f"**Answer to your query:** {result['answer']}")
                                else:
                                    st.error("No valid answer received.")

                                # Display chunks used for answering in an organized way
                                if 'chunks' in result:
                                    st.write(f"**Chunks Used:**")
                                    for i, chunk in enumerate(result["chunks"]):
                                        with st.expander(f"Chunk {i + 1}"):
                                            st.markdown(f"**Source**: {chunk['source']}")
                                            st.markdown(f"**Score**: {chunk['score']}")
                                            st.write(f"**Content**: {chunk['content'][:500]}...")  # Truncate content to 500 chars for brevity
                                            st.markdown("---")
                            except ValueError:
                                st.error("Error parsing response.")
                        else:
                            st.warning("Received an empty response or error from the server.")
                        break  # Exit loop if request is successful
                    except requests.exceptions.RequestException as e:
                        if e.response and e.response.status_code == 502:
                            # Retry on 502 error
                            st.warning(f"Received 502 error. Retrying... ({attempt + 1}/{retry_attempts})")
                            time.sleep(3)  # Wait before retrying
                        else:
                            # Handle other types of request errors (e.g., connection issues)
                            st.error(f"Error processing the query: {e}")
                            break  # Exit loop for other errors
            except requests.exceptions.RequestException as e:
                st.error(f"Error processing the query: {e}")

# Sidebar: Option to display conversation history
st.sidebar.subheader("Conversation History")
show_history = st.sidebar.checkbox("Show Conversation History")

# Display conversation history in a dropdown (select box) if selected
if show_history:
    try:
        history_response = requests.get(f"{public_url}/conversation-history")
        history_response.raise_for_status()

        if history_response.status_code == 200:
            try:
                # Parse the JSON response
                history = history_response.json().get("conversation_history", [])
                
                if history:
                    st.subheader("Conversation History:")
                    
                    # Chunk the history into smaller groups (let's say 3 entries per chunk)
                    chunk_size = 3
                    chunks = []
                    for chunk_start in range(0, len(history), chunk_size):
                        chunk_end = chunk_start + chunk_size
                        history_chunk = history[chunk_start:chunk_end]
                        chunks.append(history_chunk)
                    
                    # Create a dropdown (selectbox) for users to choose a chunk
                    chunk_options = [f"History Chunk {i + 1}" for i in range(len(chunks))]
                    selected_chunk = st.selectbox("Select a conversation chunk to view:", chunk_options)

                    # Display the selected chunk's content
                    if selected_chunk:
                        selected_chunk_index = chunk_options.index(selected_chunk)
                        selected_history_chunk = chunks[selected_chunk_index]
                        
                        for i, convo in enumerate(selected_history_chunk):
                            if isinstance(convo, dict):  # If the entry is a dictionary
                                query = convo.get('query', 'No query available')
                                answer = convo.get('answer', 'No answer available')
                                timestamp = convo.get('timestamp', 'No timestamp available')

                                # Handle timestamp conversion if numeric
                                if isinstance(timestamp, (int, float)):
                                    timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

                                # Display the conversation entries
                                st.write(f"**Query:** {query}")
                                st.write(f"**Answer:** {answer}")
                                st.write(f"**Timestamp:** {timestamp}")
                                st.markdown("---")

                            elif isinstance(convo, str):  # If the entry is a string
                                st.warning(f"Conversation entry at index {i} is a string. Displaying as plain text.")
                                st.write(convo)
                                st.markdown("---")
                            else:
                                st.warning(f"Invalid conversation entry at index {i + 1}: Not a valid dictionary or string.")
                else:
                    st.write("No conversation history available.")
            except ValueError as parse_error:
                st.error(f"Error parsing the conversation history response: {parse_error}")
        else:
            st.warning(f"Failed to fetch conversation history. Status code: {history_response.status_code}")
    except requests.exceptions.RequestException as request_error:
        st.error(f"Error fetching conversation history: {request_error}")
