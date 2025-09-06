import React, { useState } from "react";
import { Edit, Trash2, Play, BarChart3, PieChart, TrendingUp, Plus, Eye } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { ChartCell } from "./ChartCell";

export function NotebookCell({ cell, index, volunteerData, onUpdate, onDelete, onToggleEdit, onAddCell }) {
  const [showAddMenu, setShowAddMenu] = useState(false);

  const handleContentChange = (content) => {
    onUpdate(cell.id, content);
  };

  const addCellOptions = [
    { type: "text", icon: Edit, label: "Text Cell" },
    { type: "chart", icon: BarChart3, label: "Chart Cell" }
  ];

  return (
    <div className="group relative">
      {/* Cell Content */}
      <div className="bg-white rounded-2xl border hover:border-gray-300 transition-colors">
        {/* Cell Header */}
        <div className="flex items-center justify-between p-3 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
              {cell.type === "text" ? "Text" : "Chart"} [{index + 1}]
            </span>
            {cell.lastExecuted && (
              <span className="text-xs text-green-600">
                ✓ Executed {new Date(cell.lastExecuted).toLocaleTimeString()}
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {cell.type === "chart" && (
              <button
                onClick={() => onUpdate(cell.id, { ...cell.content, lastExecuted: Date.now() })}
                className="p-1 hover:bg-gray-100 rounded"
                title="Execute Cell"
              >
                <Play className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => onToggleEdit(cell.id)}
              className="p-1 hover:bg-gray-100 rounded"
              title={cell.isEditing ? "View Mode" : "Edit Mode"}
            >
              {cell.isEditing ? <Eye className="w-4 h-4" /> : <Edit className="w-4 h-4" />}
            </button>
            <button
              onClick={() => onDelete(cell.id)}
              className="p-1 hover:bg-red-100 text-red-600 rounded"
              title="Delete Cell"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Cell Body */}
        <div className="p-4">
          {cell.type === "text" ? (
            <TextCellContent
              content={cell.content}
              isEditing={cell.isEditing}
              onChange={handleContentChange}
            />
          ) : (
            <ChartCell
              content={cell.content}
              isEditing={cell.isEditing}
              volunteerData={volunteerData}
              onChange={handleContentChange}
            />
          )}
        </div>
      </div>

      {/* Add Cell Button */}
      <div className="relative">
        <div className="absolute left-1/2 transform -translate-x-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="relative">
            <button
              onClick={() => setShowAddMenu(!showAddMenu)}
              className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white text-sm rounded-full hover:bg-blue-700 shadow-lg"
            >
              <Plus className="w-3 h-3" />
              Add Cell
            </button>
            
            {showAddMenu && (
              <div className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 bg-white border rounded-lg shadow-lg p-2 z-10 whitespace-nowrap">
                {addCellOptions.map(({ type, icon, label }) => {
                  const IconComponent = icon;
                  return (
                  <button
                    key={type}
                    onClick={() => {
                      onAddCell(type, index);
                      setShowAddMenu(false);
                    }}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-gray-100 rounded"
                  >
                    <IconComponent className="w-4 h-4" />
                    {label}
                  </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function TextCellContent({ content, isEditing, onChange }) {
  if (isEditing) {
    return (
      <textarea
        value={content}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Write your analysis in Markdown..."
        className="w-full h-32 p-3 border rounded-lg resize-vertical focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    );
  }

  if (!content) {
    return (
      <div className="text-gray-500 italic p-3">
        Click edit to add content...
      </div>
    );
  }

  return <MarkdownRenderer content={content} />;
}