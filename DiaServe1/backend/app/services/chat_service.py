"""
Property Chat Service for EstateFlow.

Handles AI-powered chat interactions for property listings using LLM integration.
"""

import time
import re
from typing import List, Tuple, Optional
import logging

from app.models.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ChatSession,
    QuestionCategory,
    Source,
    MessageRole
)
from app.models.property import Property
from app.services.property_context_service import PropertyContextService

# Import local Gemini service (replaces missing shared library)
from app.integration.gemini_client import GeminiService

logger = logging.getLogger(__name__)


class PropertyChatService:
    """Service for AI-powered property chat interactions."""

    def __init__(self):
        """Initialize chat service with Gemini provider."""
        self.gemini_service = GeminiService(model="gemini-2.0-flash-exp")
        self.context_service = PropertyContextService()
        self._db = None

    def set_database(self, database):
        """Set database reference for conversation persistence."""
        self._db = database

    @property
    def conversations_collection(self):
        if self._db is None:
            return None
        return self._db["chat_conversations"]

    async def initialize(self):
        """Initialize the service (check Gemini availability)."""
        if not self.gemini_service.is_available():
            logger.warning("Gemini API key not configured - chat will use fallback responses")
        else:
            logger.info("Gemini service initialized successfully")

    def _get_system_prompt(self, language: str = "en") -> str:
        """
        Get system prompt for the AI assistant.

        Args:
            language: Language code (en, es, fr)

        Returns:
            System prompt string
        """
        prompts = {
            "en": """You are an expert real estate assistant helping potential buyers and renters learn about properties.

Your role:
- Answer questions using ONLY the provided property information
- If you don't have specific information, say "I don't have that information. Please contact the agent for details."
- Be friendly, professional, and helpful
- Provide concise answers (2-4 sentences maximum)
- Include specific numbers and data when available
- Never make up information about the property

When discussing mortgages or loans:
- Use standard assumptions (20% down payment, 7% interest rate, 30 years)
- Clearly mention these are estimates
- Recommend consulting a mortgage advisor for precise calculations

Important limitations:
- DO NOT make up information about the property
- DO NOT make promises or guarantees about availability
- DO NOT discuss pricing negotiations (direct to agent)
- For complex questions or viewing requests, suggest contacting the agent

Be conversational but professional. Focus on helping the user understand if this property meets their needs.""",

            "es": """Eres un asistente experto en bienes raíces que ayuda a compradores y arrendatarios potenciales a conocer propiedades.

Tu función:
- Responder preguntas usando SOLO la información de la propiedad proporcionada
- Si no tienes información específica, di "No tengo esa información. Por favor contacta al agente para más detalles."
- Sé amigable, profesional y útil
- Proporciona respuestas concisas (2-4 oraciones máximo)
- Incluye números y datos específicos cuando estén disponibles
- Nunca inventes información sobre la propiedad

Al discutir hipotecas o préstamos:
- Usa suposiciones estándar (20% de enganche, 7% de interés, 30 años)
- Menciona claramente que son estimaciones
- Recomienda consultar a un asesor hipotecario para cálculos precisos

Limitaciones importantes:
- NO inventes información sobre la propiedad
- NO hagas promesas o garantías sobre disponibilidad
- NO discutas negociaciones de precio (dirige al agente)
- Para preguntas complejas o solicitudes de visita, sugiere contactar al agente

Sé conversacional pero profesional. Enfócate en ayudar al usuario a entender si esta propiedad satisface sus necesidades.""",

            "fr": """Vous êtes un assistant expert en immobilier aidant les acheteurs et locataires potentiels à découvrir des propriétés.

Votre rôle:
- Répondre aux questions en utilisant UNIQUEMENT les informations de propriété fournies
- Si vous n'avez pas d'informations spécifiques, dites "Je n'ai pas cette information. Veuillez contacter l'agent pour plus de détails."
- Soyez amical, professionnel et utile
- Fournissez des réponses concises (2-4 phrases maximum)
- Incluez des chiffres et données spécifiques quand disponibles
- N'inventez jamais d'informations sur la propriété

Lors de discussions sur les prêts hypothécaires:
- Utilisez des hypothèses standard (20% d'acompte, 7% d'intérêt, 30 ans)
- Mentionnez clairement que ce sont des estimations
- Recommandez de consulter un conseiller hypothécaire pour des calculs précis

Limitations importantes:
- NE PAS inventer d'informations sur la propriété
- NE PAS faire de promesses ou garanties sur la disponibilité
- NE PAS discuter des négociations de prix (diriger vers l'agent)
- Pour les questions complexes ou demandes de visite, suggérez de contacter l'agent

Soyez conversationnel mais professionnel. Concentrez-vous sur aider l'utilisateur à comprendre si cette propriété répond à ses besoins."""
        }

        return prompts.get(language, prompts["en"])

    def _categorize_question(self, message: str) -> QuestionCategory:
        """
        Categorize the user's question.

        Args:
            message: User's question

        Returns:
            QuestionCategory enum
        """
        message_lower = message.lower()

        # Pet-related keywords
        if any(keyword in message_lower for keyword in [
            "pet", "dog", "cat", "animal", "puppy", "kitten"
        ]):
            return QuestionCategory.PET_POLICY

        # Financial keywords
        if any(keyword in message_lower for keyword in [
            "mortgage", "loan", "financing", "down payment", "monthly payment",
            "cost", "price", "afford", "hoa", "fee", "tax", "insurance"
        ]):
            return QuestionCategory.FINANCIAL

        # Location/Neighborhood keywords
        if any(keyword in message_lower for keyword in [
            "school", "restaurant", "shop", "store", "park", "amenity",
            "nearby", "close", "walk", "distance", "neighborhood", "area"
        ]):
            return QuestionCategory.LOCATION

        # Safety keywords
        if any(keyword in message_lower for keyword in [
            "safe", "safety", "crime", "security", "walkability", "walk score"
        ]):
            return QuestionCategory.NEIGHBORHOOD_SAFETY

        # Availability keywords
        if any(keyword in message_lower for keyword in [
            "view", "tour", "visit", "available", "when", "schedule", "appointment"
        ]):
            return QuestionCategory.AVAILABILITY

        # Property features
        if any(keyword in message_lower for keyword in [
            "bedroom", "bathroom", "kitchen", "garage", "pool", "garden",
            "balcony", "sqft", "square", "room", "floor", "story", "furnished"
        ]):
            return QuestionCategory.PROPERTY_FEATURES

        return QuestionCategory.GENERAL

    def _get_suggested_questions(
        self,
        category: QuestionCategory,
        property_data: Property,
        language: str = "en"
    ) -> List[str]:
        """
        Generate suggested follow-up questions based on category.

        Args:
            category: Question category
            property_data: Property data
            language: Language code

        Returns:
            List of suggested questions
        """
        suggestions_en = {
            QuestionCategory.PET_POLICY: [
                "Are there any breed restrictions?",
                "Is there a dog park nearby?",
                "What's the pet deposit amount?"
            ],
            QuestionCategory.FINANCIAL: [
                "What are the monthly costs (HOA, utilities)?",
                "Is financing available?",
                "What's included in the HOA fees?"
            ],
            QuestionCategory.LOCATION: [
                "What's the walkability score?",
                "How far is the nearest grocery store?",
                "Are there good schools nearby?"
            ],
            QuestionCategory.NEIGHBORHOOD_SAFETY: [
                "What's the crime rate in this area?",
                "Is there 24/7 security?",
                "How well-lit are the streets at night?"
            ],
            QuestionCategory.AVAILABILITY: [
                "Can I schedule a virtual tour?",
                "When is the property available?",
                "How do I contact the agent?"
            ],
            QuestionCategory.PROPERTY_FEATURES: [
                "Is the property furnished?",
                "What appliances are included?",
                f"Are all {property_data.features.bedrooms} bedrooms the same size?"
            ],
            QuestionCategory.GENERAL: [
                "What makes this property special?",
                "Tell me about the neighborhood",
                "What are the monthly costs?"
            ]
        }

        # For now, return English suggestions (multi-language can be added later)
        return suggestions_en.get(category, suggestions_en[QuestionCategory.GENERAL])

    def _extract_sources(
        self,
        property_data: Property,
        question: str,
        answer: str
    ) -> List[Source]:
        """
        Extract sources used to answer the question.

        Args:
            property_data: Property data
            question: User's question
            answer: AI's answer

        Returns:
            List of sources
        """
        sources = []
        question_lower = question.lower()
        answer_lower = answer.lower()

        # Check if pet policy was discussed
        if "pet" in question_lower or "dog" in question_lower or "cat" in question_lower:
            sources.append(Source(
                type="property_data",
                field="features.pet_policy",
                value=property_data.features.pet_policy
            ))

        # Check if price was discussed
        if any(word in question_lower for word in ["price", "cost", "afford", "mortgage"]):
            sources.append(Source(
                type="property_data",
                field="financial.price_usd",
                value=property_data.financial.price_usd
            ))

        # Check if schools were discussed
        if "school" in question_lower or "school" in answer_lower:
            if property_data.neighborhood_data and property_data.neighborhood_data.schools:
                sources.append(Source(
                    type="property_data",
                    field="neighborhood_data.schools",
                    value=f"{len(property_data.neighborhood_data.schools)} schools"
                ))

        # Check if location/neighborhood was discussed
        if any(word in question_lower for word in ["location", "neighborhood", "area", "nearby"]):
            sources.append(Source(
                type="property_data",
                field="location",
                value=f"{property_data.location.city}, {property_data.location.neighborhood}"
            ))

        # If it's a mortgage calculation
        if "monthly payment" in answer_lower or "down payment" in answer_lower:
            sources.append(Source(
                type="calculation",
                field="mortgage_estimate",
                value="Standard 20% down, 7% interest, 30 years"
            ))

        # Default source if none found
        if not sources:
            sources.append(Source(
                type="property_data",
                field="general",
                value="Property information"
            ))

        return sources

    async def chat(
        self,
        request: ChatRequest,
        property_data: Property,
        organization_id: str,
        user_id: Optional[str] = None
    ) -> ChatResponse:
        """
        Process chat request and generate AI response.

        Args:
            request: Chat request with message and property ID
            property_data: Property object to chat about
            organization_id: Organization ID for billing
            user_id: Optional user ID for billing

        Returns:
            ChatResponse with AI reply and metadata
        """
        start_time = time.time()

        # 2. Build property context
        property_context = self.context_service.build_property_context(
            property_data=property_data,
            language=request.language
        )

        # 3. Categorize question
        category = self._categorize_question(request.message)

        # 4. Check if mortgage calculation is needed
        mortgage_info = None
        if category == QuestionCategory.FINANCIAL and any(
            keyword in request.message.lower()
            for keyword in ["mortgage", "loan", "monthly payment", "down payment"]
        ):
            mortgage_data = self.context_service.get_mortgage_estimate(
                price=property_data.financial.price_usd
            )
            mortgage_info = self.context_service.format_mortgage_response(
                mortgage_data=mortgage_data,
                language=request.language
            )

        # 5. Build Gemini prompt
        system_prompt = self._get_system_prompt(language=request.language)

        # Build combined prompt with all context
        prompt_parts = [
            system_prompt,
            "\n\n---\n\nProperty Information:\n",
            property_context
        ]

        # Add mortgage calculation if relevant
        if mortgage_info:
            prompt_parts.append("\n\n---\n\nMortgage Calculation:\n")
            prompt_parts.append(mortgage_info)

        # Add conversation history (last 5 messages for context)
        if request.conversation_history:
            prompt_parts.append("\n\n---\n\nConversation History:\n")
            for msg in request.conversation_history[-5:]:
                prompt_parts.append(f"{msg.role.value.upper()}: {msg.content}\n")

        # Add current user message
        prompt_parts.append(f"\n\n---\n\nUser Question: {request.message}\n\nResponse:")

        full_prompt = "".join(prompt_parts)

        # 6. Call Gemini service
        try:
            if not self.gemini_service.is_available():
                raise Exception("Gemini API not configured")

            gemini_response = await self.gemini_service.generate_content(
                prompt=full_prompt,
                temperature=0.7,
                max_output_tokens=500,  # Concise responses
                timeout=30.0
            )

            if gemini_response.get("success"):
                reply = gemini_response.get("content", "")
                model_used = gemini_response.get("model", "gemini-2.0-flash-exp")
            else:
                raise Exception("Gemini response not successful")

        except Exception as e:
            logger.error(f"Gemini service error: {e}")
            # Fallback response
            reply = "I apologize, but I'm having trouble processing your question right now. Please contact the agent for assistance."
            model_used = "fallback"

        # 7. Extract sources
        sources = self._extract_sources(
            property_data=property_data,
            question=request.message,
            answer=reply
        )

        # 8. Generate suggested questions
        suggested_questions = self._get_suggested_questions(
            category=category,
            property_data=property_data,
            language=request.language
        )

        # 9. Calculate confidence (simple heuristic based on source count and category)
        confidence = 0.9 if category != QuestionCategory.GENERAL else 0.7
        if "don't have" in reply.lower() or "contact the agent" in reply.lower():
            confidence = 0.5

        # 10. Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        response = ChatResponse(
            reply=reply,
            sources=sources,
            confidence=confidence,
            question_category=category,
            suggested_questions=suggested_questions[:3],  # Limit to 3
            processing_time_ms=processing_time_ms,
            model_used=model_used
        )

        # Persist conversation
        await self._persist_message(
            property_id=request.property_id,
            property_name=property_data.name,
            user_message=request.message,
            assistant_reply=reply,
            organization_id=organization_id,
            user_id=user_id
        )

        return response

    # ==================== Conversation Persistence ====================

    async def _persist_message(
        self,
        property_id: str,
        property_name: str,
        user_message: str,
        assistant_reply: str,
        organization_id: str,
        user_id: Optional[str] = None
    ):
        """Persist chat messages to the conversation collection."""
        if not self.conversations_collection:
            return

        from datetime import datetime
        import uuid

        now = datetime.utcnow()

        # Find existing conversation for this user + property
        query = {
            "property_id": property_id,
            "organization_id": organization_id
        }
        if user_id:
            query["user_id"] = user_id

        existing = await self.conversations_collection.find_one(query, sort=[("updated_at", -1)])

        user_msg = {"role": "user", "content": user_message, "timestamp": now}
        assistant_msg = {"role": "assistant", "content": assistant_reply, "timestamp": now}

        if existing:
            # Append to existing conversation
            await self.conversations_collection.update_one(
                {"id": existing["id"]},
                {
                    "$push": {"messages": {"$each": [user_msg, assistant_msg]}},
                    "$set": {"updated_at": now}
                }
            )
        else:
            # Create new conversation
            conversation = {
                "id": str(uuid.uuid4()),
                "property_id": property_id,
                "property_name": property_name,
                "user_id": user_id,
                "organization_id": organization_id,
                "messages": [user_msg, assistant_msg],
                "created_at": now,
                "updated_at": now,
                "metadata": {}
            }
            await self.conversations_collection.insert_one(conversation)

    async def list_conversations(
        self,
        organization_id: str,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple:
        """List chat conversations."""
        if not self.conversations_collection:
            return [], 0

        query = {"organization_id": organization_id}
        if user_id:
            query["user_id"] = user_id

        total = await self.conversations_collection.count_documents(query)
        cursor = self.conversations_collection.find(query).sort("updated_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)

        conversations = []
        for doc in docs:
            doc.pop("_id", None)
            conversations.append(ChatSession(**doc))

        return conversations, total

    async def get_conversation(
        self,
        conversation_id: str,
        organization_id: str
    ) -> Optional[ChatSession]:
        """Get a single conversation by ID."""
        if not self.conversations_collection:
            return None

        doc = await self.conversations_collection.find_one({
            "id": conversation_id,
            "organization_id": organization_id
        })

        if not doc:
            return None

        doc.pop("_id", None)
        return ChatSession(**doc)

    async def delete_conversation(
        self,
        conversation_id: str,
        organization_id: str
    ) -> bool:
        """Delete a conversation."""
        if not self.conversations_collection:
            return False

        result = await self.conversations_collection.delete_one({
            "id": conversation_id,
            "organization_id": organization_id
        })
        return result.deleted_count > 0
