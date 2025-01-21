// src/components/movies/MovieRecommendations.tsx
import React, { useState } from 'react';
import { Star, Loader } from 'lucide-react';
import { Movie } from '../../features/movies/types';
import { useMovies, useRateMovie } from '../../features/movies/hooks';
import { MovieCard } from './MovieCard';
import { MovieFilter } from './MovieFilter';

const MovieRecommendations: React.FC = () => {
  const { movies, loading: moviesLoading, error: moviesError } = useMovies();
  const { rateMovie, loading: ratingLoading, error: ratingError } = useRateMovie();
  const [selectedGenres, setSelectedGenres] = useState<Set<string>>(new Set());

  console.log('Current movies state:', movies);
  console.log('Loading state:', moviesLoading);
  console.log('Error state:', moviesError);

  const handleRate = async (movieId: number, rating: number): Promise<void> => {
    console.log('Rating movie:', movieId, 'with rating:', rating);
    const success = await rateMovie({ movie_id: movieId, rating });
    if (success) {
      console.log('Rating updated successfully');
    }
  };

  const handleFilterChange = (genre: string, checked: boolean) => {
    console.log('Filter change:', genre, checked);
    const newGenres = new Set(selectedGenres);
    if (checked) {
      newGenres.add(genre);
    } else {
      newGenres.delete(genre);
    }
    setSelectedGenres(newGenres);
  };

  // Helper function to convert genres to array
  const getGenresArray = (genres: string | string[]): string[] => {
    if (Array.isArray(genres)) {
      return genres;
    }
    return genres.split(',').map((g: string) => g.trim());
  };

  // Get unique genres from all movies
  const allGenres = Array.from(
    new Set(
      movies.flatMap(movie => getGenresArray(movie.genres))
    )
  ).sort();

  const filteredMovies = selectedGenres.size === 0 
    ? movies 
    : movies.filter(movie => {
        const movieGenres = getGenresArray(movie.genres);
        return movieGenres.some(genre => selectedGenres.has(genre));
      });

  if (moviesError || ratingError) {
    return (
      <div className="text-red-600 p-4">
        {moviesError || ratingError}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Movie Recommender</h1>
      
      {movies.length === 0 && !moviesLoading && (
        <div className="text-gray-600 p-4 mb-4">
          No movies found. Please check the console for errors.
        </div>
      )}
      
      <div className="flex flex-col md:flex-row gap-8">
        <aside className="w-full md:w-64">
          <MovieFilter
            genres={allGenres}
            selectedGenres={selectedGenres}
            onFilterChange={handleFilterChange}
          />
        </aside>
        
        <main className="flex-1">
          {moviesLoading ? (
            <div className="flex justify-center items-center h-64">
              <Loader className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredMovies.map((movie) => (
                <MovieCard
                  key={movie.id}
                  movie={{
                    ...movie,
                    genres: getGenresArray(movie.genres),
                  }}
                  onRate={(rating) => handleRate(movie.id, rating)}
                />
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default MovieRecommendations;