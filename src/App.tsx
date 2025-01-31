// src/App.tsx
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import MovieRecommendations from './components/movies/MovieRecommendations';
import HomePage from './components/HomePage';
import { ThemeProvider } from './features/theme/themeContext';
import { ThemeToggle } from './components/ui/ThemeToggle';
import { LoginForm, RegisterForm } from './components/auth';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/ui/Navbar'; // We'll create this

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <Router>
          <div className="min-h-screen transition-colors duration-200">
            <Navbar />
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
            </Routes>
          </div>
        </Router>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;