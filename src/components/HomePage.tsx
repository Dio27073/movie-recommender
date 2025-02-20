import React, { useState, useEffect } from 'react';
import { Play, Search, Star, Sparkles } from 'lucide-react';
import MovieCarousel from './MovieCarousel';
import { Movie } from '../features/movies/types';
import { MovieDetailsModal } from './movies/MovieDetailsModal';
import apiService from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const HomePage = () => {
  const [trendingMovies, setTrendingMovies] = useState<Movie[]>([]);
  const [recentMovies, setRecentMovies] = useState<Movie[]>([]);
  const [netflixMovies, setNetflixMovies] = useState<Movie[]>([]);
  const [huluMovies, setHuluMovies] = useState<Movie[]>([]);
  const [funnyMovies, setFunnyMovies] = useState<Movie[]>([]);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchMovies = async () => {
      try {
        const [trending, recent, netflix, hulu, funny] = await Promise.all([
          apiService.getTrendingMovies({ time_window: 'week', per_page: 30 }),
          apiService.getMovies({
            sort: 'release_date_desc',
            release_date_lte: new Date().toISOString().split('T')[0],
            per_page: 30
          }),
          apiService.getMovies({
            streaming_platforms: 'Netflix',
            sort: 'imdb_rating_desc',
            per_page: 30
          }),
          apiService.getMovies({
            streaming_platforms: 'Hulu',
            sort: 'imdb_rating_desc',
            per_page: 30
          }),
          apiService.getMovies({
            mood_tags: 'Funny',
            sort: 'imdb_rating_desc',
            per_page: 30
          })
        ]);

        setTrendingMovies(trending.items || []);
        setRecentMovies(recent.items || []);
        setNetflixMovies(netflix.items || []);
        setHuluMovies(hulu.items || []);
        setFunnyMovies(funny.items || []);
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

  const handleExploreClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (isAuthenticated) {
      navigate('/browse');
    } else {
      navigate('/browse', { 
        state: { 
          from: '/browse',
          message: 'Please log in to access personalized movie recommendations' 
        } 
      });
    }
  };

  return (
    <div className="min-h-screen bg-light-primary dark:bg-dark-primary pt-16">
      {/* Enhanced Hero Section */}
      <div className="relative h-[70vh] overflow-hidden">
        {/* Animated gradient background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-900/90 via-pink-900/80 to-teal-800/90" />
          
          {/* Animated blobs */}
          <div className="absolute inset-0 opacity-30">
            <div className="absolute top-10 left-10 w-72 h-72 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl animate-blob" />
            <div className="absolute top-0 right-10 w-72 h-72 bg-teal-500 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-2000" />
            <div className="absolute bottom-10 left-20 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-4000" />
          </div>
        </div>

        {/* Content */}
        <div className="relative z-10 h-full flex flex-col justify-center items-center px-4">
          <div className="max-w-4xl mx-auto text-center">
            {/* Heading with sparkle icons */}
            <div className="flex items-center justify-center gap-4 mb-6">
              <Sparkles className="w-8 h-8 text-pink-400 animate-pulse" />
              <h1 className="text-5xl md:text-7xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-300 via-purple-300 to-teal-300 tracking-tight">
                Discover Your Next Favorite Movie
              </h1>
              <Sparkles className="w-8 h-8 text-teal-400 animate-pulse" />
            </div>

            {/* Subheading with glass effect */}
            <div className="backdrop-blur-sm bg-white/10 rounded-2xl p-6 shadow-2xl">
              <p className="text-xl md:text-2xl text-gray-100 leading-relaxed">
                Personalized recommendations based on your taste and viewing history
              </p>
            </div>

            {/* Enhanced CTA Button */}
            <button
              onClick={handleExploreClick}
              className="mt-12 group relative px-8 py-4 overflow-hidden rounded-full bg-gradient-to-r from-pink-500 to-teal-500 text-white font-semibold text-lg transform transition-all hover:scale-105 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-pink-500 focus:ring-offset-2 focus:ring-offset-transparent"
            >
              <span className="relative z-10">Start Exploring</span>
              <div className="absolute inset-0 -translate-x-full group-hover:translate-x-0 bg-gradient-to-r from-pink-600 to-teal-600 transition-transform duration-300" />
            </button>
          </div>
        </div>

        {/* Bottom fade */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-gray-900 to-transparent" />
      </div>

      {/* Movie Carousels Section */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          </div>
        ) : (
          <>
            <MovieCarousel title="Trending Movies" movies={trendingMovies} onMovieClick={handleMovieClick} />
            <MovieCarousel title="Recent Releases" movies={recentMovies} onMovieClick={handleMovieClick} />
            <MovieCarousel title="Streaming on Netflix" movies={netflixMovies} onMovieClick={handleMovieClick} />
            <MovieCarousel title="Streaming on Hulu" movies={huluMovies} onMovieClick={handleMovieClick} />
            <MovieCarousel title="Funny Movies" movies={funnyMovies} onMovieClick={handleMovieClick} />
          </>
        )}
      </div>

      {/* Enhanced Features Section */}
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
    <div className="flex flex-col items-center text-center p-6 bg-white dark:bg-dark-primary rounded-lg shadow-md hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300">
      <div className="text-blue-600 mb-4">
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2 dark:text-white">{title}</h3>
      <p className="text-gray-600 dark:text-gray-300">{description}</p>
    </div>
  );
};

export default HomePage;