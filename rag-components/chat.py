from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.ollama import Ollama
import argparse
import query_db
import json
from string import Template
from pathlib import Path
from typing import List
import os

PROMPT = Template(
    """
You are an AI assistant specializing in VTK (Visualization Toolkit)
documentation. Your primary task is to provide accurate, concise, and helpful
responses to user queries about VTK, including relevant code snippets

Here is the context information you should use to answer queries:
<context>
$CONTEXT
</context>

Here's the user's query:

<user_query>
$QUERY
</user_query>

When responding to a user query, follow these guidelines:

1. Relevance Check:
   
   - If the query is not relevant to VTK, respond with "This question is not relevant to VTK."

2. Answer Formulation:
   
   - If you don't know the answer, clearly state that.
   - If uncertain, ask the user for clarification.
   - Respond in the same language as the user's query.
   - Be concise while providing complete information.
   - If the answer isn't in the context but you have the knowledge, explain this to the user and provide the answer based on your understanding.
"""
)
# History of a chat
HISTORY = [
    ChatMessage(
        role="system", content="You are a helpful assistant"
    ),  # TODO what else to add ?
]

llm = None
client = None


def init(model: str, database: str) -> None:
    global llm, client
    try:
        if any(
            x in model for x in ["gpt", "o1", "o3"]
        ):  # TODO this is too simplistic and error-prone
            llm = OpenAI(model=model)
        elif "claude" in model:
            llm = Anthropic(model=model)
        else:  # assumming an ollama model
            llm = Ollama(
                model=model, request_timeout=3000.0, address="http://localhost:11434"
            )
    except:
        raise RuntimeError(f"Usupported Model {model}")

    client = query_db.initialize_db(database_path=database)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"


def ask(query: str, collection_name: str, top_k: int, streaming: bool = False):
    # corpus = json.load(open(collection_name+".json"))
    HISTORY.append(ChatMessage(role="user", content=query))

    # Query the index to retrieve relevant documents
    results = query_db.query_db(query, collection_name, top_k, client)
    relevant_examples = [item["original_id"] for item in results["code_metadata"]] + [
        item["code"] for item in results["text_metadata"]
    ]
    snippets = [item for item in results["code_documents"]]
    relevant_examples = list(set(relevant_examples))

    # Combine the retrieved documents into a single text
    retrieved_text = "\n\n## Next example:\n\n".join(snippets)
    content = PROMPT.substitute(CONTEXT=retrieved_text, QUERY=query.rstrip())
    # print(content)

    # Add the retrieved text as a new message
    HISTORY.append(ChatMessage(role="assistant", content=content.rstrip()))

    # Generate a response using the LLM
    if streaming:
        response = llm.stream_chat(HISTORY)
    else:
        response = llm.chat(HISTORY)

    return {"response": response, "references": relevant_examples}


def _generate_urls_from_references(references: List[str]):
    urls = []
    for ref in references:
        ref = Path(ref)
        # this transformation alters
        # vtk-examples.git/src/Python/PolyData/CurvaturesAdjustEdges.py
        # to
        # https://examples.vtk.org/site/Python/PolyData/CurvaturesAdjustEdges
        url = "https://examples.vtk.org/site/{}".format(
            (ref.relative_to(ref.parents[-3])).with_suffix("")
        )
        urls.append(url)
    return urls


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query database for code snippets",
    )
    parser.add_argument(
        "--database",
        type=str,
        help="Path to the database.",
        default="./db/codesage-codesage-large-v2",  # this corresponds to the default path of the default model in populate_db.py
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
        help="Retrieve the top `k` examples from the database when composing a context",
        default=15,
    )
    parser.add_argument(
        "--model",
        type=str,
        help="LLM model to use",
        default="gpt-4",
    )
    args = parser.parse_args()
    init(args.model, args.database)
    print(
        "Welcome to VTK's assistant! What would you like to know ?\ntype 'exit' to quit"
    )
    while True:
        user_input = input("User: ")
        if len(user_input) == 0:
            continue
        full_reply = ""
        if user_input.lower() == "exit":
            print("Bye!")
            break
        reply = ask(user_input, args.collection_name, args.top_k, streaming=True)
        for item in reply["response"]:
            print(item.delta, end="", flush=True)
            full_reply += item.delta
        print(
            "\n Here are some relevant references:\n",
            "\n".join(_generate_urls_from_references(reply["references"])),
        )
        # add reply to the chat history
        HISTORY.append(ChatMessage(role="assistant", content=full_reply.rstrip()))
