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
from database import DatabaseManager
from utils import generate_synthetic_responses, generate_survey_questions

# Page configuration
st.set_page_config(
    page_title="Theme Evolution System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
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
    
    /* Hide Streamlit footer */
    footer[data-testid="stFooter"] {
        display: none;
    }
    
    /* Hide "Made with Streamlit" text */
    .stApp > footer {
        display: none;
    }
    
    /* Prevent sidebar from being collapsible */
    .stSidebar .stCollapsible {
        display: block !important;
    }
    
    /* Hide sidebar collapse button */
    .stSidebar .stButton button[aria-label="Close sidebar"] {
        display: none !important;
    }
    
    /* Force sidebar to stay open */
    .stSidebar {
        min-width: 300px !important;
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
if 'batches_generated' not in st.session_state:
    st.session_state.batches_generated = 0
if 'batches_processed' not in st.session_state:
    st.session_state.batches_processed = 0

def initialize_processor():
    """Initialize the theme processor"""
    try:
        # Load config from YAML file
        import yaml
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return ThemeProcessor(config)
    except Exception as e:
        st.toast(f"❌ Failed to initialize theme processor: {str(e)}", icon="❌")
        return None

def generate_question():
    """Generate a random survey question"""
    questions = generate_survey_questions(1)
    return questions[0] if questions else "What are your thoughts on technology in education?"

def reset_session_data():
    """Reset all session data when a new question is generated"""
    st.session_state.responses = []
    st.session_state.themes = []
    st.session_state.assignments = []
    st.session_state.batch_count = 0
    st.session_state.batches_generated = 0
    st.session_state.batches_processed = 0
    if 'current_page' in st.session_state:
        st.session_state.current_page = 1
    # Keep current_question as it will be set by the button

def process_batch(processor, responses):
    """Process a batch of responses"""
    try:
        with st.spinner("Processing batch..."):
            # Create BatchData object
            from models import BatchData
            batch_data = BatchData(
                batch_id=st.session_state.batch_count + 1,
                question=st.session_state.current_question,
                responses=[r.response_text for r in responses]
            )
            
            # Process the batch using ThemeProcessor
            result = processor.process_batch(batch_data)
            
            # Extract themes from the result
            themes = []
            for theme_data in result.new_themes + result.updated_themes:
                from models import Theme
                theme = Theme(
                    id=theme_data.get('id'),
                    name=theme_data.get('name', ''),
                    description=theme_data.get('description', ''),
                    created_at_batch=st.session_state.batch_count + 1,
                    status='active'
                )
                themes.append(theme)
            
            # Create mock assignments for now (since the result doesn't include them directly)
            assignments = []
            for i, response in enumerate(responses):
                from models import ThemeAssignment, HighlightedKeyword
                if themes:
                    # Assign to first theme for simplicity
                    assignment = ThemeAssignment(
                        response_id=response.id or i,
                        theme_id=themes[0].id or 1,
                        confidence_score=0.8,
                        highlighted_keywords=[HighlightedKeyword(keyword="sample", score=0.5)],
                        assigned_at_batch=st.session_state.batch_count + 1
                    )
                    assignments.append(assignment)
            
            return themes, assignments, themes  # Return themes as evolved_themes for now
    except Exception as e:
        st.toast(f"❌ Error processing batch: {str(e)}", icon="❌")
        return [], [], []

def process_batch_with_progress(processor, responses, progress_bar, status_text):
    """Process a batch of responses with progress updates"""
    try:
        import time
        
        # Step 1: Prepare data
        status_text.text("🔄 Preparing batch data...")
        progress_bar.progress(10)
        time.sleep(0.5)
        
        
        # Process in smaller chunks to avoid timeout
        chunk_size = 25  # Process 25 responses at a time
        all_themes = []
        all_assignments = []
        
        for i in range(0, len(responses), chunk_size):
            chunk_responses = responses[i:i + chunk_size]
            chunk_progress = 10 + (i / len(responses)) * 80
            
            status_text.text(f"🧠 Processing chunk {i//chunk_size + 1}/{(len(responses)-1)//chunk_size + 1} ({len(chunk_responses)} responses)...")
            progress_bar.progress(int(chunk_progress))
            
            from models import BatchData
            batch_data = BatchData(
                batch_id=st.session_state.batch_count + 1,
                question=st.session_state.current_question,
                responses=[r.response_text for r in chunk_responses]
            )
            
            try:
                # Process the chunk using ThemeProcessor
                result = processor.process_batch(batch_data)
                
                # Extract themes from the result
                chunk_themes = []
                for theme_data in result.new_themes + result.updated_themes:
                    from models import Theme
                    theme = Theme(
                        id=theme_data.get('id'),
                        name=theme_data.get('name', ''),
                        description=theme_data.get('description', ''),
                        created_at_batch=st.session_state.batch_count + 1,
                        status='active'
                    )
                    chunk_themes.append(theme)
                
                all_themes.extend(chunk_themes)
                
                # Create mock assignments for this chunk
                for j, response in enumerate(chunk_responses):
                    from models import ThemeAssignment, HighlightedKeyword
                    if chunk_themes:
                        # Assign to first theme for simplicity
                        assignment = ThemeAssignment(
                            response_id=response.id or (i + j),
                            theme_id=chunk_themes[0].id or 1,
                            confidence_score=0.8,
                            highlighted_keywords=[HighlightedKeyword(keyword="sample", score=0.5)],
                            assigned_at_batch=st.session_state.batch_count + 1
                        )
                        all_assignments.append(assignment)
                
                except Exception as chunk_error:
                    st.toast(f"⚠️ Chunk {i//chunk_size + 1} failed: {str(chunk_error)}", icon="⚠️")
                    continue
        
        # Step 4: Process results
        status_text.text("📊 Processing results...")
        progress_bar.progress(90)
        time.sleep(0.5)
        
        # Step 5: Complete
        status_text.text("✅ Processing complete!")
        progress_bar.progress(100)
        time.sleep(0.5)
        
        return all_themes, all_assignments, all_themes  # Return themes as evolved_themes for now
    except Exception as e:
        st.toast(f"❌ Error processing batch: {str(e)}", icon="❌")
        return [], [], []

def main():
    # Header
    st.markdown('<h1 class="main-header">🧠 Theme Evolution System</h1>', unsafe_allow_html=True)
    
    # Display current question in main panel (if exists)
    if st.session_state.current_question:
        st.markdown("### 📋 Current Survey Question")
        st.info(st.session_state.current_question)
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Generate question button
        if st.button("🎯 Generate Random Question", use_container_width=True):
            # Reset all data when generating a new question
            reset_session_data()
            st.session_state.current_question = generate_question()
            st.toast("✅ New question generated! All previous data has been reset.", icon="✅")
        
        st.markdown("---")
        
        # Generate responses button with random count
        if st.button("📝 Generate Random Responses", use_container_width=True):
            if not st.session_state.current_question:
                st.toast("⚠️ Please generate a question first!", icon="⚠️")
            else:
                # Generate random number of responses (50-200)
                import random
                response_count = random.randint(50, 200)
                with st.spinner(f"Generating {response_count} responses..."):
                    responses = generate_synthetic_responses(
                        st.session_state.current_question, 
                        response_count
                    )
                    st.session_state.responses.extend(responses)
                    st.session_state.batches_generated += 1
                    st.toast(f"✅ Generated {response_count} responses! (Batch #{st.session_state.batches_generated})", icon="✅")
        
        st.markdown("---")
        
        # Process batch button
        if st.button("⚡ Process New Batch", use_container_width=True):
            if not st.session_state.responses:
                st.toast("⚠️ Please generate responses first!", icon="⚠️")
            else:
                processor = initialize_processor()
                if processor:
                    # Get the latest batch (last 100 responses)
                    latest_batch = st.session_state.responses[-100:]
                    themes, assignments, evolved_themes = process_batch(processor, latest_batch)
                    
                    # Update session state
                    st.session_state.themes.extend(themes)
                    st.session_state.assignments.extend(assignments)
                    st.session_state.batches_processed += 1
                    
                    st.toast(f"✅ Batch processed successfully! ({st.session_state.batches_processed} total processed)", icon="✅")
        
        st.markdown("---")
        
        # Clear data button
        if st.button("🗑️ Clear All Data", use_container_width=True):
            st.session_state.themes = []
            st.session_state.responses = []
            st.session_state.assignments = []
            st.session_state.current_question = ""
            st.session_state.batch_count = 0
            st.session_state.batches_generated = 0
            st.session_state.batches_processed = 0
            if 'current_page' in st.session_state:
                st.session_state.current_page = 1
            st.toast("🗑️ All data cleared!", icon="🗑️")
    
    # Main content area
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Responses", len(st.session_state.responses))
    
    with col2:
        st.metric("🎯 Themes Found", len(st.session_state.themes))
    
    with col3:
        st.metric("📦 Batches Generated", st.session_state.batches_generated)
    
    with col4:
        st.metric("✅ Batches Processed", st.session_state.batches_processed)
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "🎯 Themes", "📝 Responses", "🔍 Analysis", "📐 Metrics"])
    
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
                
                # Responses matching this theme
                st.subheader("📝 Responses Matching This Theme")
                theme_assignments = [a for a in st.session_state.assignments if a.theme_id == theme.id]
                
                if theme_assignments:
                    st.info(f"Found {len(theme_assignments)} responses matching this theme")
                    
                    # Show sample responses
                    for i, assignment in enumerate(theme_assignments[:5]):
                        response = next((r for r in st.session_state.responses if r.id == assignment.response_id), None)
                        if response:
                            with st.expander(f"Sample Response {i+1} (Similarity: {assignment.similarity_score:.2f})"):
                                st.write(response.response_text)
                    
                    if len(theme_assignments) > 5:
                        st.caption(f"Showing 5 of {len(theme_assignments)} responses. View all in the 'Responses' tab.")
                else:
                    st.info("No responses matched to this theme yet. Process a batch to see matches.")
        else:
            st.info("No themes available. Process a batch to see themes!")
    
    with tab3:
        st.header("📝 All Responses")
        
        if st.session_state.responses:
            # Response statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_length = sum(len(r.response_text) for r in st.session_state.responses) / len(st.session_state.responses)
                st.metric("📏 Avg Response Length", f"{avg_length:.0f} chars")
            
            with col2:
                st.metric("📦 Total Responses", len(st.session_state.responses))
            
            with col3:
                st.metric("📊 Batches Generated", st.session_state.batches_generated)
            
            st.markdown("---")
            
            # Pagination controls
            responses_per_page = 20
            total_pages = (len(st.session_state.responses) - 1) // responses_per_page + 1
            
            # Initialize page number in session state
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1
            
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("⏮️ First", disabled=(st.session_state.current_page == 1)):
                    st.session_state.current_page = 1
                    st.rerun()
            
            with col2:
                if st.button("◀️ Prev", disabled=(st.session_state.current_page == 1)):
                    st.session_state.current_page -= 1
                    st.rerun()
            
            with col3:
                st.markdown(f"<div style='text-align: center; padding: 8px;'>Page {st.session_state.current_page} of {total_pages}</div>", unsafe_allow_html=True)
            
            with col4:
                if st.button("Next ▶️", disabled=(st.session_state.current_page == total_pages)):
                    st.session_state.current_page += 1
                    st.rerun()
            
            with col5:
                if st.button("Last ⏭️", disabled=(st.session_state.current_page == total_pages)):
                    st.session_state.current_page = total_pages
                    st.rerun()
            
            st.markdown("---")
            
            # Display responses for current page
            start_idx = (st.session_state.current_page - 1) * responses_per_page
            end_idx = min(start_idx + responses_per_page, len(st.session_state.responses))
            
            st.subheader(f"Showing responses {start_idx + 1}-{end_idx} of {len(st.session_state.responses)}")
            
            for i in range(start_idx, end_idx):
                response = st.session_state.responses[i]
                with st.expander(f"📝 Response #{i + 1} (Batch {response.batch_id})"):
                    st.write(response.response_text)
                    st.caption(f"Length: {len(response.response_text)} characters")
                    if response.processed_at:
                        st.caption(f"Processed: {response.processed_at}")
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
    
    with tab5:
        st.header("📐 Metrics")
        
        # Only show metrics if we have processed data
        if st.session_state.batch_count > 0 and st.session_state.themes:
            # Performance Metrics
            st.subheader("🚀 Performance Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Processing Throughput: R = N/T
                total_responses = len(st.session_state.responses)
                if hasattr(st.session_state, 'total_processing_time') and st.session_state.total_processing_time > 0:
                    throughput = total_responses / st.session_state.total_processing_time
                    st.metric("Processing Throughput", f"{throughput:.2f} responses/sec", 
                            help="R = N/T (responses per second)")
                else:
                    st.metric("Processing Throughput", "Calculating...", 
                            help="R = N/T (responses per second)")
            
            with col2:
                # Memory Efficiency: M = (Peak_Memory / Dataset_Size) × 100%
                if hasattr(st.session_state, 'peak_memory_usage') and hasattr(st.session_state, 'dataset_size'):
                    memory_efficiency = (st.session_state.peak_memory_usage / st.session_state.dataset_size) * 100
                    st.metric("Memory Efficiency", f"{memory_efficiency:.2f}%", 
                            help="M = (Peak_Memory / Dataset_Size) × 100%")
                else:
                    st.metric("Memory Efficiency", "Calculating...", 
                            help="M = (Peak_Memory / Dataset_Size) × 100%")
            
            with col3:
                # Context Window Utilization: U = (Used_Tokens / Max_Tokens) × 100%
                if hasattr(st.session_state, 'avg_tokens_used') and hasattr(st.session_state, 'max_tokens'):
                    utilization = (st.session_state.avg_tokens_used / st.session_state.max_tokens) * 100
                    st.metric("Context Utilization", f"{utilization:.2f}%", 
                            help="U = (Used_Tokens / Max_Tokens) × 100%")
                else:
                    st.metric("Context Utilization", "Calculating...", 
                            help="U = (Used_Tokens / Max_Tokens) × 100%")
            
            # Accuracy Metrics
            st.subheader("🎯 Accuracy Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Theme Consistency Score: C = (1 - |T_i - T_j|/|T_i + T_j|) × 100%
                if len(st.session_state.themes) > 1:
                    # Simplified consistency calculation
                    theme_confidences = [theme.confidence for theme in st.session_state.themes]
                    consistency = (1 - (max(theme_confidences) - min(theme_confidences)) / 
                                (max(theme_confidences) + min(theme_confidences))) * 100
                    st.metric("Theme Consistency", f"{consistency:.2f}%", 
                            help="C = (1 - |T_i - T_j|/|T_i + T_j|) × 100%")
                else:
                    st.metric("Theme Consistency", "N/A", 
                            help="C = (1 - |T_i - T_j|/|T_i + T_j|) × 100%")
            
            with col2:
                # Cosine Similarity Accuracy: S = (1/n) × Σ(cos(θ_i))
                if st.session_state.assignments:
                    avg_similarity = sum(a.similarity_score for a in st.session_state.assignments) / len(st.session_state.assignments)
                    st.metric("Avg Similarity", f"{avg_similarity:.3f}", 
                            help="S = (1/n) × Σ(cos(θ_i))")
                else:
                    st.metric("Avg Similarity", "N/A", 
                            help="S = (1/n) × Σ(cos(θ_i))")
            
            with col3:
                # Retroactive Update Precision: P = (Correct_Updates / Total_Updates) × 100%
                if hasattr(st.session_state, 'correct_updates') and hasattr(st.session_state, 'total_updates'):
                    if st.session_state.total_updates > 0:
                        precision = (st.session_state.correct_updates / st.session_state.total_updates) * 100
                        st.metric("Update Precision", f"{precision:.2f}%", 
                                help="P = (Correct_Updates / Total_Updates) × 100%")
                    else:
                        st.metric("Update Precision", "N/A", 
                                help="P = (Correct_Updates / Total_Updates) × 100%")
                else:
                    st.metric("Update Precision", "N/A", 
                            help="P = (Correct_Updates / Total_Updates) × 100%")
            
            # Scalability Metrics
            st.subheader("📈 Scalability Metrics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Batch Processing Efficiency: E = (Processing_Time / Batch_Size) × 1000
                if hasattr(st.session_state, 'avg_batch_time') and hasattr(st.session_state, 'avg_batch_size'):
                    efficiency = (st.session_state.avg_batch_time / st.session_state.avg_batch_size) * 1000
                    st.metric("Batch Efficiency", f"{efficiency:.2f} ms/response", 
                            help="E = (Processing_Time / Batch_Size) × 1000")
                else:
                    st.metric("Batch Efficiency", "Calculating...", 
                            help="E = (Processing_Time / Batch_Size) × 1000")
            
            with col2:
                # Database Query Performance: Q = (Query_Time / Dataset_Size) × 1000
                if hasattr(st.session_state, 'avg_query_time') and hasattr(st.session_state, 'dataset_size'):
                    query_perf = (st.session_state.avg_query_time / st.session_state.dataset_size) * 1000
                    st.metric("Query Performance", f"{query_perf:.2f} ms/response", 
                            help="Q = (Query_Time / Dataset_Size) × 1000")
                else:
                    st.metric("Query Performance", "Calculating...", 
                            help="Q = (Query_Time / Dataset_Size) × 1000")
            
            # Statistical Analysis
            st.subheader("📊 Statistical Analysis")
            
            if st.session_state.assignments:
                # Similarity distribution
                similarity_scores = [a.similarity_score for a in st.session_state.assignments]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Similarity Distribution")
                    fig = px.histogram(x=similarity_scores, title="Similarity Score Distribution",
                                     labels={'x': 'Similarity Score', 'y': 'Frequency'})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("Statistical Summary")
                    import numpy as np
                    
                    mean_sim = np.mean(similarity_scores)
                    std_sim = np.std(similarity_scores)
                    median_sim = np.median(similarity_scores)
                    
                    st.metric("Mean Similarity", f"{mean_sim:.3f}")
                    st.metric("Std Deviation", f"{std_sim:.3f}")
                    st.metric("Median Similarity", f"{median_sim:.3f}")
            
            # Target Performance Indicators
            st.subheader("🎯 Target Performance Indicators")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Performance Targets:**")
                st.markdown("- Throughput: >1000 responses/sec")
                st.markdown("- Memory: <10% overhead")
                st.markdown("- Context: >85% utilization")
            
            with col2:
                st.markdown("**Accuracy Targets:**")
                st.markdown("- Consistency: >90%")
                st.markdown("- Similarity: >0.8")
                st.markdown("- Precision: >95%")
            
            with col3:
                st.markdown("**Scalability Targets:**")
                st.markdown("- Linear scaling: O(n)")
                st.markdown("- Query time: <100ms")
                st.markdown("- Memory bounds: O(batch_size)")
        
        else:
            st.info("👆 Generate responses and click 'Process New Batch' to see metrics!")
    
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
