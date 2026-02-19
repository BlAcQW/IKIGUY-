"""
Document Generation Service

AI-powered document generation with template rendering, PDF/DOCX export,
and e-signature integration.
"""

import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from jinja2 import Template, TemplateSyntaxError

from app.models.document import (
    Document,
    DocumentTemplate,
    DocumentCreateRequest,
    DocumentUpdateRequest,
    TemplateGenerateRequest,
    DocumentType,
    DocumentStatus,
    Party,
    DocumentVariable
)
from apps.shared.services.llm_provider_service import LLMProviderService

# Import centralized document generation service
import sys
sys.path.insert(0, '/opt/kasaai/apps')
from shared.services.document_generation_service import get_document_generation_service


class DocumentService:
    """
    Service for document generation and management.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.documents_collection = database["documents"]
        self.templates_collection = database["document_templates"]
        self.llm_service = LLMProviderService()

    # ==================== Document CRUD ====================

    async def create_document(
        self,
        request: DocumentCreateRequest,
        organization_id: str,
        user_id: Optional[str] = None
    ) -> Document:
        """
        Create a new document from template.

        Args:
            request: Document creation request
            organization_id: Organization ID
            user_id: User creating the document

        Returns:
            Created document

        Raises:
            ValueError: If template not found or rendering fails
        """
        # Get template
        template = await self.get_template(request.template_id, organization_id)
        if not template:
            raise ValueError(f"Template not found: {request.template_id}")

        # Validate variables
        self._validate_variables(request.variables, template.variables)

        # Render template
        rendered_content = self._render_template(template.template_content, request.variables)

        # Create document
        document = Document(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            template_id=request.template_id,
            document_type=template.document_type,
            title=request.title,
            description=request.description,
            parties=request.parties,
            variables=request.variables,
            rendered_content=rendered_content,
            status=DocumentStatus.DRAFT,
            property_id=request.property_id,
            contact_id=request.contact_id,
            booking_id=request.booking_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=user_id
        )

        # Generate PDF if requested
        if request.generate_pdf:
            # TODO: Implement PDF generation
            # document.pdf_url = await self._generate_pdf(rendered_content, document.id)
            pass

        # Generate DOCX if requested
        if request.generate_docx:
            # TODO: Implement DOCX generation
            # document.docx_url = await self._generate_docx(rendered_content, document.id)
            pass

        # Save document
        await self.documents_collection.insert_one(document.dict())

        # Send for signature if requested
        if request.send_for_signature:
            # TODO: Integrate with DocuSign/HelloSign
            # await self._send_for_signature(document)
            pass

        return document

    async def get_document(self, document_id: str, organization_id: str) -> Optional[Document]:
        """Get document by ID."""
        doc_dict = await self.documents_collection.find_one({
            "id": document_id,
            "organization_id": organization_id
        })

        if not doc_dict:
            return None

        return Document(**doc_dict)

    async def generate_pdf(self, document_id: str, organization_id: str) -> bytes:
        """
        Generate PDF from document content.

        Args:
            document_id: Document ID
            organization_id: Organization ID

        Returns:
            PDF file as bytes

        Raises:
            ValueError: If document not found
        """
        # Get document
        document = await self.get_document(document_id, organization_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Get document generation service
        doc_service = get_document_generation_service()

        # Generate PDF from rendered HTML content
        pdf_bytes = await doc_service.generate_pdf_from_html(
            html_content=document.rendered_content
        )

        return pdf_bytes

    async def generate_docx(self, document_id: str, organization_id: str) -> bytes:
        """
        Generate DOCX from document content.

        Args:
            document_id: Document ID
            organization_id: Organization ID

        Returns:
            DOCX file as bytes

        Raises:
            ValueError: If document not found
        """
        # Get document
        document = await self.get_document(document_id, organization_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Get document generation service
        doc_service = get_document_generation_service()

        # Generate DOCX from rendered HTML content
        docx_bytes = await doc_service.generate_docx_from_html(
            html_content=document.rendered_content
        )

        return docx_bytes

    async def list_documents(
        self,
        organization_id: str,
        document_type: Optional[DocumentType] = None,
        status: Optional[DocumentStatus] = None,
        property_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Document], int]:
        """
        List documents with filters.

        Returns:
            Tuple of (documents list, total count)
        """
        query = {"organization_id": organization_id}

        if document_type:
            query["document_type"] = document_type.value
        if status:
            query["status"] = status.value
        if property_id:
            query["property_id"] = property_id
        if contact_id:
            query["contact_id"] = contact_id

        # Get total count
        total = await self.documents_collection.count_documents(query)

        # Get paginated results
        cursor = self.documents_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        docs_list = await cursor.to_list(length=limit)

        documents = [Document(**doc) for doc in docs_list]

        return documents, total

    async def update_document(
        self,
        document_id: str,
        updates: DocumentUpdateRequest,
        organization_id: str
    ) -> Optional[Document]:
        """Update document."""
        update_dict = updates.dict(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow()

        # If variables changed, re-render
        if updates.variables:
            document = await self.get_document(document_id, organization_id)
            if not document:
                return None

            template = await self.get_template(document.template_id, organization_id)
            if template:
                merged_variables = {**document.variables, **updates.variables}
                update_dict["rendered_content"] = self._render_template(
                    template.template_content,
                    merged_variables
                )
                update_dict["variables"] = merged_variables

                # Add to revision history
                revision = {
                    "version": document.version + 1,
                    "updated_at": datetime.utcnow(),
                    "changes": updates.dict(exclude_unset=True)
                }
                update_dict["revision_history"] = document.revision_history + [revision]
                update_dict["version"] = document.version + 1

        result = await self.documents_collection.find_one_and_update(
            {"id": document_id, "organization_id": organization_id},
            {"$set": update_dict},
            return_document=True
        )

        if not result:
            return None

        return Document(**result)

    async def delete_document(self, document_id: str, organization_id: str) -> bool:
        """Delete document."""
        result = await self.documents_collection.delete_one({
            "id": document_id,
            "organization_id": organization_id
        })
        return result.deleted_count > 0

    # ==================== Template Management ====================

    async def create_template(
        self,
        template: DocumentTemplate,
        organization_id: str
    ) -> DocumentTemplate:
        """Create a new document template."""
        template.organization_id = organization_id
        template.id = str(uuid.uuid4())
        template.created_at = datetime.utcnow()
        template.updated_at = datetime.utcnow()

        # Validate template syntax
        try:
            Template(template.template_content)
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid template syntax: {str(e)}")

        await self.templates_collection.insert_one(template.dict())
        return template

    async def get_template(self, template_id: str, organization_id: str) -> Optional[DocumentTemplate]:
        """Get template by ID."""
        template_dict = await self.templates_collection.find_one({
            "id": template_id,
            "organization_id": organization_id
        })

        if not template_dict:
            return None

        return DocumentTemplate(**template_dict)

    async def list_templates(
        self,
        organization_id: str,
        document_type: Optional[DocumentType] = None,
        is_active: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[DocumentTemplate], int]:
        """
        List templates with filters.

        Returns:
            Tuple of (templates list, total count)
        """
        query = {"organization_id": organization_id, "is_active": is_active}

        if document_type:
            query["document_type"] = document_type.value

        # Get total count
        total = await self.templates_collection.count_documents(query)

        # Get paginated results
        cursor = self.templates_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        templates_list = await cursor.to_list(length=limit)

        templates = [DocumentTemplate(**tmpl) for tmpl in templates_list]

        return templates, total

    async def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any],
        organization_id: str
    ) -> Optional[DocumentTemplate]:
        """Update template."""
        updates["updated_at"] = datetime.utcnow()

        # Validate template syntax if content changed
        if "template_content" in updates:
            try:
                Template(updates["template_content"])
            except TemplateSyntaxError as e:
                raise ValueError(f"Invalid template syntax: {str(e)}")

        result = await self.templates_collection.find_one_and_update(
            {"id": template_id, "organization_id": organization_id},
            {"$set": updates},
            return_document=True
        )

        if not result:
            return None

        return DocumentTemplate(**result)

    async def delete_template(self, template_id: str, organization_id: str) -> bool:
        """Delete template (soft delete by setting is_active=False)."""
        result = await self.templates_collection.update_one(
            {"id": template_id, "organization_id": organization_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    # ==================== AI Template Generation ====================

    async def generate_template_with_ai(
        self,
        request: TemplateGenerateRequest,
        organization_id: str,
        user_id: Optional[str] = None
    ) -> DocumentTemplate:
        """
        Generate document template using AI.

        Args:
            request: Template generation request
            organization_id: Organization ID
            user_id: User requesting generation

        Returns:
            Generated template
        """
        # Build AI prompt
        system_prompt = """You are an expert legal document template generator. Generate professional, legally compliant document templates.

Requirements:
1. Use Jinja2 template syntax for variables ({{ variable_name }})
2. Include all standard clauses for the document type
3. Format in HTML with proper structure
4. Include clear section headings
5. Use professional legal language
6. Make it jurisdiction-appropriate

Return JSON with:
- template_content: The full HTML template with Jinja2 variables
- variables: List of variable definitions with {key, label, description, variable_type, required}
- suggested_name: Suggested template name
"""

        user_prompt = f"""Generate a {request.document_type.value} template for {request.jurisdiction}.

Language: {request.language}

Custom clauses to include:
{json.dumps(request.custom_clauses or [], indent=2)}

Clauses to exclude:
{json.dumps(request.exclude_clauses or [], indent=2)}

Additional instructions:
{request.additional_instructions or "None"}

Return the template as JSON with template_content, variables, and suggested_name."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self.llm_service.create_completion(
                messages=messages,
                model="claude-3-5-sonnet-20241022",  # More capable for legal content
                temperature=0.3,
                max_tokens=4000
            )

            # Parse JSON response
            response_text = response.get("content", "")
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_text = response_text.strip()

            generated_data = json.loads(json_text)

            # Create template
            variables = [
                DocumentVariable(**var) for var in generated_data.get("variables", [])
            ]

            template = DocumentTemplate(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                name=generated_data.get("suggested_name", f"{request.document_type.value.replace('_', ' ').title()} Template"),
                document_type=request.document_type,
                description=f"AI-generated {request.document_type.value} template for {request.jurisdiction}",
                template_content=generated_data.get("template_content", ""),
                variables=variables,
                language=request.language,
                jurisdiction=request.jurisdiction,
                version="1.0",
                is_active=True,
                is_default=False,
                ai_generated=True,
                ai_prompt=user_prompt,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by=user_id
            )

            # Save template
            await self.templates_collection.insert_one(template.dict())

            return template

        except Exception as e:
            raise ValueError(f"Failed to generate template: {str(e)}")

    # ==================== Helper Methods ====================

    def _validate_variables(self, provided_vars: Dict[str, Any], template_vars: List[DocumentVariable]):
        """
        Validate that all required variables are provided.

        Args:
            provided_vars: Variables provided by user
            template_vars: Variables defined in template

        Raises:
            ValueError: If required variables are missing
        """
        missing_vars = []
        for var in template_vars:
            if var.required and var.key not in provided_vars:
                missing_vars.append(var.key)

        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")

    def _render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """
        Render Jinja2 template with variables.

        Args:
            template_content: Jinja2 template string
            variables: Variable values

        Returns:
            Rendered content

        Raises:
            ValueError: If template rendering fails
        """
        try:
            template = Template(template_content)
            return template.render(**variables)
        except Exception as e:
            raise ValueError(f"Template rendering failed: {str(e)}")

    async def _generate_pdf(self, html_content: str, document_id: str) -> str:
        """
        Generate PDF from HTML content.

        Args:
            html_content: HTML content
            document_id: Document ID

        Returns:
            PDF file URL

        TODO: Implement using WeasyPrint or similar
        """
        # Placeholder
        return f"/documents/{document_id}.pdf"

    async def _generate_docx(self, html_content: str, document_id: str) -> str:
        """
        Generate DOCX from HTML content.

        Args:
            html_content: HTML content
            document_id: Document ID

        Returns:
            DOCX file URL

        TODO: Implement using python-docx or pandoc
        """
        # Placeholder
        return f"/documents/{document_id}.docx"

    async def _send_for_signature(self, document: Document):
        """
        Send document for e-signature.

        Args:
            document: Document to send

        TODO: Integrate with DocuSign, HelloSign, or Adobe Sign
        """
        # Placeholder
        pass
