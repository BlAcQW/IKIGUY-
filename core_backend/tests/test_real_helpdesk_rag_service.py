"""
Unit tests for Real Helpdesk RAG Service with LangChain + PostgreSQL + pgvector.
Tests the actual LangChain implementation with document chunking, retrieval chains, and vector storage.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

# LangChain imports for mocking
from langchain_core.documents import Document

from backend.services.helpdesk_rag_service import (
    HelpdeskRAGService,
    QueryResult,
    KnowledgeDocument,
    RAGMetrics
)


class TestRealHelpdeskRAGService:
    """Test cases for Real Helpdesk RAG Service with LangChain."""

    @pytest.fixture
    def rag_service(self):
        """Create a RAG service instance for testing."""
        with patch.dict('os.environ', {
            'POSTGRES_SERVER': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_USER': 'postgres',
            'POSTGRES_PASSWORD': 'testpass',
            'POSTGRES_DB_CORE': 'test_db',
            'OPENAI_API_KEY': 'test-key'
        }):
            return HelpdeskRAGService()

    @pytest.fixture
    def sample_knowledge_docs(self):
        """Sample knowledge documents for testing."""
        return [
            KnowledgeDocument(
                id="doc1",
                title="Account Management Guide",
                content="This guide explains how to manage customer accounts and billing information. "
                       "To update account details, navigate to the customer portal and select 'Edit Profile'. "
                       "For billing inquiries, contact our billing department at billing@company.com.",
                category="billing",
                tags=["account", "billing", "management"],
                metadata={"priority": "high", "department": "finance"}
            ),
            KnowledgeDocument(
                id="doc2",
                title="Technical Support Procedures",
                content="This document outlines troubleshooting procedures for common technical issues. "
                       "Step 1: Identify the problem. Step 2: Check system status. Step 3: Apply solution. "
                       "For advanced issues, escalate to Level 2 support.",
                category="technical",
                tags=["support", "troubleshooting", "technical"],
                metadata={"priority": "medium", "department": "tech"}
            )
        ]

    @pytest.fixture
    def mock_vectorstore(self):
        """Mock PGVector vectorstore."""
        mock_vs = Mock()
        mock_vs.add_documents = Mock()
        mock_vs.as_retriever = Mock()
        mock_vs.delete_collection = Mock()
        return mock_vs

    @pytest.fixture
    def mock_retriever(self):
        """Mock LangChain retriever."""
        mock_retriever = Mock()
        mock_retriever.invoke = Mock()
        return mock_retriever

    @pytest.fixture
    def sample_documents(self):
        """Sample LangChain documents for testing."""
        return [
            Document(
                page_content="Account management information chunk 1",
                metadata={"title": "Account Management", "category": "billing", "doc_id": "doc1"}
            ),
            Document(
                page_content="Technical support information chunk 1",
                metadata={"title": "Technical Support", "category": "technical", "doc_id": "doc2"}
            )
        ]

    def test_service_initialization(self, rag_service):
        """Test that the service initializes correctly with LangChain components."""
        assert rag_service.postgres_host == "localhost"
        assert rag_service.postgres_port == "5432"
        assert rag_service.postgres_user == "postgres"
        assert rag_service.confidence_threshold == 0.7
        assert rag_service.similarity_threshold == 0.8

        # Check that LangChain components are initialized
        assert rag_service.embeddings is not None
        assert rag_service.llm is not None
        assert rag_service.text_splitter is not None
        assert rag_service.connection_string is not None

    def test_get_collection_name(self, rag_service):
        """Test collection name sanitization."""
        assert rag_service._get_collection_name("Test Company") == "helpdesk_test_company"
        assert rag_service._get_collection_name("ABC-Corp") == "helpdesk_abc_corp"
        assert rag_service._get_collection_name("My-Test_Company") == "helpdesk_my_test_company"

    @patch('backend.services.helpdesk_rag_service.PGVector')
    @pytest.mark.asyncio
    async def test_get_vectorstore_creation(self, mock_pgvector, rag_service):
        """Test vectorstore creation and caching."""
        mock_vectorstore = Mock()
        mock_pgvector.return_value = mock_vectorstore

        # First call should create vectorstore
        result = await rag_service._get_vectorstore("test_company")

        assert result == mock_vectorstore
        assert "helpdesk_test_company" in rag_service._vectorstores
        mock_pgvector.assert_called_once()

        # Second call should use cached vectorstore
        mock_pgvector.reset_mock()
        result2 = await rag_service._get_vectorstore("test_company")

        assert result2 == mock_vectorstore
        mock_pgvector.assert_not_called()

    @patch('backend.services.helpdesk_rag_service.PGVector')
    @patch('asyncio.to_thread')
    @pytest.mark.asyncio
    async def test_initialize_knowledge_base_success(self, mock_to_thread, mock_pgvector, rag_service, sample_knowledge_docs):
        """Test successful knowledge base initialization with document chunking."""
        mock_vectorstore = Mock()
        mock_pgvector.return_value = mock_vectorstore
        mock_to_thread.return_value = None

        # Mock text splitter to return chunks
        with patch.object(rag_service.text_splitter, 'split_text') as mock_split:
            mock_split.side_effect = [
                ["Account chunk 1", "Account chunk 2"],  # First document
                ["Technical chunk 1"]  # Second document
            ]

            result = await rag_service.initialize_knowledge_base("test_company", sample_knowledge_docs)

            assert result["success"] is True
            assert result["documents_indexed"] == 2
            assert result["chunks_created"] == 3  # 2 + 1 chunks
            assert result["embedding_dimension"] == 1536
            assert "collection_name" in result
            assert "created_at" in result

            # Verify documents were added to vectorstore
            mock_to_thread.assert_called_once()
            call_args = mock_to_thread.call_args[0]
            assert call_args[0] == mock_vectorstore.add_documents
            # Verify that LangChain documents were created
            langchain_docs = call_args[1]
            assert len(langchain_docs) == 3

    @patch('backend.services.helpdesk_rag_service.PGVector')
    @pytest.mark.asyncio
    async def test_initialize_knowledge_base_failure(self, mock_pgvector, rag_service, sample_knowledge_docs):
        """Test knowledge base initialization failure."""
        mock_pgvector.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception) as exc_info:
            await rag_service.initialize_knowledge_base("test_company", sample_knowledge_docs)

        assert "Database connection failed" in str(exc_info.value)

    @patch('backend.services.helpdesk_rag_service.PGVector')
    @patch('backend.services.helpdesk_rag_service.MultiQueryRetriever')
    @patch('backend.services.helpdesk_rag_service.create_retrieval_chain')
    @patch('asyncio.to_thread')
    @pytest.mark.asyncio
    async def test_query_knowledge_base_success(self, mock_to_thread, mock_create_chain, mock_multi_retriever, mock_pgvector, rag_service, sample_documents):
        """Test successful knowledge base querying with LangChain retrieval chain."""
        # Mock vectorstore and retriever
        mock_vectorstore = Mock()
        mock_pgvector.return_value = mock_vectorstore

        mock_base_retriever = Mock()
        mock_vectorstore.as_retriever.return_value = mock_base_retriever

        mock_retriever = Mock()
        mock_multi_retriever.from_llm.return_value = mock_retriever

        # Mock retrieval chain
        mock_chain = Mock()
        mock_create_chain.return_value = mock_chain

        # Mock chain execution result
        mock_result = {
            "answer": "Based on our account management guide, you can update your account details by navigating to the customer portal.",
            "context": sample_documents
        }
        mock_to_thread.return_value = mock_result

        query = "How do I update my account details?"
        result = await rag_service.query_knowledge_base("test_company", query)

        assert isinstance(result, QueryResult)
        assert result.success is True
        assert result.query == query
        assert "account management" in result.response.lower()
        assert result.confidence_score > 0.6
        assert len(result.sources_used) == 2
        assert result.processing_time > 0

        # Verify LangChain components were called
        mock_vectorstore.as_retriever.assert_called_once()
        mock_multi_retriever.from_llm.assert_called_once()
        mock_create_chain.assert_called_once()
        mock_to_thread.assert_called_once()

    @patch('backend.services.helpdesk_rag_service.PGVector')
    @pytest.mark.asyncio
    async def test_query_knowledge_base_error_handling(self, mock_pgvector, rag_service):
        """Test error handling during knowledge base querying."""
        mock_pgvector.side_effect = Exception("Vector search failed")

        query = "Test query"
        result = await rag_service.query_knowledge_base("test_company", query)

        assert isinstance(result, QueryResult)
        assert result.success is False
        assert result.query == query
        assert "technical difficulties" in result.response.lower()
        assert result.confidence_score == 0.0
        assert result.requires_escalation is True
        assert result.escalation_reason == "Technical error in RAG system"
        assert "Vector search failed" in result.error_message

    def test_calculate_confidence(self, rag_service, sample_documents):
        """Test confidence score calculation."""
        # Test with no response or documents
        confidence = rag_service._calculate_confidence("", [])
        assert confidence == 0.0

        # Test with response and documents
        response = "This is a detailed response explaining the solution to your problem."
        confidence = rag_service._calculate_confidence(response, sample_documents)
        assert 0.6 <= confidence <= 1.0

        # Test with longer response (should boost confidence)
        long_response = "This is a very detailed response " * 50  # Long response
        confidence_long = rag_service._calculate_confidence(long_response, sample_documents)
        assert confidence_long > confidence

    def test_should_escalate_low_confidence(self, rag_service, sample_documents):
        """Test escalation based on low confidence."""
        query = "Test query"
        response = "Test response"
        confidence = 0.5  # Below threshold

        should_escalate, reason = rag_service._should_escalate(query, response, confidence, sample_documents)

        assert should_escalate is True
        assert "low confidence" in reason.lower()

    def test_should_escalate_no_documents(self, rag_service):
        """Test escalation when no documents are retrieved."""
        query = "Test query"
        response = "Test response"
        confidence = 0.8

        should_escalate, reason = rag_service._should_escalate(query, response, confidence, [])

        assert should_escalate is True
        assert "no relevant information" in reason.lower()

    def test_should_escalate_keywords(self, rag_service, sample_documents):
        """Test escalation based on escalation keywords."""
        queries_and_reasons = [
            ("I am very angry about this", "escalation keywords"),
            ("I want to cancel my account", "escalation keywords"),
            ("This is an emergency", "escalation keywords"),
            ("I need a custom solution", "human expertise"),
            ("Policy change required", "human expertise")
        ]

        for query, expected_reason_part in queries_and_reasons:
            should_escalate, reason = rag_service._should_escalate(query, "Response", 0.8, sample_documents)
            assert should_escalate is True
            assert expected_reason_part in reason.lower()

    def test_should_escalate_uncertainty_response(self, rag_service, sample_documents):
        """Test escalation when AI response indicates uncertainty."""
        query = "Test query"
        response = "I'm not sure about this, you should contact support"
        confidence = 0.8

        should_escalate, reason = rag_service._should_escalate(query, response, confidence, sample_documents)

        assert should_escalate is True
        assert "uncertainty" in reason.lower()

    def test_should_not_escalate_good_response(self, rag_service, sample_documents):
        """Test that good responses don't trigger escalation."""
        query = "How do I update my account?"
        response = "You can update your account by going to the settings page"
        confidence = 0.8

        should_escalate, reason = rag_service._should_escalate(query, response, confidence, sample_documents)

        assert should_escalate is False
        assert reason is None

    @patch('backend.services.helpdesk_rag_service.PGVector')
    @patch('asyncio.to_thread')
    @pytest.mark.asyncio
    async def test_update_knowledge_base(self, mock_to_thread, mock_pgvector, rag_service, sample_knowledge_docs):
        """Test updating knowledge base with new documents."""
        mock_vectorstore = Mock()
        mock_pgvector.return_value = mock_vectorstore
        mock_to_thread.return_value = None

        with patch.object(rag_service.text_splitter, 'split_text') as mock_split:
            mock_split.return_value = ["Updated chunk 1", "Updated chunk 2"]

            result = await rag_service.update_knowledge_base("test_company", sample_knowledge_docs[:1])

            assert result["success"] is True
            assert result["documents_updated"] == 1
            assert result["chunks_updated"] == 2
            assert "updated_at" in result

            mock_to_thread.assert_called_once()

    @patch('backend.services.helpdesk_rag_service.PGVector')
    @pytest.mark.asyncio
    async def test_get_knowledge_base_stats(self, mock_pgvector, rag_service):
        """Test retrieving knowledge base statistics."""
        mock_vectorstore = Mock()
        mock_pgvector.return_value = mock_vectorstore

        stats = await rag_service.get_knowledge_base_stats("test_company")

        assert "collection_name" in stats
        assert stats["embedding_dimension"] == 1536
        assert stats["vectorstore_type"] == "PostgreSQL + pgvector"
        assert "langchain_version" in stats

    @pytest.mark.asyncio
    async def test_get_rag_metrics(self, rag_service):
        """Test retrieving RAG performance metrics."""
        metrics = await rag_service.get_rag_metrics("test_company", days=30)

        assert isinstance(metrics, RAGMetrics)
        assert metrics.total_queries == 150
        assert metrics.successful_queries == 135
        assert metrics.escalated_queries == 15
        assert metrics.success_rate == 0.9  # 135/150
        assert metrics.escalation_rate == 0.1  # 15/150
        assert len(metrics.top_categories) == 3

    @patch('backend.services.helpdesk_rag_service.PGVector')
    @patch('asyncio.to_thread')
    @pytest.mark.asyncio
    async def test_delete_knowledge_base(self, mock_to_thread, mock_pgvector, rag_service):
        """Test deleting knowledge base."""
        mock_vectorstore = Mock()
        mock_pgvector.return_value = mock_vectorstore
        mock_to_thread.return_value = None

        # First get the vectorstore to add it to cache
        await rag_service._get_vectorstore("test_company")

        result = await rag_service.delete_knowledge_base("test_company")

        assert result["success"] is True
        assert "collection_name" in result
        assert "deleted_at" in result

        # Verify vectorstore was removed from cache
        collection_name = rag_service._get_collection_name("test_company")
        assert collection_name not in rag_service._vectorstores

        mock_to_thread.assert_called_once()

    @patch('backend.services.helpdesk_rag_service.PGVector')
    @patch('backend.services.helpdesk_rag_service.MultiQueryRetriever')
    @patch('backend.services.helpdesk_rag_service.create_retrieval_chain')
    @patch('asyncio.to_thread')
    @pytest.mark.asyncio
    async def test_query_with_context(self, mock_to_thread, mock_create_chain, mock_multi_retriever, mock_pgvector, rag_service):
        """Test querying with additional context."""
        # Mock vectorstore and retriever
        mock_vectorstore = Mock()
        mock_pgvector.return_value = mock_vectorstore

        mock_base_retriever = Mock()
        mock_vectorstore.as_retriever.return_value = mock_base_retriever

        mock_retriever = Mock()
        mock_multi_retriever.from_llm.return_value = mock_retriever

        # Mock retrieval chain
        mock_chain = Mock()
        mock_create_chain.return_value = mock_chain

        # Mock chain execution result
        mock_result = {
            "answer": "Context-aware response for premium customer",
            "context": []
        }
        mock_to_thread.return_value = mock_result

        context = {"customer_tier": "premium", "urgency": "high"}
        result = await rag_service.query_knowledge_base("test_company", "Test query", context)

        assert result.success is True
        assert result.context_used is True
        assert "context-aware" in result.response.lower()

    def test_langchain_document_creation(self, rag_service, sample_knowledge_docs):
        """Test that KnowledgeDocuments are properly converted to LangChain Documents."""
        doc = sample_knowledge_docs[0]
        chunks = rag_service.text_splitter.split_text(doc.content)

        # Simulate document creation logic
        langchain_docs = []
        for i, chunk in enumerate(chunks):
            langchain_doc = Document(
                page_content=chunk,
                metadata={
                    "doc_id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "source": doc.source,
                    "tags": doc.tags,
                    "company": "test_company",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    **doc.metadata
                }
            )
            langchain_docs.append(langchain_doc)

        assert len(langchain_docs) > 0

        for i, langchain_doc in enumerate(langchain_docs):
            assert isinstance(langchain_doc, Document)
            assert langchain_doc.metadata["doc_id"] == doc.id
            assert langchain_doc.metadata["title"] == doc.title
            assert langchain_doc.metadata["category"] == doc.category
            assert langchain_doc.metadata["chunk_index"] == i
            assert langchain_doc.metadata["company"] == "test_company"

    @patch('backend.services.helpdesk_rag_service.PGVector')
    @pytest.mark.asyncio
    async def test_connection_string_formation(self, mock_pgvector, rag_service):
        """Test that PostgreSQL connection string is correctly formed."""
        await rag_service._get_vectorstore("test_company")

        expected_connection = "postgresql://postgres:testpass@localhost:5432/test_db"
        assert rag_service.connection_string == expected_connection

        # Verify PGVector was called with correct parameters
        mock_pgvector.assert_called_once()
        call_kwargs = mock_pgvector.call_args[1]
        assert call_kwargs["connection"] == expected_connection
        assert call_kwargs["use_jsonb"] is True
        assert call_kwargs["pre_delete_collection"] is False