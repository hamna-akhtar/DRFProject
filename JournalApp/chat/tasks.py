"""celery task to generate AI response"""

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import traceback
from langchain_core.documents import Document
from langchain_chroma import Chroma
from chromadb.errors import NotFoundError
from .chatbot import create_chatbot
from .models import ChatMessage


def delete_from_store(store, metadata):
    try:
        # get all docs with specific id and type
        results = store.get(where={"id": metadata["id"]})
        if results:
            ids_to_delete = []
            for doc_id, md in zip(results["ids"], results["metadatas"]):
                if md.get("type") == metadata["type"]:
                    ids_to_delete.append(doc_id)

            # delete matching docs by internal chroma ids
            if ids_to_delete:
                store.delete(ids=ids_to_delete)
                print(f"doc deleted for ----- {metadata}")
            else:
                print(
                    f'Store already updated : Cant find type {metadata["type"]} with id {metadata["id"]} in vector store'
                )
    except NotFoundError as e:
        print(f'Cant find id {metadata["id"]} in vector store:\n {e}')


@shared_task
def update_vector_store_for_user(user_id, page_content="", metadata={}, action=""):
    """update an existing user's vector store whenever changes made in db"""

    chatbot = create_chatbot(user_id)
    store = chatbot.vector_store
    print(f"updating store for user {user_id}...........")

    if action == "create":
        new_doc = Document(page_content=page_content, metadata=metadata)
        store.add_documents([new_doc])
        print(f"doc created for ----- {page_content} : {metadata}")

    if action == "update":
        delete_from_store(store, metadata)
        new_doc = Document(page_content=page_content, metadata=metadata)
        store.add_documents([new_doc])
        print(f"doc updated for ----- {page_content} : {metadata}")

    if action == "delete":
        delete_from_store(store, metadata)

    # results = store.get(where={"type": metadata["type"]})
    # print("AFTER UPDATE--------------------------\n", results)


@shared_task
def delete_vector_store_for_user(user_id):
    """delete vector store for user"""
    chatbot = create_chatbot(user_id)
    collection_name = f"user_{user_id}"
    client = Chroma(
        persist_directory="./chroma_db", embedding_function=chatbot.embeddings
    )

    if any(
        collection.name == collection_name
        for collection in client._client.list_collections()
    ):
        client._client.delete_collection(collection_name)
    print(f"deleted vector store for user {user_id}")
    del chatbot


@shared_task
def generate_response_task(user_id, message, room_name):
    """Generate AI response"""

    try:
        chatbot = create_chatbot(user_id)
        response = chatbot.chat(message)

        # save bot response in db and send through websocket
        ChatMessage.objects.create(user_id=user_id, role="bot", content=response)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_name, {"type": "chat_response", "message": response}
        )

    except Exception as e:
        print(f"Error generating response: {e}")
        traceback.print_exc()

        ChatMessage.objects.create(
            user_id=user_id, role="bot", content=f"an error occurred: {str(e)}"
        )
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_name,
            {"type": "chat_response", "message": f"an error occurred: {str(e)}"},
        )
