/*
 * SmartBin Classification Example
 * 
 * This example demonstrates how to use the SmartBinClassifier class
 * to capture images from ESP32-CAM and classify waste materials.
 * 
 * Supported waste categories:
 * - metal
 * - misc
 * - paper
 * - plastic
 */

#include "SmartBinClassifier.h"

// Create classifier instance
SmartBinClassifier classifier;

void setup() {
    Serial.begin(115200);
    while (!Serial); // Wait for serial connection
    
    Serial.println("Smart Bin Waste Classifier Demo");
    Serial.println("================================");
    
    // Initialize the classifier (this also initializes the camera)
    if (!classifier.initCamera()) {
        Serial.println("Failed to initialize camera!");
        while (1); // Stop execution
    }
    
    Serial.println("Camera initialized successfully!");
    Serial.println("Starting classification in 3 seconds...");
    delay(3000);
}

void loop() {
    Serial.println("\n--- Capturing and Classifying ---");
    
    // Method 1: Capture and classify in one call
    ClassificationResult result = classifier.captureAndClassify();
    
    if (result.success) {
        Serial.println("Classification Results:");
        Serial.println("======================");
        Serial.printf("Top prediction: %s (%.2f%% confidence)\n", 
                     result.topClass.c_str(), 
                     result.topConfidence * 100.0);
        
        Serial.println("\nAll predictions:");
        for (int i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
            Serial.printf("  %s: %.2f%%\n", 
                         result.classes[i].c_str(), 
                         result.confidence[i] * 100.0);
        }
        
        // Example: Take action based on classification
        handleClassificationResult(result);
        
    } else {
        Serial.printf("Classification failed: %s\n", result.error.c_str());
    }
    
    // Method 2: Separate capture and classify calls (alternative approach)
    /*
    if (classifier.captureImage()) {
        Serial.println("Image captured successfully");
        
        ClassificationResult result = classifier.classifyImage();
        if (result.success) {
            Serial.printf("Classified as: %s\n", result.topClass.c_str());
        }
    }
    */
    
    // Wait before next classification
    delay(5000);
}

// Example function to handle classification results
void handleClassificationResult(const ClassificationResult& result) {
    // Only act if confidence is above threshold
    if (result.topConfidence > 0.7) {
        Serial.printf("\nAction: Sorting %s waste\n", result.topClass.c_str());
        
        if (result.topClass == "metal") {
            // Trigger metal bin mechanism
            Serial.println("-> Opening metal compartment");
            // activateMetalBin();
            
        } else if (result.topClass == "paper") {
            // Trigger paper bin mechanism
            Serial.println("-> Opening paper compartment");
            // activatePaperBin();
            
        } else if (result.topClass == "plastic") {
            // Trigger plastic bin mechanism
            Serial.println("-> Opening plastic compartment");
            // activatePlasticBin();
            
        } else if (result.topClass == "misc") {
            // Trigger miscellaneous bin mechanism
            Serial.println("-> Opening miscellaneous compartment");
            // activateMiscBin();
        }
        
    } else {
        Serial.printf("Low confidence (%.1f%%), asking user for manual sorting\n", 
                     result.topConfidence * 100.0);
        // Could trigger manual sorting request or default bin
    }
}

// Example bin activation functions (implement based on your hardware)
/*
void activateMetalBin() {
    // Control servo/motor to open metal compartment
    // Set LED indicator for metal
    // Log to database, etc.
}

void activatePaperBin() {
    // Control servo/motor to open paper compartment
    // Set LED indicator for paper
}

void activatePlasticBin() {
    // Control servo/motor to open plastic compartment
    // Set LED indicator for plastic
}

void activateMiscBin() {
    // Control servo/motor to open misc compartment
    // Set LED indicator for misc
}
*/
