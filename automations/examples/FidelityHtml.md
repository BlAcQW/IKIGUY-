<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fidelity Bank Ghana - AI Helpdesk Assistant Ama</title>
    
    <!-- Tailwind CSS for styling -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Google Fonts: Inter for a professional, corporate feel -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap" rel="stylesheet">

    <style>
        /* Define custom styles and color palette based on Fidelity Bank branding */
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f7fafc; /* Light gray background */
        }
        .fidelity-orange { color: #f37021; }
        .fidelity-blue { color: #0033a0; }
        .fidelity-orange-bg { background-color: #f37021; }
        .fidelity-blue-bg { background-color: #0033a0; }
        .hero-gradient {
            background: linear-gradient(to right, #0033a0, #0056b3);
        }
        .card-hover {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .card-hover:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
    </style>
</head>
<body class="min-h-screen">

    <!-- Header Section -->
    <header class="hero-gradient text-white">
        <div class="container mx-auto px-6 py-20 text-center">
            <div class="max-w-4xl mx-auto">
                <img src="https://placehold.co/150x150/ffffff/f37021?text=FB" alt="Fidelity Bank" class="w-32 h-32 md:w-40 md:h-40 mx-auto rounded-full border-4 border-white shadow-lg mb-6">
                <h1 class="text-4xl md:text-6xl font-black uppercase tracking-wider">Fidelity Bank Helpdesk</h1>
                <p class="mt-4 text-xl md:text-2xl font-light">Instant, Reliable Support. Anytime, Anywhere.</p>
                <p class="mt-2 text-lg text-gray-200">Your trusted partner in banking.</p>
            </div>
        </div>
    </header>

    <main class="w-full max-w-6xl mx-auto p-4 sm:p-6 lg:p-12">
        <!-- Introduction to AI Assistant -->
        <section class="bg-white p-8 rounded-xl shadow-lg -mt-20 z-10 relative">
            <div class="text-center">
                <h2 class="text-3xl font-bold fidelity-blue">Welcome to Your Virtual Assistant</h2>
                <p class="mt-3 text-lg text-gray-700 max-w-3xl mx-auto">
                    Have a question? Speak with <span class="font-bold fidelity-orange">Ama</span>, our official AI helpdesk assistant. She can provide instant answers about our accounts, loans, digital banking, and much more.
                </p>
                <p class="mt-6 font-semibold text-gray-800">Click the widget at the bottom right to start your conversation.</p>
            </div>
        </section>

        <!-- How Ama Can Help Section -->
        <section class="mt-16">
            <h2 class="text-3xl font-bold text-center fidelity-blue mb-10">How Ama Can Assist You Today</h2>
            <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
                <!-- Help 1: Account Info -->
                <div class="bg-white p-6 rounded-lg shadow-md card-hover text-center">
                    <div class="p-4 bg-orange-100 rounded-full inline-block mb-4">
                        <svg class="h-8 w-8 fidelity-orange" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/></svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800">Account Information</h3>
                    <p class="text-gray-600 mt-2">Learn about our Reserve, Prestige, and Smart accounts to find the perfect fit.</p>
                </div>
                <!-- Help 2: Loan Products -->
                <div class="bg-white p-6 rounded-lg shadow-md card-hover text-center">
                     <div class="p-4 bg-orange-100 rounded-full inline-block mb-4">
                        <svg class="h-8 w-8 fidelity-orange" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800">Loan Enquiries</h3>
                    <p class="text-gray-600 mt-2">Get details on personal loans, home loans, and our SME financing options.</p>
                </div>
                <!-- Help 3: Digital Banking -->
                <div class="bg-white p-6 rounded-lg shadow-md card-hover text-center">
                     <div class="p-4 bg-orange-100 rounded-full inline-block mb-4">
                        <svg class="h-8 w-8 fidelity-orange" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800">Digital Banking Support</h3>
                    <p class="text-gray-600 mt-2">Ask about our Mobile App, USSD (*776#), and IVY WhatsApp banking.</p>
                </div>
                <!-- Help 4: Branch Info -->
                <div class="bg-white p-6 rounded-lg shadow-md card-hover text-center">
                     <div class="p-4 bg-orange-100 rounded-full inline-block mb-4">
                       <svg class="h-8 w-8 fidelity-orange" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800">Find a Branch or ATM</h3>
                    <p class="text-gray-600 mt-2">Locate any of our 73 branches or 120+ VISA-enabled ATMs nationwide.</p>
                </div>
            </div>
        </section>
        
        <!-- Security Reminder Section -->
        <section class="mt-16 bg-red-50 border-l-4 border-red-500 text-red-700 p-6 rounded-md">
            <div class="flex">
                <div class="py-1"><svg class="h-6 w-6 text-red-500 mr-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg></div>
                <div>
                    <p class="font-bold">Your Security is Our Priority</p>
                    <p class="text-sm">Fidelity Bank will never ask you for your PIN, password, or full card number. Please do not share these details with anyone.</p>
                </div>
            </div>
        </section>
        
        <!-- Call to Action -->
        <section class="mt-20 fidelity-blue-bg text-white p-10 rounded-lg text-center">
             <h2 class="text-3xl font-bold">Ready to Get Started?</h2>
             <p class="mt-3 text-lg max-w-2xl mx-auto text-gray-200">Whether you need help with your account or want to explore new products, Ama is here to assist you 24/7.</p>
             <p class="mt-6 text-lg font-semibold">Click the widget below to start the conversation!</p>
        </section>
    </main>
    
    <!-- Footer -->
    <footer class="text-center p-6 mt-10">
        <p class="text-gray-600">&copy; 2025 Fidelity Bank Ghana. All rights reserved.</p>
        <p class="text-sm text-gray-500 mt-1">Head Office: Ridge Tower, 10 Ambassadorial Enclave, West Ridge, Accra</p>
    </footer>

    <!-- Vapi AI Widget -->
    <vapi-widget
      public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
      assistant-id="f78fc6e5-7f69-4590-8c60-27b46374d20f"
      mode="voice"
      theme="dark"
      base-bg-color="#000000"
      accent-color="#14B8A6"
      cta-button-color="#000000"
      cta-button-text-color="#ffffff"
      border-radius="large"
      size="full"
      position="bottom-right"
      title="Talk with Ama, our Helpdesk assistant."
      start-button-text="Start"
      end-button-text="End Call"
      chat-first-message="Hey, How can I help you today?"
      chat-placeholder="Type your message..."
      voice-show-transcript="true"
      consent-required="false"
      consent-title="Terms and conditions"
      consent-content="By clicking 'Agree,' and each time I interact with this AI agent, I consent to the recording, storage, and sharing of my communications with third-party service providers, and as otherwise described in our Terms of Service."
      consent-storage-key="vapi_widget_consent"
    ></vapi-widget>

    <script src="https://unpkg.com/@vapi-ai/client-sdk-react/dist/embed/widget.umd.js" async type="text/javascript"></script>

</body>
</html>
