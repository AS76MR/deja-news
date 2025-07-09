import requests
import numpy as np
import json
import time
from sys import exit

class FaissClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
    
    def load_index(self, partition_id , index_name) :
        """Load a FAISS index into server memory"""
        payload = { 
            "partition_id": partition_id,
            "index_name": index_name
        }
        response = requests.post(
            f"{self.base_url}/load_index",
            headers=self.headers,
            data=json.dumps(payload)
        )
        return self._handle_response(response)
    
    def add_vector(self, index_name, partition_id ,  vector, composite_id) :
        """
        Add vectors to an existing index
        :param vectors: List of lists (each inner list is a vector)
        :param ids: Optional list of integer IDs
        """
        payload = {
            "index_name": index_name,
            "partition_id": partition_id,
            "vector": vector,
            "id" : composite_id
        }

        response = requests.post(
            f"{self.base_url}/add_vector",
            headers=self.headers,
            data=json.dumps(payload))
        return self._handle_response(response)
    
    def search(self, index_name, partition_id ,  query_vector, k) :
        """
        Search for nearest neighbors
        :param query_vectors: List of query vectors
        :param k: Number of neighbors to return
        """
        payload = {
            "index_name": index_name,
            "partition_id" : partition_id,
            "vector": query_vector,
            "k": k
        }
        response = requests.post(
            f"{self.base_url}/search",
            headers=self.headers,
            data=json.dumps(payload))
        return self._handle_response(response)
    
    def save_index(self, index_name, output_path) :
        """Save in-memory index to disk"""
        payload = {
            "index_name": index_name,
            "output_path": output_path
        }
        response = requests.post(
            f"{self.base_url}/save_index",
            headers=self.headers,
            data=json.dumps(payload))
        return self._handle_response(response)
    
    def list_indices(self) :
        """List all loaded indices"""
        response = requests.get(f"{self.base_url}/indices")
        return self._handle_response(response)
    
    def index_stats(self, index_name) :
        """Get statistics for a specific index"""
        response = requests.get(f"{self.base_url}/index_stats/{index_name}")
        return self._handle_response(response)
    
    def _handle_response(self, response):
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP Error: {err}")
            print(f"Response content: {response.text}")
            return None
        except json.JSONDecodeError:
            print("Failed to parse JSON response")
            return None

