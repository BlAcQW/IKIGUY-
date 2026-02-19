<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GLICO Life - AI Helpdesk Assistant Ama</title>
    
    <!-- Tailwind CSS for styling -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Google Fonts: Inter for a professional, corporate feel -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap" rel="stylesheet">

    <style>
        /* Define custom styles and color palette based on GLICO Life branding */
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f8f9fa; /* Light grey background */
        }
        .glico-orange { color: #f58220; }
        .glico-blue { color: #003366; }
        .glico-orange-bg { background-color: #f58220; }
        .glico-blue-bg { background-color: #003366; }
        .hero-gradient {
            background: linear-gradient(to right, #003366, #004a8d);
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
                <img src="https://placehold.co/150x150/ffffff/003366?text=GL" alt="GLICO Life" class="w-32 h-32 md:w-40 md:h-40 mx-auto rounded-full border-4 border-white shadow-lg mb-6">
                <h1 class="text-4xl md:text-6xl font-black uppercase tracking-wider">GLICO Life Helpdesk</h1>
                <p class="mt-4 text-xl md:text-2xl font-light">Your Life, Our Passion. Instant Support.</p>
                <p class="mt-2 text-lg text-gray-200">Cushioning you for life.</p>
            </div>
        </div>
    </header>

    <main class="w-full max-w-6xl mx-auto p-4 sm:p-6 lg:p-12">
        <!-- Introduction to AI Assistant -->
        <section class="bg-white p-8 rounded-xl shadow-lg -mt-20 z-10 relative">
            <div class="text-center">
                <h2 class="text-3xl font-bold glico-blue">Speak with Your Virtual Assistant</h2>
                <p class="mt-3 text-lg text-gray-700 max-w-3xl mx-auto">
                    Have a question? Talk to <span class="font-bold glico-orange">Ama</span>, our official AI helpdesk assistant. She provides clear and friendly guidance on all our life insurance and savings products.
                </p>
                <p class="mt-6 font-semibold text-gray-800">Click the widget at the bottom right to start the conversation.</p>
            </div>
        </section>

        <!-- How Ama Can Help Section -->
        <section class="mt-16">
            <h2 class="text-3xl font-bold text-center glico-blue mb-10">How Ama Can Help You Plan for Life</h2>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                <!-- Help 1: Education & Savings -->
                <div class="bg-white p-6 rounded-lg shadow-md card-hover text-center">
                    <div class="p-4 bg-orange-100 rounded-full inline-block mb-4">
                        <svg class="h-8 w-8 glico-orange" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M12 14l9-5-9-5-9 5 9 5z" /><path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222 4 2.222V20" /></svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800">Education & Savings</h3>
                    <p class="text-gray-600 mt-2">Learn about our E-GEEP and Enhanced Life Savings plans to secure your family's future.</p>
                </div>
                <!-- Help 2: Funeral & Family Life -->
                <div class="bg-white p-6 rounded-lg shadow-md card-hover text-center">
                     <div class="p-4 bg-orange-100 rounded-full inline-block mb-4">
                        <svg class="h-8 w-8 glico-orange" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800">Funeral & Family Life</h3>
                    <p class="text-gray-600 mt-2">Get information on our Funeral Policy and Family Life Comprehensive Plan for peace of mind.</p>
                </div>
                <!-- Help 3: Travel & Accident -->
                <div class="bg-white p-6 rounded-lg shadow-md card-hover text-center">
                     <div class="p-4 bg-orange-100 rounded-full inline-block mb-4">
                        <svg class="h-8 w-8 glico-orange" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800">Travel & Accident</h3>
                    <p class="text-gray-600 mt-2">Ask about our Travel Insurance (with COVID-19 cover) and Personal Accident plans.</p>
                </div>
            </div>
        </section>
        
        <!-- Call to Action -->
        <section class="mt-20 glico-blue-bg text-white p-10 rounded-lg text-center">
             <h2 class="text-3xl font-bold">Have a Question? Ama is Here to Help.</h2>
             <p class="mt-3 text-lg max-w-2xl mx-auto text-gray-200">Get instant, clear, and friendly answers to all your questions about GLICO Life's products. We're here to help you make the best decisions for your future.</p>
             <p class="mt-6 text-lg font-semibold">Click the widget below to start the conversation!</p>
        </section>
    </main>
    
    <!-- Footer -->
    <footer class="text-center p-6 mt-10">
        <p class="text-gray-600">&copy; 2025 GLICO Life. All rights reserved.</p>
        <p class="text-sm text-gray-500 mt-1">GLICO House, Number 47 Kwame Nkrumah Avenue, Accra | 020 222 2113</p>
    </footer>

    <!-- Vapi AI Widget -->
    <vapi-widget
      public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
      assistant-id="7503e241-6d66-4440-8af6-40086c925ef3"
      mode="voice"
      theme="dark"
      base-bg-color="#000000"
      accent-color="#14B8A6"
      cta-button-color="#000000"
      cta-button-text-color="#ffffff"
      border-radius="large"
      size="full"
      position="bottom-right"
      title="Click to talk to Ama, our helpdesk assistant."
      start-button-text="Start"
      end-button-text="End Call"
      chat-first-message="Hey, How can I help you today?"
      chat-placeholder="Type your message..."
      voice-show-transcript="true"
      consent-required="true"
      consent-title="Terms and conditions"
      consent-content="By clicking 'Agree,' and each time I interact with this AI agent, I consent to the recording, storage, and sharing of my communications with third-party service providers, and as otherwise described in our Terms of Service."
      consent-storage-key="vapi_widget_consent"
    ></vapi-widget>

    <script src="https://unpkg.com/@vapi-ai/client-sdk-react/dist/embed/widget.umd.js" async type="text/javascript"></script>

</body>
</html>
