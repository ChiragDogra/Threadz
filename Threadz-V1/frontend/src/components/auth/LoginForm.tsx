'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useThemeStore } from '@/store/themeStore';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuthStore();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await login(email, password);
      router.push('/account');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-slate-900 dark:via-teal-800 dark:to-purple-900 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-2xl border border-purple-200/50 dark:border-teal-200/50 p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-cream-100 mb-2">Welcome Back</h2>
            <p className="text-slate-600 dark:text-cream-200">Sign in to your Threadz account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-200 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 dark:text-cream-200 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-purple-300 dark:border-teal-300 rounded-lg bg-white/90 dark:bg-gray-700/90 text-slate-900 dark:text-cream-100 placeholder-purple-500 dark:placeholder-teal-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Enter your email"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 dark:text-cream-200 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-purple-300 dark:border-teal-300 rounded-lg bg-white/90 dark:bg-gray-700/90 text-slate-900 dark:text-cream-100 placeholder-purple-500 dark:placeholder-teal-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Enter your password"
                required
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember"
                  type="checkbox"
                  className="h-4 w-4 text-purple-600 dark:text-teal-600 bg-purple-100 dark:bg-teal-100 border-purple-300 dark:border-teal-300 rounded focus:ring-purple-500 dark:focus:ring-teal-500"
                />
                <label htmlFor="remember" className="ml-2 block text-sm text-slate-600 dark:text-cream-200">
                  Remember me
                </label>
              </div>
              <a href="/forgot-password" className="text-sm text-purple-600 dark:text-teal-600 hover:text-purple-500 dark:hover:text-teal-500">
                Forgot password?
              </a>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 dark:from-teal-600 dark:to-orange-500 text-white py-3 px-4 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 dark:hover:from-teal-700 dark:hover:to-orange-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-600 dark:text-cream-200">
              Don't have an account?{' '}
              <a href="/signup" className="font-medium text-purple-600 dark:text-teal-600 hover:text-purple-500 dark:hover:text-teal-500">
                Sign up
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
