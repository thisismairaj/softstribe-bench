FROM python:3.13-slim
RUN apt-get update -qq && apt-get install -y -qq bc >/dev/null && rm -rf /var/lib/apt/lists/*
RUN pip install -q --root-user-action=ignore --upgrade pip==26.3 uv==0.13.9
