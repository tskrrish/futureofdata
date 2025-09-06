import React from 'react';
import { X, Calendar, MapPin, Tag, Users } from 'lucide-react';
import { CommentsSection } from '../comments/CommentsSection';

export function ProjectModal({ project, isOpen, onClose }) {
  if (!isOpen || !project) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold">{project.project}</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-6">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600">Branch:</span>
                <span className="font-medium">{project.branch}</span>
              </div>
              
              <div className="flex items-center gap-2">
                <Tag className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600">Category:</span>
                <span className="font-medium">{project.category}</span>
              </div>
              
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600">Department:</span>
                <span className="font-medium">{project.department}</span>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600">Date:</span>
                <span className="font-medium">{new Date(project.date).toLocaleDateString()}</span>
              </div>
              
              <div>
                <span className="text-sm text-gray-600">Project Tag:</span>
                <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                  {project.project_tag}
                </span>
              </div>
              
              <div>
                <span className="text-sm text-gray-600">Catalog:</span>
                <span className="ml-2 font-medium">{project.project_catalog}</span>
              </div>
            </div>
          </div>
          
          <div className="border-t pt-6">
            <CommentsSection
              entityType="project"
              entityId={`${project.project}_${project.branch}_${project.date}`}
              entityName={project.project}
            />
          </div>
        </div>
      </div>
    </div>
  );
}