/**
 * API service for HERMES Marketing Command Center
 * Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Leads API
export const leadsApi = {
  getAll: (params) => api.get('/api/leads', { params }),
  getById: (id) => api.get(`/api/leads/${id}`),
  create: (data) => api.post('/api/leads', data),
  update: (id, data) => api.put(`/api/leads/${id}`, data),
  delete: (id) => api.delete(`/api/leads/${id}`),
};

// Social Media API
export const socialApi = {
  getPosts: (params) => api.get('/api/social/posts', { params }),
  getPost: (id) => api.get(`/api/social/posts/${id}`),
  createPost: (data) => api.post('/api/social/posts', data),
  schedulePost: (id, scheduled_time) => api.post(`/api/social/posts/${id}/schedule`, { scheduled_time }),
  publishPost: (id) => api.post(`/api/social/posts/${id}/publish`),
  generateContent: (data) => api.post('/api/social/generate', data),
};

// Marketing Analytics API
export const analyticsApi = {
  getMetrics: () => api.get('/api/marketing/analytics/metrics'),
  getFunnel: (days) => api.get('/api/marketing/analytics/funnel', { params: { days } }),
  getPipeline: () => api.get('/api/marketing/analytics/pipeline'),
  getSocial: (days) => api.get('/api/marketing/analytics/social', { params: { days } }),
  getROI: () => api.get('/api/marketing/analytics/roi'),
};

// Webhooks API
export const webhooksApi = {
  getEvents: (params) => api.get('/api/webhooks/events', { params }),
  getEvent: (id) => api.get(`/api/webhooks/events/${id}`),
  trigger: (webhook_url, payload) => api.post('/api/webhooks/trigger', { webhook_url, payload }),
};

export default api;
