// src/components/movies/MovieRecommendations.tsx
import React, { useState, useMemo, useCallback } from 'react';
import { Star, Loader, ChevronLeft, ChevronRight } from 'lucide-react';
import { Movie } from '../../features/movies/types';
import { useMovies, useRateMovie, useDebounce } from '../../features/movies/hooks';
import { MovieCard } from './MovieCard';
import { MovieFilter } from './MovieFilter';

interface FilterParams {
  genres?: Set<string>;
  yearRange?: [number, number];
  minRating?: number;
  page?: number;
  per_page?: number;
}

type FilterValue = 
  | { genre: string; checked: boolean }
  | [number, number]
  | number;

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
}) => {
  const getPageNumbers = () => {
    let pages: (number | string)[] = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      pages = Array.from({ length: totalPages }, (_, i) => i + 1);
    } else {
      if (currentPage <= 3) {
        pages = [1, 2, 3, 4, 5, '...', totalPages];
      } else if (currentPage >= totalPages - 2) {
        pages = [1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
      } else {
        pages = [1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages];
      }
    }
    return pages;
  };

  return (
    <nav className="flex items-center justify-center w-full px-4 mt-8" aria-label="Pagination">
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className={`flex items-center justify-center p-2 rounded-md ${
            currentPage === 1
              ? 'text-gray-400 cursor-not-allowed'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-1">
          {getPageNumbers().map((page, index) => (
            <button
              key={index}
              onClick={() => typeof page === 'number' ? onPageChange(page) : null}
              disabled={page === '...'}
              className={`px-4 py-2 rounded-md ${
                page === currentPage
                  ? 'bg-blue-600 text-white'
                  : page === '...'
                  ? 'text-gray-500 cursor-default'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              {page}
            </button>
          ))}
        </div>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className={`flex items-center justify-center p-2 rounded-md ${
            currentPage === totalPages
              ? 'text-gray-400 cursor-not-allowed'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
          aria-label="Next page"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      </div>
    </nav>
  );
};

const MovieRecommendations: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedGenres, setSelectedGenres] = useState<Set<string>>(new Set());
  const [yearRange, setYearRange] = useState<[number, number]>([1888, 2024]);
  const [minRating, setMinRating] = useState(0);
  
  const debouncedYearRange = useDebounce(yearRange, 500);
  const debouncedMinRating = useDebounce(minRating, 500);
  
  const filters = useMemo(() => ({
    genres: selectedGenres,
    yearRange: debouncedYearRange,
    minRating: debouncedMinRating,
  }), [selectedGenres, debouncedYearRange, debouncedMinRating]);
  
  const { 
    movies, 
    loading: moviesLoading, 
    error: moviesError,
    pagination 
  } = useMovies(currentPage, filters);
  
  const { 
    rateMovie, 
    loading: ratingLoading, 
    error: ratingError 
  } = useRateMovie();

  const handleRate = useCallback(async (movieId: number, rating: number): Promise<void> => {
    const success = await rateMovie({ movie_id: movieId, rating });
  }, [rateMovie]);

  const handleFilterChange = useCallback((filterType: keyof FilterParams, value: FilterValue) => {
    setCurrentPage(1);
    
    switch (filterType) {
      case 'genres':
        const { genre, checked } = value as { genre: string; checked: boolean };
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
        
      case 'yearRange':
        setYearRange(value as [number, number]);
        break;
        
      case 'minRating':
        setMinRating(value as number);
        break;
    }
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const getGenresArray = useCallback((genres: string | string[]): string[] => {
    if (Array.isArray(genres)) {
      return genres;
    }
    return genres.split(',').map((g: string) => g.trim());
  }, []);

  const allGenres = useMemo(() => 
    Array.from(
      new Set(
        movies.flatMap(movie => getGenresArray(movie.genres))
      )
    ).sort(),
    [movies, getGenresArray]
  );

  if (moviesError || ratingError) {
    return (
      <div className="text-red-600 p-4">
        {moviesError || ratingError}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Movie Recommender</h1>
      
      <MovieFilter
        genres={allGenres}
        selectedGenres={selectedGenres}
        yearRange={yearRange}
        minRating={minRating}
        onFilterChange={handleFilterChange}
        minYear={1888}
        maxYear={2024}
      />

      {movies.length === 0 && !moviesLoading && (
        <div className="text-gray-600 p-4 mb-4">
          No movies found. Please check back later.
        </div>
      )}
      
      <main>
        {moviesLoading ? (
          <div className="flex justify-center items-center h-64">
            <Loader className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
        ) : (
          <div className="flex flex-col">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {movies.map((movie) => (
                <MovieCard
                  key={movie.id}
                  movie={{
                    ...movie,
                    genres: getGenresArray(movie.genres),
                  }}
                  onRate={(rating) => handleRate(movie.id, rating)}
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
    </div>
  );
};

export default MovieRecommendations;