initial_schema = {
    "type": "object",
    "properties": {
        "objects_in_room": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "new_object_id": {
                        "type": "string",
                        "description": "The id of the object, e.g. chair_1, table_1, bed_1, etc."
                    },
                    "style": {
                        "type": "string",
                        "description": "Architectural style of the object"
                    },
                    "material": {
                        "type": "string",
                        "description": "The material that this object is made of"
                    },
                    "size_in_meters": {
                        "type": "object",
                        "properties": {
                            "length": {"type": "number"},
                            "width": {"type": "number"},
                            "height": {"type": "number"}
                        },
                        "required": ["length", "width", "height"]
                    },
                    "is_on_the_floor": {
                        "type": "boolean",
                        "description": "Whether this object is touching the floor"
                    },
                    "facing": {
                        "type": "string",
                        "description": "The id of the object this object is facing, e.g. west_wall, bookshelf_1"
                    },
                    "placement": {
                        "type": "object",
                        "properties": {
                            "room_layout_elements": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "layout_element_id": {
                                            "type": "string",
                                            "enum": ["south_wall", "north_wall", "west_wall", "east_wall", "ceiling", "middle of the room"]
                                        },
                                        "preposition": {
                                            "type": "string",
                                            "enum": ["on", "in the corner"]
                                        }
                                    },
                                    "required": ["layout_element_id", "preposition"]
                                }
                            },
                            "objects_in_room": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "object_id": {"type": "string"},
                                        "preposition": {
                                            "type": "string",
                                            "enum": ["on", "left of", "right of", "in front", "behind", "under", "above"]
                                        },
                                        "is_adjacent": {"type": "boolean"}
                                    }
                                }
                            }
                        },
                        "required": ["room_layout_elements", "objects_in_room"]
                    }
                },
                "required": ["new_object_id", "style", "material", "size_in_meters", "is_on_the_floor", "facing", "placement"]
            }
        }
    },
    "required": ["objects_in_room"]
}


interior_designer_schema = {
    "type": "object",
    "properties": {
        "Objects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "object_name": {"type": "string"},
                    "architecture_style": {"type": "string"},
                    "material": {"type": "string"},
                    "bounding_box_size": {
                        "type": "object",
                        "properties": {
                            "length": {"type": "number"},
                            "width": {"type": "number"},
                            "height": {"type": "number"}
                        },
                        "required": ["length", "width", "height"]
                    },
                    "quantity": {"type": "integer"}
                },
                "required": ["object_name", "architecture_style", "material", "bounding_box_size", "quantity"]
            }
        }
    },
    "required": ["Objects"]
}


interior_architect_schema = {
    "type": "object",
    "properties": {
        "Objects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "object_name": {"type": "string"},
                    "Placements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "placement": {"type": "string"},
                                "proximity": {"type": "string"},
                                "facing": {"type": "string"}
                            },
                            "required": ["placement", "proximity", "facing"]
                        }
                    }
                },
                "required": ["object_name", "Placements"]
            }
        }
    },
    "required": ["Objects"]
}




engineer_schema = {
    "type": "object",
    "properties": {
        "objects_in_room": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "new_object_id": {
                        "type": "string",
                        "description": "The id of the object, e.g. chair_1, table_1, bed_1, etc."
                    },
                    "style": {"type": "string"},
                    "material": {"type": "string"},
                    "size_in_meters": {
                        "type": "object",
                        "properties": {
                            "length": {"type": "number"},
                            "width": {"type": "number"},
                            "height": {"type": "number"}
                        },
                        "required": ["length", "width", "height"]
                    },
                    "is_on_the_floor": {"type": "boolean"},
                    "facing": {"type": "string"},
                    "placement": {
                        "type": "object",
                        "properties": {
                            "room_layout_elements": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "layout_element_id": {
                                            "type": "string",
                                            "enum": ["south_wall", "north_wall", "west_wall", "east_wall", "ceiling", "middle of the room"]
                                        },
                                        "preposition": {
                                            "type": "string",
                                            "enum": ["on", "in the corner"]
                                        }
                                    },
                                    "required": ["layout_element_id", "preposition"]
                                }
                            }
                        },
                        "required": ["room_layout_elements"]
                    }
                },
                "required": ["new_object_id", "style", "material", "size_in_meters", "is_on_the_floor", "facing", "placement"]
            }
        }
    },
    "required": ["objects_in_room"]
}

layout_corrector_schema = {
    "type": "object",
    "properties": {
        "corrected_object": {
            "type": "object",
            "properties": {
                "new_object_id": {
                    "type": "string",
                    "description": "The id of the object, e.g. chair_1, table_1, bed_1, etc."
                },
                "is_on_the_floor": {
                    "type": "boolean",
                    "description": "Whether this object is touching the floor"
                },
                "facing": {
                    "type": "string",
                    "description": "The id of the object this object is facing"
                },
                "placement": {
                    "type": "object",
                    "properties": {
                        "room_layout_elements": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "layout_element_id": {
                                        "type": "string",
                                        "enum": ["south_wall", "north_wall", "west_wall", "east_wall", "ceiling", "middle of the room"]
                                    },
                                    "preposition": {
                                        "type": "string",
                                        "enum": ["on", "in the corner"]
                                    }
                                },
                                "required": ["layout_element_id", "preposition"]
                            }
                        },
                        "objects_in_room": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "object_id": {"type": "string"},
                                    "preposition": {
                                        "type": "string",
                                        "enum": ["on", "left of", "right of", "in front", "behind", "under", "above"]
                                    },
                                    "is_adjacent": {"type": "boolean"}
                                }
                            }
                        }
                    },
                    "required": ["room_layout_elements", "objects_in_room"]
                }
            },
            "required": ["new_object_id", "is_on_the_floor", "facing", "placement"]
        }
    }
}

deletion_schema = {
    "type": "object",
    "properties": {
        "object_to_delete": {
            "type": "string",
            "description": "The id of the object to be deleted, e.g. desk_1"
        }
    },
    "required": ["object_to_delete"]
}

layout_refiner_schema = {
    "type": "object",
    "properties": {
        "children_objects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name_id": {"type": "string"},
                    "placement": {
                        "type": "object",
                        "properties": {
                            "children_objects": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name_id": {"type": "string"},
                                        "preposition": {
                                            "type": "string",
                                            "enum": ["on", "left of", "right of", "in front", "behind", "under", "above"]
                                        },
                                        "is_adjacent": {"type": "boolean"}
                                    },
                                    "required": ["name_id", "preposition", "is_adjacent"]
                                }
                            }
                        },
                        "required": ["children_objects"]
                    }
                },
                "required": ["name_id", "placement"]
            }
        }
    },
    "required": ["children_objects"]
}
