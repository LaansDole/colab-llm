import streamlit as st
import requests
import json
import time
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Local LLM Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get API URL from user input or environment
if "api_url" not in st.session_state:
    st.session_state.api_url = ""

if "model_name" not in st.session_state:
    st.session_state.model_name = "maryasov/qwen2.5-coder-cline:7b-instruct-q8_0"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a helpful AI assistant."

# Function to format conversation history for API
def format_prompt(message, history, system_prompt=None):
    """Format the message and history into a prompt for the API."""
    formatted_prompt = ""
    
    # Add system prompt if provided
    if system_prompt:
        formatted_prompt = f"{system_prompt}\n\n"
    
    # Add conversation history
    for msg in history:
        if msg["role"] == "user":
            formatted_prompt += f"User: {msg['content']}\n\n"
        else:
            formatted_prompt += f"Assistant: {msg['content']}\n\n"
    
    # Add the current message
    formatted_prompt += f"User: {message}\n\nAssistant: "
    
    return formatted_prompt

# Function to validate API URL
def is_valid_url(url):
    """Check if a URL is properly formatted."""
    if not url:
        return False
    # Basic URL validation
    return url.startswith(("http://", "https://"))

# Function to chat with the LLM
def chat_with_llm(message, api_url, model_name, temperature, top_p, max_tokens):
    """Send a message to the LLM API and get a response."""
    if not message.strip():
        return "Please enter a message.", ""
    
    if not is_valid_url(api_url):
        return "Please enter a valid API URL starting with http:// or https://.", ""
    
    # Format conversation history
    history = st.session_state.messages.copy()
    formatted_prompt = format_prompt(message, history, st.session_state.system_prompt)
    
    # Prepare data for API request
    data = {
        "model": model_name,
        "prompt": formatted_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens
        }
    }
    
    try:
        # Send request to Ollama API
        start_time = time.time()
        response = requests.post(f"{api_url}/api/generate", json=data, timeout=120)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            bot_response = result.get('response', 'No response generated.')
            
            # Get token metrics if available
            eval_count = result.get('eval_count', 0)
            
            # Add messages to history
            st.session_state.messages.append({"role": "user", "content": message})
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            
            return bot_response, f"Generated {eval_count} tokens in {response_time:.2f}s ({eval_count/response_time:.1f} tokens/s)"
        else:
            return f"⚠️ Error: API returned status code {response.status_code}", ""
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. The model might be taking too long to respond.", ""
    except requests.exceptions.ConnectionError:
        return "🔌 Connection error. Please check if the API URL is correct and the service is running.", ""
    except Exception as e:
        return f"❌ Error: {str(e)}", ""

# Function to clear chat history
def clear_chat():
    st.session_state.messages = []

# Main interface
st.title("🤖 Local LLM Chat Interface")
st.markdown("Chat with your locally running LLM via Ollama")

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API URL input
    api_url = st.text_input(
        "API URL", 
        value=st.session_state.api_url,
        placeholder="https://your-ollama-url.trycloudflare.com",
        help="Enter the Cloudflare tunnel URL to your Ollama API"
    )
    
    if api_url != st.session_state.api_url:
        st.session_state.api_url = api_url
    
    # Model selection
    model_name = st.text_input(
        "Model Name",
        value=st.session_state.model_name,
        help="Enter the model name to use for chat"
    )
    
    if model_name != st.session_state.model_name:
        st.session_state.model_name = model_name
    
    # System prompt
    system_prompt = st.text_area(
        "System Prompt",
        value=st.session_state.system_prompt,
        help="Sets the personality/behavior of the AI"
    )
    
    if system_prompt != st.session_state.system_prompt:
        st.session_state.system_prompt = system_prompt
    
    # Generation parameters
    st.subheader("Generation Parameters")
    
    temperature = st.slider(
        "Temperature",
        min_value=0.1,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Controls randomness (lower = more focused)"
    )
    
    top_p = st.slider(
        "Top P",
        min_value=0.1,
        max_value=1.0,
        value=0.9,
        step=0.05,
        help="Controls diversity (lower = more focused)"
    )
    
    max_tokens = st.slider(
        "Max Tokens",
        min_value=100,
        max_value=4096,
        value=2048,
        step=100,
        help="Maximum response length"
    )
    
    # Clear chat button
    if st.button("Clear Chat History"):
        clear_chat()
        st.success("Chat history cleared!")
    
    # Save conversation button
    if st.button("Save Conversation"):
        if st.session_state.messages:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create conversations directory if it doesn't exist
            import os
            os.makedirs("conversations", exist_ok=True)
            
            filename = f"conversations/conversation_{timestamp}.json"
            
            try:
                # Save to conversations directory
                with open(filename, "w") as f:
                    json.dump(st.session_state.messages, f, indent=2)
                
                st.success(f"Conversation saved to {filename}")
            except Exception as e:
                st.error(f"Failed to save conversation: {str(e)}")
        else:
            st.error("No conversation to save.")

# Chat message display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_input = st.chat_input("Type your message here...")

# Handle chat input
if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get bot response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        metrics_placeholder = st.empty()
        
        with st.spinner("Thinking..."):
            response, metrics = chat_with_llm(
                user_input, 
                st.session_state.api_url,
                st.session_state.model_name,
                temperature,
                top_p,
                max_tokens
            )
        
        message_placeholder.markdown(response)
        if metrics:
            metrics_placeholder.markdown(f"<small>{metrics}</small>", unsafe_allow_html=True)

# Display API status
st.sidebar.divider()
st.sidebar.subheader("API Status")

if st.session_state.api_url:
    if not is_valid_url(st.session_state.api_url):
        st.sidebar.error("❌ Invalid API URL format")
    else:
        try:
            # Try to reach the API health endpoint or models endpoint
            response = requests.get(f"{st.session_state.api_url}/api/version", timeout=5)
            if response.status_code == 200:
                st.sidebar.success(f"✅ API is reachable (Ollama version: {response.json().get('version', 'unknown')})")
            else:
                st.sidebar.warning(f"⚠️ API returned status code {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.sidebar.error("❌ API connection failed")
        except requests.exceptions.Timeout:
            st.sidebar.error("❌ API request timed out")
        except Exception as e:
            st.sidebar.error(f"❌ API check failed: {str(e)}")
else:
    st.sidebar.warning("⚠️ API URL not set")
