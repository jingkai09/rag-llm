import requests

# Initial parameters
temperature = 0.50
k = 10
overlapping = 0.5  # Default value for chunk overlapping
rerank_method = "similarity"  # Default rerank method (can be changed)

# URL of the FastAPI application
public_url = "https://honest-games-shout.loca.lt"

# Display available rerank methods for user selection
print("Available rerank methods:")
print("1. similarity")
print("2. importance")
print("3. relevance")

# Allow user input for dynamic parameter updates
print("\nConfigure the RAG pipeline parameters:")
temperature = float(input(f"Enter temperature (default {temperature}): ") or temperature)
k = int(input(f"Enter value for k (default {k}): ") or k)
overlapping = float(input(f"Enter overlapping value (default {overlapping}): ") or overlapping)
rerank_method = input(f"Enter rerank method (choose from similarity, importance, relevance, default 'similarity'): ") or rerank_method

# Set parameters on the server
response = requests.post(f"{public_url}/set-parameters", json={
    "temperature": temperature,
    "k": k,
    "overlapping": overlapping,
    "rerank_method": rerank_method
})

if response.status_code == 200:
    print("\nParameters updated successfully.")
else:
    print(f"\nFailed to update parameters. Status code: {response.status_code}")

# User query input
user_query = input("\nEnter your query: ")
print(f"\nUser Query: {user_query}")

# Send the query to the server
response = requests.post(f"{public_url}/query", params={"query": user_query})

# Print the response with enhanced formatting
print("\nResponse from server:")
if response.content:
    try:
        result = response.json()
        if "chunks" in result:
            if isinstance(result["chunks"], list) and result["chunks"]:
                for i, chunk in enumerate(result["chunks"]):
                    print(f"\nChunk {i + 1}:")
                    print(f"Content: {chunk['content']}")
                    print(f"Keywords: {chunk.get('keywords', 'None')}")
                    print(f"Importance/Similarity Score: {chunk.get('score', 'N/A')}")
                    print("-" * 50)
            else:
                print("\nNo valid chunks found in the response.")
        else:
            print("\nNo valid chunks found in the response.")
    except ValueError:
        print("\nError parsing response as JSON.")
else:
    print("\nReceived an empty response from the server.")
