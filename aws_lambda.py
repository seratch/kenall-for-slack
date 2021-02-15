import logging

from slack_bolt.adapter.aws_lambda import SlackRequestHandler

SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)

from app import app

slack_handler = SlackRequestHandler(app=app)


def handler(event, context):
    return slack_handler.handle(event, context)


# pip install python-lambda
#
# export SLACK_SIGNING_SECRET=
# export SLACK_BOT_TOKEN=
# export KENALL_API_KEY=
# export SLACK_PROCESS_BEFORE_RESPONSE=1
#
# lambda deploy --config-file aws_lambda_config.yaml --requirements requirements-aws.txt
