# Release History

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