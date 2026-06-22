import os

from groq import Groq


class GroqRAG:

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not configured"
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model = "llama-3.1-8b-instant"

    def answer(
        self,
        query: str,
        contexts: list[str]
    ):

        context_text = "\n".join(contexts)

        prompt = f"""
You are a Delhi Government citizen grievance assistant.

Use the supplied context.

Context:
{context_text}

Question:
{query}

If the context is insufficient,
say so explicitly.
If the query seems informative like "how do i deal with floods" or "what to do",

then, give three points that are relevant to the query and helps the citizen have their first aid.



Provide a concise answer.

Answer:
"""

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Answer only from supplied context."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content