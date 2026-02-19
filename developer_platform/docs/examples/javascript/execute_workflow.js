/**
 * Execute an n8n Workflow
 *
 * This example demonstrates how to execute an n8n workflow.
 */

const API_KEY = process.env.KASAAI_API_KEY || 'your_api_key_here';
const BASE_URL = 'https://developer.ailabsafrica.com';

/**
 * Execute an n8n workflow
 * @param {string} workflowId - The workflow ID to execute
 * @param {Object} [data=null] - Optional input data for the workflow
 * @returns {Promise<Object>} Execution result with status and output
 */
async function executeWorkflow(workflowId, data = null) {
  const endpoint = `${BASE_URL}/api/v1/n8n/workflows/${workflowId}/execute`;

  const payload = data ? { data } : {};

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
 * Get the status of a workflow execution
 * @param {string} executionId - The execution ID
 * @returns {Promise<Object>} Execution status object
 */
async function getExecutionStatus(executionId) {
  const endpoint = `${BASE_URL}/api/v1/n8n/executions/${executionId}`;

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
 * List workflow executions
 * @param {string} [workflowId] - Optional workflow ID to filter executions
 * @param {number} [limit=10] - Maximum number of executions to return
 * @returns {Promise<Object>} List of execution objects
 */
async function listExecutions(workflowId = null, limit = 10) {
  const params = new URLSearchParams({ limit });
  if (workflowId) params.append('workflow_id', workflowId);

  const endpoint = `${BASE_URL}/api/v1/n8n/executions?${params}`;

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
 * Wait for a workflow execution to complete
 * @param {string} executionId - The execution ID to monitor
 * @param {number} [maxWait=60] - Maximum seconds to wait
 * @param {number} [checkInterval=2] - Seconds between checks
 * @returns {Promise<Object>} Final execution status
 */
async function waitForExecution(executionId, maxWait = 60, checkInterval = 2) {
  const startTime = Date.now();

  while ((Date.now() - startTime) / 1000 < maxWait) {
    const status = await getExecutionStatus(executionId);

    if (status.finished || status.stoppedAt) {
      return status;
    }

    await new Promise(resolve => setTimeout(resolve, checkInterval * 1000));
  }

  throw new Error(`Execution ${executionId} did not complete in ${maxWait} seconds`);
}

/**
 * Main function to demonstrate workflow execution
 */
async function main() {
  const workflowId = process.env.WORKFLOW_ID;

  if (!workflowId) {
    console.error('❌ Error: WORKFLOW_ID environment variable not set');
    console.error('   Set it with: export WORKFLOW_ID=your_workflow_id');
    process.exit(1);
  }

  try {
    // Execute workflow with sample data
    console.log(`🚀 Executing workflow: ${workflowId}`);

    const sampleData = {
      customer_name: 'John Doe',
      email: 'john@example.com',
      message: 'Hello from the API!'
    };

    const execution = await executeWorkflow(workflowId, sampleData);

    console.log('✅ Workflow execution started!');
    console.log(`   Execution ID: ${execution.id}`);
    console.log(`   Status: ${execution.status}`);
    console.log();

    // Wait for execution to complete
    console.log('⏳ Waiting for execution to complete...');
    const finalStatus = await waitForExecution(execution.id, 120);

    console.log('✅ Execution completed!');
    console.log(`   Status: ${finalStatus.status}`);
    console.log(`   Finished: ${finalStatus.finished}`);

    if (finalStatus.data) {
      console.log(`   Output:`, finalStatus.data);
    }

    // List recent executions for this workflow
    console.log(`\n📋 Recent executions for workflow ${workflowId}:`);
    const executions = await listExecutions(workflowId, 5);

    for (const exec of executions.executions || []) {
      const statusIcon = exec.finished ? '✅' : '⏳';
      console.log(`${statusIcon} ${exec.id} - ${exec.status} - ${exec.startedAt}`);
    }

  } catch (error) {
    if (error.message.includes('did not complete')) {
      console.error(`⏱️  ${error.message}`);
    } else {
      console.error(`❌ Error executing workflow: ${error.message}`);
    }
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { executeWorkflow, getExecutionStatus, listExecutions, waitForExecution };
