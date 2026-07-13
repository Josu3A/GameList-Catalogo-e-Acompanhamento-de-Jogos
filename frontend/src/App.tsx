import { Routes, Route } from 'react-router-dom';

import { Layout } from './components/Layout';
import { RequireAuth, RequireAdmin } from './auth/guards';

import { HomePage } from './pages/catalog/HomePage';
import { CatalogPage } from './pages/catalog/CatalogPage';
import { GameDetailPage } from './pages/catalog/GameDetailPage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { MyListPage } from './pages/library/MyListPage';
import { ProfilePage } from './pages/profile/ProfilePage';
import { EditProfilePage } from './pages/profile/EditProfilePage';
import { AdminGamesPage } from './pages/admin/AdminGamesPage';
import { AdminGameFormPage } from './pages/admin/AdminGameFormPage';
import { AdminTaxonomyPage } from './pages/admin/AdminTaxonomyPage';
import { FriendsPage } from './pages/social/FriendsPage';
import { NotificationsPage } from './pages/social/NotificationsPage';
import { ListsPage } from './pages/social/ListsPage';
import { ListDetailPage } from './pages/social/ListDetailPage';
import { NotFoundPage } from './pages/NotFoundPage';

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        {/* Público */}
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/games" element={<CatalogPage />} />
        <Route path="/games/:id" element={<GameDetailPage />} />
        <Route path="/users/:slug" element={<ProfilePage />} />

        {/* Usuário autenticado */}
        <Route
          path="/my-list"
          element={
            <RequireAuth>
              <MyListPage />
            </RequireAuth>
          }
        />
        <Route
          path="/settings/profile"
          element={
            <RequireAuth>
              <EditProfilePage />
            </RequireAuth>
          }
        />
        <Route
          path="/friends"
          element={
            <RequireAuth>
              <FriendsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/notifications"
          element={
            <RequireAuth>
              <NotificationsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/lists"
          element={
            <RequireAuth>
              <ListsPage />
            </RequireAuth>
          }
        />
        <Route path="/lists/:id" element={<ListDetailPage />} />

        {/* Admin */}
        <Route
          path="/admin/games"
          element={
            <RequireAdmin>
              <AdminGamesPage />
            </RequireAdmin>
          }
        />
        <Route
          path="/admin/games/new"
          element={
            <RequireAdmin>
              <AdminGameFormPage />
            </RequireAdmin>
          }
        />
        <Route
          path="/admin/games/:id/edit"
          element={
            <RequireAdmin>
              <AdminGameFormPage />
            </RequireAdmin>
          }
        />
        <Route
          path="/admin/taxonomies"
          element={
            <RequireAdmin>
              <AdminTaxonomyPage />
            </RequireAdmin>
          }
        />

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
