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
import os
import openai

from subprocess import run

from slack import WebClient
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from eva_queries.rag_queries import (
    build_relevant_knowledge_body,
    build_rag_query,
    build_search_index,
)
from utils.formatted_messages.welcome import MSG as WELCOME_MSG

import evadb


SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Set OpenAI key.
openai.api_key = OPENAI_API_KEY

# Slack app, bot, and client.
app = App(token=SLACK_BOT_TOKEN)
handler = SlackRequestHandler(app)
client = WebClient(token=SLACK_BOT_TOKEN)

# Cursor of EvaDB.
cursor = evadb.connect().cursor()


# Logging.
@app.middleware
def log_request(logger, body, next):
    # Intercept and log everything.
    logger.debug(body)
    return next()


# Handle in app mention.
@app.event("app_mention")
def handle_mention(body, say, logger):
    # Convert message body to message and eva query.
    message_body = str(body["event"]["text"]).split(">")[1]
    logger.info(f"msg body: {message_body}")

    message_queries = message_body.split("%Q")

    if len(message_queries) > 1:
        # Eva query.
        eva_query = message_queries[1]
        logger.info(f"eva query: {eva_query}")
    else:
        # User query.
        user_query = message_queries[0].strip()
        logger.info(f"user query: {user_query}")

        if user_query:
            knowledge_body = build_relevant_knowledge_body(cursor, user_query, logger)
            conversation = build_rag_query(knowledge_body, user_query)

            if knowledge_body is not None:
                # Only reply when there is knowledge body.
                openai_response = (
                    openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=conversation,
                    )
                    .choices[0]
                    .message.content
                )
                say(openai_response + WELCOME_MSG)
            else:
                say("Sorry, we didn't find relevant sources for this question.")
        else:
            say("Please try again with a valid question.")


# Handle in app file sharing.
@app.event("file_shared")
def handle_file_sharing(body, say, logger):
    file_id = str(body["event"]["file_id"])
    logger.info(f"file id: {file_id}")
    say(f"Downloading this file ... Please wait.")

    file_info = client.files_info(file=file_id)
    url = file_info["file"]["url_private_download"]
    logger.info(f"file url: {url}")

    run(["wget", f"{url}", "-P", "./files/"])


# Handle direct message.
@app.event("message")
def handle_message():
    pass


#########################################################
# Flask server                                          #
#########################################################
from flask import Flask, request

flask_app = Flask(__name__)


def run_server():
    build_search_index(cursor)
    flask_app.run(debug=True, use_reloader=False, host="0.0.0.0", port=12345)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


if __name__ == "__main__":
    run_server()
