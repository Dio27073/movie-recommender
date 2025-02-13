import { useRef, useEffect, useState } from 'react';
import { Search, X, Star } from 'lucide-react';
import { SearchType, Movie } from '../../features/movies/types';
import { useDebounce } from '../../features/movies/hooks';

// Types
interface MovieSearchProps {
  searchQuery: string;
  searchType: SearchType;
  onSearchChange: (query: string, type: SearchType) => void;
  onMovieSelect: (movie: Movie) => void;
  onCastCrewSelect?: (name: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

interface CastCrewResult {
  name: string;
  movies: number;
}

// Sub-components
const MovieResultItem = ({ movie, onSelect }: { movie: Movie; onSelect: (movie: Movie) => void }) => (
  <div
    className="px-4 py-2 hover:bg-light-secondary dark:hover:bg-dark-secondary cursor-pointer"
    onClick={() => onSelect(movie)}
  >
    <div className="flex items-center space-x-3">
      <img 
        src={movie.imageurl || '/api/placeholder/50/75'} 
        alt={movie.title}
        className="w-10 h-14 object-cover rounded"
      />
      <div className="flex-1">
        <div className="text-sm font-medium text-light-text dark:text-dark-text">
          {movie.title}
        </div>
        <div className="flex items-center text-xs text-light-text/60 dark:text-dark-text/60 space-x-2">
          <span>{movie.release_year}</span>
          {movie.imdb_rating && (
            <div className="flex items-center">
              <Star className="w-3 h-3 text-yellow-400 fill-current mr-1" />
              {movie.imdb_rating.toFixed(1)}
            </div>
          )}
        </div>
      </div>
    </div>
  </div>
);

const CastCrewResultItem = ({ result, onSelect }: { result: CastCrewResult; onSelect: (result: CastCrewResult) => void }) => (
  <div
    className="px-4 py-2 hover:bg-light-secondary dark:hover:bg-dark-secondary cursor-pointer"
    onClick={() => onSelect(result)}
  >
    <div className="flex items-center justify-between">
      <div className="text-sm font-medium text-light-text dark:text-dark-text">
        {result.name}
      </div>
      <div className="text-xs text-light-text/60 dark:text-dark-text/60">
        {result.movies} {result.movies === 1 ? 'movie' : 'movies'}
      </div>
    </div>
  </div>
);

const SearchResults = ({ 
  results, 
  isLoading, 
  onSelect 
}: { 
  results: (Movie | CastCrewResult)[];
  isLoading: boolean;
  searchType: SearchType;
  onSelect: (result: Movie | CastCrewResult) => void;
}) => {
  if (isLoading) {
    return (
      <div className="p-4 text-center text-light-text/60 dark:text-dark-text/60">
        Loading...
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="p-4 text-center text-light-text/60 dark:text-dark-text/60">
        No results found
      </div>
    );
  }

  return (
    <div className="py-1">
      {results.map((result, index) => (
        'title' in result ? (
          <MovieResultItem 
            key={`movie-${result.id}`}
            movie={result}
            onSelect={onSelect}
          />
        ) : (
          <CastCrewResultItem
            key={`cast-${result.name}-${index}`}
            result={result}
            onSelect={onSelect}
          />
        )
      ))}
    </div>
  );
};

// Main component
export const MovieSearch = ({
  searchQuery,
  searchType,
  onSearchChange,
  onMovieSelect,
  onCastCrewSelect,
  isOpen,
  onClose,
}: MovieSearchProps) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  const [searchResults, setSearchResults] = useState<(Movie | CastCrewResult)[]>([]);

  useEffect(() => {
    const fetchResults = async () => {
      if (!debouncedSearchQuery.trim()) {
        setSearchResults([]);
        return;
      }
    
      setIsLoading(true);
      try {
        const response = await fetch(
          `http://localhost:8000/movies/search/?query=${encodeURIComponent(debouncedSearchQuery)}&type=${searchType}&page=1`
        );
        if (!response.ok) {
          throw new Error('Search failed');
        }
        
        const data = await response.json();
        
        if (searchType === 'cast_crew') {
          const namesMap = new Map<string, number>();
          
          data.items.forEach((movie: Movie) => {
            const cast = Array.isArray(movie.cast) ? movie.cast : [];
            const crew = Array.isArray(movie.crew) ? movie.crew : [];
            const allNames = [...cast, ...crew];
            
            allNames.forEach(name => {
              if (name.toLowerCase().includes(debouncedSearchQuery.toLowerCase())) {
                namesMap.set(name, (namesMap.get(name) || 0) + 1);
              }
            });
          });
          
          const castCrewResults: CastCrewResult[] = Array.from(namesMap.entries())
            .map(([name, count]) => ({ name, movies: count }))
            .sort((a, b) => b.movies - a.movies)
            .slice(0, 5);
            
          setSearchResults(castCrewResults);
        } else {
          setSearchResults(data.items.slice(0, 5));
        }
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [debouncedSearchQuery, searchType]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleResultSelect = (result: Movie | CastCrewResult) => {
    if ('title' in result) {
      onMovieSelect(result);
    } else if (onCastCrewSelect) {
      onCastCrewSelect(result.name);
    }
    onClose();
    onSearchChange('', searchType);
  };

  return (
    <div 
      ref={containerRef}
      className="absolute top-0 right-0 w-96 bg-light-primary dark:bg-dark-primary p-4 rounded-lg shadow-lg z-50"
    >
      <div className="space-y-2">
        <div className="flex items-center justify-between mb-2">
          <label className="flex items-center space-x-2 text-sm font-medium text-light-text dark:text-dark-text">
            <Search className="w-4 h-4" />
            <span>Search</span>
          </label>
          <select
            className="text-sm border-gray-300 dark:border-gray-600 rounded-md text-light-text dark:text-dark-text bg-light-secondary dark:bg-dark-secondary"
            value={searchType}
            onChange={(e) => onSearchChange(searchQuery, e.target.value as SearchType)}
          >
            <option value="title">by Title</option>
            <option value="cast_crew">by Cast/Crew</option>
          </select>
        </div>
        
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            className="w-full px-3 py-2 bg-light-secondary dark:bg-dark-secondary border border-gray-300 dark:border-gray-600 rounded-md text-light-text dark:text-dark-text pr-10"
            placeholder={searchType === 'cast_crew' ? "Search by actor or director..." : "Search by movie title..."}
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value, searchType)}
          />
          {searchQuery && (
            <button
              className="absolute right-2 top-1/2 -translate-y-1/2 text-light-text/60 hover:text-light-text dark:text-dark-text/60 dark:hover:text-dark-text"
              onClick={() => onSearchChange('', searchType)}
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {searchQuery && (
          <div className="absolute left-0 right-0 mt-1 bg-light-primary dark:bg-dark-primary rounded-md shadow-lg max-h-96 overflow-auto">
            <SearchResults
              results={searchResults}
              isLoading={isLoading}
              searchType={searchType}
              onSelect={handleResultSelect}
            />
          </div>
        )}
      </div>
    </div>
  );
};