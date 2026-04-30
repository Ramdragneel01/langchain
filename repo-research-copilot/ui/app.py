from __future__ import annotations

import os

import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://127.0.0.1:8010")
API_KEY_HEADER_NAME = os.getenv("API_KEY_HEADER_NAME", "X-API-Key")

st.set_page_config(page_title="Repo Research Copilot", page_icon="🔎", layout="wide")
st.title("Repo Research Copilot")
st.caption("Ask technical questions about an indexed repository and review source citations.")

with st.sidebar:
    st.header("Settings")
    api_url = st.text_input("API URL", value=API_URL)
    api_key_header_name = st.text_input(
        "API key header",
        value=API_KEY_HEADER_NAME,
        help="Header name expected by API auth middleware.",
    )
    api_key = st.text_input(
        "API key",
        value=os.getenv("API_KEY", ""),
        type="password",
    )
    k = st.slider("Top-K sources", min_value=1, max_value=20, value=5)

question = st.text_area(
    "Question",
    value="Where is API routing initialized?",
    height=120,
)

if st.button("Ask", type="primary"):
    if not question.strip():
        st.warning("Enter a question before submitting.")
    else:
        headers: dict[str, str] = {}
        if api_key.strip():
            headers[api_key_header_name] = api_key.strip()

        try:
            response = requests.post(
                f"{api_url.rstrip('/')}/ask",
                json={"question": question, "k": k},
                headers=headers,
                timeout=90,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            st.error(f"Request failed: {exc}")
        else:
            st.subheader("Answer")
            st.write(data.get("answer", ""))

            st.subheader("Sources")
            sources = data.get("sources", [])
            if not sources:
                st.info("No sources returned.")
            for idx, source in enumerate(sources, start=1):
                title = f"{idx}. {source.get('path', 'unknown')} ({source.get('chunk_id', '-')})"
                with st.expander(title, expanded=(idx == 1)):
                    st.write(f"Score: {source.get('score', 0)}")
                    st.write(source.get("excerpt", ""))
