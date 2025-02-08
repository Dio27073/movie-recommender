import { Box, Slider } from '@mui/material';
import { styled } from '@mui/material/styles';
import { useTheme } from '../../features/theme/themeContext';

interface RangeFilterProps {
  label: string;
  icon: React.ReactNode;
  value: [number, number];
  min: number;
  max: number;
  step?: number;
  onChange: (values: [number, number]) => void;
  showMinMax?: boolean;
}

const RangeFilter = ({ 
  label, 
  icon, 
  value, 
  min, 
  max, 
  step = 1,
  onChange,
  showMinMax
}: RangeFilterProps) => {
  const { theme } = useTheme();

  // Custom styled slider with theme support
  const CustomSlider = styled(Slider)(() => ({
    color: '#3b82f6', // blue-500 for both themes
    height: 4,
    padding: '15px 0',
    '& .MuiSlider-thumb': {
      height: 16,
      width: 16,
      backgroundColor: theme === 'light' ? '#fff' : '#3b82f6',
      border: '2px solid currentColor',
      '&:hover': {
        boxShadow: '0 0 0 8px rgba(59, 130, 246, 0.16)',
      },
      '&.Mui-active': {
        boxShadow: '0 0 0 12px rgba(59, 130, 246, 0.16)',
      },
    },
    '& .MuiSlider-valueLabel': {
      fontSize: 12,
      fontWeight: 'normal',
      top: -6,
      backgroundColor: theme === 'light' ? '#fff' : '#1f2937',
      borderRadius: 6,
      color: theme === 'light' ? '#1f2937' : '#e5e7eb',
      padding: '4px 8px',
      border: theme === 'light' ? '1px solid #e5e7eb' : 'none',
    },
    '& .MuiSlider-track': {
      border: 'none',
      height: 4,
    },
    '& .MuiSlider-rail': {
      opacity: 0.3,
      backgroundColor: theme === 'light' ? '#9ca3af' : '#6b7280',
      height: 4,
    },
    '& .MuiSlider-mark': {
      backgroundColor: theme === 'light' ? '#9ca3af' : '#6b7280',
      height: 8,
      width: 1,
      '&.MuiSlider-markActive': {
        opacity: 1,
        backgroundColor: 'currentColor',
      },
    },
  }));

  return (
    <div>
      <label className={`
        flex items-center space-x-2 text-sm font-medium mb-2
        ${theme === 'light' ? 'text-gray-700' : 'text-gray-300'}
      `}>
        {icon}
        <span>{label}: {value[0]} - {value[1]}</span>
      </label>
      <Box className="px-2 py-1">
        <CustomSlider
          value={value}
          onChange={(_, newValue) => onChange(newValue as [number, number])}
          valueLabelDisplay="auto"
          min={min}
          max={max}
          step={step}
        />
      </Box>
      {showMinMax && (
        <div className={`
          flex justify-between text-xs mt-1 px-2
          ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'}
        `}>
          <span>{min}</span>
          <span>{max}</span>
        </div>
      )}
    </div>
  );
};

export default RangeFilter;