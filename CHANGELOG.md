# Changelog

All notable changes to Elimu Research Assistant will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.6] - 2026-04-03

### Performance
- Pre-warm `google-generativeai` (and `elimu_react`) in a daemon thread at page load, eliminating the ~11s "stuck at Initialising agent…" stall on first query
- Cache `ElimuConfigManager` in `st.session_state` — avoids repeating the keyring backend scan (~0.6s) on every Streamlit rerun

### Fixed
- Streamlit Cloud: `requirements.txt` was UTF-16 LE (null bytes between characters), causing pip to crash — rewritten as UTF-8, minimal 6-line file without Windows-only packages
- Streamlit Cloud: `init_config()` emitted API-key warnings before `st.secrets` values were injected; secrets now pushed to `os.environ` first
- Sidebar toggle inaccessible: `[data-testid="stToolbar"] { display: none }` wiped the whole toolbar including the toggle (Streamlit ≥1.32 moved the toggle inside the toolbar); fixed by targeting only decorative children
- Sidebar toggle invisible: `header { visibility: hidden }` hid the toggle area; replaced with targeted `[data-testid="stHeader"]` dark-background rule
- Example prefill caused `StreamlitAPIException` — cannot set a widget's session_state key after it is instantiated; fixed via staging key `"_prefill"` applied before `st.text_area` renders

### Changed
- Sidebar toggle is always white (`color: #ffffff`, SVG `fill: #ffffff`), with a gold glow + green tint on hover
- Poll interval reduced from 1.2s to 0.8s for slightly more responsive live-step updates
- Added `.streamlit/secrets.toml.example` as setup guide for Streamlit Cloud deployment

## [1.2.5] - 2026-04-03

### Fixed
- Shell: typing a partial/mistyped word (e.g. `ex`, `qui`) no longer fires a search query — unknown single-word inputs now show command suggestions (`Did you mean: exit?`); research only runs on explicit `search <query>`

### Changed
- Streamlit: model selector removed — model is shown as a read-only badge (`gemini-2.0-flash`) matching the CLI agent
- Streamlit: examples now auto-populate the input box on click (fixed via `key="query_input"` session_state binding)
- Streamlit: live ReAct step display while agent runs — shows each Thought + Action as it happens, updates every ~1.2 s
- Streamlit: Run Research button disabled while a run is in progress; Cancel button replaces Clear during a run
- Streamlit: About section added to sidebar with architecture summary, CLI install command, and PyPI/GitHub links
- Streamlit: CSS overhauled — secondary buttons (examples, clear) styled as dark chip elements distinct from the primary green action buttons; header wordmark, progress panel, and result body updated

## [1.2.4] - 2026-04-03

### Fixed
- `elimu config` (inside shell) crashed with `'ElimuConfigManager' object has no attribute 'items'` — switched to `get_all().items()` throughout
- `elimu config --show` had an incorrect `hasattr` guard that still hit the missing `items()` method — same fix applied
- `elimu research --format html` and `elimu batch-research --format html` wrote raw markdown into `.html` files; output is now a self-contained HTML document with dark-theme CSS and proper heading/bold/list rendering

## [1.2.3] - 2026-04-03

### Added
- `elimu logs` command — tail and filter `logs/agent.log` by level (debug/info/warning/error)
- `elimu history` command — view past shell queries from `~/.elimu_research_history`
- Both new commands listed in the `elimu` banner command table

### Fixed
- Version display now uses `importlib.metadata` as the authoritative source, eliminating the stale `1.1.1` fallback seen in PyPI-installed packages where `VERSION` file is not on the Python path

## [1.2.2] - 2026-04-03

### Added
- First-run setup panel: bare `elimu` now shows key status with `[+]`/`[x]` indicators and storage source (keyring/.env)
- Missing keys include direct signup URLs in the panel and at each prompt

### Changed
- Setup prompt panel explains that keys are stored in the system keyring — never written to disk as plaintext
- `elimu config` prompt includes URL hint inline: `https://aistudio.google.com/apikey` and `https://serper.dev/api-key`

## [1.2.1] - 2026-04-03

### Fixed
- `ModuleNotFoundError: No module named 'elimu_entry'` when running `elimu` from outside the project directory
- `elimu_entry` now declared under `py-modules` in `pyproject.toml` so it installs correctly in non-editable installs
- `web-research-agent` `cli.py` shadowing resolved: entry point changed from ambiguous `cli:main` to `elimu_entry:main`

## [1.2.0] - 2026-04-02

### Added
- Streamlit web app (`streamlit_app.py`): dark academic theme, sidebar config, ReAct trace display, result tabs, markdown download
- `streamlit` added as optional extra: `pip install elimu-research-assistant[webapp]`
- OIDC Trusted Publishing for PyPI — removed `PYPI_API_TOKEN` secret dependency

### Changed
- Centralised Rich colour palette in `utils/console_ui.py` (forest green `#2E7D32` + savanna gold `#F9A825`)
- All CLI panels, progress bars, and borders updated to use theme constants
- README rewritten: engineering/architecture focus, removed marketing copy, full config key reference table
- Answer panels in `elimu shell` and `elimu research` render proper Markdown (bold, headings, bullets)

## [1.0.3] - 2025-07-22

### Added
- Dynamic versioning system using VERSION file as single source of truth
- Enhanced MANIFEST.in to include all necessary package files
- Improved version bump script with changelog integration

### Changed
- Migrated from hardcoded versions to dynamic VERSION file system
- Updated setup.py to read version from VERSION file
- Enhanced __init__.py to dynamically load version
- Improved package structure for better maintainability

### Fixed
- Resolved version synchronization issues across all components
- Fixed flake8 compliance in config.py global variable usage
- Eliminated hardcoded version references in CLI and setup files
- Improved GitHub Actions workflow compatibility


### Added
- Coming soon: Multilingual support (English/Swahili)
- Coming soon: Offline content generation capabilities
- Coming soon: Mobile app development

## [1.1.1] - 2025-11-17

### Fixed
- **Critical:** Updated to use current Gemini API models (`gemini-2.0-flash`, `gemini-2.5-flash`) instead of deprecated 1.5 models
- Fixed ASCII art banner to correctly spell "ELIMU" (was displaying "ELMUY" or "REIMU" in previous attempts)
- Automatic migration of legacy model names in existing user configurations
- Enhanced model fallback chain with all current stable Gemini models

### Changed
- Default model: `gemini-2.0-flash` (was `gemini-1.5-flash`)
- Fallback model: `gemini-2.5-flash` (was `gemini-1.5-pro`)
- Extended fallback candidates to include `gemini-2.0-flash-001`, `gemini-2.5-flash-lite`, and `gemini-2.5-pro`

### Technical
- Updated `config/config.py` with new default models and legacy migration logic
- Updated `elimu_react/__init__.py` with current stable model candidates
- All users will automatically have their configs migrated on next run

## [1.0.2] - 2025-01-22

### Fixed
- Fixed version synchronization across all components
- Resolved global configuration variable usage in config.py
- Improved package structure for PyPI distribution
- Enhanced GitHub Actions workflow reliability

### Changed
- Implemented dynamic versioning using VERSION file
- Updated CLI banner to use dynamic version display
- Improved error handling in configuration management

### Technical
- Added proper flake8 compliance
- Fixed import paths in GitHub Actions workflow
- Enhanced package metadata for PyPI

## [1.0.1] - 2025-01-21

### Changed
- Updated branding to "Elimu Research Assistant"
- Enhanced educational focus in all user-facing text
- Improved CLI prompts and messaging for educators

### Fixed
- Fixed configuration directory naming consistency
- Updated banner and version display
- Improved shell command prompts

## [1.0.0] - 2025-01-20

### Added
- Initial release of Elimu Research Assistant
- Intelligent research assistant for Kenyan educators
- ReAct framework for research synthesis and content generation
- Localized educational content creation capabilities
- Context-aware content formatting for classroom use

#### Core Features
- **Educational Content Generation**: Create lesson plans, handouts, and teaching materials
- **Kenya-Focused Research**: Prioritizes local sources and contextual relevance
- **Multiple Output Formats**: Markdown, HTML, and JSON support
- **Batch Processing**: Handle multiple educational content requests
- **Interactive Shell**: Real-time content creation workflow

#### Educational Capabilities
- Lesson plan generation with learning objectives
- Student handout creation with local examples
- Assessment material development
- Cultural context integration
- Credible source verification and citation

#### Technical Foundation
- Built on proven ReAct (Reasoning + Acting) AI framework
- Google Gemini API integration for content generation
- Serper.dev API for comprehensive web search
- Robust error handling and fallback strategies
- Educational content formatting optimization

#### Command Line Interface
- `elimu research` - Single research query execution
- `elimu batch-research` - Process multiple requests from file
- `elimu shell` - Interactive content creation mode
- `elimu config` - API key and settings management

#### Educational Focus Areas
- Form 1-4 secondary education alignment
- Kenyan curriculum contextualization
- Local case studies and examples
- Cultural sensitivity and relevance
- Digital literacy promotion

### Changed
- Evolved from a general-purpose research tool to an education-focused tool
- Specialized algorithms for educational content synthesis
- Enhanced user experience for classroom practitioners
- Improved source prioritization for Kenyan educational context

### Documentation
- Comprehensive README with educational use cases
- Installation guide for educators
- Contributing guidelines for education community
- Sample outputs and classroom implementation examples

---

## Release Notes

### Versioning Strategy
- **Major versions** (x.0.0): Significant architectural changes or breaking changes
- **Minor versions** (x.y.0): New features, educational enhancements, or significant improvements
- **Patch versions** (x.y.z): Bug fixes, minor improvements, and maintenance updates

### Educational Impact Tracking
Each release includes metrics on:
- Educator adoption and feedback
- Content quality improvements
- Kenyan curriculum alignment enhancements
- Performance optimizations for local context

### Future Roadmap
- **Phase 2 (Q2 2025)**: Advanced curriculum alignment, multilingual support
- **Phase 3 (Q3-Q4 2025)**: LMS integration, collaborative features, mobile app

---

For detailed technical changes and developer notes, see the [commit history](https://github.com/ashioyajotham/elimu_research_assistant/commits/main).

For educational impact studies and classroom implementation guides, visit our [Educational Impact Wiki](https://github.com/ashioyajotham/elimu_research_assistant/wiki/Educational-Impact).
