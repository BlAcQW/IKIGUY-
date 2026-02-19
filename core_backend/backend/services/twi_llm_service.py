"""
LLM Service for Twi/Akan Conversational AI
Supports multiple LLM backends with Twi language adaptation
"""

import os
import json
import asyncio
import logging
from typing import Optional, Dict, List, Any, AsyncGenerator
from datetime import datetime
from enum import Enum
import aiohttp
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    GROQ = "groq"


class TwiLLMService:
    """Service for Twi/Akan language LLM interactions"""
    
    def __init__(self, provider: LLMProvider = LLMProvider.OPENAI):
        """
        Initialize LLM service
        
        Args:
            provider: LLM provider to use
        """
        self.provider = provider
        self.api_key = self._get_api_key()
        
        # System prompts for Twi conversation
        self.system_prompts = {
            "general": self._get_general_prompt(),
            "healthcare": self._get_healthcare_prompt(),
            "education": self._get_education_prompt(),
            "finance": self._get_finance_prompt()
        }
        
        # Twi language patterns
        self.twi_patterns = {
            "greetings": ["Akwaaba", "Ɛte sɛn", "Maakye", "Maaha", "Maadwo"],
            "responses": ["Aane", "Daabi", "Meda wo ase", "Mepa wo kyɛw"],
            "questions": ["Ɛyɛ dɛn", "Wobɛn", "Ɛwɔ he", "Bere bɛn"]
        }
        
    def _get_api_key(self) -> Optional[str]:
        """Get API key for the selected provider"""
        key_mapping = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.GOOGLE: "GEMINI_API_KEY",  # Use GEMINI_API_KEY
            LLMProvider.GROQ: "GROQ_API_KEY"
        }
        
        env_var = key_mapping.get(self.provider)
        if env_var:
            return os.getenv(env_var)
        return None
        
    def _get_general_prompt(self) -> str:
        """Get general system prompt for Twi conversation"""
        return """You are a helpful AI assistant that speaks Twi/Akan fluently. 
        Your responses should be culturally appropriate and respectful.
        
        Guidelines:
        1. Respond primarily in Twi, but can code-switch to English when necessary
        2. Use proper Twi characters (ɛ, ɔ, Ɛ, Ɔ)
        3. Be aware of dialectical differences (Asante, Akuapem, Fante)
        4. Include cultural context and proverbs when appropriate
        5. For numbers, use Twi counting system:
           - 1 = baako, 2 = mmienu, 3 = mmiɛnsa, 4 = nnan, 5 = nnum
           - 10 = du, 20 = aduonu, 100 = ɔha, 1000 = apem
        6. For dates and time, use Twi expressions:
           - Days: Dwoda, Benada, Wukuda, Yawda, Fida, Memeneda, Kwesida
           - Months: Ɔpɛpɔn, Ɔgyefuo, Ɔbenem, etc.
        7. Be warm and personable, as is common in Ghanaian culture
        
        Remember to:
        - Address elders with respect
        - Use appropriate greetings based on time of day
        - Include "please" (mepa wo kyɛw) and "thank you" (meda wo ase)
        """
        
    def _get_healthcare_prompt(self) -> str:
        """Get healthcare-specific system prompt"""
        return self._get_general_prompt() + """
        
        Healthcare Context:
        You are assisting with healthcare information in Twi. 
        
        Additional Guidelines:
        1. Always remind users to consult healthcare professionals
        2. Use simple, clear language for medical concepts
        3. Be sensitive to traditional medicine beliefs
        4. Explain symptoms in culturally understood terms
        5. For emergencies, provide clear action steps
        6. Common health terms in Twi:
           - Yareɛ = sickness
           - Aduro = medicine
           - Ɔyaresafoɔ = doctor
           - Ayaresabea = hospital
           - Mogya = blood
           - Ti = head
           - Yafunu = stomach
        
        IMPORTANT: Never diagnose conditions. Always recommend professional medical consultation.
        """
        
    def _get_education_prompt(self) -> str:
        """Get education-specific system prompt"""
        return self._get_general_prompt() + """
        
        Education Context:
        You are an educational tutor helping students learn in Twi.
        
        Additional Guidelines:
        1. Use age-appropriate language
        2. Encourage and motivate students
        3. Break down complex concepts simply
        4. Use examples from Ghanaian context
        5. Educational terms in Twi:
           - Sukuu = school
           - Ɔkyerɛkyerɛni = teacher
           - Adesua = learning
           - Nhoma = book
           - Kyerɛw = write
           - Kenkan = read
           - Akontaabu = mathematics
        6. Use storytelling (anansesɛm) when appropriate
        7. Include cultural education alongside academic content
        """
        
    def _get_finance_prompt(self) -> str:
        """Get finance-specific system prompt"""
        return self._get_general_prompt() + """
        
        Financial Context:
        You are helping with financial literacy and services in Twi.
        
        Additional Guidelines:
        1. Explain financial concepts simply
        2. Use familiar examples (mobile money, susu, etc.)
        3. Be aware of local financial systems
        4. Financial terms in Twi:
           - Sika = money
           - Sikakorabea = bank
           - Bosea = loan
           - Sikakorabea nkrataa = bank account
           - Mobile money = mobile money (commonly used as is)
        5. Currency: Ghana Cedi (GH₵)
        6. Help with:
           - Mobile money transactions
           - Savings advice (susu methods)
           - Basic budgeting
           - Understanding loans and interest
        
        Never provide specific investment advice or guarantee returns.
        """
        
    async def generate_response(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]] = None,
        domain: str = "general",
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        Generate LLM response
        
        Args:
            message: User message
            context: Conversation history
            domain: Domain context (general, healthcare, education, finance)
            stream: Whether to stream response
            
        Returns:
            LLM response
        """
        system_prompt = self.system_prompts.get(domain, self.system_prompts["general"])
        
        if self.provider == LLMProvider.OPENAI:
            return await self._openai_generate(message, context, system_prompt, stream, **kwargs)
        elif self.provider == LLMProvider.ANTHROPIC:
            return await self._anthropic_generate(message, context, system_prompt, stream, **kwargs)
        elif self.provider == LLMProvider.GOOGLE:
            return await self._gemini_generate(message, context, system_prompt, stream, **kwargs)
        elif self.provider == LLMProvider.GROQ:
            return await self._groq_generate(message, context, system_prompt, stream, **kwargs)
        else:
            # Fallback to mock response for testing
            return await self._mock_generate(message, context, domain)
            
    async def _openai_generate(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]],
        system_prompt: str,
        stream: bool,
        **kwargs
    ) -> str:
        """Generate response using OpenAI API"""
        if not self.api_key:
            return "Mepa wo kyɛw, OpenAI API key nni hɔ. (Sorry, OpenAI API key not found.)"
            
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if context:
                messages.extend(context)
                
            messages.append({"role": "user", "content": message})
            
            response = await client.chat.completions.create(
                model=kwargs.get("model", "gpt-3.5-turbo"),
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 500),
                stream=stream
            )
            
            if stream:
                # Handle streaming response
                full_response = ""
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                return full_response
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return f"Mepa wo kyɛw, mfomsoɔ bi aba. (Sorry, an error occurred: {str(e)})"
            
    async def _anthropic_generate(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]],
        system_prompt: str,
        stream: bool,
        **kwargs
    ) -> str:
        """Generate response using Anthropic Claude API"""
        if not self.api_key:
            return "Mepa wo kyɛw, Anthropic API key nni hɔ. (Sorry, Anthropic API key not found.)"
            
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            # Build messages for Claude
            messages = []
            
            if context:
                for msg in context:
                    messages.append({
                        "role": msg["role"] if msg["role"] in ["user", "assistant"] else "user",
                        "content": msg["content"]
                    })
                    
            messages.append({"role": "user", "content": message})
            
            response = await client.messages.create(
                model=kwargs.get("model", "claude-3-sonnet-20240229"),
                system=system_prompt,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 500),
                temperature=kwargs.get("temperature", 0.7),
                stream=stream
            )
            
            if stream:
                # Handle streaming response
                full_response = ""
                async for chunk in response:
                    if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                        full_response += chunk.delta.text
                return full_response
            else:
                return response.content[0].text if response.content else ""
                
        except ImportError:
            logger.warning("Anthropic library not installed. Install with: pip install anthropic")
            return "Mepa wo kyɛw, Anthropic library nni hɔ. (Anthropic library not installed.)"
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            return f"Mepa wo kyɛw, mfomsoɔ bi aba. (Sorry, an error occurred: {str(e)})"
            
    async def _gemini_generate(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]],
        system_prompt: str,
        stream: bool,
        **kwargs
    ) -> str:
        """Generate response using Google Gemini API"""
        if not self.api_key:
            return "Mepa wo kyɛw, Gemini API key nni hɔ. (Sorry, Gemini API key not found.)"
            
        try:
            import google.generativeai as genai
            
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            
            # Initialize model - use gemini-2.5-flash for fast responses
            model = genai.GenerativeModel(
                model_name=kwargs.get("model", "gemini-2.5-flash"),
                generation_config={
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_output_tokens": kwargs.get("max_tokens", 500),
                    "top_p": 0.95,
                    "top_k": 40,
                }
            )
            
            # Build conversation history
            chat_history = []
            
            # Add system prompt as first user message
            chat_history.append({
                "role": "user",
                "parts": [system_prompt + "\n\nPlease respond following these guidelines."]
            })
            chat_history.append({
                "role": "model",
                "parts": ["Aane, mete aseɛ. Me yɛ Twi AI assistant. (Yes, I understand. I am a Twi AI assistant.)"]
            })
            
            # Add context if available
            if context:
                for msg in context:
                    role = "user" if msg["role"] == "user" else "model"
                    chat_history.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })
            
            # Start chat session
            chat = model.start_chat(history=chat_history)
            
            # Send message and get response
            response = chat.send_message(message)
            
            return response.text
            
        except ImportError:
            logger.warning("Google Generative AI library not installed. Install with: pip install google-generativeai")
            return "Mepa wo kyɛw, Google Generative AI library nni hɔ. (Google Generative AI library not installed.)"
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return f"Mepa wo kyɛw, mfomsoɔ bi aba. (Sorry, an error occurred: {str(e)})"
            
    async def _groq_generate(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]],
        system_prompt: str,
        stream: bool,
        **kwargs
    ) -> str:
        """Generate response using Groq API (fast inference)"""
        if not self.api_key:
            return "Mepa wo kyɛw, Groq API key nni hɔ. (Sorry, Groq API key not found.)"
            
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if context:
                messages.extend(context)
                
            messages.append({"role": "user", "content": message})
            
            data = {
                "model": kwargs.get("model", "mixtral-8x7b-32768"),
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 500),
                "stream": stream
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error = await response.text()
                        logger.error(f"Groq API error: {error}")
                        return f"Mepa wo kyɛw, mfomsoɔ bi aba. (Error: {response.status})"
                        
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            return f"Mepa wo kyɛw, mfomsoɔ bi aba. (Sorry, an error occurred: {str(e)})"
            
    async def _mock_generate(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]],
        domain: str
    ) -> str:
        """Generate mock response for testing"""
        # Simple pattern matching for mock responses
        message_lower = message.lower()
        
        # Greetings
        if any(greeting in message_lower for greeting in ["maakye", "maaha", "maadwo", "hello", "hi"]):
            responses = [
                "Maakye! Ɛte sɛn? Me yɛ AI assistant a metumi aboa wo wɔ Twi kasa mu.",
                "Akwaaba! Mete sɛ wobɛhwehwɛ mmoa. Dɛn na metumi ayɛ ama wo nnɛ?",
                "Yɛnkɔ so! Wobɛpɛ sɛ yɛbɛkasa fa dɛn ho?"
            ]
            import random
            return random.choice(responses)
            
        # Health-related
        if domain == "healthcare" or any(word in message_lower for word in ["yareɛ", "sick", "aduro", "medicine"]):
            return """Mete wo nka ase. Yareɛ ho asɛm yɛ ade a ɛho hia pa ara. 
            
Sɛ wote nka sɛ wo ho nyɛ wo a, ɛsɛ sɛ wokɔ ayaresabea na woahwɛ ɔyaresafoɔ.

Nanso sɛ wobɛpɛ sɛ wobɛka wo ho asɛm kyerɛ me a, metumi aboa wo sɛdeɛ wobɛka akyerɛ ɔyaresafoɔ no.

Dɛn na wote nka wɔ wo ho?"""
            
        # Education-related
        if domain == "education" or any(word in message_lower for word in ["sukuu", "adesua", "kyerɛ", "school"]):
            return """Adesua ho asɛm! Ɛyɛ ade pa ara sɛ worepɛ sɛ wosua ade.

Metumi aboa wo wɔ:
- Twi kasa adesua
- Akontaabu (Mathematics)
- Abɔdeɛ mu nyansapɛ (Science)
- Anansesɛm ne mmɛbusɛm

Adeɛ bɛn na wobɛpɛ sɛ yɛsua nnɛ?"""
            
        # Finance-related
        if domain == "finance" or any(word in message_lower for word in ["sika", "money", "bank", "mobile money"]):
            return """Sika ho asɛm yɛ ade a ɛho hia. Metumi aboa wo wɔ:

- Mobile money dwumadie
- Sikakorabea (bank) ho nsɛm
- Sika a wobɛkora (savings)
- Bosea (loan) ho nkyerɛkyerɛ

Nsɛm yi mu deɛ ɛwɔ he na wobɛpɛ sɛ yɛbɛkasa fa ho?"""
            
        # Default response
        return """Meda wo ase wɔ asɛm yi ho. Metumi aboa wo wɔ:

1. Twi kasa ne ɔkasa (language help)
2. Apɔmuden ho nsɛm (health information)
3. Adesua ne nkyerɛkyerɛ (education)
4. Sika ho nyansahyɛ (financial guidance)

Fa yi mu biako na yɛnkɔ so."""
        
    async def stream_response(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]] = None,
        domain: str = "general",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM response
        
        Args:
            message: User message
            context: Conversation history
            domain: Domain context
            
        Yields:
            Response chunks
        """
        # For now, return mock streaming
        response = await self.generate_response(message, context, domain, stream=False, **kwargs)
        
        # Simulate streaming by yielding words
        words = response.split()
        for i, word in enumerate(words):
            if i > 0:
                yield " "
            yield word
            await asyncio.sleep(0.05)  # Simulate typing delay
            
    def detect_language(self, text: str) -> str:
        """
        Detect if text is Twi, English, or mixed
        
        Args:
            text: Input text
            
        Returns:
            Language code (tw, en, mixed)
        """
        twi_chars = set("ɛɔƐƆ")
        twi_words = set(["ne", "na", "no", "deɛ", "sɛ", "wɔ", "yɛ", "me", "wo", "ɔ"])
        
        text_lower = text.lower()
        words = text_lower.split()
        
        # Check for Twi characters
        has_twi_chars = any(char in text for char in twi_chars)
        
        # Check for Twi words
        twi_word_count = sum(1 for word in words if word in twi_words)
        twi_ratio = twi_word_count / len(words) if words else 0
        
        if has_twi_chars or twi_ratio > 0.3:
            return "tw"
        elif twi_ratio > 0.1:
            return "mixed"
        else:
            return "en"
            
    def translate_numbers_to_twi(self, number: int) -> str:
        """
        Translate number to Twi
        
        Args:
            number: Number to translate
            
        Returns:
            Twi representation
        """
        # Basic Twi numbers
        ones = ["", "baako", "mmienu", "mmiɛnsa", "nnan", "nnum", 
                "nsia", "nson", "nwɔtwe", "nkron"]
        tens = ["", "du", "aduonu", "aduasa", "aduanan", "aduonum",
                "aduosia", "aduoson", "aduɔwɔtwe", "aduokron"]
        
        if number == 0:
            return "ohunu"
        elif number < 10:
            return ones[number]
        elif number < 100:
            ten = number // 10
            one = number % 10
            if one == 0:
                return tens[ten]
            else:
                return f"{tens[ten]} {ones[one]}"
        elif number == 100:
            return "ɔha"
        elif number < 1000:
            hundred = number // 100
            remainder = number % 100
            if remainder == 0:
                return f"aha {ones[hundred]}" if hundred > 1 else "ɔha"
            else:
                hundred_str = f"aha {ones[hundred]}" if hundred > 1 else "ɔha"
                return f"{hundred_str} {self.translate_numbers_to_twi(remainder)}"
        elif number == 1000:
            return "apem"
        else:
            thousand = number // 1000
            remainder = number % 1000
            if remainder == 0:
                return f"mpem {ones[thousand]}" if thousand > 1 else "apem"
            else:
                thousand_str = f"mpem {ones[thousand]}" if thousand > 1 else "apem"
                return f"{thousand_str} {self.translate_numbers_to_twi(remainder)}"


# Singleton service instance
_llm_service = None


def get_llm_service(provider: LLMProvider = LLMProvider.OPENAI) -> TwiLLMService:
    """Get or create LLM service instance"""
    global _llm_service
    
    if _llm_service is None:
        _llm_service = TwiLLMService(provider)
        
    return _llm_service