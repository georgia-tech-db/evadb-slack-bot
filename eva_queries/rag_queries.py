import evadb
import pandas as pd

def build_relevant_knowledge_body(cursor, user_query, say):
    query = f"""SELECT * FROM MyPDFs 
                ORDER BY Similarity(
                        SentenceFeatureExtractor("{user_query}"), 
                        SentenceFeatureExtractor(data)) LIMIT 10;"""
    response = cursor.query(query).df()
    if type(response)==type(pd.DataFrame):
        # DataFrame response to single string
        knowledge_body = response["mypdfs.paragraph"].str.cat(sep='; ')
        print(knowledge_body)
        return knowledge_body
    else:
        say("Table not initialized")

def rag_query(knowledge_body, query):
    conversation = [
        {
            "role": "system", "context": f"{knowledge_body}"
        },
        {
            "role": "user", "context": f"{query}"
        },
    ]
    return conversation