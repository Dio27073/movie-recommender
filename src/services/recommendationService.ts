import api from './api';
import { Movie, RecommendationResponse } from '../features/movies/types';

export interface RecommendationFilters {
  strategy?: 'hybrid' | 'content' | 'collaborative';
  excludeWatched?: boolean;
  minRating?: number;
  genres?: string[];
  page?: number;
  per_page?: number;
}

export const recommendationService = {
  // Get personalized recommendations
  getRecommendations: async (filters: RecommendationFilters = {}): Promise<RecommendationResponse> => {
    const queryParams = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        if (Array.isArray(value)) {
          value.forEach(v => queryParams.append(key, v.toString()));
        } else {
          queryParams.append(key, value.toString());
        }
      }
    });

    return api.getRecommendations(filters);
  },

  // Get recommendations based on a specific movie
  getSimilarMovies: async (movieId: number): Promise<Movie[]> => {
    return api.getSimilarMovies(movieId);
  },

  // Get recommendations based on recently watched
  getRecentlyWatchedRecommendations: async (): Promise<Movie[]> => {
    return api.getRecentlyWatchedRecommendations();
  },

  // Record a movie view
  recordMovieView: async (movieId: number, data: {
    completed: boolean;
    watch_duration?: number;
  }) => {
    return api.recordMovieView(movieId, data);
  },

  // Update user preferences
  updatePreferences: async (preferences: {
    favorite_genres?: string[];
    preferred_languages?: string[];
    content_preferences?: Record<string, any>;
  }) => {
    return api.updateRecommendationPreferences(preferences);
  },

  // Get trending recommendations
  getTrendingRecommendations: async (): Promise<Movie[]> => {
    return api.getTrendingRecommendations();
  },

  // Get recommendations by genre
  getGenreRecommendations: async (genre: string): Promise<Movie[]> => {
    return api.getGenreRecommendations(genre);
  },

  // Get view history
  getViewingHistory: async () => {
    return api.getViewingHistory();
  },

  // Get user preferences
  getUserPreferences: async () => {
    return api.getUserPreferences();
  }
};