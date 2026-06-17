# The Deep Researcher

This project showcases a practical implementation build of the deep researcher.

![High-level Architecture](images/high-level_architecture.png)

**Agent workflow**

![Agent Workflow](images/agent-workflow.png)

## Techstack:

- Model
    - OpenAI: gpt-5.1
    - Google: Gemini 3.1 Flash Lite
- Python v3.14
- LangChain v1.3.9
- LangGraph v1.2.5
- LangFuse
- FastAPI
- CopilotKit

## Dependencies

This project uses a [VSCode Devcontainer](https://code.visualstudio.com/docs/devcontainers/containers) for a consistent development environment.

- **Docker**
- **Visual Studio Code**

## Setup and Installation

### 1. Clone the Repository

```bash
git clone git@gitlab.asoft-python.com:hien.nguyenvan/ai-training.git
cd ai-training/deep_researcher_agent
```

### 2. Launch the Code Editor

- Ensure Docker is running.
- Open the project folder (`deep_researcher_agent`) in Visual Studio Code.
- VSCode will automatically create a dev container in Docker.

### 3. Set Up Environment Variables

- Duplicate the sample environment variables file `.env.sample` to `.env`.
- Replace placeholder values with your actual environment variables (e.g., `OPENAI_API_KEY`, ...).