"""
streamlit_app.py — Elimu Research Assistant web interface.

Run with:
    streamlit run streamlit_app.py
"""

import sys
import os
import threading
import queue

# Make project root importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from pathlib import Path

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Elimu Research Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme / CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Palette ──────────────────────────────────────────────────────────── */
:root {
    --green-dark:   #1B5E20;
    --green-mid:    #2E7D32;
    --green-light:  #43A047;
    --gold:         #F9A825;
    --gold-light:   #FDD835;
    --sky:          #0277BD;
    --red:          #C62828;
    --bg-dark:      #0D1117;
    --bg-card:      #161B22;
    --bg-card2:     #1C2430;
    --text-main:    #E6EDF3;
    --text-muted:   #8B949E;
    --border:       #30363D;
}

/* ── Global reset ──────────────────────────────────────────────────────── */
.stApp {
    background-color: var(--bg-dark);
    color: var(--text-main);
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* ── Header bar ─────────────────────────────────────────────────────────── */
.elimu-header {
    background: linear-gradient(135deg, var(--green-dark) 0%, var(--green-mid) 60%, #1A3A5C 100%);
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 24px;
    border-bottom: 3px solid var(--gold);
}
.elimu-header h1 {
    color: var(--text-main);
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 4px 0;
    letter-spacing: -0.5px;
}
.elimu-header .subtitle {
    color: var(--gold);
    font-size: 0.9rem;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.elimu-header .tagline {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-top: 6px;
}

/* ── Cards ──────────────────────────────────────────────────────────────── */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.card-accent {
    border-left: 4px solid var(--gold);
}
.card-success {
    border-left: 4px solid var(--green-light);
}
.card-info {
    border-left: 4px solid var(--sky);
}
.card-error {
    border-left: 4px solid var(--red);
}

/* ── Step trace ─────────────────────────────────────────────────────────── */
.trace-step {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 0.85rem;
}
.trace-step .step-num {
    color: var(--gold);
    font-weight: 700;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.trace-step .thought {
    color: var(--text-main);
    margin: 4px 0;
}
.trace-step .action-tag {
    display: inline-block;
    background: var(--green-dark);
    color: var(--gold);
    border-radius: 4px;
    padding: 1px 8px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 6px;
}
.trace-step .observation {
    color: var(--text-muted);
    font-size: 0.8rem;
    margin-top: 6px;
    border-top: 1px solid var(--border);
    padding-top: 6px;
    white-space: pre-wrap;
    max-height: 120px;
    overflow-y: auto;
}

/* ── Stat boxes ─────────────────────────────────────────────────────────── */
.stat-grid {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
}
.stat-box {
    flex: 1;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    text-align: center;
}
.stat-box .stat-val {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--gold);
}
.stat-box .stat-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ── Inputs / buttons ───────────────────────────────────────────────────── */
.stTextArea textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-main) !important;
    border-radius: 8px !important;
    font-size: 0.95rem !important;
}
.stTextArea textarea:focus {
    border-color: var(--green-light) !important;
    box-shadow: 0 0 0 2px rgba(46,125,50,0.25) !important;
}
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, var(--green-mid), var(--green-light)) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 28px !important;
    font-size: 0.95rem !important;
    transition: opacity 0.2s !important;
}
div[data-testid="stButton"] button:hover {
    opacity: 0.88 !important;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .sidebar-title {
    color: var(--gold);
    font-weight: 700;
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 8px 0 4px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
}
.stTextInput input, .stSelectbox select, .stNumberInput input {
    background: var(--bg-dark) !important;
    border-color: var(--border) !important;
    color: var(--text-main) !important;
    border-radius: 6px !important;
}

/* ── Result markdown ─────────────────────────────────────────────────────── */
.result-body {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 24px 28px;
    line-height: 1.7;
    font-size: 0.95rem;
}
.result-body h1, .result-body h2, .result-body h3 {
    color: var(--gold);
}
.result-body a {
    color: var(--sky);
}
.result-body code {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 0.85rem;
}

/* ── Divider ─────────────────────────────────────────────────────────────── */
hr {
    border-color: var(--border) !important;
    margin: 20px 0 !important;
}

/* ── Hide Streamlit branding ─────────────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
.viewerBadge_container__1QSob { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_config():
    from config.config import get_config, init_config
    init_config()
    return get_config()

def _run_agent_in_thread(query: str, result_queue: queue.Queue) -> None:
    """Run the ReAct agent in a background thread, push result to queue."""
    try:
        from elimu_react import build_elimu_agent
        agent = build_elimu_agent()
        answer = agent.run(query)
        trace = agent.get_execution_trace()
        result_queue.put({"answer": answer, "trace": trace, "error": None})
    except Exception as exc:
        result_queue.put({"answer": None, "trace": [], "error": str(exc)})

def _render_trace(trace: list) -> None:
    if not trace:
        return
    st.markdown("#### ReAct Trace")
    for step in trace:
        n = step.get("step", "?")
        thought = step.get("thought", "")
        action = step.get("action", "")
        obs = step.get("observation", "")
        action_input = step.get("action_input", "")

        obs_preview = str(obs)[:400] + ("…" if len(str(obs)) > 400 else "") if obs else ""
        action_str = ""
        if action:
            action_str = f'<span class="action-tag">{action}</span>'
            if action_input:
                action_str += f'<code style="font-size:0.78rem">{str(action_input)[:120]}</code>'

        obs_block = f'<div class="observation">{obs_preview}</div>' if obs_preview else ""

        st.markdown(
            f"""<div class="trace-step">
  <div class="step-num">Step {n}</div>
  <div class="thought">{thought}</div>
  {action_str}
  {obs_block}
</div>""",
            unsafe_allow_html=True,
        )

# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar(cfg) -> dict:
    """Render configuration sidebar; return dict of overrides."""
    with st.sidebar:
        st.markdown('<div class="sidebar-title">Configuration</div>', unsafe_allow_html=True)

        gemini_key = st.text_input(
            "Gemini API Key",
            value=cfg.get("gemini_api_key", "") or "",
            type="password",
            help="Required. Get one at aistudio.google.com",
        )
        serper_key = st.text_input(
            "Serper API Key",
            value=cfg.get("serper_api_key", "") or "",
            type="password",
            help="Required. Get one at serper.dev (2 500 free searches/month)",
        )

        st.divider()
        st.markdown('<div class="sidebar-title" style="border-top:none;padding-top:0">Model</div>', unsafe_allow_html=True)

        model_options = [
            "gemini-2.0-flash",
            "gemini-2.0-flash-001",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
        ]
        current_model = cfg.get("model_name", "gemini-2.0-flash")
        model_idx = model_options.index(current_model) if current_model in model_options else 0
        model = st.selectbox("Primary model", model_options, index=model_idx)

        max_iter = st.number_input(
            "Max iterations",
            min_value=3,
            max_value=20,
            value=int(cfg.get("max_iterations", 12)),
            help="ReAct loop cap. Higher = more thorough, slower.",
        )
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=float(cfg.get("model_temperature", 0.15)),
            step=0.05,
            help="0.0 = deterministic, 1.0 = creative",
        )

        st.divider()
        st.markdown('<div class="sidebar-title" style="border-top:none;padding-top:0">Search</div>', unsafe_allow_html=True)

        kenya_bias = st.toggle(
            "Prioritise Kenyan sources",
            value=bool(cfg.get("prioritize_kenyan_sources", True)),
        )
        edu_focus = st.toggle(
            "Educational focus",
            value=bool(cfg.get("educational_focus", True)),
        )

        if st.button("Save settings", use_container_width=True):
            if gemini_key:
                cfg.update("gemini_api_key", gemini_key)
            if serper_key:
                cfg.update("serper_api_key", serper_key)
            cfg.update("model_name", model)
            cfg.update("max_iterations", max_iter)
            cfg.update("model_temperature", temperature)
            cfg.update("prioritize_kenyan_sources", kenya_bias)
            cfg.update("educational_focus", edu_focus)
            st.success("Settings saved.")

        st.divider()
        ver_file = Path(__file__).parent / "VERSION"
        ver = ver_file.read_text().strip() if ver_file.exists() else "—"
        st.caption(f"v{ver} · Ashioya Jotham")

    return {
        "gemini_api_key": gemini_key,
        "serper_api_key": serper_key,
        "model": model,
        "max_iter": max_iter,
        "temperature": temperature,
        "kenya_bias": kenya_bias,
        "edu_focus": edu_focus,
    }

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    cfg = _load_config()
    overrides = render_sidebar(cfg)

    # Header
    st.markdown("""
<div class="elimu-header">
  <h1>📚 Elimu Research Assistant</h1>
  <div class="subtitle">ReAct · Gemini 2.x · Serper.dev</div>
  <div class="tagline">Kenyan-context educational content generation via live web research</div>
</div>
""", unsafe_allow_html=True)

    # Key check
    g_key = overrides["gemini_api_key"] or cfg.get("gemini_api_key")
    s_key = overrides["serper_api_key"] or cfg.get("serper_api_key")
    if not g_key or not s_key:
        st.markdown("""
<div class="card card-accent">
  <strong style="color:#F9A825">API keys required</strong><br>
  Enter your Gemini and Serper API keys in the sidebar to get started.<br>
  <span style="color:#8B949E;font-size:0.85rem">
    Gemini: aistudio.google.com &nbsp;·&nbsp; Serper: serper.dev
  </span>
</div>
""", unsafe_allow_html=True)

    # Research input
    col_input, col_examples = st.columns([3, 1])

    with col_input:
        query = st.text_area(
            "Research query",
            placeholder='e.g. "Create a Form 3 Business Studies lesson on M-Pesa\'s impact on small enterprises in the Rift Valley"',
            height=110,
            label_visibility="collapsed",
        )
        run_col, clear_col = st.columns([2, 1])
        with run_col:
            run_btn = st.button("Run Research", type="primary", use_container_width=True)
        with clear_col:
            if st.button("Clear", use_container_width=True):
                for k in ("result", "trace", "last_query"):
                    st.session_state.pop(k, None)
                st.rerun()

    with col_examples:
        st.markdown(
            '<div style="color:#8B949E;font-size:0.78rem;font-weight:600;text-transform:uppercase;'
            'letter-spacing:1px;margin-bottom:8px">Examples</div>',
            unsafe_allow_html=True,
        )
        examples = [
            "Geothermal energy at Olkaria — Form 2 Geography",
            "M-Pesa impact on rural banking — Form 3 Business",
            "Pre-colonial trade routes in East Africa — History",
            "Ngugi wa Thiong'o themes — Literature guide",
            "Quadratic equations with Kenyan sports data — Maths",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex[:20]}", use_container_width=True):
                st.session_state["prefill"] = ex
                st.rerun()

    # Prefill handling
    if "prefill" in st.session_state:
        query = st.session_state.pop("prefill")

    # Run agent
    if run_btn and query.strip():
        if not g_key or not s_key:
            st.error("Configure API keys in the sidebar first.")
        else:
            # Apply overrides to live config
            cfg.update("gemini_api_key", g_key)
            cfg.update("serper_api_key", s_key)
            cfg.update("model_name", overrides["model"])
            cfg.update("max_iterations", overrides["max_iter"])
            cfg.update("model_temperature", overrides["temperature"])
            cfg.update("prioritize_kenyan_sources", overrides["kenya_bias"])
            cfg.update("educational_focus", overrides["edu_focus"])

            st.session_state["last_query"] = query.strip()

            with st.spinner("Running ReAct agent…"):
                q: queue.Queue = queue.Queue()
                t = threading.Thread(target=_run_agent_in_thread, args=(query.strip(), q), daemon=True)
                t.start()
                t.join(timeout=300)  # 5-minute hard cap

                if not q.empty():
                    res = q.get_nowait()
                    if res["error"]:
                        st.session_state["result"] = None
                        st.session_state["error"] = res["error"]
                    else:
                        st.session_state["result"] = res["answer"]
                        st.session_state["trace"] = res["trace"]
                        st.session_state.pop("error", None)
                else:
                    st.session_state["error"] = "Agent timed out after 5 minutes."

    # ── Results ───────────────────────────────────────────────────────────────
    if "error" in st.session_state:
        st.markdown(f"""
<div class="card card-error">
  <strong style="color:#C62828">Error</strong><br>
  {st.session_state['error']}
</div>
""", unsafe_allow_html=True)

    if "result" in st.session_state and st.session_state["result"]:
        answer = st.session_state["result"]
        trace = st.session_state.get("trace", [])
        last_q = st.session_state.get("last_query", "")

        # Stats bar
        word_count = len(answer.split())
        steps = len(trace)
        st.markdown(f"""
<div class="stat-grid">
  <div class="stat-box"><div class="stat-val">{steps}</div><div class="stat-label">ReAct steps</div></div>
  <div class="stat-box"><div class="stat-val">{word_count:,}</div><div class="stat-label">words</div></div>
  <div class="stat-box"><div class="stat-val">{len(answer):,}</div><div class="stat-label">characters</div></div>
</div>
""", unsafe_allow_html=True)

        # Tabs: result / trace / raw
        tab_result, tab_trace, tab_raw = st.tabs(["Result", "ReAct Trace", "Raw Markdown"])

        with tab_result:
            st.markdown(answer)

        with tab_trace:
            _render_trace(trace)

        with tab_raw:
            from utils.react_output import format_react_markdown
            raw_md = format_react_markdown(last_q, answer, trace)
            st.code(raw_md, language="markdown")
            st.download_button(
                "Download .md",
                data=raw_md,
                file_name=f"elimu_{last_q[:30].replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
