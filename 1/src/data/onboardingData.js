export const ONBOARDING_STEPS = [
  {
    id: 'personal-info',
    title: 'Personal Information',
    description: 'Complete personal details and emergency contact information',
    category: 'basic',
    required: true,
    order: 1
  },
  {
    id: 'background-check',
    title: 'Background Check',
    description: 'Submit and complete background check verification',
    category: 'verification',
    required: true,
    order: 2
  },
  {
    id: 'liability-waiver',
    title: 'Liability Waiver',
    description: 'Sign liability waiver and release forms',
    category: 'signature',
    required: true,
    order: 3
  },
  {
    id: 'safety-training',
    title: 'Safety Training',
    description: 'Complete mandatory safety and emergency procedures training',
    category: 'training',
    required: true,
    order: 4
  },
  {
    id: 'orientation',
    title: 'Volunteer Orientation',
    description: 'Attend volunteer orientation session',
    category: 'training',
    required: true,
    order: 5
  },
  {
    id: 'confidentiality-agreement',
    title: 'Confidentiality Agreement',
    description: 'Sign confidentiality and privacy agreement',
    category: 'signature',
    required: true,
    order: 6
  },
  {
    id: 'photo-consent',
    title: 'Photo Consent',
    description: 'Provide consent for photography and media use',
    category: 'signature',
    required: false,
    order: 7
  },
  {
    id: 'specialty-training',
    title: 'Specialty Training',
    description: 'Complete role-specific training modules',
    category: 'training',
    required: false,
    order: 8
  }
];

export const SAMPLE_VOLUNTEERS = [
  {
    id: 'vol-001',
    name: 'John Smith',
    email: 'john.smith@email.com',
    phone: '555-0123',
    startDate: '2024-01-15',
    branch: 'Downtown',
    steps: {
      'personal-info': { 
        completed: true, 
        completedDate: '2024-01-15', 
        completedBy: 'self',
        notes: 'All information verified' 
      },
      'background-check': { 
        completed: true, 
        completedDate: '2024-01-18', 
        completedBy: 'hr-manager',
        notes: 'Background check cleared' 
      },
      'liability-waiver': { 
        completed: true, 
        completedDate: '2024-01-16', 
        completedBy: 'self',
        signatureUrl: '/signatures/john-smith-waiver.pdf' 
      },
      'safety-training': { 
        completed: true, 
        completedDate: '2024-01-20', 
        completedBy: 'trainer-001',
        certificateUrl: '/certificates/john-smith-safety.pdf' 
      },
      'orientation': { 
        completed: true, 
        completedDate: '2024-01-22', 
        completedBy: 'coordinator',
        notes: 'Attended group orientation session' 
      },
      'confidentiality-agreement': { 
        completed: true, 
        completedDate: '2024-01-22', 
        completedBy: 'self',
        signatureUrl: '/signatures/john-smith-confidentiality.pdf' 
      },
      'photo-consent': { 
        completed: true, 
        completedDate: '2024-01-22', 
        completedBy: 'self',
        signatureUrl: '/signatures/john-smith-photo-consent.pdf' 
      },
      'specialty-training': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'Pending assignment to specific role' 
      }
    }
  },
  {
    id: 'vol-002',
    name: 'Sarah Johnson',
    email: 'sarah.j@email.com',
    phone: '555-0456',
    startDate: '2024-02-01',
    branch: 'West Side',
    steps: {
      'personal-info': { 
        completed: true, 
        completedDate: '2024-02-01', 
        completedBy: 'self',
        notes: 'Contact information updated' 
      },
      'background-check': { 
        completed: true, 
        completedDate: '2024-02-03', 
        completedBy: 'hr-manager',
        notes: 'Background check cleared' 
      },
      'liability-waiver': { 
        completed: true, 
        completedDate: '2024-02-02', 
        completedBy: 'self',
        signatureUrl: '/signatures/sarah-johnson-waiver.pdf' 
      },
      'safety-training': { 
        completed: true, 
        completedDate: '2024-02-05', 
        completedBy: 'trainer-002',
        certificateUrl: '/certificates/sarah-johnson-safety.pdf' 
      },
      'orientation': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'Scheduled for next session' 
      },
      'confidentiality-agreement': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'Awaiting signature' 
      },
      'photo-consent': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'Declined photo consent' 
      },
      'specialty-training': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'Will complete after orientation' 
      }
    }
  },
  {
    id: 'vol-003',
    name: 'Mike Chen',
    email: 'mike.chen@email.com',
    phone: '555-0789',
    startDate: '2024-02-15',
    branch: 'East Side',
    steps: {
      'personal-info': { 
        completed: true, 
        completedDate: '2024-02-15', 
        completedBy: 'self',
        notes: 'All required fields completed' 
      },
      'background-check': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'Submitted, pending results' 
      },
      'liability-waiver': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'Form sent via email' 
      },
      'safety-training': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'Will schedule after background check' 
      },
      'orientation': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'TBD' 
      },
      'confidentiality-agreement': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'TBD' 
      },
      'photo-consent': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'TBD' 
      },
      'specialty-training': { 
        completed: false, 
        completedDate: null, 
        completedBy: null,
        notes: 'TBD' 
      }
    }
  }
];

export const getVolunteerProgress = (volunteer) => {
  const requiredSteps = ONBOARDING_STEPS.filter(step => step.required);
  const completedRequired = requiredSteps.filter(step => 
    volunteer.steps[step.id]?.completed
  ).length;
  
  const allSteps = ONBOARDING_STEPS;
  const completedAll = allSteps.filter(step => 
    volunteer.steps[step.id]?.completed
  ).length;
  
  return {
    requiredComplete: completedRequired,
    requiredTotal: requiredSteps.length,
    allComplete: completedAll,
    allTotal: allSteps.length,
    isFullyOnboarded: completedRequired === requiredSteps.length,
    progressPercentage: Math.round((completedRequired / requiredSteps.length) * 100)
  };
};

export const getStepsByCategory = () => {
  const categories = {
    basic: ONBOARDING_STEPS.filter(step => step.category === 'basic'),
    verification: ONBOARDING_STEPS.filter(step => step.category === 'verification'),
    signature: ONBOARDING_STEPS.filter(step => step.category === 'signature'),
    training: ONBOARDING_STEPS.filter(step => step.category === 'training')
  };
  
  return categories;
};