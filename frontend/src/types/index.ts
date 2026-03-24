// frontend/src/types/index.ts
/**
 * TypeScript type definitions for the frontend application.
 */

export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface Video {
  id: number;
  title: string;
  description: string;
  filename: string;
  file_size: number;
  duration: number | null;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  thumbnail_url: string | null;
  original_url: string | null;
  processed_urls: Record<string, string> | null;
  metadata: Record<string, any> | null;
  user_id: number;
  created_at: string;
  updated_at: string | null;
}

export interface VideoUploadResponse {
  video_id: number;
  status: Video['status'];
  message: string;
  upload_url: string | null;
}

export interface VideoProcessingStatus {
  video_id: number;
  status: Video['status'];
  progress: number | null;
  message: string | null;
  error: string | null;
}

export interface VideoStreamURL {
  video_id: number;
  title: string;
  thumbnail_url: string | null;
  stream_urls: Record<string, string>;
  hls_url: string | null;
  dash_url: string | null;
}

export interface ApiError {
  error: {
    code: number;
    message: string;
    details?: any;
    path?: string;
  };
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}