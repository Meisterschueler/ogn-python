# Builder stage (full image)
FROM python:3.9-bullseye AS builder-image

# ... get build tools and dev dependencies
RUN apt update && \
    apt install -y \
    libgeos-dev

# ... get needed files for the build
COPY requirements.txt .
COPY setup.py .
COPY README.md .

# ... install everything into the venv
RUN python3 -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install -r requirements.txt

# Final stage (slim image)
FROM python:3.9-slim-bullseye AS compile-image

# ... get dependencies
RUN apt update && \
    apt install -y --no-install-recommends \
    libgeos-c1v5 \
    libjpeg62 libopenjp2-7 libtiff5 libxcb1

# ... get the venv from above
COPY --from=builder-image /opt/venv /opt/venv
ENV PATH "/opt/venv/bin:$PATH"

# ... get ogn-python
RUN mkdir /app
WORKDIR /app
ADD app app
ADD migrations migrations
COPY *.py /app/

# ... get convenience scripts
COPY deployment/docker/ogn-python/prestart.sh .
COPY deployment/docker/ogn-python/wait.sh .
