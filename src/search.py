from termination import check_termination_flag , set_termination_flag
from dist_utils import search_index
import numpy as np
from cassandra_utils import get_embeddings
from ine import important_named_entities





def search_partition(partition_id,index_name , query_vec,k , shard_ids):
    return search_index(index_name,partition_id ,  query_vec, k)


def search_news(news_id , i,broadcasted_query,k_nearest_neighbours,ine,text,broadcasted_config):
    embedding=broadcasted_query.value
    config=broadcasted_config.value

    termination_flag_path=config['termination_flag_path']



    if check_termination_flag(termination_flag_path,news_id):
        print ('aborting')
        return None

    sorted_idx_inc , sorted_indices_inc , sorted_similarities_inc , sorted_ids = search_partition(i, 'IndexIVFPQ' , embedding.astype(np.float32),k_nearest_neighbours , [])
#        print (i,sorted_idx_inc , sorted_indices_inc , sorted_similarities_inc , sorted_ids)


    emb_array , id_array , text_array = get_embeddings (sorted_ids  , embedding_type = 'embedding')

    query_norm = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
    candidate_norms = emb_array / np.linalg.norm(emb_array, axis=1, keepdims=True)
    cosine_sims = np.dot(candidate_norms, query_norm.T).squeeze()  # shape: (k,)

    for i in range(len(cosine_sims)):
        if cosine_sims[i] > 0.75:
            candidate_ine = important_named_entities(text_array[i])
            if set(candidate_ine) & set(ine):
                if not check_contradiction(text_array[i],text):
                    print ("FOUND!!!!!!")
                    set_termination_flag(termination_flag_path,news_id)
                    print (text_array[i])
                    return text_array[i]


    print ("NOT FOUND!!!!!!")
    return None


