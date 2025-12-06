"""
Configuration module for Brain Tumor Detection Streamlit App

This module centralizes all configuration constants and environment-based
overrides for the application.
"""

import os
from typing import List

# ============================================================================
# IMAGE PROCESSING CONFIGURATION
# ============================================================================

# Target image size for model input (must match training)
IMAGE_SIZE: int = 128

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

# Path to the pre-trained model file (supports environment override)
MODEL_PATH: str = os.getenv("MODEL_PATH", "model.keras")

# Class labels for tumor classification (must match model output layer)
CLASS_LABELS: List[str] = ["pituitary", "glioma", "notumor", "meningioma"]

# ============================================================================
# PREDICTION THRESHOLDS
# ============================================================================

# Confidence threshold for "high risk" classification
HIGH_RISK_THRESHOLD: float = 0.85

# Confidence threshold for "medium risk" classification
MEDIUM_RISK_THRESHOLD: float = 0.65

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================

# Streamlit page title
PAGE_TITLE: str = "Brain Tumor Detection System"

# Streamlit page icon
PAGE_ICON: str = "🧠"

# Streamlit layout mode
LAYOUT: str = "wide"

# ============================================================================
# MODEL & VERSION METADATA
# ============================================================================

# Model version identifier
MODEL_VERSION: str = "v1.0"

# Model description
MODEL_DESCRIPTION: str = "VGG16 Transfer Learning"

# Last model update date
MODEL_LAST_UPDATED: str = "December 2025"

# Model architecture description
MODEL_ARCHITECTURE: str = "VGG16 (ImageNet pre-trained) with fine-tuned classification head"

# Training configuration (for display)
TRAINING_CONFIG: dict = {
    "optimizer": "Adam (lr=0.0001)",
    "loss_function": "Sparse Categorical Crossentropy",
    "batch_size": 20,
    "epochs": 5,
    "fine_tuned_layers": "Last 3 layers of VGG16",
    "augmentation": "Brightness & Contrast variations",
}

# Model input specifications
MODEL_INPUT_SPECS: dict = {
    "image_size": IMAGE_SIZE,
    "format": "RGB",
    "channels": 3,
}

# Model output specifications
MODEL_OUTPUT_SPECS: dict = {
    "output_classes": len(CLASS_LABELS),
    "class_names": CLASS_LABELS,
    "output_type": "Softmax (probabilities)",
}

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config() -> bool:
    """
    Validate configuration values.
    
    Returns:
        True if all configurations are valid, False otherwise.
    """
    # Check that we have at least 2 classes
    if len(CLASS_LABELS) < 2:
        raise ValueError("CLASS_LABELS must contain at least 2 classes")
    
    # Check that thresholds are valid probabilities
    if not (0.0 <= MEDIUM_RISK_THRESHOLD <= 1.0):
        raise ValueError("MEDIUM_RISK_THRESHOLD must be between 0.0 and 1.0")
    
    if not (0.0 <= HIGH_RISK_THRESHOLD <= 1.0):
        raise ValueError("HIGH_RISK_THRESHOLD must be between 0.0 and 1.0")
    
    # Check that high threshold is greater than medium
    if HIGH_RISK_THRESHOLD <= MEDIUM_RISK_THRESHOLD:
        raise ValueError("HIGH_RISK_THRESHOLD must be > MEDIUM_RISK_THRESHOLD")
    
    # Check that image size is positive
    if IMAGE_SIZE <= 0:
        raise ValueError("IMAGE_SIZE must be positive")
    
    return True


# Validate on import
validate_config()
