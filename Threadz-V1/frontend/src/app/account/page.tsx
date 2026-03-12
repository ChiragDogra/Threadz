'use client';

import { useAuthStore } from '@/store/authStore';
import UserDashboard from '@/components/account/UserDashboard';
import AdminDashboard from '@/components/account/AdminDashboard';

export default function AccountPage() {
  const { user } = useAuthStore();

  if (!user) return null;

  return user.role === 'admin' ? <AdminDashboard /> : <UserDashboard />;
}
