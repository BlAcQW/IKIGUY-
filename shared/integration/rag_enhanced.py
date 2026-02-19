"""
Enhanced RAG Service with InkWave Improvements

This module extends the base RAG service with:
- LLMProviderService integration for automatic billing
- Streaming support with cost tracking
- Balance checks before queries
- Enhanced cost and token tracking

Usage:
    ```python
    from apps.shared.integration.rag_enhanced import EnhancedRAGService, EnhancedRAGConfig
    
    config = EnhancedRAGConfig(
        use_llm_provider_service=True,
        enable_billing=True,
        check_balance_before_query=True,
        # ... other RAG config options
    )
    
    rag = EnhancedRAGService(config)
    await rag.initialize()
    
    # Query with billing
    result = await rag.query_knowledge_base(
        collection_name="my_kb",
        query="What is...?",
        user_id="user_123"  # Required for billing
    )
    
    # Streaming query
    async for chunk in rag.query_knowledge_base_stream(
        collection_name="my_kb",
        query="What is...?",
        user_id="user_123"
    ):
        print(chunk, end='')
    ```
"""

import logging
import sys
from typing import Dict, List, Optional, Any, AsyncGenerator
from decimal import Decimal

# Import base RAG service
sys.path.insert(0, '/opt/kasaai/apps/shared')
from integration.rag import RAGService, RAGConfig, QueryResult, KnowledgeDocument

logger = logging.getLogger(__name__)


class EnhancedRAGConfig(RAGConfig):
    """Enhanced RAG configuration with billing support."""
    
    use_llm_provider_service: bool = True
    enable_billing: bool = True
    check_balance_before_query: bool = False


class EnhancedRAGService(RAGService):
    """
    Enhanced RAG service with InkWave improvements.
    
    Extends base RAGService with:
    - LLMProviderService integration for billing
    - Streaming query support
    - Balance checks
    - Cost tracking
    """
    
    def __init__(self, config: EnhancedRAGConfig):
        """Initialize enhanced RAG service."""
        super().__init__(config)
        self.config: EnhancedRAGConfig = config
        self._llm_provider_service = None
        self._initialized_enhanced = False
        
    async def initialize(self):
        """Initialize enhanced features."""
        if self._initialized_enhanced:
            return
            
        # Initialize base RAG service
        # (base service doesn't have initialize, but we ensure LLMProviderService is ready)
        if self.config.use_llm_provider_service:
            await self._initialize_llm_provider_service()
            
        self._initialized_enhanced = True
        logger.info("✅ Enhanced RAG service initialized")
        
    async def _initialize_llm_provider_service(self):
        """Initialize LLMProviderService for billing."""
        if self._llm_provider_service is None:
            try:
                from shared.services.llm_provider_service import (
                    LLMProviderService,
                    ChatRequest,
                    ChatMessage
                )
                
                self._llm_provider_service = LLMProviderService(
                    enable_billing=self.config.enable_billing
                )
                await self._llm_provider_service.initialize()
                logger.info("✅ LLMProviderService initialized for billing")
            except Exception as e:
                logger.error(f"Failed to initialize LLMProviderService: {e}")
                raise
                
    async def _check_balance(
        self,
        user_id: str,
        estimated_cost: float
    ) -> bool:
        """
        Check if user has sufficient balance.
        
        Args:
            user_id: User ID
            estimated_cost: Estimated cost for query
            
        Returns:
            True if sufficient balance, False otherwise
        """
        if not self.config.check_balance_before_query or estimated_cost <= 0:
            return True
            
        try:
            from shared.integration.wallet import WalletService, Currency
            
            wallet_service = WalletService()
            wallet = await wallet_service.get_wallet_by_user(
                user_id=user_id,
                currency=Currency.USD
            )
            
            if wallet and wallet.available_balance >= Decimal(str(estimated_cost)):
                return True
            else:
                logger.warning(
                    f"Insufficient balance for user {user_id}: "
                    f"required=${estimated_cost:.6f}, "
                    f"available=${float(wallet.available_balance) if wallet else 0:.6f}"
                )
                return False
        except Exception as e:
            logger.warning(f"Balance check failed (allowing request): {e}")
            return True  # Don't block if check fails
            
    async def query_knowledge_base(
        self,
        collection_name: str,
        query: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        system_prompt_template: Optional[str] = None
    ) -> QueryResult:
        """
        Query knowledge base with enhanced features (billing, balance checks).
        
        Args:
            collection_name: Collection to query
            query: User question
            user_id: User ID (required for billing)
            context: Additional context
            filters: Metadata filters
            system_prompt_template: Custom system prompt
            
        Returns:
            QueryResult with cost and token tracking
        """
        if not self._initialized_enhanced:
            await self.initialize()
            
        # Estimate cost if using LLMProviderService
        estimated_cost = 0.0
        if self.config.use_llm_provider_service and user_id:
            try:
                from shared.services.usage_calculator import UsageCalculator
                usage_calc = UsageCalculator()
                # Rough estimate: ~100 input tokens + ~200 output tokens
                estimated_cost = usage_calc.calculate_llm_cost(
                    input_tokens=len(query) // 4 + 100,
                    output_tokens=200,
                    model=self.config.llm_model
                )
                
                # Check balance if enabled
                if not await self._check_balance(user_id, estimated_cost):
                    return QueryResult(
                        success=False,
                        query=query,
                        response="Insufficient balance for this operation. Please top up your wallet.",
                        confidence_score=0.0,
                        sources_used=[],
                        requires_escalation=True,
                        escalation_reason="Insufficient balance",
                        tokens_used=0,
                        cost=0.0,
                        model_used=self.config.llm_model
                    )
            except Exception as e:
                logger.warning(f"Cost estimation/balance check failed: {e}")
        
        # Use LLMProviderService if enabled, otherwise use base implementation
        if self.config.use_llm_provider_service and self._llm_provider_service and user_id:
            return await self._query_with_llm_provider_service(
                collection_name=collection_name,
                query=query,
                user_id=user_id,
                context=context,
                filters=filters,
                system_prompt_template=system_prompt_template
            )
        else:
            # Fall back to base implementation
            result = await super().query_knowledge_base(
                collection_name=collection_name,
                query=query,
                context=context,
                filters=filters,
                system_prompt_template=system_prompt_template
            )
            # Add default cost/token fields
            result.tokens_used = result.tokens_used or 0
            result.cost = result.cost or 0.0
            result.model_used = result.model_used or self.config.llm_model
            return result
            
    async def _query_with_llm_provider_service(
        self,
        collection_name: str,
        query: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        system_prompt_template: Optional[str] = None
    ) -> QueryResult:
        """
        Query using LLMProviderService for billing integration.
        
        This method:
        1. Performs semantic search (using base RAG retrieval)
        2. Uses LLMProviderService for generation (with billing)
        3. Returns result with cost tracking
        """
        from shared.services.llm_provider_service import ChatRequest, ChatMessage
        
        # Get vectorstore and retrieve relevant documents
        vectorstore = await self._get_vectorstore(collection_name)
        
        search_kwargs = {
            "k": self.config.retrieval_k,
            "score_threshold": self.config.similarity_threshold
        }
        if filters:
            search_kwargs["filter"] = filters
            
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs=search_kwargs
        )
        
        # Retrieve relevant documents
        retrieved_docs = await asyncio.to_thread(
            retriever.get_relevant_documents,
            query
        )
        
        if not retrieved_docs:
            return QueryResult(
                success=False,
                query=query,
                response="I couldn't find relevant information in the knowledge base.",
                confidence_score=0.0,
                sources_used=[],
                requires_escalation=True,
                escalation_reason="No relevant documents found",
                tokens_used=0,
                cost=0.0,
                model_used=self.config.llm_model
            )
        
        # Build context from retrieved documents
        context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        # Build prompts
        if not system_prompt_template:
            system_prompt_template = """You are a helpful AI assistant. Answer based on the provided knowledge base context.

Context:
{context}

Guidelines:
- Only use information from the provided context
- If information is insufficient, acknowledge this
- Be helpful, professional, and concise"""
        
        system_prompt = system_prompt_template.format(context=context_text)
        user_prompt = f"Question: {query}\n\nAnswer:"
        
        # Query LLM using LLMProviderService (with billing)
        try:
            response = await self._llm_provider_service.chat(
                user_id=user_id,
                request=ChatRequest(
                    model_id=self.config.llm_model,
                    messages=[
                        ChatMessage(role="system", content=system_prompt),
                        ChatMessage(role="user", content=user_prompt)
                    ],
                    temperature=self.config.temperature,
                    max_tokens=1000
                ),
                skip_billing=not self.config.enable_billing
            )
            
            # Extract response and metadata
            answer = response.message
            tokens_used = response.usage.get('total_tokens', 0)
            cost = response.cost or 0.0
            
            # Calculate confidence
            confidence = self._calculate_confidence(answer, retrieved_docs)
            
            # Check escalation
            should_escalate, escalation_reason = self._should_escalate(
                query, answer, confidence, retrieved_docs
            )
            
            sources_used = [
                doc.metadata.get("title", "Unknown source")
                for doc in retrieved_docs
            ]
            
            return QueryResult(
                success=True,
                query=query,
                response=answer,
                confidence_score=confidence,
                sources_used=sources_used,
                requires_escalation=should_escalate,
                escalation_reason=escalation_reason,
                context_used=context is not None,
                tokens_used=tokens_used,
                cost=cost,
                model_used=self.config.llm_model
            )
            
        except Exception as e:
            logger.error(f"Enhanced RAG query failed: {e}")
            return QueryResult(
                success=False,
                query=query,
                response=f"I encountered an error: {str(e)}",
                confidence_score=0.0,
                sources_used=[],
                requires_escalation=True,
                escalation_reason="LLM query failed",
                error_message=str(e),
                tokens_used=0,
                cost=0.0,
                model_used=self.config.llm_model
            )
    
    async def query_knowledge_base_stream(
        self,
        collection_name: str,
        query: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        system_prompt_template: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream query results with billing integration.
        
        Yields:
            Text chunks as they are generated
        """
        if not self._initialized_enhanced:
            await self.initialize()
            
        if not self.config.use_llm_provider_service or not self._llm_provider_service:
            # Fall back to non-streaming if LLMProviderService not available
            result = await self.query_knowledge_base(
                collection_name=collection_name,
                query=query,
                user_id=user_id,
                context=context,
                filters=filters,
                system_prompt_template=system_prompt_template
            )
            yield result.response
            return
            
        # Retrieve documents (same as non-streaming)
        vectorstore = await self._get_vectorstore(collection_name)
        search_kwargs = {
            "k": self.config.retrieval_k,
            "score_threshold": self.config.similarity_threshold
        }
        if filters:
            search_kwargs["filter"] = filters
            
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs=search_kwargs
        )
        
        retrieved_docs = await asyncio.to_thread(
            retriever.get_relevant_documents,
            query
        )
        
        if not retrieved_docs:
            yield "I couldn't find relevant information in the knowledge base."
            return
        
        # Build context and prompts
        context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        if not system_prompt_template:
            system_prompt_template = """You are a helpful AI assistant. Answer based on the provided knowledge base context.

Context:
{context}

Guidelines:
- Only use information from the provided context
- If information is insufficient, acknowledge this
- Be helpful, professional, and concise"""
        
        system_prompt = system_prompt_template.format(context=context_text)
        user_prompt = f"Question: {query}\n\nAnswer:"
        
        # Stream from LLMProviderService
        from shared.services.llm_provider_service import ChatRequest, ChatMessage
        
        try:
            full_response = ""
            async for chunk in self._llm_provider_service.chat_stream(
                user_id=user_id,
                request=ChatRequest(
                    model_id=self.config.llm_model,
                    messages=[
                        ChatMessage(role="system", content=system_prompt),
                        ChatMessage(role="user", content=user_prompt)
                    ],
                    temperature=self.config.temperature,
                    max_tokens=1000,
                    stream=True
                ),
                skip_billing=not self.config.enable_billing
            ):
                if chunk.content:
                    full_response += chunk.content
                    yield chunk.content
                    
            logger.info(f"Streaming query completed: {len(full_response)} chars")
            
        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            yield f"Sorry, I encountered an error: {str(e)}"

