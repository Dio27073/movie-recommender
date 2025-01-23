import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import MovieRecommendations from './components/movies/MovieRecommendations';
import MovieDetails from './components/movies/MovieDetails';

function App() {
  return (
    <Router>
      <div className="bg-gray-100 min-h-screen">
        <Routes>
          <Route path="/" element={<MovieRecommendations />} />
          <Route path="/movie/:id" element={<MovieDetails />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;