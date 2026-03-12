'use client';

import { Shield, Crown } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

export default function RoleBadge() {
  const { user } = useAuthStore();

  if (!user) return null;

  return (
    <div className="flex items-center gap-2">
      {user.role === 'admin' ? (
        <div className="flex items-center gap-1 px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded-full text-sm font-medium">
          <Crown className="h-3 w-3" />
          <span>Admin</span>
        </div>
      ) : (
        <div className="flex items-center gap-1 px-3 py-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-full text-sm font-medium">
          <Shield className="h-3 w-3" />
          <span>User</span>
        </div>
      )}
    </div>
  );
}
