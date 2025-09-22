from llama_cpp import Llama
import re
import ast

def extract_action_items(journal_text):
    llm = Llama(
        model_path="./llm_models/phi-2.Q4_K_M.gguf",
        n_ctx=2048,
        n_threads=8
    )

    prompt = f""" 
            Extract actionable items (tasks to be done) from the given journal entry. 
            List only all the specific tasks, calls, appointments, or commitments etc that need to be done.
            Here's the journal entry:
            {journal_text}

            Actionable items (as a python list of strings):
            """

    response = llm(prompt, max_tokens=150, temperature=0.7)
    res = response["choices"][0]["text"].strip()
    # print("RESPONSE: ", res)
    return ast.literal_eval(re.findall(r'\[.*?]', res)[0])

