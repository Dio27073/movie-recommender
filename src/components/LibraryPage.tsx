import React, { useState } from 'react';
import { Star, Clock, BookMarked, Trash2 } from "lucide-react";
import { Tabs } from '../components/ui/tabs';
import { LibraryMovie } from '../features/movies/types';
import { useLibrary } from '../features/movies/hooks/useLibrary';
import { MovieDetailsModal } from '../components/movies/MovieDetailsModal';

interface MovieCardProps {
  movie: LibraryMovie;
  type: 'watched' | 'rated';
  onRemove: (movieId: number) => Promise<void>;
  onClick: () => void;
}

const MovieCard = ({ 
  movie, 
  type,
  onRemove,
  onClick
}: MovieCardProps) => {
  const [isRemoving, setIsRemoving] = useState(false);

  const handleRemove = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsRemoving(true);
    try {
      await onRemove(movie.movie_id);
    } catch (error) {
      console.error('Failed to remove from library:', error);
    } finally {
      setIsRemoving(false);
    }
  };

  return (
    <div 
      onClick={onClick}
      className="bg-light-primary dark:bg-dark-primary rounded-lg shadow-md overflow-hidden
        hover:shadow-lg transition-shadow cursor-pointer group"
    >
      {/* Image Container */}
      <div className="relative aspect-[2/3] overflow-hidden">
        <img 
          src={movie.imageurl || '/api/placeholder/300/450'} 
          alt={movie.title}
          className="w-full h-full object-cover transition-transform duration-300
            group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        
        {/* Remove Button - Top Right */}
        <button
          onClick={handleRemove}
          disabled={isRemoving}
          className="absolute top-2 right-2 p-2 rounded-full bg-black/40 
            hover:bg-red-600 text-white transition-colors"
          title="Remove from library"
        >
          {isRemoving ? 
            <span className="text-sm">...</span> :
            <Trash2 className="w-4 h-4" />
          }
        </button>

        {/* Movie Info - Bottom */}
        <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
          <h3 className="font-semibold text-lg mb-1 line-clamp-1">
            {movie.title}
          </h3>
          <p className="text-sm text-gray-200 mb-2">
            {movie.release_year}
          </p>
          
          {/* Watch Date or Rating */}
          <div className="flex items-center text-sm">
            {type === 'watched' && movie.watched_at && (
              <div className="flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                {new Date(movie.watched_at).toLocaleDateString()}
              </div>
            )}
            {type === 'rated' && movie.rating && (
              <div className="flex items-center text-yellow-400">
                <Star className="w-4 h-4 mr-1 fill-current" />
                <span>{movie.rating}/5</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const MovieGrid = ({ 
  movies, 
  type,
  onRemove,
  onMovieClick 
}: { 
  movies: LibraryMovie[]; 
  type: 'watched' | 'rated';
  onRemove: (movieId: number) => Promise<void>;
  onMovieClick: (movie: LibraryMovie) => void;
}) => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {movies.map((movie) => (
        <MovieCard
          key={movie.movie_id}
          movie={movie}
          type={type}
          onRemove={onRemove}
          onClick={() => onMovieClick(movie)}
        />
      ))}
    </div>
  );
};

const LibraryPage = () => {
  const { 
    watchedMovies, 
    ratedMovies,
    isLoading, 
    error,
    removeFromLibrary,
  } = useLibrary();

  const [selectedMovie, setSelectedMovie] = useState<LibraryMovie | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleMovieClick = (movie: LibraryMovie) => {
    setSelectedMovie(movie);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedMovie(null);
  };

  if (error) {
    return (
      <div className="p-8 text-center text-red-600 bg-red-50 dark:bg-red-900/10 rounded-lg">
        Error loading library: {error}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-8 text-center text-light-text/70 dark:text-dark-text/70">
        Loading your library...
      </div>
    );
  }

  const tabs = [
    {
      id: 'watched',
      label: (
        <div className="flex items-center space-x-2">
          <Clock className="w-4 h-4" />
          <span>Watched Movies ({watchedMovies.length})</span>
        </div>
      ),
      content: watchedMovies.length > 0 ? (
        <MovieGrid 
          movies={watchedMovies} 
          type="watched" 
          onRemove={removeFromLibrary}
          onMovieClick={handleMovieClick}
        />
      ) : (
        <div className="text-center py-8 text-light-text/70 dark:text-dark-text/70">
          You haven't watched any movies yet
        </div>
      )
    },
    {
      id: 'rated',
      label: (
        <div className="flex items-center space-x-2">
          <Star className="w-4 h-4" />
          <span>Rated Movies ({ratedMovies.length})</span>
        </div>
      ),
      content: ratedMovies.length > 0 ? (
        <MovieGrid 
          movies={ratedMovies} 
          type="rated" 
          onRemove={removeFromLibrary}
          onMovieClick={handleMovieClick}
        />
      ) : (
        <div className="text-center py-8 text-light-text/70 dark:text-dark-text/70">
          You haven't rated any movies yet
        </div>
      )
    }
  ];

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center mb-6 space-x-2">
        <BookMarked className="w-6 h-6" />
        <h1 className="text-2xl font-bold text-light-text dark:text-dark-text">My Library</h1>
      </div>

      <div className="bg-light-primary dark:bg-dark-primary rounded-lg shadow-lg p-6">
        <Tabs 
          tabs={tabs} 
          defaultTab="watched"
          className="w-full"
        />
      </div>

      <MovieDetailsModal
        movie={selectedMovie}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
};

export default LibraryPage;