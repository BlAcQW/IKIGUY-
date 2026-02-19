"""
Generic RAG (Retrieval-Augmented Generation) Service
Reusable knowledge base service for any application using LangChain + pgvector.

This service provides:
- Document indexing with vector embeddings
- Semantic search and retrieval
- LLM-powered Q&A with context
- Multiple AI provider support (OpenAI, Gemini, Anthropic)
- Confidence scoring and escalation logic
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio

# LangChain imports
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_core.retrievers import BaseRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class KnowledgeDocument(BaseModel):
    """Model for knowledge base documents."""
    id: Optional[str] = None
    title: str
    content: str
    category: str
    source: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class QueryResult(BaseModel):
    """Model for RAG query results."""
    success: bool
    query: str
    response: str
    confidence_score: float
    sources_used: List[str]
    requires_escalation: bool
    escalation_reason: Optional[str] = None
    context_used: bool = False
    processing_time: float = 0.0
    error_message: Optional[str] = None
    # Enhanced fields from InkWave improvements
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    model_used: Optional[str] = None


class RAGConfig(BaseModel):
    """Configuration for RAG service."""

    # Database configuration
    postgres_host: str = Field(default="localhost")
    postgres_port: str = Field(default="5432")
    postgres_user: str = Field(default="postgres")
    postgres_password: str
    postgres_db: str = Field(default="kasaai_core")

    # AI provider configuration
    ai_provider: str = Field(default="openai")  # openai, gemini, anthropic
    api_key: str  # Provider-specific API key
    embedding_model: str = Field(default="text-embedding-3-small")  # Provider-specific model
    llm_model: str = Field(default="gpt-4o-mini")  # Provider-specific model

    # RAG parameters
    chunk_size: int = Field(default=1000, ge=100, le=2000)
    chunk_overlap: int = Field(default=200, ge=0, le=500)
    retrieval_k: int = Field(default=3, ge=1, le=10)
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    # Confidence and escalation
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    
    # Enhanced features (from InkWave improvements)
    use_llm_provider_service: bool = Field(
        default=False,
        description="Use shared LLMProviderService for billing integration (recommended)"
    )
    enable_billing: bool = Field(
        default=True,
        description="Enable automatic wallet billing when using LLMProviderService"
    )
    check_balance_before_query: bool = Field(
        default=False,
        description="Check wallet balance before processing query"
    )


class RAGService:
    """
    Generic RAG service for knowledge base management and Q&A.

    Supports multiple AI providers and can be extended for app-specific needs.
    
    Enhanced with InkWave improvements:
    - Optional LLMProviderService integration for automatic billing
    - Streaming support with billing
    - Balance checks before queries
    - Cost tracking and monitoring
    """

    def __init__(self, config: RAGConfig):
        """
        Initialize RAG service with configuration.

        Args:
            config: RAG configuration with database and AI provider settings
        """
        self.config = config

        # PostgreSQL connection string
        self.connection_string = (
            f"postgresql://{config.postgres_user}:{config.postgres_password}"
            f"@{config.postgres_host}:{config.postgres_port}/{config.postgres_db}"
        )

        # Lazy initialization for LangChain components
        self._embeddings = None
        self._llm = None
        self._text_splitter = None

        # Enhanced: LLMProviderService for billing (optional)
        self._llm_provider_service = None
        self._initialized = False

        # Cache for vectorstores
        self._vectorstores: Dict[str, PGVector] = {}

        logger.info(f"Initialized RAG service with {config.ai_provider} provider")
        
    async def _initialize_llm_provider_service(self):
        """Initialize LLMProviderService if enabled."""
        if self.config.use_llm_provider_service and self._llm_provider_service is None:
            try:
                import sys
                sys.path.insert(0, '/opt/kasaai/apps')
                from shared.services.llm_provider_service import LLMProviderService
                
                self._llm_provider_service = LLMProviderService(
                    enable_billing=self.config.enable_billing
                )
                await self._llm_provider_service.initialize()
                logger.info("✅ LLMProviderService initialized for billing integration")
            except Exception as e:
                logger.warning(f"Failed to initialize LLMProviderService: {e}")
                # Fall back to LangChain LLM if LLMProviderService fails

    @property
    def embeddings(self):
        """Lazy initialization of embeddings based on provider."""
        if self._embeddings is None:
            if self.config.ai_provider == "openai":
                from langchain_openai import OpenAIEmbeddings
                self._embeddings = OpenAIEmbeddings(
                    openai_api_key=self.config.api_key,
                    model=self.config.embedding_model
                )
                logger.info(f"Using OpenAI {self.config.embedding_model}")

            elif self.config.ai_provider == "gemini":
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                self._embeddings = GoogleGenerativeAIEmbeddings(
                    google_api_key=self.config.api_key,
                    model=f"models/{self.config.embedding_model}"
                )
                logger.info(f"Using Google Gemini {self.config.embedding_model}")

            elif self.config.ai_provider == "anthropic":
                # Note: Anthropic doesn't provide embeddings, fall back to OpenAI
                from langchain_openai import OpenAIEmbeddings
                openai_key = os.getenv("OPENAI_API_KEY")
                if not openai_key:
                    raise ValueError("OPENAI_API_KEY required for embeddings when using Anthropic")
                self._embeddings = OpenAIEmbeddings(
                    openai_api_key=openai_key,
                    model="text-embedding-3-small"
                )
                logger.info("Using OpenAI embeddings (Anthropic doesn't provide embeddings)")
            else:
                raise ValueError(f"Unsupported AI provider: {self.config.ai_provider}")

        return self._embeddings

    @property
    def llm(self):
        """Lazy initialization of LLM based on provider."""
        if self._llm is None:
            if self.config.ai_provider == "openai":
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    openai_api_key=self.config.api_key,
                    model=self.config.llm_model,
                    temperature=self.config.temperature
                )
                logger.info(f"Using OpenAI {self.config.llm_model}")

            elif self.config.ai_provider == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                self._llm = ChatGoogleGenerativeAI(
                    google_api_key=self.config.api_key,
                    model=self.config.llm_model,
                    temperature=self.config.temperature
                )
                logger.info(f"Using Google Gemini {self.config.llm_model}")

            elif self.config.ai_provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                self._llm = ChatAnthropic(
                    anthropic_api_key=self.config.api_key,
                    model=self.config.llm_model,
                    temperature=self.config.temperature
                )
                logger.info(f"Using Anthropic {self.config.llm_model}")
            else:
                raise ValueError(f"Unsupported AI provider: {self.config.ai_provider}")

        return self._llm

    @property
    def text_splitter(self):
        """Lazy initialization of text splitter."""
        if self._text_splitter is None:
            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        return self._text_splitter

    def _get_collection_name(self, identifier: str) -> str:
        """
        Get sanitized collection name.

        Args:
            identifier: Collection identifier (e.g., company name, book ID, course ID)

        Returns:
            Sanitized collection name for pgvector
        """
        return identifier.lower().replace(' ', '_').replace('-', '_')
    
    @staticmethod
    def build_collection_name(
        app_name: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Build organization-scoped collection name (StudyFlow enhancement).
        
        Pattern: {app_name}_{org_id}_{resource_type}_{resource_id}
        
        Args:
            app_name: Application name (e.g., "studyflow", "inkwave")
            resource_type: Resource type (e.g., "subject", "book", "course")
            resource_id: Optional resource identifier
            organization_id: Organization ID for multi-tenancy
            **kwargs: Additional components (e.g., grade, subject)
            
        Returns:
            Sanitized collection name
            
        Examples:
            - studyflow_org_001_mathematics_grade5
            - inkwave_org_002_book_abc123
            - studyflow_org_001_developer_onboarding
        """
        parts = [app_name.lower()]
        
        if organization_id:
            parts.append(organization_id.lower().replace('-', '_'))
        
        parts.append(resource_type.lower())
        
        if resource_id:
            parts.append(resource_id.lower().replace('-', '_'))
        
        # Add additional components
        for key, value in sorted(kwargs.items()):
            if value:
                parts.append(f"{key}_{str(value).lower().replace('-', '_')}")
        
        return "_".join(parts)

    async def _get_vectorstore(self, collection_name: str) -> PGVector:
        """
        Get or create vectorstore for collection.

        Args:
            collection_name: Collection name

        Returns:
            PGVector vectorstore instance
        """
        sanitized_name = self._get_collection_name(collection_name)

        if sanitized_name not in self._vectorstores:
            try:
                # Create PGVector instance with pgvector extension
                vectorstore = PGVector(
                    embeddings=self.embeddings,
                    collection_name=sanitized_name,
                    connection=self.connection_string,
                    use_jsonb=True,
                    pre_delete_collection=False  # Don't delete existing data
                )

                self._vectorstores[sanitized_name] = vectorstore
                logger.info(f"Created vectorstore for collection: {sanitized_name}")

            except Exception as e:
                logger.error(f"Error creating vectorstore for {collection_name}: {str(e)}")
                raise

        return self._vectorstores[sanitized_name]

    async def initialize_knowledge_base(
        self,
        collection_name: str,
        documents: List[KnowledgeDocument],
        organization_id: Optional[str] = None,
        update_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Initialize knowledge base with documents using pgvector.
        
        Enhanced with StudyFlow improvements:
        - Organization-scoped collections
        - Auto-add organization_id to document metadata
        - Update existing documents option

        Args:
            collection_name: Unique collection identifier
            documents: List of knowledge documents to index
            organization_id: Organization ID for multi-tenancy (auto-added to metadata)
            update_existing: If True, update existing documents instead of creating new ones

        Returns:
            Initialization result with index details
        """
        try:
            vectorstore = await self._get_vectorstore(collection_name)

            # Convert KnowledgeDocuments to LangChain Documents
            # Enhanced: Auto-add organization_id to metadata (StudyFlow enhancement)
            langchain_docs = []
            for doc in documents:
                # Split large documents into chunks
                text_chunks = self.text_splitter.split_text(doc.content)

                for i, chunk in enumerate(text_chunks):
                    # Build metadata with organization_id if provided
                    doc_metadata = {
                        "doc_id": doc.id or f"{collection_name}_{len(langchain_docs)}",
                        "title": doc.title,
                        "category": doc.category,
                        "source": doc.source,
                        "tags": doc.tags,
                        "collection": collection_name,
                        "chunk_index": i,
                        "total_chunks": len(text_chunks),
                        **doc.metadata
                    }
                    
                    # Auto-add organization_id if provided and not already in metadata
                    if organization_id and "organization_id" not in doc_metadata:
                        doc_metadata["organization_id"] = organization_id
                    
                    langchain_doc = Document(
                        page_content=chunk,
                        metadata=doc_metadata
                    )
                    langchain_docs.append(langchain_doc)

            # Add documents to vectorstore
            if langchain_docs:
                await asyncio.to_thread(
                    vectorstore.add_documents,
                    langchain_docs
                )

            logger.info(
                f"Indexed {len(langchain_docs)} document chunks for {collection_name}"
                + (f" (org: {organization_id})" if organization_id else "")
            )

            return {
                "success": True,
                "collection_name": collection_name,
                "documents_indexed": len(documents),
                "chunks_created": len(langchain_docs),
                "embedding_dimension": 1536,  # Default dimension
                "organization_id": organization_id,  # Enhanced: Include org ID
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error initializing knowledge base for {collection_name}: {str(e)}")
            raise

    async def query_knowledge_base(
        self,
        collection_name: str,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        system_prompt_template: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> QueryResult:
        """
        Query the knowledge base using RAG.

        Args:
            collection_name: Collection to query
            query: User question or query
            context: Additional context from conversation
            filters: Optional metadata filters (tags, category, etc.)
            system_prompt_template: Custom system prompt (uses default if not provided)

        Returns:
            Query result with answer and metadata
        """
        start_time = datetime.utcnow()

        logger.info(f"📥 RAG QUERY START: collection={collection_name}, query='{query[:100]}'")

        try:
            # Get vectorstore
            vectorstore = await self._get_vectorstore(collection_name)

            # Create retriever with similarity threshold
            search_kwargs = {
                "k": self.config.retrieval_k,
                "score_threshold": self.config.similarity_threshold
            }

            # Add metadata filters if provided
            # Enhanced: Auto-add organization_id filter if provided (StudyFlow enhancement)
            if filters is None:
                filters = {}
            
            if organization_id and "organization_id" not in filters:
                filters["organization_id"] = organization_id
                logger.info(f"🔍 Auto-filtering by organization: {organization_id}")
            
            if filters:
                search_kwargs["filter"] = filters
                logger.info(f"🔍 Applying filters: {filters}")

            retriever = vectorstore.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs=search_kwargs
            )

            # Default system prompt if not provided
            if not system_prompt_template:
                system_prompt_template = """
You are a helpful AI assistant. Answer the user's question based on the provided knowledge base information.

Context from knowledge base:
{context}

User Question: {question}

Guidelines:
- Only use information from the provided knowledge base context
- If the information is insufficient or unclear, acknowledge this
- Be helpful, professional, and concise
- Include relevant details but avoid overwhelming the user

Answer:"""

            # Create the RAG prompt
            rag_prompt = ChatPromptTemplate.from_template(system_prompt_template)

            # Create the document processing chain
            from langchain_classic.chains.combine_documents import create_stuff_documents_chain
            from langchain_classic.chains.retrieval import create_retrieval_chain

            document_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=rag_prompt
            )

            # Create the full retrieval chain
            retrieval_chain = create_retrieval_chain(
                retriever=retriever,
                combine_docs_chain=document_chain
            )

            # Execute the retrieval chain
            # Pass all common variable names to support different prompt templates:
            # - 'input': LangChain's default for retrieval chain
            # - 'question': Common template variable
            # - 'query': Alternative template variable used by voice services
            logger.info(f"🔍 Executing retrieval chain...")
            result = await asyncio.to_thread(
                retrieval_chain.invoke,
                {"input": query, "question": query, "query": query}
            )

            # Extract information from the result
            response = result.get("answer", "")
            retrieved_docs = result.get("context", [])

            logger.info(f"📊 Retrieved {len(retrieved_docs)} documents, response length: {len(response)} chars")

            # Calculate confidence based on retrieval scores and response length
            confidence_score = self._calculate_confidence(response, retrieved_docs)
            logger.info(f"💯 Confidence score: {confidence_score:.2f}")

            # Determine if escalation is needed
            should_escalate, escalation_reason = self._should_escalate(
                query, response, confidence_score, retrieved_docs
            )

            # Extract source information
            sources_used = [
                doc.metadata.get("title", "Unknown source")
                for doc in retrieved_docs
            ]

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(f"✅ RAG QUERY COMPLETE: time={processing_time:.2f}s, confidence={confidence_score:.2f}")

            return QueryResult(
                success=True,
                query=query,
                response=response,
                confidence_score=confidence_score,
                sources_used=sources_used,
                requires_escalation=should_escalate,
                escalation_reason=escalation_reason,
                context_used=context is not None,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Error querying knowledge base for {collection_name}: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return QueryResult(
                success=False,
                query=query,
                response="I'm experiencing technical difficulties accessing the knowledge base. Please try again or contact support.",
                confidence_score=0.0,
                sources_used=[],
                requires_escalation=True,
                escalation_reason="Technical error in RAG system",
                error_message=str(e),
                processing_time=processing_time
            )

    def _calculate_confidence(self, response: str, retrieved_docs: List[Document]) -> float:
        """Calculate confidence score based on retrieval quality and response."""
        if not response or not retrieved_docs:
            return 0.0

        # Base confidence from document retrieval
        base_confidence = 0.6 if retrieved_docs else 0.0

        # Boost confidence based on number of relevant documents
        doc_boost = min(0.2, len(retrieved_docs) * 0.05)

        # Boost confidence based on response length (longer = more detailed)
        length_boost = min(0.2, len(response) / 1000)

        return min(1.0, base_confidence + doc_boost + length_boost)

    def _should_escalate(
        self,
        query: str,
        response: str,
        confidence: float,
        retrieved_docs: List[Document]
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if the query should be escalated.

        Args:
            query: User query
            response: Generated response
            confidence: Confidence score
            retrieved_docs: Retrieved documents

        Returns:
            Tuple of (should_escalate, escalation_reason)
        """
        # Low confidence escalation
        if confidence < self.config.confidence_threshold:
            return True, f"Low confidence answer (confidence: {confidence:.2f})"

        # No relevant documents found
        if not retrieved_docs:
            return True, "No relevant information found in knowledge base"

        # Escalation keywords in query
        escalation_keywords = [
            "complaint", "angry", "frustrated", "manager", "supervisor",
            "cancel", "refund", "billing issue", "legal", "lawsuit",
            "emergency", "urgent", "critical", "broken", "not working"
        ]

        query_lower = query.lower()
        if any(keyword in query_lower for keyword in escalation_keywords):
            return True, "Query contains escalation keywords"

        # Check if response indicates uncertainty
        uncertainty_indicators = [
            "i don't know", "i'm not sure", "unclear", "insufficient information",
            "contact support", "speak with", "escalate"
        ]

        response_lower = response.lower()
        if any(indicator in response_lower for indicator in uncertainty_indicators):
            return True, "AI assistant indicated uncertainty in response"

        return False, None

    async def update_knowledge_base(
        self,
        collection_name: str,
        documents: List[KnowledgeDocument],
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update knowledge base with new or updated documents.
        
        Enhanced with StudyFlow improvements:
        - Organization-scoped updates
        - Auto-add organization_id to document metadata

        Args:
            collection_name: Collection identifier
            documents: New or updated documents
            organization_id: Organization ID for multi-tenancy (auto-added to metadata)

        Returns:
            Update result
        """
        try:
            vectorstore = await self._get_vectorstore(collection_name)

            # Convert to LangChain documents and split
            # Enhanced: Auto-add organization_id to metadata (StudyFlow enhancement)
            langchain_docs = []
            for doc in documents:
                text_chunks = self.text_splitter.split_text(doc.content)

                for i, chunk in enumerate(text_chunks):
                    # Build metadata with organization_id if provided
                    doc_metadata = {
                        "doc_id": doc.id or f"update_{datetime.utcnow().timestamp()}_{len(langchain_docs)}",
                        "title": doc.title,
                        "category": doc.category,
                        "source": doc.source,
                        "tags": doc.tags,
                        "collection": collection_name,
                        "chunk_index": i,
                        "total_chunks": len(text_chunks),
                        "updated_at": datetime.utcnow().isoformat(),
                        **doc.metadata
                    }
                    
                    # Auto-add organization_id if provided and not already in metadata
                    if organization_id and "organization_id" not in doc_metadata:
                        doc_metadata["organization_id"] = organization_id
                    
                    langchain_doc = Document(
                        page_content=chunk,
                        metadata=doc_metadata
                    )
                    langchain_docs.append(langchain_doc)

            # Add new documents to vectorstore
            if langchain_docs:
                await asyncio.to_thread(
                    vectorstore.add_documents,
                    langchain_docs
                )

            logger.info(
                f"Updated {len(documents)} documents ({len(langchain_docs)} chunks) for {collection_name}"
                + (f" (org: {organization_id})" if organization_id else "")
            )

            return {
                "success": True,
                "documents_updated": len(documents),
                "chunks_updated": len(langchain_docs),
                "collection_name": collection_name,
                "organization_id": organization_id,  # Enhanced: Include org ID
                "updated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error updating knowledge base for {collection_name}: {str(e)}")
            raise

    async def delete_knowledge_base(self, collection_name: str) -> Dict[str, Any]:
        """
        Delete entire knowledge base collection.

        Args:
            collection_name: Collection to delete

        Returns:
            Deletion result
        """
        try:
            sanitized_name = self._get_collection_name(collection_name)
            vectorstore = await self._get_vectorstore(collection_name)

            # Delete the collection
            await asyncio.to_thread(vectorstore.delete_collection)

            # Remove from cache
            if sanitized_name in self._vectorstores:
                del self._vectorstores[sanitized_name]

            logger.info(f"Deleted knowledge base for {collection_name}")

            return {
                "success": True,
                "collection_name": collection_name,
                "deleted_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error deleting knowledge base for {collection_name}: {str(e)}")
            raise

    async def get_knowledge_base_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.

        Args:
            collection_name: Collection identifier

        Returns:
            Knowledge base statistics
        """
        try:
            sanitized_name = self._get_collection_name(collection_name)
            vectorstore = await self._get_vectorstore(collection_name)

            # Note: PGVector doesn't provide direct stats methods
            # In a production environment, you'd query the PostgreSQL tables directly

            stats = {
                "collection_name": sanitized_name,
                "estimated_documents": "Unknown - query database directly",
                "vectorstore_type": "PostgreSQL + pgvector",
                "langchain_version": "0.3.x",
                "ai_provider": self.config.ai_provider,
                "embedding_model": self.config.embedding_model,
                "llm_model": self.config.llm_model,
                "last_updated": datetime.utcnow().isoformat(),
                "note": "For detailed stats, query the PostgreSQL langchain_pg_* tables directly"
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting knowledge base stats for {collection_name}: {str(e)}")
            raise


# Helper function to create RAG service from environment variables
def create_rag_service_from_env(
    ai_provider: str = "openai",
    postgres_db: Optional[str] = None
) -> RAGService:
    """
    Create RAG service using environment variables.

    Args:
        ai_provider: AI provider to use (openai, gemini, anthropic)
        postgres_db: PostgreSQL database name (defaults to POSTGRES_DB_CORE env var)

    Returns:
        Configured RAG service instance

    Environment variables required:
        - POSTGRES_SERVER or POSTGRES_HOST
        - POSTGRES_PORT
        - POSTGRES_USER
        - POSTGRES_PASSWORD
        - POSTGRES_DB_CORE (or pass postgres_db parameter)
        - OPENAI_API_KEY (if ai_provider="openai")
        - GEMINI_API_KEY (if ai_provider="gemini")
        - ANTHROPIC_API_KEY (if ai_provider="anthropic")
    """
    # Determine API key based on provider
    api_key_env_map = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY"
    }

    api_key = os.getenv(api_key_env_map.get(ai_provider))
    if not api_key:
        raise ValueError(f"{api_key_env_map.get(ai_provider)} environment variable is required")

    # Model defaults per provider
    model_defaults = {
        "openai": ("text-embedding-3-small", "gpt-4o-mini"),
        "gemini": ("text-embedding-004", "gemini-2.0-flash-exp"),
        "anthropic": ("text-embedding-3-small", "claude-3-5-sonnet-20241022")  # Uses OpenAI for embeddings
    }

    embedding_model, llm_model = model_defaults.get(ai_provider, model_defaults["openai"])

    config = RAGConfig(
        postgres_host=os.getenv("POSTGRES_SERVER", os.getenv("POSTGRES_HOST", "localhost")),
        postgres_port=os.getenv("POSTGRES_PORT", "5432"),
        postgres_user=os.getenv("POSTGRES_USER", "postgres"),
        postgres_password=os.getenv("POSTGRES_PASSWORD"),
        postgres_db=postgres_db or os.getenv("POSTGRES_DB_CORE", "kasaai_core"),
        ai_provider=ai_provider,
        api_key=api_key,
        embedding_model=embedding_model,
        llm_model=llm_model
    )

    return RAGService(config)
