import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { SortableReportElement } from './SortableReportElement';
import { Plus } from 'lucide-react';

function EmptyCanvas() {
  const { setNodeRef } = useDroppable({
    id: 'canvas-drop-zone',
  });

  return (
    <div
      ref={setNodeRef}
      className="h-full min-h-96 border-2 border-dashed border-neutral-300 rounded-xl flex items-center justify-center bg-neutral-50/50"
    >
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-4 bg-neutral-100 rounded-full flex items-center justify-center">
          <Plus className="w-8 h-8 text-neutral-400" />
        </div>
        <h3 className="text-lg font-medium text-neutral-600 mb-2">
          Start Building Your Report
        </h3>
        <p className="text-neutral-500 max-w-md">
          Drag components from the toolbox on the left to begin creating your custom report.
          You can add sections, metrics, charts, and filters.
        </p>
      </div>
    </div>
  );
}

function CanvasWithElements({ elements, onRemoveElement, onUpdateElement }) {
  const { setNodeRef } = useDroppable({
    id: 'canvas-drop-zone',
  });

  return (
    <div
      ref={setNodeRef}
      className="min-h-96 space-y-4"
    >
      {elements.map((element) => (
        <SortableReportElement
          key={element.id}
          element={element}
          onRemove={onRemoveElement}
          onUpdate={onUpdateElement}
        />
      ))}
      
      {/* Drop zone indicator at bottom */}
      <div className="h-16 border-2 border-dashed border-neutral-200 rounded-lg flex items-center justify-center text-neutral-400 hover:border-blue-300 hover:text-blue-500 transition-colors">
        <Plus className="w-6 h-6 mr-2" />
        Drop new components here
      </div>
    </div>
  );
}

export function ReportCanvas({ elements, onRemoveElement, onUpdateElement }) {
  if (elements.length === 0) {
    return <EmptyCanvas />;
  }

  return (
    <CanvasWithElements
      elements={elements}
      onRemoveElement={onRemoveElement}
      onUpdateElement={onUpdateElement}
    />
  );
}