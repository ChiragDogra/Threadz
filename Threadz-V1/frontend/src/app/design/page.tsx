'use client';

import { useState, useRef } from 'react';
import { Search, Upload, Palette, ShoppingCart, Sparkles, Image, Save, Edit3, Scissors, Type, X, Check, ChevronDown, Plus, Minus, RotateCw, Move, Trash2, Download } from 'lucide-react';
import Link from 'next/link';

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

interface SavedDesign {
  id: string;
  name: string;
  thumbnail: string;
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
          { id: 'premium-cotton', name: 'Premium Cotton', price: 29.99 },
          { id: 'organic-cotton', name: 'Organic Cotton', price: 39.99 }
        ]
      },
      {
        id: 'henley',
        name: 'Henley',
        qualities: [
          { id: 'henley-cotton', name: 'Cotton Henley', price: 24.99 },
          { id: 'henley-blend', name: 'Cotton Blend', price: 34.99 }
        ]
      },
      {
        id: 'cropped',
        name: 'Cropped',
        qualities: [
          { id: 'cropped-cotton', name: 'Cropped Cotton', price: 22.99 }
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
          { id: 'fleece', name: 'Fleece', price: 49.99 },
          { id: 'cotton-fleece', name: 'Cotton Fleece', price: 59.99 }
        ]
      },
      {
        id: 'zip-up',
        name: 'Zip Up',
        qualities: [
          { id: 'zip-hoodie', name: 'Zip Hoodie', price: 54.99 }
        ]
      }
    ]
  },
  {
    id: 'tank-top',
    name: 'Tank Top',
    subTypes: [
      {
        id: 'muscle-tank',
        name: 'Muscle Tank',
        qualities: [
          { id: 'tank-cotton', name: 'Cotton Tank', price: 15.99 }
        ]
      }
    ]
  }
];

const savedDesigns: SavedDesign[] = [
  { id: 'design-1', name: 'Cool Tiger', thumbnail: '/api/placeholder/tiger-thumb.jpg' },
  { id: 'design-2', name: 'Abstract Waves', thumbnail: '/api/placeholder/waves-thumb.jpg' },
  { id: 'design-3', name: 'Minimal Logo', thumbnail: '/api/placeholder/logo-thumb.jpg' }
];

const colorOptions = [
  { name: 'Solid White', value: '#FFFFFF', type: 'solid' },
  { name: 'Solid Black', value: '#000000', type: 'solid' },
  { name: 'Solid Navy', value: '#001F3F', type: 'solid' },
  { name: 'Solid Gray', value: '#808080', type: 'solid' },
  { name: 'Purple Gradient', value: 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)', type: 'gradient' },
  { name: 'Blue Gradient', value: 'linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%)', type: 'gradient' },
  { name: 'Sunset Gradient', value: 'linear-gradient(135deg, #F59E0B 0%, #EF4444 100%)', type: 'gradient' }
];

export default function DesignPage() {
  const [selectedClothType, setSelectedClothType] = useState<ClothType | null>(null);
  const [selectedSubType, setSelectedSubType] = useState<ClothSubType | null>(null);
  const [selectedQuality, setSelectedQuality] = useState<ClothQuality | null>(null);
  const [selectedColor, setSelectedColor] = useState(colorOptions[0]);
  const [uploadedDesign, setUploadedDesign] = useState<File | null>(null);
  const [savedDesign, setSavedDesign] = useState<SavedDesign | null>(null);
  const [aiPrompt, setAiPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [showClothDropdown, setShowClothDropdown] = useState(false);
  const [showSubTypeDropdown, setShowSubTypeDropdown] = useState(false);
  const [showQualityDropdown, setShowQualityDropdown] = useState(false);
  const [showColorDropdown, setShowColorDropdown] = useState(false);
  const [showSavedDesigns, setShowSavedDesigns] = useState(false);
  const [showEditTools, setShowEditTools] = useState(false);
  const [currentTool, setCurrentTool] = useState<string>('move');
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedDesign(file);
      setSavedDesign(null);
    }
  };

  const handleSavedDesignSelect = (design: SavedDesign) => {
    setSavedDesign(design);
    setUploadedDesign(null);
    setShowSavedDesigns(false);
  };

  const handleAIGenerate = async () => {
    if (!aiPrompt.trim()) return;
    
    setIsGenerating(true);
    // Simulate AI generation
    setTimeout(() => {
      setIsGenerating(false);
      // In real app, this would set the generated design
    }, 2000);
  };

  const handleEditTool = (tool: string) => {
    setCurrentTool(tool);
    setIsEditing(true);
    setShowEditTools(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-slate-900 dark:via-teal-800 dark:to-purple-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-purple-900 dark:text-cream-100">Start Designing</h1>
          <div className="flex gap-4">
            <Link 
              href="/explore" 
              className="px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
            >
              Explore Designs
            </Link>
            <Link 
              href="/upload" 
              className="px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
            >
              Upload Design
            </Link>
            <Link 
              href="/generate" 
              className="px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
            >
              AI Generation
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Controls */}
          <div className="space-y-6">
            {/* Cloth Selection */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Cloth Selection</h2>
              
              {/* Cloth Type Dropdown */}
              <div className="relative mb-4">
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
                          setSelectedSubType(null);
                          setSelectedQuality(null);
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

              {/* Sub Type Dropdown */}
              {selectedClothType && (
                <div className="relative mb-4">
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
                            setSelectedQuality(null);
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

              {/* Quality Dropdown */}
              {selectedSubType && (
                <div className="relative mb-4">
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

            {/* Color Selection */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Base Color</h2>
              
              <div className="relative">
                <button
                  onClick={() => setShowColorDropdown(!showColorDropdown)}
                  className="w-full flex items-center justify-between px-4 py-2 border border-purple-300 dark:border-purple-600 rounded-lg bg-white dark:bg-gray-700 text-purple-900 dark:text-cream-100"
                >
                  <span className="flex items-center gap-2">
                    <div 
                      className="w-6 h-6 rounded border border-gray-300"
                      style={{ background: selectedColor.value }}
                    />
                    {selectedColor.name}
                  </span>
                  <ChevronDown className="w-5 h-5" />
                </button>
                
                {showColorDropdown && (
                  <div className="absolute z-10 w-full mt-2 bg-white dark:bg-gray-700 border border-purple-300 dark:border-purple-600 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    {colorOptions.map((color) => (
                      <button
                        key={color.name}
                        onClick={() => {
                          setSelectedColor(color);
                          setShowColorDropdown(false);
                        }}
                        className="w-full px-4 py-2 flex items-center gap-2 hover:bg-purple-100 dark:hover:bg-purple-600 text-purple-900 dark:text-cream-100"
                      >
                        <div 
                          className="w-6 h-6 rounded border border-gray-300"
                          style={{ background: color.value }}
                        />
                        {color.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Design Options */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Design Options</h2>
              
              <div className="space-y-4">
                {/* Upload Design */}
                <div>
                  <label className="block text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">Upload Custom Design</label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="design-upload"
                  />
                  <label
                    htmlFor="design-upload"
                    className="flex items-center justify-center px-4 py-2 border border-purple-300 dark:border-purple-600 rounded-lg bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 cursor-pointer hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
                  >
                    <Upload className="w-5 h-5 mr-2" />
                    Choose File
                  </label>
                  {uploadedDesign && (
                    <p className="mt-2 text-sm text-purple-600 dark:text-purple-400">Selected: {uploadedDesign.name}</p>
                  )}
                </div>

                {/* Saved Designs */}
                <div>
                  <label className="block text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">Saved Designs</label>
                  <button
                    onClick={() => setShowSavedDesigns(!showSavedDesigns)}
                    className="flex items-center justify-center px-4 py-2 border border-purple-300 dark:border-purple-600 rounded-lg bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
                  >
                    <Image className="w-5 h-5 mr-2" />
                    Browse Saved Designs
                  </button>
                  
                  {showSavedDesigns && (
                    <div className="mt-2 grid grid-cols-3 gap-2">
                      {savedDesigns.map((design) => (
                        <button
                          key={design.id}
                          onClick={() => handleSavedDesignSelect(design)}
                          className={`p-2 border rounded-lg ${savedDesign?.id === design.id ? 'border-purple-500 bg-purple-100' : 'border-purple-300'}`}
                        >
                          <div className="w-full h-20 bg-purple-200 rounded mb-1"></div>
                          <p className="text-xs text-purple-900 dark:text-cream-100">{design.name}</p>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* AI Generation */}
                <div>
                  <label className="block text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">AI Generation</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={aiPrompt}
                      onChange={(e) => setAiPrompt(e.target.value)}
                      placeholder="Describe your design..."
                      className="flex-1 px-3 py-2 border border-purple-300 dark:border-purple-600 rounded-lg bg-white dark:bg-gray-700 text-purple-900 dark:text-cream-100"
                    />
                    <button
                      onClick={handleAIGenerate}
                      disabled={isGenerating || !aiPrompt.trim()}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 transition-colors"
                    >
                      {isGenerating ? (
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      ) : (
                        <Sparkles className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Edit Tools */}
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
          </div>

          {/* Right Column - Preview */}
          <div className="space-y-6">
            {/* Canvas Preview */}
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
                      <Check className="w-4 h-4" />
                    </button>
                    <button 
                      onClick={() => setIsEditing(false)}
                      className="p-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <div className="space-y-4">
                <div className="flex gap-4">
                  <button className="flex-1 px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors">
                    <Save className="w-5 h-5 inline mr-2" />
                    Save Design
                  </button>
                  <button className="flex-1 px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors">
                    <Download className="w-5 h-5 inline mr-2" />
                    Download
                  </button>
                </div>
                
                <div className="flex gap-4">
                  <button className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-colors">
                    <ShoppingCart className="w-5 h-5 inline mr-2" />
                    Add to Cart
                  </button>
                  <button className="flex-1 px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-colors">
                    <ShoppingCart className="w-5 h-5 inline mr-2" />
                    Checkout
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
