/**
 * Mock Data Service for EstateFlow.
 * 
 * Provides mock data for local frontend development without backend.
 */

import { API_ENDPOINTS } from './api-config';
import { PropertyType, PropertyStatus, PetPolicy } from './types/property';

// Mock Users (2 Super Admins, 3 Sub Admins)
export const MOCK_USERS = [
    {
        id: "super-admin-1",
        email: "admin@estateflow.local",
        first_name: "Super",
        last_name: "Admin 1",
        role: "admin",
        organization_id: "org-1"
    },
    {
        id: "super-admin-2",
        email: "super2@estateflow.local",
        first_name: "Super",
        last_name: "Admin 2",
        role: "admin",
        organization_id: "org-1"
    },
    {
        id: "sub-admin-1",
        email: "sub1@estateflow.local",
        first_name: "Sub",
        last_name: "Admin 1",
        role: "agent", // "sub admin" mapping to agent or manager
        organization_id: "org-1"
    },
    {
        id: "sub-admin-2",
        email: "sub2@estateflow.local",
        first_name: "Sub",
        last_name: "Admin 2",
        role: "agent",
        organization_id: "org-1"
    },
    {
        id: "sub-admin-3",
        email: "sub3@estateflow.local",
        first_name: "Sub",
        last_name: "Admin 3",
        role: "agent",
        organization_id: "org-1"
    }
];

// Mock Token
export const MOCK_TOKEN = "mock-jwt-token-for-development";

// Currencies
export const MOCK_CURRENCIES = [
    { code: "USD", name: "US Dollar", symbol: "$" },
    { code: "GHS", name: "Ghanaian Cedi", symbol: "₵" },
    { code: "EUR", name: "Euro", symbol: "€" },
    { code: "GBP", name: "British Pound", symbol: "£" }
];

export const MOCK_EXCHANGE_RATES = {
    base_currency: "USD",
    rates: {
        "USD": 1,
        "GHS": 12.5, // Requested Rate
        "EUR": 0.92,
        "GBP": 0.79
    },
    last_updated: new Date().toISOString(),
    source: "Mock Data"
};

// Mock Contacts
export const MOCK_CONTACTS = [
    {
        id: "cont-1",
        organization_id: "org-1",
        name: "Akosua Mensah",
        email: "akosua@example.com",
        phone: "+233 24 111 2222",
        property_type_preferences: ["apartment", "villa"],
        location_preferences: ["East Legon", "Cantonments"],
        budget_min: 200000,
        budget_max: 500000,
        interest_status: "hot",
        lead_status: "qualified",
        tags: ["VIP", "Ready to Buy"],
        created_at: new Date(Date.now() - 30 * 86400000).toISOString(),
        updated_at: new Date().toISOString(),
        last_contacted: new Date(Date.now() - 2 * 86400000).toISOString(),
    },
    {
        id: "cont-2",
        organization_id: "org-1",
        name: "Kwame Boateng",
        email: "kwame@example.com",
        phone: "+233 55 333 4444",
        property_type_preferences: ["house"],
        location_preferences: ["Spintex", "Tema"],
        budget_min: 150000,
        budget_max: 300000,
        interest_status: "warm",
        lead_status: "contacted",
        tags: ["First-time Buyer"],
        created_at: new Date(Date.now() - 60 * 86400000).toISOString(),
        updated_at: new Date().toISOString(),
        last_contacted: new Date(Date.now() - 5 * 86400000).toISOString(),
    },
    {
        id: "cont-3",
        organization_id: "org-1",
        name: "Abena Appiah",
        email: "abena@example.com",
        phone: "+233 20 555 6666",
        property_type_preferences: ["penthouse"],
        location_preferences: ["Airport Residential"],
        budget_min: 1000000,
        budget_max: 2000000,
        interest_status: "hot",
        lead_status: "negotiating",
        tags: ["Investor"],
        created_at: new Date(Date.now() - 15 * 86400000).toISOString(),
        updated_at: new Date().toISOString(),
        last_contacted: new Date(Date.now() - 1 * 86400000).toISOString(),
    },
    {
        id: "cont-4",
        organization_id: "org-1",
        name: "Kofi Owusu",
        email: "kofi@example.com",
        phone: "+233 24 777 8888",
        property_type_preferences: ["apartment"],
        location_preferences: ["Osu"],
        budget_min: 100000,
        budget_max: 200000,
        interest_status: "cold",
        lead_status: "new",
        tags: ["Rental"],
        created_at: new Date(Date.now() - 5 * 86400000).toISOString(),
        updated_at: new Date().toISOString(),
    }
];

// Mock Bookings
export const MOCK_BOOKINGS = [
    {
        id: "book-1",
        organization_id: "org-1",
        property_id: "prop-1",
        contact_id: "cont-1",
        agent_id: "sub-admin-1",
        scheduled_at: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
        duration_minutes: 60,
        booking_type: "in-person",
        status: "confirmed",
        contact_name: "Akosua Mensah",
        contact_email: "akosua@example.com",
        contact_phone: "+233 24 111 2222",
        notes: "Wants to see the beach access specifically.",
        created_at: new Date(Date.now() - 2 * 86400000).toISOString(),
        updated_at: new Date().toISOString(),
        reminders: []
    },
    {
        id: "book-2",
        organization_id: "org-1",
        property_id: "prop-2",
        contact_id: "cont-2",
        agent_id: "sub-admin-2",
        scheduled_at: new Date(Date.now() + 2 * 86400000).toISOString(), // Day after tomorrow
        duration_minutes: 30,
        booking_type: "virtual",
        status: "requested",
        contact_name: "Kwame Boateng",
        contact_email: "kwame@example.com",
        contact_phone: "+233 55 333 4444",
        notes: "Virtual tour via Zoom preferred.",
        created_at: new Date(Date.now() - 1 * 86400000).toISOString(),
        updated_at: new Date().toISOString(),
        reminders: []
    },
    {
        id: "book-3",
        organization_id: "org-1",
        property_id: "prop-4",
        contact_id: "cont-3",
        scheduled_at: new Date(Date.now() - 3 * 86400000).toISOString(), // 3 days ago
        duration_minutes: 90,
        booking_type: "in-person",
        status: "completed",
        contact_name: "Abena Appiah",
        contact_email: "abena@example.com",
        contact_phone: "+233 20 555 6666",
        notes: "Looking for an investment penthouse.",
        created_at: new Date(Date.now() - 5 * 86400000).toISOString(),
        updated_at: new Date().toISOString(),
        reminders: []
    }
];

// Mock Invoices
export const MOCK_INVOICES = [
    {
        id: "inv-1",
        organization_id: "org-1",
        invoice_number: "INV-2025-001",
        invoice_date: new Date(Date.now() - 10 * 86400000).toISOString(),
        due_date: new Date(Date.now() + 20 * 86400000).toISOString(),
        contact_id: "cont-1",
        contact_name: "Akosua Mensah",
        contact_email: "akosua@example.com",
        property_id: "prop-1",
        property_name: "Luxury Seaside Villa",
        line_items: [
            { description: "Villa Purchase Deposit", quantity: 1, unit_price: 120000, amount: 120000 }
        ],
        subtotal: 120000,
        tax_amount: 0,
        total_amount: 120000,
        currency: "USD",
        status: "paid",
        paid_amount: 120000,
        paid_date: new Date(Date.now() - 5 * 86400000).toISOString(),
        created_by: "super-admin-1",
        created_at: new Date(Date.now() - 10 * 86400000).toISOString(),
        updated_at: new Date().toISOString()
    },
    {
        id: "inv-2",
        organization_id: "org-1",
        invoice_number: "INV-2025-002",
        invoice_date: new Date(Date.now() - 2 * 86400000).toISOString(),
        due_date: new Date(Date.now() + 5 * 86400000).toISOString(),
        contact_id: "cont-3",
        contact_name: "Abena Appiah",
        contact_email: "abena@example.com",
        property_id: "prop-4",
        property_name: "Exclusive Penthouse Suite",
        line_items: [
            { description: "Agency Fee", quantity: 1, unit_price: 45000, amount: 45000 },
            { description: "Legal Document Processing", quantity: 1, unit_price: 5000, amount: 5000 }
        ],
        subtotal: 50000,
        tax_amount: 0,
        total_amount: 50000,
        currency: "USD",
        status: "sent",
        paid_amount: 0,
        created_by: "super-admin-1",
        created_at: new Date(Date.now() - 2 * 86400000).toISOString(),
        updated_at: new Date().toISOString()
    },
    {
        id: "inv-3",
        organization_id: "org-1",
        invoice_number: "INV-2025-003",
        invoice_date: new Date(Date.now() - 15 * 86400000).toISOString(),
        due_date: new Date(Date.now() - 1 * 86400000).toISOString(),
        contact_id: "cont-2",
        contact_name: "Kwame Boateng",
        contact_email: "kwame@example.com",
        property_id: "prop-2",
        property_name: "Modern Urban Apartment",
        line_items: [
            { description: "Rental Advance (6 Months)", quantity: 6, unit_price: 2500, amount: 15000 }
        ],
        subtotal: 15000,
        tax_amount: 0,
        total_amount: 15000,
        currency: "USD",
        status: "overdue",
        paid_amount: 0,
        created_by: "sub-admin-1",
        created_at: new Date(Date.now() - 15 * 86400000).toISOString(),
        updated_at: new Date().toISOString()
    }
];

// Mock Properties Data
const MOCK_PROPERTIES = [
    {
        id: "prop-1",
        organization_id: "org-1",
        name: "Luxury Seaside Villa",
        description: "Stunning 5-bedroom villa with direct beach access and panoramic ocean views.",
        property_type: PropertyType.VILLA,
        status: PropertyStatus.ACTIVE,
        location: {
            address: "12 Palm Grove Avenue",
            city: "Accra",
            country: "Ghana",
            neighborhood: "Labadi",
            zip_code: "GA-100-1234"
        },
        neighborhood_data: { schools: [], amenities: [] },
        features: {
            bedrooms: 5, bathrooms: 6, parking_spaces: 4, sqft: 4500,
            pool: true, garden: true, balcony: true,
            pet_policy: PetPolicy.ALLOWED, furnished: true,
            elevator: false, air_conditioning: true, heating: false,
            fireplace: false, security_system: true, gym: true, storage: true,
            concierge: true, newly_built: false
        },
        financial: {
            price_usd: 1200000,
            base_currency: "USD",
            discount_percentage: 5
        },
        images: [
            "https://images.unsplash.com/photo-1613490493576-7fde63acd811?q=80&w=2671&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&q=80&w=2670"
        ],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    },
    {
        id: "prop-2",
        organization_id: "org-1",
        name: "Modern Urban Apartment",
        description: "Sleek 2-bedroom apartment in the heart of the city.",
        property_type: PropertyType.APARTMENT,
        status: PropertyStatus.ACTIVE,
        location: {
            address: "45 Independence Arch",
            city: "Accra",
            country: "Ghana",
            neighborhood: "Osu",
            zip_code: "GA-050-5555"
        },
        neighborhood_data: { schools: [], amenities: [] },
        features: {
            bedrooms: 2, bathrooms: 2, parking_spaces: 1, sqft: 1200,
            pool: false, garden: false, balcony: true,
            pet_policy: PetPolicy.CONDITIONAL, furnished: false,
            elevator: true, air_conditioning: true, heating: false,
            fireplace: false, security_system: true, gym: true, storage: true,
            concierge: true, newly_built: true, garage: true, renovated: false
        },
        financial: { price_usd: 350000, base_currency: "USD", discount_percentage: 10 },
        images: [
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&q=80&w=2670",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&q=80&w=2580"
        ],
        created_at: new Date(Date.now() - 86400000).toISOString(),
        updated_at: new Date().toISOString()
    },
    {
        id: "prop-3",
        organization_id: "org-1",
        name: "Contemporary Family Home",
        description: "Spacious 4-bedroom house with a large backyard.",
        property_type: PropertyType.HOUSE,
        status: PropertyStatus.PENDING,
        location: {
            address: "8 Quiet Lane",
            city: "Accra",
            country: "Ghana",
            neighborhood: "East Legon",
            zip_code: "GA-222-9876"
        },
        neighborhood_data: { schools: [], amenities: [] },
        features: {
            bedrooms: 4, bathrooms: 4, parking_spaces: 3, sqft: 3200,
            pool: true, garden: true, balcony: false,
            pet_policy: PetPolicy.ALLOWED, furnished: false,
            elevator: false, air_conditioning: true, heating: false,
            fireplace: true, security_system: true, gym: false, storage: true,
            concierge: false, newly_built: false
        },
        financial: { price_usd: 650000, base_currency: "USD", discount_percentage: 2 },
        images: [
            "https://images.unsplash.com/photo-1600596542815-2a4d04774c71?auto=format&fit=crop&q=80&w=2670"
        ],
        created_at: new Date(Date.now() - 172800000).toISOString(),
        updated_at: new Date().toISOString()
    },
    {
        id: "prop-4",
        organization_id: "org-1",
        name: "Exclusive Penthouse Suite",
        description: "Ultra-luxury penthouse offering 360-degree city views.",
        property_type: PropertyType.PENTHOUSE,
        status: PropertyStatus.ACTIVE,
        location: {
            address: "1 Skyline Boulevard",
            city: "Accra",
            country: "Ghana",
            neighborhood: "Airport Residential",
            zip_code: "GA-010-1111"
        },
        neighborhood_data: { schools: [], amenities: [] },
        features: {
            bedrooms: 3, bathrooms: 4, parking_spaces: 2, sqft: 2800,
            pool: true, garden: true, balcony: true,
            pet_policy: PetPolicy.NOT_ALLOWED, furnished: true,
            elevator: true, air_conditioning: true, heating: true,
            fireplace: true, security_system: true, gym: true, storage: true,
            concierge: true, newly_built: false, garage: true, renovated: true
        },
        financial: { price_usd: 1500000, base_currency: "USD" },
        images: [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&q=80&w=2670"
        ],
        created_at: new Date(Date.now() - 259200000).toISOString(),
        updated_at: new Date().toISOString()
    },
    {
        id: "prop-5",
        organization_id: "org-1",
        name: "Cozy Garden Cottage",
        description: "Charming 2-bedroom cottage surrounded by nature.",
        property_type: PropertyType.HOUSE,
        status: PropertyStatus.SOLD,
        location: {
            address: "22 Green Way",
            city: "Aburi",
            country: "Ghana",
            neighborhood: "Botanical Gardens Area",
            zip_code: "ER-303-4444"
        },
        neighborhood_data: { schools: [], amenities: [] },
        features: {
            bedrooms: 2, bathrooms: 1, parking_spaces: 2, sqft: 1500,
            pool: false, garden: true, balcony: true,
            pet_policy: PetPolicy.ALLOWED, furnished: true,
            elevator: false, air_conditioning: false, heating: false,
            fireplace: true, security_system: false, gym: false, storage: true,
            concierge: false, newly_built: false
        },
        financial: { price_usd: 180000, base_currency: "USD" },
        images: [
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b91d?auto=format&fit=crop&q=80&w=2574"
        ],
        created_at: new Date(Date.now() - 500000000).toISOString(),
        updated_at: new Date().toISOString()
    }
];

/**
 * Intercept fetch requests and return mock data if enabled.
 */
export async function mockFetch(url: string, options?: RequestInit): Promise<Response> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 600));

    const path = url.replace("http://localhost:30039", ""); // Remove base URL
    const urlObj = new URL(url.startsWith('http') ? url : `http://localhost${url}`);
    const pathname = urlObj.pathname;

    console.log(`[Mock API] Request: ${options?.method || 'GET'} ${pathname}`);

    // Auth: Login
    if (pathname === API_ENDPOINTS.auth.login && options?.method === 'POST') {
        const body = JSON.parse(options.body as string);
        if (body.email === "fail@test.com") {
            return new Response(JSON.stringify({ detail: "Invalid credentials" }), { status: 401 });
        }

        // Find user by email
        const user = MOCK_USERS.find(u => u.email === body.email) || MOCK_USERS[0]; // Default to first super admin if not found (for dev convenience)

        return new Response(JSON.stringify({
            access_token: MOCK_TOKEN,
            token_type: "bearer",
            user: user
        }), { status: 200 });
    }

    // Auth: Signup
    if (pathname === API_ENDPOINTS.auth.signup && options?.method === 'POST') {
        return new Response(JSON.stringify({
            access_token: MOCK_TOKEN,
            token_type: "bearer",
            user: MOCK_USERS[0]
        }), { status: 200 });
    }

    // Auth: Me
    if (pathname === API_ENDPOINTS.auth.me) {
        // Return mostly correct user info (simplified for mock, assumes constant login)
        return new Response(JSON.stringify(MOCK_USERS[0]), { status: 200 });
    }

    // Auth: Logout
    if (pathname === API_ENDPOINTS.auth.logout) {
        return new Response(JSON.stringify({ message: "Logged out" }), { status: 200 });
    }

    // Properties: List
    if (pathname === API_ENDPOINTS.properties.list) {
        return new Response(JSON.stringify({
            properties: MOCK_PROPERTIES,
            total: MOCK_PROPERTIES.length,
            limit: 10,
            offset: 0,
            has_more: false
        }), { status: 200 });
    }

    // Properties: Get One
    const matchProp = pathname.match(new RegExp(`^${API_ENDPOINTS.properties.list}/([^/]+)$`));
    if (matchProp && options?.method === 'GET') {
        const id = matchProp[1];
        const prop = MOCK_PROPERTIES.find(p => p.id === id);
        if (prop) {
            return new Response(JSON.stringify(prop), { status: 200 });
        }
        return new Response(JSON.stringify({ detail: "Property not found" }), { status: 404 });
    }

    // Properties: Search
    if (pathname === API_ENDPOINTS.properties.search) {
        // Mock search logic
        return new Response(JSON.stringify({
            matches: MOCK_PROPERTIES.map(p => ({
                property: p,
                score: 0.9,
                property_id: p.id,
                property_data: p
            })),
            total: MOCK_PROPERTIES.length,
            search_timing: { total_ms: 45 }
        }), { status: 200 });
    }

    // Currencies: List
    if (pathname === API_ENDPOINTS.currencies.list) {
        return new Response(JSON.stringify(MOCK_CURRENCIES), { status: 200 });
    }

    // Currencies: Rates
    if (pathname === API_ENDPOINTS.currencies.rates) {
        if (options?.method === 'POST') {
            const body = JSON.parse(options.body as string);
            const { currency_code, rate } = body;

            if (currency_code && rate && MOCK_EXCHANGE_RATES.rates[currency_code as keyof typeof MOCK_EXCHANGE_RATES.rates]) {
                MOCK_EXCHANGE_RATES.rates[currency_code as keyof typeof MOCK_EXCHANGE_RATES.rates] = rate;
                MOCK_EXCHANGE_RATES.last_updated = new Date().toISOString();
                return new Response(JSON.stringify(MOCK_EXCHANGE_RATES), { status: 200 });
            }
            return new Response(JSON.stringify({ detail: "Invalid currency code or rate" }), { status: 400 });
        }
        return new Response(JSON.stringify(MOCK_EXCHANGE_RATES), { status: 200 });
    }

    // Properties: Stats
    if (pathname === API_ENDPOINTS.properties.stats) {
        // Calculate Monthly Rental Value (estimate 0.8% of price)
        const totalRentalValue = MOCK_PROPERTIES.reduce((acc, p) => acc + (p.financial.price_usd * 0.008), 0);
        const avgRentalValue = totalRentalValue / MOCK_PROPERTIES.length;

        return new Response(JSON.stringify({
            active: MOCK_PROPERTIES.filter(p => p.status === PropertyStatus.ACTIVE).length,
            pending: MOCK_PROPERTIES.filter(p => p.status === PropertyStatus.PENDING).length,
            sold: MOCK_PROPERTIES.filter(p => p.status === PropertyStatus.SOLD).length,
            rented: MOCK_PROPERTIES.filter(p => p.status === PropertyStatus.RENTED).length,
            inactive: MOCK_PROPERTIES.filter(p => p.status === PropertyStatus.INACTIVE).length,
            total: MOCK_PROPERTIES.length,
            // Respond with RENTAL value instead of sales price for 'average_price' and 'total_value' as requested
            average_price: avgRentalValue,
            total_value: totalRentalValue,
            by_type: {
                [PropertyType.VILLA]: MOCK_PROPERTIES.filter(p => p.property_type === PropertyType.VILLA).length,
                [PropertyType.APARTMENT]: MOCK_PROPERTIES.filter(p => p.property_type === PropertyType.APARTMENT).length,
                [PropertyType.HOUSE]: MOCK_PROPERTIES.filter(p => p.property_type === PropertyType.HOUSE).length,
                [PropertyType.PENTHOUSE]: MOCK_PROPERTIES.filter(p => p.property_type === PropertyType.PENTHOUSE).length,
            }
        }), { status: 200 });
    }

    // Contacts: List (Handling both potential paths)
    if (pathname === "/api/v1/contacts" || pathname === "/api/v1/campaigns/contacts") {
        return new Response(JSON.stringify({
            contacts: MOCK_CONTACTS,
            total: MOCK_CONTACTS.length,
            limit: 100,
            offset: 0
        }), { status: 200 });
    }

    // Bookings: List
    if (pathname === API_ENDPOINTS.bookings.list) {
        return new Response(JSON.stringify({
            bookings: MOCK_BOOKINGS,
            total: MOCK_BOOKINGS.length,
            limit: 100,
            offset: 0
        }), { status: 200 });
    }

    // Invoices: List
    if (pathname === API_ENDPOINTS.invoices.list) {
        return new Response(JSON.stringify({
            invoices: MOCK_INVOICES,
            total: MOCK_INVOICES.length,
            limit: 100,
            offset: 0,
            has_more: false
        }), { status: 200 });
    }

    // Invoice Stats
    if (pathname === "/api/v1/invoices/stats") {
        return new Response(JSON.stringify({
            total_invoices: MOCK_INVOICES.length,
            total_revenue: MOCK_INVOICES.reduce((acc, inv) => acc + inv.total_amount, 0),
            pending_amount: MOCK_INVOICES.filter(i => i.status === "sent" || i.status === "overdue").reduce((acc, inv) => acc + inv.total_amount, 0),
            overdue_amount: MOCK_INVOICES.filter(i => i.status === "overdue").reduce((acc, inv) => acc + inv.total_amount, 0),
            draft_count: MOCK_INVOICES.filter(i => i.status === "draft").length,
            sent_count: MOCK_INVOICES.filter(i => i.status === "sent").length,
            paid_count: MOCK_INVOICES.filter(i => i.status === "paid").length,
            overdue_count: MOCK_INVOICES.filter(i => i.status === "overdue").length,
            currency: "USD"
        }), { status: 200 });
    }

    // Bookings: Get One
    const matchBooking = pathname.match(/^\/api\/v1\/bookings\/([^/]+)$/);
    if (matchBooking && options?.method === 'GET') {
        const id = matchBooking[1];
        const booking = MOCK_BOOKINGS.find(b => b.id === id);
        if (booking) return new Response(JSON.stringify(booking), { status: 200 });
        return new Response(JSON.stringify({ detail: "Booking not found" }), { status: 404 });
    }

    // Invoices: Get One
    const matchInvoice = pathname.match(/^\/api\/v1\/invoices\/([^/]+)$/);
    if (matchInvoice && options?.method === 'GET') {
        const id = matchInvoice[1];
        const invoice = MOCK_INVOICES.find(i => i.id === id);
        if (invoice) return new Response(JSON.stringify(invoice), { status: 200 });
        return new Response(JSON.stringify({ detail: "Invoice not found" }), { status: 404 });
    }

    // Default: Return 404 for unmocked endpoints
    console.warn(`[Mock API] No mock handler for ${pathname}`);
    return new Response(JSON.stringify({ detail: "Not found in mock" }), { status: 404 });
}
