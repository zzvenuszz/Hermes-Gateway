# ====================================================================
# Dockerfile: Cockpit Container Management Dashboard for Hugging Face Spaces
# Base Image: Debian Bookworm Slim (Lightweight, ~280MB)
# Includes essential system utilities + Cockpit Full Suite & Navigator
# ====================================================================

FROM debian:bookworm-slim

# Avoid prompts during apt installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV ADMIN_USER=admin
ENV ADMIN_PASSWORD=admin123

# Install system packages, Cockpit full suite, Python, SSH, xz-utils, file manager deps, and essential tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    screen \
    iputils-ping \
    net-tools \
    iproute2 \
    nano \
    vim \
    htop \
    tar \
    gzip \
    unzip \
    zip \
    rsync \
    file \
    inotify-tools \
    xz-utils \
    sudo \
    procps \
    openssh-server \
    cockpit \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install 45Drives Cockpit Navigator (Native Debian Bookworm File Manager)
RUN curl -sSL -o /tmp/navigator.deb https://github.com/45Drives/cockpit-navigator/releases/download/v0.6.1/cockpit-navigator_0.6.1-1bookworm_all.deb \
    && dpkg -i /tmp/navigator.deb \
    && rm /tmp/navigator.deb

# Pre-create admin user and configure sudoers at build time (bypasses runtime no_new_privs on Render)
RUN useradd -m -s /bin/bash admin && \
    echo "admin:admin123" | chpasswd && \
    mkdir -p /etc/sudoers.d && \
    echo "admin ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/admin && \
    chmod 0440 /etc/sudoers.d/admin

# Set working directory
WORKDIR /app

# Copy project files
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages || pip3 install --no-cache-dir -r requirements.txt

COPY . /app/

# Make app.py executable
RUN chmod +x /app/app.py

# Expose port 7860 for Hugging Face Spaces & Standalone Docker
EXPOSE 7860

# Launch orchestrator
CMD ["python3", "/app/app.py"]
