# EvaDB Slack Bot
evadb-slack-bot is an ongoing project to allow users to use the features of EvaDB on slack, using Natural Language queries.
## Installation
### Local host
> Note: requries ngrok


#### 1) Add your Token and Signing key to the terminal
```bash
export SLACK_BOT_TOKEN=<your-slack-token>
export SLACK_SIGNING_SECRET=<you-slack-siging-secret>
```


#### 2) Initialize EvaDB with data you might want  
refer ![EvaDB Docs](https://evadb.readthedocs.io/en/stable/)  


#### 3) Start Flask server
```bash
FLASK_APP=slack_client.py FLASK_ENV=development flask run -p <port-number>
```

#### 4) (Optional) expose your public IP
```bash
ngrok http <port-number>
```
