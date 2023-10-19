import json
import logging
import evadb
from slack_client import handle_mention
from eva_queries.rag_queries import load_slack_dump
import os


def test_slack_dump_conversion():
    cursor = evadb.connect().cursor()
    cursor.query("""DROP TABLE IF EXISTS OMSCSPDFTable""").df()
    pdf_path="./test_inputs_pdf/"
    for filename in os.listdir(pdf_path):
        file_path = os.path.join(pdf_path, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted old file: {filename}")
            except Exception as e:
                print(f"Error deleting old file {filename}: {e}")
    load_slack_dump(cursor, path="./test_inputs/", pdf_path=pdf_path)


def say (arg1, **kwargs):
    print(arg1)


def test_slack_bot():
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
test_slack_dump_conversion()