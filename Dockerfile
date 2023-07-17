FROM ubuntu:22.04
WORKDIR /
RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && apt-get install -y python3  python3-pip \
  chromium-browser gunicorn \
  && rm -rf /var/lib/apt/lists/*
RUN useradd -ms /bin/bash lutherlunyamwi
# The default user that should be used
ARG USER_ID=1000
ARG GROUP_ID=1000

ARG APP_USER=lutherlunyamwi


# Create user and group
RUN groupadd -g ${GROUP_ID} ${APP_USER} && useradd -u ${USER_ID} -g ${APP_USER} -s /bin/sh ${APP_USER}

# Install ca certificates
RUN apt-get update \
    && apt-get install ca-certificates -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /root/ /root/
RUN chown -R ${APP_USER}:${APP_USER} /root
RUN chmod 755 /root
RUN python3 -m pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

COPY . .

USER ${APP_USER}

CMD ["/bin/bash", "-c", "/entrypoint.sh"]
