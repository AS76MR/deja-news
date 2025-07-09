import faiss
from cassandra_utils import get_embeddings
import numpy as np
from flask_client import FaissClient

def search_index(index_name,partition_id ,  query_vec, k):

    use_cache=True


    embedding = query_vec
    if use_cache:
        client = FaissClient() 

        emb_serializable = {
        "shape": embedding.shape,
        "dtype": str(embedding.dtype),
        "data": embedding.tolist()
        }

        distances_pq, indices_pq = client.search(index_name ,partition_id , emb_serializable,  k)  
    else:
        local_shard_filename = f"/efs/tmp/{index_name}_part_{partition_id}.faiss"
        index= faiss.read_index ( local_shard_filename)
        distances_pq, indices_pq = index.search( embedding,  k)  


    candidate_embeddings , candidate_ids , candidate_text = get_embeddings(indices_pq[0],'embedding')

    query_norm = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
    candidate_norms = candidate_embeddings / np.linalg.norm(candidate_embeddings, axis=1, keepdims=True)
    cosine_sims = np.dot(candidate_norms, query_norm.T).squeeze()  # shape: (k,)

    sorted_idx = np.argsort(-cosine_sims)
    sorted_indices = [candidate_embeddings[i] for i in sorted_idx]
    sorted_ids = [candidate_ids[i] for i in sorted_idx]
    sorted_similarities = [cosine_sims[i] for i in sorted_idx]
    return sorted_idx , sorted_indices , sorted_similarities  , sorted_ids



