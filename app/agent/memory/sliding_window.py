"""
ARIA — Sliding Window Memory
Fenêtre glissante + compression avec overlap pour maintenir le contexte global.
"""

from __future__ import annotations

from typing import List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from agent.llm_provider.base_llm import BaseLLMProvider


COMPRESSION_PROMPT = """Compresse cet historique de conversation en un résumé dense et factuel.
Préserve : décisions prises, données clés, domaine analysé, erreurs et résolutions.
Sois concis. Ne perds aucune information critique."""


class SlidingWindowMemory:
    """
    Fenêtre glissante avec compression LLM.

    - window_size  : messages récents conservés intacts (défaut 10)
    - overlap      : messages de chevauchement inclus dans la compression (défaut 2)
    - max_messages : seuil déclenchant la compression (défaut 20)
    """

    def __init__(
        self,
        window_size:  int = 10,
        overlap:      int = 2,
        max_messages: int = 20,
        llm_provider: Optional[BaseLLMProvider] = None,
    ):
        self.window_size  = window_size
        self.overlap      = overlap
        self.max_messages = max_messages
        self._llm         = llm_provider or BaseLLMProvider(
            system_prompt=COMPRESSION_PROMPT,
            temperature=0.2,
            max_tokens=1024,
        )
        self._summary = ""

    def process(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """Retourne la fenêtre active précédée du résumé si compression nécessaire."""
        if len(messages) <= self.max_messages:
            return messages

        active_window = messages[-self.window_size:]
        to_compress   = messages[:len(messages) - self.window_size + self.overlap]

        history_text = "\n".join(
            f"[{msg.__class__.__name__.replace('Message','').upper()}]: {str(msg.content)[:500]}"
            for msg in to_compress
        )

        prompt = f"RÉSUMÉ EXISTANT :\n{self._summary}\n\n" if self._summary else ""
        prompt += f"MESSAGES À COMPRESSER :\n{history_text}"

        self._summary = self._llm.invoke(prompt)

        return [SystemMessage(content=f"[CONTEXTE PRÉCÉDENT]\n{self._summary}")] + list(active_window)


def apply_sliding_window(
    messages:     List[BaseMessage],
    window_size:  int = 10,
    overlap:      int = 2,
    max_messages: int = 20,
    llm_provider: Optional[BaseLLMProvider] = None,
) -> List[BaseMessage]:
    """Applique la fenêtre glissante — à appeler en début de node."""
    return SlidingWindowMemory(window_size, overlap, max_messages, llm_provider).process(messages)


if __name__ == "__main__":
    print("=== SlidingWindowMemory — Test rapide ===\n")

    messages = []
    for i in range(25):
        messages.append(HumanMessage(content=f"Message utilisateur {i+1}"))
        messages.append(AIMessage(content=f"Réponse agent {i+1}"))

    print(f"Messages initiaux : {len(messages)}")

    try:
        manager = SlidingWindowMemory(window_size=10, overlap=2, max_messages=20)
        result  = manager.process(messages)
        print(f"Messages après fenêtrage : {len(result)}")
        print(f"Premier message : {result[0].__class__.__name__} — {str(result[0].content)[:100]}")
        print("\n✅ Test terminé.")
    except Exception as e:
        print(f"❌ Erreur : {e}")