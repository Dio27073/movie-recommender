import { useState } from 'react';
import { RecommendationCard } from './RecommendationCard';
import { RecommendationFilters, type RecommendationFilters as Filters } from './RecommendationFilters';
import { ViewSwitcher, ViewType } from '../ui/ViewSwitcher';
import { Movie } from '../../features/movies/types';
import { useMovieRecommendations } from '../../features/movies/hooks';

interface RecommendationSectionProps {
  onMovieClick: (movie: Movie) => void;
}

export const RecommendationSection = ({ onMovieClick }: RecommendationSectionProps) => {
  const [viewType, setViewType] = useState<ViewType>('grid');
  const [filters, setFilters] = useState<Filters>({
    strategy: 'hybrid',
    excludeWatched: true,
  });

  const {
    data: recommendations,
    isLoading,
    isError,
    refetch
  } = useMovieRecommendations(filters);

  const handleFilterChange = (newFilters: Filters) => {
    setFilters(newFilters);
  };

  if (isError) {
    return (
      <div className="text-center py-10">
        <p className="text-gray-600 dark:text-gray-400">
          Unable to load recommendations. Please try again later.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Recommended for You
        </h2>
        <ViewSwitcher currentView={viewType} onViewChange={setViewType} />
      </div>

      <RecommendationFilters 
        onFilterChange={handleFilterChange}
        onRefresh={() => refetch()}
      />

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="bg-gray-200 dark:bg-gray-700 h-64 rounded-lg mb-4"></div>
              <div className="bg-gray-200 dark:bg-gray-700 h-4 rounded w-3/4 mb-2"></div>
              <div className="bg-gray-200 dark:bg-gray-700 h-4 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : recommendations?.items?.length ? (
        <div className={
          viewType === 'grid'
            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6'
            : 'space-y-4'
        }>
          {recommendations.items.map((recommendation) => (
            <RecommendationCard
              key={recommendation.movie_id}
              movie={recommendation}
              confidenceScore={recommendation.confidence_score}
              recommendationReason={recommendation.reason}
              onMovieClick={onMovieClick}
              viewType={viewType}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-10">
          <p className="text-gray-600 dark:text-gray-400">
            No recommendations found based on your current preferences.
            Try adjusting the filters or watching more movies to get better recommendations.
          </p>
        </div>
      )}
    </div>
  );
};