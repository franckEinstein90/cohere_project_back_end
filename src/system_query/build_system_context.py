from src.system_query.class_SystemDescription import SystemDescription

def build_system_context(system: SystemDescription) -> str:
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