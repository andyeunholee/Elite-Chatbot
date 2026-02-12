import streamlit as st
import asyncio
from agent import agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Page Config
st.set_page_config(page_title="Elite U.S. College Advisor", page_icon="🎓")

# Display Logo and Title
col1, col2 = st.columns([1, 5])
with col1:
    st.image("elitelogo-Blue-removebg-preview.png", width=80)
with col2:
    st.title("Elite U.S. College Advisor")

# Removed caption as requested
# st.caption("Powered by Google Gemini & Tavily Search")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        SystemMessage(content="You are an elite US college admissions AI consultant named 'Genny', serving students nationwide (California, Georgia, etc.). Your role is to provide comprehensive, up-to-date news and strategic advice on US university admissions. Always use the search tool to find the latest specific local data when asked. IMPORTANT: Answer in the SAME language as the user's question. If the user asks in Korean, answer in Korean. If in English, answer in English."),
        AIMessage(content="Hello! I am **Genny**, an AI Agent specializing in US college admissions consulting.\n\nAsk me anything!")
    ]

# Display Chat History
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(msg.content)

# Handle User Input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message to state
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process with Agent
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Create a container for status updates (tool calls)
        status_container = st.status("Thinking...", expanded=False)
        
        try:
            # Optimize inputs for the graph
            # We only need to send recent messages to save context limits if necessary, 
            # but LangGraph handles memory well.
            input_messages = st.session_state.messages
            
            # Stream the graph execution
            # stream_mode="updates" allows us to see intermediate steps (tool calls)
            for event in agent.stream({"messages": input_messages}, stream_mode="updates"):
                for node_name, node_output in event.items():
                    if node_name == "chatbot":
                        # The LLM generated a message (either a tool call or a final answer)
                        message = node_output["messages"][-1]
                        if message.tool_calls:
                            status_container.update(label="Searching the web...", state="running", expanded=True)
                            for tool_call in message.tool_calls:
                                status_container.write(f"🔍 Searching: {tool_call['args']}")
                        else:
                            # Final answer (or intermediate thought)
                            full_response = message.content
                    
                    elif node_name == "tools":
                        # The tool executed
                        status_container.update(label="Reading results...", state="running", expanded=True)
                        tool_message = node_output["messages"][-1]
                        status_container.write("✅ Found results.")
            
            status_container.update(label="Finished!", state="complete", expanded=False)
            message_placeholder.markdown(full_response)
            
            # Save assistant response to state
            st.session_state.messages.append(AIMessage(content=full_response))
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
