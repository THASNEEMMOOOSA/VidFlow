// frontend/src/components/upload/VideoUploader.tsx
/**
 * Video upload component with drag-and-drop functionality.
 */

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Button, CircularProgress, LinearProgress, Paper, Typography, Alert, TextField } from '@mui/material';
import { CloudUpload, CheckCircle, Error as ErrorIcon } from '@mui/icons-material';
import { videosApi } from '../../services/api/videos';
import { VideoUploadResponse } from '../../types';

interface VideoUploaderProps {
  onUploadSuccess?: (response: VideoUploadResponse) => void;
  onUploadError?: (error: Error) => void;
}

export const VideoUploader: React.FC<VideoUploaderProps> = ({ onUploadSuccess, onUploadError }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      // Validate file size (max 1GB)
      if (file.size > 1073741824) {
        setErrorMessage('File size exceeds 1GB limit');
        return;
      }
      
      // Validate file type
      const allowedTypes = ['video/mp4', 'video/mov', 'video/avi', 'video/mkv', 'video/webm'];
      if (!allowedTypes.includes(file.type)) {
        setErrorMessage('File type not supported. Please upload MP4, MOV, AVI, MKV, or WebM files.');
        return;
      }
      
      setSelectedFile(file);
      setErrorMessage('');
      setUploadStatus('idle');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/mp4': ['.mp4'],
      'video/quicktime': ['.mov'],
      'video/x-msvideo': ['.avi'],
      'video/x-matroska': ['.mkv'],
      'video/webm': ['.webm'],
    },
    maxFiles: 1,
  });

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadStatus('uploading');
    setProgress(0);
    
    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 10, 90));
    }, 500);

    try {
      const response = await videosApi.uploadVideo(selectedFile, title, description);
      clearInterval(progressInterval);
      setProgress(100);
      setUploadStatus('success');
      setSelectedFile(null);
      setTitle('');
      setDescription('');
      onUploadSuccess?.(response);
    } catch (error) {
      clearInterval(progressInterval);
      setUploadStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Upload failed');
      onUploadError?.(error as Error);
    } finally {
      setUploading(false);
    }
  };

  const handleCancel = () => {
    setSelectedFile(null);
    setTitle('');
    setDescription('');
    setUploadStatus('idle');
    setErrorMessage('');
    setProgress(0);
  };

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h5" gutterBottom>
        Upload Video
      </Typography>
      
      {errorMessage && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setErrorMessage('')}>
          {errorMessage}
        </Alert>
      )}
      
      {uploadStatus === 'success' && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Video uploaded successfully! Processing has started. You will receive a notification when it's ready.
        </Alert>
      )}
      
      {!selectedFile ? (
        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'grey.400',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            cursor: 'pointer',
            bgcolor: isDragActive ? 'action.hover' : 'background.paper',
            transition: 'all 0.2s',
            '&:hover': {
              borderColor: 'primary.main',
              bgcolor: 'action.hover',
            },
          }}
        >
          <input {...getInputProps()} />
          <CloudUpload sx={{ fontSize: 48, color: 'grey.500', mb: 2 }} />
          <Typography variant="body1" gutterBottom>
            {isDragActive
              ? 'Drop the video file here'
              : 'Drag and drop a video file here, or click to select'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Supported formats: MP4, MOV, AVI, MKV, WebM (Max size: 1GB)
          </Typography>
        </Box>
      ) : (
        <Box>
          <Typography variant="subtitle1" gutterBottom>
            Selected File: {selectedFile.name}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
          </Typography>
          
          <TextField
            fullWidth
            label="Title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            margin="normal"
          />
          
          <TextField
            fullWidth
            label="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            margin="normal"
            multiline
            rows={3}
          />
          
          {uploadStatus === 'uploading' && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress variant="determinate" value={progress} />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Uploading... {progress}%
              </Typography>
            </Box>
          )}
          
          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              onClick={handleUpload}
              disabled={uploading}
              startIcon={uploading ? <CircularProgress size={20} /> : <CloudUpload />}
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </Button>
            <Button
              variant="outlined"
              onClick={handleCancel}
              disabled={uploading}
            >
              Cancel
            </Button>
          </Box>
        </Box>
      )}
    </Paper>
  );
};