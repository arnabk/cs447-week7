import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import SurveyResponse, Theme, ThemeAssignment
from theme_processor import ThemeProcessor
from database import Database
from utils import generate_synthetic_responses, generate_survey_questions

# Page configuration
st.set_page_config(
    page_title="Theme Evolution System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
    }
    
    .success-message {
        background: #d1fae5;
        color: #065f46;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #10b981;
    }
    
    .info-message {
        background: #dbeafe;
        color: #1e40af;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
    }
    
    .warning-message {
        background: #fef3c7;
        color: #92400e;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #f59e0b;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'themes' not in st.session_state:
    st.session_state.themes = []
if 'responses' not in st.session_state:
    st.session_state.responses = []
if 'assignments' not in st.session_state:
    st.session_state.assignments = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""
if 'batch_count' not in st.session_state:
    st.session_state.batch_count = 0

def initialize_processor():
    """Initialize the theme processor"""
    try:
        return ThemeProcessor()
    except Exception as e:
        st.error(f"Failed to initialize theme processor: {str(e)}")
        return None

def generate_question():
    """Generate a random survey question"""
    questions = generate_survey_questions(1)
    return questions[0] if questions else "What are your thoughts on technology in education?"

def process_batch(processor, responses):
    """Process a batch of responses"""
    try:
        with st.spinner("Processing batch..."):
            # Extract themes
            themes = processor.extract_themes(responses)
            
            # Highlight keywords
            assignments = processor.highlight_keywords(responses, themes)
            
            # Evolve themes
            evolved_themes = processor.evolve_themes(themes)
            
            return themes, assignments, evolved_themes
    except Exception as e:
        st.error(f"Error processing batch: {str(e)}")
        return [], [], []

def main():
    # Header
    st.markdown('<h1 class="main-header">🧠 Theme Evolution System</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Generate question button
        if st.button("🎯 Generate Random Question", use_container_width=True):
            st.session_state.current_question = generate_question()
            st.success("New question generated!")
        
        # Display current question
        if st.session_state.current_question:
            st.markdown("**Current Question:**")
            st.info(st.session_state.current_question)
        
        st.markdown("---")
        
        # Generate responses button
        if st.button("📝 Generate 100 Responses", use_container_width=True):
            if not st.session_state.current_question:
                st.warning("Please generate a question first!")
            else:
                with st.spinner("Generating responses..."):
                    responses = generate_synthetic_responses(
                        st.session_state.current_question, 
                        100
                    )
                    st.session_state.responses.extend(responses)
                    st.session_state.batch_count += 1
                    st.success(f"Generated 100 responses! (Batch #{st.session_state.batch_count})")
        
        st.markdown("---")
        
        # Process batch button
        if st.button("⚡ Process New Batch", use_container_width=True):
            if not st.session_state.responses:
                st.warning("Please generate responses first!")
            else:
                processor = initialize_processor()
                if processor:
                    # Get the latest batch (last 100 responses)
                    latest_batch = st.session_state.responses[-100:]
                    themes, assignments, evolved_themes = process_batch(processor, latest_batch)
                    
                    # Update session state
                    st.session_state.themes.extend(themes)
                    st.session_state.assignments.extend(assignments)
                    
                    st.success("Batch processed successfully!")
        
        st.markdown("---")
        
        # Clear data button
        if st.button("🗑️ Clear All Data", use_container_width=True):
            st.session_state.themes = []
            st.session_state.responses = []
            st.session_state.assignments = []
            st.session_state.current_question = ""
            st.session_state.batch_count = 0
            st.success("All data cleared!")
    
    # Main content area
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Responses", len(st.session_state.responses))
    
    with col2:
        st.metric("🎯 Themes Found", len(st.session_state.themes))
    
    with col3:
        st.metric("📦 Batches Processed", st.session_state.batch_count)
    
    with col4:
        st.metric("🔗 Assignments", len(st.session_state.assignments))
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🎯 Themes", "📝 Responses", "🔍 Analysis"])
    
    with tab1:
        st.header("📊 System Dashboard")
        
        if st.session_state.themes:
            # Theme distribution
            theme_data = []
            for theme in st.session_state.themes:
                theme_data.append({
                    'Theme': theme.name,
                    'Confidence': theme.confidence,
                    'Response Count': len([a for a in st.session_state.assignments if a.theme_id == theme.id])
                })
            
            df_themes = pd.DataFrame(theme_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎯 Theme Distribution")
                fig = px.pie(df_themes, values='Response Count', names='Theme', 
                           title="Response Distribution by Theme")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("📈 Theme Confidence")
                fig = px.bar(df_themes, x='Theme', y='Confidence', 
                           title="Theme Confidence Scores")
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent themes
            st.subheader("🆕 Recent Themes")
            for theme in st.session_state.themes[-5:]:
                with st.expander(f"🎯 {theme.name} (Confidence: {theme.confidence:.2f})"):
                    st.write(f"**Description:** {theme.description}")
                    st.write(f"**Keywords:** {', '.join(theme.keywords[:10])}")
                    st.write(f"**Created:** {theme.created_at}")
        else:
            st.info("No themes found yet. Generate responses and process a batch to see themes!")
    
    with tab2:
        st.header("🎯 Theme Details")
        
        if st.session_state.themes:
            theme_names = [theme.name for theme in st.session_state.themes]
            selected_theme = st.selectbox("Select Theme to View Details:", theme_names)
            
            if selected_theme:
                theme = next(t for t in st.session_state.themes if t.name == selected_theme)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📋 Theme Information")
                    st.write(f"**Name:** {theme.name}")
                    st.write(f"**Description:** {theme.description}")
                    st.write(f"**Confidence:** {theme.confidence:.2f}")
                    st.write(f"**Status:** {theme.status}")
                    st.write(f"**Created:** {theme.created_at}")
                
                with col2:
                    st.subheader("🔑 Keywords")
                    keywords_df = pd.DataFrame({
                        'Keyword': theme.keywords,
                        'Importance': [1.0] * len(theme.keywords)  # Placeholder
                    })
                    st.dataframe(keywords_df, use_container_width=True)
                
                # Responses assigned to this theme
                st.subheader("📝 Assigned Responses")
                theme_assignments = [a for a in st.session_state.assignments if a.theme_id == theme.id]
                
                if theme_assignments:
                    assignment_data = []
                    for assignment in theme_assignments:
                        response = next(r for r in st.session_state.responses if r.id == assignment.response_id)
                        assignment_data.append({
                            'Response': response.text[:100] + "..." if len(response.text) > 100 else response.text,
                            'Similarity': assignment.similarity_score,
                            'Keywords': ', '.join(assignment.highlighted_keywords[:5])
                        })
                    
                    st.dataframe(pd.DataFrame(assignment_data), use_container_width=True)
                else:
                    st.info("No responses assigned to this theme yet.")
        else:
            st.info("No themes available. Process a batch to see themes!")
    
    with tab3:
        st.header("📝 Response Analysis")
        
        if st.session_state.responses:
            # Response statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_length = sum(len(r.text) for r in st.session_state.responses) / len(st.session_state.responses)
                st.metric("📏 Avg Response Length", f"{avg_length:.0f} chars")
            
            with col2:
                st.metric("📦 Total Responses", len(st.session_state.responses))
            
            with col3:
                assigned_count = len(st.session_state.assignments)
                st.metric("🔗 Assigned Responses", assigned_count)
            
            # Response length distribution
            response_lengths = [len(r.text) for r in st.session_state.responses]
            fig = px.histogram(x=response_lengths, title="Response Length Distribution")
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent responses
            st.subheader("📝 Recent Responses")
            for i, response in enumerate(st.session_state.responses[-10:]):
                with st.expander(f"Response #{len(st.session_state.responses) - 9 + i}"):
                    st.write(response.text)
                    st.write(f"**Batch:** {response.batch_id}")
                    st.write(f"**Created:** {response.created_at}")
        else:
            st.info("No responses available. Generate responses to see them here!")
    
    with tab4:
        st.header("🔍 Advanced Analysis")
        
        if st.session_state.themes and st.session_state.assignments:
            # Theme evolution analysis
            st.subheader("🔄 Theme Evolution")
            
            # Simulate theme evolution over time
            evolution_data = []
            for i, theme in enumerate(st.session_state.themes):
                evolution_data.append({
                    'Theme': theme.name,
                    'Batch': i + 1,
                    'Confidence': theme.confidence,
                    'Response Count': len([a for a in st.session_state.assignments if a.theme_id == theme.id])
                })
            
            if evolution_data:
                df_evolution = pd.DataFrame(evolution_data)
                fig = px.line(df_evolution, x='Batch', y='Confidence', color='Theme',
                            title="Theme Confidence Over Time")
                st.plotly_chart(fig, use_container_width=True)
            
            # Keyword analysis
            st.subheader("🔑 Keyword Analysis")
            all_keywords = []
            for theme in st.session_state.themes:
                all_keywords.extend(theme.keywords)
            
            if all_keywords:
                keyword_counts = pd.Series(all_keywords).value_counts().head(20)
                fig = px.bar(x=keyword_counts.index, y=keyword_counts.values,
                           title="Top Keywords")
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            # Similarity analysis
            st.subheader("📊 Similarity Analysis")
            similarity_scores = [a.similarity_score for a in st.session_state.assignments]
            if similarity_scores:
                fig = px.histogram(x=similarity_scores, title="Similarity Score Distribution")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Process some batches to see advanced analysis!")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6b7280; padding: 2rem;'>
        <p>🧠 Theme Evolution System - Powered by Streamlit & Ollama</p>
        <p>Process large-scale survey responses with intelligent theme extraction and evolution</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
