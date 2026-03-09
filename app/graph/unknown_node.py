"""Handler for unknown user type — greeting + wait for context."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from app.config import settings
from app.models.state import ConversationState
from app.prompts.narratives import UNKNOWN_NARRATIVE


async def unknown_node(state: ConversationState) -> dict:
    """Respond with a greeting when we can't classify the user yet."""
    llm = ChatOpenAI(model=settings.fast_model, temperature=0.7)
    messages = [SystemMessage(content=UNKNOWN_NARRATIVE)] + list(state["messages"])

    response = await llm.ainvoke(messages)

    return {
        "messages": [response],
        "bot_response": response.content,
    }
