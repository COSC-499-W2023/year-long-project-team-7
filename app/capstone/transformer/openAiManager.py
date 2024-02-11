import typing
from openai import OpenAI
from django.conf import settings
from .models import File
from tenacity import retry, stop_after_attempt, wait_random_exponential
import re
from .prompts import *


class OpenAiManager:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, organization="org-hYPJO2WKqFAN1o75AdfdfeBx")  # type: ignore

    def setup_assistant(
        self,
        input_file_paths: list[str],
        user_parameters: dict[str, typing.Union[str, int]],
    ) -> None:
        instructions = PRESENTATION.format(
            tone=user_parameters["tone"],
            language=user_parameters["language"],
            complexity=user_parameters["complexity"],
            prompt=user_parameters["prompt"],
        )

        self.openai_files = []
        for path in input_file_paths:
            self.openai_files.append(
                self.client.files.create(file=open(path, "rb"), purpose="assistants")
            )

        self.assistant = self.client.beta.assistants.create(
            instructions=instructions,
            tools=[{"type": "retrieval"}],
            model=settings.OPENAI_MODEL,  # type: ignore
            file_ids=[file.id for file in self.openai_files],
        )

    def prompt_assistant(self, proompt: str) -> str:
        thread = self.create_thread()
        self.add_message_to_thread(thread.id, proompt)
        run = self.create_run(thread.id)

        while run.status != "completed":
            run = self.retrieve_run(thread.id, run.id)
            if run.status == "failed":
                if run.last_error:
                    print(run.last_error.message)
                    return str(run.last_error.message)

        messages = []

        for msg in self.list_messages(thread.id):
            if msg.role == "assistant":
                content = msg.content[0]
                if hasattr(content, "text"):
                    messages.append(
                        re.sub(r"【.*】", "", content.text.value)
                    )  # Remove source links

        self.delete_thread(thread.id)
        return "\n".join(messages)

    def __del__(self) -> None:
        for file in self.openai_files:
            self.delete_file(file.id)

        self.delete_assistant(self.assistant.id)

    # REQUESTS WITH EXPONENTIAL BACKOFF
    # All requests need to be done like this to deal with rate-limiting
    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def add_message_to_thread(self, thread_id: str, content: str) -> None:
        self.client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=content
        )

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def create_thread(self):  # type: ignore
        return self.client.beta.threads.create()

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def create_run(self, thread_id: str):  # type: ignore
        return self.client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=self.assistant.id
        )

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def retrieve_run(self, thread_id: str, run_id: str):  # type: ignore
        return self.client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_id
        )

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_messages(self, thread_id: str):  # type: ignore
        return self.client.beta.threads.messages.list(thread_id=thread_id)

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_thread(self, thread_id: str) -> None:
        self.client.beta.threads.delete(thread_id=thread_id)

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_files(self):  # type: ignore
        return self.client.files.list()

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_file(self, file_id: str) -> None:
        self.client.files.delete(file_id)

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_assistants(self):  # type: ignore
        return self.client.beta.assistants.list(limit=100).data

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_assistant(self, assistant_id: str) -> None:
        self.client.beta.assistants.delete(assistant_id)
