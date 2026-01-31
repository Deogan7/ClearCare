import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import api from "../services/api";

interface AuthUser {
  id: string;
  role: string;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

function parseToken(token: string): AuthUser | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return { id: payload.sub, role: payload.role };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem("authToken")
  );
  const [user, setUser] = useState<AuthUser | null>(() => {
    const stored = localStorage.getItem("authToken");
    return stored ? parseToken(stored) : null;
  });

  useEffect(() => {
    if (token) {
      localStorage.setItem("authToken", token);
      setUser(parseToken(token));
    } else {
      localStorage.removeItem("authToken");
      setUser(null);
    }
  }, [token]);

  const login = async (username: string, password: string) => {
    const response = await api.post<{ access_token: string }>("/auth/login", {
      username,
      password,
    });
    setToken(response.data.access_token);
  };

  const logout = () => {
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
