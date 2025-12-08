import os
from typing import Dict, Any, List, Optional
import cohere
################################################################################
from src.system_query.class_SystemDescription import SystemDescription
from .search_vectorstore import search_system_vectorstore
################################################################################

_augmented_user_prompt = """
    The following is a detailed description of the system:
    {system_context}
    You are a security analysis assistant and you provide security assessments for enterprise systems.
    A developer trying to secure this specific system has asked you the following question:
    {user_prompt}
    Based on the system description, provide a detailed and accurate answer.
    Mention specific details from the system description to support your answer.
    Provice examples to support your answer. Compose your answer in the following format:
    -1. Start with a brief summary of the system.
    -2. Provide a detailed answer to the user's question, citing the reference material provided below to the extent possible.
    -3. Provide a list of recommendations 
    4. Provide cludes with regards to which information regarding the system is currently missing 
    that could help you provide a better answer, encourage the user to add that infroamtion to the system description.
    Reference Material:
    {reference_material}
"""

def _build_system_context(system: SystemDescription) -> str:
    context_parts = [
        f"System Name: {system.name}",
        f"Business Function: {system.business_function}",
    ]
    if system.cloud_provider:
        context_parts.append(f"Cloud Provider: {system.cloud_provider}")
    if system.region:
        context_parts.append(f"Region: {system.region}")
    if system.onprem_details:
        context_parts.append(f"On-Premises Details: {system.onprem_details}")
    if system.freeform_description:
        context_parts.append(f"Description: {system.freeform_description}")
    
    return "\n".join(context_parts)


def process_system_tool(
    system: SystemDescription, 
    user_prompt: str, 
    conversation: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
   
    try:
        system_context = _build_system_context(system)
        docs = search_system_vectorstore(
            vectorstore_path=os.getenv("VECTORSTORE_PATH", "vectorstore/") + system.name + "/",
            query=user_prompt,
            top_k=5
        )
    except Exception as e:
        error_message = f"Failed to process system tool: {str(e)}"
        raise Exception(error_message) from e
    

    full_prompt = _augmented_user_prompt.format(
        system_context=system_context,
        user_prompt=user_prompt,
        reference_material="\n".join([doc.page_content for doc, _ in docs])
    )
    try:
        messages = [
            {"role": "system", "content": "You are a helpful security analysis assistant."},
            {"role": "user", "content": full_prompt}
        ]
        cohere_api_key = os.getenv("COHERE_API_KEY")
        co = cohere.ClientV2(api_key=cohere_api_key)
        response = co.chat(
            messages=messages, 
            temperature=0.7,
            model="command-a-03-2025"
        )
    except Exception as e:
        error_message = f"Failed to process system tool: {str(e)}"
        raise Exception(error_message) from e

    answer = response.message.content[0].text
    result = {
        "action": "process_system",
        "system_name": system.name,
        "user_prompt": user_prompt,
        "processed_at": system.updated_at.isoformat(),
        "note": "This is a stubbed response. Replace with real processing.",
        "conversation_received": conversation,
        "answer": answer
    }

    return result
