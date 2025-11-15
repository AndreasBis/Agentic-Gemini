import logging
import json
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
            system_message='You are a Python developer. Write short Python scripts.',
            llm_config=self.llm_config,
        )

        reviewer = ConversableAgent(
            name='reviewer',
            system_message='You are a code reviewer. Analyze provided code and suggest improvements. '
                           'Do not generate code, only suggest improvements.',
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
        
        prompt = input('Enter the topic for the lesson plan: ')

        planner_message = 'You are a classroom lesson planner. Given a topic, write a lesson plan for a fourth grade class.'
        reviewer_message = 'You are a classroom lesson reviewer. Compare the plan to the curriculum and suggest up to 3 improvements.'

        lesson_planner = ConversableAgent(
            name='planner_agent',
            system_message=planner_message,
            description='Creates or revises lesson plans.',
            llm_config=self.llm_config,
        )

        lesson_reviewer = ConversableAgent(
            name='reviewer_agent',
            system_message=reviewer_message,
            description='Provides one round of feedback to lesson plans.',
            llm_config=self.llm_config,
        )

        teacher_message = 'You are a classroom teacher. You decide topics and collaborate with planner and reviewer to finalize lesson plans. When satisfied, output DONE!'

        teacher = ConversableAgent(
            name='teacher_agent',
            system_message=teacher_message,
            is_termination_msg=lambda x: 'DONE!' in (x.get('content', '') or '').upper(),
            llm_config=self.llm_config,
        )

        auto_selection = AutoPattern(
            agents=[teacher, lesson_planner, lesson_reviewer],
            initial_agent=lesson_planner,
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
        
        prompt = input('Enter the topic for the lesson plan (human will validate): ')

        planner_message = 'You are a classroom lesson planner. Given a topic, write a lesson plan for a fourth grade class.'
        reviewer_message = 'You are a classroom lesson reviewer. Compare the plan to the curriculum and suggest up to 3 improvements.'
        teacher_message = 'You are an experienced classroom teacher. You don\'t prepare plans, you provide simple guidance to the planner to prepare a lesson plan on the key topic.'

        lesson_planner = ConversableAgent(
            name='planner_agent',
            system_message=planner_message,
            description='Creates or revises lesson plans before having them reviewed.',
            is_termination_msg=lambda x: 'APPROVED' in (x.get('content', '') or '').upper(),
            human_input_mode='NEVER',
            llm_config=self.llm_config,
        )

        lesson_reviewer = ConversableAgent(
            name='reviewer_agent',
            system_message=reviewer_message,
            description='Provides one round of feedback to lesson plans back to the lesson planner before requiring the human validator.',
            llm_config=self.llm_config,
        )

        teacher = ConversableAgent(
            name='teacher_agent',
            system_message=teacher_message,
            description='Provides guidance on the topic and content, if required.',
            llm_config=self.llm_config,
        )

        human_validator = UserProxyAgent(
            name='human_validator',
            system_message='You are a human educator who provides final approval for lesson plans. Reply \'APPROVED\' to approve.',
            description='Evaluates the proposed lesson plan and either approves it or requests revisions, before returning to the planner.',
            code_execution_config=False
        )

        auto_selection = AutoPattern(
            agents=[teacher, lesson_planner, lesson_reviewer],
            initial_agent=teacher,
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
    def _get_weekday(date_string: Annotated[str, 'Format: YYYY-MM-DD']) -> str:

        date = datetime.strptime(date_string, '%Y-%m-%d')

        return date.strftime('%A')

    def run_tool_use_chat(self):

        self.logger.info('Running: Tool Use Chat (Weekday Finder)')
        
        prompt = input(
            'Enter your date question (e.g., \'I was born on 1995-03-25, what day was it?\'): '
        )

        date_agent = ConversableAgent(
            name='date_agent',
            system_message='You find the day of the week for a given date.',
            llm_config=self.llm_config,
        )

        executor_agent = ConversableAgent(
            name='executor_agent',
            human_input_mode='NEVER',
            llm_config=self.llm_config,
        )

        register_function(
            self._get_weekday,
            caller=date_agent,
            executor=executor_agent,
            description='Get the day of the week for a given date',
        )

        chat_result = executor_agent.initiate_chat(
            recipient=date_agent,
            message=prompt,
            max_turns=self.max_calls,
        )
        
        self.logger.info('Final output:\n%s', chat_result.chat_history[-1]['content'])


if __name__ == '__main__':
    CONFIG_PATH = 'config_path.json'
    MAX_CALLS = 4

    try:
        with open(CONFIG_PATH, 'r') as f:
            app_config = json.load(f)
        
        config_list_path = app_config['config_path']
        gemini = AgenticGemini(config_path=config_list_path, max_calls=MAX_CALLS)

    except Exception as e:
        print(f'Failed to initialize. Ensure \'{CONFIG_PATH}\' exists and is valid,')
        print('and that the path inside it is correct.')
        print(f'Error: {e}')
        exit()

    while True:
        print('\n--- Agentic Gemini Menu ---')
        print('1. Basic Code Agent (User -> Assistant w/ Code)')
        print('2. Coder vs. Reviewer Chat')
        print('3. Orchestrated Group Chat (Teacher, Planner, Reviewer)')
        print('4. Group Chat with Human-in-the-Loop')
        print('5. Tool Use Chat (Weekday Finder)')
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