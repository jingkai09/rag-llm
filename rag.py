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

# Initialize or fetch conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Function to add message to history and keep only the last 10
def add_to_conversation_history(user_message, response_message):
    # Add user and assistant responses as a tuple (user_message, response_message)
    st.session_state.conversation_history.append((user_message, response_message))
    
    # If the history exceeds 10, remove the oldest
    if len(st.session_state.conversation_history) > 10:
        st.session_state.conversation_history.pop(0)

# Fetch public URL from environment variable
public_url = "https://tender-bottles-smash.loca.lt"

# Sidebar for Parameters
st.sidebar.title("RAG System Configuration")
st.sidebar.write("Select the reranking method:")

# Select rerank method in sidebar
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
        # Implement server-side logic here if needed
        st.sidebar.success("Parameters updated!")
    except Exception as e:
        st.sidebar.error(f"Error updating parameters: {e}")

# Conversation interface (for the main content of the app)
st.title("Conversation History (Max 10)")

# Display only the last 10 messages in conversation history
for user_msg, response in st.session_state.conversation_history[-10:]:
    st.write(f"**User**: {user_msg}")
    st.write(f"**Assistant**: {response}")

# User input field
user_input = st.text_input("Your message:")

# Handle user input and generate response
if user_input:
    # Simulate a response (you can replace this with actual processing or API calls)
    response = f"Response to: {user_input}"

    # Add the current user message and generated response to history
    add_to_conversation_history(user_input, response)

    # Optionally, display a success message after adding the entry
    st.success("Message added to conversation history.")
