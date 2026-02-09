---
title: AI DJ Co-Pilot - Hardware Research
type: research
project: ai-dj-copilot
created: 2026-02-09
---

# Hardware Research - DIY DJ Controller

Research on building custom DJ hardware with Raspberry Pi + embedded AI

---

## Raspberry Pi Audio Performance

### Achievable Latency

**HiFiBerry DAC+ Pro:**
- Best case: **~5ms** latency
- With JACK + RT kernel: **4.9ms** confirmed working
- Buffer size: 64-128 samples optimal
- **Conclusion: GOOD ENOUGH for DJ use** (commercial controllers are 3-10ms)

**Configuration Required:**
```bash
# 1. Install PREEMPT RT kernel
sudo apt install linux-image-rt-arm64

# 2. Configure JACK for low latency
jackd -R -P75 -dalsa -dhw:0 -r44100 -p64 -n2

# 3. HiFiBerry DSP settings
# Set "DSP Program" to low-latency filter in ALSA mixer
```

**Key Learnings:**
- Avoid PulseAudio/Pipewire (adds latency)
- Use plain ALSA + JACK
- RT kernel essential
- Buffer <64 samples challenging but possible

**Source:**
- https://www.hifiberry.com/blog/techtalk-latency/
- https://wiki.linuxaudio.org/wiki/raspberrypi

---

## Raspberry Pi DJ Projects (Prior Art)

### 1. pi_dj (Dennis de Bel)
**GitHub:** https://github.com/dennisdebel/pi_dj

**What it does:**
- Mixxx (open-source DJ software) on Raspberry Pi
- Custom configs + skins
- Works with generic MIDI controllers

**Learnings:**
- Mixxx is proven to work on Pi
- Pi 4 handles 2-deck mixing fine
- External MIDI controller recommended

---

### 2. DivingBoard (MIDI Synth Controller)
**Source:** Raspberry Pi official blog (Feb 2024)

**Hardware:**
- Raspberry Pi Zero 2 W
- Arduino Nano (handles MIDI)
- 8 potentiometers + 4 rotary encoders
- 20×4 LCD screen

**Architecture:**
- Arduino handles inputs (low-latency)
- Pi runs main logic
- Serial communication between them

**Key Learning:**
- **Hybrid approach: Arduino for inputs, Pi for brains**
- Reduces latency on time-critical controls
- Pi handles complex logic (AI, UI, storage)

**Link:** https://www.raspberrypi.com/news/divingboard-a-homemade-midi-controller-for-synth-lovers/

---

### 3. Alcyone (Red Hat MIDI Controller)
**Source:** https://www.redhat.com/en/blog/developing-alcyone-raspberry-pi-midi-controller

**Architecture:**
- Started as Arduino project ("Frankenpedal")
- Migrated to Raspberry Pi for more power
- Custom PCB for MIDI I/O

**Key Learning:**
- Arduino good for simple MIDI
- Pi needed for complex features
- Suggests our hybrid approach is smart

---

## Hardware Architecture Decision

### Option A: Pi-Only
```
Raspberry Pi 5
├─ GPIO → buttons/encoders (direct)
├─ I2S → HiFiBerry DAC
└─ USB → storage
```

**Pros:**
- Simplest
- Fewer components

**Cons:**
- GPIO interrupt latency (not ideal for jog wheels)
- Pi busy with audio + AI = input lag risk

---

### Option B: Pi + Arduino (RECOMMENDED)
```
Arduino Nano/Teensy          Raspberry Pi 5
├─ Jog wheels                ├─ Audio processing
├─ Buttons/pads              ├─ AI inference
├─ Encoders                  ├─ UI (touchscreen)
└─ Serial/MIDI → ───────────→└─ Storage
```

**Pros:**
- Arduino handles time-critical inputs (jog wheels, pads)
- Pi focuses on audio + AI (no GPIO interrupts)
- Lower latency on physical controls
- Easier to debug

**Cons:**
- More complex (2 processors)
- Serial communication overhead (minimal)

**Verdict: This is the way**

---

## Component Deep-Dive

### 1. Jog Wheels

**Challenge:** Most critical control, needs <1ms response

**Options:**

#### A. Salvage from CDJs (Used)
- **Source:** eBay, broken Pioneer CDJs
- **Cost:** $30-100 per wheel (from broken units)
- **Pros:** Professional feel, proven reliability
- **Cons:** Hard to find, reverse-engineering needed

#### B. Optical Encoders + Custom Platter
- **Encoder:** Bourns PEC11 or similar (600 pulses/rev)
- **Platter:** 3D printed or CNC aluminum disc
- **Touch sensor:** Capacitive (detect hand on wheel)
- **Cost:** $20-40 per wheel
- **Pros:** Fully custom, easier to source
- **Cons:** Won't feel exactly like CDJ

#### C. iPac Spinner (Arcade Trackball)
- **Use:** Trackball controller as jog wheel
- **Cost:** $25
- **Pros:** USB plug-and-play
- **Cons:** Won't look/feel like DJ gear

**Recommendation:** Start with Option C for MVP, upgrade to Option B for production

---

### 2. Audio Interface

**HiFiBerry DAC+ Pro:**
- **Specs:** 24-bit/192kHz, 112dB SNR
- **Outputs:** RCA (unbalanced)
- **Cost:** $50
- **Latency:** ~5ms
- **Good for:** MVP prototype

**HiFiBerry DAC2 Pro XLR:**
- **Specs:** 24-bit/192kHz, 118dB SNR
- **Outputs:** XLR (balanced) + RCA
- **Cost:** $100
- **Latency:** ~5ms
- **Good for:** Production hardware

**Custom DAC (Future):**
- **Chip:** PCM5102A or AK4493
- **Design:** Custom PCB with balanced outputs
- **Cost:** $30-50 (DIY)
- **Good for:** Final product

---

### 3. AI Accelerator

**Why needed:**
- Raspberry Pi CPU okay for basic inference
- ML models (Transformers, RL) too slow on CPU
- Need <100ms inference for real-time suggestions

**Options:**

#### Google Coral TPU (USB)
- **Speed:** 400 GFLOPS, 4 TOPS (INT8)
- **Models:** TensorFlow Lite only
- **Latency:** 1-5ms per inference
- **Cost:** $60
- **Verdict:** Best for MVP**

#### NVIDIA Jetson Nano
- **Speed:** 472 GFLOPS (GPU)
- **Models:** PyTorch, TensorFlow (full support)
- **Cost:** $150-200
- **Verdict:** Overkill, use if Coral not enough

#### Hailo-8 AI Accelerator
- **Speed:** 26 TOPS
- **Cost:** $70
- **Verdict:** Newer, less tested

**Recommendation:** Start with Coral TPU

---

### 4. Input Components

**Buttons (Pads):**
- **Arcade buttons:** $1-3 each (Sanwa/Seimitsu clones)
- **With LEDs:** RGB addressable ($3-5 each)
- **Silicone pads:** $$$$ (like Akai MPC, not worth it for MVP)

**Rotary Encoders (EQ knobs):**
- **Basic:** $1-2 each (KY-040, EC11)
- **High-quality:** $5-10 each (Alps, Bourns)
- **Recommendation:** Mix both (high-quality for main controls)

**Faders:**
- **Crossfader:** Alps RSA0N11M9 ($15-20) - industry standard
- **Channel faders:** Generic 60mm ($5-10 each)

**Switches:**
- **Toggle:** $2-3 each
- **Momentary:** $1-2 each

---

### 5. Displays

**Per-Deck OLED (Track Info):**
- **Type:** SSD1306 128x64
- **Interface:** I2C
- **Cost:** $5-8 each
- **Shows:** Track name, BPM, key, time

**Central Touchscreen (Main UI):**
- **Type:** 7" IPS TFT
- **Resolution:** 1024x600
- **Interface:** HDMI + USB touch
- **Cost:** $40-60
- **Shows:** Waveforms, queue, AI status

**Alternative:** Single large touchscreen (10") - $80-120

---

### 6. Power Supply

**Requirements:**
- Raspberry Pi 5: 5V/5A (25W)
- HiFiBerry: <2W
- Arduino: <1W
- Displays: <5W
- LEDs/buttons: <10W
- **Total: ~45W**

**Options:**
- USB-C PD (65W charger): $20
- Internal AC/DC: $30-40 (cleaner, but more complex)

**For gigs:** Battery backup (portable power bank, 20,000mAh)

---

## Enclosure Design

### Dimensions Reference

**Pioneer DDJ-400:**
- 19.1" x 10.7" x 2.2" (485 x 272 x 57mm)

**Your Controller (Proposed):**
- 20" x 12" x 3" (500 x 300 x 75mm)
- Slightly larger for custom layout + AI displays

### Materials

**MVP (3D Printed):**
- PLA or PETG
- Print time: 30-50 hours total
- Cost: $50-100 in filament
- Design in: Fusion 360 (free for hobbyists)

**Production (CNC Aluminum):**
- 6061 aluminum, black anodized
- Top panel: 3mm thick
- Side panels: 2mm thick
- Bottom: 1.5mm steel (weight/stability)
- Cost: $300-800 (prototype), $30-80 at scale

**Hybrid (Best of Both):**
- 3D printed internal structure
- CNC top panel (professional look)
- Laser-cut acrylic sides (unique aesthetic)
- Cost: $150-250

---

## Electronics Assembly

### PCB Options

**MVP: Breadboard + Perfboard**
- Wire everything manually
- Messy but functional
- Cost: $20-30

**Better: Custom PCB (OSH Park, JLCPCB)**
- Design in KiCad (free)
- Manufacture in China ($30 for 10 boards)
- SMT assembly available (+$50-100)

**Production: Full custom PCB**
- All components integrated
- Professional assembly
- Cost: $500-1000 (prototype), $20-50 at scale

---

## Software Stack (Embedded)

### Operating System
```
Raspberry Pi OS Lite (64-bit)
├─ Minimal install (no desktop)
├─ PREEMPT RT kernel
└─ Python 3.11+
```

### Audio
```
ALSA (low-level) → JACK (routing) → Python (processing)
```

### AI Runtime
```
TensorFlow Lite (for Coral TPU)
├─ Convert PyTorch models → TFLite
└─ Optimize for INT8 quantization
```

### UI
```
Qt/QML (touchscreen interface)
├─ Hardware-accelerated graphics
└─ Responsive design
```

---

## Prototype Timeline

### Month 1-2: Order & Test Components
- [ ] Raspberry Pi 5 (8GB)
- [ ] HiFiBerry DAC+ Pro
- [ ] Google Coral TPU
- [ ] 7" touchscreen
- [ ] Arduino Nano
- [ ] Basic buttons/encoders for testing

**Goal:** Verify audio latency + AI inference speed

---

### Month 3-4: Build Control Board
- [ ] Design PCB for buttons/encoders in KiCad
- [ ] Order PCB ($30)
- [ ] Solder components
- [ ] Write Arduino firmware (MIDI output)
- [ ] Test with Pi

**Goal:** Working input system

---

### Month 5-6: Jog Wheel Integration
- [ ] Source/build jog wheels
- [ ] Integrate with Arduino
- [ ] Test latency (must be <5ms)

**Goal:** Full input hardware complete

---

### Month 7-8: Enclosure Design
- [ ] 3D model in Fusion 360
- [ ] Print prototype (iterate on design)
- [ ] Assemble all components
- [ ] Wire everything

**Goal:** Fully functional hardware prototype

---

### Month 9-10: Software Optimization
- [ ] Port Python backend to Pi
- [ ] Optimize AI models for Coral
- [ ] Build touchscreen UI
- [ ] Test with real DJ sessions

**Goal:** Production-ready firmware

---

## Cost Summary (MVP Prototype)

| Category | Cost |
|----------|------|
| **Electronics** | $300 |
| **Input Controls** | $225 |
| **Enclosure (3D)** | $80 |
| **Misc (wire, etc.)** | $50 |
| **Tools (if needed)** | $100 |
| **TOTAL** | **~$755** |

**Timeline:** 6-8 months from now to working prototype

---

## Manufacturing (1000 Units)

### Setup Costs
| Item | Cost |
|------|------|
| PCB design | $5,000 |
| Injection mold tooling | $15,000 |
| Certification (FCC, CE) | $10,000 |
| Assembly setup | $5,000 |
| **Total NRE** | **$35,000** |

### Per-Unit Cost (at 1k)
| Component | Cost |
|-----------|------|
| Electronics | $150 |
| Enclosure | $40 |
| Assembly | $20 |
| Packaging | $10 |
| **COGS** | **$220** |

**Retail:** $800  
**Margin:** 72%  
**Profit per unit:** $580

**Kickstarter goal:** $50k (covers NRE + first 100 units)

---

## Next Actions

**This Week:**
1. ✅ Document hardware vision
2. → Order Raspberry Pi 5 + HiFiBerry for testing
3. → Measure audio latency in controlled test
4. → Port track analyzer to run on Pi

**Next Month:**
1. Test AI models on Coral TPU
2. Order basic input components (buttons, encoders)
3. Build simple MIDI controller with Arduino
4. Design control layout (what goes where)

---

**Status:** Research Complete  
**Next:** Order development hardware  
**Last Updated:** February 9, 2026
