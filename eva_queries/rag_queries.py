import os
import openai

from gpt4all import GPT4All
from pdfdocument.document import PDFDocument
import evadb

import ray
import pandas as pd
import os

def build_search_index(cursor, doc_name):
    cursor.query(
        """
        CREATE FUNCTION IF NOT EXISTS SentenceFeatureExtractor
        IMPL './utils/sentence_feature_extractor.py'
    """
    ).df()

    cursor.query("""LOAD PDF '""" + doc_name + """' INTO OMSCSPDFTable""").df()
    cursor.query(
        """CREATE INDEX IF NOT EXISTS OMSCSIndex 
        ON OMSCSPDFTable (SentenceFeatureExtractor(data))
        USING FAISS
    """
    ).df()


def build_slack_dump_search_index(cursor):
    if ("slack_dump" in os.listdir(".")):
        path = "./slack_dump/"
        files = os.listdir(path)
        df = pd.DataFrame()
        if (len(files) == 0):
            return False

        pdf = PDFDocument("SlackDump.pdf")
        pdf.init_report()
        for file in files:
            if file.endswith(".json"):
                df1 = pd.read_json(path + file)
                df = pd.concat([df, df1[df1.columns.intersection(set(['client_msg_id', 'type', 'user', 'text', 'ts']))]])
                pdf.p(df.to_csv(index=False))
        pdf.generate()
        build_search_index(cursor, "SlackDump.pdf")


def build_relevant_knowledge_body_pdf(cursor, user_query, logger):
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
        knowledge_body = response["omscspdftable.data"].str.cat(sep="; ")
        referece_pageno_list = set(response["omscspdftable.page"].tolist()[:3])
        reference_pdf_name = response["omscspdftable.name"].tolist()[0]
        return knowledge_body, reference_pdf_name, referece_pageno_list
    except Exception as e:
        logger.error(str(e))
        return None, None


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
