import * as React from 'react';
import { createContext, useContext, useEffect, useState } from 'react';
import { ThemeProvider as NextThemesProvider, useTheme as useNextThemes } from 'next-themes';

interface ThemeContextType {
  theme: string;
  setTheme: (theme: string) => void;
  isDark: boolean;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <ThemeContextConsumer>{children}</ThemeContextConsumer>
    </NextThemesProvider>
  );
};

// Custom hook to use next-themes
const useNextTheme = () => {
  const { theme, setTheme, resolvedTheme } = useNextThemes();
  return { theme, setTheme, resolvedTheme };
};

const ThemeContextConsumer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { theme, setTheme, resolvedTheme } = useNextTheme();
  const isDark = resolvedTheme === 'dark';

  const toggleTheme = () => {
    setTheme(isDark ? 'light' : 'dark');
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, isDark, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
