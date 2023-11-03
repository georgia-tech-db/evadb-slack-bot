from pdfdocument.document import PDFDocument
import math
import pandas as pd
import os
from eva_queries.rag_queries import load_pdf_into_eva

def clean_dataframe(orig_df):
    df = pd.DataFrame()
    df = pd.concat([df, orig_df[orig_df.columns.intersection(set(['user', 'ts', 'text', 'replies']))]])
    df = df.dropna(subset=['text'])
    df = df[~df['text'].str.contains("has joined the channel")]
    df = df[["user", "ts", "text", "replies"]]
    return df

def find_message_with_no_reply(df):
    messages = df.values.tolist()
    no_reply_messages = []
    i = 0
    while (i < len(messages)):
        if (isinstance(messages[i][3], float) and math.isnan(messages[i][3])):
            no_reply_messages.append(messages[i])
            messages.pop(i)
            continue
        i += 1
    return messages, no_reply_messages

def add_messages_with_reply_to_pdf(messages, no_reply_messages, pdf):
    for message in messages:
        msg_to_print = message[2].replace("\n", " ")
        pdf.p(message[0] + ": " + msg_to_print)
        for reply in message[3]:
            i = 0
            while i < len(no_reply_messages):
                if no_reply_messages[i][0] == reply['user'] and str(no_reply_messages[i][1]) == reply['ts']:
                    msg_to_print = no_reply_messages[i][2].replace("\n", " ")
                    pdf.p("\u2022" + no_reply_messages[i][0] + ": " + msg_to_print)
                    no_reply_messages.pop(i)
                    continue
                i += 1
        pdf.pagebreak()
    return pdf

def preprocess_json_and_create_pdf(df1, pdf_file):
    pdf = PDFDocument(pdf_file)
    pdf.init_report()
    
    df = clean_dataframe(df1)
    
    messages, no_reply_messages = find_message_with_no_reply(df)
    
    pdf = add_messages_with_reply_to_pdf(messages, no_reply_messages, pdf)

    for message in no_reply_messages:
        msg_to_print = message[2].replace("\n", " ")
        pdf.p(message[0] + ": " + msg_to_print)
        pdf.pagebreak()
    pdf.generate()

def load_slack_dump(cursor, path = "slack_dump", pdf_path = "assets", workspace_name = "", channel_name = ""):
    print("Loading slack dump")
    if (path in os.listdir(".")):
        path = "./" + path + "/"
        dirs = os.listdir(path)
        # if ((workspace_name + "___" + channel_name) in dirs):
        if ((channel_name) in dirs):
            # full_path = path + workspace_name + "___" + channel_name + "/"
            full_path = path + channel_name + "/"
            slackDumpFiles = os.listdir(full_path)

            # Change pwd to output dir
            os.chdir(pdf_path)
            load_counter = 0
            df = pd.DataFrame()
            for file in slackDumpFiles:
                if file.endswith(".json"):
                    load_counter += 1
                    df1 = pd.read_json("../" + full_path + file)
                    df = pd.concat([df, df1])
            # pdf_name = workspace_name + "___" + channel_name + "___slackdump.pdf"
            pdf_name = channel_name + "___slackdump.pdf"
            preprocess_json_and_create_pdf(df, pdf_name)
            os.chdir("./../")
            load_pdf_into_eva (cursor, pdf_name)
            print(str(load_counter), " new slack dumps loaded")
            print("Finished loading slack dump")
        else:
            print("Could not find the correct slack dump dir.")
    else:
        print("Could not find the correct slack dump dir.")