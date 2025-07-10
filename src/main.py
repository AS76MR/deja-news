import yaml
from pyspark.sql import SparkSession
import openai
import numpy as np
from datetime import datetime

from ine import important_named_entities
from search import search_news
from flask_client import FaissClient
from preprocess import preprocess_text
from hour_article_ids import encode_id 
from cassandra_utils import insert_row

if __name__ == "__main__":

    spark = SparkSession.builder \
        .appName("DistributedNewsSimilaritySearch") \
        .master('local[4]') \
        .getOrCreate()

    spark.sparkContext.addPyFile("src/search.py")
    spark.sparkContext.addPyFile("src/termination.py")
    spark.sparkContext.addPyFile("src/dist_utils.py")
    spark.sparkContext.addPyFile("src/cassandra_utils.py")
    spark.sparkContext.addPyFile("src/hour_article_ids.py")
    spark.sparkContext.addPyFile("src/ine.py")
    spark.sparkContext.addPyFile("src/entailment.py")
    spark.sparkContext.addPyFile("src/flask_client.py")

    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)

    test_input_file = config["test_input"]["file"]
    news_id = config["test_input"]["news_id"]

    flask_client = FaissClient()
    num_partitions = config["num_partitions"]
    for m in range(num_partitions):
        load_result = flask_client.load_index(m,'IndexIVFPQ')

    with open(test_input_file, "r") as file:
        unp_text = file.read()

    text= preprocess_text(unp_text)


    ine=important_named_entities(text)

    OPENAI_API_KEY=config['openai_api_key']

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text )
    embedding = response.data[0].embedding

    embedding = np.array(embedding, dtype='float32')
    embedding = embedding.reshape(1, -1)



    broadcasted_query = spark.sparkContext.broadcast(embedding.astype(np.float32))
    broadcasted_config = spark.sparkContext.broadcast(config)


    k_nearest_neighbours = config["k_nearest_neighbours"]

    shard_ids_rdd = spark.sparkContext.parallelize(range(num_partitions), num_partitions)

    results = shard_ids_rdd.map(
        lambda part_id: search_news(news_id , part_id, broadcasted_query, k_nearest_neighbours, ine, text,broadcasted_config )
    ).filter(lambda x: x is not None).collect()


    #add new article to Cassandra table and IVFPQ index
    print ('embedding length')
    print (embedding.shape )


    emb_serializable = {
        "shape": embedding.shape,
        "dtype": str(embedding.dtype),
        "data": embedding.tolist()
        }



    now = datetime.now()
    hour_id = int(datetime.strftime(now,'%Y%m%d%H'))
    composite_id = int(encode_id (hour_id , news_id))
    index_name='IndexIVFPQ'
    partition_id = composite_id % num_partitions
    pqcode = flask_client.add_vector(index_name, partition_id ,  emb_serializable, composite_id)
    print (pqcode)
    insert_row(hour_id , composite_id , now, unp_text, text, ine  , embedding , pqcode  )




    spark.stop()



