from utils.logger import get_logger
from config.config import get_config
import google.generativeai as genai
import json
import re

logger = get_logger(__name__)

class Comprehension:
    """Text understanding and reasoning capabilities."""
    
    def __init__(self):
        """Initialize the comprehension module."""
        config = get_config()
        genai.configure(api_key=config.get("gemini_api_key"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name
    
    def analyze_task(self, task_description):
        """
        Analyze an educational task to determine its type, required information, etc.
        Specifically optimized for Kenyan educational content creation.
        
        Args:
            task_description (str): Description of the educational task to analyze
            
        Returns:
            dict: Analysis of the task with educational focus
        """
        logger.info(f"Analyzing educational task: {task_description}")
        
        # Add specific pattern recognition for educational tasks
        task_lower = task_description.lower()
        
        # Educational content type detection
        educational_patterns = {
            "lesson_plan": ["lesson plan", "teaching plan", "class plan", "curriculum"],
            "student_handout": ["handout", "worksheet", "student material", "class notes"],
            "assessment": ["quiz", "test", "exam", "assessment", "evaluation", "questions"],
            "case_study": ["case study", "example", "real-world", "scenario"],
            "comparison": ["compare", "contrast", "versus", "difference", "similarity"],
            "research_brief": ["brief", "summary", "overview", "background", "context"]
        }
        
        # Kenyan context indicators
        kenyan_indicators = ["kenya", "kenyan", "nairobi", "mombasa", "kisumu", "nakuru", 
                           "east africa", "m-pesa", "safaricom", "kicd", "8-4-4", "cbc",
                           "form 1", "form 2", "form 3", "form 4", "standard", "grade"]
        
        # Subject area detection
        subject_areas = {
            "business_studies": ["business", "commerce", "entrepreneurship", "economics", "trade"],
            "geography": ["geography", "climate", "physical", "human geography", "mapping"],
            "history": ["history", "historical", "colonial", "independence", "culture"],
            "mathematics": ["math", "mathematics", "algebra", "geometry", "statistics", "calculations"],
            "science": ["science", "biology", "chemistry", "physics", "research", "experiment"],
            "literature": ["literature", "english", "writing", "poetry", "novel", "author"],
            "social_studies": ["social", "society", "community", "government", "civics"]
        }
        
        # Detect content type
        content_type = "general_educational"
        for type_key, keywords in educational_patterns.items():
            if any(keyword in task_lower for keyword in keywords):
                content_type = type_key
                break
        
        # Detect subject area
        subject_area = "interdisciplinary"
        for subject, keywords in subject_areas.items():
            if any(keyword in task_lower for keyword in keywords):
                subject_area = subject
                break
        
        # Check for Kenyan context
        has_kenyan_context = any(indicator in task_lower for indicator in kenyan_indicators)
        
        # Check for list/compilation tasks specifically for statements/quotes
        if ("compile" in task_lower or "list" in task_lower) and \
           ("statement" in task_lower or "quote" in task_lower or "said" in task_lower):
            return {
                "task_type": "information_gathering",
                "answer_type": "list_compilation",
                "information_targets": ["statements", "quotes", "remarks"],
                "synthesis_strategy": "collect_and_organize",
                "output_structure": "list",
                "content_type": content_type,
                "subject_area": subject_area,
                "kenyan_focus": has_kenyan_context
            }
        
        prompt = f"""
        Analyze the following educational task and break it down into components with focus on Kenyan educational context:
        
        TASK: {task_description}
        
        This task is for Kenyan educators creating localized educational content. Consider:
        - Educational level (primary, secondary, tertiary)
        - Subject area and curriculum alignment
        - Need for Kenyan examples and local context
        - Format suitable for classroom use
        - Digital literacy and source verification needs
        
        Pay special attention to:
        - Multi-line tasks with bullet points or numbered criteria
        - Tasks that require gathering information based on multiple conditions
        - Tasks with nested or hierarchical requirements
        - Educational standards and learning objectives
        - Cultural sensitivity and local relevance
        
        Your analysis should include:
        - Whether each criterion is a separate requirement or part of a single search
        - How to verify that results meet all criteria
        - Whether filtering by multiple conditions requires code
        - Educational impact and classroom applicability
        
        Please provide a structured analysis in JSON format with the following fields:
        1. "task_type": The general category of the task (e.g., "educational_content_creation", "lesson_planning", "assessment_design", "research_synthesis")
        2. "content_type": Type of educational content (e.g., "lesson_plan", "student_handout", "case_study", "assessment")
        3. "subject_area": Academic subject (e.g., "business_studies", "geography", "history", "mathematics", "science")
        4. "education_level": Target level (e.g., "primary", "secondary_form_1", "secondary_form_4", "tertiary")
        5. "kenyan_focus": Boolean indicating if Kenyan context is needed or specified
        6. "requires_coding": Boolean (true/false) indicating if this task actually requires writing or generating code
        7. "key_entities": List of important entities, concepts, or topics mentioned in the task
        8. "search_queries": Suggested search queries prioritizing Kenyan sources when relevant
        9. "required_information": Types of information that need to be gathered
        10. "presentation_format": How the information should be presented for classroom use
        11. "kenyan_sources_priority": List of recommended Kenyan sources to prioritize (e.g., "KICD", "Kenyan universities", "government publications")
        12. "expected_output": What the final educational content should look like
        
        For the "requires_coding" field, only mark as true if the task explicitly asks for:
        - Writing a program, script, or function
        - Implementing an algorithm 
        - Creating code in a specific language
        
        Do NOT mark as true if the task is just about:
        - Finding information
        - Creating educational content
        - Showing data in a table/chart
        - Summarizing information for students
        
        Return ONLY the JSON without additional explanation or formatting.
        """
        
        try:
            # Updated API call format
            response = self.model.generate_content(prompt)
            analysis = self._extract_json(response.text)
            
            # Ensure educational defaults are set
            if "content_type" not in analysis:
                analysis["content_type"] = content_type
            if "subject_area" not in analysis:
                analysis["subject_area"] = subject_area
            if "kenyan_focus" not in analysis:
                analysis["kenyan_focus"] = has_kenyan_context
            if "kenyan_sources_priority" not in analysis:
                analysis["kenyan_sources_priority"] = ["KICD", "Kenyan universities", "Daily Nation", "The Standard", "government publications"]
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing educational task: {str(e)}")
            # Return a basic educational analysis if LLM fails
            return {
                "task_type": "educational_content_creation",
                "content_type": content_type,
                "subject_area": subject_area,
                "education_level": "secondary",
                "kenyan_focus": has_kenyan_context,
                "key_entities": task_description.split()[:5],
                "search_queries": [f"{task_description} Kenya", f"{task_description} East Africa"],
                "required_information": ["educational examples", "local context", "curriculum alignment"],
                "kenyan_sources_priority": ["KICD", "Kenyan universities", "government publications"],
                "expected_output": "educational_content"
            }
    
    def summarize_content(self, content, max_length=500):
        """
        Summarize content to a specified maximum length.
        
        Args:
            content (str): Content to summarize
            max_length (int): Approximate maximum length of summary
            
        Returns:
            str: Summarized content
        """
        if (len(content) <= max_length):
            return content
        
        prompt = f"""
        Summarize the following content in about {max_length} characters:
        
        {content[:10000]}  # Limit input to avoid token limits
        
        Provide only the summary without additional commentary.
        """
        
        try:
            # Updated API call format
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error summarizing content: {str(e)}")
            # Simple fallback summarization
            return content[:max_length] + "..."
    
    def extract_relevant_information(self, content, query):
        """
        Extract parts of the content most relevant to the query.
        
        Args:
            content (str): Content to analyze
            query (str): Query to extract information for
            
        Returns:
            str: Relevant information
        """
        prompt = f"""
        Extract the parts of the following content that are most relevant to the query:
        
        QUERY: {query}
        
        CONTENT:
        {content[:10000]}  # Limit input to avoid token limits
        
        Provide only the relevant extracted information without additional commentary.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error extracting information: {str(e)}")
            return "Failed to extract relevant information."
    
    def extract_entities(self, text, entity_types=None):
        """
        Extract named entities from text content with advanced formatting.
        
        Args:
            text (str): The text to analyze
            entity_types (list, optional): Types of entities to extract (e.g., 'person', 'organization', 'role')
                If None, extract all common entity types
                
        Returns:
            dict: Dictionary of entity types and their extracted values
        """
        logger.info(f"Extracting entities from text of length {len(text)}")
        
        # Default entity types if none specified
        if entity_types is None:
            entity_types = ['person', 'organization', 'role', 'location', 'date', 'title', 'event']
        
        # Cap text length to avoid token limits
        text_sample = text[:25000] if len(text) > 25000 else text
        
        # Use specialized prompt based on presence of 'role' type
        if 'role' in entity_types:
            prompt = self._create_role_focused_extraction_prompt(entity_types, text_sample)
        else:
            prompt = self._create_standard_extraction_prompt(entity_types, text_sample)
        
        try:
            response = self.model.generate_content(prompt)
            entities = self._extract_json(response.text)
            
            # Post-process the extracted entities
            cleaned_entities = self._clean_entities(entities)
            
            # Process role relationships
            if 'role' in cleaned_entities and 'person' in cleaned_entities and 'organization' in cleaned_entities:
                cleaned_entities = self._enhance_role_relationships(cleaned_entities)
            
            logger.info(f"Extracted entities: {cleaned_entities}")
            return cleaned_entities
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return {entity_type: [] for entity_type in entity_types}

    def _create_role_focused_extraction_prompt(self, entity_types, text):
        """Create a prompt specifically designed to extract roles with relationships."""
        entity_types_str = ', '.join(entity_types)
        
        return f"""
        Carefully analyze and extract the following entity types from the text below:
        {entity_types_str}
        
        For each entity type, provide a list of unique values found in the text.
        Be thorough and precise in your extraction, focusing especially on unique identifiers.
        
        Pay special attention to identifying leadership roles and their relationships to people and organizations.
        
        Special extraction instructions:
        
        1. PERSON: Extract full names when possible. Include titles only if they help identify the person.
        2. ORGANIZATION: Extract complete organization names. Include both full names and well-known abbreviations.
        3. ROLE: For roles and positions, use this exact format: "ROLE: Person @ Organization" 
           For example: "CEO: John Smith @ Acme Corp"
           This is critical for establishing the relationship between roles, people and organizations.
           If a role is mentioned (like CEO, founder, director) always try to determine which person has this role
           and at which organization.
        4. DATE: Extract specific dates mentioned, including year information when available.
        5. LOCATION: Extract specific locations including cities, countries, and venues.
        
        TEXT:
        {text}
        
        Return the results as a JSON object with entity types as keys and arrays of found entities as values.
        Only include entity types that have at least one match. Return ONLY the JSON without additional text.
        
        Example format:
        {{
            "person": ["John Smith", "Jane Doe"],
            "organization": ["Acme Corp", "Future AI Initiative"],
            "role": ["CEO: John Smith @ Acme Corp", "Director: Jane Doe @ Future AI Initiative"],
            "location": ["Geneva, Switzerland", "Washington DC"]
        }}
        """

    def _create_standard_extraction_prompt(self, entity_types, text):
        """Create a standard entity extraction prompt."""
        entity_types_str = ', '.join(entity_types)
        
        return f"""
        Carefully analyze and extract the following entity types from the text below:
        {entity_types_str}
        
        For each entity type, provide a list of unique values found in the text.
        Be thorough and precise in your extraction, focusing especially on unique identifiers.
        
        Special extraction instructions:
        
        1. PERSON: Extract full names when possible. Include titles only if they help identify the person.
        2. ORGANIZATION: Extract complete organization names. Include both full names and well-known abbreviations.
        3. DATE: Extract specific dates mentioned, including year information when available.
        4. LOCATION: Extract specific locations including cities, countries, and venues.
        
        TEXT:
        {text}
        
        Return the results as a JSON object with entity types as keys and arrays of found entities as values.
        Only include entity types that have at least one match. Return ONLY the JSON without additional text.
        """

    def _enhance_role_relationships(self, entities):
        """
        Enhance role relationships by ensuring proper format and connections.
        
        Args:
            entities (dict): Extracted entities
            
        Returns:
            dict: Entities with enhanced role relationships
        """
        # If we don't have the necessary entities, return as is
        if not all(k in entities for k in ['role', 'person', 'organization']):
            return entities
        
        # Make a copy to avoid modifying the original
        enhanced = {k: v.copy() if isinstance(v, list) else v for k, v in entities.items()}
        
        # Process each role entry
        updated_roles = []
        for role in enhanced['role']:
            # Check if the role is already properly formatted
            if ':' in role and '@' in role:
                updated_roles.append(role)
                continue
            
            # Try to extract role type and connect to person and organization
            role_parts = role.split()
            if not role_parts:
                continue
                
            # Get the role type (e.g. CEO, Director)
            role_type = role_parts[0].upper()
            
            # Find person and organization in this role text
            best_person = None
            best_org = None
            
            # Look for person name in the role text
            for person in enhanced['person']:
                if person.lower() in role.lower():
                    best_person = person
                    break
            
            # Look for organization in the role text
            for org in enhanced['organization']:
                if org.lower() in role.lower():
                    best_org = org
                    break
            
            # If we found matches, format properly. Otherwise use first entries
            if not best_person and enhanced['person']:
                best_person = enhanced['person'][0]
                
            if not best_org and enhanced['organization']:
                best_org = enhanced['organization'][0]
                
            # Create formatted role entry if we have both components
            if best_person and best_org:
                formatted_role = f"{role_type}: {best_person} @ {best_org}"
                updated_roles.append(formatted_role)
            else:
                # Keep original if we couldn't enhance
                updated_roles.append(role)
        
        enhanced['role'] = updated_roles
        return enhanced

    def _clean_entities(self, entities):
        """Clean and normalize extracted entities."""
        cleaned = {}
        
        for entity_type, values in entities.items():
            if not values:
                continue
                
            # Remove duplicates (case insensitive)
            unique_values = []
            seen = set()
            
            for value in values:
                value_lower = value.lower()
                if value_lower not in seen:
                    seen.add(value_lower)
                    unique_values.append(value)
            
            # Remove very short entities (likely not useful)
            unique_values = [v for v in unique_values if len(v) > 1]
            
            # For organization names, remove very generic terms
            if entity_type == 'organization':
                generic_orgs = {'company', 'organization', 'corporation', 'agency', 'department', 'office', 'association'}
                unique_values = [org for org in unique_values if org.lower() not in generic_orgs]
            
            # Add clean values if any remain
            if unique_values:
                cleaned[entity_type] = unique_values
        
        return cleaned
    
    def _extract_json(self, text):
        """Extract and parse JSON from text with enhanced error handling."""
        # Try to find JSON within code blocks
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without code blocks - more greedy pattern
            json_match = re.search(r'({[\s\S]*})', text)
            if json_match:
                json_str = json_match.group(1)
            else:
                logger.warning("Could not extract JSON from response, using fallback")
                return self._get_fallback_analysis()
    
        try:
            # First attempt: parse as-is
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {str(e)}. Attempting fixes...")
            
            try:
                # Advanced JSON repair techniques:
                
                # 1. Replace single quotes with double quotes
                json_str = json_str.replace("'", '"')
                
                # 2. Remove any non-JSON content like comments
                clean_json = re.sub(r'(?<!["{\s,:])\s*//.*?(?=\n|$)', '', json_str)
                
                # 3. Fix trailing commas in arrays and objects
                clean_json = re.sub(r',\s*}', '}', clean_json)
                clean_json = re.sub(r',\s*]', ']', clean_json)
                
                # 4. Fix truncated arrays/objects
                clean_json = re.sub(r'"\s*:\s*\[\s*$', '": []', clean_json)
                clean_json = re.sub(r'"\s*:\s*{\s*$', '": {}', clean_json)
                
                # 5. Check for unquoted keys and fix them
                clean_json = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', clean_json)
                
                # 6. Attempt to fix truncated or incomplete JSON
                if not (clean_json.strip().endswith('}') or clean_json.strip().endswith(']')):
                    if clean_json.count('{') > clean_json.count('}'):
                        clean_json += '}'
                    if clean_json.count('[') > clean_json.count(']'):
                        clean_json += ']'
                
                return json.loads(clean_json)
                
            except json.JSONDecodeError as e2:
                # Final attempt - try to recover partial JSON
                try:
                    # For truncated JSON, try to parse what we have and add missing closing braces
                    partial_json = self._recover_partial_json(json_str)
                    if partial_json:
                        return partial_json
                except:
                    pass
                
                logger.error(f"Failed to parse JSON after fixes: {str(e2)}")
                logger.error(f"Problematic JSON: {json_str[:100]}...")
                return self._get_fallback_analysis()
            
    def _get_fallback_analysis(self):
        """Return a fallback analysis object."""
        return {
            "answer_type": "general_research",
            "information_targets": ["general information"],
            "synthesis_strategy": "comprehensive_synthesis",
            "output_structure": "markdown"
        }
        
    def _recover_partial_json(self, json_str):
        """Attempt to recover partial JSON by extracting valid key-value pairs."""
        result = {}
        
        # Extract keys and values that are in valid format
        key_value_pattern = r'"([^"]+)"\s*:\s*(?:"([^"]*)"|\[([^\]]*)\]|(\d+)|true|false|null)'
        matches = re.findall(key_value_pattern, json_str)
        
        for match in matches:
            key = match[0]
            # Determine which value group is populated
            if match[1]:  # String value
                result[key] = match[1]
            elif match[2]:  # Array value
                try:
                    # Try to parse as JSON array
                    array_str = f"[{match[2]}]"
                    result[key] = json.loads(array_str)
                except:
                    # Fall back to string list
                    result[key] = [s.strip().strip('"') for s in match[2].split(',') if s.strip()]
            elif match[3]:  # Numeric value
                result[key] = int(match[3])
            # Else it's a boolean/null captured in the regex but not in a group
        
        return result if result else None
