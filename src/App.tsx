import { useEffect } from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import MovieRecommendations from './components/movies/MovieRecommendations';
import { RecommendationSection } from './components/movies/RecommendationSection';
import HomePage from './components/HomePage';
import { ThemeProvider } from './features/theme/themeContext';
import { LoginForm, RegisterForm } from './components/auth';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/ui/Navbar';
import LibraryPage from './components/LibraryPage';

// Import the keep-alive service
import keepAliveService from './services/keepAliveService';

// Create a client with optimized settings for cold start scenarios
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error: any) => {
        // More aggressive retries for network errors (likely cold starts)
        if (error?.message?.includes('fetch') || error?.message?.includes('network')) {
          return failureCount < 3;
        }
        return failureCount < 1;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

function App() {
  useEffect(() => {
    // Keep-alive service starts automatically when imported
    console.log('🚀 App started - Keep-alive service active');
    
    // Log initial server connectivity
    const checkInitialConnectivity = async () => {
      try {
        const health = await keepAliveService.checkServerHealth();
        console.log('Initial server health check:', health);
        
        if (health.status === 'cold_start' || health.status === 'unhealthy') {
          console.log('⚠️ Server appears to be cold starting or unhealthy');
        }
      } catch (error) {
        console.log('⚠️ Initial server health check failed - likely cold start:', error);
      }
    };
    
    checkInitialConnectivity();
    
    // Optional: Log service status periodically in development
    if (import.meta.env.DEV) {
      const statusLogger = setInterval(() => {
        const status = keepAliveService.getStatus();
        console.log('Keep-alive status:', status);
      }, 5 * 60 * 1000); // Log every 5 minutes in dev
      
      return () => clearInterval(statusLogger);
    }

    // Cleanup function when app unmounts
    return () => {
      console.log('🛑 App unmounting - keeping alive service running for other tabs');
      // Note: We don't destroy the keep-alive service here because
      // other tabs might still need it
    };
  }, []);

  // Handle global errors that might be related to cold starts
  useEffect(() => {
    const handleGlobalError = (event: ErrorEvent) => {
      if (event.error?.message?.includes('fetch') || 
          event.error?.message?.includes('network') ||
          event.error?.message?.includes('Failed to fetch')) {
        console.log('🌐 Network error detected - might be cold start related:', event.error);
      }
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      if (event.reason?.message?.includes('fetch') || 
          event.reason?.message?.includes('network')) {
        console.log('🌐 Promise rejection - might be cold start related:', event.reason);
      }
    };

    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleGlobalError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  const handleMovieClick = (movie: any) => {
    // Handle movie click - implement as needed
    console.log('Movie clicked:', movie);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider>
          <Router>
            <div className="min-h-screen w-full bg-background transition-colors duration-200">
              <Navbar />
              <div className="pt-16"> {/* Add padding-top to account for fixed navbar */}
                <Routes>
                  {/* Public routes */}
                  <Route path="/" element={<HomePage />} />
                  <Route path="/login" element={<LoginForm />} />
                  <Route path="/register" element={<RegisterForm />} />
                  
                  {/* Protected routes */}
                  <Route path="/browse" element={
                      <MovieRecommendations />
                  } />
                  <Route path="/recommendations" element={
                    <ProtectedRoute>
                      <RecommendationSection onMovieClick={handleMovieClick} />
                    </ProtectedRoute>
                  } />

                  <Route path="/library" element={
                    <ProtectedRoute>
                      <LibraryPage />
                    </ProtectedRoute>
                  } />
                </Routes>
              </div>
            </div>
          </Router>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;