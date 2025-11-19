# Release History

* **v0.6:** Expanded file compatibility, intelligent search, and safety limits.

    1.  **Expanded File Support:**
        
        - Added support for reading `.pdf` (via `pypdf`) and `.docx` (via `python-docx`) files.
        - The agent can now ingest and process complex document formats alongside code files.

    2.  **Intelligent File Search:**
        
        - `_find_file_path` now employs fuzzy matching logic. It ignores casing and common separators (`_`, `-`, ` `), allowing the agent to successfully locate files like "Example File.txt" even when searching for variations like "example_file.txt" or "examplefile".

    3.  **Safety & Performance Limits:**
        
        - `_read_file_content` now enforces a strict character limit of 65,536 characters per read operation.
        - This prevents large documents from overflowing the context window. Truncated outputs are automatically flagged with a warning message.

* **v0.5:** Implemented non-root container execution for better file permissions and added early termination logic to `Mode 5` for API efficiency.

    1.  **Docker Security (Non-Root User):**
        
        - Updated `Dockerfile` to create and run as a dedicated user `agentuser` (UID 1000) instead of `root`.
        - Files created by the agent in the mounted volume are now owned by the host user, resolving "locked file" permission errors on the host system.

    2.  **API Efficiency (Mode 5):**
        
        - Updated system prompt to instruct the agent to reply with `TERMINATE` upon task completion.
        - Added `is_termination_msg` check to `executor_agent` to immediately stop the chat loop, preventing unnecessary token usage from redundant conversation.

* **v0.4:** Major expansion of `Mode 5` toolset, implementation of security guardrails, and strict code formatting compliance.

    1.  **Extended File System Tools:**
        
        - Added `_create_file` and `_create_directory` for generating new assets.
        - Added `_delete_item` for removing files and directories.
        - Added `_copy_file`, `_cut_file`, and `_paste_file` to support clipboard-style file manipulation (copy/move).

    2.  **Security & Guardrails:**
        
        - **Human-in-the-Loop Verification:** All destructive or creative operations (Write, Create, Delete, Copy, Cut, Paste) now require explicit user confirmation (`Type "YES" to confirm`) via the terminal to prevent accidental data loss.
        - **Hidden File Protection:** Agents are strictly blocked from creating, editing, deleting, or copying hidden files and directories (those starting with `.`).

    3.  **Code Formatting & Compliance:**
        
        - Converted tool methods to static methods to ensure compatibility with `autogen` registration while maintaining clipboard state.

    4.  **STRESS_TEST:**
        
        - Added comprehensive test cases for file creation, safe deletion workflows, and clipboard (copy/cut/paste) operations.

* **v0.3:** Updated `Mode 5` with interactive script execution, improved security, and file system stability.

    1.  **Interactive Script Execution (Mode 5):**

        - The agent can now execute interactive Python scripts (using `input()`) by "acting as the user" and piping inputs via `printf` or `echo`.
        - System prompt updated to enforce this behavior, preventing terminal freezing during execution.

    2.  **Docker Execution Strategy:**

        - Switched execution to run directly inside the active container (`use_docker=False`) instead of spawning sibling containers.
        - This resolves the issue of root-owned "locked" files being created on the host system.

    3.  **File Search Improvements:**

        - `_find_file_path` now deterministically filters out hidden files and directories (starting with `.`) to improve safety and reduce clutter.

    4.  **STRESS_TEST:**

        - Refined stress test scenarios - for modes *1* and *5* - to ensure a more precise and targeted validation of agent capabilities.

* **v0.2:** Added new function tools for `mode 5`. Updated requirements.txt. Updated system prompts. Added STRESS_TEST.

    1.  New Function Tools (Mode 5):

        - `_find_file_path`: Searches the `/my_files` directory for a file.
        - `_read_file_content`: Reads text from `.py`/`.c` and extracts code from `.ipynb`.
        - `_write_file_content`: Writes/overwrites content to `.py`, `.c`, and `.ipynb` files.
        - The `_get_weekday` function tool was removed.

    2.  New Dependencies:

        - `nbformat` for working with Jupyter (`.ipynb`) notebooks.

    3.  New System Prompts:

        - Modes 3 & 4: Prompts generalized from "classroom/teacher" roles to "project manager," "senior planner," and "subject matter expert."
        - Mode 5: System prompt completely replaced to manage file operations (find, read, write) and `.py`-only code execution.

    4.  STRESS_TEST includes prompts for each *agent mode* (and *function tool*, for mode 5) so that the stable functionality of `main.py` can be guaranteed.

* **v0.1:** Dockerized `main.py`. Added README.
* **v0.0:** Initial Commit.