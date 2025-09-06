import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import {
  BarChart3,
  PieChart,
  TrendingUp,
  Users,
  Filter,
  Calendar,
  Search,
  Hash,
  Type,
  Layout
} from 'lucide-react';

const SECTIONS = [
  {
    id: 'header-section',
    type: 'header',
    icon: <Type className="w-5 h-5" />,
    title: 'Header Section',
    description: 'Add titles and descriptions'
  },
  {
    id: 'kpi-section', 
    type: 'kpi',
    icon: <Hash className="w-5 h-5" />,
    title: 'KPI Cards',
    description: 'Key performance indicators'
  },
  {
    id: 'divider-section',
    type: 'divider', 
    icon: <Layout className="w-5 h-5" />,
    title: 'Divider',
    description: 'Visual separator'
  }
];

const METRICS = [
  {
    id: 'total-hours-metric',
    type: 'metric',
    icon: <BarChart3 className="w-5 h-5" />,
    title: 'Total Hours',
    description: 'Sum of all volunteer hours',
    config: { metric: 'totalHours', aggregation: 'sum' }
  },
  {
    id: 'active-volunteers-metric', 
    type: 'metric',
    icon: <Users className="w-5 h-5" />,
    title: 'Active Volunteers',
    description: 'Count of active volunteers',
    config: { metric: 'activeVolunteers', aggregation: 'count' }
  },
  {
    id: 'hours-by-branch-chart',
    type: 'chart',
    icon: <BarChart3 className="w-5 h-5" />,
    title: 'Hours by Branch',
    description: 'Bar chart of hours per branch',
    config: { chartType: 'bar', xAxis: 'branch', yAxis: 'hours' }
  },
  {
    id: 'member-share-chart',
    type: 'chart', 
    icon: <PieChart className="w-5 h-5" />,
    title: 'Member Share',
    description: 'Pie chart of member distribution',
    config: { chartType: 'pie', metric: 'memberShare' }
  },
  {
    id: 'monthly-trend-chart',
    type: 'chart',
    icon: <TrendingUp className="w-5 h-5" />,
    title: 'Monthly Trend', 
    description: 'Line chart showing trends over time',
    config: { chartType: 'line', xAxis: 'month', yAxis: 'hours' }
  }
];

const FILTERS = [
  {
    id: 'branch-filter',
    type: 'filter',
    icon: <Filter className="w-5 h-5" />,
    title: 'Branch Filter',
    description: 'Filter by branch location',
    config: { filterType: 'select', field: 'branch' }
  },
  {
    id: 'date-filter',
    type: 'filter', 
    icon: <Calendar className="w-5 h-5" />,
    title: 'Date Range Filter',
    description: 'Filter by date range',
    config: { filterType: 'dateRange', field: 'date' }
  },
  {
    id: 'search-filter',
    type: 'filter',
    icon: <Search className="w-5 h-5" />,
    title: 'Search Filter',
    description: 'Text search across records',
    config: { filterType: 'search', field: 'name' }
  }
];

function DraggableItem({ item, category }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({
    id: item.id,
    data: {
      type: item.type,
      config: item.config,
      category: category
    },
  });

  const style = transform ? {
    transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
  } : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={`
        p-3 bg-white border border-neutral-200 rounded-lg cursor-grab hover:border-blue-300 hover:shadow-sm transition-all
        ${isDragging ? 'opacity-50' : ''}
        active:cursor-grabbing
      `}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 text-neutral-600">
          {item.icon}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-neutral-900 mb-1">
            {item.title}
          </h4>
          <p className="text-xs text-neutral-600 leading-relaxed">
            {item.description}
          </p>
        </div>
      </div>
    </div>
  );
}

function ToolboxSection({ title, items, category }) {
  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-neutral-800 mb-3 px-4">
        {title}
      </h3>
      <div className="space-y-2 px-4">
        {items.map(item => (
          <DraggableItem
            key={item.id}
            item={item}
            category={category}
          />
        ))}
      </div>
    </div>
  );
}

export function DraggableToolbox() {
  return (
    <div className="flex-1 overflow-y-auto py-4">
      <ToolboxSection 
        title="Layout Sections" 
        items={SECTIONS} 
        category="sections"
      />
      <ToolboxSection 
        title="Metrics & Charts" 
        items={METRICS} 
        category="metrics"
      />
      <ToolboxSection 
        title="Filters" 
        items={FILTERS} 
        category="filters"
      />
    </div>
  );
}