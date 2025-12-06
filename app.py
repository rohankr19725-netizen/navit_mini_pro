"""
Brain Tumor Detection Using Deep Learning - Streamlit Web App

This is a production-style Streamlit application for detecting brain tumors
from MRI images using a pre-trained deep learning model.

Author: ML/MLOps Team
Date: December 2025
"""

import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image, UnidentifiedImageError
from typing import Tuple, Optional, Dict, Any, List, TypedDict
import logging
from datetime import datetime

# TensorFlow/Keras imports
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.preprocessing.image import img_to_array

# Local imports
from config import (
    IMAGE_SIZE,
    CLASS_LABELS,
    HIGH_RISK_THRESHOLD,
    MEDIUM_RISK_THRESHOLD,
    PAGE_TITLE,
    PAGE_ICON,
    LAYOUT,
    MODEL_PATH,
    MODEL_VERSION,
    MODEL_DESCRIPTION,
    MODEL_LAST_UPDATED,
    MODEL_ARCHITECTURE,
    TRAINING_CONFIG,
    MODEL_INPUT_SPECS,
    MODEL_OUTPUT_SPECS,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================


class PredictionResult(TypedDict):
    """Type definition for structured prediction output."""
    predicted_class: str
    predicted_class_index: int
    confidence_score: float
    risk_level: str
    probs: np.ndarray


# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================


def validate_config() -> None:
    """
    Validate configuration values on application startup.
    
    Ensures:
    - Risk thresholds are in valid range (0 < medium < high < 1)
    - Model input size matches configured IMAGE_SIZE
    - Number of classes matches configuration
    
    Raises:
        AssertionError: If configuration is invalid.
        
    Side Effects:
        Logs configuration validation results.
    """
    try:
        # Validate thresholds
        assert 0 < MEDIUM_RISK_THRESHOLD < HIGH_RISK_THRESHOLD < 1, (
            f"Risk thresholds invalid: need 0 < MEDIUM ({MEDIUM_RISK_THRESHOLD}) "
            f"< HIGH ({HIGH_RISK_THRESHOLD}) < 1"
        )
        
        # Validate image size matches input specs
        assert MODEL_INPUT_SPECS["image_size"] == IMAGE_SIZE, (
            f"IMAGE_SIZE ({IMAGE_SIZE}) must match MODEL_INPUT_SPECS.image_size "
            f"({MODEL_INPUT_SPECS['image_size']})"
        )
        
        # Validate number of classes
        expected_classes = len(CLASS_LABELS)
        config_classes = MODEL_OUTPUT_SPECS.get("output_classes", expected_classes)
        assert config_classes == expected_classes, (
            f"Number of classes mismatch: CLASS_LABELS has {expected_classes} "
            f"but MODEL_OUTPUT_SPECS says {config_classes}"
        )
        
        logger.info("✓ Configuration validation passed")
        logger.info(f"  - Risk thresholds: medium={MEDIUM_RISK_THRESHOLD}, high={HIGH_RISK_THRESHOLD}")
        logger.info(f"  - Image size: {IMAGE_SIZE}×{IMAGE_SIZE}")
        logger.info(f"  - Classes: {expected_classes}")
        
    except AssertionError as e:
        error_msg = f"Configuration validation failed: {str(e)}"
        logger.error(error_msg)
        raise


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================


def initialize_session_state() -> None:
    """
    Initialize Streamlit session state variables for persistent app state.
    
    Creates:
    - prediction_history: List of prediction records for this session
    - last_prediction_result: Most recent prediction for accessing in UI
    - processing: Flag to prevent concurrent predictions
    
    Side Effects:
        Modifies st.session_state directly on first run only.
    """
    if "prediction_history" not in st.session_state:
        st.session_state.prediction_history = []
    
    if "last_prediction_result" not in st.session_state:
        st.session_state.last_prediction_result = None
    
    if "processing" not in st.session_state:
        st.session_state.processing = False


def add_to_prediction_history(
    filename: str,
    predicted_class: str,
    confidence_score: float,
    risk_level: str,
) -> None:
    """
    Add a prediction to the session history.
    
    Args:
        filename: Name of the uploaded file.
        predicted_class: Predicted tumor class.
        confidence_score: Model confidence (0.0-1.0).
        risk_level: Risk level string (e.g., "🔴 High").
    
    Side Effects:
        Appends to st.session_state.prediction_history.
    """
    history_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "filename": filename,
        "predicted_class": predicted_class,
        "confidence": confidence_score,
        "risk_level": risk_level,
    }
    st.session_state.prediction_history.append(history_entry)


def get_history_dataframe() -> Optional[pd.DataFrame]:
    """
    Convert prediction history to a displayable DataFrame.
    
    Returns:
        DataFrame with prediction history sorted by most recent first,
        or None if no predictions exist.
    """
    if not st.session_state.prediction_history:
        return None
    
    df = pd.DataFrame(st.session_state.prediction_history)
    
    # Format columns
    df["confidence"] = df["confidence"].apply(lambda x: f"{x*100:.1f}%")
    
    # Sort by timestamp descending (most recent first)
    df = df.iloc[::-1].reset_index(drop=True)
    
    # Rename for display
    df = df.rename(columns={
        "timestamp": "Time",
        "filename": "File",
        "predicted_class": "Predicted Class",
        "confidence": "Confidence",
        "risk_level": "Risk Level",
    })
    
    return df

# ============================================================================
# VALIDATION & HELPER FUNCTIONS
# ============================================================================


def validate_model(model: Model) -> bool:
    """
    Validate that the loaded model has the expected output shape.
    
    Args:
        model: Loaded Keras model to validate.
    
    Returns:
        True if model is valid, False otherwise.
    
    Raises:
        ValueError: If model output shape doesn't match number of classes.
    """
    try:
        output_classes = model.output_shape[-1]
        expected_classes = len(CLASS_LABELS)
        
        if output_classes != expected_classes:
            error_msg = (
                f"Model output shape mismatch: expected {expected_classes} "
                f"classes ({CLASS_LABELS}), but model has {output_classes} outputs."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Model validation successful: {expected_classes} output classes")
        return True
    
    except Exception as e:
        logger.error(f"Model validation failed: {str(e)}")
        raise


def confidence_band(confidence_score: float) -> str:
    """
    Determine risk level category based on confidence score.
    
    Maps confidence score to a risk level string with emoji indicator.
    
    Args:
        confidence_score: Model confidence between 0.0 and 1.0.
    
    Returns:
        Risk level string with emoji (e.g., "🔴 High", "🟡 Medium", "🟢 Low").
    """
    if confidence_score >= HIGH_RISK_THRESHOLD:
        return "🔴 High"
    elif confidence_score >= MEDIUM_RISK_THRESHOLD:
        return "🟡 Medium"
    else:
        return "🟢 Low"


def generate_prediction_report(
    filename: str,
    predicted_class: str,
    confidence_score: float,
    risk_level: str,
    interpretation: str,
    probs: np.ndarray,
) -> str:
    """
    Generate a professional markdown report of the prediction.
    
    Creates a downloadable report with all prediction details, interpretation,
    and medical disclaimers.
    
    Args:
        filename: Name of the analyzed file.
        predicted_class: Predicted tumor class.
        confidence_score: Model confidence (0.0-1.0).
        risk_level: Risk level string (e.g., "🔴 High").
        interpretation: Professional interpretation text.
        probs: Probability vector from model (one value per class).
    
    Returns:
        Markdown-formatted report string.
    """
    class_emoji = {
        "pituitary": "🔴",
        "glioma": "🔵",
        "meningioma": "🟣",
        "notumor": "✅",
    }
    emoji = class_emoji.get(predicted_class, "")
    
    report = f"""# Brain Tumor Detection Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Analysis Details

- **File Analyzed:** {filename}
- **Model Version:** {MODEL_VERSION}
- **Analysis Date:** {datetime.now().strftime("%Y-%m-%d")}

---

## Prediction Results

### Primary Prediction
- **Tumor Classification:** {emoji} {predicted_class.capitalize()}
- **Confidence Score:** {confidence_score*100:.2f}%
- **Risk Assessment:** {risk_level}

### Model Interpretation
{interpretation}

---

## Detailed Probabilities

| Tumor Type | Probability |
|-----------|-------------|
"""
    
    # Add probability breakdown with real values
    for label, prob in zip(CLASS_LABELS, probs):
        report += f"| {label.capitalize()} | {prob*100:.2f}% |\n"
    
    report += f"""

---

## ⚠️ IMPORTANT MEDICAL DISCLAIMER

**This report is for research and educational purposes ONLY.**

### Not a Medical Device
- This analysis is **NOT** a certified medical device
- It **CANNOT** be used for clinical diagnosis or treatment
- Results **DO NOT** replace professional medical evaluation
- **MUST** be reviewed by qualified radiologists or medical professionals

### Limitations
- Model predictions may contain errors
- Analysis accuracy depends on image quality and preprocessing
- Predictions are probabilistic and may be incorrect
- Cultural, geographic, or demographic variations may affect accuracy

### Recommended Use
- Research and educational purposes only
- Academic studies and training
- Technology demonstration and evaluation
- **NOT** for clinical decision-making or patient diagnosis

### Next Steps
**Professional Review Required:** Any results from this analysis must be:
1. Reviewed by qualified radiologists
2. Compared with clinical findings
3. Integrated with patient history and examination
4. Used only to support professional medical judgment

---

## Important Notice

**Always consult qualified healthcare professionals for medical diagnosis, treatment decisions, and patient care.** This tool cannot and should not replace professional medical expertise.

For medical concerns, contact a licensed healthcare provider or qualified medical specialist.

---

*Report generated by Brain Tumor Detection System (Research Edition)*
*This is an automated analysis tool for educational and research purposes.*
"""
    
    return report
    
    report += f"""

---

## ⚠️ IMPORTANT MEDICAL DISCLAIMER

**This report is for research and educational purposes ONLY.**

### Not a Medical Device
- This analysis is **NOT** a certified medical device
- It **CANNOT** be used for clinical diagnosis or treatment
- Results **DO NOT** replace professional medical evaluation
- **MUST** be reviewed by qualified radiologists or medical professionals

### Limitations
- Model predictions may contain errors
- Analysis accuracy depends on image quality and preprocessing
- Predictions are probabilistic and may be incorrect
- Cultural, geographic, or demographic variations may affect accuracy

### Recommended Use
- Research and educational purposes only
- Academic studies and training
- Technology demonstration and evaluation
- **NOT** for clinical decision-making or patient diagnosis

### Next Steps
**Professional Review Required:** Any results from this analysis must be:
1. Reviewed by qualified radiologists
2. Compared with clinical findings
3. Integrated with patient history and examination
4. Used only to support professional medical judgment

---

## Important Notice

**Always consult qualified healthcare professionals for medical diagnosis, treatment decisions, and patient care.** This tool cannot and should not replace professional medical expertise.

For medical concerns, contact a licensed healthcare provider or qualified medical specialist.

---

*Report generated by Brain Tumor Detection System (Research Edition)*
*This is an automated analysis tool for educational and research purposes.*
"""
    
    return report

# ============================================================================
# CORE MODEL FUNCTIONS
# ============================================================================


@st.cache_resource
def load_trained_model() -> Optional[Model]:
    """
    Load the pre-trained brain tumor detection model with validation.
    
    Uses Streamlit cache to load the model only once across all sessions.
    Automatically validates the model after loading.
    
    Returns:
        Trained Keras model with validated output shape, or None if loading fails.
        
    Side Effects:
        Displays error message in UI if model file not found or loading fails.
    """
    try:
        import os
        
        if not os.path.exists(MODEL_PATH):
            error_msg = f"Model file not found at {MODEL_PATH}"
            st.error(error_msg)
            logger.error(error_msg)
            return None
        
        model = load_model(MODEL_PATH)
        
        # Validate model
        validate_model(model)
        
        logger.info(f"Model loaded and validated successfully from {MODEL_PATH}")
        return model
    
    except ValueError as e:
        # Model validation error
        error_msg = f"Model validation error: {str(e)}"
        st.error(error_msg)
        logger.error(error_msg)
        return None
    
    except Exception as e:
        error_msg = f"Failed to load model: {str(e)}"
        st.error(error_msg)
        logger.error(error_msg)
        return None


def preprocess_image(
    uploaded_file: Any,
) -> Optional[Tuple[np.ndarray, Image.Image]]:
    """
    Preprocess the uploaded MRI image to match the model's expected input format.
    
    Preprocessing steps:
    - Validate that file is a valid image
    - Convert to RGB if necessary (handles grayscale/RGBA)
    - Resize to (IMAGE_SIZE, IMAGE_SIZE)
    - Normalize pixel values to [0, 1]
    - Add batch dimension for model input
    
    Args:
        uploaded_file: Streamlit UploadedFile object from file_uploader.
    
    Returns:
        Tuple of (preprocessed image array for model, original PIL image for display)
        or None if preprocessing fails.
        
    Side Effects:
        Displays error message in UI if file is invalid or corrupted.
        Logs preprocessing steps and any errors.
    """
    try:
        # Load image as PIL Image
        img = Image.open(uploaded_file)
        
    except UnidentifiedImageError:
        error_msg = (
            f"Invalid image file: '{uploaded_file.name}' is not a valid image file. "
            "Please upload a JPG, PNG, or other supported image format."
        )
        st.error(error_msg)
        logger.error(f"Image validation failed: {uploaded_file.name} is not a valid image")
        return None
    
    except Exception as e:
        error_msg = f"Error reading image file: {str(e)}"
        st.error(error_msg)
        logger.error(f"Error opening image {uploaded_file.name}: {str(e)}")
        return None
    
    try:
        # Convert to RGB if grayscale or RGBA
        if img.mode != "RGB":
            logger.info(f"Converting image from {img.mode} to RGB")
            img = img.convert("RGB")
        
        # Store original for display
        display_img = img.copy()
        
        # Resize to model input size
        img = img.resize((IMAGE_SIZE, IMAGE_SIZE))
        
        # Convert to numpy array and normalize
        img_array = img_to_array(img) / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        logger.info(
            f"Image preprocessing successful for {uploaded_file.name}. "
            f"Shape: {img_array.shape}"
        )
        return img_array, display_img
    
    except Exception as e:
        error_msg = f"Error processing image: {str(e)}"
        st.error(error_msg)
        logger.error(f"Error preprocessing {uploaded_file.name}: {str(e)}")
        return None


def predict_tumor(model: Model, preprocessed_image: np.ndarray) -> Optional[PredictionResult]:
    """
    Run the model prediction on the preprocessed image.
    
    Performs inference exactly once and returns a structured result containing
    all prediction information. This result is used throughout the app to avoid
    redundant model calls.
    
    Args:
        model: Trained Keras model.
        preprocessed_image: Preprocessed image array with shape (1, IMAGE_SIZE, IMAGE_SIZE, 3).
    
    Returns:
        PredictionResult containing:
            - predicted_class (str): Class label (e.g., 'pituitary', 'glioma', etc.)
            - predicted_class_index (int): Index of predicted class
            - confidence_score (float): Confidence between 0.0 and 1.0
            - risk_level (str): Risk category with emoji (e.g., "🔴 High")
            - probs (np.ndarray): Full probability vector for all classes (shape: (4,))
        
        Returns None if prediction fails.
        
    Side Effects:
        Logs prediction details. Displays error in UI if prediction fails.
    """
    try:
        # Run model inference exactly once
        predictions = model.predict(preprocessed_image, verbose=0)
        
        # Extract predictions
        predicted_class_index = int(np.argmax(predictions[0]))
        confidence_score = float(np.max(predictions[0]))
        predicted_class = CLASS_LABELS[predicted_class_index]
        
        # Determine risk level
        risk_level = confidence_band(confidence_score)
        
        # Full probability vector
        probs = predictions[0]
        
        logger.info(
            f"Prediction successful: class={predicted_class}, "
            f"confidence={confidence_score:.4f}, risk={risk_level}"
        )
        
        return PredictionResult(
            predicted_class=predicted_class,
            predicted_class_index=predicted_class_index,
            confidence_score=confidence_score,
            risk_level=risk_level,
            probs=probs,
        )
    
    except Exception as e:
        error_msg = f"Prediction failed: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        return None


def get_prediction_interpretation(
    predicted_class: str, confidence_score: float
) -> str:
    """
    Generate a professional interpretation of the prediction result.
    
    Provides contextual interpretation text based on the predicted class
    and confidence score. Uses the confidence_band helper to determine
    risk level for interpretation.
    
    Args:
        predicted_class: Predicted tumor class (e.g., 'pituitary', 'notumor').
        confidence_score: Model confidence between 0.0 and 1.0.
    
    Returns:
        Professional interpretation string with Markdown formatting.
    """
    class_descriptions = {
        "pituitary": "Pituitary tumor (benign, hormone-secreting gland tumor)",
        "glioma": "Glioma (brain tumor originating from glial cells)",
        "meningioma": "Meningioma (benign tumor of brain membrane)",
        "notumor": "No tumor detected",
    }
    
    # Get risk level using the same logic as predictions
    risk_band = confidence_band(confidence_score)
    
    if predicted_class == "notumor":
        interpretation = (
            f"The model finds **no evidence of a tumor** in the MRI image "
            f"with a confidence score of {confidence_score*100:.1f}%."
        )
    else:
        class_desc = class_descriptions.get(predicted_class, predicted_class)
        interpretation = (
            f"The model has identified a **{class_desc.lower()}** "
            f"with a confidence score of {confidence_score*100:.1f}%. "
            f"Risk assessment: {risk_band}. "
            f"This suggests a significant likelihood of this condition."
        )
    
    return interpretation


# ============================================================================
# UI COMPONENTS
# ============================================================================


def render_page_config() -> None:
    """
    Configure Streamlit page settings.
    
    Sets page title, icon, and layout mode using centralized configuration.
    """
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state="expanded",
    )


def render_header() -> None:
    """
    Render the main page header with title and description.
    
    Displays the application title, subtitle, and brief description
    at the top of the main content area.
    """
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("# 🧠 Brain Tumor Detection")
    with col2:
        st.markdown(
            """
            **Using Deep Learning on MRI Images**
            
            Leveraging transfer learning with VGG16 for accurate tumor classification.
            """
        )
    st.markdown("---")


def render_sidebar() -> None:
    """
    Render the sidebar with quick information and navigation guidance.
    
    Displays the app title and directs users to the tabs for detailed information.
    Most content moved to tabs for better space utilization.
    """
    st.sidebar.markdown("## 🧠 Brain Tumor Detector")
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### Quick Start
    1. **Upload** an MRI image
    2. **Analyze** using the model
    3. **Review** predictions and risk
    
    📊 See **Model Details** tab for technical information
    ℹ️ See **About & Limitations** tab for disclaimers
    """)
    st.sidebar.markdown("---")
    
    # Show session stats if there's history
    if st.session_state.prediction_history:
        st.sidebar.markdown(f"### 📈 Session Stats")
        st.sidebar.metric("Predictions Analyzed", len(st.session_state.prediction_history))
        st.sidebar.markdown("*Restart browser tab to clear history*")


def render_analysis_tab() -> None:
    """
    Render the Analysis tab with image upload and prediction interface.
    
    Features:
    - Image upload with drag-and-drop
    - Side-by-side image and results layout
    - Analyze button with progress feedback
    - Results display with metrics and interpretation
    - Prediction history display
    - Download report button
    """
    st.markdown("### 📤 Upload MRI Image")
    st.markdown("Upload a brain MRI image for analysis. Supported formats: JPG, PNG")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a brain MRI image file",
        type=["jpg", "jpeg", "png"],
        help="Upload an MRI brain image in JPG or PNG format",
        label_visibility="collapsed",
    )
    
    if uploaded_file is not None:
        # Create two columns: image on left, results on right
        img_col, results_col = st.columns([1, 1.2], gap="medium")
        
        with img_col:
            st.markdown("#### 📸 Uploaded Image")
            st.image(uploaded_file, use_column_width=True, caption="MRI Image")
        
        with results_col:
            st.markdown("#### 🔍 Analysis Controls")
            
            # Analyze button with state management
            analyze_button = st.button(
                "🔍 Analyze MRI",
                key="analyze_button",
                use_container_width=True,
                disabled=st.session_state.processing,
            )
            
            if analyze_button:
                st.session_state.processing = True
                
                # Progress indicator
                progress_bar = st.progress(0, text="Initializing...")
                
                try:
                    # Load model
                    progress_bar.progress(20, text="Loading model...")
                    model = load_trained_model()
                    if model is None:
                        st.error(
                            "❌ Failed to load the model. "
                            "Please check that 'model.keras' exists in the project root."
                        )
                        st.session_state.processing = False
                        return
                    
                    # Preprocess image
                    progress_bar.progress(40, text="Preprocessing image...")
                    preprocessed = preprocess_image(uploaded_file)
                    if preprocessed is None:
                        st.error("❌ Failed to preprocess the image.")
                        st.session_state.processing = False
                        return
                    
                    preprocessed_img, display_img = preprocessed
                    
                    # Run prediction
                    progress_bar.progress(70, text="Running prediction...")
                    prediction_result = predict_tumor(model, preprocessed_img)
                    
                    progress_bar.progress(90, text="Generating report...")
                    
                    if prediction_result is None:
                        st.error("❌ Prediction failed. Please check the logs for details.")
                        st.session_state.processing = False
                        return
                    
                    # Store in session state
                    st.session_state.last_prediction_result = prediction_result
                    
                    # Extract results
                    predicted_class = prediction_result["predicted_class"]
                    confidence_score = prediction_result["confidence_score"]
                    risk_level = prediction_result["risk_level"]
                    
                    # Add to history
                    add_to_prediction_history(
                        filename=uploaded_file.name,
                        predicted_class=predicted_class,
                        confidence_score=confidence_score,
                        risk_level=risk_level,
                    )
                    
                    progress_bar.progress(100, text="Complete!")
                    
                    st.success("✅ Analysis complete!")
                    
                except Exception as e:
                    error_msg = f"Error during analysis: {str(e)}"
                    st.error(f"❌ {error_msg}")
                    logger.error(error_msg)
                
                finally:
                    st.session_state.processing = False
                    progress_bar.empty()
        
        # Display results if available
        if st.session_state.last_prediction_result:
            st.markdown("---")
            
            prediction_result = st.session_state.last_prediction_result
            predicted_class = prediction_result["predicted_class"]
            confidence_score = prediction_result["confidence_score"]
            risk_level = prediction_result["risk_level"]
            probs = prediction_result["probs"]
            
            # Results section header
            st.markdown("### 📊 Prediction Results")
            
            # Metrics display
            metric_col1, metric_col2, metric_col3 = st.columns(3, gap="large")
            
            class_display = {
                "pituitary": "🔴 Pituitary",
                "glioma": "🔵 Glioma",
                "meningioma": "🟣 Meningioma",
                "notumor": "✅ No Tumor",
            }
            
            with metric_col1:
                st.metric(
                    "Classification",
                    class_display.get(predicted_class, predicted_class),
                )
            
            with metric_col2:
                st.metric("Confidence", f"{confidence_score*100:.1f}%")
            
            with metric_col3:
                st.metric("Risk Level", risk_level)
            
            # Professional interpretation
            st.markdown("#### 💡 Model Interpretation")
            interpretation = get_prediction_interpretation(predicted_class, confidence_score)
            st.markdown(interpretation)
            
            # Status message based on prediction
            st.markdown("---")
            if predicted_class == "notumor":
                st.success(
                    f"✅ **No tumor detected** - The model identifies this MRI as normal with "
                    f"{confidence_score*100:.1f}% confidence."
                )
            else:
                if confidence_score >= HIGH_RISK_THRESHOLD:
                    st.error(
                        f"⚠️ **High Confidence Prediction** - {predicted_class.capitalize()} "
                        f"detected at {confidence_score*100:.1f}% confidence. "
                        f"Professional review is strongly recommended."
                    )
                elif confidence_score >= MEDIUM_RISK_THRESHOLD:
                    st.warning(
                        f"⚠️ **Medium Confidence Prediction** - {predicted_class.capitalize()} "
                        f"detected at {confidence_score*100:.1f}% confidence. "
                        f"Professional medical evaluation is recommended."
                    )
                else:
                    st.info(
                        f"ℹ️ **Low Confidence Prediction** - {predicted_class.capitalize()} "
                        f"suggested at {confidence_score*100:.1f}% confidence. "
                        f"Results should be interpreted with caution and verified by specialists."
                    )
            
            # Probability table
            st.markdown("#### 📋 Detailed Prediction Probabilities")
            class_probs = {
                "Tumor Type": [label.capitalize() for label in CLASS_LABELS],
                "Probability": [f"{prob*100:.2f}%" for prob in probs],
                "Confidence": probs,
            }
            df_probs = pd.DataFrame(class_probs)
            df_probs = df_probs.sort_values("Confidence", ascending=False)
            st.dataframe(
                df_probs[["Tumor Type", "Probability"]],
                use_container_width=True,
                hide_index=True,
            )
            
            # Download report button
            st.markdown("#### 📥 Export Results")
            report_content = generate_prediction_report(
                filename=uploaded_file.name,
                predicted_class=predicted_class,
                confidence_score=confidence_score,
                risk_level=risk_level,
                interpretation=interpretation,
                probs=probs,
            )
            
            st.download_button(
                label="📄 Download Report (Markdown)",
                data=report_content,
                file_name="brain_tumor_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
            
            # Show prediction history
            st.markdown("---")
            st.markdown("### 🧾 Session Prediction History")
            
            history_df = get_history_dataframe()
            if history_df is not None:
                st.dataframe(history_df, use_container_width=True, hide_index=True)
            else:
                st.info("No predictions yet in this session.")
    
    else:
        st.info("👆 Upload an MRI image to get started")


def render_model_details_tab() -> None:
    """
    Render the Model Details tab with technical information.
    
    Displays:
    - Model version and metadata
    - Architecture details
    - Training configuration
    - Input/output specifications
    - Classes and thresholds
    """
    st.markdown("## 🤖 Model Architecture & Configuration")
    
    # Model identity
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Model Information")
        st.markdown(f"""
        - **Version:** {MODEL_VERSION}
        - **Description:** {MODEL_DESCRIPTION}
        - **Last Updated:** {MODEL_LAST_UPDATED}
        - **Architecture:** {MODEL_ARCHITECTURE}
        """)
    
    with col2:
        st.markdown("### Input Specifications")
        st.markdown(f"""
        - **Image Size:** {MODEL_INPUT_SPECS['image_size']}×{MODEL_INPUT_SPECS['image_size']} pixels
        - **Format:** {MODEL_INPUT_SPECS['format']}
        - **Channels:** {MODEL_INPUT_SPECS['channels']}
        - **Normalization:** 0-1 (pixel_value / 255.0)
        """)
    
    st.markdown("---")
    
    # Training configuration
    st.markdown("### ⚙️ Training Configuration")
    
    training_col1, training_col2 = st.columns(2)
    with training_col1:
        st.markdown("**Optimizer & Loss:**")
        st.markdown(f"""
        - Optimizer: {TRAINING_CONFIG['optimizer']}
        - Loss Function: {TRAINING_CONFIG['loss_function']}
        """)
    
    with training_col2:
        st.markdown("**Training Parameters:**")
        st.markdown(f"""
        - Batch Size: {TRAINING_CONFIG['batch_size']}
        - Epochs: {TRAINING_CONFIG['epochs']}
        - Fine-tuned: {TRAINING_CONFIG['fine_tuned_layers']}
        """)
    
    st.markdown("**Data Augmentation:**")
    st.markdown(f"- {TRAINING_CONFIG['augmentation']}")
    
    st.markdown("---")
    
    # Classification details
    st.markdown("### 🎯 Classification Details")
    
    st.markdown("**Output Classes:**")
    class_info = {
        "Class Name": [],
        "Index": [],
        "Description": [],
    }
    
    descriptions = {
        "pituitary": "Pituitary gland tumors (typically benign)",
        "glioma": "Brain tumors originating from glial cells",
        "meningioma": "Benign tumors of the brain membrane",
        "notumor": "Normal MRI scan with no tumor detected",
    }
    
    for idx, (label, desc) in enumerate(descriptions.items()):
        class_info["Class Name"].append(label.capitalize())
        class_info["Index"].append(idx)
        class_info["Description"].append(desc)
    
    st.dataframe(
        pd.DataFrame(class_info),
        use_container_width=True,
        hide_index=True,
    )
    
    st.markdown("---")
    
    # Risk thresholds
    st.markdown("### 📊 Risk Assessment Thresholds")
    
    threshold_info = {
        "Risk Level": ["🔴 High", "🟡 Medium", "🟢 Low"],
        "Confidence Range": [
            f"≥ {HIGH_RISK_THRESHOLD*100:.0f}%",
            f"{MEDIUM_RISK_THRESHOLD*100:.0f}% - {(HIGH_RISK_THRESHOLD-0.01)*100:.0f}%",
            f"< {MEDIUM_RISK_THRESHOLD*100:.0f}%",
        ],
    }
    
    st.dataframe(
        pd.DataFrame(threshold_info),
        use_container_width=True,
        hide_index=True,
    )


def render_about_tab() -> None:
    """
    Render the About & Limitations tab with disclaimers and usage guidance.
    
    Displays:
    - How the model works (simplified explanation)
    - Intended use cases
    - Important limitations
    - Medical disclaimers
    - Not for clinical decision-making
    """
    st.markdown("## ℹ️ About This Tool")
    
    st.markdown("### 🧠 How the Model Works")
    
    with st.expander("Model Explanation (Click to expand)", expanded=True):
        st.markdown("""
        #### What is Transfer Learning?
        
        This model uses **transfer learning**, which means:
        
        1. **Starting Point:** We begin with VGG16, a model trained on millions of general images
           from ImageNet to recognize patterns like edges, shapes, and textures.
        
        2. **Specialization:** We then train this model on a dataset of brain MRI images,
           teaching it to recognize specific patterns associated with different tumor types.
        
        3. **Efficiency:** Transfer learning allows us to build accurate medical AI models
           without needing millions of medical images.
        
        #### What the Model Actually Does
        
        - Takes a 128×128 pixel MRI image as input
        - Processes it through convolutional neural network layers
        - Outputs probabilities for 4 classes: Pituitary, Glioma, Meningioma, or No Tumor
        - The highest probability becomes the predicted class
        
        #### Confidence Score
        
        - Represents how "sure" the model is about its prediction
        - Range: 0% (not sure) to 100% (very confident)
        - **Higher confidence doesn't necessarily mean higher accuracy**
        - Always verify results with medical professionals
        """)
    
    st.markdown("---")
    
    st.markdown("### ✅ Intended Use")
    
    intended_col1, intended_col2 = st.columns(2)
    
    with intended_col1:
        st.markdown("**Appropriate Uses:**")
        st.markdown("""
        ✓ Educational demonstrations
        ✓ Machine learning research
        ✓ Technology workshops
        ✓ Understanding ML concepts
        ✓ Computer vision exploration
        ✓ Academic projects
        """)
    
    with intended_col2:
        st.markdown("**NOT Appropriate For:**")
        st.markdown("""
        ✗ Clinical diagnosis
        ✗ Patient treatment decisions
        ✗ Medical device replacement
        ✗ Standalone medical tool
        ✗ Self-diagnosis
        ✗ Any clinical environment
        """)
    
    st.markdown("---")
    
    st.markdown("### ⚠️ Important Limitations")
    
    with st.expander("Limitations & Considerations (Click to expand)", expanded=True):
        st.markdown("""
        #### Technical Limitations
        
        - **Model errors:** All AI models make mistakes, sometimes confidently wrong
        - **Image dependency:** Results depend heavily on image quality and preprocessing
        - **Limited training data:** Model trained on finite dataset, may not generalize perfectly
        - **No guarantees:** Probabilistic output, not deterministic diagnosis
        
        #### Data Limitations
        
        - **Dataset bias:** Training data may overrepresent certain demographics
        - **Geographic bias:** May perform differently on different populations
        - **Equipment variation:** Different MRI scanners produce different image characteristics
        - **Preprocessing artifacts:** Image processing can introduce errors
        
        #### Clinical Limitations
        
        - **Incomplete information:** Single image doesn't capture full clinical picture
        - **Contextual missing:** No patient history, symptoms, or clinical presentation
        - **Professional judgment needed:** Radiologists use extensive training and experience
        - **Multi-disciplinary assessment:** Diagnosis requires collaboration of specialists
        
        #### Regulatory Status
        
        - **NOT FDA approved** as a medical device
        - **NOT certified** for clinical use
        - **NOT validated** in clinical trials
        - **NOT licensed** for patient diagnosis
        """)
    
    st.markdown("---")
    
    st.markdown("### 🚨 Medical Disclaimer")
    
    st.warning("""
        ### CRITICAL DISCLAIMER
        
        **This application is for research and educational purposes ONLY.**
        
        #### ❌ What This Is NOT
        - NOT a medical device
        - NOT a diagnostic tool
        - NOT a treatment recommendation system
        - NOT a substitute for professional medical evaluation
        - NOT approved for clinical use
        
        #### ✅ What This Actually Is
        - An educational demonstration of AI capabilities
        - A machine learning research tool
        - A technology showcase
        - An experimental prototype
        
        #### 📋 Required Actions
        
        **For ANY medical concern:**
        1. Contact a qualified healthcare professional
        2. See a licensed medical doctor
        3. Get a proper clinical diagnosis
        4. Do NOT rely on this tool for medical decisions
        
        **If you have brain-related symptoms:**
        - Contact your primary care physician
        - Seek urgent care if symptoms are severe
        - Get a professional MRI and evaluation
        - Work with qualified neurologists/radiologists
        
        #### Legal Notice
        
        By using this tool, you acknowledge that:
        - You understand this is NOT a medical device
        - You will NOT use results for clinical decision-making
        - You will seek professional medical advice for real symptoms
        - You accept full responsibility for your health decisions
        
        **The developers and deployers of this application assume NO liability
        for any medical outcomes resulting from use of this tool.**
        
        ### ⚖️ Always consult qualified healthcare professionals.
    """)
    
    st.markdown("---")
    
    st.markdown("### 💡 Recommended Approach")
    
    st.info("""
        **For Research/Education:**
        - Use this tool with sample images
        - Understand the technology behind it
        - Learn about transfer learning and neural networks
        - Explore AI/ML concepts
        
        **For Academic Work:**
        - Reference this tool properly
        - Acknowledge its limitations
        - Use it as a learning example
        - Don't claim it's a diagnostic tool
        
        **For Real Medical Needs:**
        - Always consult qualified healthcare professionals
        - Provide your images to certified radiologists
        - Get professional medical evaluation
        - Never use this tool as a substitute for medical care
    """)


def render_main_content() -> None:
    """
    Render the main content area with tabs for different sections.
    
    Creates three main tabs:
    - Analysis: Image upload and prediction
    - Model Details: Technical specifications
    - About & Limitations: Disclaimers and usage guide
    """
    tab1, tab2, tab3 = st.tabs(["🔍 Analysis", "🤖 Model Details", "ℹ️ About & Limitations"])
    
    with tab1:
        render_analysis_tab()
    
    with tab2:
        render_model_details_tab()
    
    with tab3:
        render_about_tab()


def render_footer() -> None:
    """
    Render the page footer with disclaimers and attribution.
    
    Displays:
    - Prominent medical disclaimers
    - Important limitations
    - Attribution and version information
    """
    st.markdown("---")
    
    st.markdown("### ⚠️ Important Medical Disclaimer")
    st.warning(
        """
        **This application is for research and educational purposes ONLY.**
        
        - ❌ NOT a certified medical device
        - ❌ NOT a substitute for professional medical diagnosis
        - ✅ For educational and research use only
        - ✅ Results must be verified by qualified radiologists
        
        **Always consult qualified healthcare professionals for medical diagnosis and treatment.**
        """
    )
    
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; font-size: 0.85rem; color: gray;'>
        
        **Brain Tumor Detection System** | Built with Streamlit & Deep Learning
        
        Model: VGG16 Transfer Learning | Input: MRI Images (128×128)
        
        Last Updated: December 2025
        
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# MAIN APPLICATION
# ============================================================================


def main() -> None:
    """
    Main application entry point.
    
    Orchestrates the rendering of all UI components in the correct order:
    1. Validate configuration
    2. Initialize session state
    3. Page configuration
    4. Sidebar content
    5. Main header
    6. Main content (tabs with Analysis, Model Details, About)
    7. Footer with disclaimers
    """
    try:
        # Validate configuration on startup
        validate_config()
    except AssertionError as e:
        st.error(f"❌ Configuration Error: {str(e)}")
        logger.error(f"Configuration validation failed: {str(e)}")
        return
    
    # Initialize session state on first run
    initialize_session_state()
    
    # Configure page
    render_page_config()
    
    # Render UI components
    render_sidebar()
    render_header()
    render_main_content()
    render_footer()


if __name__ == "__main__":
    main()
