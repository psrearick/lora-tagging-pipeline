
```json
{
    "project_name": "My LoRA Project",
    "target_size": 1024,
    "clip_threshold": 0.25,
    "clip_model": "ViT-B-32",
    "loras": {
        "lora1_<axis_group>": [
            "<axis_name>",
            "<axis_name>"
        ],
        "lora2_<axis_group>": [
            "<axis_name>"
        ],
        "lora3_<axis_group>": [
            "<axis_name>"
        ]
    },
    "axes": {
        "<axis_name>": {
            "tags": {
                "<prefix>_<tag>": {
                    "description": "A plain-language description of this tag as you would describe it in an image caption. CLIP scores images against this text, so be specific and visual.",
                    "synonyms": [
                        "<synonym>",
                        "<synonym>",
                        "<synonym>"
                    ]
                },
                "<prefix>_<tag>": {
                    "description": "Another tag in this axis. Tags within an axis should be mutually exclusive — each image should match exactly one.",
                    "synonyms": [
                        "<synonym>",
                        "<synonym>"
                    ]
                }
            }
        },
        "<axis_name>": {
            "tags": {
                "<prefix>_<tag>": {
                    "description": "Tags across different axes can co-occur freely. An image can have one tag from each axis simultaneously.",
                    "synonyms": [
                        "<synonym>"
                    ]
                },
                "<prefix>_<tag>": {
                    "description": "Add as many tags per axis as needed. Three to six tags per axis is a practical range.",
                    "synonyms": [
                        "<synonym>",
                        "<synonym>"
                    ]
                }
            }
        }
    }
}
```
