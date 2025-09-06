import React, { useState } from 'react';
import { MessageSquare, Calendar, MapPin, Clock } from 'lucide-react';
import { ProjectModal } from './ProjectModal';
import { useComments } from '../../hooks/useComments';

export function ProjectsList({ data, title = "Recent Projects" }) {
  const [selectedProject, setSelectedProject] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { getCommentCount } = useComments();

  const handleProjectClick = (project) => {
    setSelectedProject(project);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedProject(null);
  };

  const getProjectId = (project) => `${project.project}_${project.branch}_${project.date}`;

  return (
    <div className="rounded-2xl border bg-white p-4">
      <h3 className="font-semibold mb-3">{title}</h3>
      <div className="space-y-3">
        {data.slice(0, 10).map((project, i) => {
          const projectId = getProjectId(project);
          const commentCount = getCommentCount('project', projectId);
          
          return (
            <div
              key={i}
              onClick={() => handleProjectClick(project)}
              className="p-3 rounded-lg border bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors"
            >
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium text-sm leading-tight">{project.project}</h4>
                {commentCount > 0 && (
                  <div className="flex items-center gap-1 text-xs text-blue-600">
                    <MessageSquare className="w-3 h-3" />
                    {commentCount}
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <div className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {project.branch}
                </div>
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {new Date(project.date).toLocaleDateString()}
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {project.hours}h
                </div>
              </div>
              
              <div className="mt-2">
                <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                  {project.category}
                </span>
              </div>
            </div>
          );
        })}
      </div>
      
      <ProjectModal
        project={selectedProject}
        isOpen={isModalOpen}
        onClose={closeModal}
      />
    </div>
  );
}