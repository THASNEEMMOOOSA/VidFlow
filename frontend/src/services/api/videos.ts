// frontend/src/services/api/videos.ts
/**
 * Video API service.
 */

import apiClient from './client';
import { Video, VideoUploadResponse, VideoStreamURL, VideoProcessingStatus } from '../../types';

export const videosApi = {
  /**
   * Upload a video
   */
  async uploadVideo(file: File, title?: string, description?: string): Promise<VideoUploadResponse> {
    const data: Record<string, string> = {};
    if (title) data.title = title;
    if (description) data.description = description;
    
    return apiClient.upload<VideoUploadResponse>('/upload/video', file, data);
  },

  /**
   * Get all videos for current user
   */
  async getVideos(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    search?: string;
  }): Promise<Video[]> {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);
    if (params?.search) queryParams.append('search', params.search);
    
    const url = `/videos/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get<Video[]>(url);
  },

  /**
   * Get a single video by ID
   */
  async getVideo(videoId: number): Promise<Video> {
    return apiClient.get<Video>(`/videos/${videoId}`);
  },

  /**
   * Update video metadata
   */
  async updateVideo(videoId: number, data: Partial<Video>): Promise<Video> {
    return apiClient.patch<Video>(`/videos/${videoId}`, data);
  },

  /**
   * Delete a video
   */
  async deleteVideo(videoId: number): Promise<void> {
    await apiClient.delete(`/videos/${videoId}`);
  },

  /**
   * Get streaming URLs for a video
   */
  async getStreamingUrls(videoId: number): Promise<VideoStreamURL> {
    return apiClient.get<VideoStreamURL>(`/videos/${videoId}/stream`);
  },

  /**
   * Upload custom thumbnail
   */
  async uploadThumbnail(videoId: number, file: File): Promise<{ thumbnail_url: string }> {
    return apiClient.upload<{ thumbnail_url: string }>(`/upload/thumbnail/${videoId}`, file);
  },
};