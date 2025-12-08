def format_cohere_answers_with_citations(message: str, citations: list) -> str:

  # Sort citations by start position in reverse order
    # This ensures we can insert citation markers without affecting positions
    sorted_citations = sorted(citations, key=lambda x: x.start, reverse=True)
    
    # Track unique document sources and assign citation numbers
    doc_to_citation_num = {}
    citation_counter = 1
    
    # Build a mapping of text spans to citation numbers
    text_to_citation = {}
    
    for citation in sorted_citations:
        # Get document IDs for this citation
        doc_ids = tuple(source.id for source in citation.sources)
        
        # Assign citation number if not already assigned
        if doc_ids not in doc_to_citation_num:
            doc_to_citation_num[doc_ids] = citation_counter
            citation_counter += 1
        
        text_to_citation[citation.text] = {
            'num': doc_to_citation_num[doc_ids],
            'start': citation.start,
            'end': citation.end,
            'sources': citation.sources
        }
    
    # Insert citation markers into the message
    formatted_message = message
    for citation in sorted_citations:
        citation_info = text_to_citation[citation.text]
        citation_num = citation_info['num']
        
        # Insert citation marker after the cited text
        formatted_message = (
            formatted_message[:citation.end] + 
            f" [{citation_num}]" + 
            formatted_message[citation.end:]
        )
    
    # Build the references section
    references = ["\n\n---\n**References:**\n"]
    
    # Sort by citation number for the references section
    sorted_refs = sorted(doc_to_citation_num.items(), key=lambda x: x[1])
    
    for doc_ids, num in sorted_refs:
        # Find the first citation with these doc_ids to get source details
        source_info = None
        for citation in citations:
            citation_doc_ids = tuple(source.id for source in citation.sources)
            if citation_doc_ids == doc_ids:
                source_info = citation.sources
                break
        
        if source_info:
            # Format document titles and snippets
            doc_list = []
            for source in source_info:
                title = source.document.get('title', 'Untitled Document')
                # Include snippet preview (first 40 chars)
                snippet = source.document.get('snippet', '')
                snippet_preview = snippet[:40].strip() + "..." if len(snippet) > 40 else snippet.strip()
                doc_list.append(f"{title}: \"{snippet_preview}\"")
            
            references.append(f"[{num}]\n" + "\n".join(doc_list) + "\n")
    
    return formatted_message + "\n".join(references)
