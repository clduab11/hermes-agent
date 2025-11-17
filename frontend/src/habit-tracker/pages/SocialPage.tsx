import React, { useEffect, useState } from 'react';
import { Heart, MessageCircle, Share2, Trophy, Flame } from 'lucide-react';
import { useStore } from '../store/useStore';
import { socialApi } from '../services/api';
import toast from 'react-hot-toast';
import { formatDistanceToNow } from 'date-fns';
import type { SocialPost } from '../types';

export const SocialPage: React.FC = () => {
  const { user, socialFeed, setSocialFeed } = useStore();
  const [loading, setLoading] = useState(true);
  const [newPost, setNewPost] = useState('');

  useEffect(() => {
    if (user) {
      loadFeed();
    }
  }, [user]);

  const loadFeed = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const feed = await socialApi.getFeed(user.id);
      setSocialFeed(feed);
    } catch (error: any) {
      toast.error('Failed to load social feed');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePost = async () => {
    if (!user || !newPost.trim()) return;

    try {
      const post = await socialApi.createPost({
        userId: user.id,
        type: 'general',
        content: newPost,
      });
      setSocialFeed([post, ...socialFeed]);
      setNewPost('');
      toast.success('Posted! 🎉');
    } catch (error: any) {
      toast.error('Failed to create post');
      console.error(error);
    }
  };

  const handleLike = async (postId: string) => {
    if (!user) return;

    try {
      await socialApi.likePost(postId, user.id);
      toast.success('Liked! ❤️');
      // Refresh feed
      loadFeed();
    } catch (error: any) {
      console.error(error);
    }
  };

  const getPostIcon = (type: SocialPost['type']) => {
    switch (type) {
      case 'achievement':
        return <Trophy className="text-yellow-500" size={20} />;
      case 'streak':
        return <Flame className="text-orange-500" size={20} />;
      case 'challenge':
        return <Trophy className="text-purple-500" size={20} />;
      case 'milestone':
        return <Trophy className="text-blue-500" size={20} />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading feed...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Social Feed</h1>
          <p className="text-gray-600 mt-1">
            Share your progress and motivate others!
          </p>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Create Post */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
              {user?.displayName?.charAt(0) || 'U'}
            </div>
            <div className="flex-1">
              <textarea
                value={newPost}
                onChange={(e) => setNewPost(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none"
                placeholder="Share your progress or motivate others..."
                rows={3}
              />
              <div className="flex justify-end mt-3">
                <button
                  onClick={handleCreatePost}
                  disabled={!newPost.trim()}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Post
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Feed */}
        <div className="space-y-6">
          {socialFeed.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-xl">
              <div className="text-6xl mb-4">👋</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                No posts yet
              </h2>
              <p className="text-gray-600">
                Be the first to share your progress!
              </p>
            </div>
          ) : (
            socialFeed.map((post: any) => (
              <div key={post.id} className="bg-white rounded-xl shadow-md overflow-hidden">
                {/* Post Header */}
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                      {post.profiles?.display_name?.charAt(0) || 'U'}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">
                          {post.profiles?.display_name || 'User'}
                        </h3>
                        {getPostIcon(post.type)}
                      </div>
                      <p className="text-sm text-gray-500">
                        @{post.profiles?.username || 'user'} •{' '}
                        {formatDistanceToNow(new Date(post.created_at), {
                          addSuffix: true,
                        })}
                      </p>
                    </div>
                  </div>

                  {/* Post Content */}
                  <p className="text-gray-800 mb-4 whitespace-pre-wrap">
                    {post.content}
                  </p>

                  {/* Post Metadata */}
                  {post.metadata && (
                    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-4 mb-4">
                      {post.metadata.streakCount && (
                        <div className="flex items-center gap-2 text-orange-600 font-semibold">
                          <Flame size={20} />
                          <span>{post.metadata.streakCount} day streak!</span>
                        </div>
                      )}
                      {post.metadata.achievementId && (
                        <div className="flex items-center gap-2 text-yellow-600 font-semibold">
                          <Trophy size={20} />
                          <span>Achievement Unlocked!</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-6 pt-4 border-t border-gray-200">
                    <button
                      onClick={() => handleLike(post.id)}
                      className="flex items-center gap-2 text-gray-600 hover:text-red-500 transition"
                    >
                      <Heart size={20} />
                      <span className="text-sm font-medium">
                        {post.likes || 0}
                      </span>
                    </button>
                    <button className="flex items-center gap-2 text-gray-600 hover:text-indigo-500 transition">
                      <MessageCircle size={20} />
                      <span className="text-sm font-medium">
                        {post.comments || 0}
                      </span>
                    </button>
                    <button className="flex items-center gap-2 text-gray-600 hover:text-green-500 transition">
                      <Share2 size={20} />
                      <span className="text-sm font-medium">Share</span>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
