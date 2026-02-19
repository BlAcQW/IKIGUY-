"""
Web Chat Integration System

This module provides web chat widget integration capabilities for the KasaAI platform.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
import uuid


class WebChatProvider(Enum):
    """Supported web chat providers"""
    CUSTOM = "custom"
    TIDIO = "tidio"
    CRISPY_CHAT = "crispy_chat"
    TALKJS = "talkjs"
    INTERCOM = "intercom"


@dataclass
class WebChatMessage:
    """Web chat message definition"""
    message_id: str
    user_id: str
    content: str
    message_type: str = "text"  # text, image, file, location
    timestamp: datetime = None
    metadata: Dict[str, Any] = None


@dataclass
class WebChatUser:
    """Web chat user definition"""
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class WebChatSession:
    """Web chat session definition"""
    session_id: str
    user_id: str
    agent_id: Optional[str] = None
    status: str = "active"  # active, waiting, closed
    created_at: datetime = None
    last_activity: datetime = None
    metadata: Dict[str, Any] = None


@dataclass
class WebChatWidget:
    """Web chat widget configuration"""
    widget_id: str
    name: str
    position: str = "bottom-right"  # bottom-right, bottom-left, top-right, top-left
    theme: str = "light"  # light, dark, custom
    primary_color: str = "#007bff"
    welcome_message: str = "Hello! How can we help you today?"
    auto_open: bool = False
    show_avatar: bool = True
    show_timestamp: bool = True
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None


class BaseWebChatProvider(ABC):
    """Base class for web chat providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the web chat provider"""
        self.config = config
        self.logger = logging.getLogger(f"WebChatProvider.{self.__class__.__name__}")
        self.provider_type = self.get_provider_type()
    
    @abstractmethod
    def get_provider_type(self) -> WebChatProvider:
        """Get the provider type"""
        pass
    
    @abstractmethod
    async def create_widget(self, widget_config: WebChatWidget) -> Dict[str, Any]:
        """Create a web chat widget"""
        pass
    
    @abstractmethod
    async def send_message(self, session_id: str, message: WebChatMessage) -> Dict[str, Any]:
        """Send a message in a chat session"""
        pass
    
    @abstractmethod
    async def get_session_messages(self, session_id: str, limit: int = 50) -> List[WebChatMessage]:
        """Get messages from a chat session"""
        pass
    
    @abstractmethod
    async def create_session(self, user: WebChatUser) -> WebChatSession:
        """Create a new chat session"""
        pass
    
    @abstractmethod
    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close a chat session"""
        pass
    
    @abstractmethod
    async def assign_agent(self, session_id: str, agent_id: str) -> Dict[str, Any]:
        """Assign an agent to a chat session"""
        pass


class CustomWebChatProvider(BaseWebChatProvider):
    """Custom web chat provider for self-hosted solutions"""
    
    def get_provider_type(self) -> WebChatProvider:
        return WebChatProvider.CUSTOM
    
    async def create_widget(self, widget_config: WebChatWidget) -> Dict[str, Any]:
        """Create a custom web chat widget"""
        try:
            # Generate widget HTML and JavaScript
            widget_html = self._generate_widget_html(widget_config)
            widget_js = self._generate_widget_js(widget_config)
            
            return {
                "success": True,
                "widget_id": widget_config.widget_id,
                "html": widget_html,
                "javascript": widget_js,
                "provider": "custom"
            }
        except Exception as e:
            self.logger.error(f"Failed to create custom web chat widget: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "custom"
            }
    
    def _generate_widget_html(self, widget_config: WebChatWidget) -> str:
        """Generate HTML for the web chat widget"""
        position_class = f"webchat-{widget_config.position.replace('-', '-')}"
        
        html = f"""
        <div id="webchat-widget-{widget_config.widget_id}" class="webchat-widget {position_class}">
            <div class="webchat-header">
                <div class="webchat-title">Customer Support</div>
                <button class="webchat-close" onclick="toggleWebChat('{widget_config.widget_id}')">×</button>
            </div>
            <div class="webchat-messages" id="webchat-messages-{widget_config.widget_id}">
                <div class="webchat-welcome">
                    {widget_config.welcome_message}
                </div>
            </div>
            <div class="webchat-input">
                <input type="text" id="webchat-input-{widget_config.widget_id}" 
                       placeholder="Type your message..." 
                       onkeypress="handleWebChatKeyPress(event, '{widget_config.widget_id}')">
                <button onclick="sendWebChatMessage('{widget_config.widget_id}')">Send</button>
            </div>
        </div>
        """
        return html
    
    def _generate_widget_js(self, widget_config: WebChatWidget) -> str:
        """Generate JavaScript for the web chat widget"""
        js = f"""
        // Web Chat Widget JavaScript for {widget_config.widget_id}
        let webchatSession_{widget_config.widget_id} = null;
        
        function initWebChat(widgetId) {{
            // Initialize web chat widget
            const widget = document.getElementById(`webchat-widget-${{widgetId}}`);
            if (widget) {{
                widget.style.display = 'none';
                // Add click handler for toggle
                document.addEventListener('click', function(e) {{
                    if (e.target.classList.contains('webchat-toggle')) {{
                        toggleWebChat(widgetId);
                    }}
                }});
            }}
        }}
        
        function toggleWebChat(widgetId) {{
            const widget = document.getElementById(`webchat-widget-${{widgetId}}`);
            if (widget) {{
                if (widget.style.display === 'none') {{
                    widget.style.display = 'block';
                    if (!webchatSession_{widget_config.widget_id}) {{
                        createWebChatSession(widgetId);
                    }}
                }} else {{
                    widget.style.display = 'none';
                }}
            }}
        }}
        
        async function createWebChatSession(widgetId) {{
            try {{
                const response = await fetch('/api/webchat/session', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        widget_id: widgetId,
                        user: {{
                            name: 'Guest User',
                            email: null
                        }}
                    }})
                }});
                
                const data = await response.json();
                if (data.success) {{
                    webchatSession_{widget_config.widget_id} = data.session_id;
                }}
            }} catch (error) {{
                console.error('Failed to create web chat session:', error);
            }}
        }}
        
        async function sendWebChatMessage(widgetId) {{
            const input = document.getElementById(`webchat-input-${{widgetId}}`);
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add message to UI
            addWebChatMessage(widgetId, message, 'user');
            input.value = '';
            
            // Send to server
            try {{
                const response = await fetch('/api/webchat/message', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        session_id: webchatSession_{widget_config.widget_id},
                        message: message,
                        widget_id: widgetId
                    }})
                }});
                
                const data = await response.json();
                if (data.success && data.response) {{
                    addWebChatMessage(widgetId, data.response, 'agent');
                }}
            }} catch (error) {{
                console.error('Failed to send web chat message:', error);
                addWebChatMessage(widgetId, 'Sorry, there was an error sending your message.', 'system');
            }}
        }}
        
        function addWebChatMessage(widgetId, message, sender) {{
            const messagesContainer = document.getElementById(`webchat-messages-${{widgetId}}`);
            const messageDiv = document.createElement('div');
            messageDiv.className = `webchat-message webchat-${{sender}}`;
            messageDiv.innerHTML = `
                <div class="webchat-message-content">${{message}}</div>
                <div class="webchat-message-time">${{new Date().toLocaleTimeString()}}</div>
            `;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }}
        
        function handleWebChatKeyPress(event, widgetId) {{
            if (event.key === 'Enter') {{
                sendWebChatMessage(widgetId);
            }}
        }}
        
        // Initialize widget when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            initWebChat('{widget_config.widget_id}');
        }});
        """
        return js
    
    async def send_message(self, session_id: str, message: WebChatMessage) -> Dict[str, Any]:
        """Send a message in a chat session"""
        try:
            # In a real implementation, this would store the message in a database
            # and potentially trigger AI processing or agent notification
            
            return {
                "success": True,
                "message_id": message.message_id,
                "session_id": session_id,
                "provider": "custom"
            }
        except Exception as e:
            self.logger.error(f"Failed to send web chat message: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "custom"
            }
    
    async def get_session_messages(self, session_id: str, limit: int = 50) -> List[WebChatMessage]:
        """Get messages from a chat session"""
        try:
            # In a real implementation, this would retrieve messages from a database
            # For now, return empty list
            return []
        except Exception as e:
            self.logger.error(f"Failed to get session messages: {e}")
            return []
    
    async def create_session(self, user: WebChatUser) -> WebChatSession:
        """Create a new chat session"""
        try:
            session_id = str(uuid.uuid4())
            session = WebChatSession(
                session_id=session_id,
                user_id=user.user_id,
                created_at=datetime.now(),
                last_activity=datetime.now()
            )
            
            return session
        except Exception as e:
            self.logger.error(f"Failed to create web chat session: {e}")
            raise
    
    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close a chat session"""
        try:
            # In a real implementation, this would update the session status in a database
            return {
                "success": True,
                "session_id": session_id,
                "provider": "custom"
            }
        except Exception as e:
            self.logger.error(f"Failed to close web chat session: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "custom"
            }
    
    async def assign_agent(self, session_id: str, agent_id: str) -> Dict[str, Any]:
        """Assign an agent to a chat session"""
        try:
            # In a real implementation, this would update the session with agent assignment
            return {
                "success": True,
                "session_id": session_id,
                "agent_id": agent_id,
                "provider": "custom"
            }
        except Exception as e:
            self.logger.error(f"Failed to assign agent to web chat session: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "custom"
            }


class TidioWebChatProvider(BaseWebChatProvider):
    """Tidio web chat provider"""
    
    def get_provider_type(self) -> WebChatProvider:
        return WebChatProvider.TIDIO
    
    async def create_widget(self, widget_config: WebChatWidget) -> Dict[str, Any]:
        """Create a Tidio web chat widget"""
        try:
            # Get Tidio configuration
            public_key = self.config.get("public_key")
            
            if not public_key:
                return {
                    "success": False,
                    "error": "Tidio public key is required",
                    "provider": "tidio"
                }
            
            # Generate Tidio widget code
            widget_code = f"""
            <!-- Tidio Web Chat Widget -->
            <script src="//code.tidio.co/{public_key}.js" async></script>
            <script>
                window.tidioSettings = {{
                    position: '{widget_config.position}',
                    theme: '{widget_config.theme}',
                    primaryColor: '{widget_config.primary_color}',
                    welcomeMessage: '{widget_config.welcome_message}',
                    autoOpen: {str(widget_config.auto_open).lower()}
                }};
            </script>
            """
            
            return {
                "success": True,
                "widget_id": widget_config.widget_id,
                "widget_code": widget_code,
                "provider": "tidio"
            }
        except Exception as e:
            self.logger.error(f"Failed to create Tidio web chat widget: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "tidio"
            }
    
    async def send_message(self, session_id: str, message: WebChatMessage) -> Dict[str, Any]:
        """Send a message via Tidio API"""
        try:
            # Get Tidio configuration
            api_key = self.config.get("api_key")
            base_url = "https://api.tidio.co"
            
            if not api_key:
                return {
                    "success": False,
                    "error": "Tidio API key is required",
                    "provider": "tidio"
                }
            
            # In a real implementation, this would make API calls to Tidio
            # For now, return a placeholder response
            return {
                "success": True,
                "message_id": message.message_id,
                "session_id": session_id,
                "provider": "tidio"
            }
        except Exception as e:
            self.logger.error(f"Failed to send Tidio message: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "tidio"
            }
    
    async def get_session_messages(self, session_id: str, limit: int = 50) -> List[WebChatMessage]:
        """Get messages from Tidio session"""
        try:
            # In a real implementation, this would retrieve messages from Tidio API
            return []
        except Exception as e:
            self.logger.error(f"Failed to get Tidio session messages: {e}")
            return []
    
    async def create_session(self, user: WebChatUser) -> WebChatSession:
        """Create a new Tidio chat session"""
        try:
            session_id = str(uuid.uuid4())
            session = WebChatSession(
                session_id=session_id,
                user_id=user.user_id,
                created_at=datetime.now(),
                last_activity=datetime.now()
            )
            
            return session
        except Exception as e:
            self.logger.error(f"Failed to create Tidio session: {e}")
            raise
    
    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close a Tidio chat session"""
        try:
            return {
                "success": True,
                "session_id": session_id,
                "provider": "tidio"
            }
        except Exception as e:
            self.logger.error(f"Failed to close Tidio session: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "tidio"
            }
    
    async def assign_agent(self, session_id: str, agent_id: str) -> Dict[str, Any]:
        """Assign an agent to a Tidio chat session"""
        try:
            return {
                "success": True,
                "session_id": session_id,
                "agent_id": agent_id,
                "provider": "tidio"
            }
        except Exception as e:
            self.logger.error(f"Failed to assign agent to Tidio session: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "tidio"
            }


class WebChatIntegration:
    """Main web chat integration class"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize web chat integration"""
        self.config = config
        self.logger = logging.getLogger("WebChatIntegration")
        self.providers: Dict[WebChatProvider, BaseWebChatProvider] = {}
        self.default_provider = WebChatProvider.CUSTOM
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize web chat providers based on configuration"""
        provider_configs = self.config.get("providers", {})
        
        # Initialize Custom provider
        if "custom" in provider_configs:
            self.providers[WebChatProvider.CUSTOM] = CustomWebChatProvider(provider_configs["custom"])
        
        # Initialize Tidio provider
        if "tidio" in provider_configs:
            self.providers[WebChatProvider.TIDIO] = TidioWebChatProvider(provider_configs["tidio"])
        
        # Set default provider
        default_provider_name = self.config.get("default_provider", "custom")
        if default_provider_name == "tidio" and WebChatProvider.TIDIO in self.providers:
            self.default_provider = WebChatProvider.TIDIO
    
    async def create_widget(self, widget_config: WebChatWidget, 
                          provider: Optional[WebChatProvider] = None) -> Dict[str, Any]:
        """Create a web chat widget"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].create_widget(widget_config)
    
    async def send_message(self, session_id: str, message: WebChatMessage,
                          provider: Optional[WebChatProvider] = None) -> Dict[str, Any]:
        """Send a message in a chat session"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].send_message(session_id, message)
    
    async def get_session_messages(self, session_id: str, limit: int = 50,
                                 provider: Optional[WebChatProvider] = None) -> List[WebChatMessage]:
        """Get messages from a chat session"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return []
        
        return await self.providers[provider].get_session_messages(session_id, limit)
    
    async def create_session(self, user: WebChatUser,
                           provider: Optional[WebChatProvider] = None) -> WebChatSession:
        """Create a new chat session"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            raise ValueError(f"Provider {provider.value} not configured")
        
        return await self.providers[provider].create_session(user)
    
    async def close_session(self, session_id: str,
                          provider: Optional[WebChatProvider] = None) -> Dict[str, Any]:
        """Close a chat session"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].close_session(session_id)
    
    async def assign_agent(self, session_id: str, agent_id: str,
                          provider: Optional[WebChatProvider] = None) -> Dict[str, Any]:
        """Assign an agent to a chat session"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].assign_agent(session_id, agent_id)
    
    def get_available_providers(self) -> List[WebChatProvider]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_provider_info(self, provider: WebChatProvider) -> Dict[str, Any]:
        """Get information about a provider"""
        if provider not in self.providers:
            return {"available": False}
        
        return {
            "available": True,
            "type": provider.value,
            "config": self.providers[provider].config
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        health_status = {
            "overall": "healthy",
            "providers": {}
        }
        
        for provider_type, provider in self.providers.items():
            try:
                # Simple health check - try to create a test widget
                test_widget = WebChatWidget(
                    widget_id="health-check",
                    name="Health Check Widget"
                )
                
                result = await provider.create_widget(test_widget)
                health_status["providers"][provider_type.value] = {
                    "status": "healthy" if result.get("success") else "unhealthy",
                    "error": result.get("error")
                }
                
                if not result.get("success"):
                    health_status["overall"] = "unhealthy"
                    
            except Exception as e:
                health_status["providers"][provider_type.value] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall"] = "unhealthy"
        
        return health_status

