// src/components/ui/ViewSwitcher.tsx
import React from 'react';
import { Grid, List, AlignJustify } from 'lucide-react';

export type ViewType = 'grid' | 'list' | 'compact';

interface ViewSwitcherProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
}

export const ViewSwitcher: React.FC<ViewSwitcherProps> = ({
  currentView,
  onViewChange,
}) => {
  return (
    <div className="flex items-center gap-2 p-2 bg-white dark:bg-dark-secondary rounded-lg shadow">
      <button
        onClick={() => onViewChange('grid')}
        className={`p-2 rounded-md transition-colors ${
          currentView === 'grid'
            ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300'
            : 'hover:bg-gray-100 dark:hover:bg-gray-700'
        }`}
        aria-label="Grid view"
      >
        <Grid className="w-5 h-5" />
      </button>
      <button
        onClick={() => onViewChange('list')}
        className={`p-2 rounded-md transition-colors ${
          currentView === 'list'
            ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300'
            : 'hover:bg-gray-100 dark:hover:bg-gray-700'
        }`}
        aria-label="List view"
      >
        <List className="w-5 h-5" />
      </button>
      <button
        onClick={() => onViewChange('compact')}
        className={`p-2 rounded-md transition-colors ${
          currentView === 'compact'
            ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300'
            : 'hover:bg-gray-100 dark:hover:bg-gray-700'
        }`}
        aria-label="Compact view"
      >
        <AlignJustify className="w-5 h-5" />
      </button>
    </div>
  );
};
