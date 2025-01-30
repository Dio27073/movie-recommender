import { useState, useRef, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { ALL_GENRES } from '../../features/movies/constant';

interface GenreFilterProps {
  selectedGenres: Set<string>;
  onFilterChange: (type: 'genres', value: { genre: string; checked: boolean }) => void;
}

const GenreFilter = ({ selectedGenres, onFilterChange }: GenreFilterProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
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
    if (selectedGenres.size === 0) return 'All Genres';
    if (selectedGenres.size === 1) return Array.from(selectedGenres)[0];
    return `${selectedGenres.size} Genres`;
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
        <div className="absolute z-50 w-96 mt-2 p-3
                      bg-gray-700/95 dark:bg-gray-800/95 
                      border border-gray-600/30 dark:border-gray-700/30
                      rounded-lg shadow-lg backdrop-blur-sm">
        <div className="grid grid-cols-3 gap-2">  {/* Changed from grid-cols-2 to grid-cols-3 */}
          {ALL_GENRES.map((genre) => (
            <label
              key={genre}
              className="flex items-center space-x-2 cursor-pointer group"
            >
              <input
                type="checkbox"
                checked={selectedGenres.has(genre)}
                onChange={(e) => onFilterChange('genres', {
                  genre,
                  checked: e.target.checked
                })}
                className="w-4 h-4 rounded 
                        border-gray-600
                        text-blue-500
                        focus:ring-1
                        focus:ring-blue-500
                        focus:ring-offset-0
                        bg-gray-800
                        checked:bg-blue-500
                        checked:border-blue-500
                        transition-colors"
              />
              <span className="text-sm text-gray-200 group-hover:text-blue-400 
                            transition-colors duration-200 whitespace-nowrap"> {/* Added whitespace-nowrap */}
                {genre}
              </span>
            </label>
          ))}
        </div>
      </div>
      )}
    </div>
  );
};

export default GenreFilter;