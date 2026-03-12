'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useThemeStore } from '@/store/themeStore';

export default function SignupForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);
  
  const { signup } = useAuthStore();
  const { theme } = useThemeStore();
  const router = useRouter();

  const checkPasswordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (/[A-Z]/.test(password)) strength += 25;
    if (/[0-9]/.test(password)) strength += 25;
    if (/[^A-Za-z0-9]/.test(password)) strength += 25;
    setPasswordStrength(strength);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }

    try {
      await signup(email, password, fullName);
      router.push('/account');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-slate-900 dark:via-teal-800 dark:to-purple-900 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-2xl border border-purple-200/50 dark:border-teal-200/50 p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-cream-100 mb-2">Create Account</h2>
            <p className="text-slate-600 dark:text-cream-200">Join Threadz and start designing</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-200 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-slate-700 dark:text-cream-200 mb-2">
                Full Name
              </label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3 py-2 border border-purple-300 dark:border-teal-300 rounded-lg bg-white/90 dark:bg-gray-700/90 text-slate-900 dark:text-cream-100 placeholder-purple-500 dark:placeholder-teal-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Enter your full name"
                required
              />
            </div>

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
                onChange={(e) => {
                  setPassword(e.target.value);
                  checkPasswordStrength(e.target.value);
                }}
                className="w-full px-3 py-2 border border-purple-300 dark:border-teal-300 rounded-lg bg-white/90 dark:bg-gray-700/90 text-slate-900 dark:text-cream-100 placeholder-purple-500 dark:placeholder-teal-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Create a password"
                required
              />
              {password && (
                <div className="mt-2">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-slate-600 dark:text-cream-200">Password Strength</span>
                    <span className={`text-xs font-medium ${
                      passwordStrength < 25 ? 'text-red-600 dark:text-red-400' :
                      passwordStrength < 50 ? 'text-yellow-600 dark:text-yellow-400' :
                      passwordStrength < 75 ? 'text-orange-600 dark:text-orange-400' :
                      'text-green-600 dark:text-green-400'
                    }`}>
                      {passwordStrength < 25 ? 'Weak' :
                       passwordStrength < 50 ? 'Fair' :
                       passwordStrength < 75 ? 'Good' : 'Strong'}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        passwordStrength < 25 ? 'bg-red-500 dark:bg-red-400 w-1/4' :
                        passwordStrength < 50 ? 'bg-yellow-500 dark:bg-yellow-400 w-2/4' :
                        passwordStrength < 75 ? 'bg-orange-500 dark:bg-orange-400 w-3/4' :
                        'bg-green-500 dark:bg-green-400 w-full'
                      }`}
                    />
                  </div>
                </div>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-700 dark:text-cream-200 mb-2">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3 py-2 border border-purple-300 dark:border-teal-300 rounded-lg bg-white/90 dark:bg-gray-700/90 text-slate-900 dark:text-cream-100 placeholder-purple-500 dark:placeholder-teal-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Confirm your password"
                required
              />
            </div>

            <div className="flex items-center">
              <input
                id="terms"
                type="checkbox"
                className="h-4 w-4 text-purple-600 dark:text-teal-600 bg-purple-100 dark:bg-teal-100 border-purple-300 dark:border-teal-300 rounded focus:ring-purple-500 dark:focus:ring-teal-500"
              />
              <label htmlFor="terms" className="ml-2 block text-sm text-slate-600 dark:text-cream-200">
                I agree to the Terms & Conditions
              </label>
            </div>

            <div className="flex items-center">
              <input
                id="newsletter"
                type="checkbox"
                className="h-4 w-4 text-purple-600 dark:text-teal-600 bg-purple-100 dark:bg-teal-100 border-purple-300 dark:border-teal-300 rounded focus:ring-purple-500 dark:focus:ring-teal-500"
              />
              <label htmlFor="newsletter" className="ml-2 block text-sm text-slate-600 dark:text-cream-200">
                Subscribe to newsletter
              </label>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 dark:from-teal-600 dark:to-orange-500 text-white py-3 px-4 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 dark:hover:from-teal-700 dark:hover:to-orange-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
            >
              {isLoading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-600 dark:text-cream-200">
              Already have an account?{' '}
              <a href="/login" className="font-medium text-purple-600 dark:text-teal-600 hover:text-purple-500 dark:hover:text-teal-500">
                Sign in
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
