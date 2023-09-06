# coding=utf-8
# Copyright 2018-2023 EvaDB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging

# logging.basicConfig(level=logging.DEBUG)

import openai
from subprocess import run
from slack import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings
from langchain.chains.question_answering import load_qa_chain
from eva_queries.rag_queries import build_relevant_knowledge_body, rag_query

import evadb
# from evadb.test.util import get_evadb_for_testing

import os
from configparser import ConfigParser

config.read('config.ini')

SLACK_BOT_TOKEN = config.get('main', 'SLACK_BOT_TOKEN')
SLACK_APP_TOKEN = config.get('main', 'SLACK_APP_TOKEN')
OPENAI_API_KEY = config.get('main', 'OPENAI_API_KEY')

# SLACK_BOT_TOKEN = ConfigurationManager().get_value("third_party", "SLACK_BOT_TOKEN")
# SLACK_APP_TOKEN = ConfigurationManager().get_value("third_party", "SLACK_APP_TOKEN")
# OPENAI_API_KEY = ConfigurationManager().get_value("third_party", "OPENAI_KEY")

app = App(token=SLACK_BOT_TOKEN)
cursor = None
client = WebClient(token=SLACK_BOT_TOKEN)


# Starts and initializes Eva Server
def start_eva_server():
    cursor = evadb.connect().cursor()
    return cursor


@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()


@app.event("app_mention")
def event_gpt(body, say, logger):
    # Convert message body to message and eva query
    # TODO: remove print statements
    print("\n\n\nEvent triggered\n\n")
    message_body = str(body["event"]["text"]).split(">")[1]
    print("The message body is:", message_body, end="\n\n\n")
    message_queries = message_body.split("%Q")
    # User query
    user_query = message_queries[0]
    print("The user_query is:", user_query, end="\n\n\n")
    # Eva query
    if len(message_queries)>1:
        eva_query = message_body.split("%Q")[1]
        print("The eva_query is:", eva_query, end="\n\n")

    say("Query received now running:")

    if user_query.strip():
        knowledge_body = build_relevant_knowledge_body(cursor, user_query, say)
        conversation = rag_query(knowledge_body, user_query)
        print("The conversation was:", conversation, end="\n\n")
        openai.api_key = OPENAI_API_KEY
        openai_response = (
            openai.Completion.create(
                engine="text-davinci-003",
                messages=conversation,
                prompt=user_query,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.5,
            )
            .choices[0]
            .text
        )

        say(openai_response)


@app.event("file_shared")
def event_test(body, say, logger):

    file_id = str(body["event"]["file_id"])
    say(f"Downloading this file, please wait.")
    file_info = client.files_info(file=file_id)
    url = file_info["file"]["url_private_download"]
    r = run(["wget", f"{url}", "-P", "./files/"])



@app.event("message")
def handle_message():
    pass


from flask import Flask, request

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)
cursor = start_eva_server()


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)