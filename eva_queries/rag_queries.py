import evadb
import pandas as pd

def build_relevant_knowledge_body(cursor, user_query, say):
    query = f"""SELECT * FROM MyPDFs 
                ORDER BY Similarity(
                        SentenceFeatureExtractor('{user_query}'), 
                        SentenceFeatureExtractor(data)
                        ) LIMIT 10;"""
    response = cursor.query(query).df()
    
    if type(response)==pd.DataFrame:
        # DataFrame response to single string
        knowledge_body = response["mypdfs.data"].str.cat(sep='; ')
        
        return knowledge_body
    else:
        say("EvaDB not initialized")
        return -1

def rag_query(knowledge_body, query):
    conversation = [
        {
            "role": "system", "content": f"""You will be provided with a document delimited by semicolons
             and a question. Your task is to answer the question using only the provided document. 
             If the document does not contain the information needed to answer this question then simply write: "Did not find this in the documents provided." """
        },
        {
            "role": "user", "content": f"""{knowledge_body}"""
        },
        {
            "role": "user", "content": f"{query}"
        },
    ]
    return conversation