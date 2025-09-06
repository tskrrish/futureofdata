import React from 'react';
import { SKILLS_CATEGORIES } from '../../data/skillsData';

const SkillsHeatmapChart = ({ volunteers, onVolunteerClick }) => {
  const getProficiencyColor = (proficiency, certified = false) => {
    const baseColors = {
      expert: certified ? 'bg-green-600' : 'bg-green-500',
      proficient: certified ? 'bg-blue-600' : 'bg-blue-500', 
      beginner: 'bg-yellow-400',
      none: 'bg-gray-200'
    };
    return baseColors[proficiency] || baseColors.none;
  };

  const getProficiencyLevel = (volunteer, categorySkills) => {
    const skills = volunteer.skillsByCategory[categorySkills]?.skills || [];
    if (skills.length === 0) return { level: 'none', certified: false };
    
    const expertSkills = skills.filter(s => s.proficiency === 'expert');
    const proficientSkills = skills.filter(s => s.proficiency === 'proficient');
    const hasCertified = skills.some(s => s.certified);
    
    if (expertSkills.length > 0) return { level: 'expert', certified: hasCertified };
    if (proficientSkills.length > 0) return { level: 'proficient', certified: hasCertified };
    return { level: 'beginner', certified: hasCertified };
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <h3 className="text-lg font-semibold mb-4">Skills Coverage Heatmap</h3>
      
      <div className="overflow-x-auto">
        <div className="min-w-max">
          {/* Header with categories */}
          <div className="flex mb-2">
            <div className="w-48 font-medium text-sm text-gray-600 py-2">Volunteer</div>
            {Object.values(SKILLS_CATEGORIES).map(category => (
              <div key={category} className="w-32 text-xs font-medium text-gray-600 text-center py-2 border-l">
                {category.replace(' & ', '\n& ')}
              </div>
            ))}
            <div className="w-24 text-xs font-medium text-gray-600 text-center py-2 border-l">Total Skills</div>
          </div>
          
          {/* Volunteer rows */}
          {volunteers.map(volunteer => (
            <div 
              key={volunteer.id} 
              className="flex hover:bg-gray-50 cursor-pointer rounded"
              onClick={() => onVolunteerClick?.(volunteer)}
            >
              <div className="w-48 py-3 px-2">
                <div className="font-medium text-sm">{volunteer.name}</div>
                <div className="text-xs text-gray-500">{volunteer.branch}</div>
              </div>
              
              {Object.values(SKILLS_CATEGORIES).map(category => {
                const { level, certified } = getProficiencyLevel(volunteer, category);
                const categoryData = volunteer.skillsByCategory[category];
                
                return (
                  <div key={category} className="w-32 py-3 px-2 border-l text-center">
                    <div className={`w-full h-8 rounded flex items-center justify-center ${getProficiencyColor(level, certified)}`}>
                      <span className="text-xs font-medium text-white">
                        {categoryData ? `${categoryData.covered}/${categoryData.total}` : '0/0'}
                      </span>
                      {certified && (
                        <span className="ml-1 text-xs">✓</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {categoryData ? Math.round(categoryData.coverage) : 0}%
                    </div>
                  </div>
                );
              })}
              
              <div className="w-24 py-3 px-2 border-l text-center">
                <div className="text-lg font-semibold text-blue-600">{volunteer.totalSkills}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Legend */}
      <div className="mt-6 flex flex-wrap items-center gap-4 text-xs">
        <span className="font-medium text-gray-600">Proficiency Levels:</span>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span>Expert</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-blue-500 rounded"></div>
          <span>Proficient</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-yellow-400 rounded"></div>
          <span>Beginner</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-gray-200 rounded"></div>
          <span>No Skills</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-green-600 rounded"></div>
          <span>✓ Certified</span>
        </div>
      </div>
    </div>
  );
};

export default SkillsHeatmapChart;