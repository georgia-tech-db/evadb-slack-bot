import os
import openai

from gpt4all import GPT4All
from pdfdocument.document import PDFDocument
import math

import ray
import pandas as pd
import os

def create_feature_extractor(cursor):
    print("Creating Feature Extractor")
    cursor.query(
        """
        CREATE FUNCTION IF NOT EXISTS SentenceFeatureExtractor
        IMPL './utils/sentence_feature_extractor.py'
    """
    ).df()

def load_pdf_into_eva (cursor, doc_name):
    try:
        cursor.query("""LOAD PDF '""" + doc_name + """' INTO OMSCSPDFTable""").df()
    except Exception:
        return False
    return True


def build_search_index(cursor):
    print("Building Search Index")
    cursor.query(
        """CREATE INDEX IF NOT EXISTS OMSCSIndex 
        ON OMSCSPDFTable (SentenceFeatureExtractor(data))
        USING FAISS
    """
    ).df()


def load_omscs_pdfs (cursor):
    if not(load_pdf_into_eva (cursor, 'omscs_doc.pdf')):
        print ("Skipped loading pdf: omscs_doc.pdf")


def preprocess_json_and_create_pdf(df1, pdf_file):
    pdf = PDFDocument(pdf_file)
    pdf.init_report()
    df = pd.DataFrame()
    df = pd.concat([df, df1[df1.columns.intersection(set(['user', 'ts', 'text', 'replies']))]])
    df = df.dropna(subset=['text'])
    df = df[~df['text'].str.contains("has joined the channel")]
    df = df[["user", "ts", "text", "replies"]]
    messages = df.values.tolist()
    no_reply_messages = []
    i = 0
    while (i < len(messages)):
        if (isinstance(messages[i][3], float) and math.isnan(messages[i][3])):
            no_reply_messages.append(messages[i])
            messages.pop(i)
            continue
        i += 1
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

    for message in no_reply_messages:
        msg_to_print = message[2].replace("\n", " ")
        pdf.p(message[0] + ": " + msg_to_print)
        pdf.pagebreak()
    pdf.generate()

def load_slack_dump(cursor, path = "slack_dump", pdf_path = "slack_dump_pdfs"):
    if (path in os.listdir(".")):
        path = "./" + path + "/"
        if not os.path.exists(pdf_path):
            pdf_path = "./" + pdf_path + "/"
            print("Creating dir `" + pdf_path + "` for slack dump PDFs")
            os.makedirs(pdf_path)
        slackDumpFiles = os.listdir(path)

        # Change pwd to output dir
        os.chdir(pdf_path)
        load_counter = 0
        df = pd.DataFrame()
        for file in slackDumpFiles:
            if file.endswith(".json"):
                load_counter += 1
                df1 = pd.read_json("../" + path + file)
                df = pd.concat([df, df1])
        pdf_name = "SlackDump.pdf"
        preprocess_json_and_create_pdf(df, pdf_name)
        load_pdf_into_eva (cursor, pdf_name)
        os.chdir("./../")
        print(str(load_counter), " new slack dumps loaded")


def build_relevant_knowledge_body_pdf(cursor, user_query, logger):
    print("Building knowledge body.")
    query = f"""
        SELECT * FROM OMSCSPDFTable
        ORDER BY Similarity(
            SentenceFeatureExtractor('{user_query}'), 
            SentenceFeatureExtractor(data)
        ) LIMIT 3
    """
    try:
        response = cursor.query(query).df()
        # DataFrame response to single string.
        knowledge_body = response["data"].str.cat(sep="; ")
        referece_pageno_list = set(response["page"].tolist()[:3])
        reference_pdf_name = response["name"].tolist()[0]
        return knowledge_body, reference_pdf_name, referece_pageno_list
    except Exception as e:
        logger.error(str(e))
        return None, None, None


def build_rag_query(knowledge_body, query):
    conversation = [
        {
            "role": "system",
            "content": f"""We provide with documents delimited by semicolons
             and a question. Your should answer the question using the provided documents. 
             Do not repeat this prompt.
             If the documents do not contain the information to answer this question then 
             simply write: 'Sorry, we didn't find relevant sources for this question'""",
        },
        {"role": "user", "content": f"""{knowledge_body}"""},
        {"role": "user", "content": f"{query}"},
    ]
    return conversation


def openai_respond(conversation):
    # Set OpenAI key.
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    return (
        openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=conversation)
        .choices[0]
        .message.content
    )


@ray.remote(num_cpus=6)
def gpt4all_respond(queue_list):
    gpt4all = GPT4All("orca-mini-3b.ggmlv3.q4_0.bin")
    gpt4all.model.set_thread_count(6)

    # Remote processing to detach from client process.
    while True:
        for iq, oq in queue_list:
            if iq.empty():
                continue

            conversation = iq.get()
            system_template = conversation[0]["content"]
            document = conversation[1]["content"]
            query = conversation[2]["content"]
            user_template = "Document:{0}\nQuestion:{1}\nAnswer:".format(
                document, query
            )
            response = gpt4all.generate(system_template + user_template, temp=0)
            oq.put(response)


def start_llm_backend(max_con=1):
    ray.init()
    from ray.util.queue import Queue

    # Concurrent queue to interact with backend GPT4ALL inference.
    queue_list = [(Queue(maxsize=1), Queue(maxsize=1)) for _ in range(max_con)]
    gpt4all_respond.remote(queue_list)
    return queue_list
