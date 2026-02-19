/**
 * Check API Usage and Quota
 *
 * This example demonstrates how to check your API usage, quota, and billing information.
 */

const API_KEY = process.env.KASAAI_API_KEY || 'your_api_key_here';
const BASE_URL = 'https://developer.ailabsafrica.com';

/**
 * Get current API quota and usage limits
 * @returns {Promise<Object>} Quota information including limits and current usage
 */
async function getQuota() {
  const endpoint = `${BASE_URL}/api/v1/usage/quota`;

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
 * Get detailed usage statistics
 * @param {string} [startDate] - Start date in YYYY-MM-DD format
 * @param {string} [endDate] - End date in YYYY-MM-DD format
 * @param {string} [granularity='day'] - Data granularity (hour, day, week, month)
 * @returns {Promise<Object>} Usage statistics with breakdown by service
 */
async function getUsageStats(startDate = null, endDate = null, granularity = 'day') {
  // Default to last 30 days if not specified
  if (!endDate) {
    endDate = new Date().toISOString().split('T')[0];
  }
  if (!startDate) {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    startDate = date.toISOString().split('T')[0];
  }

  const params = new URLSearchParams({ start_date: startDate, end_date: endDate, granularity });
  const endpoint = `${BASE_URL}/api/v1/usage/stats?${params}`;

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
 * Get current billing information
 * @returns {Promise<Object>} Billing info including credits, balance, and next billing date
 */
async function getBillingInfo() {
  const endpoint = `${BASE_URL}/api/v1/usage/billing`;

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
 * Format credits with appropriate units
 * @param {number} credits - Credit amount
 * @returns {string} Formatted credit string
 */
function formatCredits(credits) {
  if (credits >= 1000000) {
    return `${(credits / 1000000).toFixed(2)}M`;
  } else if (credits >= 1000) {
    return `${(credits / 1000).toFixed(2)}K`;
  } else {
    return credits.toFixed(2);
  }
}

/**
 * Print formatted quota information
 * @param {Object} quota - Quota data
 */
function printQuotaInfo(quota) {
  console.log('📊 API Quota & Limits\n');
  console.log('Rate Limits:');
  console.log(`   Requests per minute: ${quota.rate_limit_minute || 'N/A'}`);
  console.log(`   Requests per hour:   ${quota.rate_limit_hour || 'N/A'}`);
  console.log(`   Requests per day:    ${quota.rate_limit_day || 'N/A'}`);
  console.log();

  console.log('Current Usage:');
  console.log(`   This minute: ${quota.usage_minute || 0}`);
  console.log(`   This hour:   ${quota.usage_hour || 0}`);
  console.log(`   This day:    ${quota.usage_day || 0}`);
  console.log();
}

/**
 * Print formatted usage statistics
 * @param {Object} stats - Usage statistics data
 */
function printUsageStats(stats) {
  console.log('📈 Usage Statistics\n');

  const totalRequests = stats.total_requests || 0;
  const totalCredits = stats.total_credits_used || 0;

  console.log(`Total Requests: ${totalRequests.toLocaleString()}`);
  console.log(`Total Credits Used: ${formatCredits(totalCredits)}`);
  console.log();

  // Breakdown by service
  if (stats.by_service) {
    console.log('Breakdown by Service:');
    for (const [service, data] of Object.entries(stats.by_service)) {
      const requestsCount = data.requests || 0;
      const credits = data.credits || 0;
      console.log(`   ${service.charAt(0).toUpperCase() + service.slice(1)}:`);
      console.log(`      Requests: ${requestsCount.toLocaleString()}`);
      console.log(`      Credits:  ${formatCredits(credits)}`);
    }
    console.log();
  }

  // Time series data
  if (stats.time_series && stats.time_series.length > 0) {
    console.log('Recent Activity:');
    const recentEntries = stats.time_series.slice(-5); // Last 5 entries
    for (const entry of recentEntries) {
      const date = entry.date || 'N/A';
      const requestsCount = entry.requests || 0;
      console.log(`   ${date}: ${requestsCount.toLocaleString()} requests`);
    }
    console.log();
  }
}

/**
 * Print formatted billing information
 * @param {Object} billing - Billing data
 */
function printBillingInfo(billing) {
  console.log('💳 Billing Information\n');

  const creditsRemaining = billing.credits_remaining || 0;
  const creditsUsed = billing.credits_used || 0;
  const monthlySpend = billing.monthly_spend || 0;

  console.log(`Credits Remaining: ${formatCredits(creditsRemaining)}`);
  console.log(`Credits Used (This Month): ${formatCredits(creditsUsed)}`);
  console.log(`Monthly Spend: $${monthlySpend.toFixed(2)}`);
  console.log();

  if (billing.plan) {
    console.log(`Plan: ${billing.plan}`);
  }

  if (billing.next_billing_date) {
    console.log(`Next Billing Date: ${billing.next_billing_date}`);
  }
  console.log();
}

/**
 * Main function to demonstrate usage checking
 */
async function main() {
  try {
    // Get quota information
    console.log('Fetching quota information...\n');
    const quota = await getQuota();
    printQuotaInfo(quota);

    // Get usage statistics
    console.log('Fetching usage statistics...\n');
    const stats = await getUsageStats();
    printUsageStats(stats);

    // Get billing information
    console.log('Fetching billing information...\n');
    const billing = await getBillingInfo();
    printBillingInfo(billing);

    // Check if approaching limits
    const usagePercent = ((quota.usage_day || 0) / (quota.rate_limit_day || 1)) * 100;
    if (usagePercent > 80) {
      console.log("⚠️  WARNING: You've used over 80% of your daily quota!");
      console.log('   Consider upgrading your plan at:');
      console.log('   https://developer.ailabsafrica.com/billing');
    }

    // Check credits
    const creditsRemaining = billing.credits_remaining || 0;
    if (creditsRemaining < 100) {
      console.log('⚠️  WARNING: Low credits remaining!');
      console.log('   Add credits at:');
      console.log('   https://developer.ailabsafrica.com/billing');
    }

  } catch (error) {
    console.error('❌ Error fetching usage information:', error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { getQuota, getUsageStats, getBillingInfo };
