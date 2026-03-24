// frontend/src/components/video/VideoList.tsx
/**
 * Component for displaying a list of videos.
 */

import React, { useState, useEffect } from 'react';
import { Grid, Card, CardMedia, CardContent, Typography, CardActions, Button, Chip, Box, CircularProgress, TextField, MenuItem, Pagination } from '@mui/material';
import { PlayArrow, Delete, Schedule, CheckCircle, Error as ErrorIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { videosApi } from '../../services/api/videos';
import { Video } from '../../types';
import { useWebSocket } from '../../hooks/useWebSocket';
import { formatDistanceToNow } from 'date-fns';

export const VideoList: React.FC = () => {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const { subscribeToVideo, unsubscribeFromVideo } = useWebSocket({
    onProcessingUpdate: (update) => {
      // Update video status when processing update is received
      setVideos(prev =>
        prev.map(video =>
          video.id === update.video_id
            ? { ...video, status: update.status as any }
            : video
        )
      );
    },
  });

  const loadVideos = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await videosApi.getVideos({
        skip: (page - 1) * 12,
        limit: 12,
        status: statusFilter || undefined,
        search: searchQuery || undefined,
      });
      setVideos(data);
      setTotalPages(Math.ceil(data.length / 12));
      
      // Subscribe to updates for processing videos
      data.forEach(video => {
        if (video.status === 'processing') {
          subscribeToVideo(video.id);
        }
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to load videos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVideos();
    
    // Cleanup subscriptions
    return () => {
      videos.forEach(video => {
        if (video.status === 'processing') {
          unsubscribeFromVideo(video.id);
        }
      });
    };
  }, [page, statusFilter, searchQuery]);

  const handleDelete = async (videoId: number) => {
    if (window.confirm('Are you sure you want to delete this video?')) {
      try {
        await videosApi.deleteVideo(videoId);
        setVideos(prev => prev.filter(v => v.id !== videoId));
      } catch (error) {
        console.error('Failed to delete video:', error);
      }
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle sx={{ fontSize: 16 }} />;
      case 'processing':
        return <CircularProgress size={16} />;
      case 'failed':
        return <ErrorIcon sx={{ fontSize: 16 }} />;
      default:
        return <Schedule sx={{ fontSize: 16 }} />;
    }
  };

  const getStatusColor = (status: string): 'default' | 'success' | 'warning' | 'error' => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading && videos.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          label="Search"
          variant="outlined"
          size="small"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          sx={{ flexGrow: 1 }}
        />
        <TextField
          select
          label="Status"
          variant="outlined"
          size="small"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="pending">Pending</MenuItem>
          <MenuItem value="processing">Processing</MenuItem>
          <MenuItem value="completed">Completed</MenuItem>
          <MenuItem value="failed">Failed</MenuItem>
        </TextField>
      </Box>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          Error: {error}
        </Typography>
      )}

      {videos.length === 0 ? (
        <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 8 }}>
          No videos found. Upload your first video to get started!
        </Typography>
      ) : (
        <Grid container spacing={3}>
          {videos.map((video) => (
            <Grid item xs={12} sm={6} md={4} key={video.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardMedia
                  component="img"
                  height="180"
                  image={video.thumbnail_url || '/placeholder-video.jpg'}
                  alt={video.title}
                  sx={{ objectFit: 'cover' }}
                />
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography gutterBottom variant="h6" component="h2" noWrap>
                    {video.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {video.description || 'No description'}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Chip
                      icon={getStatusIcon(video.status)}
                      label={video.status}
                      size="small"
                      color={getStatusColor(video.status)}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {formatDistanceToNow(new Date(video.created_at), { addSuffix: true })}
                    </Typography>
                  </Box>
                  {video.duration && (
                    <Typography variant="caption" color="text.secondary">
                      Duration: {Math.floor(video.duration / 60)}:{(video.duration % 60).toString().padStart(2, '0')}
                    </Typography>
                  )}
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<PlayArrow />}
                    onClick={() => navigate(`/videos/${video.id}`)}
                    disabled={video.status !== 'completed'}
                  >
                    {video.status === 'completed' ? 'Watch' : 'Processing'}
                  </Button>
                  <Button
                    size="small"
                    color="error"
                    startIcon={<Delete />}
                    onClick={() => handleDelete(video.id)}
                  >
                    Delete
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}
    </Box>
  );
};