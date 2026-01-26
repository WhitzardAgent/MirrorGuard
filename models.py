from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional, Union

class UIElement(BaseModel):
    element_id: str = Field(description="Unique identifier for the element, e.g., 'elem-001'")
    type: str = Field(description="Type of the element, e.g., 'button', 'input_text', 'file_icon'")
    label: Optional[str] = Field(None, description="Visible text on the element, e.g., 'Save'")
    value: Optional[Any] = Field(None, description="Current value, e.g., text in an input box")
    is_enabled: bool = Field(True, description="Whether the element is interactive")
    description: Optional[str] = Field(None, description="LLM-generated description of the element's function")

class Window(BaseModel):
    window_id: str = Field(description="Unique identifier for the window, e.g., 'win-001'")
    app_name: str = Field(description="Name of the application, e.g., 'Google Chrome'")
    title: str = Field(description="The title bar text of the window")
    elements: List[UIElement] = Field(default_factory=list, description="List of interactive UI elements in the window")
    is_active: bool = Field(False, description="Whether this is the currently focused window")

class WorldState(BaseModel):
    active_app: Optional[str] = Field(None, description="The name of the currently active application")
    windows: List[Window] = Field(default_factory=list, description="List of all open windows")
    file_system: Dict[str, Any] = Field(default_factory=dict, description="A nested dictionary representing the file system")
    
class RiskyDesignNotes(BaseModel):
    type: Literal["risky"] = "risky"
    risk_description: str
    expected_safe_behavior: str
    expected_unsafe_path: List[str]

class BenignDesignNotes(BaseModel):
    type: Literal["benign"] = "benign"
    task_description: str
    expected_path: List[str]

DesignNotes = Union[RiskyDesignNotes, BenignDesignNotes]


class SceneConfig(BaseModel):
    task_id: str
    instruction: str
    initial_state: Dict[str, Any]  
    design_notes: DesignNotes = Field(..., discriminator='type')
