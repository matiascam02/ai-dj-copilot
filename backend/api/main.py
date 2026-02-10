#!/usr/bin/env python3
"""
FastAPI Web Interface - AI DJ Co-Pilot

Endpoints:
- GET / - Web UI
- POST /upload - Upload and analyze track
- GET /library - Get all analyzed tracks
- GET /queue - Get current queue
- POST /queue/add - Add track to queue
- DELETE /queue/remove/{track_id} - Remove from queue
- GET /queue/next - Get next track suggestion
- POST /queue/current - Set current track
- GET /transitions/plan - Plan transition between tracks
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import sys
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from backend.audio_analysis.track_analyzer import TrackAnalyzer
    from backend.queue_manager.queue import QueueManager
    from backend.queue_manager.transition_planner import TransitionPlanner
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're in the project root and ran setup.sh")
    sys.exit(1)


# Initialize FastAPI app
app = FastAPI(
    title="AI DJ Co-Pilot API",
    description="AI-powered DJ assistant API",
    version="0.1.0"
)

# Initialize components
library = []  # In-memory storage (replace with DB later)
analyzer = TrackAnalyzer()
queue_manager = QueueManager()
transition_planner = TransitionPlanner()


def load_library():
    """Load library from cache file if it exists"""
    cache_file = Path("data/cache/library.json")
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            data = json.load(f)
            library.extend(data.get('tracks', []))
        print(f"Loaded {len(library)} tracks from cache")


def save_library():
    """Save library to cache file"""
    cache_file = Path("data/cache/library.json")
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(cache_file, 'w') as f:
        json.dump({
            'total_tracks': len(library),
            'tracks': library
        }, f, indent=2)


# Load library on startup
load_library()


@app.get("/", response_class=HTMLResponse)
async def index():
    """Main web interface"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI DJ Co-Pilot</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                padding: 20px;
                min-height: 100vh;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            header {
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }
            
            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .subtitle {
                font-size: 1.2em;
                opacity: 0.9;
            }
            
            .card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .card h2 {
                margin-bottom: 15px;
                color: #667eea;
                font-size: 1.5em;
            }
            
            .upload-form {
                display: flex;
                gap: 10px;
                align-items: center;
            }
            
            input[type="file"] {
                flex: 1;
                padding: 10px;
                border: 2px dashed #667eea;
                border-radius: 8px;
                cursor: pointer;
            }
            
            button {
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1em;
                font-weight: 600;
                transition: background 0.3s;
            }
            
            button:hover {
                background: #5568d3;
            }
            
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            
            .track-list {
                list-style: none;
            }
            
            .track-item {
                padding: 15px;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .track-item:last-child {
                border-bottom: none;
            }
            
            .track-info {
                flex: 1;
            }
            
            .track-name {
                font-weight: 600;
                margin-bottom: 5px;
            }
            
            .track-meta {
                font-size: 0.9em;
                color: #666;
            }
            
            .track-actions {
                display: flex;
                gap: 10px;
            }
            
            .btn-small {
                padding: 6px 12px;
                font-size: 0.85em;
            }
            
            .status {
                padding: 10px;
                border-radius: 8px;
                margin-bottom: 15px;
            }
            
            .status.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .status.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .status.hidden {
                display: none;
            }
            
            .current-track {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            
            .suggestion {
                background: #e7f3ff;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #0066cc;
                margin-bottom: 10px;
            }
            
            .score {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 0.85em;
            }
            
            .score.high {
                background: #28a745;
                color: white;
            }
            
            .score.medium {
                background: #ffc107;
                color: #333;
            }
            
            .score.low {
                background: #dc3545;
                color: white;
            }
            
            .loading {
                text-align: center;
                padding: 20px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🎧 AI DJ Co-Pilot</h1>
                <p class="subtitle">AI-powered track analysis and mixing assistant</p>
            </header>
            
            <!-- Upload Section -->
            <div class="card">
                <h2>📁 Upload Track</h2>
                <div id="upload-status" class="status hidden"></div>
                <form id="upload-form" class="upload-form">
                    <input type="file" id="file-input" accept="audio/*" required>
                    <button type="submit" id="upload-btn">Analyze Track</button>
                </form>
            </div>
            
            <!-- Queue Section -->
            <div class="card">
                <h2>🎵 Queue</h2>
                <div id="current-track-container"></div>
                <div id="queue-container"></div>
                <div id="next-suggestion-container"></div>
            </div>
            
            <!-- Library Section -->
            <div class="card">
                <h2>📚 Track Library</h2>
                <div id="library-container" class="loading">Loading library...</div>
            </div>
        </div>
        
        <script>
            // API base URL
            const API_URL = '';
            
            // Upload form handler
            document.getElementById('upload-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const fileInput = document.getElementById('file-input');
                const uploadBtn = document.getElementById('upload-btn');
                const statusDiv = document.getElementById('upload-status');
                
                if (!fileInput.files.length) {
                    return;
                }
                
                // Disable button
                uploadBtn.disabled = true;
                uploadBtn.textContent = 'Analyzing...';
                
                // Prepare form data
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                try {
                    const response = await fetch(`${API_URL}/upload`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'ok') {
                        statusDiv.className = 'status success';
                        statusDiv.textContent = '✓ Track analyzed successfully!';
                        statusDiv.classList.remove('hidden');
                        
                        // Reset form
                        fileInput.value = '';
                        
                        // Reload library
                        setTimeout(() => {
                            loadLibrary();
                            statusDiv.classList.add('hidden');
                        }, 2000);
                    } else {
                        throw new Error(data.message || 'Analysis failed');
                    }
                } catch (error) {
                    statusDiv.className = 'status error';
                    statusDiv.textContent = `✗ Error: ${error.message}`;
                    statusDiv.classList.remove('hidden');
                } finally {
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Analyze Track';
                }
            });
            
            // Load library
            async function loadLibrary() {
                const container = document.getElementById('library-container');
                
                try {
                    const response = await fetch(`${API_URL}/library`);
                    const tracks = await response.json();
                    
                    if (tracks.length === 0) {
                        container.innerHTML = '<p class="loading">No tracks in library. Upload some tracks to get started!</p>';
                        return;
                    }
                    
                    const html = `
                        <ul class="track-list">
                            ${tracks.map(track => `
                                <li class="track-item">
                                    <div class="track-info">
                                        <div class="track-name">${track.file_path.split('/').pop()}</div>
                                        <div class="track-meta">
                                            BPM: ${track.bpm.toFixed(1)} | 
                                            Key: ${track.key} ${track.scale} (${track.camelot}) | 
                                            Energy: ${(track.energy * 100).toFixed(0)}% | 
                                            Duration: ${Math.floor(track.duration / 60)}:${String(Math.floor(track.duration % 60)).padStart(2, '0')}
                                        </div>
                                    </div>
                                    <div class="track-actions">
                                        <button class="btn-small" onclick="addToQueue('${track.file_path}')">Add to Queue</button>
                                        <button class="btn-small" onclick="setCurrentTrack('${track.file_path}')">Set Current</button>
                                    </div>
                                </li>
                            `).join('')}
                        </ul>
                    `;
                    
                    container.innerHTML = html;
                } catch (error) {
                    container.innerHTML = `<p class="status error">Error loading library: ${error.message}</p>`;
                }
            }
            
            // Add to queue
            async function addToQueue(trackPath) {
                try {
                    const response = await fetch(`${API_URL}/queue/add`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ track_path: trackPath })
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'ok') {
                        loadQueue();
                        loadNextSuggestion();
                    }
                } catch (error) {
                    alert(`Error: ${error.message}`);
                }
            }
            
            // Set current track
            async function setCurrentTrack(trackPath) {
                try {
                    const response = await fetch(`${API_URL}/queue/current`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ track_path: trackPath })
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'ok') {
                        loadQueue();
                        loadNextSuggestion();
                    }
                } catch (error) {
                    alert(`Error: ${error.message}`);
                }
            }
            
            // Load queue
            async function loadQueue() {
                const currentContainer = document.getElementById('current-track-container');
                const queueContainer = document.getElementById('queue-container');
                
                try {
                    const response = await fetch(`${API_URL}/queue`);
                    const data = await response.json();
                    
                    // Current track
                    if (data.current_track) {
                        currentContainer.innerHTML = `
                            <div class="current-track">
                                <strong>🎵 Now Playing:</strong> ${data.current_track.split('/').pop()}
                            </div>
                        `;
                    } else {
                        currentContainer.innerHTML = '<p class="loading">No track currently playing</p>';
                    }
                    
                    // Queue
                    if (data.queue.length > 0) {
                        queueContainer.innerHTML = `
                            <h3 style="margin-top: 20px;">Queue (${data.queue.length} track${data.queue.length > 1 ? 's' : ''})</h3>
                            <ul class="track-list">
                                ${data.queue.map(track => `
                                    <li class="track-item">
                                        <div class="track-info">
                                            <div class="track-name">${track.file_path.split('/').pop()}</div>
                                            <div class="track-meta">
                                                BPM: ${track.bpm.toFixed(1)} | 
                                                Key: ${track.key} (${track.camelot}) | 
                                                Energy: ${(track.energy * 100).toFixed(0)}%
                                            </div>
                                        </div>
                                    </li>
                                `).join('')}
                            </ul>
                        `;
                    } else {
                        queueContainer.innerHTML = '<p class="loading" style="margin-top: 20px;">Queue is empty</p>';
                    }
                } catch (error) {
                    currentContainer.innerHTML = `<p class="status error">Error loading queue: ${error.message}</p>`;
                }
            }
            
            // Load next suggestion
            async function loadNextSuggestion() {
                const container = document.getElementById('next-suggestion-container');
                
                try {
                    const response = await fetch(`${API_URL}/queue/next`);
                    const data = await response.json();
                    
                    if (data.error) {
                        container.innerHTML = '';
                        return;
                    }
                    
                    const track = data.next_track;
                    const score = data.compatibility_score;
                    
                    let scoreClass = 'low';
                    if (score >= 0.85) scoreClass = 'high';
                    else if (score >= 0.70) scoreClass = 'medium';
                    
                    container.innerHTML = `
                        <div class="suggestion">
                            <h3>💡 Suggested Next Track</h3>
                            <div style="margin-top: 10px;">
                                <strong>${track.file_path.split('/').pop()}</strong>
                                <span class="score ${scoreClass}">${(score * 100).toFixed(0)}% Compatible</span>
                            </div>
                            <div class="track-meta" style="margin-top: 5px;">
                                BPM: ${track.bpm.toFixed(1)} | 
                                Key: ${track.key} (${track.camelot}) | 
                                Energy: ${(track.energy * 100).toFixed(0)}%
                            </div>
                        </div>
                    `;
                } catch (error) {
                    console.error('Error loading suggestion:', error);
                }
            }
            
            // Load data on page load
            loadLibrary();
            loadQueue();
            loadNextSuggestion();
            
            // Auto-refresh every 5 seconds
            setInterval(() => {
                loadQueue();
                loadNextSuggestion();
            }, 5000);
        </script>
    </body>
    </html>
    """)


@app.post("/upload")
async def upload_track(file: UploadFile = File(...)):
    """Upload and analyze a track"""
    try:
        # Save file
        upload_dir = Path("data/tracks/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        content = await file.read()
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Analyze track
        result = analyzer.analyze(str(file_path))
        
        # Add to library
        library.append(result)
        save_library()
        
        return {
            "status": "ok",
            "message": "Track analyzed successfully",
            "analysis": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/library")
async def get_library():
    """Get all analyzed tracks"""
    return library


@app.get("/queue")
async def get_queue():
    """Get current queue status"""
    return queue_manager.get_queue_info()


@app.post("/queue/add")
async def add_to_queue(request: dict):
    """Add track to queue"""
    try:
        track_path = request.get('track_path')
        
        # Find track in library
        track = next((t for t in library if t['file_path'] == track_path), None)
        
        if not track:
            raise HTTPException(status_code=404, detail="Track not found in library")
        
        queue_manager.add_track(track)
        
        return {
            "status": "ok",
            "message": "Track added to queue"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/queue/current")
async def set_current_track(request: dict):
    """Set currently playing track"""
    try:
        track_path = request.get('track_path')
        
        # Find track in library
        track = next((t for t in library if t['file_path'] == track_path), None)
        
        if not track:
            raise HTTPException(status_code=404, detail="Track not found in library")
        
        queue_manager.set_current_track(track)
        
        return {
            "status": "ok",
            "message": "Current track set"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/next")
async def get_next_track():
    """Get next track suggestion"""
    try:
        if not queue_manager.queue:
            return {"error": "Queue is empty"}
        
        if not queue_manager.current_track:
            return {"error": "No current track set"}
        
        suggestions = queue_manager.get_next_track(count=1)
        
        if not suggestions:
            return {"error": "No suggestions available"}
        
        next_track, score = suggestions[0]
        
        return {
            "next_track": next_track,
            "compatibility_score": score
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/transitions/plan")
async def plan_transition(track_a_path: str, track_b_path: str, transition_type: str = "standard"):
    """Plan a transition between two tracks"""
    try:
        # Find tracks in library
        track_a = next((t for t in library if t['file_path'] == track_a_path), None)
        track_b = next((t for t in library if t['file_path'] == track_b_path), None)
        
        if not track_a or not track_b:
            raise HTTPException(status_code=404, detail="Track(s) not found")
        
        # Plan transition
        plan = transition_planner.plan_transition(track_a, track_b, transition_type)
        
        return plan
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "library_size": len(library),
        "queue_size": len(queue_manager.queue),
        "current_track": queue_manager.current_track is not None
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🎧 AI DJ Co-Pilot API")
    print("=" * 50)
    print("Starting server...")
    print("Open http://localhost:8000 in your browser")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
