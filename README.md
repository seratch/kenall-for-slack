## ケンオール API を Slack から使えるようにするアプリ（非公式）

この Slack アプリは、[ケンオール API](https://kenall.jp/) を Slack から呼び出せるようにする実装例を示すためのサンプルアプリです。

### デモ

<img src="https://user-images.githubusercontent.com/19658/107915466-e230c280-6fa7-11eb-987e-0f1e2a2241c1.gif" width=500>

### とりあえず動かしてみる

ケンオールの API キーを発行、Slack アプリの設定を https://api.slack.com/apps で行った後、以下で起動できます。

#### Slack アプリ初期設定

Slack アプリの設定でやることは

* **Features** > **OAuth & Permissions** で Bot Token Scopes に `commands` scope を追加
* **Settings** > **Basic Information** の **Signing Secret** を `SLACK_SIGNING_SECRET` として環境変数に設定
* **Settings** > **Install App** からインストールし、`xoxb-` ではじまる **Bot User OAuth Access Token** を `SLACK_BOT_TOKEN` として環境変数に設定

が最低限の設定です。後ほどスラッシュコマンド、ショートカット・モーダルの有効化をしましょう。

#### ケンオール設定

アカウントを作成して、トライアルの状態で API キーを取得するだけです。

#### Flask やソケットモードを使ったアプリ設定

この例は Flask を使っていますが、すでに[ソケットモード](https://api.slack.com/socket-mode)についてご存知なら、そちらの方が楽だと思います。ソケットモードで起動する場合は、[こちらの記事](https://qiita.com/seratch/items/1a460c08c3e245b56441)の Python の例を参考に `python socket_mode_app.py` で起動してみてください。

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

#### スラッシュコマンド、ショートカット・モーダルを有効化

Flask で動かしているなら、確定したエンドポイントの URL を Request URL として **Slash Commands** と **Interactivity & Shortcuts** の設定画面に設定してください。ソケットモードを使っているなら URL の設定は不要です。

<img width="600"  src="https://user-images.githubusercontent.com/19658/107947337-998ffe00-6fd5-11eb-8858-a1527561ec80.png">
<img width="600" src="https://user-images.githubusercontent.com/19658/107947347-9bf25800-6fd5-11eb-98d2-7e6cbe0cbc1e.png">

スラッシュコマンドは `/kenall`、グローバルショートカットの Callback ID は `kenall-search` とすると、このサンプルアプリのコードそのままで動作するでしょう。

### Heroku で動かす

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

または

```bash
heroku create
heroku config:set SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET
heroku config:set SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
heroku config:set KENALL_API_KEY=$KENALL_API_KEY

git add . -v
git commit -m'ケンオールでKEN_ALLに革命を。'
git push heroku main
```

Heroku アプリが起動したら https://api.slack.com/apps のアプリ設定へ行き、**Interactivity & Shortcuts** と **Slash Commands** の **Request URL** に `https://{あなたのサブドメイン}.herokuapp.com/slack/events` を設定してください。

### Docker で動かす

Flask + Gunicorn の雛形の Dockerfile を置いてありますが、自由に変更してください。

```bash
docker build . -t your-repo/kenall-for-slack

docker run \
  -e SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET \
  -e SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN \
  -e KENALL_API_KEY=$KENALL_API_KEY \
  -e PORT=3000 \
  -p 3000:3000 \
  -it your-repo/kenall-for-slack
```

### AWS Lambda で動かす

以下は python-lambda で Lambda を作って API Gateway は管理コンソールや aws-cli から手動で作る手順です。

```bash
# Lambda から Lambda を起動できる権限が必要です

export policy_arn=`aws iam create-policy --policy-name aws-lambda-invocation-policy --policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["lambda:InvokeFunction", "lambda:GetFunction"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}' | jq .Policy.Arn | tr -d \"`

aws iam create-role --role-name aws-lambda-invocation-role --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": ["lambda.amazonaws.com"] },
      "Action": ["sts:AssumeRole"]
    }
  ]
}
'
aws iam attach-role-policy --role-name aws-lambda-invocation-role --policy-arn $policy_arn

# 必要な環境変数をあらかじめ設定しておきます

export SLACK_SIGNING_SECRET=
export SLACK_BOT_TOKEN=
export KENALL_API_KEY=
# Lambda のときはこれを忘れずに
export SLACK_PROCESS_BEFORE_RESPONSE=1

# デプロイに python-lambda というツールを使用します（アプリはこれに依存しません）

pip install python-lambda

lambda deploy \
  --config-file aws_lambda_config.yaml \
  --requirements requirements-aws.txt
```

python-lambda は非常に高速なデプロイができるツールなので、紹介していますが、API Gateway も含め一元管理したい場合は他のソリューションを使ってください。

### ライセンス

The MIT License
