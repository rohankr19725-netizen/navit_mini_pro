# 🧠 Brain Tumor Detection Using Deep Learning

A comprehensive machine learning solution for detecting and classifying brain tumors from MRI images using deep learning and transfer learning with VGG16.

## 📋 Project Overview

This project implements a complete pipeline for brain tumor detection including:
- **Model Training**: Transfer learning using VGG16 pre-trained on ImageNet
- **Web Application**: Production-style Streamlit web app for inference
- **Classification**: 4-class tumor classification (Pituitary, Glioma, Meningioma, No Tumor)

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mini_proj
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # OR
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Streamlit App

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## 📁 Project Structure

```
mini_proj/
├── app.py                                          # Main Streamlit web application
├── brain_tumour_detection_using_deep_learning.ipynb  # Jupyter notebook with model training
├── model.keras                                     # Pre-trained model weights
├── requirements.txt                                # Python dependencies
├── README.md                                       # This file
├── main.py                                         # Legacy Flask application
├── index.html                                      # Legacy Flask template
└── [test images]                                   # Sample MRI images for testing
```

## 🧠 Model Architecture

**Base Model**: VGG16 (Pre-trained on ImageNet)

**Architecture Details**:
- Input: 128×128 RGB Images
- Base: VGG16 with frozen initial layers
- Fine-tuned: Last 3 layers of VGG16 trainable
- Custom Head:
  - Flatten layer
  - Dropout(0.3)
  - Dense(128, relu)
  - Dropout(0.2)
  - Dense(4, softmax) - Output layer for 4 classes

**Training Configuration**:
- Optimizer: Adam (learning_rate=0.0001)
- Loss: Sparse Categorical Crossentropy
- Metrics: Sparse Categorical Accuracy
- Batch Size: 20
- Epochs: 5

## 🎯 Classification Labels

The model classifies MRI images into 4 categories:

| Label | Description |
|-------|-------------|
| **Pituitary** | 🔴 Pituitary gland tumors (benign, hormone-secreting) |
| **Glioma** | 🔵 Brain tumors originating from glial cells |
| **Meningioma** | 🟣 Tumors of the brain membrane (benign) |
| **No Tumor** | ✅ Healthy MRI scan with no tumor detected |

## 🖼️ Input Requirements

- **Format**: JPG, JPEG, or PNG
- **Size**: Minimum 224×224 pixels recommended
- **Type**: Brain MRI images
- **Color**: RGB or grayscale (auto-converted to RGB)

## 🔍 Using the Streamlit App

### Step-by-Step Guide

1. **Upload an MRI Image**
   - Click "Browse files" or drag-and-drop an MRI image
   - Supported formats: `.jpg`, `.jpeg`, `.png`

2. **View the Image**
   - The uploaded MRI will be displayed for verification

3. **Run Analysis**
   - Click the "🔍 Analyze MRI" button
   - Wait for the model to process and predict

4. **Review Results**
   - **Predicted Classification**: Tumor type detected
   - **Confidence Score**: Probability of prediction (0-100%)
   - **Risk Assessment**: Color-coded risk level
   - **Model Interpretation**: Professional analysis text
   - **Detailed Probabilities**: Breakdown of all class predictions

## 📊 Features

### Main Application
- ✅ Professional Streamlit UI with responsive layout
- ✅ Real-time image preprocessing and validation
- ✅ Model caching to optimize performance
- ✅ Detailed prediction metrics and confidence scores
- ✅ Risk assessment based on confidence thresholds
- ✅ Professional interpretation of predictions
- ✅ Detailed probability breakdown for all classes

### Sidebar
- 📋 Step-by-step usage instructions
- ℹ️ Model and dataset information (expandable)
- ⚠️ Medical disclaimer (expandable)

### Error Handling
- Graceful handling of invalid image formats
- User-friendly error messages
- Image validation and preprocessing checks
- Model loading error handling

### Professional Features
- 🔐 Type hints for code clarity
- 📝 Comprehensive docstrings
- 🎯 Production-ready error handling
- 📊 Detailed logging for debugging
- ⚠️ Prominent medical disclaimers

## ⚠️ Important Medical Disclaimer

**This application is for RESEARCH and EDUCATIONAL purposes ONLY.**

### Limitations
- ❌ NOT a certified medical device
- ❌ NOT a substitute for professional medical diagnosis
- ❌ Cannot be used for clinical decision-making
- ✅ Must be reviewed by qualified radiologists before any medical use

### Recommendations
- Always consult qualified healthcare professionals
- Results must be verified by medical experts
- Do not use for diagnostic purposes without professional review
- Use only for research, education, and demonstration

## 🔧 Technical Details

### Dependencies
- **TensorFlow/Keras**: Model inference and preprocessing
- **Streamlit**: Web application framework
- **Pillow (PIL)**: Image processing
- **NumPy**: Numerical operations
- **Pandas**: Data manipulation and display

### Image Preprocessing Pipeline
1. Load image using PIL
2. Convert to RGB if necessary
3. Resize to 128×128 pixels
4. Normalize pixel values to [0, 1]
5. Add batch dimension for model input

### Prediction Pipeline
1. Preprocess input image
2. Run model inference
3. Extract predicted class and confidence
4. Determine risk level based on confidence thresholds:
   - 🔴 High Risk: ≥ 85% confidence
   - 🟡 Medium Risk: ≥ 65% confidence
   - 🟢 Low Risk: < 65% confidence

## 📈 Model Performance

The model uses transfer learning from VGG16, which provides:
- Pre-trained features from ImageNet (1.4M images)
- Fine-tuning on brain tumor dataset
- Robust feature extraction for medical imaging

Performance metrics are available in the Jupyter notebook.

## 🔍 Code Quality

### Standards Followed
- **Type Hints**: Clear function signatures with type annotations
- **Docstrings**: Comprehensive documentation for all functions
- **Error Handling**: Graceful error handling with user-friendly messages
- **Logging**: Detailed logging for debugging and monitoring
- **Code Organization**: Modular functions with single responsibilities
- **Production Ready**: Clean, maintainable, industry-standard code

## 📝 Development & Training

### Training the Model (Jupyter Notebook)

The `brain_tumour_detection_using_deep_learning.ipynb` notebook contains:
- Data loading and exploration
- Image preprocessing and augmentation
- Model architecture definition
- Training pipeline
- Evaluation metrics and visualizations
- Model saving and loading

To retrain or modify the model, see the Jupyter notebook.

## 🚀 Deployment

### Local Deployment
```bash
streamlit run app.py
```

### Production Deployment
For production deployment, consider:
- Using a production-grade Python server (Gunicorn)
- Docker containerization
- Cloud platforms (Heroku, AWS, Google Cloud, etc.)
- Load balancing for multiple instances
- API endpoint for model serving (FastAPI/Flask)

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- Type hints are included
- Docstrings are comprehensive
- Error handling is robust
- Medical disclaimers are maintained

## 📞 Support

For issues or questions:
1. Check the Jupyter notebook for model details
2. Review the error messages and logs
3. Verify the model file exists at `model.keras`
4. Ensure all dependencies are installed correctly

## 📄 License

This project is for educational and research purposes.

## 🙏 Acknowledgments

- VGG16 architecture from Oxford Visual Geometry Group
- Transfer learning methodology
- Streamlit framework for web application
- TensorFlow/Keras for deep learning

---

**Last Updated**: December 2025
**Version**: 1.0.0