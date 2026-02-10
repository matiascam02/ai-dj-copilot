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
    from backend.audio_analysis.track_analyzer import TrackAnalyzer
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
                <button class="tab active" onclick="switchTab('library')">
                    📚 Library
                </button>
                <button class="tab" onclick="switchTab('dj')" id="dj-tab">
                    🎛️ DJ Mode
                </button>
            </div>
            
            <!-- Tab content -->
            <div id="library-content" class="tab-content active">
                <!-- Upload section -->
                <div class="upload-section">
                    <h2>Upload & Analyze Tracks</h2>
                    <div class="upload-area" id="upload-area"
                         onclick="document.getElementById('file-input').click()">
                        <div style="font-size: 48px; margin-bottom: 20px;">🎵</div>
                        <div style="font-size: 18px; margin-bottom: 10px;">
                            Drag & drop MP3 files here
                        </div>
                        <div style="color: #888;">
                            or click to browse
                        </div>
                    </div>
                    <input type="file" id="file-input" multiple accept="audio/mp3,audio/mpeg">
                    <button onclick="analyzeSelected()" id="analyze-btn" disabled>
                        🔍 Analyze Selected Tracks
                    </button>
                </div>
                
                <!-- Library grid -->
                <div>
                    <h3 style="margin: 20px 0;">Your Library (<span id="track-count">0</span> tracks)</h3>
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
        
        <script>
            let selectedFiles = [];
            let selectedTrack = null;
            let ws = null;
            
            // Drag & drop
            const uploadArea = document.getElementById('upload-area');
            const fileInput = document.getElementById('file-input');
            
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
                document.getElementById('analyze-btn').disabled = selectedFiles.length === 0;
                document.getElementById('analyze-btn').textContent = 
                    `🔍 Analyze ${selectedFiles.length} Track(s)`;
            }
            
            async function analyzeSelected() {
                if (selectedFiles.length === 0) return;
                
                const overlay = document.getElementById('progress-overlay');
                overlay.classList.add('active');
                
                // Show thinking indicator
                const thinking = document.getElementById('thinking');
                if (thinking) thinking.classList.add('active');
                
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
                        await fetch('/upload', {
                            method: 'POST',
                            body: formData
                        });
                    } catch (error) {
                        console.error('Error uploading:', error);
                        alert(`Error analyzing ${file.name}: ${error.message}`);
                    }
                }
                
                overlay.classList.remove('active');
                if (thinking) thinking.classList.remove('active');
                
                selectedFiles = [];
                fileInput.value = '';
                document.getElementById('analyze-btn').disabled = true;
                
                loadLibrary();
            }
            
            async function loadLibrary() {
                const response = await fetch('/library');
                const tracks = await response.json();
                
                document.getElementById('track-count').textContent = tracks.length;
                
                const grid = document.getElementById('library-grid');
                grid.innerHTML = '';
                
                tracks.forEach(track => {
                    const card = document.createElement('div');
                    card.className = 'track-card';
                    card.onclick = () => selectTrack(track, card);
                    
                    // Safe access to track properties
                    const title = track.title || track.filename || 'Unknown Track';
                    const bpm = track.bpm ? track.bpm.toFixed(0) : '?';
                    const key = track.key || '?';
                    const duration = track.duration ? (track.duration / 60).toFixed(1) : '?';
                    const energy = track.energy !== undefined ? (track.energy * 10).toFixed(1) : '?';
                    
                    card.innerHTML = `
                        <div class="track-title">${title}</div>
                        <div class="track-info">
                            <span class="badge">${bpm} BPM</span>
                            <span class="badge">${key}</span>
                            <span class="badge">${duration}m</span>
                            <span class="badge">Energy: ${energy}</span>
                        </div>
                    `;
                    
                    grid.appendChild(card);
                });
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
                event?.target?.classList?.add('active') || 
                    document.querySelector(`button[onclick="switchTab('${tab}')"]`).classList.add('active');
                
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
                
                // Update decks
                updateDeck('a', mixer.deck_a);
                updateDeck('b', mixer.deck_b);
                
                // Update crossfader display from backend
                if (mixer.crossfader !== undefined) {
                    updateCrossfaderUI(mixer.crossfader);
                }
                
                // Update suggestion (make it prominent!)
                const sugCard = document.getElementById('suggestion');
                const sugMsg = document.getElementById('sug-msg');
                const sugTime = document.getElementById('sug-time');
                
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
    
    # Save file
    upload_dir = Path("data/tracks/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    with open(file_path, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    
    print(f"📥 Uploaded: {file.filename}")
    
    # Analyze track
    try:
        result = analyzer.analyze_track(str(file_path))
        
        # Add to library
        library.append(result)
        save_library()
        
        print(f"✅ Analyzed: {file.filename} - {result['bpm']:.0f} BPM, {result['key']}")
        
        return {"status": "ok", "track": result}
        
    except Exception as e:
        print(f"❌ Error analyzing {file.filename}: {e}")
        return {"status": "error", "message": str(e)}


# Get library
@app.get("/library")
async def get_library():
    """Get track library"""
    return library


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
                'queue': queue_manager.get_queue_info()
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
