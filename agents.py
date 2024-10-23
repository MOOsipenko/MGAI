import autogen
from autogen import AssistantAgent, UserProxyAgent
import json
from jsonschema import validate
from copy import deepcopy
from schemas import (
    initial_schema,
    interior_designer_schema,
    interior_architect_schema,
    engineer_schema
)
# Load configuration from the environment variable or JSON file (OAI_CONFIG_LIST)
config_list = autogen.config_list_from_json("OAI_CONFIG_LIST.json")

# Filter configuration for specific Groq models
config_list_llama_vision = [config for config in config_list if config["model"] == "llama-3.2-11b-text-preview"]
config_list_llama_8b = [config for config in config_list if config["model"] == "llama3-8b-8192"]

# Model configuration settings for Llama Vision (11B)
llama_vision_config = {
    "cache_seed": 42,
    "temperature": 0.7,
    "top_p": 1.0,
    "config_list": config_list_llama_vision,
    "timeout": 600,
}

# Model configuration settings for Llama 8B
llama_8b_config = {
    "cache_seed": 42,
    "temperature": 0.7,
    "top_p": 1.0,
    "config_list": config_list_llama_8b,
    "timeout": 600,
}

# Additional configurations for JSON output using the vision model
llama_json_config = deepcopy(llama_vision_config)
llama_json_config["config_list"][0]["response_format"] = {"type": "json_object"}

# JSON-specific configuration for the engineer using the Llama 8B model
llama_engineer_json_config = deepcopy(llama_8b_config)
llama_engineer_json_config["temperature"] = 0.0
llama_engineer_json_config["config_list"][0]["response_format"] = {"type": "json_object"}

# Function to check for termination messages
def is_termination_msg(content) -> bool:
    have_content = content.get("content", None) is not None
    if have_content and content["name"] == "Json_schema_debugger" and "SUCCESS" in content["content"]:
        return True
    return False

# Custom UserProxyAgent with JSON Schema validation
class JSONSchemaAgent(UserProxyAgent):
    def __init__(self, name: str, is_termination_msg):
        super().__init__(name, is_termination_msg=is_termination_msg)

    def get_human_input(self, prompt: str) -> str:
        message = self.last_message()
        preps_layout = ['in front', 'on', 'in the corner', 'in the middle of']
        preps_objs = ['on', 'left of', 'right of', 'in front', 'behind', 'under', 'above']

        try:
            json_obj_new = json.loads(message["content"])
        except json.JSONDecodeError as e:
            return f"Invalid JSON data: {str(e)}"

        try:
            json_obj_new_ids = [item["new_object_id"] for item in json_obj_new["objects_in_room"]]
        except KeyError:
            return "Use 'new_object_id' instead of 'object_id'!"

        is_success = False
        try:
            validate(instance=json_obj_new, schema=initial_schema)
            is_success = True
        except Exception as e:
            feedback = str(e)
            if e.validator == "enum":
                if e.instance in json_obj_new_ids:
                    feedback += f" Put the {e.instance} object under 'objects_in_room' instead of 'room_layout_elements' and delete the {e.instance} object under 'room_layout_elements'."
                elif str(preps_objs) in feedback:
                    feedback += f" Change the preposition {e.instance} to something suitable from {preps_objs}."
                elif str(preps_layout) in feedback:
                    feedback += f" Change the preposition {e.instance} to something suitable from {preps_layout}."
        
        if is_success:
            return "SUCCESS"
        return feedback

# Function to create and return the agents
def create_agents(no_of_objects: int):
    # User Proxy Agent for human admin
    user_proxy = autogen.UserProxyAgent(
        name="Admin",
        system_message="A human admin.",
        is_termination_msg=is_termination_msg,
        code_execution_config=False,
    )

    # JSON Schema Debugger Agent
    json_schema_debugger = JSONSchemaAgent(
        name="Json_schema_debugger",
        is_termination_msg=is_termination_msg,
    )

    # Interior Designer Agent using Groq Llama 3.2 11B Vision
    interior_designer = autogen.AssistantAgent(
        name="Interior_designer",
        llm_config=llama_json_config,
        human_input_mode="NEVER",
        is_termination_msg=is_termination_msg,
        system_message=f"""Interior Designer. Based on the user preferences, suggest a set of essential objects to design the room.
        Each object should include:
        1. Name (e.g., Sofa, Coffee Table)
        2. Style (e.g., Modern, Classic)
        3. Material (e.g., Leather, Wood)
        4. Dimensions (length, width, height)
        5. Quantity (number of objects needed)
        
        Follow the schema:
        {interior_designer_schema}
        """
    )

    # Interior Architect Agent using Groq Llama 3.2 11B Vision
    interior_architect = autogen.AssistantAgent(
        name="Interior_architect",
        llm_config=llama_json_config,
        human_input_mode="NEVER",
        is_termination_msg=is_termination_msg,
        system_message=f"""Interior Architect. Analyze the user preferences and suggest optimal placement for each object suggested by the Interior Designer.
        Each object should have explicit details for:
        1. Placement (e.g., in the corner, on the east wall)
        2. Proximity (Adjacent or Not Adjacent)
        3. Facing (e.g., facing the west wall)

        Make sure every object includes a valid 'Placements' field, even if the object has no specific placement yet. Use placeholders or default values if necessary.

        Follow the schema:
        {interior_architect_schema}
        """
    )

    # Engineer Agent using Groq Llama 8B for JSON handling
    engineer = autogen.AssistantAgent(
        name="Engineer",
        llm_config=llama_engineer_json_config,
        human_input_mode="NEVER",
        is_termination_msg=is_termination_msg,
        system_message=f"""Engineer. Create and store the objects suggested by the Interior Designer in the JSON schema.
        Each object should have accurate spatial placement and quantity information.
        
        Follow the schema:
        {engineer_schema}
        """
    )

    # Return all agents
    return user_proxy, json_schema_debugger, interior_designer, interior_architect, engineer
