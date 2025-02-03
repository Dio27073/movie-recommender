// src/components/ui/Navbar.tsx
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ThemeToggle } from './ThemeToggle';
import { BookMarked, Home, User, Film } from 'lucide-react';

const Navbar = () => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-0">
        
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold text-blue-600 dark:text-blue-500 mr-2 px-0 py-0">
              MovieApp
            </Link>
          </div>

          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <>
                <Link
                  to="/browse"
                  className="text-gray-700 dark:text-gray-200 hover:text-blue-600 dark:hover:text-blue-500 px-0 py-0" 
                >
                  Browse
                </Link>
                <Link
                  to="/recommendations"
                  className="text-gray-700 dark:text-gray-200 hover:text-blue-600 dark:hover:text-blue-500 px-0 py-0" 
                >
                  AI
                </Link>
                
                <Link 
                to="/library" 
                className="flex items-center space-x-1 px-3 py-2 rounded-md hover:bg-accent"
                >
                <BookMarked className="w-4 h-4" />
                <span>My Library</span>
              </Link>

                <button
                  onClick={handleLogout}
                  className="text-gray-700 dark:text-gray-200 hover:text-blue-600 dark:hover:text-blue-500"
                >
                  Logout
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="text-gray-700 dark:text-gray-200 hover:text-blue-600 dark:hover:text-blue-500 px-0 py-0" 
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="px-3 py-1 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors text-sm"
                >
                  Register
                </Link>
              </div>
            )}
            <ThemeToggle />
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;