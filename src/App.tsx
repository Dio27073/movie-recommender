import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import MovieRecommendations from './components/movies/MovieRecommendations';
import MovieDetails from './components/movies/MovieDetails';
import { ThemeProvider } from './features/theme/themeContext';
import { ThemeToggle } from './components/ui/ThemeToggle';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="min-h-screen bg-light-primary dark:bg-dark-primary text-light-text dark:text-dark-text transition-colors duration-200">
          <nav className="fixed top-4 right-4 z-50">
            <ThemeToggle />
          </nav>
          <Routes>
            <Route path="/" element={<MovieRecommendations />} />
            <Route path="/movie/:id" element={<MovieDetails />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;