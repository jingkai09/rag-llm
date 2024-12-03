import streamlit as st
import requests

# Initial parameters
temperature = 0.50
k = 10
overlapping = 0.5  # Default value for chunk overlapping
rerank_method = "similarity"  # Default rerank method (can be changed)
keywords = ""  # Default empty keywords

# URL of the FastAPI application
public_url = "https://honest-games-shout.loca.lt"

# Display available rerank methods for user selection
st.title("RAG System Configuration")
st.write("Select the reranking method:")

rerank_method = st.selectbox(
    "Rerank Method",
    ["similarity", "importance"],
    index=0  # Default to similarity
)

# Configure the RAG pipeline parameters
st.subheader("Configure the RAG pipeline parameters:")
temperature = st.slider("Temperature", 0.0, 1.0, 0.5)
k = st.slider("Top k", 1, 20, 10)
overlapping = st.slider("Chunk Overlap", 0, 100, 50)

# Keywords input
keywords = st.text_input("Enter Keywords (Optional)", "")

# Set parameters on the server
response = requests.post(f"{public_url}/set-parameters", json={
    "temperature": temperature,
    "k": k,
    "overlapping": overlapping,
    "rerank_method": rerank_method
})

if response.status_code == 200:
    st.success("Parameters updated successfully.")
else:
    st.error(f"Failed to update parameters. Status code: {response.status_code}")

# User query input
user_query = st.text_input("Enter your query:")

if user_query:
    # Pass the query and keywords to the server
    response = requests.post(f"{public_url}/query", params={"query": user_query, "keywords": keywords})
    
    st.subheader("Response from server:")
    if response.content:
        try:
            result = response.json()
            if "chunks" in result:
                for i, chunk in enumerate(result["chunks"]):
                    st.write(f"**Chunk {i + 1}:**")
                    st.write(f"Content: {chunk['content']}")
                    st.write(f"Keywords: {chunk.get('keywords', 'None')}")
                    st.write(f"Score: {chunk.get('score', 'N/A')}")
                    st.markdown("---")
        except ValueError:
            st.error("Error parsing response.")
    else:
        st.warning("Received an empty response from the server.")
