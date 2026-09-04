# ====================================================================
# Dockerfile: Cockpit Container Management Dashboard for Hugging Face & Render
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

# Install system packages, Cockpit full suite, Python, C/C++ build toolchain, SSH, xz-utils, file manager deps, and essential tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    gcc \
    make \
    python3-dev \
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

# Pre-create admin user and configure sudoers at build time
RUN useradd -m -s /bin/bash admin && \
    echo "admin:admin123" | chpasswd && \
    echo "root:admin123" | chpasswd && \
    mkdir -p /etc/sudoers.d && \
    echo "admin ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/admin && \
    chmod 0440 /etc/sudoers.d/admin

# Allow root login in Cockpit
RUN mkdir -p /etc/cockpit && echo "" > /etc/cockpit/disallowed-users

# Bypass "no new privileges" setuid restriction on Render/Cloud Run/HF by replacing setuid sudo with root wrapper
RUN mv /usr/bin/sudo /usr/bin/sudo.real 2>/dev/null || true && \
    echo '#!/bin/bash' > /usr/bin/sudo && \
    echo 'if [ "$(id -u)" -eq 0 ]; then' >> /usr/bin/sudo && \
    echo '  args=()' >> /usr/bin/sudo && \
    echo '  for arg in "$@"; do' >> /usr/bin/sudo && \
    echo '    case "$arg" in' >> /usr/bin/sudo && \
    echo '      -n|-v|-E|-s|-i|-S|-H|-P|-b) ;;' >> /usr/bin/sudo && \
    echo '      *) args+=("$arg") ;;' >> /usr/bin/sudo && \
    echo '    esac' >> /usr/bin/sudo && \
    echo '  done' >> /usr/bin/sudo && \
    echo '  [ ${#args[@]} -eq 0 ] && exit 0' >> /usr/bin/sudo && \
    echo '  exec "${args[@]}"' >> /usr/bin/sudo && \
    echo 'else' >> /usr/bin/sudo && \
    echo '  exec /usr/bin/sudo.real "$@"' >> /usr/bin/sudo && \
    echo 'fi' >> /usr/bin/sudo && \
    chmod 755 /usr/bin/sudo

# Set working directory
WORKDIR /app

# Copy project files
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages || pip3 install --no-cache-dir -r requirements.txt

COPY . /app/

# Make app.py executable
RUN chmod +x /app/app.py

# Expose port 7860 for Hugging Face Spaces, Render & Standalone Docker
EXPOSE 7860

# Launch orchestrator
CMD ["python3", "/app/app.py"]
