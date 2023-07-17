FROM ubuntu:22.04
RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && apt-get install -y python3 \
  && rm -rf /var/lib/apt/lists/*
RUN useradd -ms /bin/bash lutherlunyamwi
USER lutherlunyamwi
RUN python3 -m pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
RUN apt-get install -y chromium-browser

COPY . .
