# Elimu Research Assistant

An AI research agent for Kenyan educators that generates locally-grounded educational content using a ReAct (Reasoning + Acting) loop over live web search.

## What It Does

Given a teaching request such as `"Create a Form 3 Business Studies lesson on M-Pesa's impact on small enterprises"`, the agent:

1. Reasons about what to search and in what order
2. Executes web searches via Serper.dev, biased toward `.ke` and East African domains
3. Scrapes and cleans source pages for relevant content
4. Iterates (up to 12 reasoning steps by default) until it can synthesize a cited, structured educational artefact
5. Returns classroom-ready output: lesson plan, case study, handout, or assessment, depending on the request

## Architecture

```
CLI / Streamlit
      │
      ▼
build_elimu_agent()          ← elimu_react/__init__.py
      │
      ├── LLMInterface        ← Google Gemini 2.x (primary: gemini-2.0-flash)
      │     └── model fallback chain (2.0-flash → 2.5-flash → 2.5-pro)
      │
      ├── ToolManager
      │     ├── SearchTool    ← Serper.dev (Google Search API)
      │     │     └── Kenya bias: appends "Kenya", prioritises .ke / .ac.ke
      │     └── ScrapeTool    ← requests + BeautifulSoup, 6 000 char limit
      │
      └── ReActAgent          ← elimu_react/agent.py
            └── run(task) → ReAct loop (max 15 iters)
                  Thought → Action → Observation → … → Final Answer
```

### ReAct Loop (elimu_react/agent.py)

Each iteration:
1. Build a prompt: system instructions + tool descriptions + task + prior steps
2. Call LLM → parse `Thought`, `Action`, `Action Input`, or `Final Answer`
3. If action: dispatch to `SearchTool` or `ScrapeTool`, collect observation
4. Append step to trace; repeat
5. On `Final Answer` or exhausted iterations → return synthesis

The system prompt instructs the model to produce classroom-ready artefacts with Kenyan examples and cited sources, and to never fabricate URLs or statistics.

### Configuration (config/config.py)

Credentials and settings are resolved in priority order: `.env` → environment variables → system keyring. Non-sensitive settings persist in `~/.elimu_research_assistant/config.json`.

| Key | Default | Description |
|-----|---------|-------------|
| `gemini_api_key` | — | Required. Google Gemini API key |
| `serper_api_key` | — | Required. Serper.dev API key |
| `model_name` | `gemini-2.0-flash` | Primary LLM model |
| `model_fallback` | `gemini-2.5-flash` | Fallback on 404/quota |
| `model_temperature` | `0.15` | Low temperature for factual output |
| `max_iterations` | `12` | ReAct loop cap |
| `max_tool_output_length` | `6000` | Observation truncation (chars) |
| `educational_focus` | `True` | Adds "classroom" to education queries |
| `prioritize_kenyan_sources` | `True` | Biases search toward .ke domains |

## Installation

```bash
git clone https://github.com/ashioyajotham/elimu_research_assistant.git
cd elimu_research_assistant
pip install -e .
```

### API Keys

You need two keys:

- **Google Gemini**: [aistudio.google.com](https://aistudio.google.com) — free tier available
- **Serper.dev**: [serper.dev](https://serper.dev) — 2 500 free searches/month

```bash
elimu config --api-key YOUR_GEMINI_KEY
elimu config --serper-key YOUR_SERPER_KEY
```

Keys are stored in the Windows system keyring by default, or in `.env` if keyring is unavailable.

## CLI Usage

```bash
# Single research task
elimu research "Create a Form 3 lesson on M-Pesa's impact on small enterprises"

# Batch from file (one task per line or blank-line-separated blocks)
elimu batch-research tasks.txt --output results/

# Interactive shell with history and autocomplete
elimu shell

# Configuration
elimu config --show
elimu config --model gemini-2.5-pro
elimu config --format markdown   # markdown | json | html
```

Output files are saved to `results/result_<sanitized-query>.md` by default.

## Streamlit Webapp

```bash
pip install streamlit
streamlit run streamlit_app.py
```

The webapp exposes the same research agent with a browser UI: sidebar configuration, research input, expandable ReAct trace, and inline result rendering.

## Project Structure

```
elimu_research_assistant/
├── elimu_react/          # ReAct agent engine
│   ├── agent.py          # ReActAgent: reasoning loop
│   ├── llm.py            # LLMInterface: Gemini wrapper with fallback
│   └── tools/
│       ├── search.py     # SearchTool (Serper.dev)
│       └── scrape.py     # ScrapeTool (requests + BS4)
├── config/
│   ├── config.py         # ElimuConfigManager: env / keyring / file
│   └── config_manager.py # BaseConfigManager
├── utils/
│   ├── console_ui.py     # Rich theme, panels, progress
│   ├── react_output.py   # Markdown serialiser for ReAct traces
│   └── task_parser.py    # Multi-line task file parser
├── cli.py                # Click CLI entry point
├── streamlit_app.py      # Streamlit webapp
└── pyproject.toml
```

## Development

```bash
pip install -r requirements.txt
python -m pytest
```

Logs are written to `logs/agent.log`. Set `--verbose` on any CLI command for INFO-level output.

## License

MIT — see [LICENSE](LICENSE).

## Author

Ashioya Jotham · [victorashioya960@gmail.com](mailto:victorashioya960@gmail.com)
