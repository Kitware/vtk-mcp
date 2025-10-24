import chromadb
from chromadb.api import ClientAPI
from chromadb.utils import embedding_functions
from pathlib import Path
from llama_index.core.node_parser import CodeSplitter, SentenceSplitter, TextSplitter
from sentence_transformers import SentenceTransformer
import hashlib

from tqdm import tqdm
import json

import argparse
from typing import Optional, List

EMBEDDING_MODEL_TEXT = "all-MiniLM-L6-v2"  # "nomic-ai/nomic-embed-text-v2-moe"

LANGUAGE_SUFFIX = {
    "markdown": "md",
    "python": "py",
}


def _create_collection(
    client: ClientAPI, name: str, embedding_model: str, splitter: TextSplitter
):
    collection = client.create_collection(
        name=name,
        embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model, trust_remote_code=True
        ),
        metadata={
            "embedding_model": embedding_model,  # chroma db does not store the embedding model but it is required when performing queries, so we store it as metadata
            # not all model return normalized embeddings so the metric matters. Let's stick with cosine similarity
            # https://wietsevenema.eu/is-cosine-similarity-always-the-best-choice-for-text-embedding-search
            "hnsw:space": "cosine",
            "splitter": splitter.json(),
        },
    )
    return collection


def md5_for_file(path: Path):
    with open(path, "rb") as f:
        data = (
            f.read()
        )  # TODO if we have at some point larger files we will need to read increamentally
        return hashlib.md5(data).hexdigest()


def _get_unique(files: List[Path]):
    unique = {}
    for file in files:
        if not file.exists():
            continue
        md5 = md5_for_file(file)
        if md5 not in unique:
            unique[md5] = file
    return list(unique.values())


def fill_database(
    files: List[Path],
    database_path: str,
    embedding_model: str,
    language: Optional[str] = None,
    collection_name: str = "",
    corpus_name: Optional[str] = None,
):
    if corpus_name is None:
        corpus_name = collection_name + ".json"

    code_splitter = None
    if language is not None:
        # larger chunk_size means larger
        # context. Remember however that LLMs have limmited context anyways so, you
        # need to trade-off between few big examples and many small.
        code_splitter = CodeSplitter(
            language=language,
            chunk_lines=20,
            chunk_lines_overlap=5,  # this does not seem to have any effect
            max_chars=700,
        )
    text_splitter = SentenceSplitter()

    print("Setting up database ...")
    client = chromadb.PersistentClient(path=database_path)

    # Create a collection with the appropriate embedding function
    collection_code = _create_collection(
        client, collection_name, embedding_model, code_splitter
    )
    # create a collection with descriptions of the examples.
    collection_text = _create_collection(
        client, collection_name + "_text", EMBEDDING_MODEL_TEXT, text_splitter
    )

    code_files = [file for file in files if file.suffix == ".py"]
    markdown_files = [file.parent / (file.stem + ".md") for file in code_files]
    # keep only unique files, otherwise we may cause overfit. Also, it produces warnings in chromadb
    code_files = _get_unique(code_files)
    markdown_files = _get_unique(markdown_files)

    # TODO  how to use the following which processing snippets in parallel while keeping track of the association between chunk,path ?
    # text_embeddings = text_model.encode( text, batch_size=4,show_progress_bar=True,)

    # corpus is the dictionary of filesnames->content . We save is as json and
    # use it in the retrieval pahse to get the original documents
    corpus = {}

    for fcode, ftext in tqdm(zip(code_files, markdown_files)):
        print(fcode)
        with open(fcode, "r") as code:
            try:
                code = code.read()
                code_chunks = code_splitter.split_text(code)
                collection_code.add(
                    documents=code_chunks,
                    ids=[f"snippet_{fcode.name}_{i}" for i in range(len(code_chunks))],
                    metadatas=[
                        {
                            "original_id": str(fcode),
                            "text": ftext.name if ftext.exists() else "null",
                        }  # chromadb does not accept None as metadata value
                        for _ in range(len(code_chunks))
                    ],
                )
                corpus[str(fcode)] = code
                if ftext.exists():
                    text = open(ftext, "r")
                    text = text.read()
                    text_chunks = text_splitter.split_text(text)
                    collection_text.add(
                        documents=text_chunks,
                        ids=[
                            f"snippet_{ftext.name}_{i}" for i in range(len(text_chunks))
                        ],
                        metadatas=[
                            {"original_id": str(ftext), "code": str(fcode)}
                            for _ in range(len(text_chunks))
                        ],
                    )
                    corpus[str(ftext)] = text
            except ValueError as error:
                print(f"Skipping {fcode}")
                print(error)

    with open(corpus_name, "w") as file:
        json.dump(corpus, file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Populate database with embeddings of documents based on a model",
    )
    parser.add_argument(
        "--language", type=str, help="Language of the documents", default="python"
    )
    parser.add_argument(
        "--dir",
        required=True,
        type=str,
        help="Base Directory of documents. The script will collect all documents recursively",
    )
    parser.add_argument(
        "--database",
        type=str,
        help="Name of the database. Default is ./db/model-name",
        default=None,
    )
    parser.add_argument(
        "--model",
        default="codesage/codesage-large-v2",
        help="Model name for embedding. For now, we use sentence transformer models. See https://www.sbert.net/",
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        help="Name for the collection in the database. Used to distinguish different families of documents during retrieval",
        default="python-examples",
    )
    args = parser.parse_args()

    files = [file for file in Path(args.dir).rglob("*") if not file.is_dir()]

    language = args.language.lower()
    database_path = args.database
    if database_path is None:
        model_prefix = args.model.replace("/", "-")
        database_path = str(Path("./db") / Path(model_prefix))

    fill_database(files, database_path, args.model, language, args.collection_name)
