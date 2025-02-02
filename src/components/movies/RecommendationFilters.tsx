import { useState } from 'react';
import { Sliders, RefreshCw } from 'lucide-react';

interface RecommendationFiltersProps {
  onFilterChange: (filters: RecommendationFilters) => void;
  onRefresh: () => void;
}

export interface RecommendationFilters {
  strategy: 'hybrid' | 'content' | 'collaborative';
  excludeWatched: boolean;
  minRating?: number;
  genres?: string[];
}

export const RecommendationFilters = ({ onFilterChange, onRefresh }: RecommendationFiltersProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [filters, setFilters] = useState<RecommendationFilters>({
    strategy: 'hybrid',
    excludeWatched: true,
  });

  const handleFilterChange = (newFilters: Partial<RecommendationFilters>) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };

  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-4">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
        >
          <Sliders className="w-5 h-5" />
          <span>Customize Recommendations</span>
        </button>
        
        <button
          onClick={onRefresh}
          className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
        >
          <RefreshCw className="w-5 h-5" />
          <span>Refresh</span>
        </button>
      </div>

      {isOpen && (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg">
          <div className="space-y-4">
            {/* Recommendation Strategy */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Recommendation Strategy
              </label>
              <select
                value={filters.strategy}
                onChange={(e) => handleFilterChange({ strategy: e.target.value as RecommendationFilters['strategy'] })}
                className="w-full p-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
              >
                <option value="hybrid">Balanced (Hybrid)</option>
                <option value="content">Based on Movie Features</option>
                <option value="collaborative">Based on User Behavior</option>
              </select>
            </div>

            {/* Exclude Watched */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="excludeWatched"
                checked={filters.excludeWatched}
                onChange={(e) => handleFilterChange({ excludeWatched: e.target.checked })}
                className="rounded border-gray-300 dark:border-gray-600"
              />
              <label htmlFor="excludeWatched" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Hide movies I've already watched
              </label>
            </div>

            {/* Minimum Rating */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Minimum Rating
              </label>
              <input
                type="range"
                min="0"
                max="5"
                step="0.5"
                value={filters.minRating || 0}
                onChange={(e) => handleFilterChange({ minRating: parseFloat(e.target.value) })}
                className="w-full"
              />
              <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {filters.minRating || 0} stars and above
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};