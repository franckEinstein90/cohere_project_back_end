################################################################################
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
################################################################################

class SystemDescription(BaseModel):
    """
    Comprehensive system description for security and compliance documentation.
    """
    
    # Basic Information
    name: str = Field(..., description="System name", min_length=1)
    business_function: str = Field(..., description="Primary business function and purpose", min_length=1)
    
    # Users & Access
    user_types: List[str] = Field(..., description="Types of users who access the system", min_length=1)
    other_user_types: Optional[str] = Field(None, description="Additional user types (comma-separated)")
    internet_exposed: Literal[
        "Yes - Publicly accessible",
        "Yes - Restricted access (VPN, IP whitelist, etc.)",
        "No - Internal only"
    ] = Field(..., description="Internet exposure level")
    auth_methods: List[str] = Field(..., description="Authentication methods used", min_length=1)
    other_auth_methods: Optional[str] = Field(None, description="Additional authentication methods (comma-separated)")
    
    # Infrastructure & Hosting
    hosting_env: Literal["Cloud", "On-Premises", "Hybrid"] = Field(..., description="Hosting environment type")
    cloud_provider: Optional[str] = Field(None, description="Cloud provider (AWS, Azure, GCP, etc.)")
    region: Optional[str] = Field(None, description="Cloud region or geographic location")
    onprem_details: Optional[str] = Field(None, description="On-premises location details")
    
    # Data & Compliance
    data_handled: str = Field(..., description="Types of data stored, processed, or transmitted", min_length=1)
    data_sensitivity: List[str] = Field(..., description="Data sensitivity classifications", min_length=1)
    
    # Security Controls
    security_controls: List[str] = Field(default_factory=list, description="Security controls protecting the system")
    other_security_controls: Optional[str] = Field(None, description="Additional security controls (comma-separated)")
    
    # Dependencies & Business Impact
    dependencies: Optional[str] = Field(None, description="External systems, APIs, and dependencies")
    business_impact: str = Field(..., description="Business impact if system fails or is breached", min_length=1)
    
    # Comprehensive Description
    freeform_description: Optional[str] = Field(None, description="Detailed narrative system description")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "SystemDescription":
        """
        Create a SystemDescription instance from a JSON dictionary.
        
        Args:
            json_data: Dictionary containing system description data
            
        Returns:
            SystemDescription instance
            
        Example:
            >>> system_dict = {
            ...     "name": "Customer Portal",
            ...     "business_function": "Public-facing web portal",
            ...     # ... other fields
            ... }
            >>> system = SystemDescription.from_json(system_dict)
        """
        # Handle datetime fields if they're strings
        if "created_at" in json_data and isinstance(json_data["created_at"], str):
            json_data["created_at"] = datetime.fromisoformat(json_data["created_at"].replace('Z', '+00:00'))
        if "updated_at" in json_data and isinstance(json_data["updated_at"], str):
            json_data["updated_at"] = datetime.fromisoformat(json_data["updated_at"].replace('Z', '+00:00'))
        
        return cls(**json_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemDescription":
        """
        Create a SystemDescription instance from a dictionary.
        Handles datetime conversion automatically.
        
        Args:
            data: Dictionary containing system description data
            
        Returns:
            SystemDescription instance
            
        Example:
            >>> system_dict = {
            ...     "name": "Customer Portal",
            ...     "business_function": "Public-facing web portal",
            ...     "user_types": ["Customers"],
            ...     "internet_exposed": "Yes - Publicly accessible",
            ...     "auth_methods": ["SSO (Single Sign-On)"],
            ...     "hosting_env": "Cloud",
            ...     "data_handled": "Customer data",
            ...     "data_sensitivity": ["PII"],
            ...     "business_impact": "High impact"
            ... }
            >>> system = SystemDescription.from_dict(system_dict)
        """
        # Create a copy to avoid modifying the original
        data_copy = data.copy()
        
        # Handle datetime fields if they're strings
        if "created_at" in data_copy and isinstance(data_copy["created_at"], str):
            data_copy["created_at"] = datetime.fromisoformat(data_copy["created_at"].replace('Z', '+00:00'))
        if "updated_at" in data_copy and isinstance(data_copy["updated_at"], str):
            data_copy["updated_at"] = datetime.fromisoformat(data_copy["updated_at"].replace('Z', '+00:00'))
        
        try:
            return cls(**data_copy)
        except ValidationError as e:
            print("Error creating SystemDescription from dict:", e)
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert SystemDescription to a dictionary suitable for JSON serialization.
        
        Returns:
            Dictionary with datetime objects converted to ISO format strings
        """
        data = self.model_dump()
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Customer Portal",
                "business_function": "Public-facing web application for customers to view and manage their insurance policies",
                "user_types": ["Customers", "Public Users"],
                "other_user_types": "Insurance Agents",
                "internet_exposed": "Yes - Publicly accessible",
                "auth_methods": ["SSO (Single Sign-On)", "Multi-Factor Authentication (MFA)"],
                "other_auth_methods": None,
                "hosting_env": "Cloud",
                "cloud_provider": "Azure",
                "region": "West Europe",
                "onprem_details": None,
                "data_handled": "Names, addresses, policy numbers, contact information",
                "data_sensitivity": ["Personal Identifiable Information (PII)"],
                "security_controls": ["Web Application Firewall (WAF)", "Encryption in Transit (TLS/SSL)", "Rate Limiting"],
                "other_security_controls": "Azure Front Door",
                "dependencies": "Backend REST API, Azure SQL Database, SendGrid email service, Entra ID",
                "business_impact": "Customer-facing system serving 50,000+ monthly users. Downtime would prevent policy access and damage reputation. Breach would expose customer PII and violate GDPR compliance.",
                "freeform_description": "This system is the Customer Portal, a public web application used by ~50,000 active users per month to view and update their insurance policies. It's hosted in Azure App Service, behind Azure Front Door and a WAF, and talks to a backend API and a SQL database.",
            }
        }