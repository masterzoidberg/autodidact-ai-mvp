import json
from pathlib import Path
from typing import Dict, List

def generate_curriculum(goal: str) -> Dict[str, List[Dict[str, List[str]]]]:
    """Generate a curriculum for the given goal.

    Currently hardcodes a sample curriculum for the goal 'Learn Typography'.
    The curriculum is also written to ``curriculum.json`` in the same folder.
    """
    goal_normalized = goal.strip().lower()
    if goal_normalized != "learn typography":
        raise NotImplementedError(
            "Only a hardcoded curriculum for 'Learn Typography' is implemented"
        )

    curriculum = {
        "goal": "Learn Typography",
        "topics": [
            {"title": "Introduction to Typography", "prerequisites": []},
            {"title": "Fonts and Typefaces", "prerequisites": ["Introduction to Typography"]},
            {
                "title": "Layout and Hierarchy",
                "prerequisites": ["Introduction to Typography", "Fonts and Typefaces"],
            },
            {
                "title": "Typography for Web",
                "prerequisites": ["Layout and Hierarchy"],
            },
            {
                "title": "Advanced Typography Techniques",
                "prerequisites": ["Typography for Web"],
            },
        ],
    }

    output_path = Path(__file__).with_name("curriculum.json")
    output_path.write_text(json.dumps(curriculum, indent=2))
    return curriculum
