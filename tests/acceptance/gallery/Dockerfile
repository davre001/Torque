FROM mcr.microsoft.com/playwright/python:v1.63.0-noble
RUN pip install --no-cache-dir playwright==1.63.0
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && rm -rf /var/lib/apt/lists/*
COPY package.json package-lock.json /opt/gallery-tools/
RUN cd /opt/gallery-tools && npm ci --ignore-scripts --no-audit --no-fund
ENV HOME=/tmp PLAYWRIGHT_BROWSERS_PATH=/ms-playwright NODE_PATH=/opt/gallery-tools/node_modules
