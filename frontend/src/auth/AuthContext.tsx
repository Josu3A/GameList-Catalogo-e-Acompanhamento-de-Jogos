import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import {
  fetchMe,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
  type LoginPayload,
  type RegisterPayload,
} from '../api/auth';
import { ensureCsrf } from '../api/client';
import type { User } from '../types';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isAdmin: boolean;
  login: (p: LoginPayload) => Promise<void>;
  register: (p: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Garante o cookie CSRF e descobre se já há sessão.
    ensureCsrf()
      .then(fetchMe)
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  async function login(p: LoginPayload) {
    setUser(await apiLogin(p));
  }

  async function register(p: RegisterPayload) {
    await apiRegister(p);
    // O registro não cria sessão — logamos em seguida para uma UX contínua.
    setUser(await apiLogin({ email: p.email, password: p.password }));
  }

  async function logout() {
    await apiLogout();
    setUser(null);
  }

  async function refresh() {
    setUser(await fetchMe().catch(() => null));
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAdmin: user?.tipo_usuario === 'admin',
        login,
        register,
        logout,
        refresh,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth precisa de <AuthProvider>.');
  return ctx;
}
