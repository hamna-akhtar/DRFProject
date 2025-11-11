"""
AI chatbot
get LLM instance, build vector DB for context, generate chatbot response using context
"""

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import re
from JournalApp.celery import ask_llm
from journals.models import JournalEntry, Task
from users.models import CustomUser
from friends.models import FriendRequest


class Chatbot:
    def __init__(self, user_id):
        self.user_id = user_id
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.persist_dir = "./chroma_db"
        self.collection_name = f"user_{user_id}"
        self.vector_store = self._build_vector_store()

    def _build_vector_store(self):
        """build new vector store from user's data"""
        documents = []

        # get my profile
        user = CustomUser.objects.get(id=self.user_id)
        documents.append(
            Document(
                page_content=f"My Profile: {user}",
                metadata={"type": "my profile", "id": str(self.user_id)},
            )
        )

        # get journals
        my_journals = JournalEntry.objects.filter(author=user)
        public_journals = JournalEntry.objects.filter(access="public").exclude(
            author=user
        )
        shared_with_me = JournalEntry.objects.filter(shared_to=user)

        for entry in my_journals:
            documents.append(
                Document(
                    page_content=f"My Journal Entry from ({entry.created_at}): {entry.content}",
                    metadata={"type": "journal", "id": str(entry.id)},
                )
            )
        for entry in public_journals:
            documents.append(
                Document(
                    page_content=f"Public Journal Entry from: {entry.created_at}: {entry.content}",
                    metadata={"type": "journal", "id": str(entry.id)},
                )
            )
        for entry in shared_with_me:
            documents.append(
                Document(
                    page_content=f"Journal shared with me by {entry.author} at {entry.created_at}: {entry.content}",
                    metadata={"type": "journal", "id": str(entry.id)},
                )
            )

        # Get tasks
        tasks = Task.objects.filter(created_by_id=self.user_id)
        for task in tasks:
            documents.append(
                Document(
                    page_content=f"Task: {task.description}",
                    metadata={"type": "task", "id": str(task.id)},
                )
            )

        # Get friends
        friends = user.friends.all()
        for friend in friends:
            documents.append(
                Document(
                    page_content=f"{friend.email} is my friend",
                    metadata={"type": "friend", "id": str(friend.id)},
                )
            )

        # Get friend requests sent and received
        received_requests = FriendRequest.objects.filter(
            requested_to=self.user_id, accepted=False
        )
        for request in received_requests:
            documents.append(
                Document(
                    page_content=f"Unaccepted Friend Request, received from: {request.requested_by}",
                    metadata={"type": "received friend request", "id": str(request.id)},
                )
            )

        sent_requests = FriendRequest.objects.filter(
            requested_by=self.user_id, accepted=False
        )
        for request in sent_requests:
            documents.append(
                Document(
                    page_content=f"Unaccepted Friend Request, sent to: {request.requested_to}",
                    metadata={"type": "sent friend request", "id": str(request.id)},
                )
            )

        if not documents:
            documents.append(
                Document(
                    page_content="No user data yet.",
                    metadata={"type": "placeholder", "id": ""},
                )
            )

        # if vector store exists then load else create new

        client = Chroma(
            persist_directory=self.persist_dir, embedding_function=self.embeddings
        )
        if any(
            collection.name == self.collection_name
            for collection in client._client.list_collections()
        ):
            print(f"Loading existing vector store for user {self.user_id}")
            return Chroma(
                collection_name=self.collection_name,
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
            )
        print(f"Building new vector store for user {self.user_id}")
        return Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            persist_directory=self.persist_dir,
        )

    def chat(self, user_message):
        """generate response using RAG"""

        # retrieve relevant documents
        if any(
            word in user_message.lower()
            for word in ["all", "list", "multiple", "count", "many", "top", "total"]
        ):
            k = len(self.vector_store.get()["ids"])
        else:
            k = 5

        try:
            relevant_docs = self.vector_store.similarity_search(user_message, k=k)
        except Exception as e:
            print(
                f"error in similarity search:{e}\nrebuilding vector store for user {self.user_id}"
            )

            # delete old and rebuild vector store
            client = Chroma(
                persist_directory=self.persist_dir, embedding_function=self.embeddings
            )
            if any(
                collection.name == self.collection_name
                for collection in client._client.list_collections()
            ):
                client._client.delete_collection(self.collection_name)
            print(f"deleted vector store for user {self.user_id}")

            # retry similarity search w new store
            self.vector_store = self._build_vector_store()
            relevant_docs = self.vector_store.similarity_search(user_message, k=k)

        print("DOCS\n", [doc.page_content for doc in relevant_docs])
        # build context from relevant documents
        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        prompt = f"""
                <System>
                You are a helpful AI assistant with access to the user's journal entries and tasks. 
                Use the context provided below to answer the user's questions precisely starting with <Answer Begin>' and ending with <Answer End>
                Here is the context from user's data: 
                {context}

                <User question>
                {user_message}
                """
        # print("PROMPT\n", prompt)

        # Generate response from LLM service
        try:
            response = ask_llm(prompt)
            print(f"Response: {response}")
            text = response["choices"][0]["text"].strip()
            matches = re.findall(r"<Answer Begin>(.*?)<Answer End>", text, re.DOTALL)

            # get the first non-empty trimmed match
            extracted_answer = next(
                (m.strip() for m in matches if m.strip()),
                "Unable to find anything, please try again.",
            )
            # print("Extracted Answer:", extracted_answer)

            return extracted_answer

        except Exception as e:
            print(f"LLM service error: {e}")
            raise Exception(f"LLM service error: {str(e)}")


def create_chatbot(user_id):
    """helper to create chatbot"""
    return Chatbot(user_id=user_id)
