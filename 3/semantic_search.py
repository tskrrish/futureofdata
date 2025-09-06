"""
Semantic Search Engine for YMCA Volunteer PathFinder
Provides vector embeddings and semantic similarity search across volunteer data
"""

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Optional, Any, Tuple
import json
import pickle
import os
from datetime import datetime
import logging

class SemanticSearchEngine:
    """
    Semantic search engine that can find people and opportunities by meaning
    Uses sentence transformers for vector embeddings and cosine similarity for matching
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the semantic search engine
        
        Args:
            model_name: HuggingFace sentence transformer model name
        """
        self.model_name = model_name
        self.model = None
        self.volunteer_embeddings = None
        self.project_embeddings = None
        self.volunteer_data = None
        self.project_data = None
        self.is_initialized = False
        
        # Cache file paths
        self.cache_dir = "cache"
        self.volunteer_cache_file = os.path.join(self.cache_dir, "volunteer_embeddings.pkl")
        self.project_cache_file = os.path.join(self.cache_dir, "project_embeddings.pkl")
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def initialize(self, volunteer_data: pd.DataFrame, project_data: pd.DataFrame):
        """
        Initialize the search engine with data
        
        Args:
            volunteer_data: DataFrame with volunteer profiles and history
            project_data: DataFrame with project/opportunity information
        """
        self.logger.info("Initializing semantic search engine...")
        
        # Load the sentence transformer model
        self.model = SentenceTransformer(self.model_name)
        
        # Store data
        self.volunteer_data = volunteer_data.copy()
        self.project_data = project_data.copy()
        
        # Create searchable text representations
        self._create_volunteer_search_text()
        self._create_project_search_text()
        
        # Generate or load embeddings
        self._load_or_generate_embeddings()
        
        self.is_initialized = True
        self.logger.info("Semantic search engine initialized successfully!")
    
    def _create_volunteer_search_text(self):
        """Create searchable text representations for volunteers"""
        if self.volunteer_data is None:
            return
        
        search_texts = []
        for idx, volunteer in self.volunteer_data.iterrows():
            # Build comprehensive text representation
            text_parts = []
            
            # Basic info
            if pd.notna(volunteer.get('first_name')):
                text_parts.append(f"Name: {volunteer.get('first_name', '')} {volunteer.get('last_name', '')}")
            
            if pd.notna(volunteer.get('age')):
                text_parts.append(f"Age: {volunteer['age']}")
            
            if pd.notna(volunteer.get('gender')):
                text_parts.append(f"Gender: {volunteer['gender']}")
            
            if pd.notna(volunteer.get('volunteer_type')):
                text_parts.append(f"Volunteer type: {volunteer['volunteer_type']}")
            
            # Skills and experience
            if pd.notna(volunteer.get('skills')):
                text_parts.append(f"Skills: {volunteer['skills']}")
            
            # Project history and interests
            if pd.notna(volunteer.get('project_category')):
                text_parts.append(f"Experience in: {volunteer['project_category']}")
            
            if pd.notna(volunteer.get('project_clean')):
                text_parts.append(f"Previous projects: {volunteer['project_clean']}")
            
            # Branch preferences
            if pd.notna(volunteer.get('branch_short')):
                text_parts.append(f"Location: {volunteer['branch_short']}")
            
            # Availability and commitment
            if pd.notna(volunteer.get('hours')):
                text_parts.append(f"Hours contributed: {volunteer['hours']}")
            
            # Join all parts
            search_text = " | ".join(text_parts) if text_parts else "Volunteer profile"
            search_texts.append(search_text)
        
        self.volunteer_data['search_text'] = search_texts
    
    def _create_project_search_text(self):
        """Create searchable text representations for projects"""
        if self.project_data is None:
            return
        
        search_texts = []
        for idx, project in self.project_data.iterrows():
            text_parts = []
            
            # Project name and description
            if pd.notna(project.get('project_clean')):
                text_parts.append(f"Project: {project['project_clean']}")
            
            if pd.notna(project.get('project_category')):
                text_parts.append(f"Category: {project['project_category']}")
            
            # Branch location
            if pd.notna(project.get('branch_short')):
                text_parts.append(f"Location: {project['branch_short']}")
            
            # Requirements or description
            if pd.notna(project.get('description')):
                text_parts.append(f"Description: {project['description']}")
            
            # Skills needed
            if pd.notna(project.get('skills_needed')):
                text_parts.append(f"Skills needed: {project['skills_needed']}")
            
            # Time commitment
            if pd.notna(project.get('time_commitment')):
                text_parts.append(f"Time commitment: {project['time_commitment']}")
            
            search_text = " | ".join(text_parts) if text_parts else "Volunteer opportunity"
            search_texts.append(search_text)
        
        self.project_data['search_text'] = search_texts
    
    def _load_or_generate_embeddings(self):
        """Load cached embeddings or generate new ones"""
        volunteer_cache_exists = os.path.exists(self.volunteer_cache_file)
        project_cache_exists = os.path.exists(self.project_cache_file)
        
        # Generate volunteer embeddings
        if volunteer_cache_exists:
            self.logger.info("Loading cached volunteer embeddings...")
            with open(self.volunteer_cache_file, 'rb') as f:
                self.volunteer_embeddings = pickle.load(f)
        else:
            self.logger.info("Generating volunteer embeddings...")
            volunteer_texts = self.volunteer_data['search_text'].tolist()
            self.volunteer_embeddings = self.model.encode(volunteer_texts, convert_to_tensor=False)
            
            # Cache the embeddings
            with open(self.volunteer_cache_file, 'wb') as f:
                pickle.dump(self.volunteer_embeddings, f)
        
        # Generate project embeddings
        if project_cache_exists:
            self.logger.info("Loading cached project embeddings...")
            with open(self.project_cache_file, 'rb') as f:
                self.project_embeddings = pickle.load(f)
        else:
            self.logger.info("Generating project embeddings...")
            project_texts = self.project_data['search_text'].tolist()
            self.project_embeddings = self.model.encode(project_texts, convert_to_tensor=False)
            
            # Cache the embeddings
            with open(self.project_cache_file, 'wb') as f:
                pickle.dump(self.project_embeddings, f)
    
    def search_volunteers(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for volunteers by semantic meaning
        
        Args:
            query: Natural language query (e.g., "experienced youth mentors")
            top_k: Number of top results to return
            
        Returns:
            List of volunteer matches with similarity scores
        """
        if not self.is_initialized:
            raise RuntimeError("Semantic search engine not initialized")
        
        # Encode the query
        query_embedding = self.model.encode([query], convert_to_tensor=False)
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.volunteer_embeddings)[0]
        
        # Get top matches
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            volunteer = self.volunteer_data.iloc[idx]
            result = {
                'id': idx,
                'contact_id': volunteer.get('contact_id'),
                'name': f"{volunteer.get('first_name', '')} {volunteer.get('last_name', '')}".strip(),
                'volunteer_type': volunteer.get('volunteer_type'),
                'age': volunteer.get('age'),
                'gender': volunteer.get('gender'),
                'branch': volunteer.get('branch_short'),
                'experience': volunteer.get('project_category'),
                'hours': volunteer.get('hours'),
                'search_text': volunteer.get('search_text'),
                'similarity_score': float(similarities[idx]),
                'matched_on': query
            }
            results.append(result)
        
        return results
    
    def search_opportunities(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for opportunities/projects by semantic meaning
        
        Args:
            query: Natural language query (e.g., "youth development programs")
            top_k: Number of top results to return
            
        Returns:
            List of opportunity matches with similarity scores
        """
        if not self.is_initialized:
            raise RuntimeError("Semantic search engine not initialized")
        
        # Encode the query
        query_embedding = self.model.encode([query], convert_to_tensor=False)
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.project_embeddings)[0]
        
        # Get top matches
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            project = self.project_data.iloc[idx]
            result = {
                'id': idx,
                'project_id': project.get('project_id'),
                'name': project.get('project_clean'),
                'category': project.get('project_category'),
                'branch': project.get('branch_short'),
                'description': project.get('description', project.get('search_text', '')),
                'skills_needed': project.get('skills_needed'),
                'time_commitment': project.get('time_commitment'),
                'similarity_score': float(similarities[idx]),
                'matched_on': query
            }
            results.append(result)
        
        return results
    
    def search_combined(self, query: str, volunteer_count: int = 5, opportunity_count: int = 5) -> Dict[str, Any]:
        """
        Search both volunteers and opportunities with a single query
        
        Args:
            query: Natural language search query
            volunteer_count: Number of volunteer results
            opportunity_count: Number of opportunity results
            
        Returns:
            Combined search results
        """
        volunteers = self.search_volunteers(query, volunteer_count)
        opportunities = self.search_opportunities(query, opportunity_count)
        
        return {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'volunteers': volunteers,
            'opportunities': opportunities,
            'total_results': len(volunteers) + len(opportunities)
        }
    
    def find_similar_volunteers(self, contact_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find volunteers similar to a given volunteer
        
        Args:
            contact_id: ID of the reference volunteer
            top_k: Number of similar volunteers to return
            
        Returns:
            List of similar volunteers
        """
        if not self.is_initialized:
            raise RuntimeError("Semantic search engine not initialized")
        
        # Find the reference volunteer
        ref_volunteer = self.volunteer_data[self.volunteer_data['contact_id'] == contact_id]
        if ref_volunteer.empty:
            return []
        
        ref_idx = ref_volunteer.index[0]
        ref_embedding = self.volunteer_embeddings[ref_idx].reshape(1, -1)
        
        # Calculate similarities
        similarities = cosine_similarity(ref_embedding, self.volunteer_embeddings)[0]
        
        # Exclude the reference volunteer itself
        similarities[ref_idx] = -1
        
        # Get top matches
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] <= 0:  # Skip if no meaningful similarity
                continue
                
            volunteer = self.volunteer_data.iloc[idx]
            result = {
                'id': idx,
                'contact_id': volunteer.get('contact_id'),
                'name': f"{volunteer.get('first_name', '')} {volunteer.get('last_name', '')}".strip(),
                'volunteer_type': volunteer.get('volunteer_type'),
                'age': volunteer.get('age'),
                'branch': volunteer.get('branch_short'),
                'experience': volunteer.get('project_category'),
                'similarity_score': float(similarities[idx])
            }
            results.append(result)
        
        return results
    
    def get_search_suggestions(self, partial_query: str, max_suggestions: int = 5) -> List[str]:
        """
        Generate search suggestions based on partial query
        
        Args:
            partial_query: Partial search query
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested search terms
        """
        suggestions = []
        
        # Common volunteer-related search patterns
        volunteer_patterns = [
            "experienced youth mentors",
            "fitness instructors",
            "administrative volunteers", 
            "special events coordinators",
            "senior volunteers over 50",
            "volunteers with childcare experience",
            "coaches and sports volunteers",
            "volunteers interested in leadership"
        ]
        
        opportunity_patterns = [
            "youth development programs",
            "fitness and wellness opportunities",
            "special events and fundraising",
            "administrative and office support",
            "coaching and sports programs",
            "childcare and summer camps",
            "community outreach programs"
        ]
        
        all_patterns = volunteer_patterns + opportunity_patterns
        
        # Filter patterns that match partial query
        for pattern in all_patterns:
            if partial_query.lower() in pattern.lower():
                suggestions.append(pattern)
        
        return suggestions[:max_suggestions]
    
    def refresh_embeddings(self):
        """
        Refresh embeddings (useful when data changes)
        """
        self.logger.info("Refreshing embeddings...")
        
        # Remove cached files
        if os.path.exists(self.volunteer_cache_file):
            os.remove(self.volunteer_cache_file)
        if os.path.exists(self.project_cache_file):
            os.remove(self.project_cache_file)
        
        # Regenerate embeddings
        self._load_or_generate_embeddings()
        
        self.logger.info("Embeddings refreshed successfully!")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the semantic search engine
        
        Returns:
            Dictionary with engine statistics
        """
        if not self.is_initialized:
            return {"initialized": False}
        
        return {
            "initialized": True,
            "model_name": self.model_name,
            "volunteer_count": len(self.volunteer_data) if self.volunteer_data is not None else 0,
            "opportunity_count": len(self.project_data) if self.project_data is not None else 0,
            "embedding_dimensions": self.volunteer_embeddings.shape[1] if self.volunteer_embeddings is not None else 0,
            "cache_dir": self.cache_dir,
            "cache_files_exist": {
                "volunteers": os.path.exists(self.volunteer_cache_file),
                "projects": os.path.exists(self.project_cache_file)
            }
        }