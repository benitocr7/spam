import streamlit as st
from email_manager import EmailManager

st.set_page_config(page_title="Spam Detector", page_icon="📩", layout="wide")

# ---------- Session ----------
CURRENT_VERSION = "1.4" # Force update

if "app_version" not in st.session_state or st.session_state.app_version != CURRENT_VERSION:
    st.session_state.manager = EmailManager()
    st.session_state.app_version = CURRENT_VERSION
    st.rerun() # Reload immediately with new manager

if "manager" not in st.session_state:
    st.session_state.manager = EmailManager()

if "credentials" not in st.session_state:
    st.session_state.credentials = {"user": "", "pass": ""}

manager = st.session_state.manager


# ---------- Styles ----------
st.markdown("""
<style>
    color: #5f6368;
    margin-left: 10px;
    white-space: nowrap;
}
</style>
""", unsafe_allow_html=True)


# ---------- Sidebar ----------
with st.sidebar:
    st.title("📬 Mail")
    
    mode = st.radio("Mode", ["Demo (Fake)", "Real (Gmail)"])

    if mode == "Real (Gmail)":
        st.info("⚠️ Use App Password, NOT login password.")
        
        # Persistent inputs
        user_input = st.text_input("Gmail", value=st.session_state.credentials["user"])
        pass_input = st.text_input("App Password", type="password", value=st.session_state.credentials["pass"])
        
        # Save on change
        st.session_state.credentials["user"] = user_input
        st.session_state.credentials["pass"] = pass_input
        
        # Faster refresh for "instant" feel
        auto_refresh = st.checkbox("⚡ Live Updates (2s)", value=True)

        if st.session_state.credentials["user"] and st.session_state.credentials["pass"]:
            # Status indicator
            
            # Efficient connection check
            success, status = manager.ensure_connection(
                st.session_state.credentials["user"], 
                st.session_state.credentials["pass"]
            )
            
            if success:
                # Removed st.success to prevent flickering/jumping layout
                st.caption(f"🟢 Connected: {st.session_state.credentials['user']}")
                
                msgs = manager.fetch_real_emails()
                if msgs:
                    # check for new ones before processing to avoid unnecessary work? 
                    # app logic handles dupes, so just extend.
                    manager.incoming_messages.extend(msgs)
                    manager.process_incoming_messages()
            else:
                st.error(f"🔴 Connection failed: {status}")

    st.divider()

    if mode == "Demo (Fake)":
        if st.button("📥 Simulate New Message"):
            manager.mock_incoming_message()
            manager.process_incoming_messages()


# ---------- Main ----------
st.title("Spam Detector")

# ---------- Styles & Config ----------
st.markdown("""
<style>
    /* Global Font & Reset */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dashboard Metrics */
    .metric-card {
        background-color: #262730;
        border: 1px solid #3F4350;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #FFFFFF;
    }
    .metric-label {
        font-size: 12px;
        color: #A0A0A0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Email Card - Premium Look */
    .email-card {
        background-color: #1E1E24;
        border-left: 4px solid #4CAF50; /* Default legit color */
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .email-card:hover {
        transform: translateX(4px);
        background-color: #25252D;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .email-card.spam {
        border-left-color: #FF5252;
    }
    
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 12px; /* Soft square */
        background: linear-gradient(135deg, #6C63FF 0%, #3F3D56 100%);
        color: white;
        display: flex;
        justify-content: center;
        align-items: center;
        font-weight: 600;
        font-size: 18px;
        margin-right: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    .sender-name {
        font-size: 15px;
        font-weight: 600;
        color: #EAEAEA;
    }
    .email-subject {
        font-size: 14px;
        color: #BBBBBB;
        margin: 2px 0 4px 0;
    }
    .email-snippet {
        font-size: 12px;
        color: #777777;
        font-style: italic;
    }

    /* Clean up Streamlit UI */
    .stCheckbox {
        padding-top: 10px;
    }
    div[data-testid="stExpander"] {
        border: none;
        box-shadow: none;
        background-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Dashboard Header ----------
c1, c2, c3, c4 = st.columns(4)
total = len(manager.inbox_folder) + len(manager.spam_folder)
spam_count = len(manager.spam_folder)
spam_ratio = int((spam_count / total * 100)) if total > 0 else 0

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total}</div>
        <div class="metric-label">Total Correos</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(manager.inbox_folder)}</div>
        <div class="metric-label">Bandeja Entrada</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #FF5252;">{spam_count}</div>
        <div class="metric-label">Spam Detectado</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{spam_ratio}%</div>
        <div class="metric-label">Tasa de Filtrado</div>
    </div>
    """, unsafe_allow_html=True)

st.write("") # Spacer

# Use Tabs for clear, physical separation
tab_inbox, tab_spam = st.tabs([f"📥 Inbox ({len(manager.inbox_folder)})", f"🚫 Spam ({len(manager.spam_folder)})"])

def paginated_list(messages, page_size=10, key_prefix="inbox"):
    total_items = len(messages)
    if total_items == 0:
        return []
    
    # Pagination Controls
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    
    # Session state for current page
    page_key = f"page_{key_prefix}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
        
    c1, c2, c3 = st.columns([2, 3, 2])
    with c2:
        current_page = st.number_input(f"Página (1-{total_pages})", min_value=1, max_value=total_pages, value=st.session_state[page_key], key=f"num_{key_prefix}")
        st.session_state[page_key] = current_page
    
    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    
    return messages[start_idx:end_idx]

def render_email(msg, source_folder="inbox"):
    sender = msg.get('sender', 'Unknown')
    subject = msg.get('subject', 'No Subject')
    body = msg.get('body', '')
    full_body = msg.get('full_body', '')
    initial = sender[0].upper() if sender else "?"
    msg_id = msg.get('id', 'unknown')

    score = msg.get("spam_score", 0.0)
    reason = msg.get("spam_reason", "")
    
    # Layout: Checkbox | Avatar+Content
    # Using a tighter ratio to keep them close
    c_check, c_card = st.columns([0.05, 0.95]) 
    
    with c_check:
        # Checkbox for selection 
        # centered vertically by CSS usually, but let's just place it raw
        st.checkbox("", key=f"sel_{msg_id}", label_visibility="collapsed")
    
    border_class = "spam" if score > 0.5 or source_folder == "spam" else ""
    
    with c_card:
        st.markdown(f"""
        <div class="email-card {border_class}">
            <div style="display:flex; align-items:center;">
                <div class="avatar">{initial}</div>
                <div class="content">
                    <div class="sender-name">{sender}</div>
                    <div class="email-subject">{subject}</div>
                    <div class="email-snippet">{body}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Analysis Data simplified (Outside card to not break layout)
        if score > 0.1 or source_folder == "spam":
            with st.expander(f"🕵️ Ver Análisis ({int(score*100)}%)"):
                st.caption(f"**Diagnóstico:** {reason}")
                st.code(full_body[:300], language="html")

# --- Inbox Tab ---
with tab_inbox:
    st.write(f"Total: {len(manager.inbox_folder)} correos")
    if len(manager.inbox_folder) == 0:
        st.info("Inbox vacío - ¡Todo limpio!")
    else:
        with st.form("inbox_form", clear_on_submit=True):
            st.caption("Selecciona y mueve a Spam.")
            
            # Get Paginated Subset
            # Sort newest first
            sorted_msgs = list(reversed(manager.inbox_folder))
            visible_msgs = paginated_list(sorted_msgs, page_size=8, key_prefix="inbox")
            
            for msg in visible_msgs:
                render_email(msg, source_folder="inbox")
            
            st.divider()
            # Batch Action
            if st.form_submit_button("🚨 Mover Selección a Spam", type="primary"):
                moved_count = 0
                to_remove = []
                for msg in manager.inbox_folder: 
                    msg_id = msg.get('id')
                    if st.session_state.get(f"sel_{msg_id}"):
                        to_remove.append(msg)
                
                for msg in to_remove:
                    manager.inbox_folder.remove(msg)
                    manager.spam_folder.append(msg)
                    moved_count += 1
                
                if moved_count > 0:
                    st.toast(f"🚨 {moved_count} mensajes movidos a SPAM", icon="🗑️")
                    import time
                    time.sleep(1)
                    st.rerun()

# --- Spam Tab ---
with tab_spam:
    st.write(f"Total: {len(manager.spam_folder)} correos")
    if len(manager.spam_folder) == 0:
        st.info("No hay spam")
    else:
        with st.form("spam_form", clear_on_submit=True):
            st.caption("Recuperar mensajes falsos positivos.")
            
            sorted_spam = list(reversed(manager.spam_folder))
            visible_spam = paginated_list(sorted_spam, page_size=8, key_prefix="spam")
            
            for msg in visible_spam:
                render_email(msg, source_folder="spam")
            
            st.divider()
            if st.form_submit_button("✅ Recuperar a Inbox"):
                moved_count = 0
                to_remove = []
                for msg in manager.spam_folder:
                    msg_id = msg.get('id')
                    if st.session_state.get(f"sel_{msg_id}"):
                        to_remove.append(msg)
                
                for msg in to_remove:
                    manager.spam_folder.remove(msg)
                    manager.inbox_folder.append(msg)
                    moved_count += 1
                
                if moved_count > 0:
                    st.toast(f"✅ ¡Éxito! {moved_count} mensajes procesados.", icon="🎉")
                    time.sleep(1) # Brief pause to let toast show before rerun
                    st.rerun()
