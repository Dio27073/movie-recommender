import React, { useState, useEffect } from 'react';
import { Star, Clock, Calendar, Award } from 'lucide-react';
import { Modal } from './Modal';
import { LibraryMovie } from '../../features/movies/types';
import api from '../../services/api';

interface LibraryMovieModalProps {
  movie: LibraryMovie | null;
  isOpen: boolean;
  onClose: () => void;
  onRemove: (movieId: number) => Promise<void>;
}

const Badge = ({ children, variant = 'default' }: { children: React.ReactNode; variant?: 'default' | 'blue' | 'accent' }) => {
  const variants = {
    default: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
    blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
    accent: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
  };

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${variants[variant]}`}>
      {children}
    </span>
  );
};

const VideoSection = ({ url, title }: { url: string; title: string }) => {
  return (
    <div className="w-full bg-gray-900 rounded-lg overflow-hidden">
      <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
        <iframe
          src={url}
          title={title}
          className="absolute inset-0 w-full h-full border-none"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
    </div>
  );
};

const normalizeGenres = (genres: string | string[]): string[] => {
  if (Array.isArray(genres)) {
    return genres;
  }
  return genres.split(',').map(g => g.trim());
};

export const LibraryMovieModal = ({
  movie,
  isOpen,
  onClose,
  onRemove
}: LibraryMovieModalProps) => {
  const [, setIsLoading] = useState(false);
  const [fullDetails, setFullDetails] = useState<LibraryMovie | null>(null);

  useEffect(() => {
  const fetchMovieDetails = async () => {
    if (!movie) return;
    
    setIsLoading(true);
    try {
      const response = await api.getMovieDetails(movie.movie_id);
      // Extract the correct movie from the paginated response
      const movieDetails = response.items?.find(item => item.id === movie.movie_id);
      
      if (movieDetails) {
        setFullDetails({ 
          ...movieDetails,
          // Convert id to movie_id to match LibraryMovie type
          movie_id: movieDetails.id,
          // Preserve library-specific data
          watched_at: movie.watched_at,
          rating: movie.rating,
          completed: movie.completed
        });
      } else {
        // Fallback to library movie data if we can't find the movie in the response
        setFullDetails(movie);
      }
    } catch (error) {
      console.error('Failed to fetch movie details:', error);
      // Fallback to library movie data
      setFullDetails(movie);
    } finally {
      setIsLoading(false);
    }
  };

    if (isOpen && movie) {
      fetchMovieDetails();
    } else {
      setFullDetails(null);
    }
  }, [movie, isOpen]);

  if (!movie) return null;

  const displayMovie = fullDetails || movie;

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="w-full max-w-4xl mx-4">
      <div className="p-6 space-y-6">
        {/* Header Section */}
        <div className="flex justify-between items-start">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {displayMovie.title}
          </h2>
          <button
            onClick={() => onRemove(displayMovie.movie_id)}
            className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 
              p-2 rounded-full hover:bg-red-100 dark:hover:bg-red-900 transition-colors"
          >
            Remove from Library
          </button>
        </div>

        {/* Library Info Section */}
        <div className="flex flex-wrap gap-4">
          {displayMovie.watched_at && (
            <Badge variant="blue">
              <Clock className="w-4 h-4 mr-2" />
              Watched on {new Date(displayMovie.watched_at).toLocaleDateString()}
            </Badge>
          )}
          {displayMovie.rating && (
            <Badge variant="accent">
              <Star className="w-4 h-4 mr-2" />
              Your Rating: {displayMovie.rating}/5
            </Badge>
          )}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column - Poster */}
          <div>
            <img
              src={displayMovie.imageUrl || '/api/placeholder/400/600'}
              alt={displayMovie.title}
              className="w-full rounded-lg shadow-lg object-cover"
            />
          </div>

          {/* Right Column - Details */}
          <div className="space-y-4">
            {/* Movie Info */}
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4" />
                <span className="text-gray-700 dark:text-gray-300">
                  Released: {displayMovie.release_year}
                </span>
              </div>
              {displayMovie.imdb_rating && (
                <div className="flex items-center space-x-2">
                  <Award className="w-4 h-4" />
                  <span className="text-gray-700 dark:text-gray-300">
                    IMDB Rating: {displayMovie.imdb_rating}/10
                  </span>
                </div>
              )}
            </div>

            {/* Description */}
            {displayMovie.description && (
              <p className="text-gray-700 dark:text-gray-300">
                {displayMovie.description}
              </p>
            )}

            {/* Genres */}
            {displayMovie.genres && (
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Genres</h3>
                <div className="flex flex-wrap gap-2">
                  {normalizeGenres(displayMovie.genres).map((genre: string, index: number) => (
                    <Badge key={`${genre}-${index}`}>
                      {genre}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {/* Cast */}
            {Array.isArray(displayMovie.cast) && displayMovie.cast.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Cast</h3>
                <div className="flex flex-wrap gap-2">
                  {displayMovie.cast.map((actor, index) => (
                    <Badge key={`${actor}-${index}`} variant="blue">
                      {actor}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Crew */}
            {Array.isArray(displayMovie.crew) && displayMovie.crew.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Directors</h3>
                <div className="flex flex-wrap gap-2">
                  {displayMovie.crew.map((member, index) => (
                    <Badge key={`${member}-${index}`} variant="accent">
                      {member}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Trailer Section */}
        {displayMovie.trailer_url && (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold">Watch Trailer</h3>
            <VideoSection url={displayMovie.trailer_url} title={displayMovie.title} />
          </div>
        )}

        {/* Stream Section */}
        {displayMovie.imdb_id && (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold">Watch Movie</h3>
            <VideoSection 
              url={`https://vidsrc.icu/embed/movie/${displayMovie.imdb_id}`}
              title={displayMovie.title}
            />
          </div>
        )}
      </div>
    </Modal>
  );
};