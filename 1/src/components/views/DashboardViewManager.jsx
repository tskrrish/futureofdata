import React, { useState } from 'react';
import { Eye, Edit, Share2, Trash2, Star, MoreVertical, Folder, Users, Building } from 'lucide-react';
import { DASHBOARD_VIEW_ROLES } from '../../services/dashboardViewService';

export function DashboardViewManager({ 
  personalViews, 
  branchViews, 
  organizationViews, 
  currentView,
  onApplyView,
  onEditView,
  onDeleteView,
  onShareView,
  onSetDefault,
  canEditView,
  canShareView,
  canDeleteView
}) {
  const [activeTab, setActiveTab] = useState('personal');
  const [expandedView, setExpandedView] = useState(null);

  const getRoleIcon = (role) => {
    switch (role) {
      case DASHBOARD_VIEW_ROLES.PERSONAL:
        return <Folder className="w-4 h-4" />;
      case DASHBOARD_VIEW_ROLES.BRANCH:
        return <Users className="w-4 h-4" />;
      case DASHBOARD_VIEW_ROLES.ORGANIZATION:
        return <Building className="w-4 h-4" />;
      default:
        return <Folder className="w-4 h-4" />;
    }
  };

  const ViewCard = ({ view }) => {
    const isExpanded = expandedView === view.id;
    const isCurrent = currentView?.id === view.id;
    
    return (
      <div className={`border rounded-lg p-4 ${isCurrent ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'}`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              {getRoleIcon(view.role)}
              <h3 className="font-medium text-gray-900">{view.name}</h3>
              {view.isDefault && <Star className="w-4 h-4 text-yellow-500 fill-current" />}
              {isCurrent && (
                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                  Current
                </span>
              )}
            </div>
            
            {view.description && (
              <p className="text-sm text-gray-600 mb-2">{view.description}</p>
            )}
            
            <div className="text-xs text-gray-500">
              <span>Owner: {view.owner}</span>
              <span className="mx-2">•</span>
              <span>Updated: {new Date(view.updatedAt).toLocaleDateString()}</span>
              {view.sharedWith && view.sharedWith.length > 0 && (
                <>
                  <span className="mx-2">•</span>
                  <span>Shared with {view.sharedWith.length} user{view.sharedWith.length !== 1 ? 's' : ''}</span>
                </>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-1">
            <button
              onClick={() => onApplyView(view)}
              className="p-1 hover:bg-gray-100 rounded text-gray-600 hover:text-gray-900"
              title="Apply this view"
            >
              <Eye className="w-4 h-4" />
            </button>
            
            <div className="relative">
              <button
                onClick={() => setExpandedView(isExpanded ? null : view.id)}
                className="p-1 hover:bg-gray-100 rounded text-gray-600 hover:text-gray-900"
              >
                <MoreVertical className="w-4 h-4" />
              </button>
              
              {isExpanded && (
                <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-32">
                  {canEditView(view) && (
                    <button
                      onClick={() => {
                        onEditView(view);
                        setExpandedView(null);
                      }}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                    >
                      <Edit className="w-3 h-3" />
                      Edit
                    </button>
                  )}
                  
                  {canShareView(view) && (
                    <button
                      onClick={() => {
                        onShareView(view);
                        setExpandedView(null);
                      }}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                    >
                      <Share2 className="w-3 h-3" />
                      Share
                    </button>
                  )}
                  
                  {canEditView(view) && (
                    <button
                      onClick={() => {
                        onSetDefault(view.id, view.role);
                        setExpandedView(null);
                      }}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                    >
                      <Star className="w-3 h-3" />
                      {view.isDefault ? 'Unset Default' : 'Set Default'}
                    </button>
                  )}
                  
                  {canDeleteView(view) && (
                    <button
                      onClick={() => {
                        if (confirm('Are you sure you want to delete this view?')) {
                          onDeleteView(view.id);
                        }
                        setExpandedView(null);
                      }}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 text-red-600 flex items-center gap-2"
                    >
                      <Trash2 className="w-3 h-3" />
                      Delete
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        
        {isExpanded && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <h4 className="text-xs font-medium text-gray-700 mb-2">View Settings:</h4>
            <div className="text-xs text-gray-600 space-y-1">
              <div>Branch Filter: {view.config?.branchFilter || 'All'}</div>
              <div>Search: {view.config?.search || 'None'}</div>
              <div>Active Tab: {view.config?.activeTab || 'overview'}</div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const ViewSection = ({ views, emptyMessage }) => (
    <div className="space-y-3">
      {views.length > 0 ? (
        views.map(view => <ViewCard key={view.id} view={view} />)
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p>{emptyMessage}</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Dashboard Views</h2>
        
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('personal')}
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              activeTab === 'personal' 
                ? 'border-blue-500 text-blue-600' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <Folder className="w-4 h-4" />
              Personal ({personalViews.length})
            </div>
          </button>
          <button
            onClick={() => setActiveTab('branch')}
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              activeTab === 'branch' 
                ? 'border-blue-500 text-blue-600' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Branch ({branchViews.length})
            </div>
          </button>
          <button
            onClick={() => setActiveTab('organization')}
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              activeTab === 'organization' 
                ? 'border-blue-500 text-blue-600' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <Building className="w-4 h-4" />
              Organization ({organizationViews.length})
            </div>
          </button>
        </div>
      </div>
      
      <div className="p-4">
        {activeTab === 'personal' && (
          <ViewSection 
            views={personalViews}
            emptyMessage="No personal views saved. Create your first personal dashboard view!"
          />
        )}
        
        {activeTab === 'branch' && (
          <ViewSection 
            views={branchViews}
            emptyMessage="No branch views available. Create or ask your branch admin to share views."
          />
        )}
        
        {activeTab === 'organization' && (
          <ViewSection 
            views={organizationViews}
            emptyMessage="No organization views available."
          />
        )}
      </div>
    </div>
  );
}

export default DashboardViewManager;