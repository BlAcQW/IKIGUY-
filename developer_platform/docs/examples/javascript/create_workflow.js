/**
 * Create an n8n Workflow
 *
 * This example demonstrates how to create an n8n workflow for automation.
 */

const API_KEY = process.env.KASAAI_API_KEY || 'your_api_key_here';
const BASE_URL = 'https://developer.ailabsafrica.com';

/**
 * Create a new n8n workflow
 * @param {Object} options - Workflow configuration
 * @param {string} options.name - Workflow name
 * @param {string} [options.description] - Optional workflow description
 * @param {Array} [options.nodes] - List of workflow nodes
 * @param {Object} [options.connections] - Node connections configuration
 * @param {boolean} [options.active=false] - Whether to activate the workflow immediately
 * @returns {Promise<Object>} Created workflow object
 */
async function createWorkflow({
  name,
  description = null,
  nodes = null,
  connections = null,
  active = false
}) {
  const endpoint = `${BASE_URL}/api/v1/n8n/workflows`;

  const payload = { name, active };

  if (description) payload.description = description;
  if (nodes) payload.nodes = nodes;
  if (connections) payload.connections = connections;

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
 * Create a simple workflow with a webhook trigger
 * @param {string} name - Workflow name
 * @param {string} [webhookPath='webhook'] - Path for the webhook endpoint
 * @returns {Promise<Object>} Created workflow object
 */
async function createSimpleWebhookWorkflow(name, webhookPath = 'webhook') {
  const nodes = [
    {
      id: 'webhook',
      name: 'Webhook',
      type: 'n8n-nodes-base.webhook',
      typeVersion: 1,
      position: [250, 300],
      parameters: {
        path: webhookPath,
        httpMethod: 'POST',
        responseMode: 'onReceived',
        responseData: 'allEntries'
      }
    },
    {
      id: 'set',
      name: 'Process Data',
      type: 'n8n-nodes-base.set',
      typeVersion: 1,
      position: [450, 300],
      parameters: {
        values: {
          string: [
            {
              name: 'status',
              value: 'processed'
            },
            {
              name: 'message',
              value: 'Data received and processed'
            }
          ]
        }
      }
    }
  ];

  const connections = {
    'Webhook': {
      main: [
        [
          {
            node: 'Process Data',
            type: 'main',
            index: 0
          }
        ]
      ]
    }
  };

  return await createWorkflow({
    name,
    description: 'Simple webhook workflow that processes incoming data',
    nodes,
    connections,
    active: true
  });
}

/**
 * Create a workflow that sends Slack notifications for completed calls
 * @param {string} name - Workflow name
 * @param {string} slackWebhook - Slack webhook URL
 * @returns {Promise<Object>} Created workflow object
 */
async function createCallNotificationWorkflow(name, slackWebhook) {
  const nodes = [
    {
      id: 'webhook',
      name: 'Call Webhook',
      type: 'n8n-nodes-base.webhook',
      typeVersion: 1,
      position: [250, 300],
      parameters: {
        path: 'call-completed',
        httpMethod: 'POST'
      }
    },
    {
      id: 'slack',
      name: 'Send to Slack',
      type: 'n8n-nodes-base.slack',
      typeVersion: 1,
      position: [450, 300],
      parameters: {
        webhookUrl: slackWebhook,
        text: 'Call completed: {{$json.call_id}}',
        otherOptions: {
          mrkdwn: true
        }
      }
    }
  ];

  const connections = {
    'Call Webhook': {
      main: [
        [
          {
            node: 'Send to Slack',
            type: 'main',
            index: 0
          }
        ]
      ]
    }
  };

  return await createWorkflow({
    name,
    description: 'Sends Slack notification when a call is completed',
    nodes,
    connections,
    active: true
  });
}

/**
 * Main function to demonstrate workflow creation
 */
async function main() {
  try {
    // Example 1: Create a simple webhook workflow
    console.log('Creating simple webhook workflow...');
    const workflow1 = await createSimpleWebhookWorkflow(
      'Simple Data Processor',
      'process-data'
    );

    console.log('✅ Workflow 1 created successfully!');
    console.log(`   ID: ${workflow1.id}`);
    console.log(`   Name: ${workflow1.name}`);
    console.log(`   Active: ${workflow1.active}`);
    console.log();

    // Example 2: Create a call notification workflow
    const slackWebhook = process.env.SLACK_WEBHOOK_URL;
    if (slackWebhook) {
      console.log('Creating call notification workflow...');
      const workflow2 = await createCallNotificationWorkflow(
        'Call Completion Notifier',
        slackWebhook
      );

      console.log('✅ Workflow 2 created successfully!');
      console.log(`   ID: ${workflow2.id}`);
      console.log(`   Name: ${workflow2.name}`);
      console.log(`   Active: ${workflow2.active}`);
    } else {
      console.log('⚠️  Skipping Slack workflow (SLACK_WEBHOOK_URL not set)');
    }

  } catch (error) {
    console.error('❌ Error creating workflow:', error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { createWorkflow, createSimpleWebhookWorkflow, createCallNotificationWorkflow };
