""" celery tasks """

from celery import shared_task
from llama_cpp import Llama
from .models import JournalEntry, Task
from .utils import extract_action_items

LLM = None


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def extract_and_create_tasks(journal_id):
    """
    worker task:
    load the journal by id from db,
    extract action items,
    create tasks for new action items
    """
    global LLM
    # print("------------------------IN WORKER")

    if LLM is None:
        LLM = Llama(
            model_path="./llm_models/Phi-3-mini-4k-instruct-q4.gguf",
            n_ctx=2048,
            n_threads=4,
        )

    try:
        journal = JournalEntry.objects.get(id=journal_id)
    except JournalEntry.DoesNotExist:
        print(f"JournalEntry {journal_id} not found, skipping extraction")
        return {"status": "missing"}

    created = []
    new_tasks = extract_action_items(LLM, journal.content)
    for task_desc in new_tasks:
        desc = task_desc.strip()
        if (
            desc
            and desc != "None"
            and not Task.objects.filter(
                created_by=journal.author, description=desc
            ).exists()
        ):
            t = Task.objects.create(created_by=journal.author, description=desc)
            created.append(t.id)

    return {"status": "ok", "created_task_ids": created}
