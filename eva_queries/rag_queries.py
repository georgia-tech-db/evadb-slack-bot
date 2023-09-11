import evadb
import pandas as pd


def build_search_index(cursor):
    cursor.query(
        """
        CREATE FUNCTION IF NOT EXISTS SentenceFeatureExtractor
        IMPL './utils/sentence_feature_extractor.py'
    """
    ).df()

    table_list = cursor.query("""SHOW TABLES""").df()["name"].tolist()

    if "OMSCSDocPDF" not in table_list:
        cursor.query("""LOAD PDF 'omscs_doc.pdf' INTO OMSCSDocPDF""").df()
        cursor.query(
            """CREATE INDEX IF NOT EXISTS OMSCSDocPDFIndex 
            ON OMSCSDocPDF (SentenceFeatureExtractor(data))
            USING FAISS
        """
        ).df()


def build_relevant_knowledge_body(cursor, user_query, logger):
    query = f"""
        SELECT * FROM OMSCSDocPDF
        ORDER BY Similarity(
            SentenceFeatureExtractor('{user_query}'), 
            SentenceFeatureExtractor(data)
        ) LIMIT 10
    """

    try:
        response = cursor.query(query).df()
        # DataFrame response to single string.
        knowledge_body = response["omscsdocpdf.data"].str.cat(sep="; ")
        return knowledge_body
    except Exception as e:
        logger.error(str(e))
        return None


def build_rag_query(knowledge_body, query):
    conversation = [
        {
            "role": "system",
            "content": f"""You will be provided with a document delimited by semicolons
             and a question. Your task is to answer the question using only the provided document. 
             If the document does not contain the information needed to answer this question then 
             simply write: 'Sorry, we didn't find relevant sources for this question.'""",
        },
        {"role": "user", "content": f"""{knowledge_body}"""},
        {"role": "user", "content": f"{query}"},
    ]
    return conversation
