# EvaDB Slack Bot

This bot 🤖 allows users to ask questions about PDFs 📄 using EvaDB: https://github.com/georgia-tech-db/evadb. 

## Installation
### Local Host
> Note: requries ngrok

#### 1) Export your Slack Bot Token and Signing Key to the environment
```bash
export SLACK_BOT_TOKEN=<your-slack-token>
export SLACK_SIGNING_SECRET=<you-slack-siging-secret>
```


#### 2) Load the PDF datasets into EvaDB  
Refer ![EvaDB Docs](https://evadb.readthedocs.io/en/stable/)  

#### 3) Start Flask server
```bash
FLASK_APP=slack_client.py FLASK_ENV=development flask run -p <port-number>
```

#### 4) (Optional) Expose your Public IP
```bash
ngrok http <port-number>
```
