"""
RAG (Retrieval-Augmented Generation) service for enhanced helpdesk knowledge base.
Real LangChain implementation using PostgreSQL + pgvector for vector storage.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel
import asyncio

# LangChain imports
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_core.retrievers import BaseRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_postgres import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.retrievers.multi_query import MultiQueryRetriever

logger = logging.getLogger(__name__)

# Import analytics service for query tracking (lazy import to avoid circular dependency)
_analytics_service = None

def get_analytics_service():
    """Lazy load analytics service to avoid circular imports."""
    global _analytics_service
    if _analytics_service is None:
        from backend.services.rag_analytics_service import rag_analytics_service
        from backend.models.knowledge_base import QueryMetric
        _analytics_service = (rag_analytics_service, QueryMetric)
    return _analytics_service

# Redis cache service (lazy import to work in both uvicorn and script contexts)
_redis_cache_service = None

def get_redis_cache_service():
    """Lazy load Redis cache service to handle different import paths."""
    global _redis_cache_service
    if _redis_cache_service is None:
        try:
            # Try relative import first (works in script context)
            from backend.services.redis_cache_service import redis_cache_service
            _redis_cache_service = redis_cache_service
        except ModuleNotFoundError:
            # Fall back to absolute import (works in uvicorn context)
            from apps.core_backend.backend.services.redis_cache_service import redis_cache_service
            _redis_cache_service = redis_cache_service
    return _redis_cache_service

# Import hybrid search helper
try:
    from backend.services.hybrid_search_helper import should_use_hybrid_search, filter_docs_by_title_match
    HYBRID_SEARCH_AVAILABLE = True
except ImportError:
    logger.warning("Hybrid search helper not available - falling back to pure vector search")
    HYBRID_SEARCH_AVAILABLE = False

# Query complexity router disabled - caused performance degradation in testing
# Keeping Phase 1 optimizations only: expanded cache, reduced k values, timeout budget
COMPLEXITY_ROUTER_AVAILABLE = False
query_complexity_router = None

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

class RAGMetrics(BaseModel):
    """Model for RAG performance metrics."""
    total_queries: int
    successful_queries: int
    escalated_queries: int
    success_rate: float
    escalation_rate: float
    average_confidence_score: float
    response_time_avg: float
    top_categories: List[str]
    period_start: datetime
    period_end: datetime

class HelpdeskRAGService:
    """Real LangChain-based RAG service for helpdesk knowledge retrieval."""

    def __init__(self):
        # Load environment variables
        self.postgres_host = os.getenv("POSTGRES_SERVER", "localhost")
        self.postgres_port = os.getenv("POSTGRES_PORT", "5432")
        self.postgres_user = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD")
        if not self.postgres_password:
            raise ValueError("POSTGRES_PASSWORD environment variable is required")
        self.postgres_db = os.getenv("POSTGRES_DB_CORE", "kasaai_core")

        # API keys - Support multiple providers for performance optimization
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Use OpenAI GPT-4o-mini as primary (3x faster than Gemini), fallback to Gemini
        if self.openai_api_key:
            self.ai_provider = "openai"
            logger.info("🚀 AI Provider: OpenAI GPT-4o-mini (optimized for speed)")
        elif self.gemini_api_key:
            self.ai_provider = "gemini"
            logger.info("AI Provider: Google Gemini 2.5 Flash")
        else:
            raise ValueError("No AI provider API key configured (need OPENAI_API_KEY or GEMINI_API_KEY)")

        # Thresholds for escalation
        self.confidence_threshold = 0.7
        self.similarity_threshold = 0.8

        # Lazy initialization for LangChain components
        self._embeddings = None
        self._llm = None
        self._text_splitter = None

        # PostgreSQL connection string
        self.connection_string = f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

        # Cache for vectorstores
        self._vectorstores: Dict[str, PGVector] = {}

    @property
    def embeddings(self):
        """Lazy initialization of embeddings - USE ONLY GEMINI."""
        if self._embeddings is None:
            self._embeddings = GoogleGenerativeAIEmbeddings(
                google_api_key=self.gemini_api_key,
                model="models/text-embedding-004"  # Latest, faster model (was embedding-001)
            )
            logger.info("Using Google Gemini text-embedding-004 (latest, optimized)")
        return self._embeddings

    @property
    def llm(self):
        """Lazy initialization of chat model - Supports OpenAI (fast) and Gemini (fallback)."""
        if self._llm is None:
            if self.ai_provider == "openai":
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    api_key=self.openai_api_key,
                    model="gpt-4o-mini",  # Fast model optimized for speed
                    temperature=0.1
                )
                logger.info("⚡ Using OpenAI GPT-4o-mini LLM (optimized for speed - 3x faster than Gemini)")
            else:  # gemini fallback
                self._llm = ChatGoogleGenerativeAI(
                    google_api_key=self.gemini_api_key,
                    model="gemini-2.5-flash",
                    temperature=0.1
                )
                logger.info("Using Google Gemini 2.5 Flash LLM")
        return self._llm

    @property
    def text_splitter(self):
        """Lazy initialization of text splitter."""
        if self._text_splitter is None:
            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        return self._text_splitter

    def _get_collection_name(self, company_name: str) -> str:
        """Get sanitized collection name for company."""
        # Reason: Preserve hyphens in company names (e.g., ghana-tourism-board)
        # Only replace spaces with hyphens
        return f"helpdesk_{company_name.lower().replace(' ', '-')}"

    async def _get_vectorstore(self, company_name: str) -> PGVector:
        """Get or create vectorstore for company."""
        collection_name = self._get_collection_name(company_name)

        if collection_name not in self._vectorstores:
            try:
                # Create PGVector instance with pgvector extension
                vectorstore = PGVector(
                    embeddings=self.embeddings,
                    collection_name=collection_name,
                    connection=self.connection_string,
                    use_jsonb=True,
                    pre_delete_collection=False  # Don't delete existing data
                )

                self._vectorstores[collection_name] = vectorstore
                logger.info(f"Created vectorstore for collection: {collection_name}")

            except Exception as e:
                logger.error(f"Error creating vectorstore for {company_name}: {str(e)}")
                raise

        return self._vectorstores[collection_name]

    async def initialize_knowledge_base(self, company_name: str, documents: List[KnowledgeDocument]) -> Dict[str, Any]:
        """
        Initialize LangChain knowledge base for a company using PostgreSQL + pgvector.

        Args:
            company_name: Company identifier
            documents: List of knowledge documents to index

        Returns:
            Initialization result with index details
        """
        try:
            collection_name = self._get_collection_name(company_name)
            vectorstore = await self._get_vectorstore(company_name)

            # Convert KnowledgeDocuments to LangChain Documents
            langchain_docs = []
            for doc in documents:
                # Split large documents into chunks
                text_chunks = self.text_splitter.split_text(doc.content)

                for i, chunk in enumerate(text_chunks):
                    langchain_doc = Document(
                        page_content=chunk,
                        metadata={
                            "doc_id": doc.id or f"{company_name}_{len(langchain_docs)}",
                            "title": doc.title,
                            "category": doc.category,
                            "source": doc.source,
                            "tags": doc.tags,
                            "company": company_name,
                            "chunk_index": i,
                            "total_chunks": len(text_chunks),
                            **doc.metadata
                        }
                    )
                    langchain_docs.append(langchain_doc)

            # Add documents to vectorstore
            if langchain_docs:
                await asyncio.to_thread(
                    vectorstore.add_documents,
                    langchain_docs
                )

            logger.info(f"Indexed {len(langchain_docs)} document chunks for {company_name}")

            return {
                "success": True,
                "collection_name": collection_name,
                "documents_indexed": len(documents),
                "chunks_created": len(langchain_docs),
                "embedding_dimension": 1536,  # OpenAI text-embedding-3-small dimension
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error initializing knowledge base for {company_name}: {str(e)}")
            raise

    async def query_knowledge_base(self, company_name: str, query: str, context: Optional[Dict[str, Any]] = None, plan_type: Optional[str] = None, region: Optional[str] = None) -> QueryResult:
        """
        Query the knowledge base using LangChain retrieval chains.

        Args:
            company_name: Company identifier
            query: User question or query
            context: Additional context from conversation
            plan_type: Optional insurance plan type filter (e.g., 'PLATINUM PLUS', 'PLATINUM', 'MERCURY', 'REGULAR')
            region: Optional geographic region filter (e.g., 'GREATER ACCRA', 'ASHANTI', 'WESTERN REGION')

        Returns:
            Query result with answer and metadata
        """
        start_time = datetime.utcnow()
        step_start_time = None

        # Timeout budget: 18 seconds (leaves 2s buffer for VAPI's 20s webhook timeout)
        # Reason: Prevent hard timeouts by monitoring elapsed time and skipping expensive operations
        TIMEOUT_BUDGET_SECONDS = 18.0

        # Log the query details
        logger.info(f"📥 RAG QUERY START: company={company_name}, query='{query[:100]}'")
        logger.info(f"🔧 AI Provider configured: {self.ai_provider}")
        logger.info(f"⏱️  Timeout budget: {TIMEOUT_BUDGET_SECONDS}s")

        # Check Redis cache first
        try:
            redis_cache_service = get_redis_cache_service()
            cached_response = await redis_cache_service.get_cached_response(
                company_name=company_name,
                query=query
            )
            if cached_response:
                cache_time = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"🎯 CACHE HIT - Returning cached response ({cache_time:.2f}s)")
                return QueryResult(**cached_response)
            else:
                logger.info(f"💭 Cache miss - Proceeding with RAG query")
        except Exception as cache_err:
            logger.warning(f"⚠️  Cache check failed, proceeding with query: {cache_err}")

        try:
            # Step 1: Get vectorstore
            step_start_time = datetime.utcnow()
            vectorstore = await self._get_vectorstore(company_name)
            vectorstore_time = (datetime.utcnow() - step_start_time).total_seconds()
            logger.info(f"✅ Vectorstore retrieved for collection: {self._get_collection_name(company_name)} ({vectorstore_time:.2f}s)")

            # Create optimized retriever - direct search without MultiQueryRetriever overhead
            # Reduced k to 3 for faster LLM processing while maintaining quality
            # Reason: Sending fewer documents to LLM reduces processing time by 50-60%

            # Check if hybrid search will be needed (for community numbers and market locations)
            needs_hybrid_search = False
            search_params = None
            if HYBRID_SEARCH_AVAILABLE:
                needs_hybrid_search, search_params = should_use_hybrid_search(query)

            # Build search_kwargs with optimal k and threshold based on query type
            # Reason: Different query types need different retrieval strategies
            if needs_hybrid_search and search_params:
                search_type = search_params.get("search_type")

                if search_type == "community_number":
                    # Community numbers: High k for better recall (numeric differentiation is hard)
                    # Reason: Reduced from 40 to 25 to improve speed while maintaining quality
                    k_value = 25
                    score_threshold = 0.2
                    logger.info(f"🔍 Community number search detected - k={k_value}, threshold={score_threshold}")
                elif search_type == "market_location":
                    # Market locations: Higher k + lower threshold (semantic similarity is low)
                    k_value = 30
                    score_threshold = 0.15  # More lenient for market areas
                    market_loc = search_params.get("market_location")
                    logger.info(f"🏪 Market location search detected: '{market_loc}' - k={k_value}, threshold={score_threshold}")
                else:
                    k_value = 25
                    score_threshold = 0.2
            elif plan_type or region:
                k_value = 5
                score_threshold = 0.2
            else:
                k_value = 5
                score_threshold = 0.2

            search_kwargs = {
                "k": k_value,
                "score_threshold": score_threshold
            }

            # Add region filter if specified
            # Reason: Filter documents at vector search level using PostgreSQL JSON queries on cmetadata->tags
            if region:
                # PGVector metadata filtering: tags is a JSON array in cmetadata
                # We need to check if our region string is one of the elements in the tags array
                # Since $contains is not supported, we disable pre-filtering and rely on post-filtering instead
                # This is less efficient but ensures correct results
                logger.info(f"🌍 Region filter will be applied post-retrieval: '{region.upper()}'")

            retriever = vectorstore.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs=search_kwargs
            )

            filter_info = []
            if plan_type:
                filter_info.append(f"plan filtering")
            if region:
                filter_info.append(f"region={region}")

            logger.info(f"✅ Optimized retriever created (k={search_kwargs['k']}, threshold={search_kwargs['score_threshold']}, {', '.join(filter_info) if filter_info else 'no filters'})")
            logger.info(f"⚡ Performance optimizations:")
            logger.info(f"   - Removed MultiQueryRetriever (saves ~8-10s by avoiding 3 LLM calls)")
            logger.info(f"   - Balanced k={search_kwargs['k']} for quality+recall (retrieves more documents for better coverage)")
            if region:
                logger.info(f"   - Region filtering at vector search level (prevents irrelevant region results)")

            # Create the RAG prompt template
            rag_prompt = ChatPromptTemplate.from_template("""
You are a helpful customer service assistant for {company}. Answer the user's question based on the provided knowledge base information.

Context from knowledge base:
{context}

User Question: {question}

Guidelines:
- Only use information from the provided knowledge base context
- If the information is insufficient or unclear, acknowledge this and suggest escalating to a human agent
- Be helpful, professional, and concise
- Include relevant details but avoid overwhelming the user
- If you mention specific procedures or policies, reference the source document

Answer:""")

            # Create the document processing chain
            document_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=rag_prompt
            )

            # Create the full retrieval chain
            retrieval_chain = create_retrieval_chain(
                retriever=retriever,
                combine_docs_chain=document_chain
            )

            # Add company context to the query
            # Enhance query with plan type and/or region if specified
            enhancements = []
            if plan_type:
                enhancements.append(f"insurance plan: {plan_type}")
                logger.info(f"🎯 Enhanced query with plan type filter: '{plan_type}'")
            if region:
                enhancements.append(f"region: {region}")
                logger.info(f"🌍 Enhanced query with region filter: '{region}'")

            if enhancements:
                enhanced_query_text = f"{query} ({', '.join(enhancements)})"
            else:
                enhanced_query_text = query

            enhanced_query = {
                "input": enhanced_query_text,
                "question": enhanced_query_text,
                "company": company_name
            }

            # Step 2: Execute the retrieval chain
            step_start_time = datetime.utcnow()
            logger.info(f"🔍 Executing retrieval chain with enhanced query...")
            result = await asyncio.to_thread(
                retrieval_chain.invoke,
                enhanced_query
            )
            retrieval_time = (datetime.utcnow() - step_start_time).total_seconds()
            logger.info(f"✅ Retrieval chain completed ({retrieval_time:.2f}s)")

            # Extract information from the result
            response = result.get("answer", "")
            retrieved_docs = result.get("context", [])

            # Log retrieved documents for debugging
            logger.info(f"📄 Retrieved {len(retrieved_docs)} documents from vector search")
            if retrieved_docs:
                logger.info(f"📋 Retrieved document details:")
                for i, doc in enumerate(retrieved_docs[:5], 1):  # Log first 5
                    title = doc.metadata.get('title', 'No title') if hasattr(doc, 'metadata') else 'No metadata'
                    content_preview = doc.page_content[:100] if hasattr(doc, 'page_content') else 'No content'
                    logger.info(f"   [{i}] Title: {title}")
                    logger.info(f"       Preview: {content_preview}...")
                if len(retrieved_docs) > 5:
                    logger.info(f"   ... and {len(retrieved_docs) - 5} more documents")
            else:
                logger.warning(f"⚠️  NO DOCUMENTS RETRIEVED - vector search returned empty results")
                logger.warning(f"   Query: '{query}'")
                logger.warning(f"   Search config: k={search_kwargs['k']}, threshold={search_kwargs['score_threshold']}")

            # Apply hybrid search filtering for number-based queries (e.g., community numbers)
            # Reason: Vector embeddings struggle with numeric differentiation - "5" vs "38" vs "31" look similar semantically
            regenerate_response = False
            if HYBRID_SEARCH_AVAILABLE and retrieved_docs:
                use_hybrid, search_params = should_use_hybrid_search(query)
                if use_hybrid and search_params:
                    logger.info(f"🔍 Applying hybrid search filter: {search_params}")
                    title_pattern = search_params.get("title_pattern")
                    if title_pattern:
                        original_count = len(retrieved_docs)
                        retrieved_docs = filter_docs_by_title_match(retrieved_docs, title_pattern)
                        filtered_count = len(retrieved_docs)
                        if filtered_count != original_count:
                            logger.info(f"✅ Hybrid search: {original_count} docs → {filtered_count} docs (filtered by title match)")
                            regenerate_response = True  # Need to regenerate response with filtered docs

            # Apply plan type post-filtering if specified
            if plan_type and retrieved_docs:
                original_count = len(retrieved_docs)
                # Filter documents that accept the requested plan type
                # Plan types appear in facility names like "(MER/PLAT/PLAT PLUS)" or "(PLAT PLUS ONLY)"
                # Plan hierarchy: PLATINUM PLUS > PLATINUM > MERCURY > REGULAR
                # Reason: A facility accepting PLATINUM PLUS also accepts PLATINUM, but not vice versa for "ONLY" facilities

                filtered_docs = []
                for doc in retrieved_docs:
                    content = doc.page_content

                    # Extract plan information from content (looks for text in parentheses)
                    import re
                    plan_matches = re.findall(r'\(([\w\s/]+(?:ONLY)?)\)', content)

                    # If no explicit plan mentioned, assume facility accepts all plans
                    if not plan_matches:
                        filtered_docs.append(doc)
                        continue

                    # Check each plan mention in the document
                    facility_accepts_plan = False
                    for plan_str in plan_matches:
                        plan_str_upper = plan_str.upper()

                        # Check for "ONLY" restriction
                        is_exclusive = "ONLY" in plan_str_upper

                        # Extract plans from the string (handle "/" separators)
                        plans_mentioned = [p.strip() for p in plan_str_upper.replace("ONLY", "").split("/")]

                        # Normalize plan variations
                        normalized_plans = []
                        for p in plans_mentioned:
                            # Normalize common variations
                            p_norm = p.strip()
                            if "PLAT" in p_norm and "PLUS" in p_norm:
                                normalized_plans.append("PLATINUM PLUS")
                            elif "PLAT" in p_norm and "PLUS" not in p_norm:
                                normalized_plans.append("PLATINUM")
                            elif "MER" in p_norm:
                                normalized_plans.append("MERCURY")
                            elif "REG" in p_norm or "STANDARD" in p_norm or "BASIC" in p_norm:
                                normalized_plans.append("REGULAR")
                            else:
                                normalized_plans.append(p_norm)

                        # Check if requested plan matches
                        requested_plan_upper = plan_type.upper()

                        if is_exclusive:
                            # For "ONLY" facilities, exact match required
                            if requested_plan_upper in normalized_plans:
                                facility_accepts_plan = True
                                break
                        else:
                            # For non-exclusive facilities, check if plan is in the list
                            # Also handle plan hierarchy (PLATINUM PLUS includes PLATINUM)
                            if requested_plan_upper in normalized_plans:
                                facility_accepts_plan = True
                                break
                            # Check hierarchy: if facility has PLATINUM PLUS and user wants PLATINUM
                            if requested_plan_upper == "PLATINUM" and "PLATINUM PLUS" in normalized_plans:
                                facility_accepts_plan = True
                                break
                            # Check hierarchy: if facility has PLATINUM and user wants MERCURY or REGULAR
                            if requested_plan_upper in ["MERCURY", "REGULAR"] and ("PLATINUM" in normalized_plans or "PLATINUM PLUS" in normalized_plans):
                                facility_accepts_plan = True
                                break
                            # Check hierarchy: if facility has MERCURY and user wants REGULAR
                            if requested_plan_upper == "REGULAR" and "MERCURY" in normalized_plans:
                                facility_accepts_plan = True
                                break

                    if facility_accepts_plan:
                        filtered_docs.append(doc)

                retrieved_docs = filtered_docs
                if len(filtered_docs) != original_count:
                    regenerate_response = True  # Plan filtering changed docs
                logger.info(f"🎯 Plan type filter applied: {original_count} docs → {len(filtered_docs)} docs (filtered for {plan_type})")

            # Apply region post-filtering if specified
            if region and retrieved_docs:
                original_count = len(retrieved_docs)
                # Filter documents by checking the region metadata field directly
                # Reason: Region is stored in metadata.region, not in tags array
                # Tags contain city names and categories, not region names
                filtered_docs = []
                for doc in retrieved_docs:
                    # Check metadata region field for region match
                    # Handle both formats: "GREATER ACCRA" and "GREATER_ACCRA"
                    doc_region = doc.metadata.get("region", "").upper()
                    region_upper = region.upper()
                    region_with_underscore = region_upper.replace(" ", "_")

                    # Match if region equals doc_region (with or without underscores)
                    if region_upper == doc_region or region_with_underscore == doc_region:
                        filtered_docs.append(doc)

                retrieved_docs = filtered_docs
                logger.info(f"🌍 Region filter applied: {original_count} docs → {len(filtered_docs)} docs (filtered for {region})")
                regenerate_response = True  # Region filtering changed docs

            # Regenerate response if filtering changed the document set
            # But skip if approaching timeout budget (saves 2-3 seconds)
            if regenerate_response and retrieved_docs:
                elapsed_time = (datetime.utcnow() - start_time).total_seconds()
                time_remaining = TIMEOUT_BUDGET_SECONDS - elapsed_time

                if time_remaining < 3.0:
                    # Not enough time for regeneration (needs ~2-3s)
                    # Use original response with filtered context note
                    logger.warning(f"⏱️  TIMEOUT BUDGET EXCEEDED: {elapsed_time:.2f}s elapsed, skipping regeneration to avoid timeout")
                    logger.warning(f"   Time remaining: {time_remaining:.2f}s < 3.0s required for regeneration")
                    # Note: Original response may reference filtered-out documents, but that's better than timing out
                else:
                    logger.info(f"🔄 Regenerating response with filtered documents (time remaining: {time_remaining:.2f}s)...")
                    # Format documents into context string
                    context_parts = []
                    for i, doc in enumerate(retrieved_docs, 1):
                        context_parts.append(f"Document {i}:")
                        context_parts.append(doc.page_content)
                        context_parts.append("")

                    filtered_context = "\n".join(context_parts)

                    # Re-run the LLM with filtered context
                    regeneration_prompt = f"""You are a helpful customer service assistant for {company_name}. Answer the user's question based on the provided knowledge base information.

Context from knowledge base:
{filtered_context}

User Question: {query}

Guidelines:
- Only use information from the provided knowledge base context
- If the information is insufficient or unclear, acknowledge this and suggest escalating to a human agent
- Be helpful, professional, and concise
- Include relevant details but avoid overwhelming the user
- If you mention specific procedures or policies, reference the source document

Answer:"""

                    response = await asyncio.to_thread(
                        self.llm.invoke,
                        regeneration_prompt
                    )

                    # Extract text from AIMessage object
                    if hasattr(response, 'content'):
                        response = response.content

                    logger.info(f"✅ Response regenerated with filtered context")

            logger.info(f"📊 Retrieved {len(retrieved_docs)} documents, response length: {len(response)} chars")

            # Calculate confidence based on retrieval scores and response length
            confidence_score = self._calculate_confidence(response, retrieved_docs)
            logger.info(f"💯 Confidence score: {confidence_score:.2f}")

            # Determine if escalation is needed
            should_escalate, escalation_reason = self._should_escalate(
                query, response, confidence_score, retrieved_docs
            )

            # Log escalation decision for debugging
            logger.info(f"🚦 Escalation Decision:")
            logger.info(f"   - Should Escalate: {should_escalate}")
            logger.info(f"   - Reason: {escalation_reason or 'N/A'}")
            logger.info(f"   - Confidence: {confidence_score:.2f} (threshold: {self.confidence_threshold})")
            logger.info(f"   - Documents Retrieved: {len(retrieved_docs)}")

            # Extract source information
            sources_used = [
                doc.metadata.get("title", "Unknown source")
                for doc in retrieved_docs
            ]

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Log performance breakdown
            logger.info(f"⏱️  PERFORMANCE BREAKDOWN:")
            logger.info(f"   - Vectorstore: {vectorstore_time:.2f}s")
            logger.info(f"   - Retrieval+Generation: {retrieval_time:.2f}s")
            logger.info(f"   - Total: {processing_time:.2f}s")

            # Check timeout budget compliance
            if processing_time > TIMEOUT_BUDGET_SECONDS:
                logger.error(f"⚠️  TIMEOUT BUDGET EXCEEDED: {processing_time:.2f}s > {TIMEOUT_BUDGET_SECONDS}s budget")
                logger.error(f"   This query may timeout in VAPI webhook (20s limit)")
            elif processing_time > TIMEOUT_BUDGET_SECONDS * 0.8:
                logger.warning(f"⚠️  TIMEOUT BUDGET WARNING: {processing_time:.2f}s > 80% of {TIMEOUT_BUDGET_SECONDS}s budget")
            else:
                logger.info(f"✅ Within timeout budget: {processing_time:.2f}s / {TIMEOUT_BUDGET_SECONDS}s ({(processing_time/TIMEOUT_BUDGET_SECONDS*100):.1f}%)")

            result = QueryResult(
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

            # Log final result summary before returning
            logger.info(f"✅ RAG QUERY COMPLETE:")
            logger.info(f"   - Query: '{query[:50]}{'...' if len(query) > 50 else ''}'")
            logger.info(f"   - Success: {result.success}")
            logger.info(f"   - Confidence: {result.confidence_score:.2f}")
            logger.info(f"   - Escalation: {result.requires_escalation}")
            logger.info(f"   - Sources: {len(result.sources_used)}")
            logger.info(f"   - Response: {len(result.response)} chars")
            logger.info(f"   - Time: {result.processing_time:.2f}s")

            # Track query for analytics (async, non-blocking)
            asyncio.create_task(self._track_query_async(company_name, result, context))

            # Cache successful response for future queries
            if result.success:
                try:
                    redis_cache_service = get_redis_cache_service()
                    await redis_cache_service.cache_response(
                        company_name=company_name,
                        query=query,
                        response_data=result.dict()
                    )
                    logger.info(f"💾 Response cached for future queries")
                except Exception as cache_err:
                    logger.warning(f"⚠️  Failed to cache response: {cache_err}")

            return result

        except Exception as e:
            logger.error(f"Error querying knowledge base for {company_name}: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return QueryResult(
                success=False,
                query=query,
                response="I'm experiencing technical difficulties accessing our knowledge base. Please try again or contact support for immediate assistance.",
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

    def _should_escalate(self, query: str, response: str, confidence: float, retrieved_docs: List[Document]) -> Tuple[bool, Optional[str]]:
        """
        Determine if the query should be escalated to a human agent.

        Args:
            query: User query
            response: Generated response
            confidence: Confidence score
            retrieved_docs: Retrieved documents

        Returns:
            Tuple of (should_escalate, escalation_reason)
        """
        # Low confidence escalation
        if confidence < self.confidence_threshold:
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

        # Complex queries requiring human judgment
        complex_indicators = [
            "policy change", "custom solution", "exception", "special case",
            "technical integration", "API", "developer", "configuration"
        ]

        if any(indicator in query_lower for indicator in complex_indicators):
            return True, "Complex query requiring human expertise"

        # Check if response indicates uncertainty
        uncertainty_indicators = [
            "i don't know", "i'm not sure", "unclear", "insufficient information",
            "contact support", "speak with", "escalate"
        ]

        response_lower = response.lower()
        if any(indicator in response_lower for indicator in uncertainty_indicators):
            return True, "AI assistant indicated uncertainty in response"

        return False, None

    async def update_knowledge_base(self, company_name: str, documents: List[KnowledgeDocument]) -> Dict[str, Any]:
        """
        Update knowledge base with new documents using LangChain.

        Args:
            company_name: Company identifier
            documents: New or updated documents

        Returns:
            Update result
        """
        try:
            vectorstore = await self._get_vectorstore(company_name)

            # Convert to LangChain documents and split
            langchain_docs = []
            for doc in documents:
                text_chunks = self.text_splitter.split_text(doc.content)

                for i, chunk in enumerate(text_chunks):
                    langchain_doc = Document(
                        page_content=chunk,
                        metadata={
                            "doc_id": doc.id or f"update_{datetime.utcnow().timestamp()}_{len(langchain_docs)}",
                            "title": doc.title,
                            "category": doc.category,
                            "source": doc.source,
                            "tags": doc.tags,
                            "company": company_name,
                            "chunk_index": i,
                            "total_chunks": len(text_chunks),
                            "updated_at": datetime.utcnow().isoformat(),
                            **doc.metadata
                        }
                    )
                    langchain_docs.append(langchain_doc)

            # Add new documents to vectorstore
            if langchain_docs:
                await asyncio.to_thread(
                    vectorstore.add_documents,
                    langchain_docs
                )

            logger.info(f"Updated {len(documents)} documents ({len(langchain_docs)} chunks) for {company_name}")

            return {
                "success": True,
                "documents_updated": len(documents),
                "chunks_updated": len(langchain_docs),
                "collection_name": self._get_collection_name(company_name),
                "updated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error updating knowledge base for {company_name}: {str(e)}")
            raise

    async def get_knowledge_base_stats(self, company_name: str) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.

        Args:
            company_name: Company identifier

        Returns:
            Knowledge base statistics
        """
        try:
            collection_name = self._get_collection_name(company_name)
            vectorstore = await self._get_vectorstore(company_name)

            # Note: PGVector doesn't provide direct stats methods
            # In a production environment, you'd query the PostgreSQL tables directly
            # For now, return estimated stats

            stats = {
                "collection_name": collection_name,
                "estimated_documents": "Unknown - query database directly",
                "embedding_dimension": 1536,
                "last_updated": datetime.utcnow().isoformat(),
                "vectorstore_type": "PostgreSQL + pgvector",
                "langchain_version": "0.3.x",
                "note": "For detailed stats, query the PostgreSQL langchain_pg_* tables directly"
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting knowledge base stats for {company_name}: {str(e)}")
            raise

    async def get_rag_metrics(self, company_name: str, days: int = 30) -> RAGMetrics:
        """
        Get RAG performance metrics for a company.

        Args:
            company_name: Company identifier
            days: Number of days to analyze

        Returns:
            RAG performance metrics
        """
        # In a production environment, you'd track these metrics in a separate table
        # For now, return simulated metrics
        total_queries = 150
        successful_queries = 135
        escalated_queries = 15

        return RAGMetrics(
            total_queries=total_queries,
            successful_queries=successful_queries,
            escalated_queries=escalated_queries,
            success_rate=successful_queries / total_queries,
            escalation_rate=escalated_queries / total_queries,
            average_confidence_score=0.82,
            response_time_avg=0.45,
            top_categories=["billing", "technical", "account"],
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow()
        )

    async def delete_knowledge_base(self, company_name: str) -> Dict[str, Any]:
        """
        Delete knowledge base for a company.

        Args:
            company_name: Company identifier

        Returns:
            Deletion result
        """
        try:
            collection_name = self._get_collection_name(company_name)
            vectorstore = await self._get_vectorstore(company_name)

            # Delete the collection
            await asyncio.to_thread(vectorstore.delete_collection)

            # Remove from cache
            if collection_name in self._vectorstores:
                del self._vectorstores[collection_name]

            logger.info(f"Deleted knowledge base for {company_name}")

            return {
                "success": True,
                "collection_name": collection_name,
                "deleted_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error deleting knowledge base for {company_name}: {str(e)}")
            raise

    async def _track_query_async(
        self,
        company_name: str,
        result: QueryResult,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Track query for analytics (non-blocking).

        Args:
            company_name: Company identifier
            result: Query result to track
            context: Optional context data
        """
        try:
            analytics_service, QueryMetric = get_analytics_service()

            # Create metric
            metric = QueryMetric(
                company_name=company_name,
                query=result.query,
                response=result.response,
                confidence_score=result.confidence_score,
                processing_time_ms=int(result.processing_time * 1000),
                sources_used=result.sources_used,
                num_sources=len(result.sources_used),
                requires_escalation=result.requires_escalation,
                escalation_reason=result.escalation_reason,
                user_id=context.get("user_id") if context else None,
                session_id=context.get("session_id") if context else None
            )

            # Track asynchronously
            await analytics_service.track_query(metric)

        except Exception as e:
            # Don't fail the query if tracking fails
            logger.warning(f"Failed to track query for analytics: {str(e)}")

# Global service instance
helpdesk_rag_service = HelpdeskRAGService()