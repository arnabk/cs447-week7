"""
Utility functions for the theme evolution system.
"""

import json
import logging
import yaml
import random
from typing import Dict, Any, List
from pathlib import Path

from models import BatchData, SurveyResponse


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logging.error(f"Failed to load config from {config_path}: {e}")
        raise


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_batch_data(data_path: str) -> List[BatchData]:
    """Load batch data from JSON file."""
    try:
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        batches = []
        for batch_dict in data:
            batch = BatchData(
                batch_id=batch_dict['batch_id'],
                question=batch_dict['question'],
                responses=batch_dict['responses']
            )
            batches.append(batch)
        
        return batches
    except Exception as e:
        logging.error(f"Failed to load batch data from {data_path}: {e}")
        raise


def save_processing_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save processing results to JSON file."""
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logging.info(f"Results saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save results to {output_path}: {e}")
        raise


def create_output_directory(output_dir: str = "outputs") -> None:
    """Create output directory if it doesn't exist."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)


def format_processing_summary(results: List[Dict[str, Any]]) -> str:
    """Format a summary of processing results."""
    if not results:
        return "No results to summarize."
    
    total_batches = len(results)
    total_themes_created = sum(r.get('themes_created', 0) for r in results)
    total_themes_updated = sum(r.get('themes_updated', 0) for r in results)
    total_themes_deleted = sum(r.get('themes_deleted', 0) for r in results)
    total_responses = sum(r.get('total_responses', 0) for r in results)
    avg_processing_time = sum(r.get('processing_time_seconds', 0) for r in results) / total_batches
    
    summary = f"""
Processing Summary:
==================
Total Batches Processed: {total_batches}
Total Responses: {total_responses}
Total Themes Created: {total_themes_created}
Total Themes Updated: {total_themes_updated}
Total Themes Deleted: {total_themes_deleted}
Average Processing Time: {avg_processing_time:.2f} seconds per batch
"""
    
    return summary.strip()


def generate_survey_questions(count: int = 1) -> List[str]:
    """Generate random survey questions for testing."""
    questions = [
        "What are your biggest challenges with remote work?",
        "How do you stay motivated during difficult projects?",
        "What tools do you find most helpful for productivity?",
        "What are your thoughts on artificial intelligence in the workplace?",
        "How has technology changed your daily routine?",
        "What motivates you to learn new skills?",
        "What are your biggest concerns about data privacy?",
        "How do you handle work-life balance?",
        "What are your thoughts on team collaboration tools?",
        "What challenges do you face with project management?",
        "How do you stay organized with multiple tasks?",
        "What are your thoughts on automation in your field?",
        "What motivates you to contribute to open source?",
        "How do you handle difficult conversations at work?",
        "What are your biggest concerns about cybersecurity?",
        "How do you stay updated with industry trends?",
        "What challenges do you face with time management?",
        "What are your thoughts on diversity and inclusion?",
        "How do you handle stress and pressure?",
        "What motivates you to mentor others?"
    ]
    
    return random.sample(questions, min(count, len(questions)))


def generate_synthetic_responses(question: str, count: int = 100) -> List[SurveyResponse]:
    """Generate synthetic survey responses for testing that are relevant to the question."""
    responses = []
    
    # Extract key topics from the question to generate relevant responses
    question_lower = question.lower()
    
    # Response templates based on question type
    if "remote work" in question_lower or "work from home" in question_lower:
        templates = [
            "I struggle with maintaining focus at home due to distractions.",
            "Video calls are exhausting and I miss in-person interactions.",
            "I love the flexibility but miss the office culture.",
            "Setting boundaries between work and personal time is challenging.",
            "I need better equipment and a dedicated workspace.",
            "Communication is harder without face-to-face meetings.",
            "I feel isolated and disconnected from my team.",
            "The lack of structure makes it hard to stay productive.",
            "I enjoy the commute savings but miss the social aspect.",
            "Managing different time zones is difficult."
        ]
    elif "motivation" in question_lower or "motivate" in question_lower:
        templates = [
            "I'm motivated by solving complex problems and learning new things.",
            "Recognition and appreciation from my team keeps me going.",
            "I need clear goals and regular feedback to stay motivated.",
            "Working on meaningful projects that impact users drives me.",
            "I'm motivated by opportunities for career growth and advancement.",
            "Collaborating with talented colleagues inspires me.",
            "I need autonomy and trust to do my best work.",
            "Seeing the results of my efforts motivates me to continue.",
            "I'm motivated by challenges that push me out of my comfort zone.",
            "Having a supportive manager makes all the difference."
        ]
    elif "productivity" in question_lower or "tool" in question_lower:
        templates = [
            "I use task management apps to organize my work and deadlines.",
            "Time blocking helps me focus on specific activities.",
            "I rely on note-taking tools to capture ideas and information.",
            "Calendar apps help me schedule meetings and plan my day.",
            "I use project management software to track progress.",
            "Communication tools like Slack keep me connected with my team.",
            "I use automation tools to reduce repetitive tasks.",
            "Documentation tools help me share knowledge with others.",
            "I use focus apps to minimize distractions during work.",
            "Version control systems help me collaborate on code."
        ]
    elif "artificial intelligence" in question_lower or "ai " in question_lower:
        templates = [
            "AI will augment human capabilities rather than replace jobs.",
            "I'm excited about AI's potential to automate routine tasks.",
            "There are concerns about bias and fairness in AI systems.",
            "AI will require new skills and continuous learning.",
            "Privacy and data security are major concerns with AI.",
            "AI can help make better decisions with data analysis.",
            "There's a need for regulation and ethical guidelines.",
            "AI will transform how we work and interact with technology.",
            "I'm worried about job displacement in certain industries.",
            "AI has the potential to solve complex global challenges."
        ]
    elif "technology" in question_lower or "tech" in question_lower:
        templates = [
            "Technology has made communication faster and more accessible.",
            "I'm concerned about screen time and digital overload.",
            "Technology enables remote collaboration across distances.",
            "There's a learning curve with new technology adoption.",
            "Technology has improved efficiency in many tasks.",
            "I worry about privacy and data security with technology.",
            "Technology helps me stay connected with family and friends.",
            "The pace of technological change can be overwhelming.",
            "Technology has created new opportunities for innovation.",
            "I value technology that simplifies complex tasks."
        ]
    elif "skill" in question_lower or "learn" in question_lower:
        templates = [
            "I'm motivated to learn skills that advance my career.",
            "Continuous learning keeps me competitive in my field.",
            "I learn best through hands-on practice and projects.",
            "Online courses make learning new skills more accessible.",
            "Time constraints make it challenging to learn new skills.",
            "I focus on skills that solve real problems I face.",
            "Peer learning and collaboration enhance skill development.",
            "I'm interested in skills that complement my current expertise.",
            "Learning new skills keeps my work interesting and engaging.",
            "I prioritize skills that have long-term value."
        ]
    elif "privacy" in question_lower or "data" in question_lower:
        templates = [
            "I'm concerned about how companies collect and use my data.",
            "Privacy settings are often too complex to understand.",
            "I use privacy tools like VPNs and encrypted messaging.",
            "Data breaches make me worried about identity theft.",
            "I think there should be stronger data protection laws.",
            "I'm selective about what information I share online.",
            "Companies should be more transparent about data usage.",
            "I delete accounts and apps I no longer use for privacy.",
            "Privacy is a fundamental right that should be protected.",
            "I'm concerned about surveillance and tracking online."
        ]
    elif "work-life balance" in question_lower or "balance" in question_lower:
        templates = [
            "I struggle to disconnect from work during personal time.",
            "Setting clear boundaries helps maintain work-life balance.",
            "I prioritize activities that help me recharge and relax.",
            "My employer supports flexible schedules for better balance.",
            "Burnout is a real concern without proper work-life balance.",
            "I use time management techniques to balance responsibilities.",
            "Exercise and hobbies are essential for my well-being.",
            "I've learned to say no to avoid overcommitment.",
            "Technology makes it harder to maintain work-life boundaries.",
            "I schedule personal time as seriously as work commitments."
        ]
    elif "collaboration" in question_lower or "team" in question_lower:
        templates = [
            "Collaboration tools have improved team communication.",
            "I value diverse perspectives in collaborative projects.",
            "Clear roles and responsibilities are essential for teamwork.",
            "Asynchronous collaboration works well across time zones.",
            "Building trust is fundamental to effective collaboration.",
            "I prefer tools that integrate seamlessly with our workflow.",
            "Regular check-ins help keep the team aligned.",
            "Collaborative documentation prevents knowledge silos.",
            "I appreciate when team members share expertise openly.",
            "Effective collaboration requires active listening and respect."
        ]
    elif "challenge" in question_lower or "difficult" in question_lower or "problem" in question_lower:
        templates = [
            "Time management is my biggest ongoing challenge.",
            "I face difficulties with prioritizing competing demands.",
            "Communication gaps create challenges in project execution.",
            "Resource constraints limit what we can accomplish.",
            "I struggle with maintaining focus amid interruptions.",
            "Adapting to constant change is challenging but necessary.",
            "Technical debt creates problems for long-term projects.",
            "I find it difficult to balance speed with quality.",
            "Unclear requirements lead to rework and frustration.",
            "Building consensus among stakeholders is often challenging."
        ]
    else:
        # Generate responses that directly reference the question
        # Extract key words from the question
        key_words = [word for word in question_lower.split() if len(word) > 4 and word not in ['about', 'what', 'which', 'where', 'when', 'thoughts']]
        topic = key_words[0] if key_words else "this topic"
        
        templates = [
            f"I think {topic} is an important issue that deserves attention.",
            f"My experience with {topic} has been mixed but generally positive.",
            f"There are significant challenges related to {topic}.",
            f"I'm optimistic about developments in {topic}.",
            f"More research and discussion about {topic} would be helpful.",
            f"{topic.capitalize()} impacts my daily life in various ways.",
            f"I have concerns about certain aspects of {topic}.",
            f"Collaboration is key to addressing {topic} effectively.",
            f"I'm interested in learning more about {topic}.",
            f"The future of {topic} depends on how we approach it today."
        ]
    
    # Generate responses with variation
    for i in range(count):
        base_template = random.choice(templates)
        
        # Add variation to make responses more diverse
        variations = [
            f"I think {base_template.lower()}",
            f"In my experience, {base_template.lower()}",
            f"From what I've observed, {base_template.lower()}",
            f"I believe {base_template.lower()}",
            f"Personally, {base_template.lower()}",
            f"In my opinion, {base_template.lower()}",
            f"I've found that {base_template.lower()}",
            f"Based on my experience, {base_template.lower()}",
            f"I would say that {base_template.lower()}",
            f"It seems to me that {base_template.lower()}"
        ]
        
        response_text = random.choice(variations)
        
        # Add some additional context occasionally
        if random.random() < 0.3:
            additional_contexts = [
                " This has been my experience over the past year.",
                " I've noticed this trend in my industry.",
                " This is something I've been thinking about lately.",
                " I've discussed this with colleagues and friends.",
                " This relates to other challenges I'm facing.",
                " I'm curious about others' perspectives on this.",
                " This is a topic that comes up frequently.",
                " I've been researching this topic recently."
            ]
            response_text += random.choice(additional_contexts)
        
        # Create SurveyResponse object (always create one for each iteration)
        response = SurveyResponse(
            id=i+1,  # Integer ID
            question=question,  # Required question field
            response_text=response_text,  # Correct field name
            batch_id=1,  # Will be updated by the UI
            processed_at=None  # Will be updated by the UI
        )
        
        responses.append(response)
    
    return responses
