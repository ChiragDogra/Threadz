"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { Search, Filter } from "lucide-react";

interface Design {
  design_id: string;
  design_name: string;
  image_url: string;
  tags: string | null;
}

export default function ExplorePage() {
  const [designs, setDesigns] = useState<Design[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Mock data for now since API might not be ready
    const mockDesigns: Design[] = [
      {
        design_id: 'design-001',
        design_name: 'Cool Tiger',
        image_url: '/api/placeholder/tiger-design.jpg',
        tags: 'animal, cool, trendy'
      },
      {
        design_id: 'design-002',
        design_name: 'Abstract Waves',
        image_url: '/api/placeholder/waves-design.jpg',
        tags: 'abstract, modern, blue'
      },
      {
        design_id: 'design-003',
        design_name: 'Minimal Logo',
        image_url: '/api/placeholder/logo-design.jpg',
        tags: 'minimal, brand, simple'
      }
    ];
    
    setDesigns(mockDesigns);
    setIsLoading(false);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-slate-900 dark:via-teal-800 dark:to-purple-900 px-4 py-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-purple-900 dark:text-cream-100">Explore Community Designs</h1>
          <p className="text-purple-700 dark:text-cream-200 mt-2">Discover and print trending designs created by the Threadz community.</p>
        </div>
        
        <div className="flex gap-3 w-full md:w-auto">
          <div className="relative flex-grow md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-purple-400 dark:text-purple-300 w-5 h-5" />
            <input 
              type="text" 
              placeholder="Search concepts..." 
              className="w-full pl-10 pr-4 py-2 border border-purple-300 dark:border-purple-600 rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white/90 dark:bg-gray-800/90 text-purple-900 dark:text-cream-100 placeholder-purple-500 dark:placeholder-purple-400"
            />
          </div>
          <button className="flex items-center justify-center h-10 px-4 border border-purple-300 dark:border-purple-600 rounded-full bg-white dark:bg-gray-800 hover:bg-purple-100 dark:hover:bg-purple-700 transition-colors text-purple-700 dark:text-purple-300 font-medium text-sm">
            <Filter className="w-4 h-4 mr-2" /> Filters
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 dark:border-purple-400"></div>
        </div>
      ) : designs.length === 0 ? (
        <div className="text-center py-20 bg-white/50 dark:bg-gray-800/50 rounded-2xl border border-purple-100 dark:border-purple-700">
          <div className="text-4xl mb-4">🎨</div>
          <h3 className="text-xl font-bold text-purple-900 dark:text-cream-100 mb-2">No designs found</h3>
          <p className="text-purple-700 dark:text-cream-200">Be the first to upload a public design!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {designs.map((design) => (
            <div key={design.design_id} className="group relative bg-white dark:bg-gray-800 rounded-2xl overflow-hidden shadow-lg border border-purple-200 dark:border-purple-700 hover:shadow-xl transition-all duration-300">
              <div className="aspect-square relative bg-purple-100 dark:bg-purple-900 overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-200/20 to-pink-200/20 dark:from-purple-800/20 dark:to-pink-800/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[2px]">
                  <button className="bg-white dark:bg-gray-800 text-purple-900 dark:text-purple-100 font-bold py-2 px-6 rounded-full shadow-lg transform translate-y-4 group-hover:translate-y-0 transition-all duration-300">
                     Use This Design
                  </button>
                </div>
              </div>
              <div className="p-4">
                <h3 className="font-bold text-purple-900 dark:text-cream-100 truncate">{design.design_name}</h3>
                <div className="flex flex-wrap gap-2 mt-2">
                  {design.tags?.split(',').map(tag => (
                    <span key={tag} className="text-[10px] uppercase font-bold tracking-wider bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 px-2 py-1 rounded-sm">
                      {tag.trim()}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
