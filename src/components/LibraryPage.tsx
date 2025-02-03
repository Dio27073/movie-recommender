import React from 'react';
import { Star, Clock, BookMarked } from "lucide-react";
import { Tabs } from '../components/ui/tabs';
import { Movie, LibraryMovie } from '../features/movies/types';
import { useLibrary } from '../features/movies/hooks/useLibrary';

// Update MovieCard to use LibraryMovie type
const MovieCard = ({ movie, type }: { movie: LibraryMovie, type: 'watched' | 'rated' }) => (
  <div className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow">
    <div className="p-4">
      <div className="flex items-start space-x-4">
        <div className="w-24 h-36 bg-gray-200 rounded">
          {movie.imageUrl && (
            <img 
              src={movie.imageUrl} 
              alt={movie.title}
              className="w-full h-full object-cover rounded"
            />
          )}
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-lg">{movie.title}</h3>
          {type === 'watched' && movie.watched_at && (
            <div className="flex items-center mt-2 text-gray-600 dark:text-gray-400">
              <Clock className="w-4 h-4 mr-1" />
              <span>Watched on {new Date(movie.watched_at).toLocaleDateString()}</span>
            </div>
          )}
          {type === 'rated' && movie.rating && (
            <div className="flex items-center mt-2 text-yellow-500">
              <Star className="w-4 h-4 mr-1" />
              <span>{movie.rating} / 5</span>
            </div>
          )}
        </div>
      </div>
    </div>
  </div>
);

// Update MovieList to use LibraryMovie type
const MovieList = ({ movies, type }: { movies: LibraryMovie[], type: 'watched' | 'rated' }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {movies.map((movie) => (
      <MovieCard key={movie.movie_id} movie={movie} type={type} />
    ))}
  </div>
);


const LibraryPage = () => {
  const { 
    watchedMovies, 
    ratedMovies,
    isLoading, 
    error,
    removeFromLibrary 
  } = useLibrary();

  if (error) {
    return <div className="p-8 text-center text-red-600">Error loading library: {error}</div>;
  }

  if (isLoading) {
    return <div className="p-8 text-center">Loading your library...</div>;
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
        <MovieList movies={watchedMovies} type="watched" />
      ) : (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
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
        <MovieList movies={ratedMovies} type="rated" />
      ) : (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          You haven't rated any movies yet
        </div>
      )
    }
  ];

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center mb-6 space-x-2">
        <BookMarked className="w-6 h-6" />
        <h1 className="text-2xl font-bold dark:text-white">My Library</h1>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <Tabs 
          tabs={tabs} 
          defaultTab="watched"
          className="w-full"
        />
      </div>
    </div>
  );
};

export default LibraryPage;