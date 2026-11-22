"""Meeting Notes to Action Agent: The AI agent for meeting minutes and action tracking.

Turns rough meeting notes into a clear list of decisions and action items with owners.
Works immediately in Demo Mode with simple rules, or with a real AI model (OpenAI, Gemini, DeepSeek).
"""
from __future__ import annotations

import importlib
import os

import pandas as pd
import streamlit as st

import agent
importlib.reload(agent)
from agent import run, to_markdown
from demo import SECTIONS
from prompts import SYSTEM_PROMPT

st.set_page_config(page_title="Meeting Notes to Action Agent", page_icon="🎯", layout="wide")


def setting(name: str, default: str = "") -> str:
    """Read a setting from Streamlit secrets first, then from the environment."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, default)).strip()


API_KEY = setting("AI_API_KEY")
BASE_URL = setting("AI_BASE_URL", "https://api.openai.com/v1")
MODEL = setting("AI_MODEL", "gpt-4o-mini")

STATUS_COLOUR = {"Green": "#16a34a", "Amber": "#d97706", "Red": "#dc2626"}
SECTION_ICON = {
    "Decisions": "🎯",
    "Action items": "✅",
    "Discussion": "💬",
    "Blockers": "⛔",
    "Next steps": "📅",
}

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.8rem; max-width: 1160px;}
      .hero {background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color: #fff; padding: 22px 26px;
             border-radius: 14px; margin-bottom: 16px;}
      .hero h1 {font-size: 1.75rem; margin: 0 0 6px 0; color: #fff; font-weight: 700;}
      .hero p {margin: 0; opacity: .88; font-size: 1rem;}
      .card {background: #ffffff; color: #0f172a; border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px 18px; margin-bottom: 12px;
             box-shadow: 0 1px 2px rgba(0,0,0,.04);}
      .card h4 {margin: 0 0 8px 0; font-size: 1.02rem; font-weight: 600;}
      .item {padding: 7px 0; border-top: 1px dashed #eef0f3; font-size: .95rem; line-height: 1.45;}
      .item:first-of-type {border-top: none;}
      .tag {display: inline-block; font-size: .75rem; padding: 2px 8px; border-radius: 999px; background: #eef2ff; color: #3730a3;
            margin-left: 6px; font-weight: 500;}
      .status {display: inline-block; color: #fff; font-weight: 700; padding: 6px 14px; border-radius: 999px; font-size: 0.95rem;}
      .step {color: #0f172a; padding: 9px 12px; border-left: 4px solid #16a34a; background: #f8fafc; margin-bottom: 8px; border-radius: 6px;}
      .step.bad {border-left-color: #dc2626; background: #fef2f2;}
      .footer {color: #6b7280; font-size: .85rem; margin-top: 36px; text-align: center; border-top: 1px solid #e5e7eb; padding-top: 14px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Title and one-line explainer
st.markdown(
    '<div class="hero"><h1>🎯 Meeting Notes to Action Agent</h1>'
    "<p>Turn rough meeting notes into a clear list of decisions and action items with owners.</p></div>",
    unsafe_allow_html=True,
)

if API_KEY:
    st.success(f"Using a real AI model ({MODEL}).")
else:
    st.info("Demo mode: no AI key added yet, so the agent uses simple rules. Add your key in .streamlit/secrets.toml to use a real model.")

SAMPLES = {
    "Sample 1: Sprint Planning (sample1.txt)": "samples/sample1.txt",
    "Sample 2: Product Launch Sync (sample2.txt)": "samples/sample2.txt",
    "Sample 3: Messy Notes with Typos (sample3.txt)": "samples/sample3.txt",
    "Sample 4: Very Short Standup (sample4.txt)": "samples/sample4.txt",
    "Sample 5: Missing Owners & Deadlines (sample5.txt)": "samples/sample5.txt",
    "Default: Team Meeting Sync (sample_updates.txt)": "sample_updates.txt",
}


def read(p: str) -> str:
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


if "updates" not in st.session_state:
    st.session_state.updates = ""

left, right = st.columns([1, 1.35], gap="large")

with left:
    pick = st.selectbox("Choose a sample", list(SAMPLES))
    c1, c2 = st.columns(2)
    if c1.button("Load sample", use_container_width=True):
        st.session_state.updates = read(SAMPLES[pick])
    up = c2.file_uploader("or upload a file", type=["txt", "md", "csv"], label_visibility="collapsed")
    if up is not None and st.session_state.get("_uploaded") != up.name:
        st.session_state.updates = up.read().decode("utf-8", errors="ignore")
        st.session_state._uploaded = up.name

    updates = st.text_area(
        "Your rough meeting notes or transcript",
        key="updates",
        height=330,
        placeholder="Paste rough meeting notes, discussion points, Zoom chat or stand-up notes, one per line...",
    )
    go = st.button("Extract decisions and actions", type="primary", use_container_width=True)

with right:
    if go:
        if not updates.strip():
            st.warning("Paste some meeting notes first, or press 'Load sample'.")
        else:
            with st.spinner("The agent is reading notes, extracting decisions, and checking action items..."):
                try:
                    result, steps = run(updates, SYSTEM_PROMPT, API_KEY, BASE_URL, MODEL)
                except Exception as err:
                    st.error(f"The AI model could not answer. Check your key and model name, then try again. Details: {err}")
                    st.stop()
            st.session_state.result, st.session_state.steps = result, steps

    result = st.session_state.get("result")
    steps = st.session_state.get("steps", [])

    if not result:
        st.markdown(
            '<div class="card"><h4>How it works</h4>'
            '<div class="item">1. Paste rough meeting notes or press <b>Load sample</b>.</div>'
            '<div class="item">2. Press <b>Extract decisions and actions</b>.</div>'
            '<div class="item">3. The agent sorts every note, checks its own work, and lists decisions and action items with owners.</div></div>',
            unsafe_allow_html=True,
        )
    else:
        items = result.get("items", [])
        count = lambda s: len([i for i in items if i.get("section") == s])
        colour = STATUS_COLOUR.get(result.get("status", ""), "#6b7280")

        # Section 1: Overview & Status
        st.markdown(
            f'<span class="status" style="background:{colour}">Status: {result.get("status", "Not enough information")}</span>'
            f'&nbsp;&nbsp;<span style="color:#475569">{result.get("status_reason", "")}</span>',
            unsafe_allow_html=True,
        )
        st.write("")
        if result.get("headline"):
            st.markdown(
                f'<div class="card" style="border-left:5px solid {colour}"><h4>Key Highlight</h4>'
                f'<div style="font-size:1.05rem">{result["headline"]}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown(f"**Summary:** {result.get('summary', 'Not enough information.')}")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Decisions", count("Decisions"))
        k2.metric("Action items", count("Action items"))
        k3.metric("Blockers", count("Blockers"))
        k4.metric("Questions", len(result.get("questions", [])))

        # Separated Sections in Tabs
        tab_actions, tab_report, tab_email, tab_questions, tab_steps = st.tabs(
            ["Decisions & Action Items", "Full Meeting Report", "Follow-Up Email", "Questions for the Team", "Agent Steps"]
        )

        with tab_actions:
            st.markdown("#### 🎯 Agreed Decisions")
            if result.get("decisions"):
                for dcs in result.get("decisions", []):
                    st.markdown(f"- **{dcs}**")
            else:
                st.write("No formal decisions recorded.")

            st.markdown("#### ✅ Top Action Items")
            actions = result.get("actions", [])
            if actions:
                for n, a in enumerate(actions, 1):
                    owner = a.get("owner") or "Unassigned"
                    why = a.get("why", "")
                    st.markdown(
                        f'<div class="step"><b>{n}. {a.get("action", "")}</b><br>'
                        f'<span style="color:#475569">👤 Owner: <b>{owner}</b>'
                        + (f'  ·  🎯 {why}' if why else '') + '</span></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.write("No action items recorded.")

            reg = [i for i in items if i.get("section") in ("Action items", "Blockers")]
            if reg:
                st.markdown("#### 📋 Action Items & Blockers Register")
                st.dataframe(
                    pd.DataFrame([
                        {
                            "Section": i["section"],
                            "Impact": i.get("impact") or "Medium",
                            "Owner": i.get("owner") or "Unassigned",
                            "Due": i.get("due") or "Not specified",
                            "Note": i.get("text", ""),
                        }
                        for i in reg
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )

        with tab_report:
            for s in SECTIONS:
                rows = [i for i in items if i.get("section") == s]
                body = "".join(
                    f'<div class="item">{i.get("text", "")}'
                    + (f'<span class="tag">👤 {i["owner"]}</span>' if i.get("owner") else "")
                    + (f'<span class="tag">📅 {i["due"]}</span>' if i.get("due") else "")
                    + "</div>"
                    for i in rows
                ) or '<div class="item">Nothing to report.</div>'
                st.markdown(f'<div class="card"><h4>{SECTION_ICON[s]} {s}</h4>{body}</div>', unsafe_allow_html=True)

        with tab_email:
            st.text_area("Ready to copy and send to attendees", result.get("email", "") or "Not enough information.", height=240)

        with tab_questions:
            questions = result.get("questions", [])
            if questions:
                for q in questions:
                    st.markdown(f"- ❓ {q}")
            else:
                st.success("No information is missing. All action items have owners and due dates.")

        with tab_steps:
            for n, s in enumerate(steps, 1):
                css_class = "" if s.get("ok", True) else "bad"
                status_icon = "✓" if s.get("ok", True) else "⚠️"
                st.markdown(
                    f'<div class="step {css_class}"><b>{n}. {s["name"]}</b> {status_icon}<br>'
                    f'<span style="color:#475569">{s["detail"]}</span></div>',
                    unsafe_allow_html=True,
                )

        st.info("⚠️ Always check this output before using it: verify that every action item was an agreed commitment, not a casual or off-topic mention.")
        st.download_button("Download the meeting report", to_markdown(result), file_name="meeting-report.md", use_container_width=True)
        st.caption("Check the report before you send it. The agent only uses what is in the meeting notes.")

st.markdown('<div class="footer">Built by Aneeshkumar P R at Zero to Live, Future Proof India</div>', unsafe_allow_html=True)
