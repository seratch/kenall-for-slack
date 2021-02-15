## ケンオール API を Slack から使えるようにする Slack アプリ（非公式）

この Slack アプリは、[ケンオール API](https://kenall.jp/) を Slack から呼び出せるようにする実装例を示すためのサンプルアプリです。

### デモ

<img src="https://user-images.githubusercontent.com/19658/107915466-e230c280-6fa7-11eb-987e-0f1e2a2241c1.gif" width=500>

### 動かし方

ケンオールの API キーを発行、Slack アプリの設定を https://api.slack.com/apps で行った後、以下で起動できます。以下の例は Flask を使っていますが、すでに[ソケットモード](https://api.slack.com/socket-mode)についてご存知なら、そちらの方が楽だと思います。ソケットモードで起動する場合は、[こちらの記事](https://qiita.com/seratch/items/1a460c08c3e245b56441)の Python の例を参考に `slack_bolt.adapter.socket_mode.SocketModeHandler` を使って起動してください。

```bash
git clone git@github.com:seratch/kenall-for-slack.git
cd kenall-for-slack

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

export SLACK_SIGNING_SECRET=
export SLACK_BOT_TOKEN=
export KENALL_API_KEY=

FLASK_APP=flask_app.py FLASK_ENV=development flask run -p 3000
```

別のターミナルで `ngrok http 3000` とすると公開 URL を発行できます。https://api.slack.com/apps のアプリ設定で Request URL に `http://{あなたのサブドメイン}.ngrok.io/slack/events` を設定してください。

### AWS Lambda で動かす

以下は python-lambda で Lambda を作って API Gateway は管理コンソールや aws-cli から手動で作る手順です。

```bash
pip install python-lambda
export SLACK_SIGNING_SECRET=
export SLACK_BOT_TOKEN=
export KENALL_API_KEY=
export SLACK_PROCESS_BEFORE_RESPONSE=1

lambda deploy \
  --config-file aws_lambda_config.yaml \
  --requirements requirements-aws.txt
```

python-lambda は非常に高速でデプロイできるのでここでは紹介していますが、API Gateway も含め管理したい場合は他のソリューションを使ってください。

### ライセンス

The MIT License