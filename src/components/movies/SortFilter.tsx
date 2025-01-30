import { useState, useRef, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { SortOption } from '../../features/movies/types';

interface SortFilterProps {
  sortBy: SortOption;
  onSortChange: (value: SortOption) => void;
}

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'imdb_rating_desc', label: 'Rating (High to Low)' },
  { value: 'imdb_rating_asc', label: 'Rating (Low to High)' },
  { value: 'release_date_desc', label: 'Newest First' },
  { value: 'release_date_asc', label: 'Oldest First' },
  { value: 'title_asc', label: 'Title (A-Z)' },
  { value: 'title_desc', label: 'Title (Z-A)' },
];

const SortFilter = ({ sortBy, onSortChange }: SortFilterProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getButtonText = () => {
    const currentSort = sortOptions.find(option => option.value === sortBy);
    return currentSort ? currentSort.label : 'Sort By';
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-4 py-2 
                   bg-gray-700/50 dark:bg-gray-800/50 
                   hover:bg-gray-700/70 dark:hover:bg-gray-800/70
                   border border-gray-600/30 dark:border-gray-700/30
                   rounded-lg text-gray-200 text-sm
                   transition-colors duration-200"
      >
        <span className="mr-2">{getButtonText()}</span>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {isOpen && (
        <div className="absolute z-50 w-64 mt-2 p-3
                      bg-gray-700/95 dark:bg-gray-800/95 
                      border border-gray-600/30 dark:border-gray-700/30
                      rounded-lg shadow-lg backdrop-blur-sm">
          <div className="space-y-2">
            {sortOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  onSortChange(option.value);
                  setIsOpen(false);
                }}
                className={`w-full text-left px-3 py-2 rounded-md text-sm
                          transition-colors duration-200
                          ${sortBy === option.value 
                            ? 'bg-blue-500/20 text-blue-400' 
                            : 'text-gray-200 hover:bg-gray-600/50'
                          }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SortFilter;