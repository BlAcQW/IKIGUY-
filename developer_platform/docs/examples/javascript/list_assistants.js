/**
 * List All Voice Assistants
 *
 * This example demonstrates how to retrieve a list of all your voice assistants.
 */

const API_KEY = process.env.KASAAI_API_KEY || 'your_api_key_here';
const BASE_URL = 'https://developer.ailabsafrica.com';

/**
 * List all voice assistants
 * @param {number} [limit=10] - Maximum number of assistants to return
 * @param {number} [offset=0] - Number of assistants to skip
 * @returns {Promise<Array>} List of assistant objects
 */
async function listAssistants(limit = 10, offset = 0) {
  const params = new URLSearchParams({ limit, offset });
  const endpoint = `${BASE_URL}/api/v1/assistants?${params}`;

  const response = await fetch(endpoint, {
    method: 'GET',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`API Error ${response.status}: ${JSON.stringify(error)}`);
  }

  return await response.json();
}

/**
 * Get a specific assistant by ID
 * @param {string} assistantId - The assistant ID
 * @returns {Promise<Object>} Assistant object
 */
async function getAssistant(assistantId) {
  const endpoint = `${BASE_URL}/api/v1/assistants/${assistantId}`;

  const response = await fetch(endpoint, {
    method: 'GET',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`API Error ${response.status}: ${JSON.stringify(error)}`);
  }

  return await response.json();
}

/**
 * Main function to demonstrate listing assistants
 */
async function main() {
  try {
    // List all assistants
    console.log('Fetching assistants...');
    const assistants = await listAssistants(20);

    if (assistants.length === 0) {
      console.log('No assistants found. Create one first using create_assistant.js');
      return;
    }

    console.log(`\n✅ Found ${assistants.length} assistant(s):\n`);

    for (const assistant of assistants) {
      console.log(`📱 ${assistant.name}`);
      console.log(`   ID: ${assistant.id}`);
      console.log(`   Status: ${assistant.status}`);
      console.log(`   Voice: ${assistant.voice}`);
      console.log(`   Language: ${assistant.language}`);
      console.log(`   Created: ${assistant.created_at}`);
      console.log();
    }

    // Example: Get a specific assistant
    if (assistants.length > 0) {
      const firstId = assistants[0].id;
      console.log(`Getting details for assistant: ${firstId}`);
      const assistant = await getAssistant(firstId);
      console.log(`✅ Retrieved assistant: ${assistant.name}`);
    }

  } catch (error) {
    console.error('❌ Error fetching assistants:', error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { listAssistants, getAssistant };
