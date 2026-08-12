FROM mcr.microsoft.com/devcontainers/python:3.12

# Install pipx
RUN python -m pip install --no-cache-dir pipx \
    && pipx ensurepath

# Install uv with pipx
RUN pipx install uv