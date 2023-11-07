
def set_channel_value(body, new_channel_name):
    body['event']['channel'] = new_channel_name

def set_query_text(body, new_text):
    body['event']['text'] = new_text

def get_thread_ts(body):
    return body["event"].get("thread_ts", None) or body["event"]["ts"]

def get_event_id(body):
    return body["event_id"]

def get_user(body):
    return body["event"]["user"]

def get_workspace_name(body):
    return body['team_id']

def get_channel_name(body):
    return body['event']['channel']

def get_channel_pdf_name(body):
    channel_name = get_channel_name(body)
    return f"{channel_name}___slackdump.pdf"

def get_msg(body):
    return body["event"]["text"]

def get_split_msg(body):
    return str(get_msg(body)).split(">")[1]

def get_new_channel_name_and_user_query(body):
    msg = get_split_msg(body)
    if "--set-channel=" in msg:
        query = msg.split("--set-channel=")
        channel_name = query[1]
        user_query = query[0]
        return channel_name, user_query
    else:
        return False, msg


def generate_references(response, reference_pageno_list, reference_pdf_name,knowledge_body, message_df):
    """
    Takes Knowledge body list and message_df to find message and there corresponding thread_ts
    gives links for omscs documents
    for courses documents links to omscentral
    """

    for iterator, pageno in enumerate(reference_pageno_list):
        # TODO: change hardcoded url.
        # response += f"<https://omscs.gatech.edu/sites/default/files/documents/Other_docs/fall_2023_orientation_document.pdf#page={pageno}|[page {pageno}]> "
        response += f"[{reference_pdf_name[iterator]}, page {pageno}] "
    response += "\n"