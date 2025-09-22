from llama_cpp import Llama
import re
import ast

def extract_action_items(journal_text):
    llm = Llama(
        model_path="./llm_models/Phi-3-mini-4k-instruct-q4.gguf",
        n_ctx=2048,
        n_threads=8
    )

    prompt = f""" 
            Extract actionable items (tasks to be done) from the given journal entry. 
            Precisely list only all those specific tasks, calls, appointments, or commitments etc that are mentioned in the text, to be done in future.
            Here's the journal entry:
            {journal_text}

            Actionable items (your response should be formatted as a single python list of strings):
            """

    response = llm(prompt, max_tokens=150, temperature=0.7)
    response_text = response["choices"][0]["text"].strip()
    # find python list of strings from response
    result_lists = re.findall(r"\[[^\[\]]*['\"][^\[\]]*['\"][^\[\]]*]", response_text)
    if len(result_lists)>0:
        return ast.literal_eval(result_lists[0])
    else:
        return []

