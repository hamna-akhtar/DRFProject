"""celery setup"""

import os
from celery import Celery
from celery import shared_task
import requests
from JournalApp.settings import LLM_SERVICE_API_KEY, LLM_SERVICE_URL


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "JournalApp.settings")

app = Celery("JournalApp")
app.config_from_object("django.conf:settings", namespace="CELERY")


@shared_task
def ask_llm(prompt):
    print("requesting llm......")
    response = requests.post(
        f"{LLM_SERVICE_URL}/generate",
        json={"prompt": prompt},
        headers={"X-API-Key": LLM_SERVICE_API_KEY, "Content-Type": "application/json"},
        timeout=800,
    )
    # print("service response: ", response.json())
    return response.json()


app.autodiscover_tasks()
