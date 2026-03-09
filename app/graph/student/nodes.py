"""Student sub-graph nodes."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from app.config import settings
from app.models.state import ConversationState
from app.prompts.composer import compose_system_prompt
from app.tools.notify_advisor import notify_advisor


async def _student_node(state: ConversationState, phase: str) -> dict:
    """Generic handler for student phases."""
    system_prompt = await compose_system_prompt("student", phase)

    llm = ChatOpenAI(model=settings.main_model, temperature=0.5)
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

    response = await llm.ainvoke(messages)

    return {
        "messages": [response],
        "bot_response": response.content,
    }


async def identify_issue_node(state: ConversationState) -> dict:
    result = await _student_node(state, "identify_issue")
    result["issue_identified"] = True
    result["phase"] = "provide_info"
    return result


async def provide_info_node(state: ConversationState) -> dict:
    result = await _student_node(state, "provide_info")
    result["info_provided"] = True
    return result


async def escalate_node(state: ConversationState) -> dict:
    """Escalate to human support when the bot can't resolve."""
    result = await _student_node(state, "escalate")

    await notify_advisor.ainvoke({
        "contact_id": state["contact_id"],
        "contact_name": state.get("contact_name", ""),
        "user_type": "student",
        "context": f"Alumno necesita ayuda que el bot no pudo resolver. Programa: {state.get('program', 'desconocido')}",
    })
    result["phase"] = "escalate"
    return result
