/**
 * Lead API client for DiaServe.
 *
 * Public endpoint - no auth required.
 */

import { buildApiUrl, API_ENDPOINTS } from "../api-config";

export interface LeadSubmissionData {
  name: string;
  email: string;
  phone?: string;
  property_id: string;
}

export interface LeadSubmissionResponse {
  message: string;
  contact_id: string;
}

/**
 * Submit a lead from the public contact form.
 *
 * @param data - Lead form data
 * @returns Response with message and contact_id
 */
export async function submitLead(
  data: LeadSubmissionData
): Promise<LeadSubmissionResponse> {
  const response = await fetch(buildApiUrl(API_ENDPOINTS.leads.submit), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(
      error?.detail || `Failed to submit lead (${response.status})`
    );
  }

  return response.json();
}
