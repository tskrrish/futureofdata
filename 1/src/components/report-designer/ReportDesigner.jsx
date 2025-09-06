import React, { useState } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';

import { DraggableToolbox } from './DraggableToolbox';
import { ReportCanvas } from './ReportCanvas';
import { ReportPreview } from './ReportPreview';

export function ReportDesigner({ volunteerData }) {
  const [activeId, setActiveId] = useState(null);
  const [reportElements, setReportElements] = useState([]);
  const [previewMode, setPreviewMode] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  function handleDragStart(event) {
    setActiveId(event.active.id);
  }

  function handleDragEnd(event) {
    const { active, over } = event;

    if (!over) {
      setActiveId(null);
      return;
    }

    // If dragging from toolbox to canvas
    if (over.id === 'canvas-drop-zone' && active.data.current?.type) {
      const newElement = {
        id: `${active.data.current.type}-${Date.now()}`,
        type: active.data.current.type,
        config: active.data.current.config || {},
        position: reportElements.length,
      };
      setReportElements(prev => [...prev, newElement]);
    }
    
    // If reordering within canvas
    else if (active.id !== over.id && reportElements.find(el => el.id === active.id)) {
      const oldIndex = reportElements.findIndex(el => el.id === active.id);
      const newIndex = reportElements.findIndex(el => el.id === over.id);
      
      if (oldIndex !== -1 && newIndex !== -1) {
        setReportElements(prev => arrayMove(prev, oldIndex, newIndex));
      }
    }

    setActiveId(null);
  }

  function handleDragCancel() {
    setActiveId(null);
  }

  function removeElement(elementId) {
    setReportElements(prev => prev.filter(el => el.id !== elementId));
  }

  function updateElementConfig(elementId, config) {
    setReportElements(prev => 
      prev.map(el => el.id === elementId ? { ...el, config: { ...el.config, ...config } } : el)
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="h-screen bg-neutral-50 flex">
        {/* Toolbox Sidebar */}
        <div className="w-80 bg-white border-r border-neutral-200 flex-shrink-0">
          <div className="p-4 border-b border-neutral-200">
            <h2 className="text-lg font-semibold text-neutral-900">Report Designer</h2>
            <p className="text-sm text-neutral-600 mt-1">
              Drag components to build your custom report
            </p>
          </div>
          <DraggableToolbox />
        </div>

        {/* Main Canvas Area */}
        <div className="flex-1 flex flex-col">
          {/* Top Bar */}
          <div className="bg-white border-b border-neutral-200 px-6 py-4 flex items-center justify-between">
            <h3 className="text-sm font-medium text-neutral-700">
              Report Canvas ({reportElements.length} elements)
            </h3>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setPreviewMode(!previewMode)}
                className="px-3 py-1.5 text-sm rounded-lg border border-neutral-300 hover:bg-neutral-50 transition-colors"
              >
                {previewMode ? 'Edit' : 'Preview'}
              </button>
              <button
                onClick={() => setReportElements([])}
                className="px-3 py-1.5 text-sm rounded-lg bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
              >
                Clear All
              </button>
            </div>
          </div>

          {/* Canvas Content */}
          <div className="flex-1 p-6">
            {previewMode ? (
              <ReportPreview 
                elements={reportElements} 
                volunteerData={volunteerData}
              />
            ) : (
              <SortableContext 
                items={reportElements.map(el => el.id)} 
                strategy={verticalListSortingStrategy}
              >
                <ReportCanvas
                  elements={reportElements}
                  onRemoveElement={removeElement}
                  onUpdateElement={updateElementConfig}
                />
              </SortableContext>
            )}
          </div>
        </div>
      </div>

      <DragOverlay>
        {activeId ? (
          <div className="bg-white border border-neutral-300 rounded-lg p-3 shadow-lg">
            <div className="text-sm font-medium text-neutral-700">
              {activeId.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </div>
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}