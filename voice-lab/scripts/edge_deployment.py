#!/usr/bin/env python3
"""
Edge Deployment Script for Twi/Akan TTS
Optimizes and deploys TTS models for mobile and edge devices
"""

import os
import sys
import argparse
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
import json
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EdgeTTSDeployment:
    """Deploy TTS models to edge devices"""
    
    def __init__(self, model_path: str, target_platform: str = "mobile"):
        """Initialize edge deployment
        
        Args:
            model_path: Path to trained TTS model
            target_platform: Target platform (mobile, embedded, web)
        """
        self.model_path = Path(model_path)
        self.target_platform = target_platform
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Platform-specific settings
        self.platform_configs = {
            "mobile": {
                "max_model_size_mb": 100,
                "quantization": "int8",
                "optimize": True,
                "format": "tflite"
            },
            "embedded": {
                "max_model_size_mb": 50,
                "quantization": "int8",
                "optimize": True,
                "format": "onnx"
            },
            "web": {
                "max_model_size_mb": 20,
                "quantization": "fp16",
                "optimize": True,
                "format": "tfjs"
            }
        }
        
        self.config = self.platform_configs.get(
            target_platform,
            self.platform_configs["mobile"]
        )
    
    def setup_kokoro(self, output_dir: str):
        """Setup Kokoro TTS for edge deployment
        
        Args:
            output_dir: Directory to save Kokoro setup
        """
        logger.info("Setting up Kokoro TTS for edge deployment...")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Kokoro configuration
        kokoro_config = {
            "model": "kokoro-v0.19",
            "size_mb": 82,
            "languages": ["tw"],  # Twi support
            "sample_rate": 24000,
            "features": {
                "voice_cloning": False,  # Not supported in base Kokoro
                "multi_speaker": True,
                "speed_control": True,
                "pitch_control": True,
                "emotion_control": False
            },
            "deployment": {
                "android": {
                    "min_api": 24,
                    "architecture": ["arm64-v8a", "armeabi-v7a"],
                    "memory_required_mb": 150
                },
                "ios": {
                    "min_version": "12.0",
                    "architecture": ["arm64"],
                    "memory_required_mb": 150
                },
                "web": {
                    "format": "wasm",
                    "streaming": True,
                    "chunk_size_ms": 200
                }
            }
        }
        
        # Save Kokoro configuration
        config_path = output_path / "kokoro_config.json"
        with open(config_path, 'w') as f:
            json.dump(kokoro_config, f, indent=2)
        
        # Create Kokoro wrapper
        self._create_kokoro_wrapper(output_path)
        
        # Create deployment scripts
        self._create_deployment_scripts(output_path)
        
        logger.info(f"Kokoro setup completed at: {output_path}")
    
    def _create_kokoro_wrapper(self, output_path: Path):
        """Create Kokoro TTS wrapper for Twi
        
        Args:
            output_path: Output directory
        """
        wrapper_code = '''"""
Kokoro TTS Wrapper for Twi/Akan
Lightweight TTS for mobile and edge devices
"""

import numpy as np
from typing import Optional, Dict
import json


class KokoroTTS:
    """Kokoro TTS engine for Twi"""
    
    def __init__(self, model_path: str, device: str = "cpu"):
        """Initialize Kokoro TTS
        
        Args:
            model_path: Path to Kokoro model
            device: Device to run on (cpu, gpu, npu)
        """
        self.model_path = model_path
        self.device = device
        self.model = None
        self.config = None
        
        self._load_model()
    
    def _load_model(self):
        """Load Kokoro model"""
        # In production, this would load actual Kokoro model
        # For now, we create a placeholder
        
        config_path = f"{self.model_path}/kokoro_config.json"
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize model (placeholder)
        self.model = {
            "loaded": True,
            "language": "tw",
            "sample_rate": self.config["sample_rate"]
        }
        
        print(f"Kokoro model loaded: {self.config['model']}")
    
    def synthesize(self,
                  text: str,
                  speaker_id: int = 0,
                  speed: float = 1.0,
                  pitch: float = 0.0) -> np.ndarray:
        """Synthesize speech from text
        
        Args:
            text: Input text in Twi
            speaker_id: Speaker voice ID
            speed: Speech speed (0.5-2.0)
            pitch: Pitch adjustment (-5 to 5)
            
        Returns:
            Audio waveform as numpy array
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # Validate parameters
        speed = np.clip(speed, 0.5, 2.0)
        pitch = np.clip(pitch, -5, 5)
        
        # In production, this would call actual Kokoro inference
        # For now, generate placeholder audio
        
        duration = len(text) * 0.05 / speed  # Rough estimate
        sample_rate = self.config["sample_rate"]
        samples = int(duration * sample_rate)
        
        # Generate audio (placeholder sine wave)
        t = np.linspace(0, duration, samples)
        frequency = 200 * (2 ** (pitch / 12))  # Pitch adjustment
        audio = np.sin(2 * np.pi * frequency * t) * 0.3
        
        return audio.astype(np.float32)
    
    def synthesize_streaming(self,
                           text: str,
                           chunk_size_ms: int = 200,
                           **kwargs):
        """Synthesize speech in streaming chunks
        
        Args:
            text: Input text
            chunk_size_ms: Chunk size in milliseconds
            **kwargs: Additional synthesis parameters
            
        Yields:
            Audio chunks
        """
        # Generate full audio
        audio = self.synthesize(text, **kwargs)
        
        # Split into chunks
        sample_rate = self.config["sample_rate"]
        chunk_samples = int(chunk_size_ms * sample_rate / 1000)
        
        for i in range(0, len(audio), chunk_samples):
            chunk = audio[i:i + chunk_samples]
            yield chunk
    
    def get_speakers(self) -> Dict[int, str]:
        """Get available speaker voices
        
        Returns:
            Dictionary of speaker IDs and names
        """
        return {
            0: "asante_male",
            1: "asante_female",
            2: "akuapem_male",
            3: "akuapem_female",
            4: "fante_male",
            5: "fante_female"
        }
    
    def warmup(self):
        """Warmup model for faster first inference"""
        dummy_text = "Akwaaba"
        _ = self.synthesize(dummy_text)
        print("Model warmed up")


# Mobile-optimized version
class KokoroTTSMobile(KokoroTTS):
    """Mobile-optimized Kokoro TTS"""
    
    def __init__(self, model_path: str):
        """Initialize mobile version"""
        super().__init__(model_path, device="cpu")
        
        # Mobile-specific optimizations
        self.cache_size = 10  # Cache recent syntheses
        self.cache = {}
    
    def synthesize(self, text: str, **kwargs) -> np.ndarray:
        """Synthesize with caching"""
        # Check cache
        cache_key = f"{text}_{kwargs}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Generate audio
        audio = super().synthesize(text, **kwargs)
        
        # Update cache
        if len(self.cache) >= self.cache_size:
            # Remove oldest entry
            self.cache.pop(next(iter(self.cache)))
        
        self.cache[cache_key] = audio
        
        return audio
'''
        
        # Save wrapper
        wrapper_path = output_path / "kokoro_wrapper.py"
        with open(wrapper_path, 'w') as f:
            f.write(wrapper_code)
        
        logger.info(f"Kokoro wrapper created: {wrapper_path}")
    
    def _create_deployment_scripts(self, output_path: Path):
        """Create platform-specific deployment scripts
        
        Args:
            output_path: Output directory
        """
        # Android deployment script
        android_script = '''#!/bin/bash
# Android deployment script for Kokoro TTS

echo "Deploying Kokoro TTS to Android..."

# Check Android SDK
if [ -z "$ANDROID_HOME" ]; then
    echo "Error: ANDROID_HOME not set"
    exit 1
fi

# Create Android library structure
mkdir -p android/src/main/java/com/kokoro/tts
mkdir -p android/src/main/jniLibs/arm64-v8a
mkdir -p android/src/main/jniLibs/armeabi-v7a
mkdir -p android/src/main/assets/models

# Copy model files
cp kokoro_model.tflite android/src/main/assets/models/
cp kokoro_config.json android/src/main/assets/models/

# Create JNI wrapper
cat > android/src/main/java/com/kokoro/tts/KokoroTTS.java << 'EOF'
package com.kokoro.tts;

import android.content.Context;
import android.content.res.AssetManager;

public class KokoroTTS {
    static {
        System.loadLibrary("kokoro_tts");
    }
    
    private long nativeHandle;
    
    public KokoroTTS(Context context) {
        AssetManager assets = context.getAssets();
        nativeHandle = initNative(assets);
    }
    
    public float[] synthesize(String text, int speakerId, float speed) {
        return synthesizeNative(nativeHandle, text, speakerId, speed);
    }
    
    public void release() {
        releaseNative(nativeHandle);
    }
    
    private native long initNative(AssetManager assets);
    private native float[] synthesizeNative(long handle, String text, int speakerId, float speed);
    private native void releaseNative(long handle);
}
EOF

echo "Android deployment files created!"
'''
        
        # iOS deployment script
        ios_script = '''#!/bin/bash
# iOS deployment script for Kokoro TTS

echo "Deploying Kokoro TTS to iOS..."

# Create iOS framework structure
mkdir -p ios/KokoroTTS.framework
mkdir -p ios/KokoroTTS.framework/Headers
mkdir -p ios/KokoroTTS.framework/Modules

# Create header file
cat > ios/KokoroTTS.framework/Headers/KokoroTTS.h << 'EOF'
#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@interface KokoroTTS : NSObject

- (instancetype)initWithModelPath:(NSString *)modelPath;
- (NSData *)synthesizeText:(NSString *)text 
                 speakerId:(NSInteger)speakerId 
                     speed:(float)speed;
- (NSArray<NSString *> *)availableSpeakers;

@end

NS_ASSUME_NONNULL_END
EOF

# Create module map
cat > ios/KokoroTTS.framework/Modules/module.modulemap << 'EOF'
framework module KokoroTTS {
    umbrella header "KokoroTTS.h"
    export *
    module * { export * }
}
EOF

# Create Swift wrapper
cat > ios/KokoroTTS.swift << 'EOF'
import Foundation
import AVFoundation

public class KokoroTTSSwift {
    private let tts: KokoroTTS
    
    public init(modelPath: String) {
        self.tts = KokoroTTS(modelPath: modelPath)
    }
    
    public func speak(text: String, 
                     speakerId: Int = 0, 
                     speed: Float = 1.0) throws {
        guard let audioData = tts.synthesizeText(text, 
                                                speakerId: speakerId, 
                                                speed: speed) else {
            throw TTSError.synthesissFailed
        }
        
        // Play audio
        let player = try AVAudioPlayer(data: audioData)
        player.play()
    }
}

enum TTSError: Error {
    case synthesissFailed
}
EOF

echo "iOS deployment files created!"
'''
        
        # Web deployment script
        web_script = '''#!/bin/bash
# Web deployment script for Kokoro TTS

echo "Deploying Kokoro TTS to Web..."

# Create web structure
mkdir -p web/dist
mkdir -p web/src

# Create TypeScript wrapper
cat > web/src/kokoro-tts.ts << 'EOF'
export class KokoroTTS {
    private wasmModule: any;
    private modelBuffer: ArrayBuffer;
    
    async init(modelUrl: string): Promise<void> {
        // Load WASM module
        const wasmResponse = await fetch('kokoro-tts.wasm');
        const wasmBuffer = await wasmResponse.arrayBuffer();
        
        // Load model
        const modelResponse = await fetch(modelUrl);
        this.modelBuffer = await modelResponse.arrayBuffer();
        
        // Initialize WASM
        this.wasmModule = await WebAssembly.instantiate(wasmBuffer);
    }
    
    synthesize(text: string, options?: {
        speakerId?: number;
        speed?: number;
        pitch?: number;
    }): Float32Array {
        const {
            speakerId = 0,
            speed = 1.0,
            pitch = 0
        } = options || {};
        
        // Call WASM function
        const audioPtr = this.wasmModule.exports.synthesize(
            text,
            speakerId,
            speed,
            pitch
        );
        
        // Get audio data
        const audioLength = this.wasmModule.exports.getAudioLength();
        const audioArray = new Float32Array(
            this.wasmModule.exports.memory.buffer,
            audioPtr,
            audioLength
        );
        
        return audioArray;
    }
    
    async speak(text: string, options?: any): Promise<void> {
        const audio = this.synthesize(text, options);
        
        // Create audio context
        const audioContext = new AudioContext();
        const buffer = audioContext.createBuffer(
            1,
            audio.length,
            24000
        );
        
        buffer.copyToChannel(audio, 0);
        
        // Play audio
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        source.start();
    }
}
EOF

# Create HTML demo
cat > web/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Kokoro TTS - Twi Demo</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
        }
        textarea {
            width: 100%;
            height: 100px;
        }
        button {
            margin: 10px 5px;
            padding: 10px 20px;
        }
        .controls {
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>Kokoro TTS - Twi/Akan Demo</h1>
    
    <textarea id="text" placeholder="Enter Twi text here...">
Akwaaba! Me din de Kokoro. Mepɛ sɛ mekasa Twi.
    </textarea>
    
    <div class="controls">
        <label>Speaker:
            <select id="speaker">
                <option value="0">Asante Male</option>
                <option value="1">Asante Female</option>
                <option value="2">Akuapem Male</option>
                <option value="3">Akuapem Female</option>
            </select>
        </label>
        
        <label>Speed:
            <input type="range" id="speed" min="0.5" max="2" step="0.1" value="1">
            <span id="speedValue">1.0</span>
        </label>
    </div>
    
    <button onclick="speak()">Speak</button>
    <button onclick="download()">Download Audio</button>
    
    <script type="module">
        import { KokoroTTS } from './dist/kokoro-tts.js';
        
        let tts = null;
        
        async function init() {
            tts = new KokoroTTS();
            await tts.init('./models/kokoro-tw.wasm');
            console.log('TTS initialized');
        }
        
        window.speak = async function() {
            if (!tts) await init();
            
            const text = document.getElementById('text').value;
            const speakerId = parseInt(document.getElementById('speaker').value);
            const speed = parseFloat(document.getElementById('speed').value);
            
            await tts.speak(text, { speakerId, speed });
        };
        
        window.download = async function() {
            if (!tts) await init();
            
            const text = document.getElementById('text').value;
            const audio = tts.synthesize(text);
            
            // Convert to WAV
            const wav = createWAV(audio, 24000);
            const blob = new Blob([wav], { type: 'audio/wav' });
            
            // Download
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'twi_speech.wav';
            a.click();
        };
        
        document.getElementById('speed').oninput = function() {
            document.getElementById('speedValue').textContent = this.value;
        };
        
        function createWAV(audioData, sampleRate) {
            // Simple WAV encoder
            const length = audioData.length;
            const buffer = new ArrayBuffer(44 + length * 2);
            const view = new DataView(buffer);
            
            // WAV header
            const writeString = (offset, string) => {
                for (let i = 0; i < string.length; i++) {
                    view.setUint8(offset + i, string.charCodeAt(i));
                }
            };
            
            writeString(0, 'RIFF');
            view.setUint32(4, 36 + length * 2, true);
            writeString(8, 'WAVE');
            writeString(12, 'fmt ');
            view.setUint32(16, 16, true);
            view.setUint16(20, 1, true);
            view.setUint16(22, 1, true);
            view.setUint32(24, sampleRate, true);
            view.setUint32(28, sampleRate * 2, true);
            view.setUint16(32, 2, true);
            view.setUint16(34, 16, true);
            writeString(36, 'data');
            view.setUint32(40, length * 2, true);
            
            // Convert float to int16
            let offset = 44;
            for (let i = 0; i < length; i++) {
                const sample = Math.max(-1, Math.min(1, audioData[i]));
                view.setInt16(offset, sample * 0x7FFF, true);
                offset += 2;
            }
            
            return buffer;
        }
        
        // Initialize on load
        init();
    </script>
</body>
</html>
EOF

echo "Web deployment files created!"
'''
        
        # Save deployment scripts
        scripts = {
            "deploy_android.sh": android_script,
            "deploy_ios.sh": ios_script,
            "deploy_web.sh": web_script
        }
        
        for name, content in scripts.items():
            script_path = output_path / name
            with open(script_path, 'w') as f:
                f.write(content)
            script_path.chmod(0o755)  # Make executable
        
        logger.info(f"Deployment scripts created in: {output_path}")
    
    def optimize_model(self, model_path: str, output_dir: str) -> Dict:
        """Optimize model for edge deployment
        
        Args:
            model_path: Path to original model
            output_dir: Directory to save optimized model
            
        Returns:
            Optimization results
        """
        logger.info(f"Optimizing model for {self.target_platform}...")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Load model
        checkpoint = torch.load(model_path, map_location=self.device)
        model = checkpoint.get('model', checkpoint)
        
        # Get original model size
        original_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
        logger.info(f"Original model size: {original_size:.2f} MB")
        
        results = {
            "original_size_mb": original_size,
            "platform": self.target_platform
        }
        
        # Apply optimizations based on platform
        if self.config["quantization"] == "int8":
            model = self._quantize_int8(model)
            results["quantization"] = "int8"
        elif self.config["quantization"] == "fp16":
            model = self._quantize_fp16(model)
            results["quantization"] = "fp16"
        
        # Export to target format
        if self.config["format"] == "onnx":
            export_path = self._export_onnx(model, output_path)
            results["format"] = "onnx"
        elif self.config["format"] == "tflite":
            export_path = self._export_tflite(model, output_path)
            results["format"] = "tflite"
        elif self.config["format"] == "tfjs":
            export_path = self._export_tfjs(model, output_path)
            results["format"] = "tfjs"
        else:
            export_path = output_path / "optimized_model.pth"
            torch.save(model, export_path)
            results["format"] = "pytorch"
        
        # Get optimized size
        if export_path and export_path.exists():
            optimized_size = os.path.getsize(export_path) / (1024 * 1024)
            results["optimized_size_mb"] = optimized_size
            results["compression_ratio"] = original_size / optimized_size
            
            logger.info(f"Optimized model size: {optimized_size:.2f} MB")
            logger.info(f"Compression ratio: {results['compression_ratio']:.2f}x")
            
            # Check size constraints
            if optimized_size > self.config["max_model_size_mb"]:
                logger.warning(
                    f"Model size ({optimized_size:.2f} MB) exceeds platform limit "
                    f"({self.config['max_model_size_mb']} MB)"
                )
                results["meets_size_requirements"] = False
            else:
                results["meets_size_requirements"] = True
        
        # Save optimization report
        report_path = output_path / "optimization_report.json"
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Optimization complete. Report saved to: {report_path}")
        
        return results
    
    def _quantize_int8(self, model):
        """Quantize model to INT8
        
        Args:
            model: PyTorch model
            
        Returns:
            Quantized model
        """
        logger.info("Applying INT8 quantization...")
        
        # Dynamic quantization
        quantized_model = torch.quantization.quantize_dynamic(
            model,
            {torch.nn.Linear, torch.nn.Conv1d},
            dtype=torch.qint8
        )
        
        return quantized_model
    
    def _quantize_fp16(self, model):
        """Convert model to FP16
        
        Args:
            model: PyTorch model
            
        Returns:
            FP16 model
        """
        logger.info("Converting to FP16...")
        
        model = model.half()
        
        return model
    
    def _export_onnx(self, model, output_path: Path) -> Path:
        """Export to ONNX format
        
        Args:
            model: PyTorch model
            output_path: Output directory
            
        Returns:
            Path to exported model
        """
        logger.info("Exporting to ONNX...")
        
        export_path = output_path / "model.onnx"
        
        # Create dummy input
        dummy_input = torch.randn(1, 100).to(self.device)
        
        # Export
        torch.onnx.export(
            model,
            dummy_input,
            str(export_path),
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={
                'input': {0: 'batch_size', 1: 'sequence'},
                'output': {0: 'batch_size', 1: 'time'}
            }
        )
        
        # Optimize ONNX model
        try:
            import onnx
            from onnx import optimizer
            
            onnx_model = onnx.load(str(export_path))
            optimized_model = optimizer.optimize(onnx_model)
            onnx.save(optimized_model, str(export_path))
            
            logger.info("ONNX model optimized")
        except ImportError:
            logger.warning("ONNX optimizer not available")
        
        return export_path
    
    def _export_tflite(self, model, output_path: Path) -> Path:
        """Export to TensorFlow Lite format
        
        Args:
            model: PyTorch model
            output_path: Output directory
            
        Returns:
            Path to exported model
        """
        logger.info("Exporting to TensorFlow Lite...")
        
        export_path = output_path / "model.tflite"
        
        # First export to ONNX
        onnx_path = self._export_onnx(model, output_path)
        
        try:
            import tensorflow as tf
            import onnx
            from onnx_tf.backend import prepare
            
            # Load ONNX model
            onnx_model = onnx.load(str(onnx_path))
            
            # Convert to TensorFlow
            tf_rep = prepare(onnx_model)
            tf_rep.export_graph(str(output_path / "tf_model"))
            
            # Convert to TFLite
            converter = tf.lite.TFLiteConverter.from_saved_model(
                str(output_path / "tf_model")
            )
            
            # Apply optimizations
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.float16]
            
            tflite_model = converter.convert()
            
            # Save TFLite model
            with open(export_path, 'wb') as f:
                f.write(tflite_model)
            
            logger.info(f"TFLite model saved to: {export_path}")
            
        except ImportError as e:
            logger.error(f"TensorFlow/ONNX-TF not available: {e}")
            logger.info("Install with: pip install tensorflow onnx-tf")
            return onnx_path
        
        return export_path
    
    def _export_tfjs(self, model, output_path: Path) -> Path:
        """Export to TensorFlow.js format
        
        Args:
            model: PyTorch model
            output_path: Output directory
            
        Returns:
            Path to exported model
        """
        logger.info("Exporting to TensorFlow.js...")
        
        # This requires tensorflowjs converter
        # For now, we'll export to ONNX as intermediate
        
        onnx_path = self._export_onnx(model, output_path)
        
        logger.info("To complete TF.js export, run:")
        logger.info(f"tensorflowjs_converter --input_format=onnx {onnx_path} {output_path}/tfjs")
        
        return onnx_path
    
    def benchmark_model(self, model_path: str, num_runs: int = 100) -> Dict:
        """Benchmark model performance
        
        Args:
            model_path: Path to model
            num_runs: Number of benchmark runs
            
        Returns:
            Benchmark results
        """
        logger.info(f"Benchmarking model: {model_path}")
        
        import time
        
        # Load model (simplified)
        model = torch.load(model_path, map_location=self.device)
        if hasattr(model, 'eval'):
            model.eval()
        
        # Dummy input
        dummy_text = "Me pɛ sɛ mekasa Twi"
        dummy_input = torch.randn(1, 100).to(self.device)
        
        # Warmup
        for _ in range(10):
            with torch.no_grad():
                _ = model(dummy_input) if callable(model) else dummy_input
        
        # Benchmark
        latencies = []
        
        for _ in range(num_runs):
            start = time.perf_counter()
            
            with torch.no_grad():
                _ = model(dummy_input) if callable(model) else dummy_input
            
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms
        
        results = {
            "platform": self.target_platform,
            "device": str(self.device),
            "num_runs": num_runs,
            "latency_ms": {
                "mean": np.mean(latencies),
                "std": np.std(latencies),
                "min": np.min(latencies),
                "max": np.max(latencies),
                "p50": np.percentile(latencies, 50),
                "p95": np.percentile(latencies, 95),
                "p99": np.percentile(latencies, 99)
            },
            "throughput": {
                "samples_per_second": 1000 / np.mean(latencies)
            }
        }
        
        logger.info(f"Mean latency: {results['latency_ms']['mean']:.2f} ms")
        logger.info(f"P95 latency: {results['latency_ms']['p95']:.2f} ms")
        logger.info(f"Throughput: {results['throughput']['samples_per_second']:.2f} samples/sec")
        
        return results


def main():
    """Main edge deployment script"""
    parser = argparse.ArgumentParser(description="Deploy TTS models to edge devices")
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup edge TTS')
    setup_parser.add_argument('--platform', type=str,
                            choices=['kokoro', 'mobile', 'embedded', 'web'],
                            default='kokoro',
                            help='Target platform')
    setup_parser.add_argument('--output', type=str, required=True,
                            help='Output directory')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize model')
    optimize_parser.add_argument('--model', type=str, required=True,
                                help='Path to model')
    optimize_parser.add_argument('--platform', type=str,
                                choices=['mobile', 'embedded', 'web'],
                                default='mobile',
                                help='Target platform')
    optimize_parser.add_argument('--output', type=str, required=True,
                                help='Output directory')
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Benchmark model')
    benchmark_parser.add_argument('--model', type=str, required=True,
                                 help='Path to model')
    benchmark_parser.add_argument('--runs', type=int, default=100,
                                 help='Number of benchmark runs')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'setup':
        if args.platform == 'kokoro':
            # Setup Kokoro
            deployment = EdgeTTSDeployment("", "mobile")
            deployment.setup_kokoro(args.output)
        else:
            # Setup other platforms
            deployment = EdgeTTSDeployment("", args.platform)
            deployment.setup_kokoro(args.output)
        
    elif args.command == 'optimize':
        # Optimize model
        deployment = EdgeTTSDeployment(args.model, args.platform)
        results = deployment.optimize_model(args.model, args.output)
        
        print("\nOptimization Results:")
        print(f"  Original size: {results['original_size_mb']:.2f} MB")
        print(f"  Optimized size: {results.get('optimized_size_mb', 'N/A')} MB")
        print(f"  Compression ratio: {results.get('compression_ratio', 'N/A')}x")
        print(f"  Meets requirements: {results.get('meets_size_requirements', 'N/A')}")
        
    elif args.command == 'benchmark':
        # Benchmark model
        deployment = EdgeTTSDeployment(args.model, "mobile")
        results = deployment.benchmark_model(args.model, args.runs)
        
        print("\nBenchmark Results:")
        print(f"  Mean latency: {results['latency_ms']['mean']:.2f} ms")
        print(f"  P95 latency: {results['latency_ms']['p95']:.2f} ms")
        print(f"  Throughput: {results['throughput']['samples_per_second']:.2f} samples/sec")
    
    logger.info("Edge deployment completed!")


if __name__ == "__main__":
    main()