import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import axios from 'axios';

// Define types for our context
interface AuthContextType {
  isAuthenticated: boolean;
  user: string | null;
  userRole: string | null;  // Add userRole property
  login: (username: string, password: string) => Promise<boolean>;
  register: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  error: string | null;
}

// Create the context with a default value
const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
  userRole: null,  // Add default value for userRole
  login: async () => false,
  register: async () => false,
  logout: () => {},
  error: null,
});

// Custom hook to use the auth context
export const useAuth = () => useContext(AuthContext);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);  // Add state for userRole
  const [error, setError] = useState<string | null>(null);

  // Check if user is already authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await axios.get('/api/check-auth', { withCredentials: true });
        if (response.data.authenticated) {
          setIsAuthenticated(true);
          setUser(response.data.usuario);
          setUserRole(response.data.permisos);  // Set userRole from response
        }
      } catch (err) {
        // User is not authenticated, that's okay
        console.log('No active session');
      }
    };

    checkAuth();
  }, []);

  // Login function
  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      setError(null);
      const response = await axios.post('/api/login', { username, password }, { withCredentials: true });

      if (response.data.usuario) {
        setIsAuthenticated(true);
        setUser(response.data.usuario);
        setUserRole(response.data.permisos);  // Set userRole from response
        return true;
      }

      return false;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al iniciar sesión');
      return false;
    }
  };

  // Register function
  const register = async (username: string, password: string): Promise<boolean> => {
    try {
      setError(null);
      const response = await axios.post('/api/register', { username, password });

      if (response.status === 200) {
        return true;
      }

      return false;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al registrarse');
      return false;
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await axios.post('/api/logout', {}, { withCredentials: true });
    } catch (err) {
      console.error('Error during logout:', err);
    } finally {
      setIsAuthenticated(false);
      setUser(null);
      setUserRole(null);  // Clear userRole on logout
    }
  };

  // Provide the context value
  const value = {
    isAuthenticated,
    user,
    userRole,  // Include userRole in the context value
    login,
    register,
    logout,
    error,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
