# Meeting to Action Items Agent

A powerful, self-verifying AI Agent built with **Streamlit** that transforms unstructured meeting notes, Zoom/Teams transcripts, and discussion scratchpads into clear meeting minutes, decisions, and tracked action items.

Works out of the box in **Demo Mode** (using rule-based heuristics, no API key needed). Add your AI provider API key to switch to an intelligent LLM (OpenAI, Google Gemini, DeepSeek).

---

## What the Agent Does

1. **Extracts Action Items & Ownership:**
   - **Task description:** Actionable, verb-first task.
   - **Assignee / Owner:** Person responsible.
   - **Deadline / Due Date:** Target date or timeframe.
   - **Priority:** `High`, `Medium`, or `Low`.
   - **Category:** `Engineering`, `Product`, `Design`, `QA`, `Operations`, or `Follow-up`.
   - **Deliverable:** Clear definition of done.
2. **Captures Key Decisions:** Logs agreements made by the team so alignment is preserved.
3. **Drafts Follow-Up Email:** Ready-to-copy email/Slack message for meeting participants.
4. **Self-Verification & Anti-Hallucination:**
   - Checks that all extracted details are strictly grounded in the meeting notes.
   - Highlights unassigned tasks or missing deadlines and formulates clarification questions.
   - Re-prompts the model to self-correct any detected issues before presenting.
5. **Multi-Format Export:** Download meeting minutes in **Markdown** (`.md`) or action items in **CSV** (`.csv`) for Jira, Linear, or Excel.

---

## Quickstart

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Run the App
```bash
python -m streamlit run app.py
```
Open **`http://localhost:8501`** in your web browser.

---

## Using a Real AI Model (Optional)

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
2. Configure your provider API key:

   **OpenAI:**
   ```toml
   AI_API_KEY = "sk-..."
   AI_BASE_URL = "https://api.openai.com/v1"
   AI_MODEL = "gpt-4o-mini"
   ```

   **Google Gemini (Free tier available):**
   ```toml
   AI_API_KEY = "your-gemini-api-key"
   AI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
   AI_MODEL = "gemini-2.5-flash"
   ```

   **DeepSeek:**
   ```toml
   AI_API_KEY = "your-deepseek-api-key"
   AI_BASE_URL = "https://api.deepseek.com"
   AI_MODEL = "deepseek-chat"
   ```

3. Restart the Streamlit app. The badge at the top will indicate that a real AI model is active.

---

## Project Structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit web interface with interactive tables, badges, metrics, and download controls. |
| `agent.py` | Agent logic: planning, extraction, 3-step self-reflection checks, self-correction, markdown & CSV exports. |
| `prompts.py` | Agent system prompt and operational boundaries (Who You Are, What You Always Do, What You Never Do). |
| `demo.py` | Offline heuristic engine for demo mode (pattern matching for tasks, owners, dates, and priorities). |
| `sample_updates.txt` | Default sample meeting notes (Sprint Planning & Architecture Sync). |
| `samples/` | Realistic meeting transcripts across Product, SRE Incident Retrospective, Cloud, and Banking. |
| `requirements.txt` | Minimal dependencies: `streamlit`, `openai`, `pandas`. |

---

## Deploying to Streamlit Community Cloud

1. Push this repository to GitHub (ensure `.streamlit/secrets.toml` is **not** committed).
2. Go to [share.streamlit.io](https://share.streamlit.io) and create a new app.
3. Select your repository and set the main file path to `app.py`.
4. In **Advanced Settings -> Secrets**, paste the contents of your `.streamlit/secrets.toml`.
5. Click **Deploy**.
