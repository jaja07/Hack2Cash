"""
ARIA — Base LLM Provider
Kimi K2 via NVIDIA API using ChatOpenAI (LangChain-native).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterator, List, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

load_dotenv()

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL   = "moonshotai/kimi-k2-instruct"
DEFAULT_TEMP    = 0.6
DEFAULT_TOKENS  = 4096


def get_nvidia_llm(
    model_name:  str   = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMP,
    max_tokens:  int   = DEFAULT_TOKENS,
) -> ChatOpenAI:
    """Factory — retourne un ChatOpenAI pointé sur l'endpoint NVIDIA."""
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY manquant dans les variables d'environnement.")
    return ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        base_url=NVIDIA_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
    )


class ChatNVIDIA:
    """
    Adapter autour de ChatOpenAI compatible avec create_react_agent.
    Expose invoke, ainvoke, stream, bind_tools.
    """

    def __init__(
        self,
        model_name:  str   = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMP,
        max_tokens:  int   = DEFAULT_TOKENS,
    ):
        self.llm = get_nvidia_llm(model_name, temperature, max_tokens)

    def invoke(self, messages: List[BaseMessage], **kwargs: Any):
        return self.llm.invoke(messages, **kwargs)

    async def ainvoke(self, messages: List[BaseMessage], **kwargs: Any):
        return await self.llm.ainvoke(messages, **kwargs)

    def stream(self, messages: List[BaseMessage], **kwargs: Any):
        return self.llm.stream(messages, **kwargs)

    def bind_tools(self, tools: List[Any], **kwargs: Any):
        return self.llm.bind_tools(tools, **kwargs)

    def __getattr__(self, name: str):
        return getattr(self.llm, name)


class BaseLLMProvider:
    """
    Wrapper haut niveau utilisé par les nodes ARIA.
    Gère l'injection du system prompt, le contexte, et le parsing JSON.
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        model_name:    str   = DEFAULT_MODEL,
        temperature:   float = DEFAULT_TEMP,
        max_tokens:    int   = DEFAULT_TOKENS,
    ):
        self.system_prompt = system_prompt
        self._llm = get_nvidia_llm(model_name, temperature, max_tokens)

    def _build_messages(
        self,
        user_message: str,
        context:    Optional[str]  = None,
        input_data: Optional[Dict] = None,
    ) -> List[BaseMessage]:
        messages: List[BaseMessage] = []
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        prompt = user_message
        if context:
            prompt = f"# CONTEXTE\n{context}\n\n{prompt}"
        if input_data:
            prompt += "\n\n# DONNÉES (JSON):\n" + json.dumps(input_data, indent=2, ensure_ascii=False)
        messages.append(HumanMessage(content=prompt))
        return messages

    @staticmethod
    def _clean_json(raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        return raw.strip()

    def invoke(self, user_message: str, context: Optional[str] = None,
               input_data: Optional[Dict] = None, reset_chat: bool = False) -> str:
        resp = self._llm.invoke(self._build_messages(user_message, context, input_data))
        return getattr(resp, "content", str(resp))

    def invoke_for_json(self, user_message: str, context: Optional[str] = None,
                        input_data: Optional[Dict] = None) -> Optional[Dict]:
        raw = self.invoke(user_message, context, input_data)
        try:
            return json.loads(self._clean_json(raw))
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}\nRéponse brute:\n{raw[:300]}")
            return None

    async def ainvoke(self, user_message: str, context: Optional[str] = None,
                      input_data: Optional[Dict] = None) -> str:
        resp = await self._llm.ainvoke(self._build_messages(user_message, context, input_data))
        return getattr(resp, "content", str(resp))

    def stream(self, user_message: str, context: Optional[str] = None,
               input_data: Optional[Dict] = None) -> Iterator[str]:
        for chunk in self._llm.stream(self._build_messages(user_message, context, input_data)):
            content = getattr(chunk, "content", "")
            if content:
                yield content


if __name__ == "__main__":
    import asyncio

    print("=== ARIA LLM Provider — Test rapide ===\n")

    llm = BaseLLMProvider(
        system_prompt="Tu es un assistant concis. Réponds en une phrase maximum.",
        temperature=0.6,
        max_tokens=128,
    )

    # Test 1 — invoke simple
    print("[1] invoke() :")
    print(llm.invoke("Dis bonjour en français."))

    # Test 2 — invoke_for_json
    print("\n[2] invoke_for_json() :")
    llm_json = BaseLLMProvider(
        system_prompt="Réponds UNIQUEMENT en JSON valide, sans backticks ni texte.",
        temperature=0.2,
        max_tokens=128,
    )
    print(llm_json.invoke_for_json('Retourne {"nom": "ARIA", "version": 1}'))

    print("\n✅ Tests terminés.")