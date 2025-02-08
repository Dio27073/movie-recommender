import { useState, useRef, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { ALL_GENRES } from '../../features/movies/constant';
import { FilterValue, FilterParams } from '../../features/movies/types';
import { useTheme } from '../../features/theme/themeContext';

interface GenreFilterProps {
  selectedGenres: Set<string>;
  onFilterChange: (filterType: keyof FilterParams, value: FilterValue) => void;
}

const GenreFilter = ({ selectedGenres, onFilterChange }: GenreFilterProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();

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

  const handleGenreChange = (genre: string, checked: boolean) => {
    onFilterChange('genre', {
      type: 'genre',
      genre,
      checked
    });
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-full px-4 py-2 rounded-lg flex items-center justify-between
          ${theme === 'light' 
            ? 'bg-white hover:bg-gray-50 border border-gray-200' 
            : 'bg-gray-800 hover:bg-gray-700 border border-gray-700'
          }
        `}
      >
        <div className="flex items-center space-x-2">
          <span>{getButtonText()}</span>
          {selectedGenres.size > 0 && (
            <span className="ml-2 px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 text-xs">
              {selectedGenres.size}
            </span>
          )}
        </div>
        {isOpen ? (
          <ChevronUp className={`w-4 h-4 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
        ) : (
          <ChevronDown className={`w-4 h-4 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
        )}
      </button>

      {isOpen && (
        <div className={`
          absolute z-50 mt-2 w-96 rounded-lg shadow-lg
          ${theme === 'light' 
            ? 'bg-white border border-gray-200' 
            : 'bg-gray-800 border border-gray-700'
          }
        `}>
          <div className="p-2 space-y-1 max-h-60 overflow-y-auto">
            <div className="grid grid-cols-3 gap-2">
              {ALL_GENRES.map((genre) => (
                <label
                  key={genre}
                  className="flex items-center space-x-2 cursor-pointer group"
                >
                  <input
                    type="checkbox"
                    checked={selectedGenres.has(genre)}
                    onChange={(e) => handleGenreChange(genre, e.target.checked)}
                    className={`
                      w-4 h-4 rounded transition-colors
                      ${theme === 'light'
                        ? 'border-gray-300 text-blue-600 focus:ring-blue-500'
                        : 'border-gray-600 text-blue-500 focus:ring-blue-500 bg-gray-800'
                      }
                    `}
                  />
                  <span className={`
                    text-sm whitespace-nowrap transition-colors duration-200
                    ${theme === 'light'
                      ? 'text-gray-700 group-hover:text-blue-600'
                      : 'text-gray-200 group-hover:text-blue-400'
                    }
                  `}>
                    {genre}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GenreFilter;