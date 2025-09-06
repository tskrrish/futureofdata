import React, { useState } from 'react';
import {
  useSortable,
} from '@dnd-kit/sortable';
import {
  CSS,
} from '@dnd-kit/utilities';
import { 
  GripVertical, 
  X, 
  Settings,
  Type,
  Hash,
  Layout,
  BarChart3,
  Filter
} from 'lucide-react';

import { ElementConfigPanel } from './ElementConfigPanel';

function getElementIcon(type) {
  switch (type) {
    case 'header':
      return <Type className="w-4 h-4" />;
    case 'kpi':
      return <Hash className="w-4 h-4" />;
    case 'divider':
      return <Layout className="w-4 h-4" />;
    case 'metric':
    case 'chart':
      return <BarChart3 className="w-4 h-4" />;
    case 'filter':
      return <Filter className="w-4 h-4" />;
    default:
      return <Layout className="w-4 h-4" />;
  }
}

function getElementTitle(element) {
  const { type, config } = element;
  
  switch (type) {
    case 'header':
      return config.title || 'Header Section';
    case 'kpi':
      return 'KPI Cards';
    case 'divider':
      return 'Divider';
    case 'metric':
      return config.title || 'Metric';
    case 'chart':
      return config.title || 'Chart';
    case 'filter':
      return config.title || 'Filter';
    default:
      return 'Element';
  }
}

function ElementPreview({ element }) {
  const { type, config } = element;

  switch (type) {
    case 'header':
      return (
        <div className="py-4">
          <h2 className="text-xl font-semibold text-neutral-800 mb-2">
            {config.title || 'Report Title'}
          </h2>
          {config.subtitle && (
            <p className="text-neutral-600">
              {config.subtitle}
            </p>
          )}
        </div>
      );

    case 'kpi':
      return (
        <div className="py-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="bg-white p-4 rounded-lg border">
                <div className="text-2xl font-bold text-neutral-800">--</div>
                <div className="text-sm text-neutral-600">KPI {i}</div>
              </div>
            ))}
          </div>
        </div>
      );

    case 'divider':
      return (
        <div className="py-4">
          <hr className="border-neutral-300" />
        </div>
      );

    case 'metric':
      return (
        <div className="py-4">
          <div className="bg-white p-4 rounded-lg border">
            <div className="text-2xl font-bold text-neutral-800 mb-1">--</div>
            <div className="text-sm text-neutral-600">
              {config.title || 'Metric Value'}
            </div>
          </div>
        </div>
      );

    case 'chart':
      return (
        <div className="py-4">
          <div className="bg-white p-4 rounded-lg border">
            <h3 className="font-medium text-neutral-800 mb-4">
              {config.title || 'Chart Title'}
            </h3>
            <div className="h-48 bg-neutral-50 rounded flex items-center justify-center">
              <div className="text-neutral-400 text-center">
                <BarChart3 className="w-8 h-8 mx-auto mb-2" />
                <div className="text-sm">Chart Preview</div>
              </div>
            </div>
          </div>
        </div>
      );

    case 'filter':
      return (
        <div className="py-4">
          <div className="bg-white p-4 rounded-lg border">
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              {config.title || 'Filter'}
            </label>
            <div className="w-full h-10 bg-neutral-50 border border-neutral-200 rounded-md flex items-center px-3 text-neutral-400 text-sm">
              Filter placeholder
            </div>
          </div>
        </div>
      );

    default:
      return (
        <div className="py-4">
          <div className="bg-neutral-50 p-4 rounded-lg border-2 border-dashed border-neutral-300">
            <div className="text-neutral-500 text-center">Unknown element type</div>
          </div>
        </div>
      );
  }
}

export function SortableReportElement({ element, onRemove, onUpdate }) {
  const [showConfig, setShowConfig] = useState(false);
  
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: element.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        group bg-white border border-neutral-200 rounded-lg overflow-hidden
        ${isDragging ? 'opacity-50 shadow-lg' : 'hover:border-neutral-300'}
      `}
    >
      {/* Element Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-neutral-50 border-b border-neutral-200">
        <div className="flex items-center gap-3">
          <button
            {...attributes}
            {...listeners}
            className="text-neutral-400 hover:text-neutral-600 cursor-grab active:cursor-grabbing"
          >
            <GripVertical className="w-4 h-4" />
          </button>
          
          <div className="flex items-center gap-2 text-neutral-600">
            {getElementIcon(element.type)}
            <span className="text-sm font-medium">
              {getElementTitle(element)}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="p-1 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded"
          >
            <Settings className="w-4 h-4" />
          </button>
          <button
            onClick={() => onRemove(element.id)}
            className="p-1 text-neutral-400 hover:text-red-500 hover:bg-red-50 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Configuration Panel */}
      {showConfig && (
        <ElementConfigPanel
          element={element}
          onUpdate={onUpdate}
          onClose={() => setShowConfig(false)}
        />
      )}

      {/* Element Content */}
      <div className="p-4">
        <ElementPreview element={element} />
      </div>
    </div>
  );
}