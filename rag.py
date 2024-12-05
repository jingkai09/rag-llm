import os
import streamlit as st
import requests
from datetime import datetime

# Initial parameters
temperature = 0.50
k = 10
overlapping = 50  # Default value for chunk overlapping
rerank_method = "similarity"  # Default rerank method (can be changed)
keywords = ""  # Default empty keywords

# Fetch public URL from environment variable
public_url = "https://chilly-plums-stand.loca.lt"

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
        else:
            st.sidebar.error(f"Failed to update parameters. Status code: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Error communicating with the server: {e}")

# Main content: Ask a Question
st.title("RAG")

user_query = st.text_input("Enter your query:")

# Button to submit query
if st.button("Submit Query"):
    if user_query:
        with st.spinner('Processing your query...'):
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
            except requests.exceptions.RequestException as e:
                st.error(f"Error processing the query: {e}")

# Sidebar: Option to display conversation history
st.sidebar.subheader("Conversation History (Optional)")
show_history = st.sidebar.checkbox("Show Conversation History")

# Display conversation history in the main content area if selected
if show_history:
    try:
        history_response = requests.get(f"{public_url}/conversation-history")
        history_response.raise_for_status()

        if history_response.status_code == 200:
            try:
                # Log the raw response to inspect its structure
                st.write("Raw response from /conversation-history:", history_response.json())

                # Parse the JSON response
                history = history_response.json().get("conversation_history", [])
                
                if history:
                    st.subheader("Conversation History:")
                    last_query = None
                    for i, convo in enumerate(history):
                        # Log each conversation entry to check its type
                        st.write(f"Type of conversation entry at index {i}: {type(convo)}")

                        if isinstance(convo, dict):  # If the entry is a dictionary
                            query = convo.get('query', 'No query available')
                            answer = convo.get('answer', 'No answer available')
                            timestamp = convo.get('timestamp', 'No timestamp available')

                            # Handle timestamp conversion if numeric
                            if isinstance(timestamp, (int, float)):
                                timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

                            # Avoid duplicate answers for the same query
                            if query != last_query:
                                with st.expander(f"History {i + 1} - {timestamp}"):
                                    st.write(f"**Query:** {query}")
                                    st.write(f"**Answer:** {answer}")
                                    st.markdown("---")

                            # Update the last query to avoid displaying the same query multiple times
                            last_query = query
                        elif isinstance(convo, str):  # If the entry is a string
                            st.warning(f"Conversation entry at index {i} is a string. Displaying as plain text.")
                            with st.expander(f"History {i + 1} (String entry)"):
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
