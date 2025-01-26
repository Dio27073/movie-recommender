import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Star, ArrowLeft, Play, Pause } from 'lucide-react';
import { Movie } from '../../features/movies/types';
import apiService from '../../services/api';


interface VideoPlayerProps {
  url: string;
  title: string;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ url, title }) => {
  const [error, setError] = useState<string | null>(null);

  const getYouTubeEmbedUrl = (url: string): string | null => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return match && match[2].length === 11 ? match[2] : null;
  };

  const videoId = getYouTubeEmbedUrl(url);

  if (!videoId) {
    return (
      <div className="w-full bg-gray-900 rounded-lg p-4">
        <p className="text-red-400 text-center">Invalid video URL</p>
      </div>
    );
  }

  return (
    <div className="w-full bg-gray-900 rounded-lg overflow-hidden">
      <div className="relative w-full" style={{ paddingBottom: '56.25%' }}> {/* 16:9 aspect ratio */}
        <iframe
          src={`https://www.youtube.com/embed/${videoId}`}
          title={`${title} trailer`}
          className="absolute top-0 left-0 w-full h-full"
          style={{ border: 'none' }}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          onError={() => setError('Failed to load video')}
        />
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-90">
            <p className="text-red-400 text-center p-4">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export const MovieDetails: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const movie = location.state?.movie as Movie;
  const [loading, setLoading] = useState(!movie);
  const [error, setError] = useState<string | null>(null);
  const [movieData, setMovieData] = useState<Movie | null>(movie || null);

  useEffect(() => {
    if (!movie) {
      const fetchMovie = async () => {
        try {
          setLoading(true);
          const id = location.pathname.split('/').pop();
          const response = await apiService.getMovie(id!);
          setMovieData(response);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to fetch movie details');
        } finally {
          setLoading(false);
        }
      };

      fetchMovie();
    }
  }, [movie, location.pathname]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-50 text-red-800 p-4 rounded-lg">
          Error: {error}
        </div>
        <button 
          onClick={() => navigate(-1)}
          className="mt-4 inline-flex items-center text-blue-600 hover:text-blue-800"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </button>
      </div>
    );
  }
  
  if (!movieData) return null;

  return (
    <div className="p-6 bg-gray-100 dark:bg-dark-primary min-h-screen">
      <button 
        onClick={() => navigate(-1)}
        className="mb-6 inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Movies
      </button>
      
      <div className="bg-white dark:bg-dark-secondary rounded-xl shadow-lg overflow-hidden">
        <div className="md:flex">
          <div className="md:flex-shrink-0">
            <img
              src={movieData.imageUrl || '/api/placeholder/400/600'}
              alt={movieData.title}
              className="h-96 w-full object-cover md:w-96"
            />
          </div>
          
          <div className="p-8">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {movieData.title}
              </h1>
              <div className="flex items-center">
                <Star className="w-6 h-6 text-yellow-400 fill-current" />
                <div className="ml-2">
                  <div className="text-lg font-semibold dark:text-gray-200">
                    {movieData.imdb_rating 
                      ? `${movieData.imdb_rating.toFixed(1)}/10` 
                      : 'N/A'}
                    <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-1">
                      IMDB
                    </span>
                  </div>
                  {movieData.imdb_votes && (
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {new Intl.NumberFormat().format(movieData.imdb_votes)} votes
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Released: {movieData.release_year}
            </p>
            
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              {movieData.description}
            </p>
            
            <div className="mt-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Genres
              </h2>
              <div className="flex flex-wrap gap-2">
                {(Array.isArray(movieData.genres) ? movieData.genres : [movieData.genres]).map((genre) => (
                  <span
                    key={genre}
                    className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm"
                  >
                    {genre}
                  </span>
                ))}
              </div>
            </div>
            
            {movieData.imdb_id && (
              <div className="mt-6">
                <a
                  href={`https://www.imdb.com/title/${movieData.imdb_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-gray-900 rounded-lg transition-colors"
                >
                  View on IMDB
                </a>
              </div>
            )}

            {movieData?.trailer_url && (
              <div className="mt-8">
                <div className="max-w-4xl mx-auto px-4">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
                    Watch Trailer
                  </h2>
                  <VideoPlayer url={movieData.trailer_url} title={movieData.title} />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MovieDetails; // Add this line
