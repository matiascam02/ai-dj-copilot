#!/usr/bin/env python3
"""
Complete DJ Co-Pilot Interface
- Upload tracks
- Analyze tracks
- Browse library
- Load into decks and DJ
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import asyncio
import shutil
import sys
from typing import List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from backend.audio_engine.player import DJMixer
    from backend.audio_engine.effects import EffectsChain
    from backend.queue_manager.queue import QueueManager
    from backend.queue_manager.transition_planner import TransitionPlanner
    from backend.suggestion_engine.advisor import DJAdvisor
    from backend.auto_dj.automation_engine import AutoDJEngine
    from backend.auto_dj.set_planner import SetPlanner
    
    # Try to import Essentia-based analyzer, fallback to simple one
    try:
        from backend.audio_analysis.track_analyzer import TrackAnalyzer
        print("✓ Using Essentia-based analyzer")
    except ImportError:
        print("⚠️ Essentia not available, using librosa-only analyzer")
        from backend.audio_analysis.simple_analyzer import SimpleTrackAnalyzer as TrackAnalyzer
        
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


# Initialize FastAPI
app = FastAPI(title="AI DJ Co-Pilot - Complete Interface")

# Initialize components
mixer = DJMixer()
effects_a = EffectsChain()
effects_b = EffectsChain()
queue_manager = QueueManager()
transition_planner = TransitionPlanner()
advisor = DJAdvisor(mixer, queue_manager, transition_planner)
analyzer = TrackAnalyzer()
auto_dj = AutoDJEngine(mixer, queue_manager, transition_planner)
set_planner = SetPlanner(transition_planner)

# Track library
library = []
library_path = Path("data/cache/library.json")

# Active WebSocket connections
active_connections: List[WebSocket] = []


def load_library():
    """Load track library from cache"""
    if library_path.exists():
        with open(library_path, 'r') as f:
            data = json.load(f)
            library.extend(data.get('tracks', []))
        print(f"📚 Loaded {len(library)} tracks")


def save_library():
    """Save track library to cache"""
    library_path.parent.mkdir(parents=True, exist_ok=True)
    with open(library_path, 'w') as f:
        json.dump({'tracks': library}, f, indent=2)
    print(f"💾 Saved {len(library)} tracks")


# Load library on startup
load_library()

# Start mixer with error handling
try:
    mixer.start()
    print("🎛️ Mixer started successfully")
    print(f"   Sample rate: {mixer.sample_rate} Hz")
    print(f"   Block size: {mixer.blocksize} samples")
except Exception as e:
    print(f"❌ Error starting mixer: {e}")
    print("   Audio playback will not work!")
    print("   Install dependencies: pip3 install --break-system-packages sounddevice soundfile scipy")


@app.on_event("shutdown")
async def shutdown():
    """Clean shutdown"""
    mixer.stop()
    print("🎛️ Mixer stopped")


# Main interface
@app.get("/", response_class=HTMLResponse)
async def main_interface():
    """Complete interface with tabs"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI DJ Co-Pilot</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #1a1a1a;
                color: #fff;
                overflow: hidden;
            }
            
            .container {
                display: grid;
                grid-template-rows: 60px 50px 1fr;
                height: 100vh;
            }
            
            /* Header */
            header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 15px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            header h1 { font-size: 24px; }
            
            .status-badge {
                background: rgba(255,255,255,0.2);
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
            }
            
            /* Tabs */
            .tabs {
                background: #2a2a2a;
                display: flex;
                border-bottom: 2px solid #667eea;
            }
            
            .tab {
                padding: 15px 30px;
                cursor: pointer;
                border: none;
                background: transparent;
                color: #888;
                font-size: 16px;
                font-weight: 600;
                transition: all 0.2s;
            }
            
            .tab:hover {
                color: #fff;
                background: rgba(255,255,255,0.05);
            }
            
            .tab.active {
                color: #fff;
                background: rgba(102,126,234,0.2);
                border-bottom: 3px solid #667eea;
            }
            
            /* Tab content */
            .tab-content {
                display: none;
                padding: 20px;
                overflow-y: auto;
            }
            
            .tab-content.active {
                display: block;
            }
            
            /* Library tab */
            .upload-section {
                background: #2a2a2a;
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                margin-bottom: 20px;
            }
            
            .upload-area {
                border: 3px dashed #667eea;
                border-radius: 12px;
                padding: 60px;
                margin: 20px 0;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .upload-area:hover {
                border-color: #764ba2;
                background: rgba(102,126,234,0.1);
            }
            
            .upload-area.dragging {
                border-color: #764ba2;
                background: rgba(102,126,234,0.2);
                transform: scale(1.02);
            }
            
            input[type="file"] {
                display: none;
            }
            
            button {
                padding: 12px 24px;
                background: #667eea;
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            button:hover {
                background: #5568d3;
                transform: translateY(-2px);
            }
            
            button:disabled {
                background: #555;
                cursor: not-allowed;
                transform: none;
            }
            
            .library-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            
            .track-card {
                background: #2a2a2a;
                border-radius: 8px;
                padding: 15px;
                cursor: pointer;
                transition: all 0.2s;
                border: 2px solid transparent;
                position: relative;
            }
            
            .track-card:hover {
                background: #333;
                transform: translateY(-2px);
                border-color: #667eea;
            }
            
            .track-card.selected {
                border-color: #667eea;
                background: rgba(102,126,234,0.2);
            }
            
            .track-card:hover .delete-btn {
                opacity: 1;
            }
            
            .delete-btn {
                position: absolute;
                top: 10px;
                right: 10px;
                background: #e74c3c;
                border: none;
                border-radius: 50%;
                width: 32px;
                height: 32px;
                color: white;
                font-size: 16px;
                cursor: pointer;
                opacity: 0;
                transition: all 0.2s;
                z-index: 10;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .delete-btn:hover {
                background: #c0392b;
                transform: scale(1.1);
            }
            
            /* Track selection */
            .track-checkbox {
                position: absolute;
                top: 10px;
                left: 10px;
                width: 24px;
                height: 24px;
                cursor: pointer;
                z-index: 10;
            }
            
            .track-card.has-checkbox {
                padding-left: 45px;
            }
            
            /* Build Plan Button */
            .build-plan-section {
                background: #2a2a2a;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
            }
            
            .build-plan-btn {
                padding: 15px 30px;
                font-size: 18px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                cursor: pointer;
            }
            
            .build-plan-btn:disabled {
                background: #555;
                cursor: not-allowed;
            }
            
            /* Preview Modal */
            .preview-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.9);
                z-index: 2000;
                overflow-y: auto;
                padding: 20px;
            }
            
            .preview-modal.active {
                display: flex;
                align-items: flex-start;
                justify-content: center;
            }
            
            .preview-content {
                background: #2a2a2a;
                border-radius: 12px;
                padding: 30px;
                max-width: 1200px;
                width: 100%;
                margin: 20px;
            }
            
            .preview-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }
            
            .preview-header h2 {
                font-size: 28px;
                color: #667eea;
            }
            
            .close-preview {
                background: #555;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                color: white;
                cursor: pointer;
            }
            
            .track-order {
                background: #1a1a1a;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .track-order h3 {
                margin-bottom: 15px;
                color: #667eea;
            }
            
            .track-order-item {
                padding: 10px;
                margin: 8px 0;
                background: #2a2a2a;
                border-radius: 6px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .timeline-section {
                background: #1a1a1a;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                max-height: 400px;
                overflow-y: auto;
            }
            
            .timeline-section h3 {
                margin-bottom: 15px;
                color: #667eea;
                sticky: top;
                background: #1a1a1a;
            }
            
            .timeline-event {
                padding: 12px;
                margin: 8px 0;
                background: #2a2a2a;
                border-radius: 6px;
                border-left: 4px solid #667eea;
            }
            
            .timeline-event.transition {
                border-left-color: #f39c12;
            }
            
            .timeline-event.action {
                border-left-color: #e74c3c;
            }
            
            .timeline-time {
                font-weight: bold;
                color: #667eea;
                margin-right: 10px;
            }
            
            .timeline-icon {
                font-size: 18px;
                margin-right: 8px;
            }
            
            .transitions-summary {
                background: #1a1a1a;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .transitions-summary h3 {
                margin-bottom: 15px;
                color: #667eea;
            }
            
            .transition-item {
                padding: 15px;
                margin: 10px 0;
                background: #2a2a2a;
                border-radius: 6px;
            }
            
            .transition-title {
                font-weight: bold;
                margin-bottom: 10px;
                font-size: 16px;
            }
            
            .transition-details {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                font-size: 14px;
                color: #aaa;
            }
            
            .compatibility-good { color: #2ecc71; }
            .compatibility-ok { color: #f39c12; }
            .compatibility-poor { color: #e74c3c; }
            
            .preview-actions {
                display: flex;
                gap: 15px;
                justify-content: center;
                margin-top: 30px;
            }
            
            .preview-actions button {
                padding: 15px 40px;
                font-size: 18px;
            }
            
            .start-auto-btn {
                background: linear-gradient(135deg, #2ecc71, #27ae60);
            }
            
            /* Enhanced suggestions */
            .suggestion-details {
                background: #1a1a1a;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
                font-size: 14px;
            }
            
            .suggestion-next-actions {
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid #333;
            }
            
            .next-action {
                padding: 8px;
                margin: 5px 0;
                background: rgba(102,126,234,0.1);
                border-radius: 4px;
                font-size: 13px;
            }
            
            .track-title {
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 8px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .track-info {
                font-size: 12px;
                color: #888;
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
            }
            
            .badge {
                background: rgba(102,126,234,0.3);
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 11px;
            }
            
            .progress-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.8);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }
            
            .progress-overlay.active {
                display: flex;
            }
            
            .progress-box {
                background: #2a2a2a;
                border-radius: 12px;
                padding: 30px;
                min-width: 400px;
                text-align: center;
            }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #1a1a1a;
                border-radius: 4px;
                overflow: hidden;
                margin: 20px 0;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                transition: width 0.3s;
            }
            
            .load-buttons {
                position: fixed;
                bottom: 20px;
                right: 20px;
                display: flex;
                gap: 10px;
            }
            
            .load-buttons button {
                padding: 15px 30px;
                font-size: 16px;
            }
            
            /* DJ tab - reuse from dj_interface.py */
            .dj-grid {
                display: grid;
                grid-template-columns: 1fr 450px 1fr;
                gap: 20px;
                height: calc(100vh - 180px);
            }
            
            .deck {
                background: #2a2a2a;
                border-radius: 12px;
                padding: 20px;
            }
            
            .deck-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
            }
            
            .deck-label {
                font-size: 20px;
                font-weight: bold;
            }
            
            .track-name {
                font-size: 14px;
                color: #aaa;
                margin-top: 5px;
            }
            
            .waveform {
                width: 100%;
                height: 80px;
                background: #1a1a1a;
                border-radius: 8px;
                margin: 15px 0;
                position: relative;
            }
            
            .waveform-progress {
                position: absolute;
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                opacity: 0.3;
            }
            
            .position-marker {
                position: absolute;
                width: 2px;
                height: 100%;
                background: #fff;
                box-shadow: 0 0 10px rgba(255,255,255,0.5);
            }
            
            .time-display {
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: #888;
            }
            
            .controls {
                display: flex;
                gap: 10px;
                margin: 15px 0;
            }
            
            .controls button {
                flex: 1;
            }
            
            .center-panel {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            
            .suggestion-card {
                background: #2a2a2a;
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                min-height: 150px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                position: relative;
            }
            
            .suggestion-card.high {
                background: linear-gradient(135deg, #e74c3c, #c0392b);
                animation: pulse 2s infinite;
            }
            
            .suggestion-card.medium {
                background: linear-gradient(135deg, #f39c12, #e67e22);
            }
            
            .suggestion-card.low {
                background: #2a2a2a;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            .suggestion-message {
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 15px;
                line-height: 1.4;
            }
            
            .suggestion-timing {
                font-size: 18px;
                color: #ddd;
                font-weight: 600;
            }
            
            .thinking-indicator {
                display: none;
                margin-top: 10px;
            }
            
            .thinking-indicator.active {
                display: block;
            }
            
            .thinking-dots {
                display: inline-block;
            }
            
            .thinking-dots span {
                animation: blink 1.4s infinite;
                display: inline-block;
                margin: 0 2px;
            }
            
            .thinking-dots span:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .thinking-dots span:nth-child(3) {
                animation-delay: 0.4s;
            }
            
            @keyframes blink {
                0%, 60%, 100% { opacity: 0.3; }
                30% { opacity: 1; }
            }
            
            .crossfader-section {
                background: #2a2a2a;
                border-radius: 12px;
                padding: 20px;
            }
            
            .crossfader-labels {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                font-size: 14px;
                font-weight: 600;
            }
            
            .crossfader-labels .active {
                color: #667eea;
                text-shadow: 0 0 10px rgba(102,126,234,0.5);
            }
            
            .crossfader {
                width: 100%;
                height: 60px;
                -webkit-appearance: none;
                background: linear-gradient(90deg, 
                    rgba(102,126,234,0.3) 0%, 
                    rgba(255,255,255,0.1) 50%, 
                    rgba(118,75,162,0.3) 100%);
                border-radius: 30px;
                border: 2px solid #1a1a1a;
            }
            
            .crossfader::-webkit-slider-thumb {
                -webkit-appearance: none;
                width: 50px;
                height: 56px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                border-radius: 12px;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
                transition: transform 0.1s;
            }
            
            .crossfader::-webkit-slider-thumb:hover {
                transform: scale(1.1);
            }
            
            .cf-levels {
                display: flex;
                justify-content: space-between;
                margin-top: 15px;
                font-size: 12px;
                color: #888;
            }
            
            .cf-level {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .cf-bar {
                width: 80px;
                height: 8px;
                background: #1a1a1a;
                border-radius: 4px;
                overflow: hidden;
            }
            
            .cf-bar-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                transition: width 0.1s;
            }
            
            /* Auto DJ controls */
            .auto-dj-section {
                background: #2a2a2a;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 15px;
            }
            
            .auto-dj-section.active {
                background: linear-gradient(135deg, rgba(102,126,234,0.3), rgba(118,75,162,0.3));
                border: 2px solid #667eea;
            }
            
            .auto-dj-button {
                width: 100%;
                padding: 15px;
                font-size: 16px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                margin-bottom: 10px;
            }
            
            .auto-dj-button.active {
                background: linear-gradient(135deg, #2ecc71, #27ae60);
            }
            
            .auto-dj-button.stop {
                background: linear-gradient(135deg, #e74c3c, #c0392b);
            }
            
            .auto-dj-status {
                background: #1a1a1a;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
                font-size: 14px;
            }
            
            .auto-dj-status .action {
                font-weight: 600;
                color: #667eea;
                margin-bottom: 5px;
            }
            
            .auto-dj-status .details {
                color: #aaa;
            }
            
            .auto-dj-controls {
                display: flex;
                gap: 10px;
                margin-top: 10px;
            }
            
            .auto-dj-controls button {
                flex: 1;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <header>
                <h1>🎧 AI DJ Co-Pilot</h1>
                <div class="status-badge" id="status">Ready</div>
            </header>
            
            <!-- Tabs -->
            <div class="tabs">
                <button class="tab active" data-tab="library">
                    📚 Library
                </button>
                <button class="tab" data-tab="dj" id="dj-tab">
                    🎛️ DJ Mode
                </button>
            </div>
            
            <!-- Tab content -->
            <div id="library-content" class="tab-content active">
                <!-- Upload section -->
                <div class="upload-section">
                    <h2>Upload & Analyze Tracks</h2>
                    <div class="upload-area" id="upload-area">
                        <div style="font-size: 48px; margin-bottom: 20px;">🎵</div>
                        <div style="font-size: 18px; margin-bottom: 10px;">
                            Drag & drop audio files here
                        </div>
                        <div style="color: #888;">
                            MP3, WAV, FLAC, M4A, AAC, OGG, AIFF<br>
                            or click to browse
                        </div>
                    </div>
                    <input type="file" id="file-input" multiple accept="audio/*,.mp3,.wav,.flac,.m4a,.aac,.ogg,.aiff">
                    <button id="analyze-btn" disabled>
                        🔍 Analyze Selected Tracks
                    </button>
                </div>
                
                <!-- Build Set Plan Section -->
                <div class="build-plan-section" id="build-plan-section" style="display: none;">
                    <h3 style="margin-bottom: 15px;">🎯 Build Your Set</h3>
                    <button class="build-plan-btn" id="build-plan-btn" onclick="buildSetPreview()" disabled>
                        Build Set Plan (0 tracks selected)
                    </button>
                </div>
                
                <!-- Library grid -->
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin: 20px 0;">
                        <h3>Your Library (<span id="track-count">0</span> tracks)</h3>
                        <div style="display: flex; gap: 10px;">
                            <button onclick="toggleSelectAll()" id="select-all-btn" style="background: #667eea; padding: 8px 16px;">
                                ☑️ Select All
                            </button>
                            <button onclick="clearLibrary()" style="background: #e74c3c; padding: 8px 16px;">
                                🗑️ Clear All
                            </button>
                        </div>
                    </div>
                    <div class="library-grid" id="library-grid">
                        <!-- Tracks appear here -->
                    </div>
                </div>
                
                <!-- Load buttons -->
                <div class="load-buttons" id="load-buttons" style="display: none;">
                    <button onclick="loadToDeck('a')">Load to Deck A</button>
                    <button onclick="loadToDeck('b')">Load to Deck B</button>
                </div>
            </div>
            
            <div id="dj-content" class="tab-content">
                <div class="dj-grid">
                    <!-- Deck A -->
                    <div class="deck">
                        <div class="deck-header">
                            <div>
                                <div class="deck-label">DECK A</div>
                                <div class="track-name" id="track-a">No track loaded</div>
                            </div>
                        </div>
                        
                        <div class="waveform">
                            <div class="waveform-progress" id="wave-a"></div>
                            <div class="position-marker" id="pos-a"></div>
                        </div>
                        
                        <div class="time-display">
                            <span id="time-a">0:00</span>
                            <span id="remain-a">-0:00</span>
                        </div>
                        
                        <div class="controls">
                            <button onclick="control('play_a')">▶️</button>
                            <button onclick="control('pause_a')">⏸</button>
                            <button onclick="control('stop_a')">⏹</button>
                        </div>
                    </div>
                    
                    <!-- Center panel -->
                    <div class="center-panel">
                        <!-- Auto DJ Section -->
                        <div class="auto-dj-section" id="auto-dj-section">
                            <h3 style="margin-bottom: 15px;">🤖 Auto DJ</h3>
                            <button class="auto-dj-button" id="auto-dj-toggle" onclick="toggleAutoDJ()">
                                Enable Auto DJ
                            </button>
                            <div class="auto-dj-controls" id="auto-dj-controls" style="display: none;">
                                <button onclick="pauseAutoDJ()">⏸ Pause</button>
                                <button onclick="resumeAutoDJ()">▶️ Resume</button>
                                <button class="auto-dj-button stop" onclick="stopAutoDJ()">⏹ Stop</button>
                            </div>
                            <div class="auto-dj-status" id="auto-dj-status" style="display: none;">
                                <div class="action" id="auto-action">Idle</div>
                                <div class="details" id="auto-details"></div>
                                <div style="margin-top: 10px; font-size: 12px; color: #888;">
                                    Track <span id="auto-track-progress">0/0</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Suggestions -->
                        <div class="suggestion-card low" id="suggestion">
                            <div class="suggestion-message" id="sug-msg">Load tracks to start</div>
                            <div class="suggestion-timing" id="sug-time"></div>
                            <div class="thinking-indicator" id="thinking">
                                <div class="thinking-dots">
                                    <span>●</span><span>●</span><span>●</span>
                                </div>
                                <div style="margin-top: 5px; font-size: 14px;">AI thinking...</div>
                            </div>
                        </div>
                        
                        <div class="crossfader-section">
                            <h3 style="margin-bottom: 15px;">Crossfader</h3>
                            <div class="crossfader-labels">
                                <span id="cf-label-a" class="active">DECK A</span>
                                <span id="cf-label-center">CENTER</span>
                                <span id="cf-label-b">DECK B</span>
                            </div>
                            <input type="range" class="crossfader" id="crossfader"
                                   min="-1" max="1" step="0.01" value="-1"
                                   oninput="setCrossfader(this.value)">
                            <div class="cf-levels">
                                <div class="cf-level">
                                    <span>A:</span>
                                    <div class="cf-bar">
                                        <div class="cf-bar-fill" id="cf-level-a" style="width: 100%"></div>
                                    </div>
                                    <span id="cf-percent-a">100%</span>
                                </div>
                                <div class="cf-level">
                                    <span>B:</span>
                                    <div class="cf-bar">
                                        <div class="cf-bar-fill" id="cf-level-b" style="width: 0%"></div>
                                    </div>
                                    <span id="cf-percent-b">0%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Deck B -->
                    <div class="deck">
                        <div class="deck-header">
                            <div>
                                <div class="deck-label">DECK B</div>
                                <div class="track-name" id="track-b">No track loaded</div>
                            </div>
                        </div>
                        
                        <div class="waveform">
                            <div class="waveform-progress" id="wave-b"></div>
                            <div class="position-marker" id="pos-b"></div>
                        </div>
                        
                        <div class="time-display">
                            <span id="time-b">0:00</span>
                            <span id="remain-b">-0:00</span>
                        </div>
                        
                        <div class="controls">
                            <button onclick="control('play_b')">▶️</button>
                            <button onclick="control('pause_b')">⏸</button>
                            <button onclick="control('stop_b')">⏹</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Progress overlay -->
        <div class="progress-overlay" id="progress-overlay">
            <div class="progress-box">
                <h3 id="progress-title">Analyzing tracks...</h3>
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill"></div>
                </div>
                <div id="progress-text">0 / 0 tracks</div>
            </div>
        </div>
        
        <!-- Preview Modal -->
        <div class="preview-modal" id="preview-modal">
            <div class="preview-content">
                <div class="preview-header">
                    <h2>🎯 Set Plan Preview</h2>
                    <button class="close-preview" onclick="closePreview()">✕ Close</button>
                </div>
                
                <!-- Set Summary -->
                <div style="background: #1a1a1a; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #667eea;" id="preview-duration">
                        15m 32s
                    </div>
                    <div style="color: #aaa; margin-top: 5px;" id="preview-tracks">
                        3 tracks • 2 transitions
                    </div>
                </div>
                
                <!-- Track Order -->
                <div class="track-order">
                    <h3>📋 Track Order</h3>
                    <div id="preview-track-list">
                        <!-- Track list appears here -->
                    </div>
                </div>
                
                <!-- Timeline -->
                <div class="timeline-section">
                    <h3>⏱️ Timeline</h3>
                    <div id="preview-timeline">
                        <!-- Timeline events appear here -->
                    </div>
                </div>
                
                <!-- Transitions Summary -->
                <div class="transitions-summary">
                    <h3>🔀 Transitions</h3>
                    <div id="preview-transitions">
                        <!-- Transition details appear here -->
                    </div>
                </div>
                
                <!-- Actions -->
                <div class="preview-actions">
                    <button onclick="closePreview()" class="secondary">
                        ← Back to Selection
                    </button>
                    <button onclick="startAutoDJFromPreview()" class="start-auto-btn">
                        🚀 Start Auto DJ
                    </button>
                </div>
            </div>
        </div>
        
        <script>
            let selectedFiles = [];
            let selectedTrack = null;
            let selectedTracks = [];  // For multi-select
            let currentPreviewPlan = null;
            let ws = null;
            
            // Drag & drop
            const uploadArea = document.getElementById('upload-area');
            const fileInput = document.getElementById('file-input');
            const analyzeBtn = document.getElementById('analyze-btn');
            
            // Click upload area to open file picker
            uploadArea.addEventListener('click', () => {
                fileInput.click();
            });
            
            // Analyze button
            analyzeBtn.addEventListener('click', () => {
                analyzeSelected();
            });
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragging');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragging');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragging');
                handleFiles(e.dataTransfer.files);
            });
            
            fileInput.addEventListener('change', (e) => {
                handleFiles(e.target.files);
            });
            
            function handleFiles(files) {
                selectedFiles = Array.from(files);
                const count = selectedFiles.length;
                const btn = document.getElementById('analyze-btn');
                
                btn.disabled = count === 0;
                
                if (count === 0) {
                    btn.textContent = '🔍 Analyze Selected Tracks';
                } else if (count === 1) {
                    btn.textContent = `🔍 Analyze 1 Track`;
                } else {
                    btn.textContent = `🔍 Analyze ${count} Tracks`;
                }
            }
            
            async function analyzeSelected() {
                if (selectedFiles.length === 0) return;
                
                const overlay = document.getElementById('progress-overlay');
                overlay.classList.add('active');
                
                // Show thinking indicator
                const thinking = document.getElementById('thinking');
                if (thinking) thinking.classList.add('active');
                
                let successCount = 0;
                let errorCount = 0;
                
                for (let i = 0; i < selectedFiles.length; i++) {
                    const file = selectedFiles[i];
                    
                    document.getElementById('progress-title').textContent = 
                        `🎵 Analyzing: ${file.name}`;
                    document.getElementById('progress-text').textContent = 
                        `${i + 1} / ${selectedFiles.length} tracks • Detecting BPM, key, energy...`;
                    document.getElementById('progress-fill').style.width = 
                        `${((i + 1) / selectedFiles.length) * 100}%`;
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    try {
                        console.log(`Uploading: ${file.name} (${file.size} bytes, ${file.type})`);
                        
                        const response = await fetch('/upload', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        console.log('Upload result:', result);
                        
                        if (result.status === 'ok') {
                            successCount++;
                        } else {
                            errorCount++;
                            console.error('Upload failed:', result.message);
                            alert(`Error with ${file.name}: ${result.message}`);
                        }
                    } catch (error) {
                        errorCount++;
                        console.error('Error uploading:', error);
                        alert(`Error analyzing ${file.name}: ${error.message}`);
                    }
                }
                
                overlay.classList.remove('active');
                if (thinking) thinking.classList.remove('active');
                
                // Show summary
                if (successCount > 0) {
                    alert(`✅ Analyzed ${successCount} track(s) successfully!${errorCount > 0 ? `\n⚠️ ${errorCount} failed` : ''}`);
                }
                
                selectedFiles = [];
                fileInput.value = '';
                document.getElementById('analyze-btn').disabled = true;
                
                loadLibrary();
            }
            
            async function loadLibrary() {
                const response = await fetch('/library');
                const tracks = await response.json();
                
                // Save to session storage for access
                sessionStorage.setItem('library', JSON.stringify(tracks));
                
                document.getElementById('track-count').textContent = tracks.length;
                
                const grid = document.getElementById('library-grid');
                grid.innerHTML = '';
                
                tracks.forEach((track, index) => {
                    const card = document.createElement('div');
                    card.className = 'track-card has-checkbox';
                    card.dataset.index = index;
                    card.dataset.filepath = track.file_path;
                    
                    card.onclick = (e) => {
                        if (e.target.type !== 'checkbox' && !e.target.classList.contains('delete-btn')) {
                            selectTrack(track, card);
                        }
                    };
                    
                    // Safe access to track properties
                    const title = track.title || track.filename || 'Unknown Track';
                    const bpm = track.bpm ? track.bpm.toFixed(0) : '?';
                    const key = track.key || '?';
                    const duration = track.duration ? (track.duration / 60).toFixed(1) : '?';
                    const energy = track.energy !== undefined ? (track.energy * 10).toFixed(1) : '?';
                    
                    // Create elements without inline onclick to avoid escaping issues
                    card.innerHTML = `
                        <input type="checkbox" class="track-checkbox" 
                               id="track-check-${index}">
                        <button class="delete-btn">×</button>
                        <div class="track-title">${title}</div>
                        <div class="track-info">
                            <span class="badge">${bpm} BPM</span>
                            <span class="badge">${key}</span>
                            <span class="badge">${duration}m</span>
                            <span class="badge">Energy: ${energy}</span>
                        </div>
                    `;
                    
                    // Attach event listeners properly
                    const checkbox = card.querySelector('.track-checkbox');
                    checkbox.addEventListener('change', (e) => {
                        e.stopPropagation();
                        toggleTrackSelection(index, e);
                    });
                    
                    const deleteBtn = card.querySelector('.delete-btn');
                    deleteBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        deleteTrack(e, track.file_path);
                    });
                    
                    grid.appendChild(card);
                });
                
                // Show build plan section if tracks exist
                if (tracks.length > 0) {
                    document.getElementById('build-plan-section').style.display = 'block';
                }
            }
            
            function selectTrack(track, element) {
                // Deselect previous
                document.querySelectorAll('.track-card').forEach(el => {
                    el.classList.remove('selected');
                });
                
                // Select this one
                element.classList.add('selected');
                selectedTrack = track;
                
                // Show load buttons
                document.getElementById('load-buttons').style.display = 'flex';
            }
            
            async function deleteTrack(event, filePath) {
                // Stop propagation so card doesn't get selected
                event.stopPropagation();
                
                if (!confirm('Delete this track?')) {
                    return;
                }
                
                try {
                    const response = await fetch('/library/delete', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({file_path: filePath})
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'ok') {
                        // Reload library
                        loadLibrary();
                        
                        // Clear selection if deleted track was selected
                        if (selectedTrack && selectedTrack.file_path === filePath) {
                            selectedTrack = null;
                            document.getElementById('load-buttons').style.display = 'none';
                        }
                    } else {
                        alert('Error deleting track: ' + result.message);
                    }
                } catch (error) {
                    alert('Error deleting track: ' + error.message);
                }
            }
            
            async function clearLibrary() {
                const count = document.getElementById('track-count').textContent;
                
                if (!confirm(`Delete all ${count} tracks from library?`)) {
                    return;
                }
                
                try {
                    const response = await fetch('/library/clear', {method: 'POST'});
                    const result = await response.json();
                    
                    if (result.status === 'ok') {
                        loadLibrary();
                        selectedTrack = null;
                        selectedTracks = [];
                        document.getElementById('load-buttons').style.display = 'none';
                        updateBuildPlanButton();
                    } else {
                        alert('Error clearing library: ' + result.message);
                    }
                } catch (error) {
                    alert('Error clearing library: ' + error.message);
                }
            }
            
            function toggleTrackSelection(index, event) {
                const checkbox = document.getElementById(`track-check-${index}`);
                
                if (checkbox.checked) {
                    if (!selectedTracks.includes(index)) {
                        selectedTracks.push(index);
                    }
                } else {
                    selectedTracks = selectedTracks.filter(i => i !== index);
                }
                
                updateBuildPlanButton();
            }
            
            function toggleSelectAll() {
                const libraryData = JSON.parse(sessionStorage.getItem('library') || '[]');
                const allChecked = selectedTracks.length === libraryData.length;
                
                if (allChecked) {
                    // Unselect all
                    selectedTracks = [];
                    document.querySelectorAll('.track-checkbox').forEach(cb => cb.checked = false);
                    document.getElementById('select-all-btn').textContent = '☑️ Select All';
                } else {
                    // Select all
                    selectedTracks = libraryData.map((_, i) => i);
                    document.querySelectorAll('.track-checkbox').forEach(cb => cb.checked = true);
                    document.getElementById('select-all-btn').textContent = '☐ Deselect All';
                }
                
                updateBuildPlanButton();
            }
            
            function updateBuildPlanButton() {
                const btn = document.getElementById('build-plan-btn');
                const count = selectedTracks.length;
                
                if (count === 0) {
                    btn.disabled = true;
                    btn.textContent = 'Build Set Plan (0 tracks selected)';
                } else if (count === 1) {
                    btn.disabled = true;
                    btn.textContent = 'Build Set Plan (need at least 2 tracks)';
                } else {
                    btn.disabled = false;
                    btn.textContent = `Build Set Plan (${count} tracks selected)`;
                }
            }
            
            async function buildSetPreview() {
                if (selectedTracks.length < 2) return;
                
                // Show loading
                document.getElementById('progress-overlay').classList.add('active');
                document.getElementById('progress-title').textContent = 'Building set plan...';
                document.getElementById('progress-text').textContent = 'Analyzing transitions...';
                document.getElementById('progress-fill').style.width = '50%';
                
                try {
                    const response = await fetch('/auto_dj/build_plan', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({track_indices: selectedTracks})
                    });
                    
                    const plan = await response.json();
                    
                    if (plan.status === 'ok') {
                        currentPreviewPlan = plan;
                        showPreviewModal(plan);
                    } else {
                        alert('Error building plan: ' + plan.message);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                } finally {
                    document.getElementById('progress-overlay').classList.remove('active');
                }
            }
            
            function showPreviewModal(plan) {
                const visual = plan.visual;
                
                // Set summary
                document.getElementById('preview-duration').textContent = visual.total_duration_str;
                document.getElementById('preview-tracks').textContent = 
                    `${visual.track_list.length} tracks • ${visual.transitions.length} transitions`;
                
                // Track list
                const trackList = document.getElementById('preview-track-list');
                trackList.innerHTML = '';
                visual.track_list.forEach((track, i) => {
                    const item = document.createElement('div');
                    item.className = 'track-order-item';
                    item.innerHTML = `
                        <div>
                            <strong>${i + 1}.</strong> ${track.name}
                        </div>
                        <div style="color: #888; font-size: 14px;">
                            ${track.bpm?.toFixed(0)} BPM • ${track.key} • ${(track.duration / 60).toFixed(1)}m
                        </div>
                    `;
                    trackList.appendChild(item);
                });
                
                // Timeline
                const timeline = document.getElementById('preview-timeline');
                timeline.innerHTML = '';
                visual.timeline.forEach(event => {
                    const item = document.createElement('div');
                    item.className = 'timeline-event';
                    item.innerHTML = `
                        <span class="timeline-time">${event.time_str}</span>
                        <span class="timeline-icon">${event.icon}</span>
                        <span>${event.description}</span>
                    `;
                    timeline.appendChild(item);
                });
                
                // Transitions
                const transitions = document.getElementById('preview-transitions');
                transitions.innerHTML = '';
                visual.transitions.forEach(trans => {
                    const compatClass = trans.compatibility > 0.8 ? 'compatibility-good' :
                                       trans.compatibility > 0.6 ? 'compatibility-ok' : 'compatibility-poor';
                    
                    const item = document.createElement('div');
                    item.className = 'transition-item';
                    item.innerHTML = `
                        <div class="transition-title">${trans.from} → ${trans.to}</div>
                        <div class="transition-details">
                            <div>Duration: ${trans.duration}s crossfade</div>
                            <div class="${compatClass}">Compatibility: ${(trans.compatibility * 100).toFixed(0)}%</div>
                            <div>BPM diff: ${trans.bpm_diff.toFixed(1)} BPM</div>
                            <div>${trans.energy_flow}</div>
                        </div>
                    `;
                    transitions.appendChild(item);
                });
                
                // Show modal
                document.getElementById('preview-modal').classList.add('active');
            }
            
            function closePreview() {
                document.getElementById('preview-modal').classList.remove('active');
            }
            
            async function startAutoDJFromPreview() {
                closePreview();
                
                // Switch to DJ tab
                switchTab('dj');
                
                // Start Auto DJ
                try {
                    const response = await fetch('/auto_dj/start', {method: 'POST'});
                    const result = await response.json();
                    
                    if (result.status !== 'ok') {
                        alert('Error starting Auto DJ: ' + result.message);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }
            
            async function loadToDeck(deck) {
                if (!selectedTrack) return;
                
                await fetch(`/load/${deck}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file_path: selectedTrack.file_path})
                });
                
                // Switch to DJ tab
                switchTab('dj');
            }
            
            function switchTab(tab) {
                // Update tab buttons
                document.querySelectorAll('.tab').forEach(t => {
                    t.classList.remove('active');
                });
                document.querySelector(`.tab[data-tab="${tab}"]`).classList.add('active');
                
                // Update content
                document.querySelectorAll('.tab-content').forEach(c => {
                    c.classList.remove('active');
                });
                document.getElementById(`${tab}-content`).classList.add('active');
                
                // Connect WebSocket when switching to DJ mode
                if (tab === 'dj' && !ws) {
                    connectWebSocket();
                }
            }
            
            function connectWebSocket() {
                ws = new WebSocket(`ws://${window.location.host}/ws`);
                
                ws.onopen = () => {
                    document.getElementById('status').textContent = '🟢 Live';
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    updateDJUI(data);
                };
                
                ws.onclose = () => {
                    document.getElementById('status').textContent = '🔴 Disconnected';
                    setTimeout(connectWebSocket, 1000);
                };
            }
            
            function updateDJUI(data) {
                const mixer = data.mixer;
                const suggestion = data.suggestion;
                const autoDJ = data.auto_dj;
                
                // Update decks
                updateDeck('a', mixer.deck_a);
                updateDeck('b', mixer.deck_b);
                
                // Update crossfader display from backend
                if (mixer.crossfader !== undefined) {
                    updateCrossfaderUI(mixer.crossfader);
                }
                
                // Update Auto DJ status
                updateAutoDJUI(autoDJ);
                
                // Update suggestion (make it prominent!)
                const sugCard = document.getElementById('suggestion');
                const sugMsg = document.getElementById('sug-msg');
                const sugTime = document.getElementById('sug-time');
                
                // If Auto DJ is running, show enhanced automation status
                if (autoDJ && autoDJ.running) {
                    sugMsg.textContent = '🤖 ' + autoDJ.action_details;
                    sugTime.textContent = autoDJ.paused ? '⏸ PAUSED' : '🟢 AUTO';
                    sugCard.className = 'suggestion-card low';
                    
                    // Show next actions if available
                    showEnhancedSuggestions(autoDJ);
                } else {
                    sugMsg.textContent = suggestion.message || '🎧 Ready to DJ';
                    sugTime.textContent = suggestion.timing || '';
                    
                    // Update card style based on urgency
                    sugCard.className = `suggestion-card ${suggestion.urgency || 'low'}`;
                    
                    // Flash animation on urgent messages
                    if (suggestion.urgency === 'high') {
                        sugCard.style.boxShadow = '0 0 30px rgba(231, 76, 60, 0.8)';
                    } else if (suggestion.urgency === 'medium') {
                        sugCard.style.boxShadow = '0 0 20px rgba(243, 156, 18, 0.6)';
                    } else {
                        sugCard.style.boxShadow = 'none';
                    }
                    
                    // Clear enhanced suggestions
                    clearEnhancedSuggestions();
                }
            }
            
            function showEnhancedSuggestions(autoDJ) {
                // Check if we already have a details section
                let detailsSection = document.getElementById('suggestion-details');
                
                if (!detailsSection) {
                    detailsSection = document.createElement('div');
                    detailsSection.id = 'suggestion-details';
                    detailsSection.className = 'suggestion-details';
                    document.getElementById('suggestion').appendChild(detailsSection);
                }
                
                // Show track progress and next actions
                const trackInfo = `Track ${autoDJ.current_track_index + 1}/${autoDJ.total_tracks}`;
                
                // Smart suggestions based on current action
                let tips = [];
                if (autoDJ.current_action.includes('loading')) {
                    tips.push('💡 Tip: Preview the incoming track in your headphones');
                } else if (autoDJ.current_action.includes('transitioning')) {
                    tips.push('🎚️ You can take over the crossfader anytime');
                    tips.push('💡 Try adding your own creative touch');
                } else if (autoDJ.current_action.includes('monitoring')) {
                    tips.push('🎧 Perfect time to plan your next move');
                }
                
                detailsSection.innerHTML = `
                    <div style="color: #888; font-size: 13px; margin-bottom: 5px;">
                        ${trackInfo}
                    </div>
                    ${tips.length > 0 ? `
                        <div class="suggestion-next-actions">
                            ${tips.map(tip => `<div class="next-action">${tip}</div>`).join('')}
                        </div>
                    ` : ''}
                `;
            }
            
            function clearEnhancedSuggestions() {
                const detailsSection = document.getElementById('suggestion-details');
                if (detailsSection) {
                    detailsSection.remove();
                }
            }
            
            function updateAutoDJUI(autoDJ) {
                if (!autoDJ) return;
                
                const section = document.getElementById('auto-dj-section');
                const toggle = document.getElementById('auto-dj-toggle');
                const controls = document.getElementById('auto-dj-controls');
                const status = document.getElementById('auto-dj-status');
                const action = document.getElementById('auto-action');
                const details = document.getElementById('auto-details');
                const progress = document.getElementById('auto-track-progress');
                
                if (autoDJ.running) {
                    section.classList.add('active');
                    toggle.style.display = 'none';
                    controls.style.display = 'flex';
                    status.style.display = 'block';
                    
                    action.textContent = autoDJ.current_action.replace(/_/g, ' ').toUpperCase();
                    details.textContent = autoDJ.action_details;
                    progress.textContent = `${autoDJ.current_track_index + 1}/${autoDJ.total_tracks}`;
                } else {
                    section.classList.remove('active');
                    toggle.style.display = 'block';
                    controls.style.display = 'none';
                    status.style.display = 'none';
                    
                    if (autoDJ.enabled) {
                        toggle.textContent = '🤖 Auto DJ Ready';
                        toggle.className = 'auto-dj-button active';
                    } else {
                        toggle.textContent = 'Enable Auto DJ';
                        toggle.className = 'auto-dj-button';
                    }
                }
            }
            
            async function toggleAutoDJ() {
                const response = await fetch('/auto_dj/build_plan', {method: 'POST'});
                const plan = await response.json();
                
                if (plan.status === 'ok') {
                    alert(`Set Plan Built!\n${plan.tracks} tracks, ${Math.floor(plan.total_duration / 60)} minutes`);
                    
                    const startResponse = await fetch('/auto_dj/start', {method: 'POST'});
                    const result = await startResponse.json();
                    
                    if (result.status === 'ok') {
                        console.log('Auto DJ started!');
                    }
                } else {
                    alert('Error: ' + plan.message);
                }
            }
            
            async function pauseAutoDJ() {
                await fetch('/auto_dj/pause', {method: 'POST'});
            }
            
            async function resumeAutoDJ() {
                await fetch('/auto_dj/resume', {method: 'POST'});
            }
            
            async function stopAutoDJ() {
                if (confirm('Stop Auto DJ?')) {
                    await fetch('/auto_dj/stop', {method: 'POST'});
                }
            }
            
            function updateDeck(id, deck) {
                // Safe track name
                const trackName = deck.track || 'No track loaded';
                document.getElementById(`track-${id}`).textContent = trackName;
                
                // Progress (safe defaults)
                const progress = (deck.progress || 0) * 100;
                document.getElementById(`wave-${id}`).style.width = `${progress}%`;
                document.getElementById(`pos-${id}`).style.left = `${progress}%`;
                
                // Time displays (safe defaults)
                const position = deck.position || 0;
                const remaining = deck.time_remaining || 0;
                document.getElementById(`time-${id}`).textContent = formatTime(position);
                document.getElementById(`remain-${id}`).textContent = '-' + formatTime(remaining);
            }
            
            function formatTime(seconds) {
                const mins = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${mins}:${secs.toString().padStart(2, '0')}`;
            }
            
            function control(action) {
                fetch(`/control/${action}`, {method: 'POST'});
            }
            
            function setCrossfader(value) {
                const val = parseFloat(value);
                
                // Send to backend
                fetch('/control/crossfader', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({value: val})
                });
                
                // Immediate visual feedback (don't wait for websocket)
                updateCrossfaderUI(val);
            }
            
            function updateCrossfaderUI(cfValue) {
                // Calculate levels (same as backend)
                const cf_pos = (cfValue + 1) / 2;  // 0 to 1
                const a_level = Math.cos(cf_pos * Math.PI / 2);
                const b_level = Math.sin(cf_pos * Math.PI / 2);
                
                // Update bars
                document.getElementById('cf-level-a').style.width = `${a_level * 100}%`;
                document.getElementById('cf-level-b').style.width = `${b_level * 100}%`;
                
                // Update percentages
                document.getElementById('cf-percent-a').textContent = `${Math.round(a_level * 100)}%`;
                document.getElementById('cf-percent-b').textContent = `${Math.round(b_level * 100)}%`;
                
                // Update labels
                const labelA = document.getElementById('cf-label-a');
                const labelCenter = document.getElementById('cf-label-center');
                const labelB = document.getElementById('cf-label-b');
                
                labelA.classList.remove('active');
                labelCenter.classList.remove('active');
                labelB.classList.remove('active');
                
                if (cfValue < -0.3) {
                    labelA.classList.add('active');
                } else if (cfValue > 0.3) {
                    labelB.classList.add('active');
                } else {
                    labelCenter.classList.add('active');
                }
            }
            
            // Attach tab event listeners
            document.querySelectorAll('.tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    switchTab(tab.dataset.tab);
                });
            });
            
            // Load library on start
            loadLibrary();
            
            // Initialize crossfader display
            updateCrossfaderUI(-1);  // Start at full A
        </script>
    </body>
    </html>
    """)


# Upload endpoint
@app.post("/upload")
async def upload_track(file: UploadFile = File(...)):
    """Upload and analyze a track"""
    
    # Validate file type
    allowed_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.aiff', '.aif'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        return {
            "status": "error",
            "message": f"Unsupported format: {file_ext}. Supported: {', '.join(allowed_extensions)}"
        }
    
    # Save file
    upload_dir = Path("data/tracks/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    with open(file_path, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    
    print(f"📥 Uploaded: {file.filename} ({file_ext})")
    
    # Analyze track
    try:
        result = analyzer.analyze(str(file_path))
        
        # Add to library
        library.append(result)
        save_library()
        
        print(f"✅ Analyzed: {file.filename} - {result['bpm']:.0f} BPM, {result['key']}")
        
        return {"status": "ok", "track": result}
        
    except Exception as e:
        print(f"❌ Error analyzing {file.filename}: {e}")
        # Clean up failed file
        try:
            file_path.unlink()
        except:
            pass
        return {"status": "error", "message": str(e)}


# Get library
@app.get("/library")
async def get_library():
    """Get track library"""
    return library


@app.post("/library/delete")
async def delete_track(data: dict):
    """Delete a track from library"""
    file_path = data.get('file_path')
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path required")
    
    # Find and remove from library
    global library
    original_length = len(library)
    library = [t for t in library if t.get('file_path') != file_path]
    
    if len(library) == original_length:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Save updated library
    save_library()
    
    # Optionally delete the file
    try:
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            file_path_obj.unlink()
            print(f"🗑️ Deleted file: {file_path_obj.name}")
    except Exception as e:
        print(f"⚠️ Could not delete file: {e}")
    
    print(f"✓ Removed from library: {file_path}")
    
    return {
        'status': 'ok',
        'message': 'Track deleted',
        'remaining_tracks': len(library)
    }


@app.post("/library/clear")
async def clear_library():
    """Clear entire library"""
    global library
    
    count = len(library)
    
    # Delete all files
    for track in library:
        try:
            file_path = Path(track.get('file_path'))
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"⚠️ Could not delete {file_path}: {e}")
    
    # Clear library
    library = []
    save_library()
    
    print(f"🗑️ Cleared library ({count} tracks deleted)")
    
    return {
        'status': 'ok',
        'message': f'{count} tracks deleted'
    }


# WebSocket for DJ mode
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for live status updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            status = {
                'mixer': mixer.get_status(),
                'suggestion': advisor.get_suggestion(),
                'queue': queue_manager.get_queue_info(),
                'auto_dj': auto_dj.get_status()
            }
            
            await websocket.send_json(status)
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)


# Control endpoints
@app.post("/control/{action}")
async def control(action: str):
    """Control mixer"""
    
    if action == 'play_a':
        mixer.deck_a.play()
    elif action == 'pause_a':
        mixer.deck_a.pause()
    elif action == 'stop_a':
        mixer.deck_a.stop()
    elif action == 'play_b':
        mixer.deck_b.play()
    elif action == 'pause_b':
        mixer.deck_b.pause()
    elif action == 'stop_b':
        mixer.deck_b.stop()
    
    return {'status': 'ok'}


@app.post("/control/crossfader")
async def set_crossfader(data: dict):
    """Set crossfader position"""
    mixer.set_crossfader(data['value'])
    return {'status': 'ok'}


@app.post("/load/{deck}")
async def load_track(deck: str, data: dict):
    """Load track into deck"""
    
    file_path = data.get('file_path')
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path required")
    
    target_deck = mixer.deck_a if deck == 'a' else mixer.deck_b
    
    if target_deck.load(file_path):
        return {'status': 'ok'}
    else:
        raise HTTPException(status_code=500, detail="Failed to load track")


@app.get("/audio/status")
async def audio_status():
    """Check if audio system is working"""
    return {
        'mixer_running': mixer.is_running,
        'sample_rate': mixer.sample_rate,
        'deck_a_loaded': mixer.deck_a.audio is not None,
        'deck_b_loaded': mixer.deck_b.audio is not None,
        'deck_a_playing': mixer.deck_a.is_playing,
        'deck_b_playing': mixer.deck_b.is_playing,
        'crossfader': mixer.crossfader,
        'crossfader_a_level': mixer._get_a_level() if mixer.is_running else 0,
        'crossfader_b_level': mixer._get_b_level() if mixer.is_running else 0
    }


# Auto DJ endpoints
@app.post("/auto_dj/build_plan")
async def build_auto_dj_plan(data: dict):
    """Build set plan from selected tracks"""
    track_indices = data.get('track_indices', [])
    
    if not track_indices:
        # Use all tracks if none selected
        selected_tracks = library
    else:
        # Get selected tracks
        selected_tracks = [library[i] for i in track_indices if i < len(library)]
    
    if not selected_tracks:
        raise HTTPException(status_code=400, detail="No tracks selected")
    
    # Build automation plan
    auto_plan = auto_dj.build_set_plan(selected_tracks)
    
    # Build visual roadmap
    visual_plan = set_planner.build_visual_plan(selected_tracks)
    
    return {
        **auto_plan,
        'visual': visual_plan
    }


@app.post("/auto_dj/start")
async def start_auto_dj():
    """Start Auto DJ mode"""
    result = auto_dj.start()
    return result


@app.post("/auto_dj/stop")
async def stop_auto_dj():
    """Stop Auto DJ mode"""
    result = auto_dj.stop()
    return result


@app.post("/auto_dj/pause")
async def pause_auto_dj():
    """Pause Auto DJ (human override)"""
    auto_dj.pause()
    return {'status': 'ok', 'message': 'Auto DJ paused'}


@app.post("/auto_dj/resume")
async def resume_auto_dj():
    """Resume Auto DJ after override"""
    auto_dj.resume()
    return {'status': 'ok', 'message': 'Auto DJ resumed'}


@app.get("/auto_dj/status")
async def get_auto_dj_status():
    """Get Auto DJ status"""
    return auto_dj.get_status()


if __name__ == "__main__":
    import uvicorn
    
    print("🎧 AI DJ Co-Pilot - Complete Interface")
    print("=" * 50)
    print("📚 Library Management + 🎛️ Live DJ Mode")
    print()
    print("Starting server on http://localhost:8000")
    print()
    print("Features:")
    print("  ✓ Upload MP3 files")
    print("  ✓ Automatic analysis (BPM, key, energy)")
    print("  ✓ Browse library")
    print("  ✓ Load tracks into decks")
    print("  ✓ Live DJ interface with suggestions")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
