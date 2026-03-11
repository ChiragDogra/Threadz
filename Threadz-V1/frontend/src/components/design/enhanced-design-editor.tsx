import React, { useRef, useEffect, useState, useCallback } from 'react';
import { fabric } from 'fabric';

interface EnhancedDesignEditorProps {
  initialDesign?: string;
  onSave?: (designData: string) => void;
  width?: number;
  height?: number;
  className?: string;
}

const EnhancedDesignEditor: React.FC<EnhancedDesignEditorProps> = ({
  initialDesign,
  onSave,
  width = 800,
  height = 600,
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [canvas, setCanvas] = useState<fabric.Canvas | null>(null);
  const [selectedTool, setSelectedTool] = useState<string>('select');
  const [isDrawing, setIsDrawing] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [showGrid, setShowGrid] = useState(true);
  const [snapToGrid, setSnapToGrid] = useState(true);
  const [zoom, setZoom] = useState(1);

  // Initialize canvas
  useEffect(() => {
    if (!canvasRef.current) return;

    const fabricCanvas = new fabric.Canvas(canvasRef.current, {
      width,
      height,
      backgroundColor: '#ffffff',
      selection: true,
      preserveObjectStacking: true
    });

    // Enable object snapping
    fabricCanvas.on('object:moving', (e) => {
      if (snapToGrid) {
        const obj = e.target;
        const gridSize = 20;
        obj.set({
          left: Math.round(obj.left! / gridSize) * gridSize,
          top: Math.round(obj.top! / gridSize) * gridSize
        });
      }
    });

    // Add keyboard shortcuts
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!canvas) return;
      
      // Delete key
      if (e.key === 'Delete' || e.key === 'Backspace') {
        const activeObject = canvas.getActiveObject();
        if (activeObject) {
          canvas.remove(activeObject);
          canvas.renderAll();
          saveToHistory();
        }
      }
      
      // Ctrl+Z for undo
      if (e.ctrlKey && e.key === 'z') {
        undo();
      }
      
      // Ctrl+Y for redo
      if (e.ctrlKey && e.key === 'y') {
        redo();
      }
      
      // Ctrl+S for save
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    setCanvas(fabricCanvas);

    // Load initial design if provided
    if (initialDesign) {
      fabricCanvas.loadFromJSON(initialDesign, () => {
        fabricCanvas.renderAll();
        saveToHistory();
      });
    }

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      fabricCanvas.dispose();
    };
  }, [width, height, snapToGrid]);

  // Grid overlay
  useEffect(() => {
    if (!canvas) return;

    if (showGrid) {
      drawGrid();
    } else {
      clearGrid();
    }
  }, [showGrid, canvas]);

  const drawGrid = () => {
    if (!canvas) return;

    const gridSize = 20;
    const canvasWidth = canvas.getWidth();
    const canvasHeight = canvas.getHeight();

    // Clear existing grid
    clearGrid();

    // Draw vertical lines
    for (let x = 0; x <= canvasWidth; x += gridSize) {
      const line = new fabric.Line([x, 0, x, canvasHeight], {
        stroke: '#e0e0e0',
        strokeWidth: 1,
        selectable: false,
        evented: false,
        excludeFromExport: true
      });
      canvas.add(line);
    }

    // Draw horizontal lines
    for (let y = 0; y <= canvasHeight; y += gridSize) {
      const line = new fabric.Line([0, y, canvasWidth, y], {
        stroke: '#e0e0e0',
        strokeWidth: 1,
        selectable: false,
        evented: false,
        excludeFromExport: true
      });
      canvas.add(line);
    }

    canvas.renderAll();
  };

  const clearGrid = () => {
    if (!canvas) return;

    const objects = canvas.getObjects();
    objects.forEach(obj => {
      if (obj.excludeFromExport) {
        canvas.remove(obj);
      }
    });
    canvas.renderAll();
  };

  const saveToHistory = useCallback(() => {
    if (!canvas) return;

    const json = JSON.stringify(canvas.toJSON());
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(json);
    
    // Limit history to 50 states
    if (newHistory.length > 50) {
      newHistory.shift();
    }
    
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  }, [canvas, history, historyIndex]);

  const undo = () => {
    if (historyIndex > 0 && canvas) {
      const newIndex = historyIndex - 1;
      canvas.loadFromJSON(history[newIndex], () => {
        canvas.renderAll();
        setHistoryIndex(newIndex);
      });
    }
  };

  const redo = () => {
    if (historyIndex < history.length - 1 && canvas) {
      const newIndex = historyIndex + 1;
      canvas.loadFromJSON(history[newIndex], () => {
        canvas.renderAll();
        setHistoryIndex(newIndex);
      });
    }
  };

  const addText = () => {
    if (!canvas) return;

    const text = new fabric.IText('Click to edit', {
      left: width / 2 - 50,
      top: height / 2 - 25,
      width: 100,
      fontSize: 24,
      fontFamily: 'Arial',
      fill: '#000000'
    });

    canvas.add(text);
    canvas.setActiveObject(text);
    canvas.renderAll();
    saveToHistory();
  };

  const addShape = (shapeType: string) => {
    if (!canvas) return;

    let shape;
    const centerX = width / 2;
    const centerY = height / 2;

    switch (shapeType) {
      case 'rectangle':
        shape = new fabric.Rect({
          left: centerX - 50,
          top: centerY - 50,
          width: 100,
          height: 100,
          fill: '#3b82f6'
        });
        break;
      case 'circle':
        shape = new fabric.Circle({
          left: centerX - 50,
          top: centerY - 50,
          radius: 50,
          fill: '#ef4444'
        });
        break;
      case 'triangle':
        shape = new fabric.Triangle({
          left: centerX - 50,
          top: centerY - 50,
          width: 100,
          height: 100,
          fill: '#10b981'
        });
        break;
      default:
        return;
    }

    canvas.add(shape);
    canvas.setActiveObject(shape);
    canvas.renderAll();
    saveToHistory();
  };

  const startDrawing = () => {
    if (!canvas) return;
    
    setIsDrawing(true);
    canvas.isDrawingMode = true;
    canvas.freeDrawingBrush.width = 2;
    canvas.freeDrawingBrush.color = '#000000';
  };

  const stopDrawing = () => {
    if (!canvas) return;
    
    setIsDrawing(false);
    canvas.isDrawingMode = false;
    saveToHistory();
  };

  const handleSave = () => {
    if (!canvas || !onSave) return;

    const json = JSON.stringify(canvas.toJSON());
    onSave(json);
  };

  const handleZoom = (newZoom: number) => {
    if (!canvas) return;
    
    setZoom(newZoom);
    canvas.setZoom(newZoom);
    canvas.renderAll();
  };

  const clearCanvas = () => {
    if (!canvas) return;
    
    canvas.clear();
    canvas.backgroundColor = '#ffffff';
    canvas.renderAll();
    saveToHistory();
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !canvas) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const fabricImg = new fabric.Image(img, {
          left: width / 2 - img.width / 2,
          top: height / 2 - img.height / 2
        });
        
        // Scale image if too large
        const maxSize = 400;
        if (fabricImg.width! > maxSize || fabricImg.height! > maxSize) {
          const scale = Math.min(maxSize / fabricImg.width!, maxSize / fabricImg.height!);
          fabricImg.scale(scale);
        }
        
        canvas.add(fabricImg);
        canvas.setActiveObject(fabricImg);
        canvas.renderAll();
        saveToHistory();
      };
      img.src = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className={`enhanced-design-editor ${className}`}>
      {/* Toolbar */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex flex-wrap items-center gap-2">
          {/* Selection Tools */}
          <div className="flex items-center gap-1 border-r border-gray-300 pr-2">
            <button
              onClick={() => { setSelectedTool('select'); canvas?.selection = true; }}
              className={`p-2 rounded ${selectedTool === 'select' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
              title="Select"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2z" />
              </svg>
            </button>
            <button
              onClick={() => { setSelectedTool('draw'); startDrawing(); }}
              className={`p-2 rounded ${selectedTool === 'draw' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
              title="Draw"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
            {isDrawing && (
              <button
                onClick={stopDrawing}
                className="p-2 rounded bg-red-100 text-red-600"
                title="Stop Drawing"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Shape Tools */}
          <div className="flex items-center gap-1 border-r border-gray-300 pr-2">
            <button
              onClick={() => addShape('rectangle')}
              className="p-2 rounded hover:bg-gray-100"
              title="Rectangle"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <rect x="4" y="6" width="16" height="12" strokeWidth={2} />
              </svg>
            </button>
            <button
              onClick={() => addShape('circle')}
              className="p-2 rounded hover:bg-gray-100"
              title="Circle"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="8" strokeWidth={2} />
              </svg>
            </button>
            <button
              onClick={() => addShape('triangle')}
              className="p-2 rounded hover:bg-gray-100"
              title="Triangle"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M12 4L4 18h16z" strokeWidth={2} />
              </svg>
            </button>
          </div>

          {/* Text Tool */}
          <div className="flex items-center gap-1 border-r border-gray-300 pr-2">
            <button
              onClick={addText}
              className="p-2 rounded hover:bg-gray-100"
              title="Add Text"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
          </div>

          {/* File Operations */}
          <div className="flex items-center gap-1 border-r border-gray-300 pr-2">
            <label className="p-2 rounded hover:bg-gray-100 cursor-pointer" title="Upload Image">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
            </label>
            <button
              onClick={clearCanvas}
              className="p-2 rounded hover:bg-gray-100"
              title="Clear Canvas"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>

          {/* History */}
          <div className="flex items-center gap-1 border-r border-gray-300 pr-2">
            <button
              onClick={undo}
              disabled={historyIndex <= 0}
              className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Undo (Ctrl+Z)"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
              </svg>
            </button>
            <button
              onClick={redo}
              disabled={historyIndex >= history.length - 1}
              className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Redo (Ctrl+Y)"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 10h-10a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6" />
              </svg>
            </button>
          </div>

          {/* View Options */}
          <div className="flex items-center gap-1 border-r border-gray-300 pr-2">
            <button
              onClick={() => setShowGrid(!showGrid)}
              className={`p-2 rounded ${showGrid ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
              title="Toggle Grid"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              onClick={() => setSnapToGrid(!snapToGrid)}
              className={`p-2 rounded ${snapToGrid ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
              title="Snap to Grid"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v14a1 1 0 01-1 1H5a1 1 0 01-1-1V5z" />
              </svg>
            </button>
          </div>

          {/* Zoom */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleZoom(Math.max(0.5, zoom - 0.1))}
              className="p-2 rounded hover:bg-gray-100"
              title="Zoom Out"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
              </svg>
            </button>
            <span className="text-sm font-medium px-2">{Math.round(zoom * 100)}%</span>
            <button
              onClick={() => handleZoom(Math.min(2, zoom + 0.1))}
              className="p-2 rounded hover:bg-gray-100"
              title="Zoom In"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
              </svg>
            </button>
          </div>

          {/* Save */}
          <button
            onClick={handleSave}
            className="ml-auto px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Save Design
          </button>
        </div>
      </div>

      {/* Canvas Container */}
      <div className="relative overflow-auto bg-gray-50 p-4" style={{ height: '600px' }}>
        <div className="inline-block">
          <canvas ref={canvasRef} />
        </div>
      </div>

      {/* Status Bar */}
      <div className="bg-gray-100 border-t border-gray-200 px-4 py-2 flex items-center justify-between text-sm text-gray-600">
        <div className="flex items-center space-x-4">
          <span>Tool: {selectedTool}</span>
          <span>Zoom: {Math.round(zoom * 100)}%</span>
          <span>Grid: {showGrid ? 'On' : 'Off'}</span>
          <span>Snap: {snapToGrid ? 'On' : 'Off'}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span>Press Ctrl+Z to undo, Ctrl+Y to redo, Ctrl+S to save</span>
        </div>
      </div>
    </div>
  );
};

export default EnhancedDesignEditor;
