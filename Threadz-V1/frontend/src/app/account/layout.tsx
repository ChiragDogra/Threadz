'use client';

import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import RoleBadge from '@/components/ui/RoleBadge';
import ThemeToggle from '@/components/ui/ThemeToggle';

export default function AccountLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 dark:border-teal-600"></div>
          <p className="mt-4 text-slate-600 dark:text-cream-200">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold text-slate-900 dark:text-cream-100">
                Threadz Account
              </h1>
              <RoleBadge />
            </div>
            
            <div className="flex items-center gap-4">
              <ThemeToggle />
              
              <div className="relative">
                <button
                  onClick={() => {
                    // Toggle dropdown
                    const dropdown = document.getElementById('account-dropdown');
                    dropdown?.classList.toggle('hidden');
                  }}
                  className="flex items-center gap-2 p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  <span className="text-sm font-medium text-slate-700 dark:text-cream-200">
                    {user.name}
                  </span>
                  <svg className="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0l4-4a1 1 0 01.414 0l4 4a1 1 0 01-.414-.414L10.586 9.414a1 1 0 01-.414.414l-4-4a1 1 0 01-.414-.414L5.293 7.293z" clipRule="evenodd" />
                  </svg>
                </button>
                
                {/* Dropdown Menu */}
                <div id="account-dropdown" className="hidden absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                  <div className="py-1">
                    <a
                      href="/account"
                      className="block px-4 py-2 text-sm text-gray-700 dark:text-cream-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Dashboard
                    </a>
                    <a
                      href="/account/profile"
                      className="block px-4 py-2 text-sm text-gray-700 dark:text-cream-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Profile
                    </a>
                    <hr className="my-1 border-gray-200 dark:border-gray-700" />
                    <button
                      onClick={logout}
                      className="block w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Logout
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
