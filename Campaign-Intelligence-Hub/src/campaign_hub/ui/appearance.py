"""Packaged decorative background with readable, opaque analytical surfaces."""
import base64
from pathlib import Path
import streamlit as st


@st.cache_data(max_entries=1, show_spinner=False)
def _background():
    path=Path(__file__).resolve().parents[3]/'assets/architecture-background.png'
    return base64.b64encode(path.read_bytes()).decode('ascii')


def apply_appearance():
    st.html('''<style>
    [data-testid="stAppViewContainer"] {
      background:linear-gradient(100deg,rgba(243,246,247,.93),rgba(243,246,247,.70)),
      url("data:image/png;base64,'''+_background()+'''") center top / cover fixed;
    }
    [data-testid="stHeader"] {background:rgba(243,246,247,.90)}
    [data-testid="stMainBlockContainer"] {max-width:1500px}
    [data-testid="stMetric"], [data-testid="stVerticalBlockBorderWrapper"] {
      background:rgba(255,255,255,.97);border-radius:14px;
      box-shadow:0 5px 22px rgba(16,38,61,.05);
    }
    [data-testid="stSidebar"] {border-right:1px solid #29455b}
    @media(max-width:640px) {
      [data-testid="stAppViewContainer"] {background-attachment:scroll}
    }
    </style>''')
