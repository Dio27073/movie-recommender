import React from 'react';
import { MovieFilterProps, SortOption } from '../../features/movies/types';
import Box from '@mui/material/Box';
import Slider from '@mui/material/Slider';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Chip from '@mui/material/Chip';

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'release_date_desc', label: 'Release Date (Newest)' },
  { value: 'release_date_asc', label: 'Release Date (Oldest)' },
  { value: 'rating_desc', label: 'Rating (High to Low)' },
  { value: 'rating_asc', label: 'Rating (Low to High)' },
  { value: 'title_asc', label: 'Title (A-Z)' },
  { value: 'title_desc', label: 'Title (Z-A)' },
];

export const MovieFilter: React.FC<MovieFilterProps> = ({ 
  genres, 
  selectedGenres, 
  yearRange,
  minRating,
  sortBy,
  onFilterChange,
  minYear,
  maxYear
}) => {
  const handleGenreChange = (event: any) => {
    const value = event.target.value;
    onFilterChange('genres', { 
      genre: value, 
      checked: !selectedGenres.has(value) 
    });
  };

  const handleSortChange = (event: any) => {
    onFilterChange('sort', event.target.value as SortOption);
  };

  return (
    <div className="bg-white shadow-sm p-4 mb-6 rounded-lg">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex flex-col w-[150px]">
          <div className="text-sm font-medium mb-1">Genre</div>
          <FormControl size="small">
            <Select
              value=""
              onChange={handleGenreChange}
              displayEmpty
            >
              {genres.map((genre) => (
                <MenuItem 
                  key={genre} 
                  value={genre}
                  disabled={selectedGenres.has(genre)}
                >
                  {genre}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </div>

        <div className="flex flex-col w-[200px]">
          <div className="text-sm font-medium mb-1">Sort By</div>
          <FormControl size="small">
            <Select
              value={sortBy}
              onChange={handleSortChange}
            >
              {sortOptions.map((option) => (
                <MenuItem 
                  key={option.value} 
                  value={option.value}
                >
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </div>

        <div className="flex-1 flex flex-wrap gap-2">
          {Array.from(selectedGenres).map((genre) => (
            <Chip
              key={genre}
              label={genre}
              onDelete={() => onFilterChange('genres', { genre, checked: false })}
              size="small"
            />
          ))}
        </div>

        <Box className="w-[200px]">
          <div className="text-sm font-medium mb-1">Year: {yearRange[0]} - {yearRange[1]}</div>
          <Slider
            value={yearRange}
            onChange={(_, newValue) => onFilterChange('yearRange', newValue as [number, number])}
            min={minYear}
            max={maxYear}
            size="small"
          />
        </Box>

        <Box className="w-[150px]">
          <div className="text-sm font-medium mb-1">Min Rating: {minRating}</div>
          <Slider
            value={minRating}
            onChange={(_, newValue) => onFilterChange('minRating', newValue as number)}
            min={0}
            max={5}
            step={0.5}
            size="small"
          />
        </Box>
      </div>
    </div>
  );
};