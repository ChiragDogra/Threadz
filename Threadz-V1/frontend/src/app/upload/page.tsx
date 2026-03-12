'use client';

import { useState, useRef } from 'react';
import { Upload, Save, X, RotateCw, Edit3, Search, ChevronDown, ShoppingCart, Palette, Image, Sparkles } from 'lucide-react';
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

export default function UploadPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [designName, setDesignName] = useState('My Custom Design');
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

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedImage(file);
      // In a real app, this would render the image on the canvas
    }
  };

  const handleSave = () => {
    if (!uploadedImage) return;
    
    // Save logic here
    if (saveToExplore) {
      // Save to explore page
    }
    if (saveToAccount) {
      // Save to user's saved designs
    }
  };

  const handleUseDesign = () => {
    if (!uploadedImage || !selectedClothType || !selectedSubType || !selectedQuality) return;
    
    // Redirect to design page with pre-filled data
    window.location.href = '/design';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-slate-900 dark:via-teal-800 dark:to-purple-900">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-purple-900 dark:text-cream-100">Upload Design</h1>
          <div className="flex gap-4">
            <Link 
              href="/design" 
              className="px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
            >
              Start Designing
            </Link>
            <Link 
              href="/explore" 
              className="px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
            >
              Explore Designs
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
          {/* Left Column - Upload & Settings */}
          <div className="space-y-6">
            {/* Upload Section */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Upload Your Design</h2>
              
              <div className="border-2 border-dashed border-purple-300 dark:border-purple-600 rounded-lg p-8 text-center">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                  id="image-upload"
                />
                <label
                  htmlFor="image-upload"
                  className="cursor-pointer"
                >
                  <Upload className="w-12 h-12 text-purple-400 mx-auto mb-4" />
                  <p className="text-purple-700 dark:text-purple-300 mb-2">Click to upload or drag and drop</p>
                  <p className="text-sm text-purple-500 dark:text-purple-400">PNG, JPG, GIF up to 10MB</p>
                </label>
              </div>
              
              {uploadedImage && (
                <div className="mt-4 p-4 bg-purple-100 dark:bg-purple-800 rounded-lg">
                  <p className="text-purple-700 dark:text-purple-300">Uploaded: {uploadedImage.name}</p>
                </div>
              )}
            </div>

            {/* Design Name */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Design Details</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">Design Name</label>
                  <input
                    type="text"
                    value={designName}
                    onChange={(e) => setDesignName(e.target.value)}
                    className="w-full px-3 py-2 border border-purple-300 dark:border-purple-600 rounded-lg bg-white dark:bg-gray-700 text-purple-900 dark:text-cream-100"
                  />
                </div>
                
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
              </div>
            </div>

            {/* Cloth Selection */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100 mb-4">Cloth Selection</h2>
              
              {/* Similar cloth selection dropdowns as design page */}
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
          </div>

          {/* Right Column - Preview */}
          <div className="space-y-6">
            {/* Preview Canvas */}
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

            {/* Action Buttons */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <div className="space-y-4">
                <div className="flex gap-4">
                  <button
                    onClick={handleSave}
                    disabled={!uploadedImage}
                    className="flex-1 px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors disabled:opacity-50"
                  >
                    <Save className="w-5 h-5 inline mr-2" />
                    Save Design
                  </button>
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="flex-1 px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors"
                  >
                    <Edit3 className="w-5 h-5 inline mr-2" />
                    Edit
                  </button>
                </div>
                
                <button
                  onClick={handleUseDesign}
                  disabled={!uploadedImage || !selectedClothType || !selectedSubType || !selectedQuality}
                  className="w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-colors disabled:opacity-50"
                >
                  Use in Design Studio
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
