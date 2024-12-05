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
public_url = "https://cold-comics-work.loca.lt"

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
                # Parse the JSON response
                history = history_response.json().get("conversation_history", [])
                
                if history:
                    st.subheader("Conversation History:")
                    # Iterate through history items safely
                    for i, convo in enumerate(history):
                        # Check if each entry has all the expected fields
                        if isinstance(convo, dict):
                            query = convo.get('query', 'No query available')
                            answer = convo.get('answer', 'No answer available')
                            timestamp = convo.get('timestamp', 'No timestamp available')
                            
                            # Handle timestamp conversion if it's present
                            if isinstance(timestamp, (int, float)):
                                timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Display conversation history with proper labels
                            with st.expander(f"History {i + 1} - {timestamp}"):
                                st.write(f"**Query:** {query}")
                                st.write(f"**Answer:** {answer}")
                                st.markdown("---")
                        else:
                            st.warning(f"Invalid conversation entry at index {i + 1}: Not a valid dictionary.")
                else:
                    st.write("No conversation history available.")
            except ValueError:
                st.error("Error parsing the conversation history response.")
        else:
            st.warning("Failed to fetch conversation history.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching conversation history: {e}")
