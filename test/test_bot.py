from slack_client import handle_mention, handle_file_sharing
import json
import logging

def say (arg1, **kwargs):
    print(arg1)

def test_slack_bot():
#     file_shared_body = """{
# 	"type": "file_shared",
# 	"channel_id": "D01315BHHSN",
# 	"file_id": "F2147483862",
# 	"user_id": "U0Z7K8SRH", 
# 	"file": {
# 		"id": "F2147483862"
# 	},
# 	"event_ts": "1617804931.000300"
# }"""
#     handle_file_sharing(json.dumps(file_shared_body), say, logging)

    handle_message_body = """
{
    "token": "ZZZZZZWSxiZZZ2yIvs3peJ",
    "team_id": "T123ABC456",
    "api_app_id": "A123ABC456",
    "event": {
        "type": "app_mention",
        "user": "U123ABC456",
        "text": "<@U0LAN0Z89> Which is the hardest course in OMSCS?",
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
    handle_mention(json.loads(handle_message_body), say, logging)
test_slack_bot()