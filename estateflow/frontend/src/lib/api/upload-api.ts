/**
 * Upload API Client
 *
 * Handles file uploads (images, videos) to the backend storage.
 */

import { API_BASE_URL, getSelectedOrganizationId } from "../api-config";
import { getAuthTokenSync } from "../auth";

export interface UploadResponse {
  file_id: string;
  filename: string;
  url: string;
  path: string;
  size: number;
  mime_type: string;
  uploaded_at: string;
}

export interface GridFSUploadResponse {
  image_id: string;
  file_id: string;
  thumbnail_file_id: string;
  filename: string;
  url: string;
  thumbnail_url: string;
  size: number;
  width: number;
  height: number;
  mime_type: string;
  uploaded_at: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

/**
 * Upload a single image file
 */
export async function uploadImage(
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const token = getAuthTokenSync();

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          onProgress({
            loaded: e.loaded,
            total: e.total,
            percentage: Math.round((e.loaded / e.total) * 100),
          });
        }
      });
    }

    // Handle completion
    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (error) {
          reject(new Error("Invalid response format"));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || `Upload failed: ${xhr.statusText}`));
        } catch {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      }
    });

    // Handle errors
    xhr.addEventListener("error", () => {
      reject(new Error("Network error during upload"));
    });

    xhr.addEventListener("abort", () => {
      reject(new Error("Upload cancelled"));
    });

    // Send request
    xhr.open("POST", `${API_BASE_URL}/api/v1/upload/images`);
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    const orgId = getSelectedOrganizationId();
    if (orgId) {
      xhr.setRequestHeader("X-Organization-ID", orgId);
    }

    xhr.send(formData);
  });
}

/**
 * Upload multiple images in batch using GridFS
 */
export async function uploadImageBatch(
  files: File[],
  propertyId?: string,
  onProgress?: (fileIndex: number, progress: UploadProgress) => void
): Promise<GridFSUploadResponse[]> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  if (propertyId) {
    formData.append("property_id", propertyId);
  }

  const token = getAuthTokenSync();
  const orgId = getSelectedOrganizationId();

  const response = await fetch(`${API_BASE_URL}/api/v1/upload/images/batch/gridfs`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
      ...(orgId && { "X-Organization-ID": orgId }),
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Batch upload failed");
  }

  return response.json();
}

/**
 * Upload a video file
 */
export async function uploadVideo(
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const token = getAuthTokenSync();

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          onProgress({
            loaded: e.loaded,
            total: e.total,
            percentage: Math.round((e.loaded / e.total) * 100),
          });
        }
      });
    }

    // Handle completion
    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (error) {
          reject(new Error("Invalid response format"));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || `Upload failed: ${xhr.statusText}`));
        } catch {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      }
    });

    // Handle errors
    xhr.addEventListener("error", () => {
      reject(new Error("Network error during upload"));
    });

    xhr.addEventListener("abort", () => {
      reject(new Error("Upload cancelled"));
    });

    // Send request
    xhr.open("POST", `${API_BASE_URL}/api/v1/upload/videos`);
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    const orgId = getSelectedOrganizationId();
    if (orgId) {
      xhr.setRequestHeader("X-Organization-ID", orgId);
    }

    xhr.send(formData);
  });
}

/**
 * Get file URL from storage path
 */
export function getFileUrl(path: string): string {
  return `${API_BASE_URL}/api/v1/storage/${path}`;
}

/**
 * Validate image file
 */
export function validateImageFile(file: File): { valid: boolean; error?: string } {
  const maxSize = 10 * 1024 * 1024; // 10 MB
  const allowedTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"];

  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: "Invalid file type. Allowed: JPEG, PNG, GIF, WebP",
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File too large. Maximum size: ${maxSize / 1024 / 1024} MB`,
    };
  }

  return { valid: true };
}

/**
 * Validate video file
 */
export function validateVideoFile(file: File): { valid: boolean; error?: string } {
  const maxSize = 100 * 1024 * 1024; // 100 MB
  const allowedTypes = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"];

  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: "Invalid file type. Allowed: MP4, MOV, AVI, WebM",
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File too large. Maximum size: ${maxSize / 1024 / 1024} MB`,
    };
  }

  return { valid: true };
}

// ===============================================================================
// GridFS Upload Functions (MongoDB-based storage)
// ===============================================================================

/**
 * Upload a single image to GridFS with thumbnail generation
 */
export async function uploadImageGridFS(
  file: File,
  propertyId?: string,
  isFeatured?: boolean,
  onProgress?: (progress: UploadProgress) => void
): Promise<GridFSUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (propertyId) {
    formData.append("property_id", propertyId);
  }
  if (isFeatured !== undefined) {
    formData.append("is_featured", String(isFeatured));
  }

  const token = getAuthTokenSync();

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          onProgress({
            loaded: e.loaded,
            total: e.total,
            percentage: Math.round((e.loaded / e.total) * 100),
          });
        }
      });
    }

    // Handle completion
    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (error) {
          reject(new Error("Invalid response format"));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || `Upload failed: ${xhr.statusText}`));
        } catch {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      }
    });

    // Handle errors
    xhr.addEventListener("error", () => {
      reject(new Error("Network error during upload"));
    });

    xhr.addEventListener("abort", () => {
      reject(new Error("Upload cancelled"));
    });

    // Send request
    xhr.open("POST", `${API_BASE_URL}/api/v1/upload/images/gridfs`);
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    const orgId = getSelectedOrganizationId();
    if (orgId) {
      xhr.setRequestHeader("X-Organization-ID", orgId);
    }

    xhr.send(formData);
  });
}

/**
 * Upload multiple images to GridFS in batch
 */
export async function uploadImageBatchGridFS(
  files: File[],
  propertyId?: string,
  onProgress?: (fileIndex: number, progress: UploadProgress) => void
): Promise<GridFSUploadResponse[]> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  if (propertyId) {
    formData.append("property_id", propertyId);
  }

  const token = getAuthTokenSync();
  const orgId = getSelectedOrganizationId();

  const response = await fetch(`${API_BASE_URL}/api/v1/upload/images/batch/gridfs`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
      ...(orgId && { "X-Organization-ID": orgId }),
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Batch upload failed");
  }

  return response.json();
}
