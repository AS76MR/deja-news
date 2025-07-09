from cassandra.cluster import Cluster
from cassandra.query import PreparedStatement
import uuid
import datetime
from collections import defaultdict
from hour_article_ids import encode_id , decode_id
import numpy as np

cluster = Cluster(['127.0.0.1'])  
session = cluster.connect('news')  


def insert_row(hour_bucket , article_id  , timestamp, original_text, fact_text, named_entities , embedding , pq ):   
    
    insert_stmt = session.prepare('''
        INSERT INTO articles (hour_bucket, article_id, timestamp, original_text, fact_text, entities, embedding, pq_blob)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''')
    
    session.execute(insert_stmt, (hour_bucket, article_id, timestamp, original_text, fact_text, named_entities, embedding, pq))
    
    print(article_id , " insert done!")
   
def get_embeddings ( composite_ids , embedding_type = 'pq'):


    batch = session.prepare("""
        SELECT hour_bucket, article_id, embedding , pq_blob , original_text FROM articles
        WHERE hour_bucket = ? AND article_id IN ?
    """)

    queries = defaultdict(list)

    print ('composite_ids in get_embeddings ')
    print (composite_ids)
    for composite_id in composite_ids:
        #print ('composite_id')
        #print (composite_id)
        hb, aid = decode_id(composite_id)
        queries[hb].append(composite_id)

    emb_array=[]
    id_array=[]
    text_array=[]

    for hb, aids in queries.items():
        results = session.execute(batch, (hb, tuple(composite_ids)))
        for row in results:
            if embedding_type == 'pq': 
                emb_array.append (np.frombuffer(row[3], dtype=np.uint8))  #check if order is preserved
            elif embedding_type == 'embedding': 
                emb_array.append (row[2])  #check if order is preserved
            id_array.append (encode_id ( row[0],row[1]))  #check if order is preserved
            text_array.append (row[4])

    return emb_array , id_array , text_array



