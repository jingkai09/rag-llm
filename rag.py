import streamlit as st
import requests

# Initial parameters
temperature = 0.50
k = 10
overlapping = 50  # Default value for chunk overlapping
rerank_method = "similarity"  # Default rerank method (can be changed)
keywords = ""  # Default empty keywords

# URL of the FastAPI application
public_url = "https://spotty-bats-shave.loca.lt"  # Replace with the actual public URL of your FastAPI server

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

# Keywords input (comma-separated)
keywords = st.text_input("Enter Keywords (Optional)", "")

# Set parameters on the server
if st.button("Update Parameters"):
    response = requests.post(f"{public_url}/set-parameters", json={
        "temperature": temperature,
        "k": k,
        "chunk_overlap": overlapping,
        "rerank_method": rerank_method,
        "keywords": keywords
    })

    if response.status_code == 200:
        st.success("Parameters updated successfully.")
    else:
        st.error(f"Failed to update parameters. Status code: {response.status_code} - {response.text}")

# User query input
st.subheader("Ask a Question")
user_query = st.text_input("Enter your query:")

if user_query:
    # Pass the query and keywords to the server
    response = requests.post(f"{public_url}/query", params={"query": user_query, "keywords": keywords})

    st.subheader("Response from server:")
    if response.status_code == 200 and response.content:
        try:
            result = response.json()

            # Display the query answer
            st.write(f"**Answer to your query:**")
            st.write(result.get("answer", "No answer available."))

            # Display chunks used for answering
            st.write(f"**Chunks Used:**")
            for i, chunk in enumerate(result["chunks"]):
                st.write(f"**Source**: {chunk['source']} | **Score**: {chunk['score']}")
                st.write(f"Content: {chunk['content']}")
                st.write(f"Keywords Matched: {chunk.get('keywords', 'None')}")
                st.markdown("---")
        except ValueError:
            st.error("Error parsing response.")
    else:
        st.warning("Received an empty response or error from the server.")

# Display conversation history
st.subheader("Conversation History (Last 10 Queries)")
history_response = requests.get(f"{public_url}/conversation-history")

if history_response.status_code == 200:
    history = history_response.json().get("conversation_history", [])
    if history:
        for i, convo in enumerate(history):
            if i >= 10:  # Limit to last 10 entries
                break
            st.write(f"**Query {i + 1}:** {convo['query']}")
            st.write(f"**Answer {i + 1}:** {convo['answer']}")
            st.write("---")
    else:
        st.write("No conversation history available.")
else:
    st.error(f"Error fetching conversation history: {history_response.text}")
