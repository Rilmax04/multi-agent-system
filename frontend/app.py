import streamlit as st
import requests
import uuid
from datetime import datetime
import json

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000"
DEFAULT_MODEL = "gemini"
SAMPLE_QUESTIONS = [
    "Проанализируй динамику Bitcoin и Ethereum за последние 30 дней.",
    "Какие факторы влияют на рост Solana?",
    "Сравни капитализацию BTC и ETH.",
    "Как изменение цены BTC влияет на рынок альткоинов?",
]


# --- Helper Functions ---
def post_to_backend(endpoint: str, data: dict):
    """Send POST request to backend."""
    try:
        response = requests.post(f"{BACKEND_URL}{endpoint}", json=data, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Ошибка соединения с сервером: {e}")
        return None


def create_new_chat():
    """Create a new chat session."""
    frontend_chat_id = str(uuid.uuid4())
    st.session_state.chats[frontend_chat_id] = {
        "name": "Чат",
        "messages": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    st.session_state.current_chat_id = frontend_chat_id


def get_sorted_chat_ids():
    """Return sorted chat IDs by creation time."""
    return sorted(
        st.session_state.chats.keys(),
        key=lambda cid: st.session_state.chats[cid]["created_at"],
        reverse=True,
    )


def handle_user_input(user_input):
    """Send user message to backend and append assistant reply."""
    current_chat = st.session_state.chats[st.session_state.current_chat_id]

    # Add user message
    current_chat["messages"].append(
        {
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M"),
        }
    )

    with st.spinner("🤖 Генерация ответа..."):
        data = {"question": user_input}
        response = post_to_backend("/ask", data)

        if response and "answer" in response:
            answer = response["answer"]
        else:
            answer = "⚠️ Не удалось получить ответ от модели."

        current_chat["messages"].append(
            {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": answer,
                "timestamp": datetime.now().strftime("%H:%M"),
            }
        )


def delete_chat(chat_id):
    del st.session_state.chats[chat_id]
    if st.session_state.current_chat_id == chat_id:
        st.session_state.current_chat_id = None
    st.rerun()


def render_message(message):
    """Display chat message with style."""
    col = st.columns([0.1, 0.9])
    with col[0]:
        st.markdown("👤" if message["role"] == "user" else "🤖")
    with col[1]:
        msg_class = "user-message" if message["role"] == "user" else "bot-message"
        with st.container():
            st.markdown(
                f"<div class='chat-message {msg_class}'>"
                f"<div class='message-text'>{message['content']}</div>"
                f"<div class='message-time'>{message['timestamp']}</div>"
                "</div>",
                unsafe_allow_html=True,
            )


# --- Session State Initialization ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --- Custom CSS ---
st.markdown(
    """
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-message {
        background: #e8f4ff;
        border-left: 4px solid #2b73b7;
    }
    .bot-message {
        background: #f5f7fa;
        border-left: 4px solid #4a5568;
    }
    .message-text {
        margin-bottom: 0.5rem;
        line-height: 1.6;
    }
    .message-time {
        color: #718096;
        font-size: 0.8rem;
        text-align: right;
    }
    .stButton>button {
        min-width: 40px;
        padding: 0.2rem 0.5rem;
    }
    .sample-question {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.2s;
    }
    .sample-question:hover {
        background: #f7fafc;
        transform: translateY(-2px);
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- Sidebar ---
with st.sidebar:
    st.title("💬 Мои чаты")

    if st.button("✨ Новый чат", use_container_width=True, type="primary"):
        create_new_chat()
        st.rerun()

    st.write("---")
    if st.session_state.chats:
        for chat_id in get_sorted_chat_ids():
            chat = st.session_state.chats[chat_id]
            cols = st.columns([0.8, 0.2])
            with cols[0]:
                btn_type = (
                    "primary"
                    if chat_id == st.session_state.current_chat_id
                    else "secondary"
                )
                if st.button(
                    f"{chat['name']}",
                    key=f"btn_{chat_id}",
                    use_container_width=True,
                    type=btn_type,
                ):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with cols[1]:
                if st.button("🗑️", key=f"del_{chat_id}", help="Удалить чат"):
                    delete_chat(chat_id)

# --- Main Interface ---
if st.session_state.current_chat_id in st.session_state.chats:
    current_chat = st.session_state.chats[st.session_state.current_chat_id]

    st.subheader(current_chat["name"])

    for msg in current_chat["messages"]:
        render_message(msg)

    st.write("---")
    st.markdown("**Примеры запросов:**")
    cols = st.columns(2)
    for i, question in enumerate(SAMPLE_QUESTIONS):
        with cols[i % 2]:
            if st.button(question, key=f"sample_{i}"):
                handle_user_input(question)
                st.rerun()

    user_input = st.chat_input("Введите ваш вопрос...")
    if user_input:
        handle_user_input(user_input)
        st.rerun()

else:
    st.markdown(
        "<h2 style='text-align: center; margin-top: 3rem'>Добро пожаловать! 💬</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center'>Начните новый чат, чтобы задать вопрос</p>",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Начать новый чат", use_container_width=True, type="primary"):
            create_new_chat()
            st.rerun()
