"""celery setup"""

import os
from celery import Celery
from celery import shared_task
from llama_cpp import Llama



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "JournalApp.settings")

app = Celery("JournalApp")
app.config_from_object("django.conf:settings", namespace="CELERY")

LLM = None
@shared_task
def ask_llm(prompt):
    global LLM
    if LLM is None:
        print("Loading model...")
        LLM = Llama(
            model_path="./llm_models/Phi-3-mini-4k-instruct-q4.gguf",
            n_ctx=4096,
            n_threads=4,
            verbose=False,
        )
        print("Model loaded!")

    # generate response
    response = LLM(
        prompt,
        max_tokens=512,
        temperature=0.7,
    )
    return response


app.autodiscover_tasks()
