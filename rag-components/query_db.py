import chromadb
from chromadb.api import ClientAPI
from sentence_transformers import CrossEncoder
from chromadb.utils import embedding_functions
import argparse


def _get_collection(client, collection_name: str):
    collection = client.get_collection(name=collection_name)
    embedding_model = collection.metadata["embedding_model"]

    collection = client.get_collection(
        name=collection_name,
        embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model, trust_remote_code=True
        ),
    )
    return collection


def initialize_db(database_path: str) -> ClientAPI:
    return chromadb.PersistentClient(path=database_path)


def query_db_interactive(
    query: str,
    database_path: str,
    collection_name: str,
    top_k: int = 5,
):
    client = initialize_db(database_path)
    return query_db(query, collection_name, top_k, client)


def query_db(
    query: str,
    collection_name: str,
    top_k: int = 5,
    client: ClientAPI = None,
):
    # how many results to get from the database ? This is the first selection. Once we get them we rerank them and select the top K.
    num_code_query_results = 50
    num_text_query_results = 25

    # Get collection  by name and the appropriate embedding function
    code_collection = _get_collection(client, collection_name)
    text_collection = _get_collection(client, collection_name + "_text")

    # Perform search
    code_results = code_collection.query(
        query_texts=[query], n_results=num_code_query_results
    )
    text_results = text_collection.query(
        query_texts=[query], n_results=num_text_query_results
    )
    code_snippets = code_results["documents"][0]
    text_snippets = text_results["documents"][0]

    # rerank results and keep top k, these can be the contex of the LLM
    rerank_model = CrossEncoder(
        "jinaai/jina-reranker-v1-turbo-en", trust_remote_code=True
    )
    code_reranked_results = rerank_model.rank(query, code_snippets, top_k=top_k)
    text_reranked_results = rerank_model.rank(query, text_snippets, top_k=top_k)

    code_documents = []
    code_metadata = []
    code_scores = []
    text_documents = []
    text_metadata = []
    text_scores = []
    for citem, titem in zip(code_reranked_results, text_reranked_results):
        code_corpus_id = citem["corpus_id"]
        code_scores.append(citem["score"])
        code_documents.append(code_snippets[code_corpus_id])
        code_metadata.append(code_results["metadatas"][0][code_corpus_id])

        text_corpus_id = titem["corpus_id"]
        text_scores.append(titem["score"])
        text_documents.append(text_snippets[text_corpus_id])
        text_metadata.append(text_results["metadatas"][0][text_corpus_id])

    return {
        "code_documents": code_documents,
        "code_metadata": code_metadata,
        "code_scores": code_scores,
        "text_documents": text_documents,
        "text_metadata": text_metadata,
        "text_scores": text_scores,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query dabase for code snippets",
    )
    parser.add_argument(
        "query",
        type=str,
        help="Query for the search",
        default=None,
    )
    parser.add_argument(
        "--database",
        type=str,
        help="Path to the database.",
        default=None,
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        help="Name for the collection in the database. Used to distinguish different families of documents during retrieval",
        default="python-examples",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        help="Return the top k matches tot he query",
        default=5,
    )
    args = parser.parse_args()

    print("***********************************************************************")
    reranked_results = query_db_interactive(
        args.query, args.database, args.collection_name, args.top_k
    )
    print(f"Query: {args.query}\n")
    print(f"Top {args.top_k} most similar code chunks:")
    for document, metadata, score in zip(
        reranked_results["code_documents"],
        reranked_results["code_metadata"],
        reranked_results["code_scores"],
    ):
        print(f"Score: {score}")
        print(f"snippet {document}:")
        print(f"from {metadata}:")
        print("-------------------------------------------------------")
    for document, metadata, score in zip(
        reranked_results["text_documents"],
        reranked_results["text_metadata"],
        reranked_results["text_scores"],
    ):
        print(f"Score: {score}")
        print(f"snippet {document}:")
        print(f"from {metadata}:")
        print("-------------------------------------------------------")
