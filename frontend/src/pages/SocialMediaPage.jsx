/**
 * Social Media Management Page
 * Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { socialApi } from '../services/api';

export default function SocialMediaPage() {
  const [showGenerator, setShowGenerator] = useState(false);
  const [generatorData, setGeneratorData] = useState({
    platform: 'linkedin',
    practice_area: 'personal_injury',
    content_type: 'thought_leadership',
  });
  const [generatedContent, setGeneratedContent] = useState('');
  const queryClient = useQueryClient();

  const { data: posts, isLoading } = useQuery({
    queryKey: ['socialPosts'],
    queryFn: async () => {
      const response = await socialApi.getPosts({});
      return response.data;
    },
  });

  const generateMutation = useMutation({
    mutationFn: async (data) => {
      const response = await socialApi.generateContent(data);
      return response.data;
    },
    onSuccess: (data) => {
      setGeneratedContent(data.content);
    },
  });

  const createPostMutation = useMutation({
    mutationFn: async (data) => {
      const response = await socialApi.createPost(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['socialPosts']);
      setShowGenerator(false);
      setGeneratedContent('');
    },
  });

  const handleGenerate = () => {
    generateMutation.mutate(generatorData);
  };

  const handleCreatePost = () => {
    if (!generatedContent) return;
    createPostMutation.mutate({
      platform: generatorData.platform,
      content: generatedContent,
      practice_area: generatorData.practice_area,
    });
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      linkedin: '💼',
      facebook: '👥',
      instagram: '📸',
      twitter: '🐦',
    };
    return icons[platform] || '📱';
  };

  const getStatusBadge = (status) => {
    const colors = {
      draft: 'badge-neutral',
      scheduled: 'badge-info',
      published: 'badge-success',
      failed: 'badge-error',
    };
    return colors[status] || 'badge-neutral';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Social Media Manager</h1>
        <button
          className="btn btn-primary"
          onClick={() => setShowGenerator(!showGenerator)}
        >
          {showGenerator ? 'Cancel' : '✨ Generate Content'}
        </button>
      </div>

      {/* Content Generator */}
      {showGenerator && (
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">AI Content Generator</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Platform</span>
                </label>
                <select
                  className="select select-bordered"
                  value={generatorData.platform}
                  onChange={(e) => setGeneratorData({ ...generatorData, platform: e.target.value })}
                >
                  <option value="linkedin">LinkedIn</option>
                  <option value="facebook">Facebook</option>
                  <option value="instagram">Instagram</option>
                  <option value="twitter">Twitter</option>
                </select>
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">Practice Area</span>
                </label>
                <select
                  className="select select-bordered"
                  value={generatorData.practice_area}
                  onChange={(e) => setGeneratorData({ ...generatorData, practice_area: e.target.value })}
                >
                  <option value="personal_injury">Personal Injury</option>
                  <option value="family_law">Family Law</option>
                  <option value="criminal_defense">Criminal Defense</option>
                  <option value="estate_planning">Estate Planning</option>
                  <option value="business_law">Business Law</option>
                </select>
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">Content Type</span>
                </label>
                <select
                  className="select select-bordered"
                  value={generatorData.content_type}
                  onChange={(e) => setGeneratorData({ ...generatorData, content_type: e.target.value })}
                >
                  <option value="thought_leadership">Thought Leadership</option>
                  <option value="case_study">Case Study</option>
                  <option value="behind_the_scenes">Behind the Scenes</option>
                </select>
              </div>
            </div>

            <div className="mt-4 flex gap-2">
              <button
                className="btn btn-primary"
                onClick={handleGenerate}
                disabled={generateMutation.isPending}
              >
                {generateMutation.isPending ? 'Generating...' : '🤖 Generate Content'}
              </button>
            </div>

            {generatedContent && (
              <div className="mt-4">
                <label className="label">
                  <span className="label-text">Generated Content</span>
                </label>
                <textarea
                  className="textarea textarea-bordered w-full h-32"
                  value={generatedContent}
                  onChange={(e) => setGeneratedContent(e.target.value)}
                />
                <div className="mt-2 flex gap-2">
                  <button
                    className="btn btn-success"
                    onClick={handleCreatePost}
                    disabled={createPostMutation.isPending}
                  >
                    {createPostMutation.isPending ? 'Saving...' : '💾 Save as Draft'}
                  </button>
                  <button
                    className="btn btn-ghost"
                    onClick={handleGenerate}
                  >
                    🔄 Regenerate
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Posts Grid */}
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <span className="loading loading-spinner loading-lg"></span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {posts?.map((post) => (
            <div key={post.id} className="card bg-base-100 shadow-xl">
              <div className="card-body">
                <div className="flex justify-between items-start">
                  <h2 className="card-title">
                    {getPlatformIcon(post.platform)} {post.platform}
                  </h2>
                  <span className={`badge ${getStatusBadge(post.status)}`}>
                    {post.status}
                  </span>
                </div>
                <p className="text-sm line-clamp-3">{post.content}</p>
                <div className="text-xs text-base-content/70 mt-2">
                  {post.practice_area && (
                    <div>📚 {post.practice_area.replace('_', ' ')}</div>
                  )}
                  {post.scheduled_time && (
                    <div>📅 {new Date(post.scheduled_time).toLocaleString()}</div>
                  )}
                </div>
                <div className="card-actions justify-end mt-4">
                  {post.status === 'draft' && (
                    <button className="btn btn-sm btn-primary">Schedule</button>
                  )}
                  {post.status === 'scheduled' && (
                    <button className="btn btn-sm btn-success">Publish Now</button>
                  )}
                  <button className="btn btn-sm btn-ghost">Edit</button>
                </div>
                {post.status === 'published' && (
                  <div className="stats stats-horizontal shadow mt-4">
                    <div className="stat p-2">
                      <div className="stat-title text-xs">Impressions</div>
                      <div className="stat-value text-sm">{post.impressions}</div>
                    </div>
                    <div className="stat p-2">
                      <div className="stat-title text-xs">Engagement</div>
                      <div className="stat-value text-sm">{post.engagements}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
