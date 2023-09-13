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
import time
import random

from math import ceil
from subprocess import run

from slack import WebClient
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from eva_queries.rag_queries import (
    build_relevant_knowledge_body,
    build_rag_query,
    build_search_index,
    start_llm_backend,
)
from utils.formatted_messages.welcome import MSG as WELCOME_MSG
from utils.formatted_messages.wait import MSG as WAIT_MSG
from utils.formatted_messages.busy import MSG as BUSY_MSG
from utils.formatted_messages.reference import MSG_HEADER as REF_MSG_HEADER
from utils.usage_tracker import time_tracker

import evadb


SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")


# Slack app, bot, and client.
app = App(token=SLACK_BOT_TOKEN)
handler = SlackRequestHandler(app)
client = WebClient(token=SLACK_BOT_TOKEN)

# Queue list to connect to backend.
queue_list = start_llm_backend(2)

# Cursor of EvaDB.
cursor = evadb.connect().cursor()
build_search_index(cursor)


#########################################################
# Helper functions                                      #
#########################################################
def queue_backend_llm(conversation):
    for iq, oq in queue_list:
        if iq.full():
            continue
        else:
            iq.put(conversation)
            return oq.get()
    return None


def is_all_queue_full():
    for iq, _ in queue_list:
        if not iq.full():
            return False
    return True


#########################################################
# Slack handler                                         #
#########################################################
# Logging.
@app.middleware
def log_request(logger, body, next):
    # Intercept and log everything.
    logger.debug(body)
    return next()


# Handle in app mention.
@app.event("app_mention")
def handle_mention(body, say, logger):
    # Thread id to reply.
    thread_ts = body["event"].get("thread_ts", None) or body["event"]["ts"]

    # Check if users ask question too soon.
    user = body["event"]["user"]
    cooldown_time = time.time() - time_tracker[user]
    if cooldown_time < 300:
        say(WAIT_MSG.format(ceil((5 - cooldown_time / 60))), thread_ts=thread_ts)
        return
    else:
        time_tracker[user] = time.time()

    # Abort early, if all queues are full.
    if is_all_queue_full():
        print("Pre-abort: all queues are full")
        say(BUSY_MSG, thread_ts=thread_ts)
        return

    # Convert message body to message and eva query.
    message_body = str(body["event"]["text"]).split(">")[1]
    print(f"msg body: {message_body}")

    message_queries = message_body.split("%Q")

    if len(message_queries) > 1:
        # Eva query.
        eva_query = message_queries[1]
        print(f"eva query: {eva_query}")
    else:
        # User query.
        user_query = message_queries[0].strip()
        print(f"user query: {user_query}")

        if user_query:
            knowledge_body, reference_pageno_list = build_relevant_knowledge_body(
                cursor, user_query, logger
            )
            conversation = build_rag_query(knowledge_body, user_query)

            if knowledge_body is not None:
                # Only reply when there is knowledge body.
                response = queue_backend_llm(conversation)
                if response is None:
                    print("Post-abort: all queues are full")
                    say(BUSY_MSG, thread_ts=thread_ts)
                    return

                if response == "I dont know":
                    response = (
                        "Sorry, we didn't find relevant sources for this question."
                    )

                # Attach reference
                response += REF_MSG_HEADER
                for i, pageno in enumerate(reference_pageno_list):
                    response += f"<https://omscs.gatech.edu/sites/default/files/documents/Other_docs/fall_2023_orientation_document.pdf#page={pageno}|[page {pageno}]> "
                response += "\n"

                # Reply back with welcome msg randomly.
                if random.random() < 0.1:
                    response += WELCOME_MSG

                say(response, thread_ts=thread_ts)
            else:
                say(
                    "Sorry, we didn't find relevant sources for this question.",
                    thread_ts=thread_ts,
                )
        else:
            say("Please try again with a valid question.", thread_ts=thread_ts)


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


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)
