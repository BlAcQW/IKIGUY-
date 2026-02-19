/**
 * Initiate an Outbound Call
 *
 * This example demonstrates how to initiate an outbound call using your voice assistant.
 */

const API_KEY = process.env.KASAAI_API_KEY || 'your_api_key_here';
const BASE_URL = 'https://developer.ailabsafrica.com';

/**
 * Initiate an outbound call
 * @param {Object} options - Call configuration
 * @param {string} options.assistantId - The assistant ID to use for the call
 * @param {string} options.phoneNumber - Phone number in E.164 format
 * @param {string} [options.task='outbound'] - Call type
 * @returns {Promise<Object>} Call object with status and details
 */
async function initiateCall({ assistantId, phoneNumber, task = 'outbound' }) {
  const endpoint = `${BASE_URL}/api/v1/calls`;

  const payload = {
    assistant_id: assistantId,
    phone_number: phoneNumber,
    task
  };

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
 * Get the status of a call
 * @param {string} callId - The call ID
 * @returns {Promise<Object>} Call status object
 */
async function getCallStatus(callId) {
  const endpoint = `${BASE_URL}/api/v1/calls/${callId}`;

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
 * Monitor a call until it completes or times out
 * @param {string} callId - The call ID to monitor
 * @param {number} [maxWait=60] - Maximum seconds to wait
 */
async function monitorCall(callId, maxWait = 60) {
  console.log(`\n📞 Monitoring call: ${callId}`);
  const startTime = Date.now();

  while ((Date.now() - startTime) / 1000 < maxWait) {
    try {
      const status = await getCallStatus(callId);
      const currentStatus = status.status;

      console.log(`   Status: ${currentStatus}`);

      if (['completed', 'failed', 'busy', 'no-answer'].includes(currentStatus)) {
        console.log(`\n✅ Call ended with status: ${currentStatus}`);
        if (status.duration) {
          console.log(`   Duration: ${status.duration} seconds`);
        }
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds

    } catch (error) {
      console.error(`❌ Error checking call status: ${error.message}`);
      break;
    }
  }
}

/**
 * Main function to demonstrate initiating a call
 */
async function main() {
  const assistantId = process.env.ASSISTANT_ID;
  const phoneNumber = process.env.PHONE_NUMBER;

  if (!assistantId) {
    console.error('❌ Error: ASSISTANT_ID environment variable not set');
    console.error('   Set it with: export ASSISTANT_ID=your_assistant_id');
    process.exit(1);
  }

  if (!phoneNumber) {
    console.error('❌ Error: PHONE_NUMBER environment variable not set');
    console.error('   Set it with: export PHONE_NUMBER=+1234567890');
    process.exit(1);
  }

  try {
    // Initiate the call
    console.log(`📞 Initiating call to ${phoneNumber}...`);
    const call = await initiateCall({
      assistantId,
      phoneNumber
    });

    console.log('✅ Call initiated successfully!');
    console.log(`   Call ID: ${call.id}`);
    console.log(`   Status: ${call.status}`);
    console.log(`   Phone: ${call.phone_number}`);
    console.log(`   Type: ${call.type}`);

    // Monitor the call
    await monitorCall(call.id, 120);

  } catch (error) {
    console.error(`❌ Error initiating call: ${error.message}`);

    // Provide helpful error messages
    if (error.message.includes('400')) {
      console.error('\n💡 Common issues:');
      console.error('   - Phone number must be in E.164 format (+country_code + number)');
      console.error('   - Check that your assistant_id is correct');
    } else if (error.message.includes('402')) {
      console.error('\n💡 Insufficient credits. Add credits at:');
      console.error('   https://developer.ailabsafrica.com/billing');
    } else if (error.message.includes('429')) {
      console.error('\n💡 Rate limit exceeded. Wait a moment and try again.');
    }

    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { initiateCall, getCallStatus, monitorCall };
