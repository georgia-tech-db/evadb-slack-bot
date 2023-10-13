import slack_client
import json
from logging import Logger

def say (arg1, **kwargs):
    print(arg1)

def test_slack_bot():
    body = """
{
    "token": "ZZZZZZWSxiZZZ2yIvs3peJ",
    "team_id": "T123ABC456",
    "api_app_id": "A123ABC456",
    "event": {
        "type": "app_mention",
        "user": "U123ABC456",
        "text": "What is the hour of the pearl, <@U0LAN0Z89>?",
        "ts": "1515449522.000016",
        "channel": "C123ABC456",
        "event_ts": "1515449522000016"
    },
    "type": "event_callback",
    "event_id": "Ev123ABC456",
    "event_time": 1515449522000016,
    "authed_users": [
        "U0LAN0Z89"
    ]
}"""
    slack_client.handle_mention(json.loads(body), say, Logger)
test_slack_bot()