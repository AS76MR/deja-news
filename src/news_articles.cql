 CREATE KEYSPACE news WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};


CREATE TABLE news.articles (     hour_bucket INT,         article_id BIGINT,     timestamp TIMESTAMP,      original_text TEXT,        fact_text TEXT,            entities LIST<TEXT>,         embedding VECTOR<FLOAT, 384>, pq_blob BLOB,       PRIMARY KEY ((hour_bucket), article_id) ) WITH CLUSTERING ORDER BY (article_id  DESC)  ;

