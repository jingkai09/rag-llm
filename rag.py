import streamlit as st
import requests
import time
from requests.exceptions import RequestException

# Configuration
MAX_RETRIES = 5
RETRY_DELAY = 2

def make_request_with_retry(method, url, **kwargs):
    for attempt in range(MAX_RETRIES):
        try:
            response = method(url, **kwargs)
            if response.status_code != 502:
                return response
            if attempt < MAX_RETRIES - 1:
                with st.spinner(f'Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})'):
                    time.sleep(RETRY_DELAY)
        except RequestException as e:
            if attempt < MAX_RETRIES - 1:
                with st.spinner(f'Connection error. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})'):
                    time.sleep(RETRY_DELAY)
            else:
                raise e
    return response

# Page configuration
st.set_page_config(
    page_title="RAG System",
    page_icon="🤖",
    layout="wide"
)

# Initialize session states
if 'server_url' not in st.session_state:
    st.session_state.server_url = ""
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'chatbot_id' not in st.session_state:
    st.session_state.chatbot_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

st.title("RAG System")

# Step 1: Server Configuration
st.header("1. Server Setup")
if st.session_state.current_step >= 1:
    input_url = st.text_input("Server URL:", value=st.session_state.server_url, 
                             help="Example: http://localhost:8000")
    
    if input_url != st.session_state.server_url:
        st.session_state.server_url = input_url

    if st.session_state.server_url:
        st.success("✅ Server URL configured")
        if st.session_state.current_step == 1:
            st.session_state.current_step = 2

# Step 2: User Setup
if st.session_state.current_step >= 2:
    st.header("2. User Setup")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Create New User")
        new_user_name = st.text_input("Enter username")
        if st.button("Create User"):
            try:
                response = make_request_with_retry(
                    requests.post,
                    f"{st.session_state.server_url}/users",
                    data={"name": new_user_name}
                )
                if response.status_code == 200:
                    st.success(f"User created! ID: {response.json()['id']}")
                    st.session_state.user_id = response.json()['id']
                    if st.session_state.current_step == 2:
                        st.session_state.current_step = 3
                else:
                    st.error(f"Failed to create user: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col2:
        st.subheader("Existing User")
        user_id = st.text_input("Enter User ID", value=st.session_state.user_id or "")
        if user_id:
            st.session_state.user_id = user_id
            if st.session_state.current_step == 2:
                st.session_state.current_step = 3

    if st.session_state.user_id:
        st.success("✅ User configured")

# Step 3: Chatbot Setup
if st.session_state.current_step >= 3:
    st.header("3. Chatbot Setup")
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Create New Chatbot")
        new_bot_name = st.text_input("Chatbot Name")
        new_bot_desc = st.text_area("Description")
        if st.button("Create Chatbot"):
            try:
                response = make_request_with_retry(
                    requests.post,
                    f"{st.session_state.server_url}/chatbots",
                    data={
                        "user_id": st.session_state.user_id,
                        "name": new_bot_name,
                        "description": new_bot_desc
                    }
                )
                if response.status_code == 200:
                    st.success(f"Chatbot created! ID: {response.json()['id']}")
                    st.session_state.chatbot_id = response.json()['id']
                    if st.session_state.current_step == 3:
                        st.session_state.current_step = 4
                else:
                    st.error(f"Failed to create chatbot: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col4:
        st.subheader("Existing Chatbot")
        chatbot_id = st.text_input("Enter Chatbot ID", value=st.session_state.chatbot_id or "")
        if chatbot_id:
            st.session_state.chatbot_id = chatbot_id
            if st.session_state.current_step == 3:
                st.session_state.current_step = 4

    if st.session_state.chatbot_id:
        st.success("✅ Chatbot configured")

# Step 4: Knowledge Base and Configuration
if st.session_state.current_step >= 4:
    st.header("4. Knowledge Base Setup")
    
    # Chatbot Configuration
    st.subheader("Chatbot Settings")
    col5, col6, col7 = st.columns(3)
    with col5:
        temperature = st.slider("Temperature", 0.0, 1.0, 0.5)
    with col6:
        max_tokens = st.slider("Max Tokens", 100, 4000, 2000)
    with col7:
        k = st.slider("Top k Results", 1, 20, 10)

    if st.button("Update Settings"):
        try:
            response = make_request_with_retry(
                requests.post,
                f"{st.session_state.server_url}/chatbots/{st.session_state.chatbot_id}/configure",
                data={
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "k": k
                }
            )
            if response.status_code == 200:
                st.success("Settings updated!")
            else:
                st.error(f"Update failed: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # Knowledge Base Creation
    st.subheader("Create Knowledge Base")
    col8, col9 = st.columns(2)

    with col8:
        kb_name = st.text_input("Knowledge Base Name")
        kb_desc = st.text_area("Knowledge Base Description")
        if st.button("Create Knowledge Base"):
            try:
                response = make_request_with_retry(
                    requests.post,
                    f"{st.session_state.server_url}/knowledge-bases",
                    data={
                        "chatbot_id": st.session_state.chatbot_id,
                        "name": kb_name,
                        "description": kb_desc
                    }
                )
                if response.status_code == 200:
                    st.success(f"Knowledge base created! ID: {response.json()['id']}")
                    st.session_state['kb_id'] = response.json()['id']
                    if st.session_state.current_step == 4:
                        st.session_state.current_step = 5
                else:
                    st.error(f"Creation failed: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col9:
        kb_id = st.text_input("Or enter existing Knowledge Base ID", 
                             value=st.session_state.get('kb_id', ''))
        if kb_id:
            st.session_state['kb_id'] = kb_id
            if st.session_state.current_step == 4:
                st.session_state.current_step = 5

    if st.session_state.get('kb_id'):
        st.success("✅ Knowledge base configured")

# Step 5: Document Upload
if st.session_state.current_step >= 5:
    st.header("5. Document Upload")
    uploaded_file = st.file_uploader("Choose a file", type=['txt', 'csv', 'pdf'])
    
    if uploaded_file:
        if st.button("Upload Document"):
            try:
                files = {"file": uploaded_file}
                response = make_request_with_retry(
                    requests.post,
                    f"{st.session_state.server_url}/knowledge-bases/{st.session_state['kb_id']}/documents",
                    files=files
                )
                if response.status_code == 200:
                    st.success("Document uploaded successfully!")
                    if st.session_state.current_step == 5:
                        st.session_state.current_step = 6
                else:
                    st.error(f"Upload failed: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Step 6: Chat Interface
if st.session_state.current_step >= 6:
    st.header("6. Chat Interface")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "documents" in message:
                with st.expander("View Sources"):
                    for doc in message["documents"]:
                        st.markdown(f"**Document**: {doc['name']}")
                        st.markdown(f"**Preview**: {doc['preview']}")
                        if 'keywords' in doc and doc['keywords']:
                            st.markdown(f"**Keywords**: {', '.join(doc['keywords'])}")

    # Chat input
    user_query = st.chat_input("Ask a question...")

    if user_query:
        with st.chat_message("user"):
            st.write(user_query)
        
        st.session_state.chat_history.append({
            "role": "user", 
            "content": user_query
        })
        
        with st.chat_message("assistant"):
            with st.spinner('Processing...'):
                try:
                    response = make_request_with_retry(
                        requests.post,
                        f"{st.session_state.server_url}/query",
                        data={
                            "query": user_query,
                            "chatbot_id": st.session_state.chatbot_id,
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.write(result['answer'])
                        
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": result['answer'],
                            "documents": result.get('documents', [])
                        })
                        
                        if 'documents' in result and result['documents']:
                            with st.expander("View Sources"):
                                for doc in result['documents']:
                                    st.markdown(f"**Document**: {doc['name']}")
                                    st.markdown(f"**Preview**: {doc['preview']}")
                                    if 'keywords' in doc and doc['keywords']:
                                        st.markdown(f"**Keywords**: {', '.join(doc['keywords'])}")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
