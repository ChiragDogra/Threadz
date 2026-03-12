"use client";

import Link from "next/link";
import { useState } from "react";
import { ShoppingCart, Menu, X } from "lucide-react";
import MobileMenu from "@/components/home/mobile-menu";
import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/store/themeStore";
import ThemeToggle from "@/components/ui/ThemeToggle";

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const cartQuantity = 0; // TODO: Connect to cart store
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <>
      <nav className="sticky top-0 z-50 w-full bg-white/30 dark:bg-gray-900/30 backdrop-blur-xl border-b border-white/20 dark:border-gray-700/20 shadow-lg">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          {/* Logo on the left */}
          <Link href="/" className="text-3xl font-bold tracking-tighter bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent hover:from-purple-700 hover:to-pink-700 transition-colors">
            Threadz
          </Link>

          {/* Centered navigation items - Desktop only */}
          <div className="absolute left-1/2 transform -translate-x-1/2 hidden md:flex items-center gap-8">
            <Link href="/design" className="font-medium text-slate-700 dark:text-slate-300 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">
              Start Designing
            </Link>
            <Link href="/upload" className="font-medium text-slate-700 dark:text-slate-300 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">
              Upload Design
            </Link>
            <Link href="/explore" className="font-medium text-slate-700 dark:text-slate-300 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">
              Explore
            </Link>
            <Link href="/generate" className="font-medium text-slate-700 dark:text-slate-300 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">
              AI Generation
            </Link>
          </div>

          {/* Right side actions */}
          <div className="flex items-center gap-3">
            <ThemeToggle />
            
            <Link href="/cart" className="relative p-2 text-slate-700 dark:text-slate-300 hover:text-purple-600 dark:hover:text-purple-400 transition">
               <ShoppingCart className="w-5 h-5" />
               {cartQuantity > 0 && (
                 <span className="absolute top-0 right-0 inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold leading-none text-white transform translate-x-1/4 -translate-y-1/4 bg-purple-600 dark:bg-purple-500 rounded-full">
                   {cartQuantity}
                 </span>
               )}
            </Link>
            
            {/* Desktop auth buttons */}
            <div className="hidden md:flex items-center gap-3">
              {user ? (
                <div className="flex items-center gap-3">
                  {user.role === 'admin' && (
                    <Link href="/admin" className="text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition">
                      Admin
                    </Link>
                  )}
                  <Link href="/account" className="text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-purple-600 dark:hover:text-purple-400 transition">
                    Account
                  </Link>
                  <button 
                    onClick={logout}
                    className="text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-purple-600 dark:hover:text-purple-400 transition"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <>
                  <Link href="/login" className="text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition">
                    Log in
                  </Link>
                  <Link 
                    href="/signup" 
                    className="inline-flex h-9 items-center justify-center rounded-md bg-gradient-to-r from-purple-600 to-pink-600 px-4 py-2 text-sm font-medium text-white shadow hover:from-purple-700 hover:to-pink-700 transition-colors"
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-lg hover:bg-white/50 dark:hover:bg-gray-700/50 transition-colors"
            >
              <Menu className="w-5 h-5 text-slate-700 dark:text-slate-300" />
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile menu */}
      <MobileMenu isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} />
    </>
  );
}
