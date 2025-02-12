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

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const handleMovieClick = (movie: any) => {
    // Handle movie click - implement as needed
    console.log('Movie clicked:', movie);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider>
          <Router>
            <div className="min-h-screen transition-colors duration-200">
              <Navbar />
              <div className="pt-16"> {/* Add padding-top to account for fixed navbar */}
                <Routes>
                  {/* Public routes */}
                  <Route path="/" element={<HomePage />} />
                  <Route path="/login" element={<LoginForm />} />
                  <Route path="/register" element={<RegisterForm />} />
                  
                  {/* Protected routes */}
                  <Route path="/browse" element={
                    <ProtectedRoute>
                      <MovieRecommendations />
                    </ProtectedRoute>
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