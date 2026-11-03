import os

from typing import List, Dict
from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


class QueryRewriter:

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash"
    ):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing.")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def rewrite_question(
        self,
        question: str,
        history: List[Dict]
    ) -> str:

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        if not history:
            return question

        conversation = []

        for message in history:
            role = message["role"].upper()
            content = message["content"]

            conversation.append(
                f"{role}: {content}"
            )

        conversation_text = "\n".join(conversation)

        prompt = f"""
You are a query rewriting assistant for a codebase RAG system.

Your task is to convert the latest user question into a
standalone question using the conversation history.

CONVERSATION HISTORY:

{conversation_text}

LATEST USER QUESTION:

{question}

RULES:

1. Resolve references such as "it", "this", "that function",
   and "where is it" using conversation history.
2. Preserve the original intent of the latest question.
3. Do not answer the question.
4. Do not invent implementation details.
5. Do not add unrelated information.
6. If the latest question is already standalone, return it unchanged.
7. Return only the rewritten question.
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=256
            )
        )

        if not response.text:
            return question

        return response.text.strip()