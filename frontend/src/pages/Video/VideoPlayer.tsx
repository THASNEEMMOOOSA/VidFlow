// frontend/src/pages/Video/VideoPlayer.tsx
/**
 * Video player page with streaming capabilities.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Paper, Typography, CircularProgress, Alert, Button, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import ReactPlayer from 'react-player';
import { videosApi } from '../../services/api/videos';
import { Video, VideoStreamURL } from '../../types';

export const VideoPlayer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [video, setVideo] = useState<Video | null>(null);
  const [streamData, setStreamData] = useState<VideoStreamURL | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedQuality, setSelectedQuality] = useState<string>('720p');

  useEffect(() => {
    loadVideo();
  }, [id]);

  const loadVideo = async () => {
    if (!id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const videoData = await videosApi.getVideo(parseInt(id));
      setVideo(videoData);
      
      if (videoData.status === 'completed') {
        const streamUrls = await videosApi.getStreamingUrls(parseInt(id));
        setStreamData(streamUrls);
        
        // Set default quality
        const qualities = Object.keys(streamUrls.stream_urls);
        if (qualities.length > 0) {
          setSelectedQuality(qualities[0]);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load video');
    } finally {
      setLoading(false);
    }
  };

  const getVideoUrl = () => {
    if (!streamData) return '';
    return streamData.stream_urls[selectedQuality] || Object.values(streamData.stream_urls)[0];
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!video) {
    return (
      <Alert severity="warning" sx={{ m: 2 }}>
        Video not found
      </Alert>
    );
  }

  if (video.status !== 'completed') {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>
          Video is still processing
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Your video is being processed. This may take a few minutes.
        </Typography>
        <Button variant="contained" onClick={() => navigate('/videos')}>
          Back to My Videos
        </Button>
      </Paper>
    );
  }

  return (
    <Box>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {video.title}
        </Typography>
        {video.description && (
          <Typography variant="body1" color="text.secondary" paragraph>
            {video.description}
          </Typography>
        )}
      </Paper>
      
      <Paper elevation={3} sx={{ overflow: 'hidden' }}>
        <Box sx={{ position: 'relative', paddingTop: '56.25%' }}> {/* 16:9 aspect ratio */}
          <ReactPlayer
            url={getVideoUrl()}
            width="100%"
            height="100%"
            controls
            playing
            config={{
              file: {
                attributes: {
                  controlsList: 'nodownload',
                },
              },
            }}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
            }}
          />
        </Box>
        
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            {video.duration && `Duration: ${Math.floor(video.duration / 60)}:${(video.duration % 60).toString().padStart(2, '0')}`}
          </Typography>
          
          {streamData && Object.keys(streamData.stream_urls).length > 1 && (
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Quality</InputLabel>
              <Select
                value={selectedQuality}
                label="Quality"
                onChange={(e) => setSelectedQuality(e.target.value)}
              >
                {Object.keys(streamData.stream_urls).map((quality) => (
                  <MenuItem key={quality} value={quality}>
                    {quality}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </Box>
      </Paper>
    </Box>
  );
};