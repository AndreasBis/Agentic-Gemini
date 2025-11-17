# Agentic Gemini Stress Test Prompts

This file provides a set of standard prompts to test the core functionality of each agent mode in `main.py`.

---

## Mode 1: Basic Code Agent

**Prompt:** `Plot a sine wave from 0 to 4*pi and save the plot to a file named 'sine_wave.png'.`

**Expected Outcome:** The agent should write and execute Python code (using `matplotlib`) to generate the plot and save it to the `coding` directory.

---

## Mode 2: Coder vs. Reviewer Chat

**Prompt:** `Write a Python function that takes a list of strings and returns a new list containing only the strings that are palindromes.`

**Expected Outcome:** The `coder` agent should provide a Python function. The `reviewer` agent should analyze the code, suggest improvements (e.g., case-insensitivity, handling of spaces), and *not* write code itself.

---

## Mode 3: Orchestrated Group Chat

**Prompt:** `Create a plan for a new social media marketing campaign for a local coffee shop.`

**Expected Outcome:** The `manager_agent` should initiate the topic. The `planner_agent` should create a plan. The `reviewer_agent` should provide feedback. The chat should conclude when the `manager_agent` is satisfied and says `DONE!`.

---

## Mode 4: Group Chat with Human-in-the-Loop

**Prompt:** `Outline the key sections for a technical whitepaper on the "find, read, edit, run" agent model.`

**Expected Outcome:** The `expert_agent` should provide initial guidance. The `planner_agent` should draft an outline. The `reviewer_agent` should give feedback. The conversation should eventually be passed to the `human_validator` for final approval. The chat ends when the human user types `APPROVED`.

---

## Mode 5: Tool Use Chat (File Operations)

*(Note: These prompts assume you have a `test.py`, `test.c`, and `test.ipynb` file in your mounted `/my_files` directory.)*

### Function: _find_file_path
**Prompt:** `First, find the file 'test.py'.`
**Expected Outcome:** Agent calls `_find_file_path('test.py')` and returns its relative path.

### Function: _read_file_content (.py)
**Prompt:** `Read the contents of 'test.py'.`
**Expected Outcome:** Agent finds and reads the file, returning its full text content.

### Function: _read_file_content (.c)
**Prompt:** `What's inside the 'test.c' file?`
**Expected Outcome:** Agent finds and reads the file, returning its full text content.

### Function: _read_file_content (.ipynb)
**Prompt:** `Read the 'test.ipynb' notebook.`
**Expected Outcome:** Agent finds and reads the file, returning *only* the content from its code cells.

### Function: _write_file_content
**Prompt:** `Find 'test.py', read it, and then edit it to add a comment at the top: '# This file was edited by an agent'.`
**Expected Outcome:** Agent finds, reads, then calls `_write_file_content` to overwrite the file with the new comment and the original content.

### Function: Run .py
**Prompt:** `Run the 'test.py' script.`
**Expected Outcome:** Agent finds the file and replies with a `sh` block (e.g., `python3 "test.py"`) for the executor to run.

### Function: Fail to Run .c (Expected)
**Prompt:** `Find 'test.c' and run it.`
**Expected Outcome:** The agent should state that it *cannot* run `.c` files, as per its instructions, and that it can only execute `.py` files. It should *not* attempt to run it.