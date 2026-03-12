'use client';

import { useState, useRef } from 'react';
import { Sparkles, Loader2, RefreshCw, Wand2, Download, Edit3, Search, ChevronDown, ShoppingCart, Palette, Image, Save, X, Plus, Minus, RotateCw, Move, Trash2, Type, Scissors } from 'lucide-react';
import Link from 'next/link';

interface GeneratedDesign {
  design_id: string;
  image_url: string;
  ai_prompt: string;
  ai_style: string;
}

interface ClothType {
  id: string;
  name: string;
  subTypes: ClothSubType[];
}

interface ClothSubType {
  id: string;
  name: string;
  qualities: ClothQuality[];
}

interface ClothQuality {
  id: string;
  name: string;
  price: number;
}

const clothTypes: ClothType[] = [
  {
    id: 'tshirt',
    name: 'T-Shirt',
    subTypes: [
      {
        id: 'crew-neck',
        name: 'Crew Neck',
        qualities: [
          { id: 'basic-cotton', name: 'Basic Cotton', price: 19.99 },
          { id: 'premium-cotton', name: 'Premium Cotton', price: 29.99 }
        ]
      },
      {
        id: 'henley',
        name: 'Henley',
        qualities: [
          { id: 'henley-cotton', name: 'Cotton Henley', price: 24.99 }
        ]
      }
    ]
  },
  {
    id: 'hoodie',
    name: 'Hoodie',
    subTypes: [
      {
        id: 'pullover',
        name: 'Pullover',
        qualities: [
          { id: 'fleece', name: 'Fleece', price: 49.99 }
        ]
      }
    ]
  }
];

const colorOptions = [
  { name: 'Solid White', value: '#FFFFFF', type: 'solid' },
  { name: 'Solid Black', value: '#000000', type: 'solid' },
  { name: 'Solid Navy', value: '#001F3F', type: 'solid' },
  { name: 'Purple Gradient', value: 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)', type: 'gradient' }
];

const STYLE_PRESETS = [
  "Realistic",
  "Artistic", 
  "Minimalist",
  "Vintage",
  "Cyberpunk",
  "Anime",
  "Pop Art",
  "Watercolor"
];

export default function GeneratePage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState("Minimalist");
  const [isGenerating, setIsGenerating] = useState(false);
  const [results, setResults] = useState<GeneratedDesign[]>([]);
  const [selectedDesign, setSelectedDesign] = useState<GeneratedDesign | null>(null);
  const [saveToExplore, setSaveToExplore] = useState(false);
  const [saveToAccount, setSaveToAccount] = useState(true);
  const [selectedClothType, setSelectedClothType] = useState<ClothType | null>(null);
  const [selectedSubType, setSelectedSubType] = useState<ClothSubType | null>(null);
  const [selectedQuality, setSelectedQuality] = useState<ClothQuality | null>(null);
  const [selectedColor, setSelectedColor] = useState(colorOptions[0]);
  const [showClothDropdown, setShowClothDropdown] = useState(false);
  const [showSubTypeDropdown, setShowSubTypeDropdown] = useState(false);
  const [showQualityDropdown, setShowQualityDropdown] = useState(false);
  const [showColorDropdown, setShowColorDropdown] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [currentTool, setCurrentTool] = useState<string>('move');
  const [showEditTools, setShowEditTools] = useState(false);

  const maxChars = 500;

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    
    setIsGenerating(true);
    
    // Simulate AI generation
    setTimeout(() => {
      const mockDesign: GeneratedDesign = {
        design_id: 'ai-design-' + Date.now(),
        image_url: '/api/placeholder/ai-generated.jpg',
        ai_prompt: prompt,
        ai_style: style
      };
      
      setResults([mockDesign]);
      setSelectedDesign(mockDesign);
      setIsGenerating(false);
    }, 2000);
  };

  const handleEditTool = (tool: string) => {
    setCurrentTool(tool);
    setIsEditing(true);
    setShowEditTools(true);
  };

  const handleSave = () => {
    if (!selectedDesign) return;
    
    // Save logic here
    if (saveToExplore) {
      // Save to explore page
    }
    if (saveToAccount) {
      // Save to user's saved designs
    }
  };

  const handleAddToCart = () => {
    if (!selectedDesign || !selectedClothType || !selectedSubType || !selectedQuality) return;
    
    // Add to cart logic
    window.location.href = '/cart';
  };

  const handleCheckout = () => {
    if (!selectedDesign || !selectedClothType || !selectedSubType || !selectedQuality) return;
    
    // Direct checkout logic
    window.location.href = '/checkout';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-slate-900 dark:via-teal-800 dark:to-purple-900">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-purple-900 dark:text-cream-100">AI Generation</h1>
          <div className="flex gap-4">
            <Link 
              href="/design" 
              className="px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
            >
              Start Designing
            </Link>
            <Link 
              href="/upload" 
              className="px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
            >
              Upload Design
            </Link>
            <Link 
              href="/explore" 
              className="px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
            >
              Explore Designs
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - AI Generation & Settings */}
          <div className="space-y-6">
            {/* AI Generation Section */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Generate Design</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">
                    Describe your design ({prompt.length}/{maxChars} chars)
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value.slice(0, maxChars))}
                    placeholder="A cool tiger with sunglasses, cyberpunk style..."
                    className="w-full px-3 py-2 border border-purple-300 dark:border-purple-600 rounded-lg bg-white dark:bg-gray-700 text-purple-900 dark:text-cream-100 h-24 resize-none"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">Style</label>
                  <div className="grid grid-cols-2 gap-2">
                    {STYLE_PRESETS.map((preset) => (
                      <button
                        key={preset}
                        onClick={() => setStyle(preset)}
                        className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                          style === preset
                            ? 'bg-purple-600 text-white'
                            : 'bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-700'
                        }`}
                      >
                        {preset}
                      </button>
                    ))}
                  </div>
                </div>
                
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating || !prompt.trim()}
                  className="w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-colors disabled:opacity-50"
                >
                  {isGenerating ? (
                    <div className="flex items-center justify-center">
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Generating...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center">
                      <Sparkles className="w-5 h-5 mr-2" />
                      Generate Design
                    </div>
                  )}
                </button>
              </div>
            </div>

            {/* Save Options */}
            {selectedDesign && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
                <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Save Options</h2>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">Save Options</label>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={saveToExplore}
                          onChange={(e) => setSaveToExplore(e.target.checked)}
                          className="mr-2"
                        />
                        <span className="text-purple-700 dark:text-purple-300">Save to Explore Page</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={saveToAccount}
                          onChange={(e) => setSaveToAccount(e.target.checked)}
                          className="mr-2"
                        />
                        <span className="text-purple-700 dark:text-purple-300">Save to Account</span>
                      </label>
                    </div>
                  </div>
                  
                  <button
                    onClick={handleSave}
                    className="w-full px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
                  >
                    <Save className="w-5 h-5 inline mr-2" />
                    Save Design
                  </button>
                </div>
              </div>
            )}

            {/* Cloth Selection */}
            {selectedDesign && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
                <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Cloth Selection</h2>
                
                <div className="space-y-4">
                  <div className="relative">
                    <button
                      onClick={() => setShowClothDropdown(!showClothDropdown)}
                      className="w-full flex items-center justify-between px-4 py-2 border border-purple-300 dark:border-purple-600 rounded-lg bg-white dark:bg-gray-700 text-purple-900 dark:text-cream-100"
                    >
                      <span>{selectedClothType ? selectedClothType.name : 'Select Cloth Type'}</span>
                      <ChevronDown className="w-5 h-5" />
                    </button>
                    
                    {showClothDropdown && (
                      <div className="absolute z-10 w-full mt-2 bg-white dark:bg-gray-700 border border-purple-300 dark:border-purple-600 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                        {clothTypes.map((type) => (
                          <button
                            key={type.id}
                            onClick={() => {
                              setSelectedClothType(type);
                              setShowClothDropdown(false);
                              setShowSubTypeDropdown(true);
                            }}
                            className="w-full px-4 py-2 text-left hover:bg-purple-100 dark:hover:bg-purple-600 text-purple-900 dark:text-cream-100"
                          >
                            {type.name}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {selectedClothType && (
                    <div className="relative">
                      <button
                        onClick={() => setShowSubTypeDropdown(!showSubTypeDropdown)}
                        className="w-full flex items-center justify-between px-4 py-2 border border-purple-300 dark:border-purple-600 rounded-lg bg-white dark:bg-gray-700 text-purple-900 dark:text-cream-100"
                      >
                        <span>{selectedSubType ? selectedSubType.name : 'Select Style'}</span>
                        <ChevronDown className="w-5 h-5" />
                      </button>
                      
                      {showSubTypeDropdown && (
                        <div className="absolute z-10 w-full mt-2 bg-white dark:bg-gray-700 border border-purple-300 dark:border-purple-600 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                          {selectedClothType.subTypes.map((subType) => (
                            <button
                              key={subType.id}
                              onClick={() => {
                                setSelectedSubType(subType);
                                setShowSubTypeDropdown(false);
                                setShowQualityDropdown(true);
                              }}
                              className="w-full px-4 py-2 text-left hover:bg-purple-100 dark:hover:bg-purple-600 text-purple-900 dark:text-cream-100"
                            >
                              {subType.name}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {selectedSubType && (
                    <div className="relative">
                      <button
                        onClick={() => setShowQualityDropdown(!showQualityDropdown)}
                        className="w-full flex items-center justify-between px-4 py-2 border border-purple-300 dark:border-purple-600 rounded-lg bg-white dark:bg-gray-700 text-purple-900 dark:text-cream-100"
                      >
                        <span>{selectedQuality ? `${selectedQuality.name} - $${selectedQuality.price}` : 'Select Quality'}</span>
                        <ChevronDown className="w-5 h-5" />
                      </button>
                      
                      {showQualityDropdown && (
                        <div className="absolute z-10 w-full mt-2 bg-white dark:bg-gray-700 border border-purple-300 dark:border-purple-600 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                          {selectedSubType.qualities.map((quality) => (
                            <button
                              key={quality.id}
                              onClick={() => {
                                setSelectedQuality(quality);
                                setShowQualityDropdown(false);
                              }}
                              className="w-full px-4 py-2 text-left hover:bg-purple-100 dark:hover:bg-purple-600 text-purple-900 dark:text-cream-100"
                            >
                              {quality.name} - ${quality.price}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Edit Tools */}
            {selectedDesign && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
                <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Edit Tools</h2>
                
                <div className="grid grid-cols-4 gap-2">
                  {[
                    { icon: Move, tool: 'move', label: 'Move' },
                    { icon: RotateCw, tool: 'rotate', label: 'Rotate' },
                    { icon: Plus, tool: 'scale-up', label: 'Scale Up' },
                    { icon: Minus, tool: 'scale-down', label: 'Scale Down' },
                    { icon: Edit3, tool: 'draw', label: 'Draw' },
                    { icon: Type, tool: 'text', label: 'Text' },
                    { icon: Scissors, tool: 'cut', label: 'Cut' },
                    { icon: Trash2, tool: 'delete', label: 'Delete' }
                  ].map(({ icon: Icon, tool, label }) => (
                    <button
                      key={tool}
                      onClick={() => handleEditTool(tool)}
                      className={`flex flex-col items-center p-2 rounded-lg transition-colors ${
                        currentTool === tool 
                          ? 'bg-purple-600 text-white' 
                          : 'bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-700'
                      }`}
                    >
                      <Icon className="w-5 h-5 mb-1" />
                      <span className="text-xs">{label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Preview & Results */}
          <div className="space-y-6">
            {/* Generated Results */}
            {results.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
                <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Generated Design</h2>
                
                <div className="grid grid-cols-1 gap-4">
                  {results.map((design) => (
                    <div
                      key={design.design_id}
                      onClick={() => setSelectedDesign(design)}
                      className={`cursor-pointer border-2 rounded-lg p-4 transition-colors ${
                        selectedDesign?.design_id === design.design_id
                          ? 'border-purple-500 bg-purple-50 dark:bg-purple-900'
                          : 'border-purple-200 hover:border-purple-300'
                      }`}
                    >
                      <div className="w-full h-32 bg-purple-100 dark:bg-purple-800 rounded mb-2"></div>
                      <p className="text-sm text-purple-700 dark:text-purple-300 truncate">{design.ai_prompt}</p>
                      <p className="text-xs text-purple-500 dark:text-purple-400">Style: {design.ai_style}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Preview Canvas */}
            {selectedDesign && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
                <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Preview</h2>
                
                <div className="relative bg-purple-100 dark:bg-purple-900 rounded-lg aspect-square flex items-center justify-center">
                  <canvas
                    ref={canvasRef}
                    width={400}
                    height={400}
                    className="border-2 border-purple-300 dark:border-purple-600 rounded-lg bg-white"
                  />
                  
                  {isEditing && (
                    <div className="absolute top-2 right-2 flex gap-2">
                      <button className="p-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            {selectedDesign && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
                <div className="space-y-4">
                  <div className="flex gap-4">
                    <button className="flex-1 px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors">
                      <Download className="w-5 h-5 inline mr-2" />
                      Download
                    </button>
                    <button className="flex-1 px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors">
                      <RefreshCw className="w-5 h-5 inline mr-2" />
                      Regenerate
                    </button>
                  </div>
                  
                  <div className="flex gap-4">
                    <button
                      onClick={handleAddToCart}
                      disabled={!selectedClothType || !selectedSubType || !selectedQuality}
                      className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-colors disabled:opacity-50"
                    >
                      <ShoppingCart className="w-5 h-5 inline mr-2" />
                      Add to Cart
                    </button>
                    <button
                      onClick={handleCheckout}
                      disabled={!selectedClothType || !selectedSubType || !selectedQuality}
                      className="flex-1 px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-colors disabled:opacity-50"
                    >
                      <ShoppingCart className="w-5 h-5 inline mr-2" />
                      Checkout
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
