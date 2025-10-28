"""RAG chatbot"""
from langchain_community.chains import ConversationalRetrievalChain
from langchain_community.memory import ConversationBufferMemory
from .llm import Phi3LLM
from .vector_db_builder import VectorDBBuilder


class RAGChatbot:
    def __init__(self, user_id):
        self.user_id = user_id
        self.llm = Phi3LLM()

        builder = VectorDBBuilder()
        self.vector_store = builder.load_for_user(user_id)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=self.memory,
            return_source_documents=False,
            verbose=False
        )

    def chat(self, message):
        """send message, get response"""
        result = self.qa_chain({"question": message})
        return result["answer"]

# def create_chatbot(user_id):
#     return RAGChatbot(user_id=user_id)