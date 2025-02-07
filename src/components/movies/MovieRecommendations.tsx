import { useState, useMemo, useCallback } from 'react';
import { Loader } from 'lucide-react';
import { 
  Movie, 
  FilterParams,
  FilterValue,
  SortOption,
  ViewType,
  SearchType
} from '../../features/movies/types';
import { useMovies, useDebounce } from '../../features/movies/hooks';
import { MovieCard } from './MovieCard';
import { MovieFilter } from './MovieFilter';
import { MovieDetailsModal } from './MovieDetailsModal';
import { ViewSwitcher } from '../ui/ViewSwitcher';
import { Pagination } from '../ui/Pagination';
import { useLibrary } from '../../features/movies/hooks/useLibrary';

const CURRENT_YEAR = new Date().getFullYear();
const MIN_YEAR = 1888;
const MIN_RATING = 0;
const MAX_RATING = 10;

const useMovieFilters = (onPageReset: () => void) => {
  const [selectedGenres, setSelectedGenres] = useState<Set<string>>(new Set());
  const [yearRange, setYearRange] = useState<[number, number]>([MIN_YEAR, CURRENT_YEAR]);
  const [ratingRange, setRatingRange] = useState<[number, number]>([MIN_RATING, MAX_RATING]);
  const [sortBy, setSortBy] = useState<SortOption>('imdb_rating_desc');
  const [viewType, setViewType] = useState<ViewType>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState<SearchType>('title');
  const [selectedCastCrew, setSelectedCastCrew] = useState<Set<string>>(new Set());
  const [selectedContentRatings, setSelectedContentRatings] = useState<Set<string>>(new Set());
  const [selectedMoods, setSelectedMoods] = useState<Set<string>>(new Set());
  const [selectedPlatforms, setSelectedPlatforms] = useState<Set<string>>(new Set());

  const debouncedYearRange = useDebounce(yearRange, 500);
  const debouncedRatingRange = useDebounce(ratingRange, 500);

  const handleFilterChange = useCallback((filterType: keyof FilterParams, value: FilterValue) => {
    onPageReset();
    
    switch (filterType) {
      case 'genres': {
        const { genre, checked } = value as { type: 'genres'; genre: string; checked: boolean };
        setSelectedGenres(prev => {
          const newGenres = new Set(prev);
          if (checked) {
            newGenres.add(genre);
          } else {
            newGenres.delete(genre);
          }
          return newGenres;
        });
        break;
      }
      case 'yearRange':
        setYearRange((value as { type: 'yearRange'; value: [number, number] }).value);
        break;
      case 'ratingRange':
        setRatingRange((value as { type: 'ratingRange'; value: [number, number] }).value);
        break;
      case 'sort':
        setSortBy((value as { type: 'sort'; value: SortOption }).value);
        break;
      case 'castCrew':
        setSelectedCastCrew((value as { type: 'castCrew'; value: Set<string> }).value);
        setSearchQuery('');
        break;
      case 'contentRating':
        setSelectedContentRatings((value as { type: 'contentRating'; value: Set<string> }).value);
        break;
      case 'moodTags':
        setSelectedMoods((value as { type: 'moodTags'; value: Set<string> }).value);
        break;
      case 'streamingPlatforms':
        setSelectedPlatforms((value as { type: 'streamingPlatforms'; value: Set<string> }).value);
        break;
    }
  }, [onPageReset]);

  const handleSearchChange = useCallback((query: string, type: SearchType) => {
    setSearchQuery(query);
    setSearchType(type);
    onPageReset();
  }, [onPageReset]);

  const handleCastCrewSelect = useCallback((name: string) => {
    const newSet = new Set(selectedCastCrew);
    newSet.add(name);
    handleFilterChange('castCrew', { type: 'castCrew', value: newSet });
  }, [selectedCastCrew, handleFilterChange]);

  const filters = useMemo((): FilterParams => ({
    genres: selectedGenres,
    yearRange: debouncedYearRange,
    ratingRange: debouncedRatingRange,
    sort: sortBy,
    view: viewType,
    castCrew: selectedCastCrew,
    searchQuery,
    searchType,
    contentRating: selectedContentRatings,
    moodTags: selectedMoods,
    streamingPlatforms: selectedPlatforms
  }), [
    selectedGenres, 
    debouncedYearRange, 
    debouncedRatingRange, 
    sortBy, 
    viewType, 
    selectedCastCrew, 
    searchQuery, 
    searchType,
    selectedContentRatings,
    selectedMoods,
    selectedPlatforms
  ]);

  return {
    filters,
    viewType,
    setViewType,
    handleFilterChange,
    handleSearchChange,
    handleCastCrewSelect,
    selectedGenres,
    yearRange,
    ratingRange,
    sortBy,
    searchQuery,
    searchType,
    selectedCastCrew,
    selectedContentRatings,
    selectedMoods,
    selectedPlatforms
  };
};

const MovieRecommendations = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { 
    watchedMovies, 
    ratedMovies,
    addToLibrary: handleAddToLibrary,
    removeFromLibrary: handleRemoveFromLibrary  // Add this
  } = useLibrary();

  const isInLibrary = useCallback((movieId: number) => {
    return watchedMovies.some(m => m.movie_id === movieId) || 
           ratedMovies.some(m => m.movie_id === movieId);
  }, [watchedMovies, ratedMovies]);

  const handlePageReset = useCallback(() => setCurrentPage(1), []);
  
  const {
    filters,
    viewType,
    setViewType,
    handleFilterChange,
    handleSearchChange,
    handleCastCrewSelect,
    selectedGenres,
    yearRange,
    ratingRange,
    sortBy,
    searchQuery,
    searchType,
    selectedCastCrew
  } = useMovieFilters(handlePageReset);

  const { 
    movies, 
    loading: moviesLoading, 
    error: moviesError,
    pagination 
  } = useMovies(currentPage, filters);

  const handleMovieClick = useCallback((movie: Movie) => {
    setSelectedMovie(movie);
    setIsModalOpen(true);
  }, []);

  const handleViewChange = useCallback((newView: ViewType) => {
    setViewType(newView);
  }, [setViewType]);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const getGenresArray = useCallback((genres: string | string[]): string[] => {
    if (Array.isArray(genres)) {
      return genres;
    }
    return genres.split(',').map(g => g.trim());
  }, []);

  const allGenres = useMemo(() => 
    Array.from(
      new Set(
        movies.flatMap(movie => getGenresArray(movie.genres))
      )
    ).sort(),
    [movies, getGenresArray]
  );

  const getViewClassName = () => {
    const baseClasses = {
      grid: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6',
      list: 'flex flex-col gap-4',
      compact: 'flex flex-col gap-2'
    };
    return baseClasses[viewType] || baseClasses.grid;
  };

  if (moviesError) {
    return (
      <div className="text-red-600 p-4" role="alert">
        {moviesError}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-dark-primary p-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">
        
      </h1>

      <div className="flex justify-between items-center mb-6">
        <ViewSwitcher currentView={viewType} onViewChange={handleViewChange} />
      </div>

      <div className="relative z-50">
        <MovieFilter
          genres={allGenres}
          selectedGenres={selectedGenres}
          yearRange={yearRange}
          ratingRange={ratingRange}
          sortBy={sortBy}
          viewType={viewType}
          onFilterChange={handleFilterChange}
          minYear={MIN_YEAR}
          maxYear={CURRENT_YEAR}
          searchQuery={searchQuery}
          searchType={searchType}
          onSearchChange={handleSearchChange}
          onCastCrewSelect={handleCastCrewSelect}
          selectedCastCrew={selectedCastCrew}
          onMovieSelect={handleMovieClick}
          selectedContentRatings={filters.contentRating}
          selectedMoods={filters.moodTags}
          selectedPlatforms={filters.streamingPlatforms}
        />
      </div>
  
      <div className="relative z-0">
        {movies.length === 0 && !moviesLoading ? (
          <div className="text-gray-600 dark:text-gray-400 p-4 mb-4">
            No movies found. Please adjust your filters and try again.
          </div>
        ) : (
          <main>
            {moviesLoading ? (
              <div className="flex justify-center items-center h-64">
                <Loader className="w-8 h-8 text-blue-500 dark:text-blue-400 animate-spin" />
              </div>
            ) : (
              <div className="flex flex-col">
                <div className={getViewClassName()}>
                  {movies.map((movie) => (
                    <MovieCard
                      key={movie.id}
                      movie={{
                        ...movie,
                        genres: getGenresArray(movie.genres),
                      }}
                      viewType={viewType}
                      onMovieClick={handleMovieClick}
                      onAddToLibrary={handleAddToLibrary}
                      onRemoveFromLibrary={handleRemoveFromLibrary}  // Add this
                      isInLibrary={isInLibrary(movie.id)}
                      />
                  ))}
                </div>
                
                {pagination && pagination.totalPages > 1 && (
                  <Pagination
                    currentPage={currentPage}
                    totalPages={pagination.totalPages}
                    onPageChange={handlePageChange}
                  />
                )}
              </div>
            )}
          </main>
        )}
      </div>

      <MovieDetailsModal
        movie={selectedMovie}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
};

export default MovieRecommendations;