import React from 'react';
import { Star } from 'lucide-react';
import { Movie } from '../../features/movies/types';
import { Modal } from './Modal';

interface VideoPlayerProps {
  url: string;
  title: string;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ url, title }) => {
  const [error, setError] = React.useState<string | null>(null);

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
      <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
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

interface MovieDetailsModalProps {
  movie: Movie | null;
  isOpen: boolean;
  onClose: () => void;
}

export const MovieDetailsModal: React.FC<MovieDetailsModalProps> = ({
  movie,
  isOpen,
  onClose,
}) => {
  if (!movie) return null;

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
          <div>
            <img
              src={movie.imageUrl || '/api/placeholder/400/600'}
              alt={movie.title}
              className="w-full h-96 object-cover rounded-lg"
            />
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center">
                <Star className="w-6 h-6 text-yellow-400 fill-current" />
                <div className="ml-2">
                  <div className="text-lg font-semibold dark:text-gray-200">
                    {movie.imdb_rating 
                      ? `${movie.imdb_rating.toFixed(1)}/10` 
                      : 'N/A'}
                    <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-1">
                      IMDB
                    </span>
                  </div>
                  {movie.imdb_votes && (
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {new Intl.NumberFormat().format(movie.imdb_votes)} votes
                    </div>
                  )}
                </div>
              </div>
              <p className="text-gray-600 dark:text-gray-400">
                Released: {movie.release_year}
              </p>
            </div>

            <p className="text-gray-700 dark:text-gray-300">
              {movie.description}
            </p>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Genres
              </h3>
              <div className="flex flex-wrap gap-2">
                {(Array.isArray(movie.genres) ? movie.genres : [movie.genres]).map((genre) => (
                  <span
                    key={genre}
                    className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm"
                  >
                    {genre}
                  </span>
                ))}
              </div>
            </div>

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

        {movie?.trailer_url && (
          <div className="mt-6">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Watch Trailer
            </h3>
            <VideoPlayer url={movie.trailer_url} title={movie.title} />
          </div>
        )}
      </div>
    </Modal>
  );
};
export default MovieDetailsModal;