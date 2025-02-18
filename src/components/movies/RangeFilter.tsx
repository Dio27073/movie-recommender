import { Box, Slider, styled } from '@mui/material';
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

const CustomSlider = styled(Slider)(({ }) => ({
  color: '#1d2854',
  height: 4,
  padding: '15px 0',
  '& .MuiSlider-thumb': {
    height: 16,
    width: 16,
    backgroundColor: '#fff',
    border: '2px solid currentColor',
    '&:hover': {
      boxShadow: '0 0 0 8px rgba(59, 130, 246, 0.16)',
    },
    '&.Mui-active': {
      boxShadow: '0 0 0 12px rgba(59, 130, 246, 0.16)',
    },
  },
  '& .MuiSlider-valueLabel': {
    lineHeight: 1.2,
    fontSize: 12,
    background: 'unset',
    padding: 0,
    width: 32,
    height: 32,
    borderRadius: '50% 50% 50% 0',
    backgroundColor: '#1d2854',
    transformOrigin: 'bottom left',
    transform: 'translate(50%, -100%) rotate(-45deg) scale(0)',
    '&:before': { display: 'none' },
    '&.MuiSlider-valueLabelOpen': {
      transform: 'translate(50%, -100%) rotate(-45deg) scale(1)',
    },
    '& > *': {
      transform: 'rotate(45deg)',
      color: '#fff',
    },
  },
  '& .MuiSlider-track': {
    border: 'none',
    height: 4,
  },
  '& .MuiSlider-rail': {
    opacity: 0.3,
    backgroundColor: '#9ca3af',
    height: 4,
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
}: RangeFilterProps) => {
  const { theme } = useTheme();
  
  const handleChange = (_event: Event, newValue: number | number[]) => {
    onChange(newValue as [number, number]);
  };

  return (
    <div className="w-full">
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
          onChange={handleChange}
          valueLabelDisplay="auto"
          min={min}
          max={max}
          step={step}
          marks={showMinMax ? [
            { value: min, label: min.toString() },
            { value: max, label: max.toString() }
          ] : undefined}
        />
      </Box>
    </div>
  );
};

export default RangeFilter;