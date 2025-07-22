# Changelog

All notable changes to Elimu Research Assistant will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Updated branding from "Web Research Agent" to "Elimu Research Assistant"
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
- Evolved from academic "Web Research Agent" to education-focused tool
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
