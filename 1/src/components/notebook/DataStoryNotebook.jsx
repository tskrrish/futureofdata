import React, { useState } from "react";
import { Play, Plus, Download, Edit, Eye, Save, X } from "lucide-react";
import { NotebookCell } from "./NotebookCell";
import { generateDataStory } from "../../utils/storyGenerator";
import { exportDataStory } from "../../utils/exportUtils";

export function DataStoryNotebook({ volunteerData }) {
  const [cells, setCells] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [storyTitle, setStoryTitle] = useState("Volunteer Impact Analysis");
  const [isGenerating, setIsGenerating] = useState(false);

  // Generate initial data story
  const generateStory = async () => {
    setIsGenerating(true);
    try {
      const generatedCells = await generateDataStory(volunteerData);
      setCells(generatedCells);
    } catch (error) {
      console.error("Error generating story:", error);
    } finally {
      setIsGenerating(false);
    }
  };

  // Add new cell
  const addCell = (type = "text", index = null) => {
    const newCell = {
      id: `cell-${Date.now()}`,
      type,
      content: type === "text" ? "" : { chartType: "bar", data: [] },
      isEditing: true
    };
    
    const insertIndex = index !== null ? index + 1 : cells.length;
    const newCells = [...cells];
    newCells.splice(insertIndex, 0, newCell);
    setCells(newCells);
  };

  // Update cell content
  const updateCell = (cellId, content) => {
    setCells(prevCells =>
      prevCells.map(cell =>
        cell.id === cellId
          ? { ...cell, content, isEditing: false }
          : cell
      )
    );
  };

  // Delete cell
  const deleteCell = (cellId) => {
    setCells(prevCells => prevCells.filter(cell => cell.id !== cellId));
  };

  // Toggle cell editing
  const toggleCellEdit = (cellId) => {
    setCells(prevCells =>
      prevCells.map(cell =>
        cell.id === cellId
          ? { ...cell, isEditing: !cell.isEditing }
          : cell
      )
    );
  };

  // Execute all cells (refresh visualizations)
  const executeAllCells = () => {
    setCells(prevCells =>
      prevCells.map(cell => ({ ...cell, lastExecuted: Date.now() }))
    );
  };

  // Export story
  const exportStory = () => {
    exportDataStory(storyTitle, cells, volunteerData);
  };

  const hasContent = cells.length > 0;

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      {/* Header */}
      <div className="bg-white rounded-2xl border p-6">
        <div className="flex items-center justify-between mb-4">
          {isEditing ? (
            <input
              type="text"
              value={storyTitle}
              onChange={(e) => setStoryTitle(e.target.value)}
              className="text-2xl font-bold bg-transparent border-b-2 border-blue-500 focus:outline-none"
              onBlur={() => setIsEditing(false)}
              onKeyDown={(e) => e.key === 'Enter' && setIsEditing(false)}
              autoFocus
            />
          ) : (
            <h1 
              className="text-2xl font-bold cursor-pointer hover:text-blue-600"
              onClick={() => setIsEditing(true)}
            >
              {storyTitle}
            </h1>
          )}
          <div className="flex gap-2">
            {!hasContent && (
              <button
                onClick={generateStory}
                disabled={isGenerating}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50"
              >
                {isGenerating ? "Generating..." : "Generate Story"}
              </button>
            )}
            {hasContent && (
              <>
                <button
                  onClick={executeAllCells}
                  className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  title="Execute All Cells"
                >
                  <Play className="w-4 h-4" />
                </button>
                <button
                  onClick={() => addCell("text")}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                  title="Add Text Cell"
                >
                  <Plus className="w-4 h-4" />
                </button>
                <button
                  onClick={exportStory}
                  className="flex items-center gap-2 px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                  title="Export Story"
                >
                  <Download className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        </div>

        {!hasContent && !isGenerating && (
          <div className="text-center py-8 text-gray-500">
            <p className="mb-4">Create compelling data stories with embedded visualizations</p>
            <p className="text-sm">Click "Generate Story" to create an automated narrative based on your volunteer data</p>
          </div>
        )}
      </div>

      {/* Notebook Cells */}
      {cells.map((cell, index) => (
        <NotebookCell
          key={cell.id}
          cell={cell}
          index={index}
          volunteerData={volunteerData}
          onUpdate={updateCell}
          onDelete={deleteCell}
          onToggleEdit={toggleCellEdit}
          onAddCell={addCell}
        />
      ))}

      {hasContent && (
        <div className="text-center py-4">
          <button
            onClick={() => addCell("text")}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg border-2 border-dashed border-gray-300"
          >
            <Plus className="w-4 h-4" />
            Add Cell
          </button>
        </div>
      )}
    </div>
  );
}