""" celery tasks """

from celery import shared_task
from chat.tasks import update_vector_store_for_user
from .models import JournalEntry, Task
from .utils import extract_action_items


@shared_task
def extract_and_create_tasks(journal_id):
    """
    worker task:
    load the journal by id from db,
    extract action items,
    create tasks for new action items
    """

    try:
        journal = JournalEntry.objects.get(id=journal_id)
    except JournalEntry.DoesNotExist:
        print(f"JournalEntry {journal_id} not found, skipping extraction")
        return {"status": "missing"}

    created = []
    new_tasks = extract_action_items(journal.content)
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

            page_content=f"Task: {t.description}"
            metadata={"type": "task", "id": str(t.id)}
            update_vector_store_for_user.delay(journal.author.id, page_content=page_content, metadata=metadata, action='create')

    return {"status": "ok", "created_task_ids": created}
