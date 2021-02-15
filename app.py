import logging
import os
from logging import Logger
from typing import List, Dict, Any, Callable
from urllib.parse import quote

from slack_bolt import App, Ack
from slack_sdk import WebClient

logging.basicConfig(level=logging.DEBUG)

# Visit https://kenall.jp/home and grab your api key
kenall_api_key = os.environ["KENALL_API_KEY"]

# This value must be True when you run this app on FaaS
pbr_env = os.environ.get("SLACK_PROCESS_BEFORE_RESPONSE")
process_before_response = pbr_env is not None and pbr_env == "1"

app = App(
    token_verification_enabled=False,
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    process_before_response=process_before_response,
)


@app.middleware
def print_request(body: dict, next: Callable, logger: Logger):
    if logger.level <= logging.DEBUG:
        logger.debug(f"Request body: {body}")
    next()


search_form = {
    "type": "modal",
    "callback_id": "kenall-search",
    "title": {
        "type": "plain_text",
        "text": "ケンオール検索",
    },
    "submit": {
        "type": "plain_text",
        "text": "検索",
    },
    "close": {
        "type": "plain_text",
        "text": "キャンセル",
    },
    "blocks": [
        {
            "type": "input",
            "block_id": "postal_code",
            "element": {
                "type": "plain_text_input",
                "action_id": "input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "郵便番号を指定してください",
                },
            },
            "label": {
                "type": "plain_text",
                "text": "郵便番号",
            },
        },
    ],
}


def open_search_window_if_no_arg(body: dict, client: WebClient):
    if len(body.get("text", "").strip()) == 0:
        client.views_open(
            trigger_id=body["trigger_id"],
            view=search_form,
        )


def handle_commands(body: dict, ack: Ack, logger: Logger):
    postal_code = body.get("text", "").strip()
    if len(postal_code) == 0:
        ack()
    else:
        blocks = call_kenall_and_build_blocks(postal_code, logger)
        ack(
            text="ケンオールでの検索結果です",
            blocks=blocks,
        )


app.command(command="/kenall")(
    ack=handle_commands,
    lazy=[open_search_window_if_no_arg],
)


@app.shortcut("kenall-search")
def handle_shortcuts(body: dict, ack: Ack, client: WebClient):
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view=search_form,
    )


@app.view("kenall-search")
def show_search_result(ack: Ack, view: dict, client: WebClient, logger: Logger):
    if len(view["state"]["values"]) == 0:
        return ack(
            response_action="update",
            view=search_form,
        )

    postal_code = view["state"]["values"]["postal_code"]["input"]["value"]
    if postal_code is None:
        return ack(response_action="errors", errors={"postal_code": "郵便番号を指定してください"})
    postal_code = postal_code.replace("-", "")
    if len(postal_code) < 7 or not postal_code.isnumeric():
        return ack(
            response_action="errors",
            errors={"postal_code": "郵便番号は 123-4567 または 1234567 の形式で指定してください"},
        )

    if not process_before_response:
        ack(
            response_action="update",
            view={
                "type": "modal",
                "callback_id": "kenall-search",
                "title": {
                    "type": "plain_text",
                    "text": "ケンオール検索",
                },
                "close": {
                    "type": "plain_text",
                    "text": "閉じる",
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f":postbox: *〒 {postal_code}* に対応する郵便区画を検索中... :mag:",
                        },
                    }
                ],
            },
        )

    blocks = call_kenall_and_build_blocks(postal_code, logger)
    result_view = {
        "type": "modal",
        "callback_id": "kenall-search",
        "title": {
            "type": "plain_text",
            "text": "ケンオール検索",
        },
        "submit": {
            "type": "plain_text",
            "text": "再検索",
        },
        "close": {
            "type": "plain_text",
            "text": "閉じる",
        },
        "blocks": blocks,
    }
    if process_before_response:
        ack(response_action="update", view=result_view)
    else:
        client.views_update(view_id=view["id"], view=result_view)


import requests


def call_kenall_and_build_blocks(
    postal_code: str, logger: Logger
) -> List[Dict[str, Any]]:
    postal_code = postal_code.replace("-", "").replace("*", "").strip()
    url = f"https://api.kenall.jp/v1/postalcode/{quote(postal_code)}"
    headers = {"Authorization": f"Token {kenall_api_key}"}
    res = requests.get(url, headers=headers)
    logger.debug(f"KENALL API response (status: {res.status_code}, body: {res.text})")
    printable_code = postal_code[:3] + "-" + postal_code[3:]
    if res.status_code == 200:
        results = res.json().get("data")
        result_num = len(results)
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":postbox: *〒 {printable_code}* に対応する {result_num} 件の郵便区画が見つかりました :postbox:",
                },
            }
        ]
        for result in results:
            fields = []
            if len(result.get("prefecture", "")) > 0:
                fields.append(
                    {"type": "mrkdwn", "text": f"*都道府県:*\n{result['prefecture']}"}
                )
            if len(result.get("city", "")) > 0:
                fields.append({"type": "mrkdwn", "text": f"*市区町村:*\n{result['city']}"})
            if len(result.get("town", "")) > 0:
                fields.append({"type": "mrkdwn", "text": f"*町域名:*\n{result['town']}"})
            if len(result.get("koaza", "")) > 0:
                fields.append(
                    {"type": "mrkdwn", "text": f"*小字・丁目:*\n{result['koaza']}"}
                )
            if len(result.get("building", "")) > 0:
                fields.append(
                    {"type": "mrkdwn", "text": f"*ビル名:*\n{result['building']}"}
                )
            if len(result.get("floor", "")) > 0:
                fields.append(
                    {"type": "mrkdwn", "text": f"*ビルの階層:*\n{result['floor']}"}
                )
            if result.get("corporation") is not None:
                fields.append(
                    {
                        "type": "mrkdwn",
                        "text": f"*事業所:*\n{result['corporation']['name']}",
                    }
                )
                fields.append(
                    {
                        "type": "mrkdwn",
                        "text": f"*小字名、丁目、番地等:*\n{result['corporation']['block_lot']}",
                    }
                )
                fields.append(
                    {
                        "type": "mrkdwn",
                        "text": f"*取扱郵便局:*\n{result['corporation']['post_office']}",
                    }
                )
                code_type = (
                    "大口事業所" if result["corporation"]["code_type"] == 0 else "私書箱"
                )
                fields.append({"type": "mrkdwn", "text": f"*個別番号の種別:*\n{code_type}"})
            blocks.append({"type": "divider"})
            blocks.append({"type": "section", "fields": fields})

        return blocks

    if res.status_code == 404:
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":postbox: *〒 {printable_code}* に対応する郵便区画は見つかりませんでした :postbox:",
                },
            }
        ]
    raise RuntimeError(
        f"Failed to call KENALL API (status: {res.status_code}, body: {res.text})"
    )
