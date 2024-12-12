# ... [previous imports and configuration remain the same] ...

    # Button to submit query
    if st.button("Submit Query"):
        if user_query:
            with st.spinner('Processing your query...'):
                try:
                    response = make_request_with_retry(
                        requests.post,
                        f"{st.session_state.public_url}/query",
                        params={"query": user_query, "keywords": keywords}
                    )

                    st.subheader("Response from server:")
                    if response.status_code == 200 and response.content:
                        try:
                            result = response.json()

                            # Display keywords if they were used
                            if keywords:
                                st.info(f"Keywords used: {keywords}")

                            if 'answer' in result:
                                st.write(f"**Answer to your query:** {result['answer']}")
                            else:
                                st.error("No valid answer received.")

                            if 'chunks' in result:
                                st.write(f"**Retrieved Chunks:**")
                                for rank, chunk in enumerate(result["chunks"], 1):
                                    chunk_index = chunk.get('chunk_index', 'Unknown')
                                    with st.expander(f"Rank #{rank} (Chunk Index: {chunk_index})", expanded=False):
                                        st.markdown(f"**Source**: {chunk['source']}")
                                        st.markdown(f"**Score**: {chunk['score']}")
                                        st.markdown(f"**Chunk Index**: {chunk_index}")
                                        st.markdown(f"**Reference**: {chunk.get('reference', 'N/A')}")
                                        if chunk.get('keywords'):  # New: Display keywords for chunk
                                            st.markdown(f"**Keywords**: {chunk['keywords']}")
                                        st.write("**Content**:")
                                        st.text_area("", chunk['content'], height=150, disabled=True)
                                        st.markdown("---")

                        except ValueError:
                            st.error("Error parsing response.")
                    else:
                        st.warning("Received an empty response or error from the server.")
                except RequestException as e:
                    st.error(f"Error processing the query: {e}")

    # ... [previous conversation history code] ...

    # Updated conversation history display
    if show_history:
        try:
            history_response = make_request_with_retry(
                requests.get,
                f"{st.session_state.public_url}/conversation-history"
            )

            if history_response.status_code == 200:
                try:
                    history = history_response.json().get("conversation_history", [])
                    
                    if history:
                        st.subheader("Latest Conversation History:")
                        
                        latest_history = history[-10:]
                        
                        for history_idx, convo in enumerate(reversed(latest_history), 1):
                            with st.expander(f"History #{history_idx}: {convo.get('query', 'No query available')[:50]}...", expanded=False):
                                if isinstance(convo, dict):
                                    query = convo.get('query', 'No query available')
                                    answer = convo.get('answer', 'No answer available')
                                    timestamp = convo.get('timestamp', 'No timestamp available')
                                    keywords = convo.get('keywords', '')  # New: Get keywords from history

                                    if isinstance(timestamp, (int, float)):
                                        timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

                                    st.write(f"**Full Query:** {query}")
                                    if keywords:  # New: Display keywords in history
                                        st.write(f"**Keywords Used:** {keywords}")
                                    st.write(f"**Answer:** {answer}")
                                    st.write(f"**Timestamp:** {timestamp}")
                                else:
                                    st.warning("Invalid conversation entry: Not a valid dictionary")
                    else:
                        st.write("No conversation history available.")
                except ValueError as parse_error:
                    st.error(f"Error parsing the conversation history response: {parse_error}")
            else:
                st.warning(f"Failed to fetch conversation history. Status code: {history_response.status_code}")
        except RequestException as request_error:
            st.error(f"Error fetching conversation history: {request_error}")
