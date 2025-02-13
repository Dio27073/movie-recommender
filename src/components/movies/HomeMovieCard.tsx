import { Movie } from '../../features/movies/types';

interface HomeMovieCardProps {
  movie: Movie;
  onMovieClick: (movie: Movie) => void;
}

const HomeMovieCard = ({ movie, onMovieClick }: HomeMovieCardProps) => {
  return (
    <div 
      onClick={() => onMovieClick(movie)}
      className="relative group cursor-pointer overflow-hidden rounded-lg transition-transform duration-300 hover:scale-105"
      role="button"
      tabIndex={0}
      onKeyPress={(e) => e.key === 'Enter' && onMovieClick(movie)}
    >
      {/* Poster Image */}
      <img
        src={movie.imageurl || '/api/placeholder/200/300'}
        alt={movie.title}
        className="w-full h-96 object-cover"
      />
      
      {/* Overlay with movie title on hover */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <h3 className="text-white font-semibold text-lg">
            {movie.title}
          </h3>
          <p className="text-gray-300 text-sm">
            {movie.release_year}
          </p>
        </div>
      </div>
    </div>
  );
};

export default HomeMovieCard;