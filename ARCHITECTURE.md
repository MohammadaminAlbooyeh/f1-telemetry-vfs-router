# Sovereign Pit-Wall: System Architecture

## Overview

Sovereign Pit-Wall implements a **dual-layer edge computing architecture** designed for zero-latency F1 safety intervention. The system decouples compute from storage to eliminate I/O bottlenecks.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FORMULA 1 TELEMETRY SYSTEM                          │
└─────────────────────────────────────────────────────────────────────────────┘

                    ╔════════════════════════════════════════╗
                    ║   F1 CAR TELEMETRY BROADCAST          ║
                    ║   (1.1M data points/second)           ║
                    ║   • Tyres (pressure, temperature)     ║
                    ║   • Biometrics (heart rate, G-forces) ║
                    ║   • Engine (RPM, thermal)             ║
                    ║   • Hydraulics (pressure)             ║
                    ║   • Brakes (disc wear)                ║
                    ║   • Fuel (pressure, consumption)      ║
                    ╚════════════════════════════════════════╝
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                     LAYER 1: SOVEREIGN VFS (In-Memory)                     │
│                         Location: Trackside Edge Server                    │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ FIFO Decay Gate (30-Second Sliding Window)                          │  │
│  │ ─────────────────────────────────────────────────────────────────  │  │
│  │ • Accepts: Time frame 00:00 to 00:30                               │  │
│  │ • Purges: Expired data (-00:01) → Cloud Archive                    │  │
│  │ • Manages: 30-second high-entropy buffer                           │  │
│  │ • Output: Clean FIFO queue                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Priority Sector Packer (Binary Compression)                         │  │
│  │ ─────────────────────────────────────────────────────────────────  │  │
│  │ • Tier 1 (CRITICAL): Tyres, Biometrics, Engine, Hydraulics, Fuel  │  │
│  │   └─ Packed in 4KB Binary Sectors (struct module)                 │  │
│  │ • Tier 2 (STANDARD): Aero, Fuel Distribution                       │  │
│  │   └─ Packed in Standard Sectors                                   │  │
│  │ • Tier 3 (BACKGROUND): Driver Steering, Misc Telemetry            │  │
│  │   └─ Packed in Background Sectors                                 │  │
│  │                                                                      │  │
│  │ Format: struct.pack('6I', tyres, fatigue, thermal, hydraulics,   │  │
│  │                              brakes, fuel_system)                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                         (Zero-Latency Binary Stream)                       │
│                                    │                                        │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                  LAYER 2: IBM GRANITE AI DECISION ENGINE                   │
│                      Location: Pit Wall Local CPU                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Binary Unpacking & Data Extraction (Python struct module)           │  │
│  │ ─────────────────────────────────────────────────────────────────  │  │
│  │ • struct.unpack('6I', binary_payload)                               │  │
│  │ • Prevents Magic Byte TypeErrors                                    │  │
│  │ • Lossless data recovery from compressed binary                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Holistic Degradation Index (HDI) Calculation                        │  │
│  │ ─────────────────────────────────────────────────────────────────  │  │
│  │ Scale: 0 (Perfect) ──→ 100 (Dead/Catastrophic)                    │  │
│  │                                                                      │  │
│  │ HDI = Σ(Parameter × Weight)                                        │  │
│  │                                                                      │  │
│  │ • Tyre Degradation      (Weight: 25%)  → Blowout risk              │  │
│  │ • Driver Fatigue        (Weight: 25%)  → Cognitive degradation     │  │
│  │ • PU Thermal Health     (Weight: 20%)  → Engine operating window   │  │
│  │ • Hydraulics            (Weight: 15%)  → Gearbox/steering pressure │  │
│  │ • Brake Disc Wear       (Weight: 10%)  → Carbon friction limits    │  │
│  │ • Fuel System           (Weight: 5%)   → Pump pressure detection   │  │
│  │                                                                      │  │
│  │ Total: 1.0 (100%)                                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Dual-Trigger Safety Override Engine                                 │  │
│  │ ─────────────────────────────────────────────────────────────────  │  │
│  │                                                                      │  │
│  │ TRIGGER 1: REDLINE VETO (Single Parameter Kill Switch)             │  │
│  │ ──────────────────────────────────────────────────────────────     │  │
│  │ IF any_parameter > 85:                                             │  │
│  │    └─→ IMMEDIATE BOX BOX BOX (zero-latency override)              │  │
│  │    └─→ Bypass HDI average, enforce safety interrupt                │  │
│  │                                                                      │  │
│  │ TRIGGER 2: CASCADING FAILURE (System-Wide Degradation)             │  │
│  │ ──────────────────────────────────────────────────────────────     │  │
│  │ IF HDI > 70:                                                        │  │
│  │    └─→ STRATEGIC BOX BOX BOX (controlled pit intervention)         │  │
│  │    └─→ Prevents dead state before irreversible system failure     │  │
│  │                                                                      │  │
│  │ Result: Boolean pit_command + descriptive status message            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ IBM Granite LLM Natural Language Analysis                           │  │
│  │ ─────────────────────────────────────────────────────────────────  │  │
│  │ • System Health Classification (CRITICAL/WARNING/NOMINAL)           │  │
│  │ • Risk Factor Analysis (severity levels)                            │  │
│  │ • Strategic Recommendations (driver, tactical, technical)           │  │
│  │ • Natural Language Explanation for pit wall crew                    │  │
│  │ • JSON export for decision audit trail                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │ PIT COMMAND  │ │ LLM ANALYSIS │ │ CSV/JSON LOG │
            ├──────────────┤ ├──────────────┤ ├──────────────┤
            │ BOX BOX BOX  │ │ Structured   │ │ Telemetry    │
            │ (if triggered│ │ JSON export  │ │ data export  │
            │              │ │ with NLP     │ │ for analysis │
            └──────────────┘ └──────────────┘ └──────────────┘


```

---

## Data Flow Sequence

```
1. INGESTION
   F1 Telemetry → VFS Packer → Binary Payload (24 bytes)

2. STORAGE (30-sec FIFO)
   Binary → Deque(maxlen=30) → In-Memory Buffer

3. DECISION
   Unpack Binary → Calculate HDI → Check Dual-Triggers

4. OUTPUT
   Pit Command + Status → Console + Logging + JSON/CSV

5. ANALYSIS
   Granite LLM → Risk Assessment → Recommendations → Crew
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.12+ | Cross-platform implementation |
| **Binary Packing** | Python `struct` module | Zero-copy, lossless compression |
| **In-Memory Buffer** | Python `deque(maxlen=30)` | O(1) FIFO with automatic cleanup |
| **Decision Logic** | Pure Python computation | Fast weighted average + conditional logic |
| **AI Analysis** | IBM Granite LLM | Natural language insights & recommendations |
| **Logging** | Python `logging` + JSON | Structured event audit trail |
| **Data Export** | CSV + JSON | Integration with external tools |
| **Visualization** | Matplotlib | Real-time trend analysis charts |
| **Testing** | PyTest (20 unit tests) | Comprehensive coverage |

---

## Performance Characteristics

| Metric | Target | Status |
|--------|--------|--------|
| **Latency** | < 1ms per decision | ✅ Sub-millisecond (pure Python) |
| **Buffer Overhead** | 30 × 24 bytes = 720 bytes | ✅ Minimal RAM footprint |
| **Decision Frequency** | Real-time (per telemetry frame) | ✅ Every ~100ms in simulation |
| **Scalability** | Extensible to N parameters | ✅ Schema-less design |

---

## Deployment Architecture

```
┌─────────────────────────────────┐
│   F1 Trackside Network          │
│   (Telemetry Broadcast Feed)    │
└──────────────┬──────────────────┘
               │
        ┌──────▼──────┐
        │ Edge Server │ ← Sovereign VFS (Layer 1)
        │ (VFS Cache) │
        └──────┬──────┘
               │
        ┌──────▼──────────────┐
        │  Pit Wall CPU       │ ← IBM Granite (Layer 2)
        │  (Decision Engine)  │
        └──────┬──────────────┘
               │
        ┌──────▼──────────────┐
        │  FIA Telemetry      │ ← Cloud Archive
        │  Storage            │   (30s+ retention)
        └─────────────────────┘
```

---

## Safety Design Principles

1. **Zero-Latency**: In-memory processing eliminates database I/O
2. **Dual-Trigger**: Redundant safety mechanisms prevent single-point failure
3. **Bio-Mechanical Parity**: Driver safety weighted equally with mechanical integrity
4. **Extensibility**: New parameters absorb without core logic rewrite
5. **Auditability**: Complete decision audit trail in JSON logs

---

## IBM Granite Integration

The system leverages IBM Granite LLM for:

- **Natural Language Explanations**: Pit wall crew receives human-readable status
- **Risk Factor Analysis**: Structured assessment of each parameter
- **Strategic Recommendations**: Tactical guidance for race strategy
- **Decision Justification**: Audit trail for FIA compliance

Example Granite Output:
```json
{
  "system_health": "CRITICAL - IMMEDIATE INTERVENTION REQUIRED",
  "risk_factors": [
    {
      "parameter": "Driver Fatigue",
      "value": 88,
      "severity": "CRITICAL",
      "description": "Driver fatigue exceeded safe limit (85)"
    }
  ],
  "recommendations": [
    "PRIORITY: Driver requires immediate rest intervention",
    "STRATEGIC: Schedule pit stop for driver change"
  ]
}
```

---

## Testing & Validation

- **20 Unit Tests**: VFS packing, AI decisions, Granite analysis, edge cases
- **100% Test Pass Rate**: All scenarios validated
- **Safety Boundary Testing**: Redline Veto and Cascading Failure thresholds verified
- **Parameter Validation**: HDI calculation accuracy confirmed

---

## Future Extensions

1. **Real-Time Model Updates**: Dynamic weight calibration per race conditions
2. **Multi-Car Orchestration**: Fleet-wide telemetry synchronization
3. **FIA Regulation Adapter**: Absorb new parameters dynamically
4. **Predictive Analytics**: Forecast failure modes before threshold breach
5. **Cloud Sync**: Hybrid edge/cloud architecture for extended analysis

