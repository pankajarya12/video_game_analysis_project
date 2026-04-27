"""
auth.py — minimal username/password auth for the Streamlit app.

Stores users in config/users.yaml with bcrypt-hashed passwords.
Default seed users (change in production!):
    admin / admin123     (role: admin)
    analyst / analyst123 (role: viewer)
"""

from pathlib import Path
import yaml
import bcrypt
import streamlit as st

USERS_FILE = Path(__file__).resolve().parents[1] / "config" / "users.yaml"


def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _seed():
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        data = {
            "users": {
                "admin":   {"password": _hash("admin123"),   "role": "admin"},
                "analyst": {"password": _hash("analyst123"), "role": "viewer"},
            }
        }
        USERS_FILE.write_text(yaml.safe_dump(data))


def _load():
    _seed()
    return yaml.safe_load(USERS_FILE.read_text())


def login_form() -> bool:
    """Render a sidebar login form. Returns True when authenticated."""
    if st.session_state.get("auth_ok"):
        with st.sidebar:
            st.success(f"👤 {st.session_state['user']} ({st.session_state['role']})")
            if st.button("Logout"):
                for k in ("auth_ok", "user", "role"):
                    st.session_state.pop(k, None)
                st.rerun()
        return True

    st.title("🔐 Sign in")
    st.caption("Default: admin/admin123  •  analyst/analyst123")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        ok = st.form_submit_button("Sign in")
    if ok:
        users = _load()["users"]
        if u in users and bcrypt.checkpw(p.encode(), users[u]["password"].encode()):
            st.session_state["auth_ok"] = True
            st.session_state["user"] = u
            st.session_state["role"] = users[u]["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")
    return False
