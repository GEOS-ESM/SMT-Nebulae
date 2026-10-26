import os


class ArgumentValidationError(ValueError):
    """Raised when cross-argument validation fails."""

    pass


class RunnerArgs:
    """Holds CLI arguments"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class BaseRunner:
    def __init__(self, **kwargs):
        self.args = RunnerArgs(**kwargs)
        self.env = os.environ.copy()
        self.rundir = os.getcwd()

        self.validate_inputs()

    def validate_inputs(self):
        """Override this in subclasses to perform cross-argument validation."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement 'validate_inputs'")

    def run(self):
        """Execute the pipeline steps in sequence."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement 'run'")


class PipelineStep:
    """Base class for a pipeline step. Subclass and override the three internal methods below to implement custom behavior."""

    def validate_inputs(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__} must implement 'validate_inputs'")

    def operate(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__} must implement 'operate'")

    def validate_outputs(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__} must implement 'validate_outputs'")

    def __call__(self, *args, **kwargs):
        self.validate_inputs(*args, **kwargs)
        result = self.operate(*args, **kwargs)
        self.validate_outputs(result)
        return result
