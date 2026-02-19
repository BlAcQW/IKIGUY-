/**
 * Document API client for EstateFlow.
 *
 * AI-powered document generation and template management.
 */

import { buildApiUrl, getDefaultHeaders, API_ENDPOINTS } from "../api-config";
import { getAuthTokenSync } from "../auth";

/**
 * Get authentication token from localStorage or session storage.
 * TODO: Replace with actual auth implementation
 */

// ==================== Types ====================

export type DocumentType =
  | "lease_agreement"
  | "purchase_agreement"
  | "rental_application"
  | "property_disclosure"
  | "offer_letter"
  | "counter_offer"
  | "addendum"
  | "tenant_screening"
  | "eviction_notice"
  | "lease_renewal"
  | "move_in_checklist"
  | "move_out_checklist"
  | "maintenance_request"
  | "rent_receipt"
  | "security_deposit_return";

export type DocumentStatus =
  | "draft"
  | "pending_review"
  | "ready"
  | "sent"
  | "signed"
  | "expired"
  | "cancelled";

export type SignatureStatus = "pending" | "signed" | "declined";

export interface Party {
  role: string;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  signature_required: boolean;
  signature_status: SignatureStatus;
  signed_at?: string;
  signature_data?: string;
}

export interface DocumentVariable {
  key: string;
  label: string;
  description?: string;
  variable_type: string;
  required: boolean;
  default_value?: any;
  options?: string[];
  validation_regex?: string;
}

export interface DocumentTemplate {
  id: string;
  organization_id: string;
  name: string;
  document_type: DocumentType;
  description?: string;
  template_content: string;
  variables: DocumentVariable[];
  language: string;
  jurisdiction?: string;
  version: string;
  is_active: boolean;
  is_default: boolean;
  ai_generated: boolean;
  ai_prompt?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface Document {
  id: string;
  organization_id: string;
  template_id: string;
  document_type: DocumentType;
  title: string;
  description?: string;
  parties: Party[];
  variables: Record<string, any>;
  rendered_content?: string;
  pdf_url?: string;
  docx_url?: string;
  status: DocumentStatus;
  property_id?: string;
  contact_id?: string;
  booking_id?: string;
  signature_request_id?: string;
  all_signed: boolean;
  fully_executed_at?: string;
  expires_at?: string;
  version: number;
  revision_history: any[];
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface DocumentCreateRequest {
  template_id: string;
  title: string;
  description?: string;
  variables: Record<string, any>;
  parties: Party[];
  property_id?: string;
  contact_id?: string;
  booking_id?: string;
  generate_pdf?: boolean;
  generate_docx?: boolean;
  send_for_signature?: boolean;
}

export interface DocumentUpdateRequest {
  title?: string;
  description?: string;
  variables?: Record<string, any>;
  parties?: Party[];
  status?: DocumentStatus;
}

export interface TemplateGenerateRequest {
  document_type: DocumentType;
  jurisdiction?: string;
  language?: string;
  custom_clauses?: string[];
  exclude_clauses?: string[];
  additional_instructions?: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  limit: number;
  offset: number;
}

export interface TemplateListResponse {
  templates: DocumentTemplate[];
  total: number;
  limit: number;
  offset: number;
}

export interface DocumentFilters {
  document_type?: DocumentType;
  status?: DocumentStatus;
  property_id?: string;
  contact_id?: string;
  limit?: number;
  offset?: number;
}

export interface TemplateFilters {
  document_type?: DocumentType;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}

// ==================== Document API Functions ====================

/**
 * Create a new document from template.
 *
 * @param request - Document creation request
 * @returns Created document
 */
export async function createDocument(request: DocumentCreateRequest): Promise<Document> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.documents.create), {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create document");
  }

  return response.json();
}

/**
 * List documents with optional filters.
 *
 * @param filters - Optional filters
 * @returns List of documents
 */
export async function listDocuments(filters?: DocumentFilters): Promise<DocumentListResponse> {
  const token = getAuthTokenSync();
  const params = new URLSearchParams();

  if (filters?.document_type) params.append("document_type", filters.document_type);
  if (filters?.status) params.append("status", filters.status);
  if (filters?.property_id) params.append("property_id", filters.property_id);
  if (filters?.contact_id) params.append("contact_id", filters.contact_id);
  if (filters?.limit) params.append("limit", String(filters.limit));
  if (filters?.offset) params.append("offset", String(filters.offset));

  const url = `${buildApiUrl(API_ENDPOINTS.documents.list)}?${params.toString()}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch documents");
  }

  return response.json();
}

/**
 * Get document by ID.
 *
 * @param documentId - Document ID
 * @returns Document details
 */
export async function getDocument(documentId: string): Promise<Document> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.documents.get(documentId)), {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch document");
  }

  return response.json();
}

/**
 * Update document.
 *
 * @param documentId - Document ID
 * @param updates - Updates to apply
 * @returns Updated document
 */
export async function updateDocument(
  documentId: string,
  updates: DocumentUpdateRequest
): Promise<Document> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.documents.update(documentId)), {
    method: "PUT",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update document");
  }

  return response.json();
}

/**
 * Delete document.
 *
 * @param documentId - Document ID
 * @returns Success message
 */
export async function deleteDocument(documentId: string): Promise<{ message: string }> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.documents.delete(documentId)), {
    method: "DELETE",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to delete document");
  }

  return response.json();
}

// ==================== Template API Functions ====================

/**
 * Create a new document template.
 *
 * @param template - Template data
 * @returns Created template
 */
export async function createTemplate(template: Partial<DocumentTemplate>): Promise<DocumentTemplate> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.templates.create), {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(template),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create template");
  }

  return response.json();
}

/**
 * List templates with optional filters.
 *
 * @param filters - Optional filters
 * @returns List of templates
 */
export async function listTemplates(filters?: TemplateFilters): Promise<TemplateListResponse> {
  const token = getAuthTokenSync();
  const params = new URLSearchParams();

  if (filters?.document_type) params.append("document_type", filters.document_type);
  if (filters?.is_active !== undefined) params.append("is_active", String(filters.is_active));
  if (filters?.limit) params.append("limit", String(filters.limit));
  if (filters?.offset) params.append("offset", String(filters.offset));

  const url = `${buildApiUrl(API_ENDPOINTS.templates.list)}?${params.toString()}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch templates");
  }

  return response.json();
}

/**
 * Get template by ID.
 *
 * @param templateId - Template ID
 * @returns Template details
 */
export async function getTemplate(templateId: string): Promise<DocumentTemplate> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.templates.get(templateId)), {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch template");
  }

  return response.json();
}

/**
 * Update template.
 *
 * @param templateId - Template ID
 * @param updates - Updates to apply
 * @returns Updated template
 */
export async function updateTemplate(
  templateId: string,
  updates: Partial<DocumentTemplate>
): Promise<DocumentTemplate> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.templates.update(templateId)), {
    method: "PUT",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update template");
  }

  return response.json();
}

/**
 * Delete template.
 *
 * @param templateId - Template ID
 * @returns Success message
 */
export async function deleteTemplate(templateId: string): Promise<{ message: string }> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.templates.delete(templateId)), {
    method: "DELETE",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to delete template");
  }

  return response.json();
}

/**
 * Generate a new template using AI.
 *
 * @param request - Template generation request
 * @returns Generated template
 */
export async function generateTemplateWithAI(request: TemplateGenerateRequest): Promise<DocumentTemplate> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.templates.generateAi), {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to generate template");
  }

  return response.json();
}

// ==================== Document Actions ====================

/**
 * Send document for e-signature.
 *
 * @param documentId - Document ID
 * @returns Response
 */
export async function sendForSignature(documentId: string): Promise<any> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.documents.sendForSignature(documentId)), {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to send for signature");
  }

  return response.json();
}

/**
 * Download document as PDF.
 *
 * @param documentId - Document ID
 * @returns Blob
 */
export async function downloadPdf(documentId: string): Promise<Blob> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.documents.downloadPdf(documentId)), {
    method: "GET",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to download PDF");
  }

  return response.blob();
}

/**
 * Download document as DOCX.
 *
 * @param documentId - Document ID
 * @returns Blob
 */
export async function downloadDocx(documentId: string): Promise<Blob> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.documents.downloadDocx(documentId)), {
    method: "GET",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to download DOCX");
  }

  return response.blob();
}
