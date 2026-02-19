/**
 * React Query hooks for document management.
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult, UseMutationResult } from "@tanstack/react-query";
import {
  listDocuments,
  getDocument,
  createDocument,
  updateDocument,
  deleteDocument,
  listTemplates,
  getTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  generateTemplateWithAI,
  sendForSignature,
  downloadPdf,
  downloadDocx,
  type Document,
  type DocumentCreateRequest,
  type DocumentUpdateRequest,
  type DocumentListResponse,
  type DocumentFilters,
  type DocumentTemplate,
  type TemplateGenerateRequest,
  type TemplateListResponse,
  type TemplateFilters,
} from "../lib/api/document-api";

// ==================== Document Query Hooks ====================

/**
 * Hook to list documents with optional filters.
 *
 * @param filters - Optional filters
 * @returns Query result with documents
 */
export function useDocuments(filters?: DocumentFilters): UseQueryResult<DocumentListResponse, Error> {
  return useQuery({
    queryKey: ["documents", filters],
    queryFn: () => listDocuments(filters),
  });
}

/**
 * Hook to get a single document by ID.
 *
 * @param documentId - Document ID
 * @param enabled - Whether the query should execute
 * @returns Query result with document details
 */
export function useDocument(documentId: string, enabled: boolean = true): UseQueryResult<Document, Error> {
  return useQuery({
    queryKey: ["document", documentId],
    queryFn: () => getDocument(documentId),
    enabled: enabled && !!documentId,
  });
}

// ==================== Document Mutation Hooks ====================

/**
 * Hook to create a new document from template.
 *
 * @returns Mutation for creating document
 */
export function useCreateDocument(): UseMutationResult<Document, Error, DocumentCreateRequest> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

/**
 * Hook to update a document.
 *
 * @returns Mutation for updating document
 */
export function useUpdateDocument(): UseMutationResult<
  Document,
  Error,
  { documentId: string; updates: DocumentUpdateRequest }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ documentId, updates }) => updateDocument(documentId, updates),
    onSuccess: (data) => {
      queryClient.setQueryData(["document", data.id], data);
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

/**
 * Hook to delete a document.
 *
 * @returns Mutation for deleting document
 */
export function useDeleteDocument(): UseMutationResult<{ message: string }, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

// ==================== Template Query Hooks ====================

/**
 * Hook to list templates with optional filters.
 *
 * @param filters - Optional filters
 * @returns Query result with templates
 */
export function useTemplates(filters?: TemplateFilters): UseQueryResult<TemplateListResponse, Error> {
  return useQuery({
    queryKey: ["templates", filters],
    queryFn: () => listTemplates(filters),
  });
}

/**
 * Hook to get a single template by ID.
 *
 * @param templateId - Template ID
 * @param enabled - Whether the query should execute
 * @returns Query result with template details
 */
export function useTemplate(
  templateId: string,
  enabled: boolean = true
): UseQueryResult<DocumentTemplate, Error> {
  return useQuery({
    queryKey: ["template", templateId],
    queryFn: () => getTemplate(templateId),
    enabled: enabled && !!templateId,
  });
}

// ==================== Template Mutation Hooks ====================

/**
 * Hook to create a new template.
 *
 * @returns Mutation for creating template
 */
export function useCreateTemplate(): UseMutationResult<
  DocumentTemplate,
  Error,
  Partial<DocumentTemplate>
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

/**
 * Hook to update a template.
 *
 * @returns Mutation for updating template
 */
export function useUpdateTemplate(): UseMutationResult<
  DocumentTemplate,
  Error,
  { templateId: string; updates: Partial<DocumentTemplate> }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ templateId, updates }) => updateTemplate(templateId, updates),
    onSuccess: (data) => {
      queryClient.setQueryData(["template", data.id], data);
      queryClient.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

/**
 * Hook to delete a template.
 *
 * @returns Mutation for deleting template
 */
export function useDeleteTemplate(): UseMutationResult<{ message: string }, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

/**
 * Hook to generate a template using AI.
 *
 * @returns Mutation for AI template generation
 */
export function useGenerateTemplate(): UseMutationResult<
  DocumentTemplate,
  Error,
  TemplateGenerateRequest
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: generateTemplateWithAI,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

// ==================== Document Action Hooks ====================

/**
 * Hook to send a document for e-signature.
 *
 * @returns Mutation for sending document for signature
 */
export function useSendForSignature(): UseMutationResult<any, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: sendForSignature,
    onSuccess: (_, documentId) => {
      queryClient.invalidateQueries({ queryKey: ["document", documentId] });
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

/**
 * Hook to download a document as PDF.
 *
 * @returns Mutation for downloading PDF
 */
export function useDownloadPdf(): UseMutationResult<Blob, Error, string> {
  return useMutation({
    mutationFn: downloadPdf,
    onSuccess: (blob, documentId) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `document-${documentId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}

/**
 * Hook to download a document as DOCX.
 *
 * @returns Mutation for downloading DOCX
 */
export function useDownloadDocx(): UseMutationResult<Blob, Error, string> {
  return useMutation({
    mutationFn: downloadDocx,
    onSuccess: (blob, documentId) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `document-${documentId}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}
