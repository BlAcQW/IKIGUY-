/**
 * Create an AI Voice Assistant
 *
 * This example demonstrates how to create a new voice assistant using the KasaAI API.
 * The assistant can be configured with custom personality, voice, and language.
 */

const API_KEY = process.env.KASAAI_API_KEY || 'your_api_key_here';
const BASE_URL = 'https://developer.ailabsafrica.com';

/**
 * Create a new voice assistant
 * @param {Object} options - Assistant configuration
 * @param {string} options.name - Name of the assistant
 * @param {string} options.systemPrompt - System prompt that defines assistant behavior
 * @param {string} [options.voice='alloy'] - Voice to use
 * @param {string} [options.language='en'] - Language code
 * @param {string} [options.firstMessage] - Optional greeting message
 * @returns {Promise<Object>} Created assistant data
 */
async function createAssistant({
  name,
  systemPrompt,
  voice = 'alloy',
  language = 'en',
  firstMessage = null
}) {
  const endpoint = `${BASE_URL}/api/v1/assistants`;

  const payload = {
    name,
    system_prompt: systemPrompt,
    voice,
    language
  };

  if (firstMessage) {
    payload.first_message = firstMessage;
  }

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`API Error ${response.status}: ${JSON.stringify(error)}`);
  }

  return await response.json();
}

/**
 * Main function to demonstrate assistant creation
 */
async function main() {
  try {
    // Create a customer support assistant
    const assistant = await createAssistant({
      name: 'Customer Support Bot',
      systemPrompt:
        'You are a helpful customer support assistant for TechCorp. ' +
        'Be friendly, professional, and solve customer issues efficiently. ' +
        'If you cannot solve an issue, escalate to a human agent.',
      voice: 'alloy',
      language: 'en',
      firstMessage: 'Hello! I\'m here to help with any questions or issues you have. How can I assist you today?'
    });

    console.log('✅ Successfully created assistant!');
    console.log(`   ID: ${assistant.id}`);
    console.log(`   Name: ${assistant.name}`);
    console.log(`   Status: ${assistant.status}`);
    console.log(`   Voice: ${assistant.voice}`);
    console.log(`   Language: ${assistant.language}`);
    console.log(`   Created: ${assistant.created_at}`);

  } catch (error) {
    console.error('❌ Error creating assistant:', error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { createAssistant };
