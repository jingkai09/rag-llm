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
public_url = "https://tender-bottles-smash.loca.lt"  # Fixed extra space

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
    params = {
        "rerank_method": rerank_method,
        "temperature": temperature,
        "k": k,
        "overlapping": overlapping,
        "keywords": keywords
    }
    
    # Send the parameters to the server
    try:
        response = requests.post(f"{public_url}/update_parameters", json=params)
        if response.status_code == 200:
            st.sidebar.success("Parameters updated successfully!")
        else:
            st.sidebar.error(f"Failed to update parameters. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Error updating parameters: {e}")

# Display current configuration
st.title("Current RAG System Configuration")
st.write(f"**Rerank Method:** {rerank_method}")
st.write(f"**Temperature:** {temperature}")
st.write(f"**Top k:** {k}")
st.write(f"**Chunk Overlap:** {overlapping}")
st.write(f"**Keywords:** {keywords if keywords else 'None'}")

# Optionally, display a timestamp or other info
st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
