'use client';

import Link from "next/link";
import FloatingClothes from "@/components/home/floating-clothes";

export default function Home() {
  return (
    <div className="flex-1 w-full bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-slate-900 dark:via-teal-800 dark:to-purple-900 flex flex-col items-center justify-center relative overflow-hidden text-center px-4 py-16 min-h-screen">
      
      {/* Floating clothes animation */}
      <FloatingClothes />
      
      {/* Enhanced decorative gradient background circles */}
      <div className="absolute top-0 right-0 -mr-32 -mt-32 w-96 h-96 rounded-full bg-gradient-to-br from-purple-300/30 to-pink-300/30 blur-3xl pointer-events-none animate-pulse" />
      <div className="absolute bottom-0 left-0 -ml-32 -mb-32 w-96 h-96 rounded-full bg-gradient-to-br from-rose-300/30 to-pink-300/30 blur-3xl pointer-events-none animate-pulse" style={{ animationDelay: '2s' }} />
      <div className="absolute top-1/2 left-1/2 -ml-20 -mt-20 w-96 h-96 rounded-full bg-gradient-to-br from-yellow-200/20 to-orange-300/20 blur-3xl pointer-events-none animate-pulse" style={{ animationDelay: '4s' }} />

      {/* Main content with enhanced styling */}
      <div className="relative z-10 max-w-6xl mx-auto flex flex-col items-center">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-purple-900 dark:text-cream-100 mb-6 drop-shadow-2xl text-center">
          Create Your Own <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 animate-gradient">Fashion</span>
        </h1>
        <p className="max-w-[42rem] leading-normal text-purple-700 dark:text-cream-200 sm:text-xl sm:leading-8 mb-10 drop-shadow-lg text-center">
          Upload your design, explore community creations, or describe your vision and let our AI bring it to life on premium garments.
        </p>

        {/* Enhanced buttons with better positioning */}
        <div className="flex flex-col sm:flex-row gap-6 mb-16 items-center justify-center relative z-20">
          <Link href="/design" className="group inline-flex h-14 items-center justify-center rounded-full bg-gradient-to-r from-purple-600 to-pink-600 px-8 text-sm font-semibold text-white shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 hover:from-purple-700 hover:to-pink-700">
            <span className="relative z-10">Start Designing Now</span>
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          </Link>
          <Link href="/explore" className="group inline-flex h-14 items-center justify-center rounded-full border-2 border-purple-200/80 bg-white/90 backdrop-blur-sm px-8 text-sm font-semibold text-purple-800 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 hover:bg-white">
            Explore Designs
          </Link>
        </div>
        
        {/* Enhanced Three Pathways Preview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl w-full z-10 mt-10">
          <div className="group flex flex-col items-center bg-white/80 backdrop-blur-sm p-8 rounded-3xl shadow-xl border border-purple-100/50 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:bg-white/90">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-purple-200 text-purple-600 rounded-full flex items-center justify-center mb-4 text-2xl group-hover:scale-110 transition-transform duration-300">🎨</div>
            <h3 className="text-xl font-bold text-purple-900 mb-2 group-hover:text-purple-600 transition-colors">Upload Design</h3>
            <p className="text-purple-600 text-sm">Have your own artwork? Upload it in seconds and preview it on any garment.</p>
          </div>
          <div className="group flex flex-col items-center bg-white/80 backdrop-blur-sm p-8 rounded-3xl shadow-xl border border-pink-100/50 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:bg-white/90">
            <div className="w-16 h-16 bg-gradient-to-br from-pink-100 to-rose-200 text-pink-600 rounded-full flex items-center justify-center mb-4 text-2xl group-hover:scale-110 transition-transform duration-300">🌍</div>
            <h3 className="text-xl font-bold text-purple-900 mb-2 group-hover:text-pink-600 transition-colors">Explore Community</h3>
            <p className="text-purple-600 text-sm">Discover trending styles and graphics made by other creators from around the world.</p>
          </div>
          <div className="group flex flex-col items-center bg-white/80 backdrop-blur-sm p-8 rounded-3xl shadow-xl border border-yellow-100/50 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:bg-white/90 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-yellow-50 to-orange-50 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="w-16 h-16 bg-gradient-to-br from-yellow-100 to-orange-200 text-orange-600 rounded-full flex items-center justify-center mb-4 text-2xl z-10 group-hover:scale-110 transition-transform duration-300">✨</div>
            <h3 className="text-xl font-bold text-purple-900 mb-2 z-10 group-hover:text-orange-600 transition-colors">AI Generation</h3>
            <span className="absolute top-2 right-2 bg-gradient-to-r from-yellow-300 to-orange-400 text-orange-900 text-xs font-bold px-3 py-1 rounded-full shadow-lg z-10 animate-pulse">PREMIUM</span>
            <p className="text-purple-600 text-sm z-10">Describe what you want to see, and let Stable Diffusion AI generate unique, breathtaking prints.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
