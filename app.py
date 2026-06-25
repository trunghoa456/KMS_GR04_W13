#!/usr/bin/env python3
"""Week 13 Dockerized Streamlit UI for the CityRise RAG chatbot."""

from __future__ import annotations

import os

import streamlit as st

from rag_engine import generate_answer, vector_persist_dir


def env_flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


st.set_page_config(page_title="CityRise Week 13 RAG Evaluation", layout="wide")

st.title("CityRise RAG Chatbot - Week 13")
st.caption("Dockerized RAG UI for benchmark testing, public/internal access checks, and demo evaluation.")

with st.sidebar:
    st.header("Evaluation Settings")
    provider_options = ["local", "auto", "ollama", "openai", "gemini"]
    default_provider = os.getenv("RAG_PROVIDER", "local")
    provider_index = provider_options.index(default_provider) if default_provider in provider_options else 0
    audience_options = ["public", "internal"]
    default_audience = "internal" if os.getenv("RAG_AUDIENCE", "public") == "internal" else "public"
    audience_index = audience_options.index(default_audience) if default_audience in audience_options else 0

    if env_flag("RAG_ALLOW_ROLE_SWITCH"):
        audience = st.radio("Audience / role filter", audience_options, index=audience_index)
    else:
        audience = default_audience
        st.text_input("Audience / role filter", value=audience, disabled=True)
    provider = st.selectbox("LLM provider", provider_options, index=provider_index)
    top_k = st.slider("Top-K context chunks", min_value=1, max_value=10, value=int(os.getenv("RAG_TOP_K", "4")), step=1)
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=float(os.getenv("RAG_TEMPERATURE", "0.2")),
        step=0.05,
    )
    max_context_chars = st.slider(
        "Max context characters",
        min_value=800,
        max_value=8000,
        value=int(os.getenv("RAG_MAX_CONTEXT_CHARS", "4000")),
        step=400,
    )
    st.divider()
    st.write("Vector DB")
    st.code(str(vector_persist_dir()))
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Xin chao. Hay chon public/internal o sidebar va hoi ve CityRise products, "
                "sales, purchase, helpdesk, employees hoac security benchmark cases."
            ),
            "sources": [],
            "warning": "",
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("warning"):
            st.warning(message["warning"])
        if message.get("sources"):
            st.caption("Nguon: " + ", ".join(message["sources"]))

prompt = st.chat_input("Nhap cau hoi benchmark cho CityRise RAG...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Dang truy van Vector DB va tao cau tra loi..."):
            result = generate_answer(
                prompt,
                top_k=top_k,
                temperature=temperature,
                audience=audience,
                provider=provider,
                max_context_chars=max_context_chars,
            )
        if result.get("fallback"):
            st.warning(result.get("warning") or "fallback")
        st.write(result["answer"])
        if result.get("sources"):
            st.caption("Nguon: " + ", ".join(result["sources"]))

        with st.expander("Retrieved context"):
            for chunk in result.get("chunks", []):
                st.markdown(f"**{chunk['title']}** - `{chunk['access_role']}` / `{chunk['source_model']}`")
                st.write(chunk["content"])

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result.get("sources", []),
            "warning": result.get("warning", "") if result.get("fallback") else "",
        }
    )
