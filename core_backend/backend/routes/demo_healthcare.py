"""
Healthcare Demo Deployment Service
Combines Universal Wizard demo capabilities with Premier Health domain expertise
"""

import os
import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from datetime import datetime
import logging

from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo-healthcare"])

class HealthcareDemoRequest(BaseModel):
    """Request model for healthcare demo deployment."""
    organizationName: str
    region: str
    html: str
    vapiAssistantId: str
    features: List[str]
    emergencySimulation: bool = True
    providerStats: Dict[str, Any] = {}

class HealthcareDemoResponse(BaseModel):
    """Response model for healthcare demo deployment."""
    url: str
    demoId: str
    organizationName: str
    features: List[str]
    analyticsEnabled: bool
    emergencyFeaturesEnabled: bool

@router.post("/deploy-healthcare-demo", response_model=HealthcareDemoResponse)
async def deploy_healthcare_demo(
    demo_request: HealthcareDemoRequest,
    request: Request,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Deploy an interactive healthcare provider demo with domain-specific features.

    This combines the Universal Wizard's flexible demo deployment with
    Premier Health's specialized healthcare functionality.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Deploying healthcare demo for: {demo_request.organizationName}, organization={org_id}")

        # Generate unique demo ID
        demo_id = f"healthcare_{uuid.uuid4().hex[:8]}"

        # Enhanced HTML with healthcare-specific features
        enhanced_html = enhance_healthcare_demo_html(
            base_html=demo_request.html,
            organization_name=demo_request.organizationName,
            region=demo_request.region,
            vapi_assistant_id=demo_request.vapiAssistantId,
            features=demo_request.features,
            emergency_simulation=demo_request.emergencySimulation,
            provider_stats=demo_request.providerStats,
            demo_id=demo_id
        )

        # Deploy to static hosting (simulate deployment)
        demo_url = f"https://demos.ailabsafrica.com/healthcare/{demo_id}"

        # Create demo files structure
        demo_files = {
            'index.html': enhanced_html,
            'healthcare-demo.js': generate_healthcare_demo_js(demo_request.vapiAssistantId, demo_id),
            'healthcare-styles.css': generate_healthcare_demo_css(),
            'analytics.js': generate_healthcare_analytics_js(demo_id)
        }

        # Simulate file deployment
        await deploy_demo_files(demo_id, demo_files)

        # Setup demo analytics tracking
        await setup_demo_analytics(demo_id, demo_request.organizationName, demo_request.features)

        response = HealthcareDemoResponse(
            url=demo_url,
            demoId=demo_id,
            organizationName=demo_request.organizationName,
            features=demo_request.features,
            analyticsEnabled=True,
            emergencyFeaturesEnabled=demo_request.emergencySimulation
        )

        logger.info(f"Healthcare demo deployed successfully: {demo_url}, organization={org_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying healthcare demo for organization={org_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deploy healthcare demo: {str(e)}"
        )

def enhance_healthcare_demo_html(
    base_html: str,
    organization_name: str,
    region: str,
    vapi_assistant_id: str,
    features: List[str],
    emergency_simulation: bool,
    provider_stats: Dict[str, Any],
    demo_id: str
) -> str:
    """
    Enhance the base demo HTML with healthcare-specific interactive features.
    """

    # Extract provider statistics
    total_providers = provider_stats.get('activeProviders', 103)
    specialties_count = len(provider_stats.get('specialties', [])) or 15
    locations_count = len(provider_stats.get('locations', [])) or 25

    enhanced_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{organization_name} - Healthcare Provider Locator Demo</title>
    <link rel="stylesheet" href="./healthcare-styles.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <meta name="description" content="Interactive demo of {organization_name}'s AI-powered healthcare provider locator serving {region}">
</head>
<body>
    <div class="demo-container">
        <!-- Header Section -->
        <header class="demo-header">
            <div class="header-content">
                <div class="brand-section">
                    <div class="logo-area">
                        <div class="logo-icon">🏥</div>
                        <div class="brand-text">
                            <h1>{organization_name}</h1>
                            <p class="tagline">AI-Powered Healthcare Provider Locator</p>
                        </div>
                    </div>
                    <div class="region-info">
                        <span class="region-badge">📍 {region}</span>
                        <span class="demo-badge">Interactive Demo</span>
                    </div>
                </div>

                <div class="live-stats">
                    <div class="stat-item">
                        <div class="stat-number">{total_providers}</div>
                        <div class="stat-label">Active Providers</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{specialties_count}</div>
                        <div class="stat-label">Specialties</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{locations_count}</div>
                        <div class="stat-label">Locations</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">24/7</div>
                        <div class="stat-label">Emergency</div>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Demo Section -->
        <main class="demo-main">
            <div class="demo-intro">
                <h2>Experience AI-Powered Healthcare Provider Search</h2>
                <p>Try our voice assistant to find doctors, hospitals, clinics, and pharmacies in {region}.
                   Our AI can help you book appointments, verify insurance, and get emergency assistance.</p>
            </div>

            <!-- Voice Interaction Panel -->
            <div class="voice-interaction-panel">
                <div class="voice-controls">
                    <button id="start-call" class="primary-call-button">
                        <span class="button-icon">🎤</span>
                        <span class="button-text">Start Voice Search</span>
                        <span class="button-subtitle">Find healthcare providers</span>
                    </button>

                    {f'''
                    <button id="emergency-call" class="emergency-call-button">
                        <span class="button-icon">🚨</span>
                        <span class="button-text">Emergency Services</span>
                        <span class="button-subtitle">Urgent medical help</span>
                    </button>
                    ''' if emergency_simulation else ''}
                </div>

                <div id="call-status" class="call-status hidden">
                    <div class="status-indicator pulsing"></div>
                    <div class="status-text">
                        <span class="status-title">Connected to AI Healthcare Assistant</span>
                        <span class="status-subtitle">Listening for your healthcare needs...</span>
                    </div>
                    <button id="end-call" class="end-call-button">End Call</button>
                </div>

                <div class="voice-suggestions">
                    <h4>Try saying:</h4>
                    <div class="suggestion-chips">
                        <button class="suggestion-chip" onclick="simulateQuery('Find me an eye doctor in Accra')">
                            "Find me an eye doctor in Accra"
                        </button>
                        <button class="suggestion-chip" onclick="simulateQuery('I need a pediatrician in Madina')">
                            "I need a pediatrician in Madina"
                        </button>
                        <button class="suggestion-chip" onclick="simulateQuery('Show me hospitals near Circle')">
                            "Show me hospitals near Circle"
                        </button>
                        <button class="suggestion-chip" onclick="simulateQuery('Find a pharmacy in East Legon')">
                            "Find a pharmacy in East Legon"
                        </button>
                    </div>
                </div>
            </div>

            <!-- Demo Features Grid -->
            <div class="features-grid">
                {''.join([f'''
                <div class="feature-card" data-feature="{feature}">
                    <div class="feature-header">
                        <div class="feature-icon">{get_feature_icon(feature)}</div>
                        <h3>{get_feature_title(feature)}</h3>
                    </div>
                    <p>{get_feature_description(feature)}</p>
                    <button class="try-feature-btn" onclick="demoFeature('{feature}')">
                        Try Feature
                    </button>
                </div>
                ''' for feature in features])}
            </div>

            <!-- Live Demo Results -->
            <div id="demo-results" class="demo-results hidden">
                <div class="results-header">
                    <h3>Live Search Results</h3>
                    <button id="clear-results" class="clear-btn">Clear</button>
                </div>
                <div id="results-content" class="results-content">
                    <!-- Dynamic results will be populated here -->
                </div>
            </div>

            <!-- Integration Showcase -->
            <div class="integration-showcase">
                <h3>Powered By Advanced AI & Integrations</h3>
                <div class="integration-grid">
                    <div class="integration-item">
                        <div class="integration-icon">🤖</div>
                        <div class="integration-name">VAPI Voice AI</div>
                        <div class="integration-desc">Natural language processing</div>
                    </div>
                    <div class="integration-item">
                        <div class="integration-icon">🗄️</div>
                        <div class="integration-name">Provider Database</div>
                        <div class="integration-desc">Real-time provider data</div>
                    </div>
                    <div class="integration-item">
                        <div class="integration-icon">📅</div>
                        <div class="integration-name">Calendly Integration</div>
                        <div class="integration-desc">Appointment booking</div>
                    </div>
                    <div class="integration-item">
                        <div class="integration-icon">📧</div>
                        <div class="integration-name">Email & SMS</div>
                        <div class="integration-desc">Provider information delivery</div>
                    </div>
                    <div class="integration-item">
                        <div class="integration-icon">🛡️</div>
                        <div class="integration-name">HIPAA Compliance</div>
                        <div class="integration-desc">Secure data handling</div>
                    </div>
                    <div class="integration-item">
                        <div class="integration-icon">📊</div>
                        <div class="integration-name">Analytics Dashboard</div>
                        <div class="integration-desc">Performance monitoring</div>
                    </div>
                </div>
            </div>
        </main>

        <!-- Demo Analytics Panel (for admin view) -->
        <div id="admin-panel" class="admin-panel hidden">
            <div class="panel-header">
                <h4>Live Demo Analytics</h4>
                <button id="toggle-admin" class="toggle-btn">Hide</button>
            </div>
            <div class="analytics-grid">
                <div class="metric-card">
                    <h5>Demo Interactions</h5>
                    <div class="metric-value" id="interaction-count">0</div>
                    <div class="metric-change">+0 today</div>
                </div>
                <div class="metric-card">
                    <h5>Voice Calls</h5>
                    <div class="metric-value" id="call-count">0</div>
                    <div class="metric-change">+0 today</div>
                </div>
                <div class="metric-card">
                    <h5>Feature Usage</h5>
                    <div class="metric-value" id="feature-usage">0</div>
                    <div class="metric-change">+0 today</div>
                </div>
                <div class="metric-card">
                    <h5>Time on Demo</h5>
                    <div class="metric-value" id="time-spent">00:00</div>
                    <div class="metric-change">Current session</div>
                </div>
            </div>
        </div>

        <!-- Floating Admin Toggle -->
        <button id="admin-toggle" class="floating-admin-btn" onclick="toggleAdminPanel()">
            📊 Analytics
        </button>
    </div>

    <!-- Scripts -->
    <script src="https://vapi.ai/js/vapi.js"></script>
    <script src="./healthcare-demo.js"></script>
    <script src="./analytics.js"></script>
    <script>
        // Initialize healthcare demo
        const healthcareDemo = new HealthcareDemoApp({{
            vapiAssistantId: '{vapi_assistant_id}',
            organizationName: '{organization_name}',
            region: '{region}',
            demoId: '{demo_id}',
            features: {features},
            emergencySimulation: {str(emergency_simulation).lower()},
            providerStats: {provider_stats}
        }});

        healthcareDemo.initialize();
    </script>
</body>
</html>"""

    return enhanced_html

def get_feature_icon(feature: str) -> str:
    """Get icon for healthcare feature."""
    icons = {
        'provider_search': '🔍',
        'emergency_services': '🚨',
        'appointment_booking': '📅',
        'insurance_verification': '🛡️',
        'multilanguage_support': '🌐',
        'human_escalation': '👥'
    }
    return icons.get(feature, '🏥')

def get_feature_title(feature: str) -> str:
    """Get title for healthcare feature."""
    titles = {
        'provider_search': 'Provider Search',
        'emergency_services': 'Emergency Services',
        'appointment_booking': 'Appointment Booking',
        'insurance_verification': 'Insurance Verification',
        'multilanguage_support': 'Multilingual Support',
        'human_escalation': 'Human Escalation'
    }
    return titles.get(feature, feature.replace('_', ' ').title())

def get_feature_description(feature: str) -> str:
    """Get description for healthcare feature."""
    descriptions = {
        'provider_search': 'Find doctors, hospitals, clinics, and pharmacies by specialty, location, or insurance network.',
        'emergency_services': 'Get immediate access to emergency healthcare providers and urgent care facilities.',
        'appointment_booking': 'Schedule appointments directly with available healthcare providers through integrated booking systems.',
        'insurance_verification': 'Verify insurance coverage and find in-network providers for cost-effective care.',
        'multilanguage_support': 'Get assistance in multiple languages for diverse patient populations.',
        'human_escalation': 'Seamlessly connect with human healthcare specialists for complex medical queries.'
    }
    return descriptions.get(feature, f'Advanced {feature.replace("_", " ")} capabilities for enhanced healthcare service.')

def generate_healthcare_demo_js(vapi_assistant_id: str, demo_id: str) -> str:
    """Generate healthcare-specific demo JavaScript."""
    return f"""
class HealthcareDemoApp {{
    constructor(config) {{
        this.config = config;
        this.callActive = false;
        this.startTime = Date.now();
        this.interactions = 0;
        this.callCount = 0;
        this.featureUsage = 0;

        this.setupEventListeners();
        this.startTimeTracking();
    }}

    initialize() {{
        console.log('Healthcare Demo initialized for', this.config.organizationName);
        this.trackEvent('demo_loaded', {{
            organization: this.config.organizationName,
            region: this.config.region,
            features: this.config.features
        }});

        // Show welcome animation
        this.showWelcomeAnimation();
    }}

    setupEventListeners() {{
        // Voice call buttons
        const startCallBtn = document.getElementById('start-call');
        const emergencyCallBtn = document.getElementById('emergency-call');
        const endCallBtn = document.getElementById('end-call');

        if (startCallBtn) {{
            startCallBtn.addEventListener('click', () => this.startHealthcareCall('general'));
        }}

        if (emergencyCallBtn) {{
            emergencyCallBtn.addEventListener('click', () => this.startHealthcareCall('emergency'));
        }}

        if (endCallBtn) {{
            endCallBtn.addEventListener('click', () => this.endCall());
        }}

        // Suggestion chips
        document.querySelectorAll('.suggestion-chip').forEach(chip => {{
            chip.addEventListener('click', () => {{
                this.trackInteraction('suggestion_clicked');
                this.simulateVoiceQuery(chip.textContent.replace(/"/g, ''));
            }});
        }});

        // Feature cards
        document.querySelectorAll('.try-feature-btn').forEach(btn => {{
            btn.addEventListener('click', (e) => {{
                const feature = e.target.closest('.feature-card').dataset.feature;
                this.demoFeature(feature);
            }});
        }});
    }}

    startHealthcareCall(type = 'general') {{
        if (this.callActive) return;

        this.callActive = true;
        this.callCount++;
        this.trackInteraction('voice_call_started', {{ type }});

        // Show call status
        const callStatus = document.getElementById('call-status');
        const startBtn = document.getElementById('start-call');
        const emergencyBtn = document.getElementById('emergency-call');

        if (callStatus) callStatus.classList.remove('hidden');
        if (startBtn) startBtn.classList.add('hidden');
        if (emergencyBtn) emergencyBtn.classList.add('hidden');

        // Simulate VAPI integration
        this.simulateVAPICall(type);

        // Update analytics
        this.updateAnalytics();
    }}

    simulateVAPICall(type) {{
        const messages = {{
            general: [
                "Hello! I'm your healthcare provider assistant. How can I help you find medical care today?",
                "I can search for doctors, hospitals, clinics, or pharmacies in {self.config.region}. What type of provider are you looking for?"
            ],
            emergency: [
                "This is the emergency healthcare assistant. I understand this may be urgent. What type of emergency medical help do you need?",
                "I'm connecting you to emergency services and finding the nearest emergency facilities."
            ]
        }};

        const statusText = document.querySelector('.status-subtitle');
        const responseMessages = messages[type] || messages.general;

        responseMessages.forEach((message, index) => {{
            setTimeout(() => {{
                if (statusText) {{
                    statusText.textContent = message;
                }}

                // Show typing indicator
                this.showTypingIndicator();

                setTimeout(() => {{
                    this.hideTypingIndicator();
                    if (index === responseMessages.length - 1) {{
                        this.showDemoResults(type);
                    }}
                }}, 2000);
            }}, index * 4000);
        }});
    }}

    simulateVoiceQuery(query) {{
        if (!this.callActive) {{
            this.startHealthcareCall('general');
        }}

        this.trackInteraction('voice_query_simulated', {{ query }});

        // Simulate processing the query
        const statusText = document.querySelector('.status-subtitle');
        if (statusText) {{
            statusText.textContent = `Processing: "${{query}}"`;
        }}

        setTimeout(() => {{
            this.showSearchResults(query);
        }}, 3000);
    }}

    showSearchResults(query) {{
        const resultsDiv = document.getElementById('demo-results');
        const resultsContent = document.getElementById('results-content');

        if (!resultsDiv || !resultsContent) return;

        // Simulate search results based on query
        const mockResults = this.generateMockResults(query);

        resultsContent.innerHTML = mockResults.map(result => `
            <div class="result-card">
                <div class="result-header">
                    <h4>${{result.name}}</h4>
                    <span class="result-type">${{result.type}}</span>
                </div>
                <div class="result-details">
                    <p><strong>Specialty:</strong> ${{result.specialty}}</p>
                    <p><strong>Location:</strong> ${{result.location}}</p>
                    <p><strong>Phone:</strong> ${{result.phone}}</p>
                    <p><strong>Distance:</strong> ${{result.distance}}</p>
                </div>
                <div class="result-actions">
                    <button class="book-appointment-btn" onclick="healthcareDemo.bookAppointment('${{result.id}}')">
                        Book Appointment
                    </button>
                    <button class="get-directions-btn" onclick="healthcareDemo.getDirections('${{result.id}}')">
                        Get Directions
                    </button>
                </div>
            </div>
        `).join('');

        resultsDiv.classList.remove('hidden');
        this.trackInteraction('search_results_shown', {{ query, resultCount: mockResults.length }});
    }}

    generateMockResults(query) {{
        const queryLower = query.toLowerCase();

        // Determine result type based on query
        let resultType = 'General Practice';
        let providerType = 'Clinic';

        if (queryLower.includes('eye') || queryLower.includes('ophthalmology')) {{
            resultType = 'Ophthalmology';
        }} else if (queryLower.includes('children') || queryLower.includes('pediatric')) {{
            resultType = 'Pediatrics';
        }} else if (queryLower.includes('hospital')) {{
            providerType = 'Hospital';
        }} else if (queryLower.includes('pharmacy')) {{
            providerType = 'Pharmacy';
            resultType = 'Pharmacy Services';
        }}

        const locations = ['Accra Central', 'Madina', 'East Legon', 'Circle', 'Kokomlemle'];
        const mockProviders = [
            'Premier Medical Center',
            'Accra Regional Hospital',
            'Healthy Living Clinic',
            'Care Plus Medical',
            'Metro Health Center'
        ];

        return Array.from({{ length: 3 }}, (_, i) => ({{
            id: `provider_${{i + 1}}`,
            name: mockProviders[i],
            type: providerType,
            specialty: resultType,
            location: locations[i],
            phone: `+233 ${{String(Math.floor(Math.random() * 900) + 100)}} ${{String(Math.floor(Math.random() * 900000) + 100000)}}`,
            distance: `${{(Math.random() * 10 + 0.5).toFixed(1)}} km`
        }})));
    }}

    demoFeature(feature) {{
        this.featureUsage++;
        this.trackInteraction('feature_demo', {{ feature }});

        const featureActions = {{
            'provider_search': () => this.simulateVoiceQuery('Find me a general practitioner near me'),
            'emergency_services': () => this.startHealthcareCall('emergency'),
            'appointment_booking': () => this.showAppointmentBooking(),
            'insurance_verification': () => this.showInsuranceVerification(),
            'multilanguage_support': () => this.showLanguageOptions(),
            'human_escalation': () => this.showHumanEscalation()
        }};

        const action = featureActions[feature];
        if (action) {{
            action();
        }}

        this.updateAnalytics();
    }}

    showAppointmentBooking() {{
        const modal = this.createModal('Appointment Booking Demo', `
            <div class="appointment-demo">
                <h4>Book an Appointment</h4>
                <p>The voice assistant can help you:</p>
                <ul>
                    <li>Check provider availability</li>
                    <li>Schedule appointments</li>
                    <li>Send confirmation via SMS/email</li>
                    <li>Set appointment reminders</li>
                </ul>
                <div class="demo-simulation">
                    <p><strong>AI:</strong> "I found available slots for Dr. Smith. Would you prefer Tuesday at 2 PM or Wednesday at 10 AM?"</p>
                    <p><strong>Patient:</strong> "Tuesday at 2 PM works for me."</p>
                    <p><strong>AI:</strong> "Perfect! I've booked your appointment for Tuesday, March 15th at 2 PM. You'll receive a confirmation SMS shortly."</p>
                </div>
            </div>
        `);
        modal.show();
    }}

    showInsuranceVerification() {{
        const modal = this.createModal('Insurance Verification Demo', `
            <div class="insurance-demo">
                <h4>Insurance Coverage Verification</h4>
                <p>Automatically verify coverage with:</p>
                <ul>
                    <li>In-network provider search</li>
                    <li>Coverage benefit details</li>
                    <li>Copay and deductible information</li>
                    <li>Pre-authorization requirements</li>
                </ul>
                <div class="coverage-status">
                    <div class="coverage-item">
                        <span class="status-indicator approved"></span>
                        <span>Dr. Smith - Covered (90%)</span>
                    </div>
                    <div class="coverage-item">
                        <span class="status-indicator approved"></span>
                        <span>Accra Medical Center - In Network</span>
                    </div>
                </div>
            </div>
        `);
        modal.show();
    }}

    createModal(title, content) {{
        const modalHTML = `
            <div class="demo-modal-overlay">
                <div class="demo-modal">
                    <div class="modal-header">
                        <h3>${{title}}</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-content">
                        ${{content}}
                    </div>
                </div>
            </div>
        `;

        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = modalHTML;
        document.body.appendChild(modalDiv);

        const closeBtn = modalDiv.querySelector('.modal-close');
        const overlay = modalDiv.querySelector('.demo-modal-overlay');

        const closeModal = () => {{
            document.body.removeChild(modalDiv);
        }};

        closeBtn.addEventListener('click', closeModal);
        overlay.addEventListener('click', (e) => {{
            if (e.target === overlay) closeModal();
        }});

        return {{ show: () => modalDiv.style.display = 'block' }};
    }}

    endCall() {{
        this.callActive = false;

        const callStatus = document.getElementById('call-status');
        const startBtn = document.getElementById('start-call');
        const emergencyBtn = document.getElementById('emergency-call');

        if (callStatus) callStatus.classList.add('hidden');
        if (startBtn) startBtn.classList.remove('hidden');
        if (emergencyBtn) emergencyBtn.classList.remove('hidden');

        this.trackInteraction('voice_call_ended');
    }}

    trackInteraction(event, data = {{}}) {{
        this.interactions++;
        console.log('Healthcare Demo Event:', event, data);

        // Send to analytics endpoint
        fetch('/api/analytics/demo-event', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                demoId: this.config.demoId,
                event,
                data,
                timestamp: new Date().toISOString(),
                organization: this.config.organizationName
            }})
        }}).catch(console.error);

        this.updateAnalytics();
    }}

    updateAnalytics() {{
        const interactionCount = document.getElementById('interaction-count');
        const callCount = document.getElementById('call-count');
        const featureUsage = document.getElementById('feature-usage');
        const timeSpent = document.getElementById('time-spent');

        if (interactionCount) interactionCount.textContent = this.interactions;
        if (callCount) callCount.textContent = this.callCount;
        if (featureUsage) featureUsage.textContent = this.featureUsage;
        if (timeSpent) {{
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            timeSpent.textContent = `${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
        }}
    }}

    startTimeTracking() {{
        setInterval(() => this.updateAnalytics(), 1000);
    }}

    showWelcomeAnimation() {{
        // Add welcome animation logic here
        console.log('Welcome to Healthcare Provider Demo!');
    }}

    showTypingIndicator() {{
        // Add typing indicator logic here
    }}

    hideTypingIndicator() {{
        // Hide typing indicator logic here
    }}
}}

// Global functions for demo interactions
function simulateQuery(query) {{
    if (window.healthcareDemo) {{
        window.healthcareDemo.simulateVoiceQuery(query);
    }}
}}

function demoFeature(feature) {{
    if (window.healthcareDemo) {{
        window.healthcareDemo.demoFeature(feature);
    }}
}}

function toggleAdminPanel() {{
    const panel = document.getElementById('admin-panel');
    if (panel) {{
        panel.classList.toggle('hidden');
    }}
}}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {{
    console.log('Healthcare Demo JavaScript loaded');
}});
"""

def generate_healthcare_demo_css() -> str:
    """Generate healthcare-specific demo CSS."""
    return """
:root {
    --primary-blue: #2563eb;
    --healthcare-green: #16a34a;
    --emergency-red: #dc2626;
    --warning-orange: #ea580c;
    --success-green: #059669;
    --background-gradient: linear-gradient(135deg, #2563eb 0%, #16a34a 100%);
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --border-color: #e5e7eb;
    --background-light: #f9fafb;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--text-primary);
    background: var(--background-gradient);
    min-height: 100vh;
}

.demo-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

/* Header Styles */
.demo-header {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 30px;
    margin-bottom: 30px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 20px;
}

.brand-section {
    display: flex;
    align-items: center;
    gap: 20px;
}

.logo-area {
    display: flex;
    align-items: center;
    gap: 15px;
}

.logo-icon {
    font-size: 3em;
    background: var(--background-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.brand-text h1 {
    font-size: 2.5em;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 5px;
}

.tagline {
    font-size: 1.1em;
    color: var(--text-secondary);
    font-weight: 500;
}

.region-info {
    display: flex;
    gap: 10px;
    flex-direction: column;
    align-items: flex-start;
}

.region-badge, .demo-badge {
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 0.9em;
    font-weight: 500;
}

.region-badge {
    background: var(--healthcare-green);
    color: white;
}

.demo-badge {
    background: var(--primary-blue);
    color: white;
}

.live-stats {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}

.stat-item {
    text-align: center;
    padding: 15px;
    background: var(--background-light);
    border-radius: 10px;
    min-width: 100px;
}

.stat-number {
    font-size: 1.8em;
    font-weight: 700;
    color: var(--primary-blue);
    margin-bottom: 5px;
}

.stat-label {
    font-size: 0.85em;
    color: var(--text-secondary);
    font-weight: 500;
}

/* Main Demo Styles */
.demo-main {
    background: white;
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
    margin-bottom: 30px;
}

.demo-intro {
    text-align: center;
    margin-bottom: 40px;
}

.demo-intro h2 {
    font-size: 2.2em;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 15px;
}

.demo-intro p {
    font-size: 1.1em;
    color: var(--text-secondary);
    max-width: 800px;
    margin: 0 auto;
    line-height: 1.7;
}

/* Voice Interaction Panel */
.voice-interaction-panel {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 20px;
    padding: 40px;
    margin-bottom: 40px;
    text-align: center;
    border: 2px solid var(--border-color);
}

.voice-controls {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-bottom: 30px;
    flex-wrap: wrap;
}

.primary-call-button, .emergency-call-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 25px 35px;
    border: none;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.3s ease;
    min-width: 200px;
    position: relative;
    overflow: hidden;
}

.primary-call-button {
    background: var(--healthcare-green);
    color: white;
    box-shadow: 0 8px 30px rgba(22, 163, 74, 0.3);
}

.primary-call-button:hover {
    background: #15803d;
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(22, 163, 74, 0.4);
}

.emergency-call-button {
    background: var(--emergency-red);
    color: white;
    box-shadow: 0 8px 30px rgba(220, 38, 38, 0.3);
}

.emergency-call-button:hover {
    background: #b91c1c;
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(220, 38, 38, 0.4);
}

.button-icon {
    font-size: 2em;
    margin-bottom: 8px;
}

.button-text {
    font-size: 1.1em;
    font-weight: 600;
    margin-bottom: 4px;
}

.button-subtitle {
    font-size: 0.9em;
    opacity: 0.9;
    font-weight: 400;
}

.call-status {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
    padding: 20px;
    background: var(--success-green);
    color: white;
    border-radius: 15px;
    margin-bottom: 20px;
}

.call-status.hidden {
    display: none;
}

.status-indicator {
    width: 12px;
    height: 12px;
    background: white;
    border-radius: 50%;
}

.status-indicator.pulsing {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

.status-text {
    display: flex;
    flex-direction: column;
}

.status-title {
    font-weight: 600;
    font-size: 1.1em;
}

.status-subtitle {
    font-size: 0.95em;
    opacity: 0.9;
}

.end-call-button {
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.end-call-button:hover {
    background: rgba(255, 255, 255, 0.3);
}

.voice-suggestions h4 {
    color: var(--text-primary);
    margin-bottom: 15px;
    font-size: 1.1em;
}

.suggestion-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
}

.suggestion-chip {
    background: white;
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 10px 18px;
    border-radius: 25px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 0.9em;
}

.suggestion-chip:hover {
    background: var(--primary-blue);
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
}

/* Features Grid */
.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 25px;
    margin-bottom: 40px;
}

.feature-card {
    background: var(--background-light);
    border: 1px solid var(--border-color);
    border-radius: 15px;
    padding: 25px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.feature-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.1);
    border-color: var(--primary-blue);
}

.feature-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;
}

.feature-icon {
    font-size: 2.5em;
    background: var(--background-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.feature-card h3 {
    color: var(--text-primary);
    font-size: 1.2em;
    font-weight: 600;
}

.feature-card p {
    color: var(--text-secondary);
    margin-bottom: 20px;
    line-height: 1.6;
}

.try-feature-btn {
    background: var(--primary-blue);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
    width: 100%;
}

.try-feature-btn:hover {
    background: #1d4ed8;
    transform: translateY(-2px);
}

/* Demo Results */
.demo-results {
    margin-top: 30px;
    padding: 25px;
    background: var(--background-light);
    border-radius: 15px;
    border: 1px solid var(--border-color);
}

.demo-results.hidden {
    display: none;
}

.results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.results-header h3 {
    color: var(--text-primary);
    font-size: 1.3em;
}

.clear-btn {
    background: var(--text-secondary);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9em;
}

.result-card {
    background: white;
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 15px;
}

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.result-header h4 {
    color: var(--text-primary);
    font-size: 1.1em;
}

.result-type {
    background: var(--healthcare-green);
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.8em;
}

.result-details {
    margin-bottom: 15px;
}

.result-details p {
    margin-bottom: 5px;
    font-size: 0.95em;
    color: var(--text-secondary);
}

.result-actions {
    display: flex;
    gap: 10px;
}

.book-appointment-btn, .get-directions-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9em;
    transition: all 0.3s ease;
}

.book-appointment-btn {
    background: var(--healthcare-green);
    color: white;
}

.get-directions-btn {
    background: var(--primary-blue);
    color: white;
}

.book-appointment-btn:hover, .get-directions-btn:hover {
    transform: translateY(-1px);
    opacity: 0.9;
}

/* Integration Showcase */
.integration-showcase {
    margin-top: 40px;
    padding: 30px;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 15px;
}

.integration-showcase h3 {
    text-align: center;
    color: var(--text-primary);
    margin-bottom: 25px;
    font-size: 1.4em;
}

.integration-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
}

.integration-item {
    text-align: center;
    padding: 20px;
    background: white;
    border-radius: 10px;
    border: 1px solid var(--border-color);
    transition: all 0.3s ease;
}

.integration-item:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.integration-icon {
    font-size: 2em;
    margin-bottom: 10px;
}

.integration-name {
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 5px;
}

.integration-desc {
    font-size: 0.9em;
    color: var(--text-secondary);
}

/* Admin Panel */
.admin-panel {
    position: fixed;
    bottom: 80px;
    right: 20px;
    width: 350px;
    background: white;
    border-radius: 15px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
    border: 1px solid var(--border-color);
    z-index: 1000;
}

.admin-panel.hidden {
    display: none;
}

.panel-header {
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.panel-header h4 {
    color: var(--text-primary);
    font-size: 1.1em;
}

.toggle-btn {
    background: var(--text-secondary);
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8em;
}

.analytics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    padding: 20px;
}

.metric-card {
    text-align: center;
    padding: 15px;
    background: var(--background-light);
    border-radius: 10px;
}

.metric-card h5 {
    color: var(--text-secondary);
    font-size: 0.9em;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 1.5em;
    font-weight: 700;
    color: var(--primary-blue);
    margin-bottom: 4px;
}

.metric-change {
    font-size: 0.8em;
    color: var(--text-secondary);
}

.floating-admin-btn {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: var(--primary-blue);
    color: white;
    border: none;
    padding: 15px 20px;
    border-radius: 50px;
    cursor: pointer;
    box-shadow: 0 8px 30px rgba(37, 99, 235, 0.3);
    font-weight: 500;
    transition: all 0.3s ease;
    z-index: 999;
}

.floating-admin-btn:hover {
    background: #1d4ed8;
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(37, 99, 235, 0.4);
}

/* Modal Styles */
.demo-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2000;
}

.demo-modal {
    background: white;
    border-radius: 15px;
    max-width: 600px;
    width: 90%;
    max-height: 80%;
    overflow-y: auto;
    box-shadow: 0 25px 80px rgba(0, 0, 0, 0.3);
}

.modal-header {
    padding: 25px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-header h3 {
    color: var(--text-primary);
    font-size: 1.3em;
}

.modal-close {
    background: none;
    border: none;
    font-size: 1.5em;
    cursor: pointer;
    color: var(--text-secondary);
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.3s ease;
}

.modal-close:hover {
    background: var(--background-light);
    color: var(--text-primary);
}

.modal-content {
    padding: 25px;
}

.appointment-demo, .insurance-demo {
    color: var(--text-primary);
}

.appointment-demo h4, .insurance-demo h4 {
    margin-bottom: 15px;
    color: var(--primary-blue);
}

.appointment-demo ul, .insurance-demo ul {
    margin: 15px 0;
    padding-left: 20px;
}

.appointment-demo li, .insurance-demo li {
    margin-bottom: 8px;
    color: var(--text-secondary);
}

.demo-simulation {
    background: var(--background-light);
    padding: 20px;
    border-radius: 10px;
    margin-top: 20px;
    border-left: 4px solid var(--primary-blue);
}

.demo-simulation p {
    margin-bottom: 10px;
    line-height: 1.6;
}

.coverage-status {
    margin-top: 20px;
}

.coverage-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px;
    background: var(--background-light);
    border-radius: 8px;
    margin-bottom: 8px;
}

.status-indicator.approved {
    background: var(--success-green);
}

/* Responsive Design */
@media (max-width: 768px) {
    .demo-container {
        padding: 15px;
    }

    .header-content {
        flex-direction: column;
        text-align: center;
    }

    .live-stats {
        justify-content: center;
    }

    .voice-controls {
        flex-direction: column;
        align-items: center;
    }

    .primary-call-button, .emergency-call-button {
        width: 100%;
        max-width: 300px;
    }

    .features-grid {
        grid-template-columns: 1fr;
    }

    .integration-grid {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    }

    .admin-panel {
        width: 90%;
        right: 5%;
        bottom: 20px;
    }

    .result-actions {
        flex-direction: column;
    }

    .analytics-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 480px) {
    .brand-text h1 {
        font-size: 2em;
    }

    .demo-intro h2 {
        font-size: 1.8em;
    }

    .voice-interaction-panel {
        padding: 25px 20px;
    }

    .suggestion-chips {
        flex-direction: column;
        align-items: center;
    }

    .suggestion-chip {
        width: 100%;
        max-width: 300px;
        text-align: center;
    }
}
"""

def generate_healthcare_analytics_js(demo_id: str) -> str:
    """Generate healthcare-specific analytics JavaScript."""
    return f"""
class HealthcareAnalytics {{
    constructor(demoId) {{
        this.demoId = demoId;
        this.sessionId = this.generateSessionId();
        this.startTime = Date.now();
        this.events = [];

        this.setupTracking();
    }}

    generateSessionId() {{
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }}

    setupTracking() {{
        // Track page visibility
        document.addEventListener('visibilitychange', () => {{
            this.trackEvent('page_visibility_change', {{
                hidden: document.hidden
            }});
        }});

        // Track scroll behavior
        let scrollTimeout;
        window.addEventListener('scroll', () => {{
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {{
                const scrollPercent = Math.round(
                    (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
                );
                this.trackEvent('scroll_depth', {{ percent: scrollPercent }});
            }}, 100);
        }});

        // Track clicks on healthcare-specific elements
        document.addEventListener('click', (e) => {{
            const target = e.target.closest('[data-analytics]');
            if (target) {{
                this.trackEvent('element_click', {{
                    element: target.dataset.analytics,
                    text: target.textContent.trim().substring(0, 100)
                }});
            }}
        }});

        // Track form interactions (if any)
        document.addEventListener('input', (e) => {{
            if (e.target.matches('input, textarea, select')) {{
                this.trackEvent('form_interaction', {{
                    field: e.target.name || e.target.id || 'unknown',
                    type: e.target.type
                }});
            }}
        }});
    }}

    trackEvent(eventName, eventData = {{}}) {{
        const event = {{
            eventName,
            eventData,
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId,
            demoId: this.demoId,
            url: window.location.href,
            userAgent: navigator.userAgent,
            sessionDuration: Date.now() - this.startTime,
            viewport: {{
                width: window.innerWidth,
                height: window.innerHeight
            }}
        }};

        this.events.push(event);

        // Send to analytics endpoint
        this.sendAnalytics(event);

        // Store locally as backup
        this.storeEventLocally(event);
    }}

    async sendAnalytics(event) {{
        try {{
            await fetch('/api/analytics/healthcare-demo', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(event)
            }});
        }} catch (error) {{
            console.warn('Analytics tracking failed:', error);
            // Store failed events for retry
            this.storeFailedEvent(event);
        }}
    }}

    storeEventLocally(event) {{
        try {{
            const stored = JSON.parse(localStorage.getItem('healthcare_demo_events') || '[]');
            stored.push(event);

            // Keep only last 100 events
            if (stored.length > 100) {{
                stored.splice(0, stored.length - 100);
            }}

            localStorage.setItem('healthcare_demo_events', JSON.stringify(stored));
        }} catch (error) {{
            console.warn('Local storage failed:', error);
        }}
    }}

    storeFailedEvent(event) {{
        try {{
            const failed = JSON.parse(localStorage.getItem('failed_healthcare_events') || '[]');
            failed.push(event);
            localStorage.setItem('failed_healthcare_events', JSON.stringify(failed));
        }} catch (error) {{
            console.warn('Failed event storage failed:', error);
        }}
    }}

    retryFailedEvents() {{
        try {{
            const failed = JSON.parse(localStorage.getItem('failed_healthcare_events') || '[]');
            if (failed.length > 0) {{
                failed.forEach(event => this.sendAnalytics(event));
                localStorage.removeItem('failed_healthcare_events');
            }}
        }} catch (error) {{
            console.warn('Retry failed events failed:', error);
        }}
    }}

    // Healthcare-specific tracking methods
    trackProviderSearch(query, results) {{
        this.trackEvent('provider_search', {{
            query,
            resultCount: results.length,
            searchType: 'voice_assistant'
        }});
    }}

    trackAppointmentBooking(providerId, appointmentType) {{
        this.trackEvent('appointment_booking_attempt', {{
            providerId,
            appointmentType,
            source: 'demo'
        }});
    }}

    trackEmergencyAction(actionType) {{
        this.trackEvent('emergency_action', {{
            actionType,
            timestamp: new Date().toISOString(),
            urgency: 'high'
        }});
    }}

    trackFeatureEngagement(feature, duration) {{
        this.trackEvent('feature_engagement', {{
            feature,
            duration,
            engagementLevel: duration > 30000 ? 'high' : duration > 10000 ? 'medium' : 'low'
        }});
    }}

    trackVoiceInteraction(interactionType, duration) {{
        this.trackEvent('voice_interaction', {{
            interactionType,
            duration,
            successful: duration > 5000 // Assume success if call lasted more than 5 seconds
        }});
    }}

    // Export analytics data
    exportAnalytics() {{
        const data = {{
            demoId: this.demoId,
            sessionId: this.sessionId,
            sessionDuration: Date.now() - this.startTime,
            events: this.events,
            summary: this.generateSummary()
        }};

        const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `healthcare_demo_analytics_${{this.sessionId}}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }}

    generateSummary() {{
        const eventTypes = {{}};
        let totalInteractions = 0;
        let voiceInteractions = 0;
        let featureUsage = 0;

        this.events.forEach(event => {{
            eventTypes[event.eventName] = (eventTypes[event.eventName] || 0) + 1;

            if (event.eventName.includes('interaction') || event.eventName.includes('click')) {{
                totalInteractions++;
            }}

            if (event.eventName.includes('voice')) {{
                voiceInteractions++;
            }}

            if (event.eventName.includes('feature')) {{
                featureUsage++;
            }}
        }});

        return {{
            totalEvents: this.events.length,
            eventTypes,
            totalInteractions,
            voiceInteractions,
            featureUsage,
            sessionDuration: Date.now() - this.startTime,
            engagementScore: this.calculateEngagementScore()
        }};
    }}

    calculateEngagementScore() {{
        const sessionDuration = Date.now() - this.startTime;
        const interactionCount = this.events.filter(e =>
            e.eventName.includes('interaction') ||
            e.eventName.includes('click') ||
            e.eventName.includes('voice')
        ).length;

        // Simple engagement score: interactions per minute
        const score = (interactionCount / (sessionDuration / 60000)) * 10;
        return Math.min(100, Math.round(score));
    }}

    // Cleanup on page unload
    cleanup() {{
        this.trackEvent('session_end', {{
            totalDuration: Date.now() - this.startTime,
            totalEvents: this.events.length,
            engagementScore: this.calculateEngagementScore()
        }});

        // Retry any failed events
        this.retryFailedEvents();
    }}
}}

// Initialize analytics
const healthcareAnalytics = new HealthcareAnalytics('{demo_id}');

// Cleanup on page unload
window.addEventListener('beforeunload', () => {{
    healthcareAnalytics.cleanup();
}});

// Make analytics available globally for demo app
window.healthcareAnalytics = healthcareAnalytics;

console.log('Healthcare Demo Analytics initialized for demo: {demo_id}');
"""

async def deploy_demo_files(demo_id: str, files: Dict[str, str]):
    """Deploy demo files to hosting infrastructure."""
    try:
        # Simulate file deployment
        logger.info(f"Deploying demo files for {demo_id}")

        # In a real implementation, this would:
        # 1. Upload files to S3/CDN
        # 2. Update DNS records
        # 3. Setup SSL certificates
        # 4. Configure analytics tracking

        # For now, just log the deployment
        for filename, content in files.items():
            logger.info(f"Deployed {filename} ({len(content)} characters)")

        return True
    except Exception as e:
        logger.error(f"Failed to deploy demo files: {str(e)}")
        raise

async def setup_demo_analytics(demo_id: str, organization_name: str, features: List[str]):
    """Setup analytics tracking for the healthcare demo."""
    try:
        # Setup analytics configuration
        analytics_config = {
            "demo_id": demo_id,
            "organization": organization_name,
            "features": features,
            "tracking_events": [
                "demo_loaded",
                "voice_call_started",
                "voice_call_ended",
                "provider_search",
                "appointment_booking",
                "emergency_action",
                "feature_demo",
                "session_end"
            ],
            "kpis": [
                "demo_engagement_time",
                "voice_interaction_rate",
                "feature_usage_rate",
                "conversion_metrics"
            ]
        }

        logger.info(f"Setup analytics for healthcare demo: {demo_id}")
        return analytics_config
    except Exception as e:
        logger.error(f"Failed to setup demo analytics: {str(e)}")
        raise

@router.get("/healthcare-demo/{demo_id}/analytics")
async def get_demo_analytics(
    demo_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get analytics data for a healthcare demo.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Fetching demo analytics for demo_id={demo_id}, organization={org_id}")

        # This would fetch real analytics data
        return {
            "demo_id": demo_id,
            "total_views": 150,
            "unique_visitors": 120,
            "average_session_duration": "4:32",
            "voice_interactions": 85,
            "feature_demos": 240,
            "conversion_rate": 0.12,
            "top_features": [
                {"name": "provider_search", "usage": 85},
                {"name": "appointment_booking", "usage": 45},
                {"name": "emergency_services", "usage": 25}
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting demo analytics for organization={org_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get demo analytics: {str(e)}"
        )