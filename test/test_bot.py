import json
import logging
import evadb
import os
import logging
from slack_client import handle_mention
from eva_queries.rag_queries import (
    build_relevant_knowledge_body_pdf,
    build_search_index,
    load_slack_dump,
    create_feature_extractor,
)
from utils.logging import QUERY_LOGGER

def clean_setup(cursor):
    cursor.query("""DROP INDEX IF EXISTS OMSCSIndex""").df()
    cursor.query("""DROP TABLE IF EXISTS OMSCSPDFTable""").df()
    pdf_path="test_inputs_pdf"
    for filename in os.listdir("./" + pdf_path + "/"):
        file_path = os.path.join("./" + pdf_path + "/", filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting old file {filename}: {e}")

def slack_dump_conversion(cursor):
    clean_setup(cursor)
    load_slack_dump(cursor, path="test_inputs", pdf_path="test_inputs_pdf", workspace_name="OMSCSStudentLife", channel_name="atlanta")

def test_slack_dump_conversion():
    cursor = evadb.connect().cursor()
    slack_dump_conversion(cursor)

def test_e2e_pipeline():
    cursor = evadb.connect().cursor()
    user_query = "Do we need to have a background in security before taking information security course?"
    workspace_name = "OMSCSStudentLife"
    channel_name = "atlanta"
    channel_id = f"{workspace_name}___{channel_name}___slackdump.pdf"
    create_feature_extractor(cursor)
    slack_dump_conversion(cursor)
    build_search_index(cursor)
    print(build_relevant_knowledge_body_pdf(cursor, user_query,channel_id, QUERY_LOGGER))

def say (arg1, **kwargs):
    print(arg1)


def test_slack_bot_answer():
    handle_message_body = """
{
    "token": "ZZZZZZWSxiZZZ2yIvs3peJ",
    "team_id": "T123ABC456",
    "api_app_id": "A123ABC456",
    "event": {
        "type": "app_mention",
        "user": "U123ABC456",
        "text": "<@U0LAN0Z89> Do we need to have a background in security before taking information security course?",
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
    clean_setup(evadb.connect().cursor())
    handle_mention(json.loads(handle_message_body), say, logging)

def test_handle_message():
    import pickle
    body = pickle.load(open("test_inputs/body.pkl", "rb"))
    def convert_say_to_print(message, thread_ts=None):
        print(message)
    say = convert_say_to_print
    from slack_client import handle_message
    handle_mention(body, say, QUERY_LOGGER)
