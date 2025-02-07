import React from 'react';
import { Check, Film, Heart, Play } from 'lucide-react';
import { useTheme } from '../../features/theme/themeContext';
import { useState } from 'react';


interface MultiSelectFilterProps {
  label: string;
  icon: React.ReactNode;
  options: string[];
  selectedOptions: Set<string>;
  onChange: (selected: Set<string>) => void;
}

const MultiSelectFilter: React.FC<MultiSelectFilterProps> = ({
  label,
  icon,
  options,
  selectedOptions,
  onChange,
}) => {
  const { theme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  const handleToggleOption = (option: string) => {
    const newSelected = new Set(selectedOptions);
    if (newSelected.has(option)) {
      newSelected.delete(option);
    } else {
      newSelected.add(option);
    }
    onChange(newSelected);
  };

  return (
    <div className="relative">
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
          {icon}
          <span>{label}</span>
          {selectedOptions.size > 0 && (
            <span className="ml-2 px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 text-xs">
              {selectedOptions.size}
            </span>
          )}
        </div>
      </button>

      {isOpen && (
        <div className={`
          absolute z-50 mt-2 w-full rounded-lg shadow-lg
          ${theme === 'light' 
            ? 'bg-white border border-gray-200' 
            : 'bg-gray-800 border border-gray-700'
          }
        `}>
          <div className="p-2 space-y-1 max-h-60 overflow-y-auto">
            {options.map((option) => (
              <button
                key={option}
                onClick={() => handleToggleOption(option)}
                className={`
                  w-full px-3 py-2 rounded-md flex items-center justify-between
                  ${selectedOptions.has(option)
                    ? theme === 'light'
                      ? 'bg-blue-50 text-blue-700'
                      : 'bg-blue-900/30 text-blue-300'
                    : theme === 'light'
                      ? 'hover:bg-gray-100'
                      : 'hover:bg-gray-700'
                  }
                `}
              >
                <span>{option}</span>
                {selectedOptions.has(option) && <Check className="w-4 h-4" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export const ContentRatingFilter: React.FC<{
  selectedRatings: Set<string>;
  onChange: (selected: Set<string>) => void;
}> = ({ selectedRatings, onChange }) => {
  const contentRatings = ['G', 'PG', 'PG-13', 'R', 'NC-17'];
  
  return (
    <MultiSelectFilter
      label="Content Rating"
      icon={<Film className="w-4 h-4" />}
      options={contentRatings}
      selectedOptions={selectedRatings}
      onChange={onChange}
    />
  );
};

export const MoodFilter: React.FC<{
  selectedMoods: Set<string>;
  onChange: (selected: Set<string>) => void;
}> = ({ selectedMoods, onChange }) => {
  const moods = [
    'Feel-Good',
    'Romantic',
    'Intense',
    'Thought-Provoking',
    'Funny',
    'Dark',
    'Inspirational',
    'Relaxing'
  ];
  
  return (
    <MultiSelectFilter
      label="Mood"
      icon={<Heart className="w-4 h-4" />}
      options={moods}
      selectedOptions={selectedMoods}
      onChange={onChange}
    />
  );
};

export const StreamingFilter: React.FC<{
  selectedPlatforms: Set<string>;
  onChange: (selected: Set<string>) => void;
}> = ({ selectedPlatforms, onChange }) => {
  const platforms = [
    'Netflix',
    'Prime Video',
    'Hulu',
    'Disney+',
    'HBO Max',
    'Apple TV+',
    'Peacock'
  ];
  
  return (
    <MultiSelectFilter
      label="Streaming On"
      icon={<Play className="w-4 h-4" />}
      options={platforms}
      selectedOptions={selectedPlatforms}
      onChange={onChange}
    />
  );
};

export default {
  ContentRatingFilter,
  MoodFilter,
  StreamingFilter
};