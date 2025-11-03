""" journals helper functions """

import re
import ast
from JournalApp.celery import ask_llm


def extract_action_items(journal_text):
    """extract tasks from given journal entry through llm"""

    # print("---------------EXTRACTING NOW")

    prompt = f"""
            Extract actionable items (tasks to be done) from the given journal entry.
            Precisely list only all those specific tasks, calls, appointments, or commitments etc that are mentioned in the journal entry, to be done in future.
            if there is nothing to be done, only in that case return an empty list.
            Here's the journal entry:
            {journal_text}
            
            Actionable items (your response should be formatted as a single python list of strings):
            """

    response = ask_llm(prompt)
    response_text = response["choices"][0]["text"].strip()
    print("TASKS--------------------------\n", response_text)
    # find python list of strings from response
    result_lists = re.findall(r"\[[^\[\]]*['\"][^\[\]]*['\"][^\[\]]*]", response_text)
    if len(result_lists) > 0:
        return ast.literal_eval(result_lists[0])
    return []
