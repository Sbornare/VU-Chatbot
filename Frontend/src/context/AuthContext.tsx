import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  email: string;
  name: string;
  phone_number?: string;
  interested_programs?: string;
  whatsapp_notifications_enabled?: boolean;
  role: 'student' | 'admin';
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (name: string, email: string, password: string, phone: string, whatsapp_notifications: boolean, interested_programs?: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('college_agent_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    // Accept any email/password - works offline without backend
    if (email && password) {
      const newUser: User = {
        id: Date.now().toString(),
        email,
        name: email.split('@')[0],
        phone_number: '',
        role: email.includes('admin') ? 'admin' : 'student',
      };
      setUser(newUser);
      localStorage.setItem('college_agent_user', JSON.stringify(newUser));
      return true;
    }

    return false;
  };

  const register = async (name: string, email: string, password: string, phone: string, whatsapp_notifications: boolean, interested_programs?: string): Promise<boolean> => {
    // Accept any registration - works offline without backend
    if (name && email && password) {
      const newUser: User = {
        id: Date.now().toString(),
        email,
        name,
        phone_number: phone,
        interested_programs,
        whatsapp_notifications_enabled: whatsapp_notifications,
        role: email.includes('admin') ? 'admin' : 'student',
      };
      
      setUser(newUser);
      localStorage.setItem('college_agent_user', JSON.stringify(newUser));
      return true;
    }
    
    return false;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('college_agent_user');
    localStorage.removeItem('access_token');
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};
