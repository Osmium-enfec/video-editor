"""
Job abstraction for ffedit.
Represents a video editing job.
"""
class Job:
    def __init__(self, operation, input_files, output_file, params=None):
        self.operation = operation
        self.input_files = input_files
        self.output_file = output_file
        self.params = params or {}
        self.status = "pending"
        self.progress = 0.0
        self.error = None
