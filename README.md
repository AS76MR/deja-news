# deja-news
# Déjà-News: Scalable News Deduplication and Semantic Similarity Detection

**Déjà-News** is a high-performance system that determines whether a newly published news item has already been reported — even if phrased differently. Instead of relying solely on keyword or title overlap, it uses semantic embeddings, approximate nearest-neighbor search, and entailment logic to robustly detect redundant or stale news.

---

## 🚀 Why Not Just Cosine Similarity?

Cosine similarity between embeddings is a good filter, but it's not sufficient alone. Here are the key limitations:

1. **High-dimensional embeddings** are needed to capture meaning well, but these are memory-intensive and computationally expensive to search directly.
2. Cosine similarity can be **misleadingly high** between semantically opposite sentences:
   - _“I am going to New York tomorrow.”_ vs. _“I am **not** going to New York tomorrow.”_
   -  _“**Jack** gave the book to **Jill**.”_ vs. _“**Jill** gave the book to **Jack**.”_
3. It can be **misleadingly low** when the same news is reported with differing commentary or subjective language.
4. Cosine similarity may be **spuriously high** for distinct but similar incidents (e.g., _truck collides with school bus in City A_ vs. _in City B_).

---

## ⚙️ How Déjà-News Works

This system is designed for **low latency**, **high throughput**, and **horizontal scalability** using commodity hardware.

### ✅ Core Steps:

1. **Preprocessing & Indexing**
   - Compute embeddings using `text-embedding-3-small` from OpenAI.
   - Extract important named entities using `dbmdz/bert-large-cased-finetuned-conll03-english`.
   - Precompute **Product Quantization (PQ) codes** using a trained FAISS IVFPQ index.
   - Store all metadata in **Cassandra** (text, embeddings, PQ codes, named entities).

2. **Distributed Search**
   - FAISS indexes are **partitioned and cached in RAM** using Flask servers.
   - PQ codes require far less memory than full embeddings, making caching feasible.
   - **Apache Spark** orchestrates a distributed search to retrieve the nearest `N` neighbors efficiently.

3. **Candidate Filtering**
   - For each neighbor:
     - **Subjectivity filtering**: Remove quoted text and discard sentences with `TextBlob` subjectivity ≥ 0.9.
     - **Cosine similarity** is computed only on cleaned text.
     - If similarity is above threshold:
       - Named entities are compared.
       - If entity overlap exists, use **Sentence Transformers (SBERT)** to test for **entailment or contradiction**.

4. **Early Termination**
   - If a matching article is entailed by the new news item, a **termination flag** is set on a shared file system.
   - Other workers can check this flag and **abort their search early** to save resources.
---

## 🛠 Tech Stack

| Component     | Tool/Library |
|---------------|--------------|
| Embeddings    | OpenAI `text-embedding-3-small` |
| ANN Search    | FAISS IVFPQ |
| Named Entities| `dbmdz/bert-large-cased-finetuned-conll03-english` |
| Entailment    | Sentence Transformers (SBERT) |
| Subjectivity  | TextBlob |
| Storage       | Cassandra |
| Distributed   | Apache Spark |
| Caching Layer | Flask Servers |
| Sync Mechanism| Shared NFS (to be replaced with distributed key-value store) |

---

## 🧪 Design Considerations

- **Scalability**: Designed to scale horizontally across machines using Spark and lightweight Flask servers.
- **Performance**: Precomputing and caching PQ codes enables fast search, even over large datasets.
- **Extensibility**: Easily configurable to:
  - Use different embedding models
  - Swap out named entity extractors
  - use a more efficient protocal instead of JSON if the number of neighbours searched in every partition is very large
  - Integrate a more robust coordination backend (e.g., Redis, etcd)

---

## ⚠️ Notes

- This repository **focuses on algorithmic and architectural design**.
- It **skips deployment code, error handling**, and **logging**, except where failure likelihood is high or critical for performance.
- Designed for use in **research, prototyping, or private deployments**. Production use would require enhancements in security, monitoring, and system resilience.

---


---

## 📜 License

[MIT License](LICENSE)

---

## 👤 Author
https://github.com/AS76MR

