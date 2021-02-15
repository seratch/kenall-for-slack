#
# docker build . -t your-repo/kenall-for-slack
#
FROM python:3.9.1-slim-buster as builder
COPY requirements-docker.txt /build/requirements.txt
WORKDIR /build/
RUN pip install -U pip && pip install -r requirements.txt

FROM python:3.9.1-slim-buster as app
WORKDIR /app/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
COPY *.py /app/
ENTRYPOINT gunicorn --bind :$PORT --workers 1 --threads 2 --timeout 0 flask_app:flask_app

#
# docker run -e SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET -e SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN -e KENALL_API_KEY=$KENALL_API_KEY -e PORT=3000 -p 3000:3000 -it your-repo/kenall-for-slack
#

