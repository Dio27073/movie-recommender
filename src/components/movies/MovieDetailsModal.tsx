import React from 'react';
import { Star } from 'lucide-react';
import { Movie } from '../../features/movies/types';
import { Modal } from './Modal';

// Types
interface VideoPlayerProps {
  url: string;
  title: string;
}

interface MovieDetailsModalProps {
  movie: Movie | null;
  isOpen: boolean;
  onClose: () => void;
}

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'blue' | 'purple';
}

// Utility functions
const getYouTubeEmbedUrl = (url: string): string | null => {
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
  const match = url.match(regExp);
  return match && match[2].length === 11 ? match[2] : null;
};

// Badge Component
const Badge = ({ children, variant = 'default' }: BadgeProps) => {
  const variantStyles = {
    default: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
    blue: 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
    purple: 'bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
  };

  return (
    <span className={`px-3 py-1 rounded-full text-sm ${variantStyles[variant]}`}>
      {children}
    </span>
  );
};

const StreamPlayer = ({ movieId, title }: { movieId: string; title: string }) => {
  return (
    <div className="w-full bg-gray-900 rounded-lg overflow-hidden">
      <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
        <iframe
          src={`https://vidsrc.icu/embed/movie/${movieId}`}
          title={title}
          className="absolute inset-0 w-full h-full border-none"
          allow="fullscreen"
          allowFullScreen
        />
      </div>
    </div>
  );
};

// Video Player Component
const VideoPlayer = ({ url, title }: VideoPlayerProps) => {
  const [error, setError] = React.useState<string | null>(null);
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
      <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
        <iframe
          src={`https://www.youtube.com/embed/${videoId}`}
          title={`${title} trailer`}
          className="absolute inset-0 w-full h-full border-none"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          onError={() => setError('Failed to load video')}
        />
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900/90">
            <p className="text-red-400 text-center p-4">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Movie Rating Component
const MovieRating = ({ rating, votes }: { rating: number | null | undefined; votes?: number }) => (
  <div className="flex items-center">
    <Star className="w-6 h-6 text-yellow-400 fill-current" />
    <div className="ml-2">
      <div className="text-lg font-semibold dark:text-gray-200">
        {rating != null ? `${rating.toFixed(1)}/10` : 'N/A'}
        <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-1">
          IMDB
        </span>
      </div>
      {votes && (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {new Intl.NumberFormat().format(votes)} votes
        </div>
      )}
    </div>
  </div>
);

// Main MovieDetailsModal Component
export const MovieDetailsModal = ({
  movie,
  isOpen,
  onClose,
}: MovieDetailsModalProps) => {
  if (!movie) return null;

  const castArray = Array.isArray(movie.cast) 
    ? movie.cast 
    : movie.cast?.split(',').filter(Boolean) || [];
    
  const crewArray = Array.isArray(movie.crew)
    ? movie.crew
    : movie.crew?.split(',').filter(Boolean) || [];

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose}
      className="w-full max-w-4xl mx-4"
    >
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
          {movie.title}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Movie Poster */}
          <div>
            <img
              src={movie.imageUrl || '/api/placeholder/400/600'}
              alt={movie.title}
              className="w-full h-96 object-cover rounded-lg"
            />
          </div>

          {/* Movie Details */}
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <MovieRating rating={movie.imdb_rating} votes={movie.imdb_votes} />
              <p className="text-gray-600 dark:text-gray-400">
                Released: {movie.release_year}
              </p>
            </div>

            <p className="text-gray-700 dark:text-gray-300">
              {movie.description}
            </p>

            {/* Genres */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Genres
              </h3>
              <div className="flex flex-wrap gap-2">
                {(Array.isArray(movie.genres) ? movie.genres : [movie.genres])
                  .map((genre) => (
                    <Badge key={genre}>{genre}</Badge>
                  ))}
              </div>
            </div>
            
            {/* Cast & Crew */}
            <div className="space-y-4">
              {castArray.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    Cast
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {castArray.map((actor) => (
                      <Badge key={actor} variant="blue">{actor}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {crewArray.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    Directors
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {crewArray.map((director) => (
                      <Badge key={director} variant="purple">{director}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* IMDB Link */}
            {movie.imdb_id && (
              <a
                href={`https://www.imdb.com/title/${movie.imdb_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-gray-900 rounded-lg transition-colors"
              >
                View on IMDB
              </a>
            )}
          </div>
        </div>

        {/* Trailer Section */}
        {movie?.trailer_url && (
          <div className="mt-6">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Watch Trailer
            </h3>
            <VideoPlayer url={movie.trailer_url} title={movie.title} />
          </div>
        )}

        {/* Stream Section */}
        {movie?.imdb_id && (
          <div className="mt-6">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Watch Movie
            </h3>
            <StreamPlayer movieId={movie.imdb_id} title={movie.title} />
          </div>
        )}
      </div>
    </Modal>
  );
};