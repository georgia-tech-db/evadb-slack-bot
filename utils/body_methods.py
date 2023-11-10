
from email import message


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

def match_reference_kb_message_df(kb, message_df):
    """
    This method returns the messages that are present in KB and sorts based on their size (in descending order).
    """
    def is_message_in_kb(msg):
        # We can use faster string matching algorithm here
        for i in kb:
            if msg in i:
                if len(msg)<10:
                    return False
                return True
        return False
    
    msdf = message_df[message_df.loc[:,'text'].apply(is_message_in_kb)]
    msdf['length'] = msdf.loc[:, "text"].apply(len)
    msdf = msdf.sort_values('length', ascending=False)
    
    return msdf
    

def generate_references(response, reference_pageno_list, reference_pdf_name,knowledge_body, message_df, channel_name):
    """
    Takes Knowledge body list and message_df to find message and there corresponding thread_ts
    gives links for omscs documents
    for courses documents links to omscentral
    """

    # Required for debugging
    # import pickle
    # pickle.dump(message_df, open("message_df.pkl", "wb"))
    # pickle.dump(knowledge_body, open("knowledge.pkl", "wb"))
    message_df = message_df.dropna()
    message_df = match_reference_kb_message_df(knowledge_body, message_df)
    message_df = message_df.reset_index()
    msg_count = 0

    for iterator, pageno in enumerate(reference_pageno_list):
        # TODO: change hardcoded url.
        if reference_pdf_name[iterator] == "assets/omscs_doc.pdf":
            response += f"<https://omscs.gatech.edu/sites/default/files/documents/Other_docs/fall_2023_orientation_document.pdf#page={pageno}|[OMSCS document, page {pageno}]> "
        elif reference_pdf_name[iterator] == "assets/coursesomscs_abb.pdf":
            response += f"<https://www.omscentral.com/ | [OMSCS Central]>"
        else:
            if msg_count>=len(message_df):
                continue
            response += f"<https://omscs-study.slack.com/archives/{channel_name}/p{str(message_df.loc[msg_count, 'ts']).replace('.', '')}|[slack message link {msg_count+1}]>"
            msg_count+=1
            
        # response += f"[{reference_pdf_name[iterator]}, page {pageno}] "
        response += "\n"
    return response