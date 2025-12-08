import os
from typing import Dict, Any, List, Optional
import cohere
################################################################################
from src.system_query.class_SystemDescription import SystemDescription
from .search_vectorstore import search_system_vectorstore
from .format_cohere_answers_with_citations import format_cohere_answers_with_citations
################################################################################

_augmented_user_prompt = """
    The following is a detailed description of the system:
    {system_context}
    You are a security analysis assistant and you provide security assessments for enterprise systems.
    A developer trying to secure this specific system has asked you the following question:
    {user_prompt}
    Based on the system description, provide a detailed and accurate answer.
    Mention specific details from the system description to support your answer.

    Provide examples to support your answer. Compose your answer in the following format:
    -1. Start with a brief summary of the system.
    -2. Provide a detailed answer to the user's question, citing the reference material provided below to the extent possible.
    -3. Provide a list of recommendations 
    -4. Provide clues with regards to which information regarding the system is currently missing 
    that could help you provide a better answer, encourage the user to add that information to the system description.
"""
_no_citation_user_prompt = """
    IMPORTANT: Use only the information provided in the reference material below to answer the question and cite it specifically whenever
    you do so.
    
    BEGIN REFERENCE MATERIAL:
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
    conversation: Optional[List[Dict[str, Any]]] = None,
    citation_mode: bool = True 
) -> Dict[str, Any]:
   
    try:
        system_context = _build_system_context(system)
        docs = search_system_vectorstore(
            vectorstore_path=os.getenv("VECTORSTORE_PATH", "vectorstore/") + system.name + "/",
            query=user_prompt,
            top_k=15
        )
        if citation_mode:
            cohere_docs = [{
                "data": {
                    "title": doc.metadata.get("source_file", "Untitled") + "- page " + str(doc.metadata.get("page", "???")  ),
                    "content": doc.page_content
                }} for doc, _ in docs
            ]
    except Exception as e:
        error_message = f"Failed to process system tool: {str(e)}"
        raise Exception(error_message) from e
    

    full_prompt = _augmented_user_prompt.format(
        system_context=system_context,
        user_prompt=user_prompt
    )
    if not citation_mode:
        full_prompt = _no_citation_user_prompt.format( reference_material="\n".join([doc.page_content for doc, _ in docs])) 

    try:
        messages = [
            {"role": "system", "content": "You are a helpful security analysis assistant."},
            {"role": "user", "content": full_prompt}
        ]
        cohere_api_key = os.getenv("COHERE_API_KEY")
        co = cohere.ClientV2(api_key=cohere_api_key)
        if citation_mode:
            response = co.chat(
                messages=messages, 
                temperature=0.7,
                model="command-a-03-2025",
                documents=cohere_docs,
                citation_options={"mode": "fast"}
            )
        else:
            response = co.chat(
                messages=messages, 
                temperature=0.7,
                model="command-a-03-2025"
            )
    except Exception as e:
        error_message = f"Failed to process system tool: {str(e)}"
        raise Exception(error_message) from e

    answer = response.message.content[0].text
    if citation_mode:
        citations = response.message.citations
        answer = format_cohere_answers_with_citations(answer, citations)
    
    result = {
        "action": "process_system",
        "system_name": system.name,
        "user_prompt": user_prompt,
        "processed_at": system.updated_at.isoformat(),
        "conversation_received": conversation,
        "answer": answer
    }

    return result
