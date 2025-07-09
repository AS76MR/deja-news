from flask import Flask, request, jsonify
import numpy as np
import faiss
from typing import List, Tuple, Dict
import threading


app = Flask(__name__)

FAISS_INDICES: Dict[str, faiss.Index] = {}
INDEX_LOCKS: Dict[str, threading.Lock] = {}

def validate_vector(vector, expected_dim):
    """Validate input vector format and dimensions"""
    return True
    return (
        isinstance(vector, list) and
        len(vector) == expected_dim and
        all(isinstance(x, (float, int)) for x in vector)
    )

def get_index_lock(index_name) :
    """Get or create a thread lock for an index"""
    if index_name not in INDEX_LOCKS:
        INDEX_LOCKS[index_name] = threading.Lock()
    return INDEX_LOCKS[index_name]



def get_pq_code(index, vector_id):
    """Retrieve PQ code for a specific vector ID, handling different index structures"""
    ivf = faiss.downcast_index(index.index)

    #ivf=faiss.swigfaiss_avx512.IndexIVFPQ.cast(index)
    invlists = ivf.invlists
    pq = ivf.pq
    nlist = invlists.nlist

    for list_id in range(nlist):
        list_size = invlists.list_size(list_id)
        if list_size == 0:
            continue

        ids_ptr = faiss.rev_swig_ptr(invlists.get_ids(list_id), list_size)
        codes_ptr = faiss.rev_swig_ptr(invlists.get_codes(list_id), list_size * pq.code_size)

        for i in range(list_size):
            if ids_ptr[i] == vector_id:
                start = i * pq.code_size
                end = start + pq.code_size
                pq_code = codes_ptr[start:end]
                return pq_code  # returns a numpy array of uint8

    raise ValueError(f"Vector ID {vector_id} not found in any inverted list.")





@app.route('/add_vector', methods=['POST'])
def add_vector():
    """Add new vectors to an existing index"""
    try:
        data = request.json
        index_name = data['index_name']
        partition_id = data['partition_id']
        vector = data['vector']  
        vector = np.array(vector["data"], dtype=vector["dtype"]).reshape(vector["shape"])
        vector_id = data.get('id')
        vector_ids = [vector_id] 

        print ('vector.shape')
        print (vector.shape)

        index_name = index_name + str(partition_id)
        vector=vector.squeeze()
        vectors=[vector]
        print ('vector.shape')
        print (vector.shape)

        
        # Validate index exists
        if index_name not in FAISS_INDICES:
            return jsonify({"error": f"Index '{index_name}' not loaded"}), 404
            
        index = FAISS_INDICES[index_name]
        expected_dim = index.d
        
        # Validate input vectors
        for i, vector in enumerate(vectors):
            if not validate_vector(vector, expected_dim):
                print (type(vector))
                print (len(vector))
                print (expected_dim)

                return jsonify({
                    "error": f"Vector {i} has invalid format or dimension",
                    "expected_dimension": expected_dim
                }), 400
        
        # Convert to numpy array
        new_vectors = np.array(vectors, dtype='float32')
        
        # Validate IDs if provided
        if vector_ids:
            if len(vector_ids) != len(vectors):
                return jsonify({"error": "Incorrect number of ids"}), 404
        
        # Validate index exists
        if index_name not in FAISS_INDICES:
            return jsonify({"error": f"Index '{index_name}' not loaded"}), 404
            
        index = FAISS_INDICES[index_name]
        expected_dim = index.d
        
        # Validate input vectors
        for i, vector in enumerate(vectors):
            if not validate_vector(vector, expected_dim):
                print (type(vector))
                print (len(vector))

                return jsonify({
                    "error": f"Vector {i} has invalid format or dimension",
                    "expected_dimension": expected_dim
                }), 400
        
        # Convert to numpy array
        new_vectors = np.array(vectors, dtype='float32')
        
        
        with get_index_lock(index_name):
            try:
                # Add vectors to index
                    # Convert IDs to int64 array
                ids_array = np.array(vector_ids, dtype='int64')
                index.add_with_ids(new_vectors, ids_array)

                pqcode = get_pq_code(index, vector_id)


                
                print ('returning sucessfully')    
                return jsonify({
                    "status": "success",
                    "index_name": index_name,
                    "added_vectors": len(vectors),
                    "total_vectors": index.ntotal,
                    "pqcode": pqcode
                })
            
            except RuntimeError as e:
                return jsonify({"error": f"FAISS operation failed: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/load_index', methods=['POST'])
def load_index():
    """Load a FAISS index into memory"""
    try:
        data = request.json
        partition_id = data['partition_id']
        index_name = data['index_name']
        index_path =  f"/efs/tmp/{index_name}_part_{partition_id}.faiss"
        index_id = index_name+str(partition_id)
 
        index = faiss.read_index(index_path)
        
        FAISS_INDICES[index_id] = index
        
        return jsonify({
            "status": "success",
            "index_name": index_name,
            "dimension": index.d,
            "vectors_count": index.ntotal
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/search', methods=['POST'])
def search():
    """Search for nearest neighbors in specified index"""
    try:
        data = request.json
        index_name = data['index_name']
        partition_id = data['partition_id']
        vector = data['vector']  
        vector = np.array(vector["data"], dtype=vector["dtype"]).reshape(vector["shape"])

        k = data.get('k', 100)       # Number of neighbors

        index_name = index_name + str (partition_id)
        # Validate index exists
        if index_name not in FAISS_INDICES:
            return jsonify({"error": f"Index '{index_name}' not loaded"}), 404
            
        index = FAISS_INDICES[index_name]
        expected_dim = index.d
        
        # Validate input vectors
        if not validate_vector(vector, expected_dim):
            return jsonify({
                "error": f"Vector {i} has invalid format or dimension",
                "expected_dimension": expected_dim
            }), 400
        
        # Convert to numpy array
        query_vector = np.array(vector, dtype='float32')
        
        # Perform search
        print (index)
        print (query_vector)
        print (k)
        distances, indices = index.search(query_vector, k)
        
        # Format results
        results = []
        for i in range(len(vectors)):
            results.append({
                "query_id": i,
                "neighbors": [
                    {"id": int(indices[i][j]), "distance": float(distances[i][j])}
                    for j in range(k)
                ]
            })
        
        return jsonify({
            "index": index_name,
            "results": results
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/indices', methods=['GET'])
def list_indices():
    """List all loaded indices"""
    return jsonify({
        "loaded_indices": list(FAISS_INDICES.keys()),
        "count": len(FAISS_INDICES)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
