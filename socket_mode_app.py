import os
from slack_bolt.adapter.socket_mode import SocketModeHandler

if __name__ == "__main__":
    from app import app

    app_level_token = os.environ["SLACK_APP_TOKEN"]
    handler = SocketModeHandler(app, app_level_token)
    handler.start()

# export KENALL_API_KEY=
# export SLACK_SIGNING_SECRET=
# export SLACK_BOT_TOKEN=xoxb-
# export SLACK_APP_TOKEN=xapp-
# python socket_mode_app.py
