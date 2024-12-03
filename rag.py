import streamlit as st
import requests

# FastAPI application URL
public_url = "https://eleven-toys-stand.loca.lt"

# Streamlit UI for configuring the parameters
st.title("RAG Pipeline Configuration")

# Configure temperature
temperature = st.slider(
    "Temperature", min_value=0.0, max_value=1.0, value=0.50, step=0.01,
    help="Controls the randomness of the model's responses."
)

# Configure k (top-k)
k = st.number_input("Top-k", min_value=1, value=10, step=1, help="Number of results to retrieve.")

# Configure overlapping chunks
overlapping = st.slider(
    "Overlapping Chunks", min_value=0.0, max_value=1.0, value=0.5, step=0.05,
    help="Percentage of overlap between chunks."
)

# Configure rerank method
rerank_method = st.selectbox(
    "Rerank Method", 
    options=["similarity", "importance", "relevance"],
    index=0,
    help="Method to rerank the retrieved chunks."
)

# Configure index type
index_type = st.selectbox(
    "Index Type", 
    options=["basic", "rerank"],
    index=1,
    help="Choose between basic retrieval or rerank method."
)

# Optional keyword input
keyword = st.text_input("Optional Keyword", help="Enter a keyword to refine the search (optional).")

# Button to submit configuration
if st.button("Update Parameters"):
    response = requests.post(f"{public_url}/set-parameters", json={
        "temperature": temperature,
        "k": k,
        "overlapping": overlapping,
        "rerank_method": rerank_method,
        "index_type": index_type
    })

    if response.status_code == 200:
        st.success("Parameters updated successfully.")
    else:
        st.error(f"Failed to update parameters. Status code: {response.status_code}")

# User query input
user_query = st.text_input("Enter your query:", help="Enter the query to retrieve information.")
if user_query:
    st.write(f"User Query: {user_query}")

    # Send the query to the server
    params = {"query": user_query}
    if keyword:
        params["keyword"] = keyword

    response = requests.post(f"{public_url}/query", params=params)

    if response.status_code == 200:
        try:
            result = response.json()
            if "chunks" in result and isinstance(result["chunks"], list):
                if result["chunks"]:
                    for i, chunk in enumerate(result["chunks"]):
                        st.subheader(f"Chunk {i + 1}")
                        st.write(f"Content: {chunk['content']}")
                        st.write(f"Keywords: {chunk.get('keywords', 'None')}")
                        st.write(f"Importance/Similarity Score: {chunk.get('score', 'N/A')}")
                        st.markdown("---")
                else:
                    st.warning("No valid chunks found in the response.")
            else:
                st.warning("No valid chunks found in the response.")
        except ValueError:
            st.error("Error parsing response as JSON.")
    else:
        st.error(f"Error with server response. Status code: {response.status_code}")
