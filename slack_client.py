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

from evadb.server.command_handler import execute_query_fetch_all
from test.util import get_evadb_for_testing

from evadb.configuration.configuration_manager import ConfigurationManager

# from evadb.configuration.configuration_manager import ConfigurationManager

SLACK_BOT_TOKEN = ConfigurationManager().get_value("third_party", "SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = ConfigurationManager().get_value("third_party", "SLACK_APP_TOKEN")
OPENAI_API_KEY = ConfigurationManager().get_value("third_party", "OPENAI_KEY")

app = App(token=SLACK_BOT_TOKEN)
evadb = None
client = WebClient(token=SLACK_BOT_TOKEN)


# Starts and initializes Eva Server
def start_eva_server():
    global evadb
    evadb = get_evadb_for_testing()
    evadb.catalog().reset()


@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()


@app.event("app_mention")
def event_test(body, say, logger):
    # logger.info(body)

    message_body = str(body["event"]["text"]).split(">")[1]
    message_text = message_body.split("%Q")[0]
    query = message_body.split("%Q")[1]

    openai_response = None

    print("\n\n\n\n")
    print(message_body, message_text,"query =", query, end="\n\n\n\n")

    # if message_body.strip():
    #     print("\nopenai\n\n",)
    #     openai.api_key = OPENAI_API_KEY
    #     openai_response = (
    #         openai.Completion.create(
    #             engine="text-davinci-003",
    #             prompt=message_text,
    #             max_tokens=1024,
    #             n=1,
    #             stop=None,
    #             temperature=0.5,
    #         )
    #         .choices[0]
    #         .text
    #     )

    sql_response = None

    if query.strip():
        print("\nsql\n\n", )
        try:
            sql_response = execute_query_fetch_all(evadb, query)
        except Exception as e:
            sql_response = f"caught error: {e}"

    response = ""
    if openai_response:
        response = openai_response
    if sql_response:
        response = response + "\n" + sql_response.frames.to_string()
    
    # Use Tabluate in python
    say(f'text: "{message_text}" & query: "{query}":\n{response}')


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
start_eva_server()


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)