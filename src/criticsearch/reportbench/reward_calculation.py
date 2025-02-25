from extract_ground_truth import extractDirectoryTree

class RewardCalculator:
    def __init__(self):
        self.current_section_name = None  # Guide model to search/generate current section
        self.current_section_ground_truth = None
        self.current_section_student_answer = None
