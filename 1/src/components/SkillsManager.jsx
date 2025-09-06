import React, { useState } from 'react';
import { Plus, Edit2, Trash2, Tag, User, Award, AlertCircle } from 'lucide-react';
import { SKILLS_DATA, SKILLS_CATEGORIES, VOLUNTEER_SKILLS } from '../data/skillsData';

const SkillsManager = ({ volunteers }) => {
  const [viewMode, setViewMode] = useState('volunteers'); // 'volunteers' or 'skills'
  const [searchFilter, setSearchFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');

  const getVolunteerSkills = (volunteerId) => {
    return VOLUNTEER_SKILLS.filter(skill => skill.volunteerId === volunteerId)
      .map(vSkill => ({
        ...vSkill,
        skillData: SKILLS_DATA.find(s => s.id === vSkill.skillId)
      }));
  };

  const getSkillVolunteers = (skillId) => {
    return VOLUNTEER_SKILLS.filter(vSkill => vSkill.skillId === skillId)
      .map(vSkill => ({
        ...vSkill,
        volunteerData: volunteers.find(v => v.id === vSkill.volunteerId)
      }));
  };

  const getProficiencyBadge = (proficiency, certified = false) => {
    const baseStyle = "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium";
    const styles = {
      expert: `${baseStyle} ${certified ? 'bg-green-100 text-green-800' : 'bg-green-50 text-green-600'}`,
      proficient: `${baseStyle} ${certified ? 'bg-blue-100 text-blue-800' : 'bg-blue-50 text-blue-600'}`,
      beginner: `${baseStyle} bg-yellow-50 text-yellow-600`
    };
    
    return (
      <span className={styles[proficiency] || styles.beginner}>
        {proficiency}
        {certified && <Award className="w-3 h-3" />}
      </span>
    );
  };

  const filteredVolunteers = volunteers.filter(volunteer => 
    volunteer.name.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const filteredSkills = SKILLS_DATA.filter(skill => {
    const matchesSearch = skill.name.toLowerCase().includes(searchFilter.toLowerCase());
    const matchesCategory = categoryFilter === 'All' || skill.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const VolunteerSkillsView = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search volunteers..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="grid gap-4">
        {filteredVolunteers.map(volunteer => {
          const volunteerSkills = getVolunteerSkills(volunteer.id);
          
          return (
            <div key={volunteer.id} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{volunteer.name}</h3>
                    <p className="text-sm text-gray-600">{volunteer.branch} • {volunteer.totalHours.toFixed(1)}h</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">{volunteerSkills.length} skills</span>
                  <button
                    onClick={() => {
                      // TODO: Implement add skill functionality
                      console.log('Add skill for:', volunteer.name);
                    }}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-md"
                    title="Add skill"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {volunteerSkills.length > 0 ? (
                <div className="space-y-3">
                  {Object.values(SKILLS_CATEGORIES).map(category => {
                    const categorySkills = volunteerSkills.filter(
                      skill => skill.skillData?.category === category
                    );
                    
                    if (categorySkills.length === 0) return null;
                    
                    return (
                      <div key={category} className="space-y-2">
                        <h4 className="text-sm font-medium text-gray-700">{category}</h4>
                        <div className="flex flex-wrap gap-2">
                          {categorySkills.map(skill => (
                            <div key={skill.skillId} className="flex items-center gap-2 bg-gray-50 rounded-lg p-2">
                              <div>
                                <div className="text-sm font-medium text-gray-900">
                                  {skill.skillData?.name}
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                  {getProficiencyBadge(skill.proficiency, skill.certified)}
                                  <span className="text-xs text-gray-500">
                                    Updated {new Date(skill.lastUpdated).toLocaleDateString()}
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">
                  <Tag className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No skills tagged yet</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

  const SkillsLibraryView = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search skills..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="All">All Categories</option>
          {Object.values(SKILLS_CATEGORIES).map(category => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>
      </div>

      <div className="grid gap-4">
        {filteredSkills.map(skill => {
          const skillVolunteers = getSkillVolunteers(skill.id);
          const expertCount = skillVolunteers.filter(v => v.proficiency === 'expert').length;
          const proficientCount = skillVolunteers.filter(v => v.proficiency === 'proficient').length;
          const beginnerCount = skillVolunteers.filter(v => v.proficiency === 'beginner').length;
          
          return (
            <div key={skill.id} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    skill.level === 'essential' ? 'bg-red-500' :
                    skill.level === 'intermediate' ? 'bg-yellow-500' : 'bg-blue-500'
                  }`}></div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{skill.name}</h3>
                    <p className="text-sm text-gray-600">{skill.category} • {skill.level} level</p>
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {skillVolunteers.length} volunteers
                </div>
              </div>

              {skillVolunteers.length > 0 ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 bg-green-500 rounded"></div>
                      <span>Expert: {expertCount}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 bg-blue-500 rounded"></div>
                      <span>Proficient: {proficientCount}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                      <span>Beginner: {beginnerCount}</span>
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-2">
                    {skillVolunteers.slice(0, 5).map(skillVolunteer => (
                      <div key={skillVolunteer.volunteerId} className="flex items-center gap-1 bg-gray-50 rounded px-2 py-1">
                        <span className="text-xs font-medium">
                          {skillVolunteer.volunteerData?.name}
                        </span>
                        {getProficiencyBadge(skillVolunteer.proficiency, skillVolunteer.certified)}
                      </div>
                    ))}
                    {skillVolunteers.length > 5 && (
                      <span className="text-xs text-gray-500 px-2 py-1">
                        +{skillVolunteers.length - 5} more
                      </span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-orange-600 text-sm">
                  <AlertCircle className="w-4 h-4" />
                  <span>No volunteers have this skill</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Skills Management</h2>
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('volunteers')}
            className={`px-4 py-2 rounded text-sm font-medium ${
              viewMode === 'volunteers' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            By Volunteers
          </button>
          <button
            onClick={() => setViewMode('skills')}
            className={`px-4 py-2 rounded text-sm font-medium ${
              viewMode === 'skills' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Skills Library
          </button>
        </div>
      </div>

      {viewMode === 'volunteers' ? <VolunteerSkillsView /> : <SkillsLibraryView />}
    </div>
  );
};

export default SkillsManager;