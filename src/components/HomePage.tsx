import React, { useState, useEffect } from 'react';
import { Play, Search, Star, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';
import MovieCarousel from './MovieCarousel';
import { Movie } from '../features/movies/types';
import { MovieDetailsModal } from './movies/MovieDetailsModal';
import apiService from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const HomePage = () => {
  // Movie data states
  const [trendingMovies, setTrendingMovies] = useState<Movie[]>([]);
  const [recentMovies, setRecentMovies] = useState<Movie[]>([]);
  const [netflixMovies, setNetflixMovies] = useState<Movie[]>([]);
  const [huluMovies, setHuluMovies] = useState<Movie[]>([]);
  const [funnyMovies, setFunnyMovies] = useState<Movie[]>([]);
  
  // Cold start handling states
  const [backendStatus, setBackendStatus] = useState<'checking' | 'starting' | 'ready' | 'error'>('checking');
  const [coldStartProgress, setColdStartProgress] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  
  // Individual loading states for each section
  const [loadingStates, setLoadingStates] = useState({
    trending: true,
    recent: true,
    netflix: true,
    hulu: true,
    funny: true
  });
  
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Cold start detection and handling
  useEffect(() => {
    const handleColdStart = async () => {
      try {
        setBackendStatus('checking');
        
        // Check if backend is already ready
        const health = await apiService.checkHealth();
        
        if (health.status === 'healthy') {
          setBackendStatus('ready');
          loadMovieData();
          return;
        }
        
        // Backend is cold starting
        setBackendStatus('starting');
        
        // Simulate progress during cold start
        const progressInterval = setInterval(() => {
          setColdStartProgress(prev => {
            if (prev >= 90) return prev; // Don't go to 100% until actually ready
            return prev + Math.random() * 10;
          });
        }, 1000);
        
        // Wait for backend to be ready
        await apiService.waitForBackend(90000); // 90 second timeout
        
        clearInterval(progressInterval);
        setColdStartProgress(100);
        setBackendStatus('ready');
        
        // Small delay for smooth UX
        setTimeout(() => {
          loadMovieData();
        }, 500);
        
      } catch (error) {
        console.error('Cold start failed:', error);
        setBackendStatus('error');
        setColdStartProgress(0);
      }
    };

    handleColdStart();
  }, [retryCount]);

  const loadMovieData = async () => {
    // Load each section independently with staggered timing
    const sections = [
      { name: 'trending', fetch: fetchTrending, delay: 0 },
      { name: 'recent', fetch: fetchRecent, delay: 500 },
      { name: 'netflix', fetch: fetchNetflix, delay: 1000 },
      { name: 'hulu', fetch: fetchHulu, delay: 1500 },
      { name: 'funny', fetch: fetchFunny, delay: 2000 }
    ];

    sections.forEach(({ fetch, delay }) => {
      setTimeout(fetch, delay);
    });
  };

  const fetchTrending = async () => {
    try {
      console.log('Fetching trending movies...');
      const data = await apiService.getTrendingMovies({ time_window: 'week', per_page: 30 });
      setTrendingMovies(data.items || []);
    } catch (error) {
      console.error('Error fetching trending movies:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, trending: false }));
    }
  };

  const fetchRecent = async () => {
    try {
      console.log('Fetching recent movies...');
      const data = await apiService.getMovies({
        sort: 'release_date_desc',
        release_date_lte: new Date().toISOString().split('T')[0],
        per_page: 30
      });
      setRecentMovies(data.items || []);
    } catch (error) {
      console.error('Error fetching recent movies:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, recent: false }));
    }
  };

  const fetchNetflix = async () => {
    try {
      console.log('Fetching Netflix movies...');
      const data = await apiService.getMovies({
        streaming_platforms: 'Netflix',
        sort: 'imdb_rating_desc',
        per_page: 30
      });
      setNetflixMovies(data.items || []);
    } catch (error) {
      console.error('Error fetching Netflix movies:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, netflix: false }));
    }
  };

  const fetchHulu = async () => {
    try {
      console.log('Fetching Hulu movies...');
      const data = await apiService.getMovies({
        streaming_platforms: 'Hulu',
        sort: 'imdb_rating_desc',
        per_page: 30
      });
      setHuluMovies(data.items || []);
    } catch (error) {
      console.error('Error fetching Hulu movies:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, hulu: false }));
    }
  };

  const fetchFunny = async () => {
    try {
      console.log('Fetching funny movies...');
      const data = await apiService.getMovies({
        mood_tags: 'Funny',
        sort: 'imdb_rating_desc',
        per_page: 30
      });
      setFunnyMovies(data.items || []);
    } catch (error) {
      console.error('Error fetching funny movies:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, funny: false }));
    }
  };

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

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    setColdStartProgress(0);
  };

  // Cold Start Loading Screen
  if (backendStatus === 'checking' || backendStatus === 'starting') {
    return (
      <div className="min-h-screen bg-light-primary dark:bg-dark-primary flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          {/* Animated Logo/Icon */}
          <div className="mb-8">
            <div className="w-20 h-20 mx-auto bg-gradient-to-r from-pink-500 to-teal-500 rounded-full flex items-center justify-center animate-pulse">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
          </div>

          {/* Status Message */}
          <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4">
            {backendStatus === 'checking' ? 'Connecting...' : 'Waking up the server...'}
          </h2>
          
          <p className="text-gray-600 dark:text-gray-300 mb-8">
            {backendStatus === 'checking' 
              ? 'Checking server status...'
              : 'Our server was sleeping to save energy. This usually takes 30-60 seconds.'
            }
          </p>

          {/* Progress Bar */}
          {backendStatus === 'starting' && (
            <div className="mb-6">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-2">
                <div 
                  className="bg-gradient-to-r from-pink-500 to-teal-500 h-3 rounded-full transition-all duration-1000 ease-out"
                  style={{ width: `${coldStartProgress}%` }}
                />
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {Math.round(coldStartProgress)}% complete
              </p>
            </div>
          )}

          {/* Loading Spinner */}
          <div className="flex justify-center">
            <RefreshCw className="w-6 h-6 text-pink-500 animate-spin" />
          </div>
        </div>
      </div>
    );
  }

  // Error State
  if (backendStatus === 'error') {
    return (
      <div className="min-h-screen bg-light-primary dark:bg-dark-primary flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4">
            Connection Failed
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-8">
            We're having trouble connecting to our servers. This sometimes happens with free hosting.
          </p>
          <button
            onClick={handleRetry}
            className="px-6 py-3 bg-gradient-to-r from-pink-500 to-teal-500 text-white rounded-lg font-semibold hover:shadow-lg transform hover:scale-105 transition-all"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Skeleton loader for carousels
  const CarouselSkeleton = () => (
    <div className="mb-12">
      <div className="w-48 h-7 bg-gray-300 dark:bg-gray-700 rounded mb-4 animate-pulse"></div>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {Array(5).fill(0).map((_, i) => (
          <div key={i} className="flex-shrink-0 w-48 animate-pulse">
            <div className="w-full h-72 bg-gray-300 dark:bg-gray-700 rounded-lg mb-2"></div>
            <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-3/4 mb-1"></div>
            <div className="h-3 bg-gray-300 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-light-primary dark:bg-dark-primary pt-16">
      {/* Enhanced Hero Section */}
      <div className="relative h-[70vh] overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-900/90 via-pink-900/80 to-teal-800/90" />
          
          <div className="absolute inset-0 opacity-30">
            <div className="absolute top-10 left-10 w-72 h-72 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl animate-blob" />
            <div className="absolute top-0 right-10 w-72 h-72 bg-teal-500 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-2000" />
            <div className="absolute bottom-10 left-20 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-4000" />
          </div>
        </div>

        <div className="relative z-10 h-full flex flex-col justify-center items-center px-4">
          <div className="max-w-4xl mx-auto text-center">
            <div className="flex items-center justify-center gap-4 mb-6">
              <Sparkles className="w-8 h-8 text-pink-400 animate-pulse" />
              <h1 className="text-5xl md:text-7xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-300 via-purple-300 to-teal-300 tracking-tight">
                Discover Your Next Favorite Movie
              </h1>
              <Sparkles className="w-8 h-8 text-teal-400 animate-pulse" />
            </div>

            <div className="backdrop-blur-sm bg-white/10 rounded-2xl p-6 shadow-2xl">
              <p className="text-xl md:text-2xl text-gray-100 leading-relaxed">
                Personalized recommendations based on your taste and viewing history
              </p>
            </div>

            <button
              onClick={handleExploreClick}
              className="mt-12 group relative px-8 py-4 overflow-hidden rounded-full bg-gradient-to-r from-pink-500 to-teal-500 text-white font-semibold text-lg transform transition-all hover:scale-105 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-pink-500 focus:ring-offset-2 focus:ring-offset-transparent"
            >
              <span className="relative z-10">Start Exploring</span>
              <div className="absolute inset-0 -translate-x-full group-hover:translate-x-0 bg-gradient-to-r from-pink-600 to-teal-600 transition-transform duration-300" />
            </button>
          </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-gray-900 to-transparent" />
      </div>

      {/* Movie Carousels Section - Progressive Loading */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Success indicator - movies are loading */}
        {backendStatus === 'ready' && (
          <div className="mb-8 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">Server is ready! Loading your movies...</span>
            </div>
          </div>
        )}

        {/* Each section loads independently */}
        <div className="mb-8">
          {loadingStates.trending 
            ? <CarouselSkeleton /> 
            : <MovieCarousel 
                title="Trending Movies" 
                movies={trendingMovies} 
                onMovieClick={handleMovieClick}
              />
          }
        </div>
        
        <div className="mb-8">
          {loadingStates.recent 
            ? <CarouselSkeleton /> 
            : <MovieCarousel 
                title="Recent Releases" 
                movies={recentMovies} 
                onMovieClick={handleMovieClick}
              />
          }
        </div>
        
        <div className="mb-8">
          {loadingStates.netflix 
            ? <CarouselSkeleton /> 
            : <MovieCarousel 
                title="Streaming on Netflix" 
                movies={netflixMovies} 
                onMovieClick={handleMovieClick}
              />
          }
        </div>
        
        <div className="mb-8">
          {loadingStates.hulu 
            ? <CarouselSkeleton /> 
            : <MovieCarousel 
                title="Streaming on Hulu" 
                movies={huluMovies} 
                onMovieClick={handleMovieClick}
              />
          }
        </div>
        
        <div className="mb-8">
          {loadingStates.funny 
            ? <CarouselSkeleton /> 
            : <MovieCarousel 
                title="Funny Movies" 
                movies={funnyMovies} 
                onMovieClick={handleMovieClick}
              />
          }
        </div>
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