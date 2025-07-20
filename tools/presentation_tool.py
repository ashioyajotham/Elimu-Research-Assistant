from typing import Dict, Any, List, Optional
from .tool_registry import BaseTool
from utils.logger import get_logger
import re

logger = get_logger(__name__)

class PresentationTool(BaseTool):
    """Tool for organizing and presenting educational information without writing code."""
    
    def __init__(self):
        """Initialize the presentation tool."""
        super().__init__(
            name="present",
            description="Organizes and formats educational information into lesson plans, handouts, summaries, and other classroom-ready materials"
        )
    
    def execute(self, parameters: Dict[str, Any], memory: Any) -> str:
        """
        Execute the presentation tool with the given parameters for educational content.
        
        Args:
            parameters (dict): Parameters for the tool
                - data (dict or list, optional): Data to present
                - format_type (str): Type of presentation ('lesson_plan', 'handout', 'case_study', 'assessment', 'table', 'list', 'summary', 'comparison')
                - title (str, optional): Title for the presentation
                - prompt (str): Description of what to present and how
                - task (str): Original educational task description
            memory (Memory): Agent's memory
            
        Returns:
            str: Formatted educational presentation of the information
        """
        format_type = parameters.get("format_type", "summary")
        title = parameters.get("title", "Educational Content")
        prompt = parameters.get("prompt", "")
        task_description = parameters.get("task", "")
        data = parameters.get("data", {})
        
        # Process the prompt to replace placeholders with actual entities
        if prompt:
            prompt = self._replace_placeholders(prompt, memory)
        
        # Detect educational content type from task description
        if task_description:
            educational_type = self._detect_educational_type(task_description)
            if educational_type and format_type == "summary":  # Only override if default
                format_type = educational_type
        
        # Check if we have entities to present
        if hasattr(memory, 'extracted_entities') and memory.extracted_entities:
            if not data:  # Only use entities if no other data provided
                data = {"entities": memory.extracted_entities}
            else:
                # Add entities to existing data
                data["entities"] = memory.extracted_entities
        
        # Check if we have search results but no data
        if not data and hasattr(memory, 'search_results') and memory.search_results:
            logger.info("No data provided, using search results from memory")
            data = {"search_results": memory.search_results}
        
        # Check if we have any previous results
        if not data:
            past_results = []
            for key, value in memory.task_results.items():
                if isinstance(value, dict):
                    past_results.append(value)
            
            if past_results:
                logger.info("Using past results as data source")
                data = {"past_results": past_results}
        
        # If we have no data and no reference, generate appropriate message
        if not data:
            logger.warning("No data available for presentation")
            if prompt or task_description:
                content = prompt or task_description
                return f"# {title}\n\n{content}\n\n*Note: I wasn't able to gather sufficient information to provide detailed educational content. Consider refining your search terms or specifying Kenyan sources for better local context.*"
        
        # Educational format routing
        if format_type == "lesson_plan":
            return self._format_as_lesson_plan(title, task_description, data)
        elif format_type == "handout":
            return self._format_as_student_handout(title, task_description, data)
        elif format_type == "case_study":
            return self._format_as_case_study(title, task_description, data)
        elif format_type == "assessment":
            return self._format_as_assessment(title, task_description, data)
        elif format_type == "comparison":
            return self._format_as_comparison_table(title, task_description, data)
        # Traditional formats
        elif format_type == "table":
            return self._format_as_table(title, prompt, data)
        elif format_type == "list":
            return self._format_as_list(title, prompt, data)
        elif format_type == "summary":
            return self._format_as_educational_summary(title, task_description, data)
        else:
            return self._format_as_educational_summary(title, task_description, data)
    
    def _detect_educational_type(self, task_description: str) -> str:
        """Detect the type of educational content from task description."""
        task_lower = task_description.lower()
        
        if any(word in task_lower for word in ["lesson plan", "teaching plan", "class plan"]):
            return "lesson_plan"
        elif any(word in task_lower for word in ["handout", "worksheet", "student material"]):
            return "handout"
        elif any(word in task_lower for word in ["case study", "example", "scenario"]):
            return "case_study"
        elif any(word in task_lower for word in ["quiz", "test", "assessment", "questions"]):
            return "assessment"
        elif any(word in task_lower for word in ["compare", "contrast", "versus", "difference"]):
            return "comparison"
        else:
            return "summary"

    def _replace_placeholders(self, text: str, memory: Any) -> str:
        """
        Replace entity placeholders in text with actual entity values from memory.
        
        Args:
            text (str): Text containing placeholders
            memory (Memory): Agent's memory containing extracted entities
            
        Returns:
            str: Text with placeholders replaced with actual values
        """
        if not hasattr(memory, 'extracted_entities') or not memory.extracted_entities:
            return text
        
        # Define patterns for common placeholder formats
        placeholder_patterns = [
            # [Entity's Name], [ENTITY NAME], [EntityName]
            r'\[([\w\s\']+(?:\'s)?[\s]*(?:Name|Role|Title|Position|Organization|Company|Location|Date)?)\]',
            # {Entity's Name}, {ENTITY NAME}, {EntityName}
            r'\{([\w\s\']+(?:\'s)?[\s]*(?:Name|Role|Title|Position|Organization|Company|Location|Date)?)\}',
            # <Entity's Name>, <ENTITY NAME>, <EntityName>
            r'\<([\w\s\']+(?:\'s)?[\s]*(?:Name|Role|Title|Position|Organization|Company|Location|Date)?)\>',
        ]
        
        replaced_text = text
        
        # Look for placeholders using the defined patterns
        for pattern in placeholder_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                original_placeholder = match.group(0)  # The full placeholder, e.g., [CEO's Name]
                placeholder_text = match.group(1).strip()  # The text inside, e.g., "CEO's Name"
                
                # Determine entity type from placeholder
                entity_type = self._infer_entity_type(placeholder_text)
                
                # Try to find a matching entity
                entity_value = self._find_matching_entity(placeholder_text, entity_type, memory)
                
                if entity_value:
                    logger.info(f"Replacing placeholder '{original_placeholder}' with '{entity_value}'")
                    replaced_text = replaced_text.replace(original_placeholder, entity_value)
        
        return replaced_text

    def _infer_entity_type(self, placeholder_text: str) -> str:
        """
        Infer the entity type from the placeholder text.
        
        Args:
            placeholder_text (str): Text inside the placeholder
            
        Returns:
            str: Inferred entity type
        """
        placeholder_lower = placeholder_text.lower()
        
        # Map common placeholder terms to entity types
        type_mapping = {
            'person': ['person', 'name', 'who', 'individual', 'people', 'founder'],
            'organization': ['organization', 'company', 'org', 'corporation', 'business', 'team'],
            'role': ['ceo', 'coo', 'cfo', 'role', 'title', 'position', 'job', 'director', 'manager', 'founder'],
            'location': ['location', 'place', 'city', 'country', 'region', 'address', 'where'],
            'date': ['date', 'time', 'when', 'year', 'month', 'day']
        }
        
        # Check for matches in the type mapping
        for entity_type, keywords in type_mapping.items():
            if any(keyword in placeholder_lower for keyword in keywords):
                return entity_type
        
        # Default to searching all types if no specific type is inferred
        return None

    def _find_matching_entity(self, placeholder_text: str, entity_type: Optional[str], memory: Any) -> Optional[str]:
        """
        Find an entity value that best matches the placeholder text.
        
        Args:
            placeholder_text (str): Text from the placeholder
            entity_type (str): Inferred entity type (or None if not inferred)
            memory (Memory): Agent's memory
            
        Returns:
            str or None: Matching entity value or None if no match
        """
        if not hasattr(memory, 'extracted_entities') or not memory.extracted_entities:
            return None
            
        # Extract keywords from placeholder for matching
        keywords = self._extract_keywords(placeholder_text)
        
        # If we have a specific entity type, search only there
        if entity_type and entity_type in memory.extracted_entities:
            entities = memory.extracted_entities[entity_type]
            
            # Special handling for role entities (which might have compound formats)
            if entity_type == "role" and "ceo" in placeholder_text.lower():
                for role in entities:
                    if "ceo" in role.lower():
                        # For role format "CEO: Person @ Organization", extract the person
                        parts = role.split("@")
                        if len(parts) > 1:
                            # Get person name from "Role: Person @"
                            role_parts = parts[0].split(":")
                            if len(role_parts) > 1:
                                return role_parts[1].strip()
                        return role
            
            # General search for matching entities
            for entity in entities:
                # Check for keyword matches
                if any(keyword in entity.lower() for keyword in keywords):
                    return entity
            
            # If no keyword match, return the first entity as a fallback
            if entities:
                return entities[0]
        else:
            # If no specific type was inferred or found, search all entity types
            best_match = None
            
            # Priority order for entity types
            type_priority = ["person", "organization", "role", "location", "date"]
            
            # Search through entity types in priority order
            for entity_type in type_priority:
                if entity_type not in memory.extracted_entities:
                    continue
                    
                for entity in memory.extracted_entities[entity_type]:
                    # Check for keyword matches
                    if any(keyword in entity.lower() for keyword in keywords):
                        return entity
                    
                    # Keep track of the first entity of each type as a fallback
                    if not best_match and memory.extracted_entities[entity_type]:
                        best_match = memory.extracted_entities[entity_type][0]
            
            # Return the best match found (if any)
            return best_match
            
        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for matching entities.
        
        Args:
            text (str): Text to extract keywords from
            
        Returns:
            list: List of keywords
        """
        # Remove common filler words
        stop_words = {'the', 'a', 'an', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 
                      'about', 'to', 's', 'name', 'is', 'are', 'their', 'his', 'her'}
        
        # Split by non-alphanumeric characters and lowercase
        words = re.findall(r'\w+', text.lower())
        
        # Filter out stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _format_as_table(self, title: str, prompt: str, data: Any) -> str:
        """Format information as a markdown table."""
        output = [f"# {title}", "", prompt, ""]
        
        # Generate a table based on the data structure
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # List of dictionaries - create table with headers
            headers = list(data[0].keys())
            output.append("| " + " | ".join(headers) + " |")
            output.append("| " + " | ".join(["---" for _ in headers]) + " |")
            
            for item in data:
                row = [str(item.get(header, "")) for header in headers]
                output.append("| " + " | ".join(row) + " |")
        else:
            # For other data structures, create a simple key-value table
            output.append("| Key | Value |")
            output.append("| --- | --- |")
            
            if isinstance(data, dict):
                for key, value in data.items():
                    output.append(f"| {key} | {value} |")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    output.append(f"| Item {i+1} | {item} |")
            else:
                # If data isn't structured, use the prompt to generate a meaningful table
                output.append("| Note | No structured data provided |")
                output.append(f"| Prompt | {prompt} |")
        
        return "\n".join(output)
    
    def _format_as_list(self, title: str, prompt: str, data: Any) -> str:
        """Format information as a markdown list."""
        output = [f"# {title}", "", prompt, ""]
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    output.append(f"- **{next(iter(item))}**: {item[next(iter(item))]}")
                    for key, value in list(item.items())[1:]:
                        output.append(f"  - {key}: {value}")
                else:
                    output.append(f"- {item}")
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    output.append(f"- **{key}**:")
                    for subkey, subvalue in value.items():
                        output.append(f"  - {subkey}: {subvalue}")
                elif isinstance(value, list):
                    output.append(f"- **{key}**:")
                    for item in value:
                        output.append(f"  - {item}")
                else:
                    output.append(f"- **{key}**: {value}")
        else:
            # If data isn't structured, use the prompt to generate a list
            output.append("- This is a presentation of the requested information:")
            output.append(f"  - Based on: {prompt}")
            output.append("- No structured data was provided")
        
        return "\n".join(output)
    
    def _format_as_summary(self, title: str, prompt: str, data: Any) -> str:
        """Format information as a markdown summary."""
        output = [f"# {title}", "", prompt, "", "## Summary", ""]
        
        # For summary format, we mostly rely on the prompt
        output.append(f"This is a summary based on the request: '{prompt}'")
        output.append("")
        
        if isinstance(data, dict) and len(data) > 0:
            output.append("### Key Points")
            for key, value in data.items():
                output.append(f"- **{key}**: {value}")
        elif isinstance(data, list) and len(data) > 0:
            output.append("### Key Points")
            for item in data:
                if isinstance(item, dict):
                    for key, value in item.items():
                        output.append(f"- **{key}**: {value}")
                else:
                    output.append(f"- {item}")
        else:
            output.append("No structured data was provided for this summary.")
        
        return "\n".join(output)
    
    def _format_as_comparison(self, title: str, prompt: str, data: Any) -> str:
        """Format information as a comparison."""
        output = [f"# {title}", "", prompt, "", "## Comparison", ""]
        
        if isinstance(data, dict) and len(data) >= 2:
            # Compare dictionary values
            items = list(data.items())
            output.append(f"### Comparing {items[0][0]} vs {items[1][0]}")
            output.append("")
            output.append("| Aspect | " + " | ".join([key for key, _ in items]) + " |")
            output.append("| --- | " + " | ".join(["---" for _ in items]) + " |")
            
            # Find all unique keys in the nested dictionaries
            all_aspects = set()
            for _, value in items:
                if isinstance(value, dict):
                    all_aspects.update(value.keys())
            
            # Create comparison rows
            for aspect in all_aspects:
                row = [aspect]
                for _, value in items:
                    if isinstance(value, dict):
                        row.append(str(value.get(aspect, "N/A")))
                    else:
                        row.append("N/A")
                output.append("| " + " | ".join(row) + " |")
        elif isinstance(data, list) and len(data) >= 2:
            # Compare list items
            output.append("| Aspect | " + " | ".join([f"Item {i+1}" for i in range(len(data))]) + " |")
            output.append("| --- | " + " | ".join(["---" for _ in data]) + " |")
            
            # If list contains dictionaries, compare their values
            if all(isinstance(item, dict) for item in data):
                all_keys = set()
                for item in data:
                    all_keys.update(item.keys())
                
                for key in all_keys:
                    row = [key]
                    for item in data:
                        row.append(str(item.get(key, "N/A")))
                    output.append("| " + " | ".join(row) + " |")
            else:
                # Simple list comparison
                output.append("| Value | " + " | ".join([str(item) for item in data]) + " |")
        else:
            output.append("Insufficient data provided for meaningful comparison. Need multiple items to compare.")
        
        return "\n".join(output)
    
    def _format_as_generic(self, title: str, prompt: str, data: Any) -> str:
        """Format information in a generic way when no specific format is specified."""
        output = [f"# {title}", "", prompt, "", "## Information", ""]
        
        if isinstance(data, dict):
            for key, value in data.items():
                output.append(f"### {key}")
                output.append("")
                output.append(f"{value}")
                output.append("")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                output.append(f"### Item {i+1}")
                output.append("")
                output.append(f"{item}")
                output.append("")
        else:
            output.append(f"Based on the request: '{prompt}'")
            output.append("")
            output.append("No structured data was provided. Here's a generic presentation of the information.")
        
        return "\n".join(output)
    
    def _format_entities(self, title: str, prompt: str, entities: Dict[str, List[str]]) -> str:
        """
        Format extracted entities in a readable way with relationships highlighted.
        
        Args:
            title (str): Title for the presentation
            prompt (str): Description of what to present
            entities (dict): Dictionary of entity types and values
            
        Returns:
            str: Formatted entity presentation
        """
        output = [f"# {title}", "", prompt, "", "## Extracted Information", ""]
        
        # Find key organizations (if any)
        key_orgs = []
        if "organization" in entities and entities["organization"]:
            key_orgs = entities["organization"]
        
        # Format roles first with organization context
        if "role" in entities and entities["role"]:
            output.append("### Key Roles and Positions")
            
            # Extract role-person-organization relationships
            role_info = []
            for role_entry in entities["role"]:
                # Handle different role formats
                if ":" in role_entry and "@" in role_entry:
                    # Format: "Role: Person @ Organization"
                    parts = role_entry.split(":")
                    if len(parts) >= 2:
                        role = parts[0].strip()
                        person_org = parts[1].strip().split("@")
                        if len(person_org) >= 2:
                            person = person_org[0].strip()
                            org = person_org[1].strip()
                            role_info.append({"role": role, "person": person, "organization": org})
                        else:
                            role_info.append({"role": role, "description": parts[1].strip()})
                else:
                    # Simple role format
                    role_info.append({"role": role_entry})
            
            # Display role information
            for info in role_info:
                if "person" in info and "organization" in info:
                    output.append(f"- **{info['role']}**: {info['person']} at {info['organization']}")
                elif "description" in info:
                    output.append(f"- **{info['role']}**: {info['description']}")
                else:
                    output.append(f"- {info['role']}")
            
            output.append("")
        
        # Display organizations with context
        if key_orgs:
            output.append("### Organizations")
            for org in key_orgs:
                # Look for roles associated with this organization
                org_roles = []
                if "role" in entities:
                    for role in entities["role"]:
                        if org.lower() in role.lower():
                            org_roles.append(role)
                
                output.append(f"- **{org}**")
                if org_roles:
                    output.append("  - Associated roles:")
                    for role in org_roles:
                        output.append(f"    - {role}")
            output.append("")
        
        # Format persons with context
        if "person" in entities and entities["person"]:
            output.append("### People")
            for person in entities["person"]:
                # Look for roles associated with this person
                person_roles = []
                if "role" in entities:
                    for role in entities["role"]:
                        if person.lower() in role.lower():
                            person_roles.append(role)
                
                output.append(f"- **{person}**")
                if person_roles:
                    output.append("  - Roles:")
                    for role in person_roles:
                        output.append(f"    - {role}")
            output.append("")
        
        # Format other entity types
        for entity_type, values in entities.items():
            if entity_type not in ["role", "organization", "person"] and values:
                output.append(f"### {entity_type.title()}")
                for value in values:
                    output.append(f"- {value}")
                output.append("")
        
        # Provide a structured summary if we have organization and role information
        if "organization" in entities and "role" in entities:
            org_role_map = {}
            
            # Map organizations to roles
            for role_entry in entities.get("role", []):
                for org in entities.get("organization", []):
                    if org.lower() in role_entry.lower():
                        if org not in org_role_map:
                            org_role_map[org] = []
                        org_role_map[org].append(role_entry)
            
            if org_role_map:
                output.append("## Summary of Findings")
                for org, roles in org_role_map.items():
                    output.append(f"### {org}")
                    for role in roles:
                        output.append(f"- {role}")
                    output.append("")
        
        return "\n".join(output)
    
    def _format_as_lesson_plan(self, title: str, task_description: str, data: Dict[str, Any]) -> str:
        """Format content as a lesson plan for teachers."""
        output = [f"# Lesson Plan: {title}\n"]
        
        # Extract subject and level from task
        subject = self._extract_subject(task_description)
        level = self._extract_education_level(task_description)
        
        output.extend([
            f"**Subject:** {subject}",
            f"**Level:** {level}",
            f"**Duration:** 40 minutes (adjustable)",
            "",
            "## Learning Objectives",
            "By the end of this lesson, students will be able to:",
            "- Understand key concepts related to the topic",
            "- Apply knowledge to real-world Kenyan examples",
            "- Analyze local case studies and examples",
            "",
            "## Materials Needed",
            "- Whiteboard/Blackboard",
            "- Handouts (see student materials below)",
            "- Projector (if available)",
            "",
            "## Lesson Structure",
            "",
            "### Introduction (10 minutes)",
            "- Review previous lesson connections",
            "- Introduce today's topic with a local example",
            "",
            "### Main Content (25 minutes)"
        ])
        
        # Add content from search results
        if "search_results" in data:
            output.append("**Key Points to Cover:**")
            for i, result in enumerate(data["search_results"][:5], 1):
                title_clean = result.get("title", f"Point {i}")
                snippet = result.get("snippet", "")
                output.append(f"{i}. {title_clean}")
                if snippet:
                    output.append(f"   - {snippet[:100]}...")
            output.append("")
        
        output.extend([
            "### Activity (15 minutes)",
            "- Group discussion on local examples",
            "- Student presentations (if time allows)",
            "",
            "### Conclusion (5 minutes)",
            "- Summarize key points",
            "- Preview next lesson",
            "",
            "## Assessment Methods",
            "- Formative: Questions during lesson",
            "- Summative: Quiz in next lesson",
            "",
            "## Homework/Extension",
            "- Research one local example related to today's topic",
            "- Prepare to share findings in next class",
            "",
            "## Teacher Notes",
            "- Emphasize Kenyan context throughout",
            "- Adapt examples to student backgrounds",
            "- Use local languages for key terms when helpful"
        ])
        
        return "\n".join(output)
    
    def _format_as_student_handout(self, title: str, task_description: str, data: Dict[str, Any]) -> str:
        """Format content as a student handout."""
        output = [f"# Student Handout: {title}\n"]
        
        subject = self._extract_subject(task_description)
        level = self._extract_education_level(task_description)
        
        output.extend([
            f"**Subject:** {subject} | **Level:** {level}",
            f"**Name:** _________________ **Date:** _________",
            "",
            "## Key Information",
            ""
        ])
        
        # Add content from search results in student-friendly format
        if "search_results" in data:
            for i, result in enumerate(data["search_results"][:6], 1):
                title_clean = result.get("title", f"Topic {i}")
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                
                output.append(f"### {i}. {title_clean}")
                if snippet:
                    output.append(f"{snippet}")
                output.append(f"*Source: {link}*")
                output.append("")
        
        output.extend([
            "## Activity Questions",
            "1. Which example from the content above relates most to your daily life? Explain.",
            "2. How does this topic connect to what you observe in your community?",
            "3. What questions do you still have about this topic?",
            "",
            "## Key Terms",
            "Write definitions for these important terms:",
            "- Term 1: _________________________________",
            "- Term 2: _________________________________",
            "- Term 3: _________________________________",
            "",
            "## Notes Section",
            "_Use this space for additional notes during class discussion:_",
            "",
            "_" * 50,
            "",
            "_" * 50,
            "",
            "_" * 50
        ])
        
        return "\n".join(output)
    
    def _format_as_case_study(self, title: str, task_description: str, data: Dict[str, Any]) -> str:
        """Format content as a case study."""
        output = [f"# Case Study: {title}\n"]
        
        output.extend([
            "## Background",
            "This case study examines real-world applications and examples relevant to Kenyan students.",
            "",
            "## The Situation"
        ])
        
        # Use search results to build case study narrative
        if "search_results" in data:
            main_content = []
            for result in data["search_results"][:3]:
                snippet = result.get("snippet", "")
                if snippet:
                    main_content.append(snippet)
            
            if main_content:
                output.append(" ".join(main_content))
                output.append("")
        
        output.extend([
            "## Key Players",
            "- Stakeholder 1: [To be filled based on content]",
            "- Stakeholder 2: [To be filled based on content]",
            "- Impact on Community: [To be discussed]",
            "",
            "## Analysis Questions",
            "1. What are the main challenges presented in this case?",
            "2. How do cultural and economic factors influence the situation?",
            "3. What solutions would you propose?",
            "4. How might this case study apply to other regions in Kenya?",
            "",
            "## Discussion Points",
            "- Economic implications",
            "- Social impact",
            "- Environmental considerations",
            "- Policy recommendations",
            "",
            "## Further Research",
            "Students should investigate:"
        ])
        
        # Add research suggestions based on search results
        if "search_results" in data:
            for result in data["search_results"][3:6]:
                title_clean = result.get("title", "")
                if title_clean:
                    output.append(f"- {title_clean}")
        
        return "\n".join(output)
    
    def _format_as_assessment(self, title: str, task_description: str, data: Dict[str, Any]) -> str:
        """Format content as assessment questions."""
        output = [f"# Assessment: {title}\n"]
        
        subject = self._extract_subject(task_description)
        level = self._extract_education_level(task_description)
        
        output.extend([
            f"**Subject:** {subject} | **Level:** {level}",
            f"**Time Allowed:** 30 minutes",
            f"**Instructions:** Answer all questions. Use examples from Kenya where possible.",
            "",
            "## Section A: Multiple Choice (10 marks)",
            ""
        ])
        
        # Generate multiple choice questions based on content
        for i in range(1, 6):
            output.extend([
                f"{i}. [Question based on researched content]",
                "   a) Option A",
                "   b) Option B", 
                "   c) Option C",
                "   d) Option D",
                ""
            ])
        
        output.extend([
            "## Section B: Short Answer (15 marks)",
            "",
            "6. Define [key term] and give a Kenyan example. (3 marks)",
            "",
            "7. Explain the relationship between [concept A] and [concept B] using local examples. (4 marks)",
            "",
            "8. List three ways this topic affects daily life in Kenya. (3 marks)",
            "",
            "9. Compare and contrast [two related concepts]. (5 marks)",
            "",
            "## Section C: Essay Question (15 marks)",
            "",
            "10. Choose ONE of the following:",
            "    a) Discuss the impact of [topic] on Kenyan society, using specific examples.",
            "    b) Analyze how [topic] has evolved in Kenya over the past decade.",
            "    c) Evaluate the effectiveness of [relevant policy/program] in addressing [issue].",
            "",
            "**Essay Guidelines:**",
            "- Minimum 200 words",
            "- Use specific Kenyan examples",
            "- Include introduction, body, and conclusion",
            "- Reference credible sources where possible"
        ])
        
        return "\n".join(output)
    
    def _format_as_comparison_table(self, title: str, task_description: str, data: Dict[str, Any]) -> str:
        """Format content as a comparison table."""
        output = [f"# Comparison: {title}\n"]
        
        output.extend([
            "| Aspect | Option A | Option B | Kenyan Context |",
            "|--------|----------|----------|----------------|"
        ])
        
        # Create comparison rows based on search results
        if "search_results" in data:
            aspects = ["Definition", "Key Features", "Advantages", "Disadvantages", "Local Examples"]
            for aspect in aspects:
                output.append(f"| {aspect} | [To be filled] | [To be filled] | [Local example] |")
        
        output.extend([
            "",
            "## Summary",
            "Based on the comparison above:",
            "- Key similarities: [To be filled]",
            "- Major differences: [To be filled]", 
            "- Relevance to Kenya: [To be filled]",
            "",
            "## Discussion Questions",
            "1. Which option would be more suitable for the Kenyan context? Why?",
            "2. How do local factors influence the effectiveness of each option?",
            "3. What adaptations would be needed for successful implementation in Kenya?"
        ])
        
        return "\n".join(output)
    
    def _format_as_educational_summary(self, title: str, task_description: str, data: Dict[str, Any]) -> str:
        """Format content as an educational summary with Kenyan focus."""
        output = [f"# {title}\n"]
        
        # Add educational context
        subject = self._extract_subject(task_description)
        level = self._extract_education_level(task_description)
        
        if subject != "General" or level != "Secondary":
            output.extend([
                f"**Subject Area:** {subject}",
                f"**Education Level:** {level}",
                f"**Relevance:** Kenyan Educational Context",
                ""
            ])
        
        output.append("## Overview")
        
        # Create summary from search results with educational focus
        if "search_results" in data:
            overview_content = []
            for result in data["search_results"][:2]:
                snippet = result.get("snippet", "")
                if snippet:
                    overview_content.append(snippet)
            
            if overview_content:
                output.append(" ".join(overview_content))
            else:
                output.append("This summary provides key information relevant to Kenyan educational contexts.")
            output.append("")
        
        # Add key points section
        output.append("## Key Points")
        if "search_results" in data:
            for i, result in enumerate(data["search_results"][:5], 1):
                title_clean = result.get("title", f"Point {i}")
                snippet = result.get("snippet", "")
                output.append(f"### {i}. {title_clean}")
                if snippet:
                    output.append(snippet)
                output.append("")
        
        # Add educational applications
        output.extend([
            "## Educational Applications",
            "- **For Teachers:** Use these examples to create locally relevant lessons",
            "- **For Students:** Connect global concepts to Kenyan experiences", 
            "- **For Assessment:** Develop questions using local contexts",
            "",
            "## Kenyan Context",
            "This content relates to Kenya through:",
            "- Local examples and case studies",
            "- Cultural and economic relevance",
            "- Alignment with national curriculum goals",
            "",
            "## Further Learning",
            "To deepen understanding, explore:"
        ])
        
        # Add learning suggestions
        if "search_results" in data:
            for result in data["search_results"][5:8]:
                title_clean = result.get("title", "")
                if title_clean:
                    output.append(f"- {title_clean}")
        
        output.extend([
            "",
            "## Sources",
            "Information compiled from verified educational sources with priority given to Kenyan institutions and publishers."
        ])
        
        return "\n".join(output)
    
    def _extract_subject(self, task_description: str) -> str:
        """Extract subject area from task description."""
        task_lower = task_description.lower()
        subjects = {
            "business studies": ["business", "commerce", "entrepreneurship", "economics"],
            "geography": ["geography", "climate", "physical", "human geography"],
            "history": ["history", "historical", "colonial", "independence"],
            "mathematics": ["math", "mathematics", "algebra", "geometry", "statistics"],
            "science": ["science", "biology", "chemistry", "physics"],
            "literature": ["literature", "english", "writing", "poetry"],
            "social studies": ["social", "society", "community", "government"]
        }
        
        for subject, keywords in subjects.items():
            if any(keyword in task_lower for keyword in keywords):
                return subject.title()
        return "General"
    
    def _extract_education_level(self, task_description: str) -> str:
        """Extract education level from task description."""
        task_lower = task_description.lower()
        
        if "form 4" in task_lower:
            return "Form 4 (Secondary)"
        elif "form 3" in task_lower:
            return "Form 3 (Secondary)"
        elif "form 2" in task_lower:
            return "Form 2 (Secondary)"
        elif "form 1" in task_lower:
            return "Form 1 (Secondary)"
        elif any(word in task_lower for word in ["primary", "standard"]):
            return "Primary"
        elif "tertiary" in task_lower or "university" in task_lower:
            return "Tertiary"
        else:
            return "Secondary"
