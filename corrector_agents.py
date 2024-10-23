import autogen
from autogen import AssistantAgent, UserProxyAgent
from copy import deepcopy
from jsonschema import validate
import json
import re

from schemas import layout_corrector_schema, deletion_schema
from agents import is_termination_msg


class JSONSchemaAgent(UserProxyAgent):
    def __init__(self, name: str, is_termination_msg):
        super().__init__(name, is_termination_msg=is_termination_msg)

    def get_human_input(self, prompt: str) -> str:
        message = self.last_message()
        preps_layout = ["left-side", "right-side", "in the middle"]
        preps_objs = ['on', 'left of', 'right of', 'in front', 'behind', 'under', 'above']

        # Extract JSON content from the message using regex
        pattern = r'```json\s*([^`]+)\s*```'  # Match the JSON object
        match = re.search(pattern, message["content"], re.DOTALL)
        
        if not match:
            return "Invalid format: No JSON object found in the message."

        json_obj_new = json.loads(match.group(1))

        is_success = False
        try:
            validate(instance=json_obj_new, schema=layout_corrector_schema)
            return "SUCCESS"
        except Exception as e:
            feedback = str(e)
            if "enum" in feedback:
                if any(prep in feedback for prep in preps_objs):
                    feedback += f" Change the preposition {e.instance} to something suitable from {preps_objs}."
                elif any(prep in feedback for prep in preps_layout):
                    feedback += f" Change the preposition {e.instance} to something suitable from {preps_layout}."
        
        return feedback


# Load the Groq Llama models for both vision and language tasks
config_list_llama_vision = autogen.config_list_from_json(
    "OAI_CONFIG_LIST.json",
    filter_dict={
        "model": ["llama-3.2-11b-vision-preview"],
    },
)

config_list_llama_language = autogen.config_list_from_json(
    "OAI_CONFIG_LIST.json",
    filter_dict={
        "model": ["llama3-8b-8192"],
    },
)

# Configuration for the Llama vision model
llama_vision_config = {
    "cache_seed": 42,
    "temperature": 0.0,
    "config_list": config_list_llama_vision,
    "timeout": 600,
}

# Configuration for the Llama language model with JSON output
llama_language_json_config = deepcopy(llama_vision_config)
llama_language_json_config["config_list"] = config_list_llama_language
llama_language_json_config["config_list"][0]["response_format"] = {"type": "json_object"}


def get_corrector_agents():
    # User Proxy Agent (human interaction proxy)
    user_proxy = autogen.UserProxyAgent(
        name="Admin",
        system_message="A human admin.",
        is_termination_msg=is_termination_msg,
        human_input_mode="NEVER",
        code_execution_config=False
    )

    # JSON Schema Debugger Agent
    json_schema_debugger = JSONSchemaAgent(
        name="Json_schema_debugger",
        is_termination_msg=is_termination_msg,
    )

    # Spatial Corrector Agent using Groq Llama vision model for spatial conflict correction
    spatial_corrector_agent = AssistantAgent(
        name="Spatial_corrector_agent",
        llm_config=llama_vision_config,
        is_termination_msg=is_termination_msg,
        human_input_mode="NEVER",
        system_message=f"""
        Spatial Corrector Agent. Whenever a user provides an object that doesn't fit the room due to spatial conflicts,
        you will make changes to its "scene_graph" and "facing_object" keys so that these conflicts are resolved.
        You will use the JSON Schema to validate the JSON object that the user provides.

        For relative placement with other objects in the room, use the prepositions "on", "left of", "right of", "in front", "behind", "under".
        For relative placement with room layout elements (walls, middle of the room, ceiling), use the prepositions "on", "in the corner".

        Use only the following JSON Schema to save the corrected JSON object:
        {layout_corrector_schema}
        """
    )

    # Object Deletion Agent using Groq Llama language model for selecting non-essential objects
    object_deletion_agent = AssistantAgent(
        name="Object_deletion_agent",
        llm_config=llama_language_json_config,
        is_termination_msg=is_termination_msg,
        human_input_mode="NEVER",
        system_message=f"""
        Object Deletion Agent. When the user provides a list of objects that don't fit the room, select one object to delete that would be the least essential for the room.

        Example JSON output:
        {deletion_schema}
        """
    )

    # Return the agents
    return user_proxy, json_schema_debugger, spatial_corrector_agent, object_deletion_agent
