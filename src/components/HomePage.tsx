import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Play, Search, Star } from 'lucide-react';
import MovieCarousel from './MovieCarousel';
import { Movie } from '../features/movies/types';
import { MovieDetailsModal } from './movies/MovieDetailsModal';
import apiService from '../services/api';

const HomePage = () => {
  const [trendingMovies, setTrendingMovies] = useState<Movie[]>([]);
  const [recentMovies, setRecentMovies] = useState<Movie[]>([]);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMovies = async () => {
      try {
        // Fetch trending movies (sorted by rating)
        const trendingResponse = await apiService.getMovies({
          sort: 'imdb_rating_desc',
          per_page: 10
        });
        setTrendingMovies(trendingResponse.items || []);

        // Fetch recent releases (sorted by release date, excluding future releases)
        const currentDate = new Date();
        const recentResponse = await apiService.getMovies({
          sort: 'release_date_desc',
          max_year: currentDate.getFullYear(),
          per_page: 10
        });
        setRecentMovies(recentResponse.items || []);
      } catch (error) {
        console.error('Error fetching movies:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMovies();
  }, []);

  const handleMovieClick = (movie: Movie) => {
    setSelectedMovie(movie);
    setIsModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-light-primary dark:bg-dark-primary">
      {/* Hero Section */}
      <div className="relative h-[70vh] bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800">
        {/* Animated background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMzLjMxIDAgNiAyLjY5IDYgNnMtMi42OSA2LTYgNi02LTIuNjktNi02IDIuNjktNiA2LTZ6TTQgNGg1MnY1Mkg0VjR6IiBzdHJva2U9IiNmZmYiIHN0cm9rZS1vcGFjaXR5PSIuMDUiLz48L2c+PC9zdmc+')] bg-repeat" />
        </div>
        
        {/* Accent gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-teal-500/20" />
        
        {/* Content */}
        <div className="relative z-10 h-full flex flex-col justify-center items-center text-white px-4">
          <h1 className="text-5xl md:text-7xl font-bold text-center mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-teal-400">
            Discover Your Next Favorite Movie
          </h1>
          <p className="text-xl md:text-2xl text-center mb-8 max-w-2xl text-gray-300">
            Personalized recommendations based on your taste and viewing history
          </p>
          <Link
            to="/browse"
            className="group relative px-8 py-3 overflow-hidden rounded-full bg-gradient-to-r from-blue-500 to-teal-500 hover:from-blue-600 hover:to-teal-600 text-white font-semibold text-lg transition-all duration-300"
          >
            <span className="relative z-10">Start Exploring</span>
            <div className="absolute inset-0 -translate-x-full group-hover:translate-x-0 bg-gradient-to-r from-blue-600 to-teal-600 transition-transform duration-300" />
          </Link>
        </div>

        {/* Bottom fade */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-gray-900 to-transparent" />
      </div>

      {/* Movie Carousels Section */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            <MovieCarousel
              title="Trending Now"
              movies={trendingMovies}
              onMovieClick={handleMovieClick}
            />
            <MovieCarousel
              title="Recent Releases"
              movies={recentMovies}
              onMovieClick={handleMovieClick}
            />
          </>
        )}
      </div>

      {/* Features Section */}
      <div className="py-16 px-4 bg-gray-50 dark:bg-dark-secondary">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
          <FeatureCard
            icon={<Search className="w-8 h-8" />}
            title="Advanced Search"
            description="Filter by genre, year, rating, and more to find exactly what you're looking for"
          />
          <FeatureCard
            icon={<Star className="w-8 h-8" />}
            title="Personalized Recommendations"
            description="Get movie suggestions tailored to your taste and viewing history"
          />
          <FeatureCard
            icon={<Play className="w-8 h-8" />}
            title="Comprehensive Database"
            description="Access detailed information about thousands of movies, including ratings and trailers"
          />
        </div>
      </div>

      <MovieDetailsModal
        movie={selectedMovie}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
};

const FeatureCard = ({ icon, title, description }: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) => {
  return (
    <div className="flex flex-col items-center text-center p-6 bg-white dark:bg-dark-primary rounded-lg shadow-md">
      <div className="text-blue-600 mb-4">
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2 dark:text-white">{title}</h3>
      <p className="text-gray-600 dark:text-gray-300">{description}</p>
    </div>
  );
};

export default HomePage;