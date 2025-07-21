from setuptools import setup, find_packages

setup(
    name="elimu-research-assistant",
    version="1.0.2",
    packages=find_packages(),
    include_package_data=True,
    py_modules=["cli"],
    install_requires=[
        "click>=8.0.0",
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "html2text>=2020.1.16",
        "google-generativeai>=0.3.0",
        "python-dotenv>=0.19.0",
        "prompt_toolkit>=3.0.0",
        "rich>=10.0.0",
        "keyring>=23.0.0"
    ],
    entry_points={
        'console_scripts': [
            'elimu=cli:main',
        ],
    },
    author="Ashioya Jotham",
    author_email="victorashioya960@gmail.com",
    description="An intelligent research assistant for Kenyan educators to create localized, contextual educational content that bridges the context deficit in education.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ashioyajotham/elimu_research_assistant",
    project_urls={
        "Bug Tracker": "https://github.com/ashioyajotham/elimu_research_assistant/issues",
        "Documentation": "https://github.com/ashioyajotham/elimu_research_assistant#readme",
        "Source Code": "https://github.com/ashioyajotham/elimu_research_assistant",
        "Educational Impact": "https://github.com/ashioyajotham/elimu_research_assistant/wiki/Educational-Impact",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Education",
        "Topic :: Education :: Computer Aided Instruction (CAI)",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    keywords="education, kenya, ai, research, teaching, localized-content, curriculum, pedagogy, african-education, context-aware, educational-technology",
    python_requires=">=3.9",
)
