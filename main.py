import logging
import json
import os
import shutil
import nbformat
from nbformat.v4 import new_notebook, new_code_cell
from datetime import datetime
from typing import Annotated

from autogen import (
    AssistantAgent,
    UserProxyAgent,
    LLMConfig,
    ConversableAgent,
    register_function,
)
from autogen.agentchat import run_group_chat
from autogen.agentchat.group.patterns import AutoPattern


class AgenticGemini:

    _clipboard_src = None
    _clipboard_op = None

    def __init__(self, config_path: str, max_calls: int):

        self.config_path = config_path
        self.max_calls = max_calls
        self.llm_config = LLMConfig.from_json(path=self.config_path)

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def run_basic_code_agent(self):

        self.logger.info('Running: Basic Code Agent')

        prompt = input('Enter your prompt for the assistant: ')

        assistant = AssistantAgent('assistant', llm_config=self.llm_config)
        user_proxy = UserProxyAgent(
            'user_proxy',
            code_execution_config={'work_dir': 'coding', 'use_docker': False}
        )

        response = user_proxy.run(assistant, message=prompt)

        response.process()
        self.logger.info('Final output:\n%s', response.summary)

    def run_coder_reviewer_chat(self):

        self.logger.info('Running: Coder vs. Reviewer Chat')

        prompt = input('Enter your prompt for the coder: ')

        coder = ConversableAgent(
            name='coder',
            system_message='You are a Python developer. You write Python scripts to solve tasks. Be concise.',
            llm_config=self.llm_config,
        )

        reviewer = ConversableAgent(
            name='reviewer',
            system_message='You are a code reviewer. Analyze provided code and suggest improvements. Do not generate code, only suggest improvements.',
            llm_config=self.llm_config,
        )

        response = reviewer.run(
            recipient=coder,
            message=prompt,
            max_turns=self.max_calls
        )

        response.process()
        self.logger.info('Final output:\n%s', response.summary)

    def run_group_chat_auto(self):

        self.logger.info('Running: Orchestrated Group Chat (AutoPattern)')

        prompt = input('Enter the topic for the plan: ')

        planner_message = 'You are a senior planner. Given a topic, you create a detailed, step-by-step plan.'
        reviewer_message = 'You are a senior reviewer. You analyze the provided plan, check it for completeness and logic, and suggest up to 3 concrete improvements.'
        manager_message = 'You are the project manager. You initiate the topic for the plan and collaborate with the planner and reviewer to finalize it. When satisfied with the result, output DONE!'

        planner_agent = ConversableAgent(
            name='planner_agent',
            system_message=planner_message,
            description='Creates or revises plans.',
            llm_config=self.llm_config,
        )

        reviewer_agent = ConversableAgent(
            name='reviewer_agent',
            system_message=reviewer_message,
            description='Provides one round of feedback to plans.',
            llm_config=self.llm_config,
        )

        manager_agent = ConversableAgent(
            name='manager_agent',
            system_message=manager_message,
            is_termination_msg=lambda x: 'DONE!' in (x.get('content', '') or '').upper(),
            llm_config=self.llm_config,
        )

        auto_selection = AutoPattern(
            agents=[manager_agent, planner_agent, reviewer_agent],
            initial_agent=manager_agent,
            group_manager_args={'name': 'group_manager', 'llm_config': self.llm_config},
        )

        response = run_group_chat(
            pattern=auto_selection,
            messages=prompt,
            max_rounds=self.max_calls,
        )

        response.process()
        self.logger.info('Final output:\n%s', response.summary)

    def run_human_in_the_loop_chat(self):

        self.logger.info('Running: Group Chat with Human-in-the-Loop')

        prompt = input('Enter the topic for the plan (human will validate): ')

        planner_message = 'You are a senior planner. Given a topic, you create a detailed, step-by-step plan.'
        reviewer_message = 'You are a senior reviewer. You analyze the provided plan, check it for completeness and logic, and suggest up to 3 concrete improvements.'
        expert_message = 'You are a subject matter expert. You do not write the plan, but you provide initial guidance and context on the key topic to the planner.'

        planner_agent = ConversableAgent(
            name='planner_agent',
            system_message=planner_message,
            description='Creates or revises plans before having them reviewed.',
            is_termination_msg=lambda x: 'APPROVED' in (x.get('content', '') or '').upper(),
            human_input_mode='NEVER',
            llm_config=self.llm_config,
        )

        reviewer_agent = ConversableAgent(
            name='reviewer_agent',
            system_message=reviewer_message,
            description='Provides one round of feedback to plans back to the planner before requiring the human validator.',
            llm_config=self.llm_config,
        )

        expert_agent = ConversableAgent(
            name='expert_agent',
            system_message=expert_message,
            description='Provides guidance on the topic and content, if required.',
            llm_config=self.llm_config,
        )

        human_validator = UserProxyAgent(
            name='human_validator',
            system_message='You are the human-in-the-loop. You provide final approval. Review the plan and feedback. Reply "APPROVED" to approve, or provide specific instructions for revision.',
            description='Evaluates the proposed plan and either approves it or requests revisions.',
            code_execution_config=False
        )

        auto_selection = AutoPattern(
            agents=[expert_agent, planner_agent, reviewer_agent],
            initial_agent=expert_agent,
            user_agent=human_validator,
            group_manager_args={'name': 'group_manager', 'llm_config': self.llm_config},
        )

        response = run_group_chat(
            pattern=auto_selection,
            messages=prompt,
            max_rounds=self.max_calls,
        )

        response.process()
        self.logger.info('Final output:\n%s', response.summary)

    @staticmethod
    def _get_allowed_extensions() -> set:

        return {'.py', '.c', '.ipynb'}

    @staticmethod
    def _get_absolute_path(relative_path: str) -> str:

        base_dir = '/my_files'

        if relative_path.startswith('/'):
            relative_path = relative_path[1:]

        return os.path.normpath(os.path.join(base_dir, relative_path))

    @staticmethod
    def _find_file_path(file_name: Annotated[str, 'The name of the file to find, e.g., main.c']) -> str:

        directory_path = '/my_files'
        ext = os.path.splitext(file_name)[1]

        if ext not in AgenticGemini._get_allowed_extensions():
            return f'Error: File type {ext} is not allowed. Only .py, .c, and .ipynb are supported.'

        if not os.path.isdir(directory_path):
            return f'Error: Search directory not found or is not a directory: {directory_path}'

        for root, dirs, files in os.walk(directory_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            files = [f for f in files if not f.startswith('.')]

            if file_name in files:
                full_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(full_path, directory_path)

                return relative_path

        return f'Error: File not found: {file_name} within {directory_path}'

    @staticmethod
    def _read_file_content(relative_path: Annotated[str, 'The relative path from /my_files']) -> str:

        absolute_path = AgenticGemini._get_absolute_path(relative_path)
        ext = os.path.splitext(absolute_path)[1]

        if ext not in AgenticGemini._get_allowed_extensions():
            return f'Error: File type {ext} is not allowed. Only .py, .c, and .ipynb are supported.'

        if not absolute_path.startswith('/my_files'):
            return 'Error: Path traversal detected. Access denied.'

        if not os.path.exists(absolute_path):
            return f'Error: File not found at path: {absolute_path}'

        try:
            if ext == '.ipynb':
                with open(absolute_path, 'r', encoding='utf-8') as f:
                    notebook = nbformat.read(f, as_version=4)

                code_content = []

                for cell in notebook.cells:
                    if cell.cell_type == 'code':
                        code_content.append(cell.source)

                if not code_content:
                    return 'Notebook contains no code cells.'

                return '\n\n# --- New Code Cell ---\n\n'.join(code_content)

            else:
                with open(absolute_path, 'r') as f:
                    content = f.read()

                return content

        except Exception as e:
            return f'Error reading file: {str(e)}'

    @staticmethod
    def _write_file_content(relative_path: Annotated[str, 'The relative path from /my_files'],
                            content: Annotated[str, 'The new content to write to the file']) -> str:

        absolute_path = AgenticGemini._get_absolute_path(relative_path)
        ext = os.path.splitext(absolute_path)[1]

        if ext not in AgenticGemini._get_allowed_extensions():
            return f'Error: File type {ext} is not allowed. Only .py, .c, and .ipynb are supported.'

        if not absolute_path.startswith('/my_files'):
            return 'Error: Path traversal detected. Access denied.'

        if os.path.basename(absolute_path).startswith('.'):
            return 'Error: Cannot edit hidden files.'

        print(f'VERIFICATION REQUIRED: Agent wants to OVERWRITE/EDIT file: {absolute_path}')
        user_verification = input('Type "YES" to confirm: ')

        if user_verification != 'YES':
            return 'Error: User denied the operation.'

        try:
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

            if ext == '.ipynb':
                notebook = new_notebook()
                code_cell = new_code_cell(content)
                notebook.cells.append(code_cell)

                with open(absolute_path, 'w', encoding='utf-8') as f:
                    nbformat.write(notebook, f)

            else:
                with open(absolute_path, 'w') as f:
                    f.write(content)

            return f'Successfully wrote to {absolute_path}'

        except Exception as e:
            return f'Error writing file: {str(e)}'

    @staticmethod
    def _create_file(relative_path: Annotated[str, 'The path of the new file']) -> str:

        absolute_path = AgenticGemini._get_absolute_path(relative_path)
        ext = os.path.splitext(absolute_path)[1]

        if ext not in AgenticGemini._get_allowed_extensions():
            return f'Error: File type {ext} is not allowed. Only .py, .c, and .ipynb are supported.'

        if not absolute_path.startswith('/my_files'):
            return 'Error: Path traversal detected. Access denied.'

        if os.path.basename(absolute_path).startswith('.'):
            return 'Error: Cannot create hidden files.'

        print(f'VERIFICATION REQUIRED: Agent wants to CREATE file: {absolute_path}')
        user_verification = input('Type "YES" to confirm: ')

        if user_verification != 'YES':
            return 'Error: User denied the operation.'

        try:
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

            with open(absolute_path, 'w') as f:
                pass

            return f'Successfully created file {absolute_path}'

        except Exception as e:
            return f'Error creating file: {str(e)}'

    @staticmethod
    def _create_directory(relative_path: Annotated[str, 'The directory path to create inside /my_files']) -> str:

        absolute_path = AgenticGemini._get_absolute_path(relative_path)

        if not absolute_path.startswith('/my_files'):
            return 'Error: Path traversal detected. Access denied.'

        if os.path.basename(absolute_path).startswith('.'):
            return 'Error: Cannot create hidden directories.'

        print(f'VERIFICATION REQUIRED: Agent wants to CREATE directory: {absolute_path}')
        user_verification = input('Type "YES" to confirm: ')

        if user_verification != 'YES':
            return 'Error: User denied the operation.'

        try:
            os.makedirs(absolute_path, exist_ok=True)

            return f'Successfully created directory {absolute_path}'

        except Exception as e:
            return f'Error creating directory: {str(e)}'

    @staticmethod
    def _delete_item(relative_path: Annotated[str, 'The path to the file or directory to delete']) -> str:

        absolute_path = AgenticGemini._get_absolute_path(relative_path)

        if not absolute_path.startswith('/my_files'):
            return 'Error: Path traversal detected. Access denied.'

        if os.path.basename(absolute_path).startswith('.'):
            return 'Error: Cannot delete hidden files or directories.'

        if not os.path.exists(absolute_path):
            return f'Error: Path not found: {absolute_path}'

        print(f'VERIFICATION REQUIRED: Agent wants to DELETE: {absolute_path}')
        user_verification = input('Type "YES" to confirm: ')

        if user_verification != 'YES':
            return 'Error: User denied the operation.'

        try:
            if os.path.isdir(absolute_path):
                shutil.rmtree(absolute_path)
            else:
                os.remove(absolute_path)

            return f'Successfully deleted {absolute_path}'

        except Exception as e:
            return f'Error deleting item: {str(e)}'

    @staticmethod
    def _copy_file(relative_path: Annotated[str, 'The path to the file or directory to copy to clipboard']) -> str:

        absolute_path = AgenticGemini._get_absolute_path(relative_path)

        if not absolute_path.startswith('/my_files'):
            return 'Error: Path traversal detected. Access denied.'

        if os.path.basename(absolute_path).startswith('.'):
            return 'Error: Cannot copy hidden files or directories.'

        if not os.path.exists(absolute_path):
            return f'Error: Path not found: {absolute_path}'

        print(f'VERIFICATION REQUIRED: Agent wants to COPY to clipboard: {absolute_path}')
        user_verification = input('Type "YES" to confirm: ')

        if user_verification != 'YES':
            return 'Error: User denied the operation.'

        AgenticGemini._clipboard_src = absolute_path
        AgenticGemini._clipboard_op = 'COPY'

        return f'Item copied to clipboard: {absolute_path}. Use paste_file to complete operation.'

    @staticmethod
    def _cut_file(relative_path: Annotated[str, 'The path to the file or directory to cut (move) to clipboard']) -> str:

        absolute_path = AgenticGemini._get_absolute_path(relative_path)

        if not absolute_path.startswith('/my_files'):
            return 'Error: Path traversal detected. Access denied.'

        if os.path.basename(absolute_path).startswith('.'):
            return 'Error: Cannot cut hidden files or directories.'

        if not os.path.exists(absolute_path):
            return f'Error: Path not found: {absolute_path}'

        print(f'VERIFICATION REQUIRED: Agent wants to CUT to clipboard: {absolute_path}')
        user_verification = input('Type "YES" to confirm: ')

        if user_verification != 'YES':
            return 'Error: User denied the operation.'

        AgenticGemini._clipboard_src = absolute_path
        AgenticGemini._clipboard_op = 'CUT'

        return f'Item cut to clipboard: {absolute_path}. Use paste_file to complete operation.'

    @staticmethod
    def _paste_file(relative_destination_path: Annotated[str, 'The destination path to paste the clipboard item']) -> str:

        if not AgenticGemini._clipboard_src or not AgenticGemini._clipboard_op:
            return 'Error: Clipboard is empty. Use copy_file or cut_file first.'

        dest_path = AgenticGemini._get_absolute_path(relative_destination_path)

        if not dest_path.startswith('/my_files'):
            return 'Error: Path traversal detected. Access denied.'

        if os.path.basename(dest_path).startswith('.'):
            return 'Error: Cannot paste to hidden files or directories.'

        if not os.path.exists(AgenticGemini._clipboard_src):
            AgenticGemini._clipboard_src = None
            AgenticGemini._clipboard_op = None

            return 'Error: Source item no longer exists.'

        print(f'VERIFICATION REQUIRED: Agent wants to PASTE ({AgenticGemini._clipboard_op}) from {AgenticGemini._clipboard_src} to {dest_path}')
        user_verification = input('Type "YES" to confirm: ')

        if user_verification != 'YES':
            return 'Error: User denied the operation.'

        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            if AgenticGemini._clipboard_op == 'COPY':
                if os.path.isdir(AgenticGemini._clipboard_src):
                    shutil.copytree(AgenticGemini._clipboard_src, dest_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(AgenticGemini._clipboard_src, dest_path)

                return f'Successfully copied to {dest_path}'

            elif AgenticGemini._clipboard_op == 'CUT':
                shutil.move(AgenticGemini._clipboard_src, dest_path)
                AgenticGemini._clipboard_src = None
                AgenticGemini._clipboard_op = None

                return f'Successfully moved to {dest_path}'

            return 'Error: Unknown clipboard operation.'

        except Exception as e:
            return f'Error pasting item: {str(e)}'

    def run_tool_use_chat(self):

        self.logger.info('Running: Tool Use Chat (Find, Read, Edit, Run Files)')

        prompt = input(
            'Enter your prompt (e.g., "Find main.c, read it, and then run it"): '
        )

        system_message = (
            'You are an assistant that uses tools. You can only interact with files ending in `.py`, `.c`, or `.ipynb`.\n'
            'You have 9 tools: `_find_file_path`, `_read_file_content`, `_write_file_content`, `_create_file`, `_create_directory`, `_delete_item`, `_copy_file`, `_cut_file`, `_paste_file`.\n'
            'All file tools operate on the `/my_files` directory.\n'
            'Dangerous operations (Write, Create, Delete, Copy, Cut, Paste) will prompt the user for manual verification. If denied, handle the error gracefully.\n'
            '`_find_file_path` returns a relative path. Hidden files are ignored.\n'
            '`_delete_item` permanently removes files or directories. Hidden files cannot be deleted.\n'
            'To move or copy files, use the clipboard: `_copy_file`/`_cut_file` -> `_paste_file`.\n'
            'To *run* a file, you do not have a tool. Instead, you must **reply with a shell code block** (starting with ```sh) for the executor to run.\n'
            '**CRITICAL: You must act as the user for any interactive script.**\n'
            'If a script requires input, pipe it using `printf` or `echo`.\n'
            '**You can ONLY execute .py (Python) files. You CANNOT execute .c or .ipynb files.**\n'
            '**You must not call a tool named "run_code".**\n'
            '**Do NOT use shell commands for file manipulation (rm, mkdir, touch, cp, mv). Use the provided tools.**\n'
            'The script will be executed with `/my_files` as the working directory, so use relative paths.\n'
            'When the operation is successful and the task is done, reply with TERMINATE.'
        )

        tool_agent = ConversableAgent(
            name='tool_agent',
            system_message=system_message,
            llm_config=self.llm_config,
        )

        executor_agent = UserProxyAgent(
            name='executor_agent',
            human_input_mode='NEVER',
            llm_config=self.llm_config,
            code_execution_config={'work_dir': '/my_files', 'use_docker': False},
            is_termination_msg=lambda x: 'TERMINATE' in (x.get('content', '') or '').upper()
        )

        register_function(
            self._find_file_path,
            caller=tool_agent,
            executor=executor_agent,
            description='Find the relative path of a file (must be .py, .c, or .ipynb) by searching the /my_files directory',
        )

        register_function(
            self._read_file_content,
            caller=tool_agent,
            executor=executor_agent,
            description='Read the content of a file, given its relative path. Special handling for .ipynb to extract code.',
        )

        register_function(
            self._write_file_content,
            caller=tool_agent,
            executor=executor_agent,
            description='Write (or overwrite) content to a file (.py, .c, or .ipynb), given its relative path from /my_files',
        )

        register_function(
            self._create_file,
            caller=tool_agent,
            executor=executor_agent,
            description='Create a new empty file (.py, .c, or .ipynb), given its relative path from /my_files',
        )

        register_function(
            self._create_directory,
            caller=tool_agent,
            executor=executor_agent,
            description='Create a new directory, given its relative path from /my_files',
        )

        register_function(
            self._delete_item,
            caller=tool_agent,
            executor=executor_agent,
            description='Permanently delete a file or directory, given its relative path from /my_files',
        )

        register_function(
            self._copy_file,
            caller=tool_agent,
            executor=executor_agent,
            description='Copy a file/directory to the clipboard.',
        )

        register_function(
            self._cut_file,
            caller=tool_agent,
            executor=executor_agent,
            description='Cut (move) a file/directory to the clipboard.',
        )

        register_function(
            self._paste_file,
            caller=tool_agent,
            executor=executor_agent,
            description='Paste the item currently in the clipboard to a new destination.',
        )

        chat_result = executor_agent.initiate_chat(
            recipient=tool_agent,
            message=prompt,
            max_turns=self.max_calls,
        )

        self.logger.info('Final output:\n%s', chat_result.chat_history[-1]['content'])


if __name__ == '__main__':
    CONFIG_PATH = 'config_path.json'
    MAX_CALLS = 15

    try:
        with open(CONFIG_PATH, 'r') as f:
            app_config = json.load(f)

        config_list_path = app_config['config_path']
        gemini = AgenticGemini(config_path=config_list_path, max_calls=MAX_CALLS)

    except Exception as e:
        print(f'Failed to initialize. Ensure "{CONFIG_PATH}" exists and is valid,')
        print('and that the path inside it is correct.')
        print(f'Error: {e}')
        exit()

    while True:
        print('\n--- Agentic Gemini Menu ---')
        print('1. Basic Code Agent (User -> Assistant w/ Code)')
        print('2. Coder vs. Reviewer Chat')
        print('3. Orchestrated Group Chat (Manager, Planner, Reviewer)')
        print('4. Group Chat with Human-in-the-Loop (Expert, Planner, Reviewer, Human)')
        print('5. Tool Use Chat (Find, Read, Edit, Run, Create, Delete, Copy/Cut/Paste)')
        print('6. Exit')

        choice = input('Enter your choice (1-6): ')

        if choice == '1':
            gemini.run_basic_code_agent()

        elif choice == '2':
            gemini.run_coder_reviewer_chat()

        elif choice == '3':
            gemini.run_group_chat_auto()

        elif choice == '4':
            gemini.run_human_in_the_loop_chat()

        elif choice == '5':
            gemini.run_tool_use_chat()

        elif choice == '6':
            print('Exiting...')
            break

        else:
            print('Invalid choice. Please select a number between 1 and 6.')