import typing
from openai import OpenAI
from django.conf import settings
from .models import Conversion, File, Exercise
from tenacity import retry, stop_after_attempt, wait_random_exponential
import re
from .prompts import *


class OpenAiManager:
    def __init__(self, input_file_text: str, conversion: Conversion) -> None:
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, organization="org-hYPJO2WKqFAN1o75AdfdfeBx")  # type: ignore

        self.model = conversion.model

        all_files = self.list_files()
        all_assistants = self.list_assistants()
        for file in all_files:
            self.delete_file(file.id)

        for assistant in all_assistants:
            self.delete_assistant(assistant.id)

        self.instructions = SYSTEM_PROMPT.format(
            tone=conversion.tone,
            language=conversion.language,
            complexity=conversion.complexity,
            prompt=conversion.prompt,
            input_file_text=input_file_text,
        )
        self.messages = [{"role": "system", "content": self.instructions}]

    def prompt_chat(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})
        return self.create_chat()

    # REQUESTS WITH EXPONENTIAL BACKOFF
    # All requests need to be done like this to deal with rate-limiting
    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def create_chat(self) -> str:
        return str(
            self.client.chat.completions.create(  # type: ignore
                model=self.model,
                messages=self.messages,
                response_format={"type": "json_object"},
            )
            .choices[0]
            .message.content
        )

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_files(self):  # type: ignore
        return self.client.files.list().data

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_file(self, file_id: str) -> None:
        self.client.files.delete(file_id)

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_assistants(self):  # type: ignore
        return self.client.beta.assistants.list(limit=100).data

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_assistant(self, assistant_id: str) -> None:
        self.client.beta.assistants.delete(assistant_id)


class OpenAiMCQManager:
    def __init__(self, input_file_text: str, exercise: Exercise) -> None:
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, organization="org-hYPJO2WKqFAN1o75AdfdfeBx")  # type: ignore

        self.model = exercise.model

        all_files = self.list_files()
        all_assistants = self.list_assistants()
        for file in all_files:
            self.delete_file(file.id)

        for assistant in all_assistants:
            self.delete_assistant(assistant.id)

        self.instructions = MULTIPLE_CHOICE_PROMPT.format(
            language=exercise.language,
            complexity=exercise.complexity,
            prompt=exercise.prompt,
            input_file_text=input_file_text,
        )
        self.messages = [{"role": "system", "content": self.instructions}]

    def prompt_chat(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})
        return self.create_chat()

    # REQUESTS WITH EXPONENTIAL BACKOFF
    # All requests need to be done like this to deal with rate-limiting
    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def create_chat(self) -> str:
        return str(
            self.client.chat.completions.create(  # type: ignore
                model=self.model,
                messages=self.messages,
                response_format={"type": "json_object"},
            )
            .choices[0]
            .message.content
        )

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_files(self):  # type: ignore
        return self.client.files.list().data

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_file(self, file_id: str) -> None:
        self.client.files.delete(file_id)

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_assistants(self):  # type: ignore
        return self.client.beta.assistants.list(limit=100).data

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_assistant(self, assistant_id: str) -> None:
        self.client.beta.assistants.delete(assistant_id)


class OpenAiTFManager:
    def __init__(self, input_file_text: str, exercise: Exercise) -> None:
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, organization="org-hYPJO2WKqFAN1o75AdfdfeBx")  # type: ignore

        self.model = exercise.model

        all_files = self.list_files()
        all_assistants = self.list_assistants()
        for file in all_files:
            self.delete_file(file.id)

        for assistant in all_assistants:
            self.delete_assistant(assistant.id)

        self.instructions = TRUE_FALSE_PROMPT.format(
            language=exercise.language,
            complexity=exercise.complexity,
            prompt=exercise.prompt,
            input_file_text=input_file_text,
        )
        self.messages = [{"role": "system", "content": self.instructions}]

    def prompt_chat(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})
        return self.create_chat()

    # REQUESTS WITH EXPONENTIAL BACKOFF
    # All requests need to be done like this to deal with rate-limiting
    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def create_chat(self) -> str:
        return str(
            self.client.chat.completions.create(  # type: ignore
                model=self.model,
                messages=self.messages,
                response_format={"type": "json_object"},
            )
            .choices[0]
            .message.content
        )

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_files(self):  # type: ignore
        return self.client.files.list().data

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_file(self, file_id: str) -> None:
        self.client.files.delete(file_id)

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_assistants(self):  # type: ignore
        return self.client.beta.assistants.list(limit=100).data

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_assistant(self, assistant_id: str) -> None:
        self.client.beta.assistants.delete(assistant_id)


class OpenAiShortAnsManager:
    def __init__(self, input_file_text: str, exercise: Exercise) -> None:
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, organization="org-hYPJO2WKqFAN1o75AdfdfeBx")  # type: ignore

        self.model = exercise.model

        all_files = self.list_files()
        all_assistants = self.list_assistants()
        for file in all_files:
            self.delete_file(file.id)

        for assistant in all_assistants:
            self.delete_assistant(assistant.id)

        self.instructions = SHORT_ANS_PROMPT.format(
            language=exercise.language,
            complexity=exercise.complexity,
            prompt=exercise.prompt,
            input_file_text=input_file_text,
        )
        self.messages = [{"role": "system", "content": self.instructions}]

    def prompt_chat(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})
        return self.create_chat()

    # REQUESTS WITH EXPONENTIAL BACKOFF
    # All requests need to be done like this to deal with rate-limiting
    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def create_chat(self) -> str:
        return str(
            self.client.chat.completions.create(  # type: ignore
                model=self.model,
                messages=self.messages,
                response_format={"type": "json_object"},
            )
            .choices[0]
            .message.content
        )

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_files(self):  # type: ignore
        return self.client.files.list().data

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_file(self, file_id: str) -> None:
        self.client.files.delete(file_id)

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_assistants(self):  # type: ignore
        return self.client.beta.assistants.list(limit=100).data

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_assistant(self, assistant_id: str) -> None:
        self.client.beta.assistants.delete(assistant_id)
