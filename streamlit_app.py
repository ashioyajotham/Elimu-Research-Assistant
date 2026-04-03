"""
streamlit_app.py — Elimu Research Assistant web interface.

Run with:
    python -m streamlit run streamlit_app.py
"""

import sys
import os
import threading
import queue
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from pathlib import Path

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Elimu Research Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --green-dark:  #1B5E20;
    --green-mid:   #2E7D32;
    --green-light: #43A047;
    --gold:        #F9A825;
    --sky:         #0277BD;
    --red:         #C62828;
    --bg:          #0D1117;
    --card:        #161B22;
    --card2:       #1C2430;
    --text:        #E6EDF3;
    --muted:       #8B949E;
    --border:      #30363D;
}

/* ── Global ── */
.stApp { background: var(--bg); color: var(--text); font-family: 'Inter','Segoe UI',system-ui,sans-serif; }

/* ── Header ── */
.elimu-header {
    background: linear-gradient(135deg, var(--green-dark) 0%, var(--green-mid) 55%, #1A3A5C 100%);
    border-radius: 10px; padding: 22px 28px; margin-bottom: 20px;
    border-bottom: 3px solid var(--gold); position: relative; overflow: hidden;
}
.elimu-header::after {
    content: ''; position: absolute; top: -50px; right: -50px;
    width: 200px; height: 200px; background: rgba(249,168,37,0.05); border-radius: 50%;
}
.elimu-header .wordmark { font-size: 1.65rem; font-weight: 700; color: var(--text); margin: 0 0 2px; letter-spacing: -.4px; }
.elimu-header .wordmark span { color: var(--gold); }
.elimu-header .subtitle  { color: var(--gold); font-size: .75rem; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; }
.elimu-header .tagline   { color: var(--muted); font-size: .82rem; margin-top: 4px; }

/* ── Cards ── */
.card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; }
.card-accent  { border-left: 3px solid var(--gold); }
.card-error   { border-left: 3px solid var(--red); }

/* ── Input ── */
.stTextArea textarea {
    background: var(--card)  !important; border: 1px solid var(--border) !important;
    color: var(--text) !important; border-radius: 7px !important; font-size: .93rem !important;
}
.stTextArea textarea:focus { border-color: var(--green-light) !important; box-shadow: 0 0 0 2px rgba(46,125,50,.2) !important; }

/* ── Buttons ── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, var(--green-mid), var(--green-light)) !important;
    color: #fff !important; border: none !important; border-radius: 7px !important;
    font-weight: 600 !important; font-size: .93rem !important; letter-spacing: .2px !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover { opacity: .88 !important; }
div[data-testid="stButton"] > button[kind="primary"]:disabled { opacity: .45 !important; }

div[data-testid="stButton"] > button[kind="secondary"] {
    background: var(--card2) !important; color: var(--muted) !important;
    border: 1px solid var(--border) !important; border-radius: 6px !important;
    font-size: .8rem !important; font-weight: 400 !important;
    transition: border-color .15s, color .15s !important;
}
div[data-testid="stButton"] > button[kind="secondary"]:hover {
    border-color: var(--green-light) !important; color: var(--green-light) !important;
}
div[data-testid="stButton"] > button[kind="secondary"]:disabled { opacity: .35 !important; }

/* ── Examples label ── */
.ex-label {
    color: var(--muted); font-size: .72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;
}

/* ── Progress panel ── */
.progress-panel {
    background: var(--card); border: 1px solid var(--green-mid);
    border-radius: 8px; padding: 14px 18px; margin: 10px 0;
}
.progress-title {
    color: var(--green-light); font-size: .73rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
}
.p-step {
    display: flex; align-items: flex-start; gap: 10px; padding: 5px 0;
    border-bottom: 1px solid var(--border); font-size: .82rem;
}
.p-step:last-child { border-bottom: none; }
.p-step-n    { color: var(--gold); font-weight: 700; min-width: 18px; }
.p-step-t    { color: var(--text); flex: 1; }
.p-step-a    {
    display: inline-block; background: var(--green-dark); color: var(--gold);
    border-radius: 3px; padding: 0 6px; font-size: .7rem; font-weight: 600; margin-left: 6px;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
.p-step.active .p-step-t { animation: pulse 1.5s ease-in-out infinite; }

/* ── Stat bar ── */
.stat-grid { display: flex; gap: 10px; margin-bottom: 16px; }
.stat-box  {
    flex: 1; background: var(--card); border: 1px solid var(--border);
    border-radius: 6px; padding: 12px; text-align: center;
}
.stat-val   { font-size: 1.5rem; font-weight: 700; color: var(--gold); }
.stat-label { font-size: .7rem; color: var(--muted); text-transform: uppercase; letter-spacing: .8px; }

/* ── Trace step ── */
.trace-step {
    background: var(--card2); border: 1px solid var(--border);
    border-radius: 6px; padding: 9px 13px; margin-bottom: 6px; font-size: .83rem;
}
.trace-step .step-num  { color: var(--gold); font-weight: 700; font-size: .7rem; text-transform: uppercase; letter-spacing: 1px; }
.trace-step .thought   { color: var(--text); margin: 3px 0; }
.trace-step .action-tag {
    display: inline-block; background: var(--green-dark); color: var(--gold);
    border-radius: 3px; padding: 0 6px; font-size: .7rem; font-weight: 600; margin-right: 5px;
}
.trace-step .observation {
    color: var(--muted); font-size: .77rem; margin-top: 5px;
    border-top: 1px solid var(--border); padding-top: 5px;
    white-space: pre-wrap; max-height: 100px; overflow-y: auto;
}

/* ── Result body ── */
.result-body { line-height: 1.75; }
.result-body h1,.result-body h2,.result-body h3 { color: var(--gold); }
.result-body a { color: var(--sky); }
.result-body code {
    background: var(--card2); border: 1px solid var(--border);
    border-radius: 3px; padding: 1px 5px; font-size: .85rem;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: var(--card) !important; border-right: 1px solid var(--border) !important; }
.sb-label {
    color: var(--gold); font-weight: 700; font-size: .73rem;
    text-transform: uppercase; letter-spacing: 1.2px;
    padding: 4px 0 6px; border-bottom: 1px solid var(--border); margin-bottom: 10px;
}
.stTextInput input, .stNumberInput input {
    background: var(--bg) !important; border-color: var(--border) !important;
    color: var(--text) !important; border-radius: 5px !important;
}
.model-badge {
    display: inline-block; background: var(--green-dark); color: var(--gold);
    border-radius: 4px; padding: 2px 10px; font-size: .77rem; font-weight: 600; letter-spacing: .4px;
}
.about-box {
    background: var(--card2); border: 1px solid var(--border); border-radius: 6px;
    padding: 11px 13px; font-size: .8rem; color: var(--muted); line-height: 1.65;
}
.about-box strong { color: var(--text); }
.about-box a { color: var(--sky); text-decoration: none; }
.about-box code {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 3px; padding: 1px 5px; font-size: .78rem;
}

/* ── Misc ── */
hr { border-color: var(--border) !important; margin: 14px 0 !important; }

/* Dark-theme the Streamlit header (contains sidebar toggle — must stay visible) */
[data-testid="stHeader"] {
    background-color: var(--bg) !important;
    border-bottom: 1px solid var(--border) !important;
}
/* Hide only decorative children inside the toolbar — NOT the whole toolbar.
   In Streamlit >=1.32 the sidebar toggle lives inside stToolbar; hiding the
   whole element makes the sidebar permanently inaccessible. */
[data-testid="stToolbar"] .stAppDeployButton,
[data-testid="stToolbar"] [data-testid="stDecoration"],
[data-testid="stToolbar"] .viewerBadge_container__1QSob {
    display: none !important;
}
/* Force the sidebar toggle to always be reachable regardless of parent rules */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stSidebarNavToggleButton"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}
footer { display: none; }
[data-testid="stDecoration"] { display: none; }
#MainMenu { visibility: hidden; }
.viewerBadge_container__1QSob { display: none; }
[data-testid="stStatusWidget"] { display: none !important; }
div.stApp > div:first-child { background: var(--bg) !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
_MODEL = "gemini-2.0-flash"

_EXAMPLES = [
    "Create a Form 2 Geography lesson on geothermal energy at Olkaria",
    "Analyse M-Pesa's impact on rural banking — Form 3 Business Studies",
    "Pre-colonial trade routes in East Africa — Form 1 History",
    "Ngugi wa Thiong'o themes in Weep Not Child — Form 4 Literature",
    "Quadratic equations using Kenya athletics data — Form 3 Maths",
    "Climate change effects on the Mau Forest — Form 3 Geography",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_config():
    # Inject Streamlit Cloud secrets as env vars BEFORE init_config so the
    # config system finds them on first check and doesn't emit warnings.
    try:
        import os
        for secret_key, env_key in (
            ("GEMINI_API_KEY", "GEMINI_API_KEY"),
            ("SERPER_API_KEY", "SERPER_API_KEY"),
        ):
            val = st.secrets.get(secret_key)
            if val:
                os.environ.setdefault(env_key, val)
    except Exception:
        pass

    from config.config import get_config, init_config
    init_config()
    return get_config()


def _run_agent_in_thread(
    query: str,
    result_queue: queue.Queue,
    step_queue: queue.Queue,
) -> None:
    """Run the ReAct agent; push step updates and final result to queues."""
    done = threading.Event()
    try:
        from elimu_react import build_elimu_agent
        agent = build_elimu_agent()

        def _monitor():
            seen = 0
            while not done.is_set():
                current = agent.steps
                if len(current) > seen:
                    for s in current[seen:]:
                        step_queue.put({
                            "thought": s.thought or "",
                            "action":  s.action  or "",
                        })
                    seen = len(current)
                time.sleep(0.35)

        threading.Thread(target=_monitor, daemon=True).start()

        answer = agent.run(query)
        trace  = agent.get_execution_trace()
        done.set()
        result_queue.put({"answer": answer, "trace": trace, "error": None})
    except Exception as exc:
        done.set()
        result_queue.put({"answer": None, "trace": [], "error": str(exc)})


def _render_trace(trace: list) -> None:
    if not trace:
        st.caption("No trace available.")
        return
    for step in trace:
        n      = step.get("step", "?")
        thought = step.get("thought", "")
        action  = step.get("action", "")
        obs     = step.get("observation", "")
        a_input = step.get("action_input", "")

        obs_html = ""
        if obs:
            obs_preview = str(obs)[:400] + ("…" if len(str(obs)) > 400 else "")
            obs_html = f'<div class="observation">{obs_preview}</div>'

        action_html = ""
        if action:
            action_html = f'<span class="action-tag">{action}</span>'
            if a_input:
                action_html += f'<code style="font-size:.72rem">{str(a_input)[:100]}</code>'

        st.markdown(
            f'<div class="trace-step">'
            f'<div class="step-num">Step {n}</div>'
            f'<div class="thought">{thought}</div>'
            f'{action_html}{obs_html}'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_live_steps(steps: list) -> None:
    if not steps:
        st.markdown(
            '<div class="progress-panel"><div class="progress-title">Initialising agent…</div></div>',
            unsafe_allow_html=True,
        )
        return

    items = ""
    for i, s in enumerate(steps):
        thought = str(s.get("thought", ""))[:130]
        action  = s.get("action", "")
        a_html  = f'<span class="p-step-a">{action}</span>' if action else ""
        active  = " active" if i == len(steps) - 1 else ""
        items  += (
            f'<div class="p-step{active}">'
            f'<span class="p-step-n">{i+1}</span>'
            f'<span class="p-step-t">{thought}{a_html}</span>'
            f'</div>'
        )

    last = steps[-1]
    summary = str(last.get("thought", ""))
    title   = f"Step {len(steps)} — {summary[:70]}{'…' if len(summary) > 70 else ''}"

    st.markdown(
        f'<div class="progress-panel">'
        f'<div class="progress-title">{title}</div>'
        f'{items}</div>',
        unsafe_allow_html=True,
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar(cfg) -> dict:
    with st.sidebar:
        # ── API Keys ──────────────────────────────────────────────────────────
        st.markdown('<div class="sb-label">API Keys</div>', unsafe_allow_html=True)
        gemini_key = st.text_input(
            "Gemini API Key",
            value=cfg.get("gemini_api_key", "") or "",
            type="password",
            help="aistudio.google.com/apikey — free tier available",
        )
        serper_key = st.text_input(
            "Serper API Key",
            value=cfg.get("serper_api_key", "") or "",
            type="password",
            help="serper.dev — 2,500 free searches/month",
        )

        st.divider()

        # ── Model (read-only) ─────────────────────────────────────────────────
        st.markdown('<div class="sb-label">Model</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="model-badge">{_MODEL}</div>', unsafe_allow_html=True)
        st.caption("ReAct loop · max 15 iterations")

        st.divider()

        # ── Search settings ───────────────────────────────────────────────────
        st.markdown('<div class="sb-label">Search</div>', unsafe_allow_html=True)
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
            cfg.update("prioritize_kenyan_sources", kenya_bias)
            cfg.update("educational_focus", edu_focus)
            st.success("Settings saved.")

        st.divider()

        # ── About ─────────────────────────────────────────────────────────────
        st.markdown('<div class="sb-label">About</div>', unsafe_allow_html=True)

        ver_file = Path(__file__).parent / "VERSION"
        ver = ver_file.read_text().strip() if ver_file.exists() else "—"

        st.markdown(f"""
<div class="about-box">
<strong>Elimu Research Assistant v{ver}</strong><br>
Generates Kenya-curriculum-aligned educational content through a live-web
ReAct loop tuned for secondary school educators.<br><br>

<strong>Architecture</strong><br>
Gemini 2.0 Flash &rarr; ReAct (Thought / Action / Observe) &rarr;
Serper.dev search &rarr; BeautifulSoup extraction &rarr; structured lesson output<br><br>

<strong>Install the CLI</strong><br>
<code>pip install elimu-research-assistant</code><br><br>

<a href="https://pypi.org/project/elimu-research-assistant/" target="_blank">PyPI</a>
&nbsp;&middot;&nbsp;
<a href="https://github.com/ashioyajotham/elimu_research_assistant" target="_blank">GitHub</a>
</div>
""", unsafe_allow_html=True)

    return {
        "gemini_api_key": gemini_key,
        "serper_api_key": serper_key,
        "kenya_bias":     kenya_bias,
        "edu_focus":      edu_focus,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    cfg = _load_config()

    # ── Sidebar first — renders on every execution path, including reruns ──────
    overrides = render_sidebar(cfg)
    g_key = overrides["gemini_api_key"] or cfg.get("gemini_api_key")
    s_key = overrides["serper_api_key"] or cfg.get("serper_api_key")

    # ── Poll for in-progress agent result ─────────────────────────────────────
    if st.session_state.get("running"):
        step_q:    queue.Queue      = st.session_state.get("step_q")
        result_q:  queue.Queue      = st.session_state.get("result_q")
        agent_thr: threading.Thread = st.session_state.get("agent_thread")

        # Drain new steps into session_state list
        while step_q and not step_q.empty():
            try:
                st.session_state["live_steps"].append(step_q.get_nowait())
            except queue.Empty:
                break

        # Check if finished
        result_ready = result_q is not None and not result_q.empty()
        thread_dead  = agent_thr is not None and not agent_thr.is_alive()

        if result_ready or thread_dead:
            if result_ready:
                res = result_q.get_nowait()
                if res["error"]:
                    st.session_state["agent_error"] = res["error"]
                    st.session_state.pop("result", None)
                else:
                    st.session_state["result"] = res["answer"]
                    st.session_state["trace"]  = res["trace"]
                    st.session_state.pop("agent_error", None)
            else:
                st.session_state["agent_error"] = "Agent stopped unexpectedly."
            st.session_state["running"] = False
            st.rerun()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
<div class="elimu-header">
  <div class="wordmark">Elimu <span>Research</span> Assistant</div>
  <div class="subtitle">ReAct &middot; Gemini 2.0 Flash &middot; Serper.dev</div>
  <div class="tagline">Kenyan-context educational content generation via live web research</div>
</div>
""", unsafe_allow_html=True)

    # ── API key warning ───────────────────────────────────────────────────────
    if not g_key or not s_key:
        missing = []
        if not g_key:
            missing.append('<a href="https://aistudio.google.com/apikey" target="_blank">Gemini API key</a>')
        if not s_key:
            missing.append('<a href="https://serper.dev" target="_blank">Serper API key</a>')
        st.markdown(
            f'<div class="card card-accent"><strong style="color:#F9A825">Setup required</strong>'
            f' &mdash; enter your {" and ".join(missing)} in the sidebar to continue.</div>',
            unsafe_allow_html=True,
        )

    # ── Query input ───────────────────────────────────────────────────────────
    # Apply any staged prefill BEFORE the widget is instantiated (Streamlit
    # forbids setting a widget key after its widget has been rendered).
    if "_prefill" in st.session_state:
        st.session_state["query_input"] = st.session_state.pop("_prefill")
    elif "query_input" not in st.session_state:
        st.session_state["query_input"] = ""

    running = st.session_state.get("running", False)

    query = st.text_area(
        "Research query",
        placeholder='e.g. "Create a Form 3 Business Studies lesson on M-Pesa\'s impact in the Rift Valley"',
        height=100,
        label_visibility="collapsed",
        key="query_input",
        disabled=running,
    )

    # ── Examples ─────────────────────────────────────────────────────────────
    st.markdown('<div class="ex-label">Examples — click to populate</div>', unsafe_allow_html=True)
    ex_cols = st.columns(3)
    for i, ex in enumerate(_EXAMPLES):
        with ex_cols[i % 3]:
            if st.button(ex, key=f"ex_{i}", use_container_width=True, disabled=running):
                st.session_state["_prefill"] = ex
                st.rerun()

    st.write("")

    # ── Action row ────────────────────────────────────────────────────────────
    keys_ok  = bool(g_key and s_key)
    query_ok = bool(query.strip())

    run_col, right_col = st.columns([3, 1])
    with run_col:
        run_btn = st.button(
            "Running…" if running else "Run Research",
            type="primary",
            use_container_width=True,
            disabled=running or not query_ok or not keys_ok,
        )
    with right_col:
        if running:
            cancel_btn = st.button("Cancel", use_container_width=True)
            if cancel_btn:
                st.session_state["running"] = False
                st.session_state.pop("live_steps", None)
                st.rerun()
        else:
            if st.button("Clear", use_container_width=True):
                for k in ("result", "trace", "last_query", "agent_error", "live_steps"):
                    st.session_state.pop(k, None)
                st.session_state["query_input"] = ""
                st.rerun()

    # ── Launch agent ──────────────────────────────────────────────────────────
    if run_btn and query_ok and keys_ok and not running:
        cfg.update("gemini_api_key", g_key)
        cfg.update("serper_api_key", s_key)
        cfg.update("prioritize_kenyan_sources", overrides["kenya_bias"])
        cfg.update("educational_focus", overrides["edu_focus"])

        st.session_state["last_query"]  = query.strip()
        st.session_state["running"]     = True
        st.session_state["live_steps"]  = []
        for k in ("result", "trace", "agent_error"):
            st.session_state.pop(k, None)

        result_q: queue.Queue = queue.Queue()
        step_q:   queue.Queue = queue.Queue()
        t = threading.Thread(
            target=_run_agent_in_thread,
            args=(query.strip(), result_q, step_q),
            daemon=True,
        )
        t.start()
        st.session_state["result_q"]    = result_q
        st.session_state["step_q"]      = step_q
        st.session_state["agent_thread"] = t
        st.rerun()

    # ── Live step display while running ───────────────────────────────────────
    if running:
        progress_slot = st.empty()
        with progress_slot:
            _render_live_steps(st.session_state.get("live_steps", []))
        time.sleep(0.8)
        st.rerun()

    # ── Error ─────────────────────────────────────────────────────────────────
    if "agent_error" in st.session_state:
        st.markdown(
            f'<div class="card card-error"><strong style="color:#C62828">Error</strong>'
            f'<br>{st.session_state["agent_error"]}</div>',
            unsafe_allow_html=True,
        )

    # ── Results ───────────────────────────────────────────────────────────────
    if st.session_state.get("result"):
        answer = st.session_state["result"]
        trace  = st.session_state.get("trace", [])
        last_q = st.session_state.get("last_query", "")

        st.markdown(f"""
<div class="stat-grid">
  <div class="stat-box"><div class="stat-val">{len(trace)}</div><div class="stat-label">ReAct steps</div></div>
  <div class="stat-box"><div class="stat-val">{len(answer.split()):,}</div><div class="stat-label">words</div></div>
  <div class="stat-box"><div class="stat-val">{len(answer):,}</div><div class="stat-label">characters</div></div>
</div>""", unsafe_allow_html=True)

        tab_result, tab_trace, tab_raw = st.tabs(["Result", "ReAct Trace", "Raw Markdown"])

        with tab_result:
            st.markdown('<div class="result-body">', unsafe_allow_html=True)
            st.markdown(answer)
            st.markdown('</div>', unsafe_allow_html=True)

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
