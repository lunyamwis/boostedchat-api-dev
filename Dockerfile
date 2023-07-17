FROM ubuntu:22.04
WORKDIR /
RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && apt-get install -y python3  python3-pip \
  chromium-browser gunicorn  python3-gevent\
  && rm -rf /var/lib/apt/lists/*
RUN useradd -ms /bin/bash lutherlunyamwi
USER root

RUN python3 -m pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

COPY . .

CMD ["/bin/bash", "+x", "/entrypoint.sh"]
