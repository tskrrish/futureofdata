
      </div>
      
      <AdvancedFilters 
        showAdvancedFiltering={showAdvancedFiltering}
        onFiltersChange={(filters) => {
          console.log('Advanced filters changed:', filters);
          // In a real implementation, you'd apply these filters
        }}
      />
    </div>
  );
}