import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timedelta
import json
from database import TodoDatabase

# Load environment variables
load_dotenv()

# Initialize database
db = TodoDatabase()

# Configure OpenAI client with X.AI API key
client = OpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.x.ai/v1"
)

# Set page config
st.set_page_config(
    page_title="Grok Todo Assistant",
    page_icon="📝",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .todo-table {
        width: 100%;
        margin-bottom: 1rem;
        font-family: 'Arial', sans-serif;
    }
    .stButton button {
        background: none;
        border: none;
        color: #e74c3c;
        cursor: pointer;
        opacity: 0.6;
        transition: all 0.2s;
        font-size: 18px;
        padding: 4px;
        border-radius: 4px;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .stButton button:hover {
        opacity: 1;
        background-color: #fee;
    }
    .todo-description {
        font-size: 15px;
        color: #2c3e50;
        font-weight: 400;
        padding: 8px;
    }
    .todo-datetime {
        font-size: 14px;
        color: #666;
        white-space: nowrap;
        padding: 8px;
    }
    .stTextInput > div > div > input {
        background-color: #f8f9fa;
        border: 1px solid #eee;
        border-radius: 4px;
        padding: 8px;
        font-size: 15px;
        font-family: 'Arial', sans-serif;
        width: 100%;
        color: #2c3e50;
    }
    .stTextInput > div {
        padding: 0;
    }
    button[data-testid="baseButton-secondary"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

def get_grok_response(prompt):
    try:
        # Get current date and time for context
        current_datetime = datetime.now().strftime("%B %d, %Y %H:%M")
        
        # Add current date context to the prompt
        contextual_prompt = f"Current date and time is: {current_datetime}\nUser request: {prompt}"
        
        response = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {"role": "system", "content": """You are a helpful task assistant. Your job is to:
                1. Extract the core task description (without any date/time information)
                2. Extract the date and time mentioned in the request

                When responding:
                - Remove ALL date and time information from the task description
                - Convert relative dates (tomorrow, next week) to actual dates
                - Use the current date as reference
                - Format dates as 'Month DD, YYYY HH:MMam/pm'
                
                Example responses:
                Input: "Call mom tomorrow at 2pm"
                Response: Task: Call mom | Date: March 16, 2024 2:00pm

                Example responses:
                Input: "Remind me to go to temple next friday morning 5am"
                Response: Task: Go to temple | Date: November 29, 2024 5:00am

                Input: "Submit report by next Friday 3pm"
                Response: Task: Submit report | Date: March 22, 2024 3:00pm

                Input: "Team meeting on March 20th at 10:30am"
                Response: Task: Team meeting | Date: March 20, 2024 10:30am

                Always use the | symbol to separate task and date."""},
                {"role": "user", "content": contextual_prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def parse_grok_response(response_text):
    """Parse Grok's response to extract task details"""
    try:
        # Split response into task and date parts
        if "|" in response_text:
            parts = response_text.split("|")
            task_part = parts[0].strip()
            date_part = parts[1].strip()
            
            # Extract task (remove "Task:" prefix if present)
            task = task_part.replace("Task:", "").strip()
            
            # Extract date (remove "Date:" prefix if present)
            date_str = date_part.replace("Date:", "").strip()
            
            try:
                # Parse the date string to ensure it's valid
                dt = datetime.strptime(date_str, "%B %d, %Y %I:%M%p")
                formatted_date = dt.strftime("%Y-%m-%d %H:%M")
            except:
                # If date parsing fails, use the original date string
                formatted_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            return {
                "description": task,
                "datetime": formatted_date
            }
        else:
            # Fallback if response doesn't contain the separator
            return {
                "description": response_text,
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
    except Exception as e:
        st.error(f"Error parsing response: {str(e)}")
        return None

def format_datetime(datetime_str):
    """Convert datetime string to desired format"""
    try:
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        return dt.strftime("%B %d, %Y %I:%M%p").replace(" 0", " ").replace("AM", "am").replace("PM", "pm")
    except:
        return datetime_str

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display title
st.title("📝 Grok Todo Assistant")

# Display Todo List Section
st.header("Todo List")

# Get todos from database
todos = db.get_all_todos()

if not todos:
    st.info("No tasks yet. Start adding tasks through the chat!")
else:
    # Initialize session state for editing
    if 'editing_todo' not in st.session_state:
        st.session_state.editing_todo = None
        
    def save_edit(todo_id):
        # Get the value from session state
        edit_key = f"edit_{todo_id}"
        if edit_key in st.session_state:
            new_value = st.session_state[edit_key]
            if isinstance(new_value, str) and new_value.strip():
                db.update_todo_description(todo_id, new_value)
        st.session_state.editing_todo = None
        st.rerun()
    
    for todo in todos:
        formatted_datetime = format_datetime(todo['datetime'])
        
        col1, col2, col3 = st.columns([6, 3.5, 0.5])
        
        with col1:
            if st.session_state.editing_todo == todo['id']:
                # Initialize the session state for this todo's edit field
                if f"edit_{todo['id']}" not in st.session_state:
                    st.session_state[f"edit_{todo['id']}"] = todo['description']
                
                # Show text input for editing
                edited_text = st.text_input(
                    "Edit task",
                    key=f"edit_{todo['id']}",
                    value=todo['description'],
                    on_change=save_edit,
                    args=(todo['id'],),
                    label_visibility="collapsed"
                )
            else:
                # Show clickable description
                if st.markdown(
                    f'''<div class="todo-description" 
                        onclick="document.getElementById('edit_{todo['id']}').click()"
                        style="cursor: pointer;">{todo['description']}</div>''',
                    unsafe_allow_html=True
                ):
                    pass
                
                # Hidden button to enable edit mode
                if st.button("", key=f"edit_{todo['id']}", type="secondary"):
                    st.session_state.editing_todo = todo['id']
                    st.rerun()
        
        with col2:
            st.markdown(f'<div class="todo-datetime">{formatted_datetime}</div>', unsafe_allow_html=True)
        
        with col3:
            if st.button('🗑️', key=f'delete_{todo["id"]}'):
                db.delete_todo(todo['id'])
                st.rerun()

# Divider
st.markdown("---")

# Chat Section
st.header("Chat")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your task here (e.g., 'Remind me to call mom tomorrow at 2pm')"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            response = get_grok_response(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Parse the response and add to database
            parsed_task = parse_grok_response(response)
            if parsed_task:
                db.add_todo(
                    description=parsed_task["description"],
                    datetime_str=parsed_task["datetime"]
                )
                st.success("Task added to the todo list!")
                st.rerun()

# Sidebar
with st.sidebar:
    st.title("Options")
    if st.button("Clear All Tasks"):
        db.clear_all_todos()
        st.rerun()
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("""
    ### Tips
    - Add tasks with specific dates and times
    - Delete tasks using the 🗑️ button
    - Clear all tasks or chat history using the sidebar buttons
    
    Made with ❤️ using Streamlit and Grok
    """)
