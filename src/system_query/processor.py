from typing import Dict, Any, List, Optional
from src.system_query.class_SystemDescription import SystemDescription


def process_system_tool(
    system: SystemDescription, 
    user_prompt: str, 
    conversation: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Process a query for the 'system' tool.

    This is a stubbed processor — replace with real business logic.

    Args:
        system: validated SystemDescription instance
        user_prompt: user's prompt string
        conversation: optional list of prior conversation turns (dicts with role/content)

    Returns:
        A dict containing processing results.
    """
    # Example processing: echo back a structured response including the system name
    result = {
        "action": "process_system",
        "system_name": system.name,
        "user_prompt": user_prompt,
        "processed_at": system.updated_at.isoformat(),
        "note": "This is a stubbed response. Replace with real processing.",
        "conversation_received": conversation,
    }

    return result
