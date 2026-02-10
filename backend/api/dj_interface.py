#!/usr/bin/env python3
"""
DJ Interface API - Real-time mixer control and suggestions

Complete API for live DJ performance:
- Deck control (play/pause/cue/loop)
- Effects (EQ, filter, reverb)
- Real-time suggestions
- Track queue management
- WebSocket for live updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import asyncio
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
app = FastAPI(title="AI DJ Co-Pilot - Live Interface")

# Initialize components
mixer = DJMixer()
effects_a = EffectsChain()
effects_b = EffectsChain()
queue_manager = QueueManager()
transition_planner = TransitionPlanner()
advisor = DJAdvisor(mixer, queue_manager, transition_planner)
analyzer = TrackAnalyzer()

# Track library (load from cache)
library = []

# Active WebSocket connections
active_connections: List[WebSocket] = []


def load_library():
    """Load track library from cache"""
    cache_file = Path("data/cache/library.json")
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            data = json.load(f)
            library.extend(data.get('tracks', []))
        print(f"📚 Loaded {len(library)} tracks")


# Load library on startup
load_library()

# Start mixer
mixer.start()
print("🎛️ Mixer started")


@app.on_event("shutdown")
async def shutdown():
    """Clean shutdown"""
    mixer.stop()
    print("🎛️ Mixer stopped")


# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for live status updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send status update every 100ms
            status = {
                'mixer': mixer.get_status(),
                'suggestion': advisor.get_suggestion(),
                'queue': queue_manager.get_queue_info()
            }
            
            await websocket.send_json(status)
            await asyncio.sleep(0.1)  # 10 Hz update rate
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)


# Main DJ interface
@app.get("/", response_class=HTMLResponse)
async def dj_interface():
    """Main DJ interface"""
    html_path = Path(__file__).parent.parent.parent / "frontend" / "dj_interface.html"
    
    if html_path.exists():
        return FileResponse(html_path)
    
    # Inline HTML if file doesn't exist yet
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI DJ Co-Pilot - Live</title>
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
                grid-template-rows: 60px 1fr 200px;
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
            
            header h1 {
                font-size: 24px;
            }
            
            .status-badge {
                background: rgba(255,255,255,0.2);
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
            }
            
            /* Main area */
            .main {
                display: grid;
                grid-template-columns: 1fr 400px 1fr;
                gap: 20px;
                padding: 20px;
                overflow-y: auto;
            }
            
            /* Deck */
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
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .waveform {
                width: 100%;
                height: 80px;
                background: #1a1a1a;
                border-radius: 8px;
                margin: 15px 0;
                position: relative;
                overflow: hidden;
            }
            
            .waveform-progress {
                position: absolute;
                top: 0;
                left: 0;
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                opacity: 0.3;
                transition: width 0.1s linear;
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
                margin-bottom: 15px;
            }
            
            .controls {
                display: flex;
                gap: 10px;
                margin: 15px 0;
            }
            
            button {
                flex: 1;
                padding: 12px;
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
            
            button:active {
                transform: translateY(0);
            }
            
            button.danger {
                background: #e74c3c;
            }
            
            button.secondary {
                background: #555;
            }
            
            /* Center panel - Suggestions */
            .center-panel {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            
            .suggestion-card {
                background: #2a2a2a;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
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
                50% { transform: scale(1.02); }
            }
            
            .suggestion-message {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .suggestion-timing {
                font-size: 14px;
                color: #ddd;
            }
            
            .crossfader-section {
                background: #2a2a2a;
                border-radius: 12px;
                padding: 20px;
            }
            
            .crossfader {
                width: 100%;
                height: 60px;
                -webkit-appearance: none;
                background: #1a1a1a;
                border-radius: 30px;
                outline: none;
            }
            
            .crossfader::-webkit-slider-thumb {
                -webkit-appearance: none;
                width: 40px;
                height: 50px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                border-radius: 10px;
                cursor: pointer;
            }
            
            .queue-panel {
                background: #2a2a2a;
                border-radius: 12px;
                padding: 20px;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .queue-item {
                padding: 10px;
                background: #1a1a1a;
                border-radius: 6px;
                margin-bottom: 8px;
                font-size: 14px;
            }
            
            /* Bottom panel */
            .bottom-panel {
                background: #2a2a2a;
                padding: 20px;
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
            }
            
            .eq-section {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .eq-control {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .eq-label {
                width: 60px;
                font-size: 12px;
            }
            
            input[type="range"] {
                flex: 1;
                -webkit-appearance: none;
                background: #1a1a1a;
                height: 4px;
                border-radius: 2px;
            }
            
            input[type="range"]::-webkit-slider-thumb {
                -webkit-appearance: none;
                width: 16px;
                height: 16px;
                background: #667eea;
                border-radius: 50%;
                cursor: pointer;
            }
            
            .meter {
                width: 100%;
                height: 20px;
                background: #1a1a1a;
                border-radius: 4px;
                overflow: hidden;
                margin-top: 5px;
            }
            
            .meter-fill {
                height: 100%;
                background: linear-gradient(90deg, #2ecc71, #f39c12, #e74c3c);
                transition: width 0.1s;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <header>
                <h1>🎧 AI DJ Co-Pilot - Live</h1>
                <div class="status-badge" id="status">Connecting...</div>
            </header>
            
            <!-- Main area -->
            <div class="main">
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
                        <button onclick="control('play_a')">▶️ Play</button>
                        <button onclick="control('pause_a')" class="secondary">⏸</button>
                        <button onclick="control('stop_a')" class="danger">⏹</button>
                    </div>
                    
                    <div class="controls">
                        <button onclick="control('cue_a')" class="secondary">⏮ Cue</button>
                        <button onclick="control('loop_a')" class="secondary">🔁 Loop</button>
                    </div>
                    
                    <div class="meter">
                        <div class="meter-fill" id="meter-a" style="width: 0%"></div>
                    </div>
                </div>
                
                <!-- Center panel -->
                <div class="center-panel">
                    <div class="suggestion-card" id="suggestion">
                        <div class="suggestion-message" id="sug-msg">
                            Waiting for tracks...
                        </div>
                        <div class="suggestion-timing" id="sug-time"></div>
                    </div>
                    
                    <div class="crossfader-section">
                        <h3 style="margin-bottom: 15px;">Crossfader</h3>
                        <input type="range" class="crossfader" id="crossfader"
                               min="-1" max="1" step="0.01" value="0"
                               oninput="setCrossfader(this.value)">
                        <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 12px;">
                            <span>A</span>
                            <span>CENTER</span>
                            <span>B</span>
                        </div>
                    </div>
                    
                    <div class="queue-panel">
                        <h3 style="margin-bottom: 15px;">Queue</h3>
                        <div id="queue">
                            <div style="text-align: center; color: #666;">Queue empty</div>
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
                        <button onclick="control('play_b')">▶️ Play</button>
                        <button onclick="control('pause_b')" class="secondary">⏸</button>
                        <button onclick="control('stop_b')" class="danger">⏹</button>
                    </div>
                    
                    <div class="controls">
                        <button onclick="control('cue_b')" class="secondary">⏮ Cue</button>
                        <button onclick="control('loop_b')" class="secondary">🔁 Loop</button>
                    </div>
                    
                    <div class="meter">
                        <div class="meter-fill" id="meter-b" style="width: 0%"></div>
                    </div>
                </div>
            </div>
            
            <!-- Bottom panel - EQ and Effects -->
            <div class="bottom-panel">
                <div class="eq-section">
                    <h3>EQ Deck A</h3>
                    <div class="eq-control">
                        <span class="eq-label">BASS</span>
                        <input type="range" min="0" max="2" step="0.1" value="1" 
                               oninput="setEQ('a', 'bass', this.value)">
                    </div>
                    <div class="eq-control">
                        <span class="eq-label">MID</span>
                        <input type="range" min="0" max="2" step="0.1" value="1"
                               oninput="setEQ('a', 'mid', this.value)">
                    </div>
                    <div class="eq-control">
                        <span class="eq-label">HIGH</span>
                        <input type="range" min="0" max="2" step="0.1" value="1"
                               oninput="setEQ('a', 'high', this.value)">
                    </div>
                </div>
                
                <div class="eq-section">
                    <h3>EQ Deck B</h3>
                    <div class="eq-control">
                        <span class="eq-label">BASS</span>
                        <input type="range" min="0" max="2" step="0.1" value="1"
                               oninput="setEQ('b', 'bass', this.value)">
                    </div>
                    <div class="eq-control">
                        <span class="eq-label">MID</span>
                        <input type="range" min="0" max="2" step="0.1" value="1"
                               oninput="setEQ('b', 'mid', this.value)">
                    </div>
                    <div class="eq-control">
                        <span class="eq-label">HIGH</span>
                        <input type="range" min="0" max="2" step="0.1" value="1"
                               oninput="setEQ('b', 'high', this.value)">
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            
            // Connect to WebSocket
            function connect() {
                ws = new WebSocket(`ws://${window.location.host}/ws`);
                
                ws.onopen = () => {
                    document.getElementById('status').textContent = '🟢 Live';
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    updateUI(data);
                };
                
                ws.onclose = () => {
                    document.getElementById('status').textContent = '🔴 Disconnected';
                    setTimeout(connect, 1000);
                };
            }
            
            function updateUI(data) {
                const mixer = data.mixer;
                const suggestion = data.suggestion;
                
                // Update Deck A
                updateDeck('a', mixer.deck_a);
                
                // Update Deck B
                updateDeck('b', mixer.deck_b);
                
                // Update suggestion
                const sugCard = document.getElementById('suggestion');
                sugCard.className = `suggestion-card ${suggestion.urgency}`;
                document.getElementById('sug-msg').textContent = suggestion.message;
                document.getElementById('sug-time').textContent = suggestion.timing || '';
            }
            
            function updateDeck(id, deck) {
                // Track name
                document.getElementById(`track-${id}`).textContent = 
                    deck.track || 'No track loaded';
                
                // Progress
                const progress = deck.progress * 100;
                document.getElementById(`wave-${id}`).style.width = `${progress}%`;
                document.getElementById(`pos-${id}`).style.left = `${progress}%`;
                
                // Time
                document.getElementById(`time-${id}`).textContent = 
                    formatTime(deck.position);
                document.getElementById(`remain-${id}`).textContent = 
                    '-' + formatTime(deck.time_remaining);
                
                // Meter
                document.getElementById(`meter-${id}`).style.width = 
                    `${Math.min(deck.peak * 100, 100)}%`;
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
                fetch('/control/crossfader', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({value: parseFloat(value)})
                });
            }
            
            function setEQ(deck, band, value) {
                fetch('/control/eq', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        deck: deck,
                        band: band,
                        value: parseFloat(value)
                    })
                });
            }
            
            // Connect on load
            connect();
        </script>
    </body>
    </html>
    """)


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


@app.post("/control/eq")
async def set_eq(data: dict):
    """Set EQ band"""
    deck = data['deck']
    band = data['band']
    value = data['value']
    
    effects = effects_a if deck == 'a' else effects_b
    
    if band == 'bass':
        effects.eq.bass = value
    elif band == 'mid':
        effects.eq.mid = value
    elif band == 'high':
        effects.eq.high = value
    
    return {'status': 'ok'}


@app.post("/load/{deck}")
async def load_track(deck: str, track_path: str):
    """Load track into deck"""
    
    target_deck = mixer.deck_a if deck == 'a' else mixer.deck_b
    
    if target_deck.load(track_path):
        return {'status': 'ok'}
    else:
        raise HTTPException(status_code=500, detail="Failed to load track")


@app.get("/library")
async def get_library():
    """Get track library"""
    return library


if __name__ == "__main__":
    import uvicorn
    
    print("🎧 AI DJ Co-Pilot - Live Interface")
    print("=" * 50)
    print("Starting server on http://localhost:8000")
    print("Open in your browser to start DJing!")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
