ARG PYTHON_VERSION=""
FROM python:$PYTHON_VERSION-alpine

ENV USER=riotkit
ENV UID=1000
ENV GID=1000

RUN addgroup -g $GID $USER
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "$(pwd)" \
    --ingroup "$USER" \
    --no-create-home \
    --uid "$UID" \
    "$USER"

ADD ./ /workspace
ADD .ci/entrypoint.sh /

RUN apk add git make bash openssh && mkdir -p /.ssh
RUN chown 1000:1000 -R /workspace /.ssh

USER riotkit
ENTRYPOINT '/entrypoint.sh'
WORKDIR /workspace
