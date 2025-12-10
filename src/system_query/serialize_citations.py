 # Serialize citations properly
def serialize_citations(citations):
    """Serialize citation objects into JSON-serializable format."""
    serializable_citations = []
    for citation in citations:
                        try:
                            # Convert citation to dict, handling nested objects
                            citation_dict = {
                                'start': getattr(citation, 'start', None),
                                'end': getattr(citation, 'end', None),
                                'text': getattr(citation, 'text', None),
                                'sources': []
                            }
                            
                            # Handle sources
                            if hasattr(citation, 'sources'):
                                for source in citation.sources:
                                    if hasattr(source, 'type') and hasattr(source, 'id'):
                                        citation_dict['sources'].append({
                                            'type': source.type,
                                            'id': source.id,
                                            'document': getattr(source, 'document', {})
                                        })
                            
                            serializable_citations.append(citation_dict)
                        except Exception as e:
                            print(f"Warning: Could not serialize citation: {e}")
                            continue
    return serializable_citations