import os
from typing import Dict, Any, List, Optional
from flask import Response, json, stream_with_context
################################################################################  
import cohere
################################################################################
from src.system_query.class_SystemDescription import SystemDescription
################################################################################
from .search_vectorstore import search_system_vectorstore
from .format_cohere_answers_with_citations import format_cohere_answers_with_citations
################################################################################
from .build_system_context import build_system_context 
from .serialize_citations import serialize_citations
################################################################################

_augmented_user_prompt = """
    The following is a detailed description of the system:

    <SYSTEM_CONTEXT>
    {system_context}
    </SYSTEM_CONTEXT>

    You are a security analysis assistant and you provide security assessments for enterprise systems.
    A developer trying to secure this specific system has asked you the following question:

    <USER_PROMPT>
    {user_prompt}
    </USER_PROMPT>

    Based on the system description, provide a detailed and accurate answer.
    Mention specific details from the system description to support your answer.

    Provide examples to support your answer. Compose your answer in the following format:
    Start by providing a brief description of the system based on the provided system context, and include its name. Then proceed to:

    -1. Provide a detailed answer to the user's question, citing the reference material provided below to the extent 
        possible. Do not make up information that is not in the reference material.

    -2. Provide a list of recommendations with specific actions the developer can take to improve the security posture of the system.

    -3. Provide clues with regards to which information regarding the system is currently missing 
        that could help you provide a better answer, encourage the user to add that information to the system description.


    Remember to provide long and detailed answers, focusing on security best practices and on the specific context of the system, 
    in combination with the user's prompt and implied intent. Finish your answer by proposing  to generate related documents or playbooks
    or plans that could help the developer. For this last section, begin your sentences with "Would you like me to generate...".
"""

_no_citation_user_prompt = """
    IMPORTANT: Use only the information provided in the reference material below to answer the question and cite it specifically whenever
    you do so.
    
    BEGIN REFERENCE MATERIAL:
    {reference_material}
"""



def process_system_tool(
    system: SystemDescription, 
    user_prompt: str, 
    conversation: Optional[List[Dict[str, Any]]] = None,
    citation_mode: bool = True 
) -> Response:

    def generate():

        # Build system context from the system description
        # and search the vectorstore for relevant documents
        try:
            system_context = build_system_context(system)
            docs = search_system_vectorstore(
                query=system_context,
                top_k=35
            )
        except Exception as e:
            error_message = f"Failed to process system tool: {str(e)}"
            yield f"data: {json.dumps({'status': 'error', 'message': error_message})}\n\n"
            return 

        # Initialize Cohere client
        try:    
            cohere_api_key = os.getenv("COHERE_API_KEY")
            co = cohere.ClientV2(api_key=cohere_api_key)  
        except Exception as e:
            error_message = f"Failed to initialize Cohere client: {str(e)}"
            yield f"data: {json.dumps({'status': 'error', 'message': error_message})}\n\n"
            return

        # Rerank documents based on the augmented user prompt
        try:
            full_prompt = _augmented_user_prompt.format(
                system_context=system_context,
                user_prompt=user_prompt
            )
            reranked_docs = [doc.page_content for doc, _ in docs]
            rerank_res = co.rerank(
                model="rerank-v3.5",
                query=full_prompt,
                documents=reranked_docs,
                top_n=15
            )
            selected_docs = []
            for rerank in rerank_res.results:
                index = rerank.index
                selected_docs.append(docs[index])

        except Exception as e:
            error_message = f"Failed to rerank documents for system tool: {str(e)}"
            selected_docs = docs  # Fallback to original docs 

        # Prepare and stream the response from Cohere
        try:
            if not citation_mode:
                full_prompt = _no_citation_user_prompt.format( reference_material="\n".join([doc.page_content for doc, _ in docs]))    
            else:
                cohere_docs = [{
                    "data": {
                        "title": doc.metadata.get("source_file", "Untitled") + "- page " + str(doc.metadata.get("page", "???")  ),
                        "content": doc.page_content
                    }} for doc, _ in selected_docs]

            messages = [
                {"role": "system", "content": "You are a helpful security analysis assistant."},
                {"role": "user", "content": full_prompt}
            ]

            stream = co.chat_stream(
                messages=messages, 
                temperature=0.3,
                model="command-a-03-2025",
                documents=cohere_docs,
                citation_options={"mode": "fast"}
            )  
            
            full_text = ""
            citations = []
            
            # Process the stream
            for event in stream:
                if event.type == "content-delta":
                    # Stream text chunks
                    delta = event.delta.message.content.text
                    full_text += delta
                    yield f"data: {json.dumps({'type': 'content', 'text': delta})}\n\n"
                
                elif event.type == "citation-start":
                    # Collect citation information
                    citation_data = {
                        'start': event.delta.message.citations.start,
                        'end': event.delta.message.citations.end,
                        'sources': event.delta.message.citations.sources,
                        'text': event.delta.message.citations.text
                    }
                    citations.append(citation_data)
                
                elif event.type == "citation-end":
                    pass
                
                elif event.type == "message-end":
                    # Send final message with complete citations
                    if hasattr(event, 'response') and hasattr(event.response.message, 'citations'):
                        citations = event.response.message.citations

                    serialized_citations = serialize_citations(citations) 
                    # Format the final response with citations
                    formatted_response = format_cohere_answers_with_citations(full_text, citations)
                    yield f"data: {json.dumps({'type': 'done', 'formatted': formatted_response, 'citations': serialized_citations})}\n\n"

        except Exception as e:
            error_message = f"Failed to process system tool: {str(e)}"
            yield f"data: {json.dumps({'status': 'error', 'message': error_message})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')