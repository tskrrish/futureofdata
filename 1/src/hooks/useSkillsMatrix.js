import { useMemo } from 'react';
import { SKILLS_DATA, SKILLS_CATEGORIES, VOLUNTEER_SKILLS, TRAINING_PROGRAMS } from '../data/skillsData';

export function useSkillsMatrix(volunteerData = []) {
  return useMemo(() => {
    // Get unique volunteers from the data
    const volunteers = [...new Set(volunteerData.map(record => record.assignee))]
      .map(name => ({
        id: name.toLowerCase().replace(/\s+/g, '-'),
        name,
        branch: volunteerData.find(record => record.assignee === name)?.branch || '',
        totalHours: volunteerData
          .filter(record => record.assignee === name)
          .reduce((sum, record) => sum + record.hours, 0)
      }));

    // Calculate skill coverage for each volunteer
    const skillsCoverage = volunteers.map(volunteer => {
      const volunteerSkills = VOLUNTEER_SKILLS.filter(skill => skill.volunteerId === volunteer.id);
      
      const skillsByCategory = Object.values(SKILLS_CATEGORIES).reduce((acc, category) => {
        const categorySkills = SKILLS_DATA.filter(skill => skill.category === category);
        const volunteerCategorySkills = volunteerSkills.filter(vSkill => 
          categorySkills.some(skill => skill.id === vSkill.skillId)
        );
        
        acc[category] = {
          total: categorySkills.length,
          covered: volunteerCategorySkills.length,
          coverage: categorySkills.length > 0 ? (volunteerCategorySkills.length / categorySkills.length) * 100 : 0,
          skills: volunteerCategorySkills.map(vSkill => {
            const skillData = SKILLS_DATA.find(s => s.id === vSkill.skillId);
            return {
              ...vSkill,
              ...skillData
            };
          })
        };
        return acc;
      }, {});

      return {
        ...volunteer,
        totalSkills: volunteerSkills.length,
        skillsByCategory
      };
    });

    // Calculate overall skill gaps across the organization
    const organizationGaps = SKILLS_DATA.map(skill => {
      const volunteers = VOLUNTEER_SKILLS.filter(vSkill => vSkill.skillId === skill.id);
      const expertCount = volunteers.filter(v => v.proficiency === 'expert').length;
      const proficientCount = volunteers.filter(v => v.proficiency === 'proficient').length;
      const beginnerCount = volunteers.filter(v => v.proficiency === 'beginner').length;
      const totalCount = volunteers.length;
      
      // Determine gap severity based on coverage and skill level requirement
      let gapSeverity = 'low';
      if (skill.level === 'essential' && expertCount < 2) gapSeverity = 'critical';
      else if (skill.level === 'intermediate' && (expertCount + proficientCount) < 3) gapSeverity = 'high';
      else if (skill.level === 'advanced' && expertCount < 1) gapSeverity = 'medium';

      return {
        ...skill,
        coverage: {
          expert: expertCount,
          proficient: proficientCount,
          beginner: beginnerCount,
          total: totalCount,
          percentage: totalCount > 0 ? (totalCount / volunteers.length) * 100 : 0
        },
        gapSeverity,
        recommendedTraining: TRAINING_PROGRAMS.filter(program => 
          program.skillsAddressed.includes(skill.id)
        )
      };
    });

    // Calculate category-level statistics
    const categoryStats = Object.values(SKILLS_CATEGORIES).map(category => {
      const categorySkills = organizationGaps.filter(skill => skill.category === category);
      const totalVolunteersWithSkills = [...new Set(
        VOLUNTEER_SKILLS
          .filter(vSkill => categorySkills.some(skill => skill.id === vSkill.skillId))
          .map(vSkill => vSkill.volunteerId)
      )].length;

      return {
        category,
        totalSkills: categorySkills.length,
        averageCoverage: categorySkills.reduce((sum, skill) => sum + skill.coverage.total, 0) / categorySkills.length,
        criticalGaps: categorySkills.filter(skill => skill.gapSeverity === 'critical').length,
        highGaps: categorySkills.filter(skill => skill.gapSeverity === 'high').length,
        volunteersWithSkills: totalVolunteersWithSkills
      };
    });

    // Generate training recommendations
    const trainingRecommendations = organizationGaps
      .filter(skill => ['critical', 'high'].includes(skill.gapSeverity))
      .flatMap(skill => skill.recommendedTraining)
      .reduce((unique, program) => {
        if (!unique.find(p => p.id === program.id)) {
          const priority = organizationGaps
            .filter(skill => program.skillsAddressed.includes(skill.id))
            .reduce((max, skill) => {
              const priorityScore = skill.gapSeverity === 'critical' ? 4 : 
                                 skill.gapSeverity === 'high' ? 3 :
                                 skill.gapSeverity === 'medium' ? 2 : 1;
              return Math.max(max, priorityScore);
            }, 0);

          unique.push({
            ...program,
            priority: priority === 4 ? 'critical' : priority === 3 ? 'high' : 'medium',
            skillsGapCount: organizationGaps.filter(skill => 
              program.skillsAddressed.includes(skill.id) && 
              ['critical', 'high'].includes(skill.gapSeverity)
            ).length
          });
        }
        return unique;
      }, [])
      .sort((a, b) => {
        const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      });

    return {
      volunteers: skillsCoverage,
      organizationGaps,
      categoryStats,
      trainingRecommendations,
      totalSkills: SKILLS_DATA.length,
      totalVolunteers: volunteers.length
    };
  }, [volunteerData]);
}