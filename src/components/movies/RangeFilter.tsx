import { Box, Slider } from '@mui/material';
import { styled } from '@mui/material/styles';

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

// Custom styled slider to match your dark theme
const CustomSlider = styled(Slider)(({  }) => ({
  color: '#3b82f6', // blue-500
  height: 4,
  padding: '15px 0',
  '& .MuiSlider-thumb': {
    height: 16,
    width: 16,
    backgroundColor: '#3b82f6',
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
    backgroundColor: '#1f2937', // gray-800
    borderRadius: 6,
    color: '#e5e7eb', // gray-200
    padding: '4px 8px',
  },
  '& .MuiSlider-track': {
    border: 'none',
    height: 4,
  },
  '& .MuiSlider-rail': {
    opacity: 0.3,
    backgroundColor: '#6b7280', // gray-500
    height: 4,
  },
  '& .MuiSlider-mark': {
    backgroundColor: '#6b7280',
    height: 8,
    width: 1,
    '&.MuiSlider-markActive': {
      opacity: 1,
      backgroundColor: 'currentColor',
    },
  },
}));

const RangeFilter = ({ 
  label, 
  icon, 
  value, 
  min, 
  max, 
  step = 1,
  onChange,
  showMinMax
}: RangeFilterProps) => (
  <div className="space-y-2">
    <label className="flex items-center space-x-2 text-sm font-medium text-gray-300">
      {icon}
      <span>{label}: {value[0]} - {value[1]}</span>
    </label>
    <Box className="px-2 py-4">
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
      <div className="flex justify-between text-xs text-gray-400">
      </div>
    )}
  </div>
);

export default RangeFilter;