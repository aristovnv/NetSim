from dataclasses import dataclass
import random
import DataClasses.Node as Node
# deprecated_module.py
import warnings

# Show deprecation warning when module is imported
warnings.warn(
    "This module is deprecated and will be removed in future versions."
    "Remove all references",
    DeprecationWarning,
    stacklevel=2
)

@dataclass
class Cargo:
    id: int
    weight: float
    origin_port: Node
    destination_port: Node
    is_loaded: bool = False






