import React, { useState } from 'react';
import { Star } from 'lucide-react';
import { MovieCardProps, MovieFilterProps, Movie } from '../../features/movies/types';

const MovieCard: React.FC<MovieCardProps> = ({ 
  title, 
  year, 
  rating, 
  imageUrl = '/api/placeholder/200/300', 
  onRate 
}) => {
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <div 
      className="bg-white rounded-lg shadow-lg overflow-hidden transform transition duration-200 hover:scale-105"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <img
        src={imageUrl}
        alt={title}
        className="w-full h-64 object-cover"
      />
      <div className="p-4">
        <h3 className="text-xl font-semibold text-gray-800 mb-2">{title}</h3>
        <p className="text-gray-600 mb-2">{year}</p>
        <div className="flex items-center">
          <Star className="w-5 h-5 text-yellow-500" />
          <span className="ml-2 text-gray-700">{rating}</span>
        </div>
      </div>
      {isHovered && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center transition-opacity duration-200">
          <button 
            onClick={() => onRate(5)}
            className="bg-white p-3 rounded-full hover:bg-gray-100 transition-colors duration-200"
          >
            <Star className="w-6 h-6 text-yellow-500" />
          </button>
        </div>
      )}
    </div>
  );
};

const MovieFilter: React.FC<MovieFilterProps> = ({ genres, onFilterChange }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Filter by Genre</h2>
      <div className="space-y-3">
        {genres.map((genre) => (
          <label key={genre} className="flex items-center space-x-3 text-gray-700">
            <input
              type="checkbox"
              className="form-checkbox h-5 w-5 text-blue-600 rounded border-gray-300"
              onChange={(e) => onFilterChange(genre, e.target.checked)}
            />
            <span className="text-base">{genre}</span>
          </label>
        ))}
      </div>
    </div>
  );
};

const MovieRecommendations: React.FC = () => {
  const [movies, setMovies] = useState<Movie[]>([
    { id: 1, title: "Sample Movie 1", year: 2024, rating: 4.5 },
    { id: 2, title: "Sample Movie 2", year: 2024, rating: 4.0 }
  ]);

  const handleRate = (movieId: number, rating: number): void => {
    console.log(`Rating movie ${movieId} with ${rating} stars`);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Movie Recommender</h1>
      
      <div className="flex flex-col md:flex-row gap-8">
        <aside className="w-full md:w-64">
          <MovieFilter
            genres={["Action", "Comedy", "Drama", "Horror", "Sci-Fi"]}
            onFilterChange={(genre: string, checked: boolean) => 
              console.log(`${genre}: ${checked}`)
            }
          />
        </aside>
        
        <main className="flex-1">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {movies.map((movie) => (
              <MovieCard
                key={movie.id}
                {...movie}
                onRate={(rating) => handleRate(movie.id, rating)}
              />
            ))}
          </div>
        </main>
      </div>
    </div>
  );
};

export default MovieRecommendations;