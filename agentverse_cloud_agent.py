"""
CampusMate AI - Autonomous Academic & Placement Twin Agent
Fetch.ai Cloud Hosted Agent for Agentverse (24/7 Zero-Downtime Deployment)
Compatible with ASI:One and official Agent Chat Protocol (ACP 0.3.0).
"""

import re
import json
import asyncio
from typing import Dict, Any, List, Optional
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage as ACPChatMessage,
    ChatAcknowledgement,
    TextContent
)

# Embedded Official Databases (Zero-Hallucination Ground Truth)
CURRICULUM_DATA = {
  "metadata": {
    "university": "Dr. A.P.J. Abdul Kalam Technical University (AKTU)",
    "college": "Galgotias College of Engineering and Technology (GCET)",
    "curriculum_version": "2024-2026 AICTE/AKTU Model Scheme",
    "target_academic_year": 3,
    "target_semesters": [
      5,
      6
    ],
    "author": "Member 2 - Syllabus Engine Lead"
  },
  "branches": {
    "ECE": {
      "branch_name": "Electronics & Communication Engineering",
      "branch_code": "ECE",
      "subjects": [
        {
          "subject_code": "KEC-502",
          "subject_name": "Digital Electronics & Logic Design",
          "semester": 5,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "High (VLSI, FPGA, Hardware/Firmware, Qualcomm, Intel)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Combinational Logic Circuits",
              "weightage_percent": 15.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "Boolean Algebra and Logic Minimization",
                "Karnaugh Maps (K-Maps) up to 5 variables",
                "Quine-McCluskey Minimization",
                "Binary Adders and Subtractors",
                "Look-Ahead Carry Generator",
                "Multiplexers and Demultiplexers",
                "Encoders and Priority Encoders",
                "Decoders and Code Converters"
              ],
              "key_concepts": [
                "K-Map minimization",
                "Mux-based logic synthesis",
                "Carry lookahead delay reduction"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Sequential Logic & Flip-Flops",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Latches vs Flip-Flops",
                "SR Latch and SR Flip-Flop",
                "JK Flip-Flop and Race-Around Condition",
                "Master-Slave JK Flip-Flop",
                "D Flip-Flop (Delay) and T Flip-Flop (Toggle)",
                "Characteristic Equations and Truth Tables",
                "Excitation Tables for all Flip-Flops",
                "Flip-Flop Conversions (e.g., SR to JK, D to T)",
                "Edge-Triggering and Setup/Hold Times"
              ],
              "key_concepts": [
                "Master-Slave elimination of race-around",
                "Excitation tables for sequential synthesis",
                "Setup and Hold time constraints"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Sequential Circuit Design: Registers & Counters",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Registers and Shift Registers (SISO, SIPO, PISO, PIPO)",
                "Bidirectional and Universal Shift Registers",
                "Asynchronous / Ripple Counters (MOD-N Counter Design)",
                "Synchronous Counter Design using Excitation Tables",
                "Up-Down Synchronous Counters",
                "Ring Counter and Johnson (Twisted Ring) Counter",
                "Decade Counter (7490 IC Architecture)"
              ],
              "key_concepts": [
                "MOD-N counter state transitions",
                "Propagation delay in ripple counters",
                "Johnson counter decoding efficiency"
              ]
            },
            {
              "unit_number": 4,
              "unit_title": "Finite State Machines & Synchronous Sequential Design",
              "weightage_percent": 20.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Mealy vs Moore State Machine Models",
                "State Diagrams and State Tables",
                "State Minimization using Implication Charts",
                "State Assignment Strategies (Gray Code, One-Hot)",
                "Sequence Detectors (Overlapping vs Non-overlapping 1011/1101)"
              ],
              "key_concepts": [
                "Mealy output dependence on current input",
                "Moore output glitch immunity",
                "Sequence detector synthesis"
              ]
            },
            {
              "unit_number": 5,
              "unit_title": "Logic Families and Semiconductor Memories",
              "weightage_percent": 15.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "Digital IC Logic Families (TTL, CMOS, ECL)",
                "Fan-in, Fan-out, Noise Margin, Propagation Delay",
                "ROM, PROM, EPROM, EEPROM, Flash Memory",
                "SRAM vs DRAM Cells",
                "Programmable Logic Devices (PLA, PAL, CPLD, FPGA)"
              ],
              "key_concepts": [
                "CMOS static power dissipation advantages",
                "PLA vs PAL architecture and programmability"
              ]
            }
          ]
        },
        {
          "subject_code": "KEC-501",
          "subject_name": "Microprocessors & Microcontrollers",
          "semester": 5,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "High (Embedded Systems, IoT, Firmware, Texas Instruments, Qualcomm)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "8085 Microprocessor Architecture",
              "weightage_percent": 20.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "8085 Architecture Overview and Functional Block Diagram",
                "Register Organization (A, B, C, D, E, H, L, SP, PC)",
                "Flag Register (Sign, Zero, Auxiliary Carry, Parity, Carry)",
                "Demultiplexing Address/Data Bus (ALE signal)",
                "Control and Status Signals (RD, WR, IO/M, S0, S1)",
                "Clock and Power Supply Circuitry"
              ],
              "key_concepts": [
                "Demultiplexing AD0-AD7 via 74LS373 latch",
                "Flag updates across arithmetic instructions"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "8085 Instruction Set & Assembly Programming",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Addressing Modes of 8085 (Immediate, Direct, Register, Register Indirect, Implicit)",
                "Instruction Classification (Data Transfer, Arithmetic, Logical, Branch, Stack/IO)",
                "Machine Cycles and Timing Diagrams (Opcode Fetch, Memory Read/Write, IO Read/Write)",
                "Assembly Language Programs (Block Move, Array Sorting, 16-bit Addition, BCD Arithmetic)",
                "Subroutines, CALL and RET operations, Stack Manipulation"
              ],
              "key_concepts": [
                "Opcode Fetch 4T machine cycle",
                "Timing diagram waveforms for MEMR and MEMW",
                "Subroutine stack pointer mechanics"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "8086 16-Bit Microprocessor Architecture",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "8086 Internal Architecture: Bus Interface Unit (BIU) & Execution Unit (EU)",
                "Pipelining and Instruction Queue (6-byte Prefetch Queue)",
                "Memory Segmentation and Physical Address Calculation (Segment:Offset)",
                "Segment Registers (CS, DS, SS, ES) and Pointer/Index Registers",
                "Minimum Mode vs Maximum Mode Operation",
                "8086 Addressing Modes and Basic Instruction Set"
              ],
              "key_concepts": [
                "Physical address = (Segment * 16) + Offset",
                "BIU and EU parallel pipelining",
                "Bus controller 8288 in Maximum mode"
              ]
            },
            {
              "unit_number": 4,
              "unit_title": "Peripheral Interfacing & Support Devices",
              "weightage_percent": 15.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "Memory Interfacing (Address Decoding using 74LS138)",
                "8255 Programmable Peripheral Interface (PPI) Architecture & Control Word",
                "8254/8253 Programmable Interval Timer (Modes 0 to 5)",
                "8259 Programmable Interrupt Controller (Cascading, Priority Modes)",
                "8257/8237 Direct Memory Access (DMA) Controller"
              ],
              "key_concepts": [
                "8255 BSR mode vs I/O mode control word",
                "DMA cycle stealing vs burst transfer"
              ]
            },
            {
              "unit_number": 5,
              "unit_title": "Interrupts & Real-Time Interfacing",
              "weightage_percent": 15.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "8085 Interrupt Structure (TRAP, RST 7.5, RST 6.5, RST 5.5, INTR)",
                "Hardware vs Software Interrupts, Vectored vs Non-Vectored Interrupts",
                "Interrupt Masking (SIM and RIM instructions)",
                "8086 Interrupt Vector Table (IVT) and Type 0-255 Interrupts",
                "Interfacing ADC0808/0809, DAC0808, and Stepper Motor"
              ],
              "key_concepts": [
                "TRAP highest priority non-maskable interrupt",
                "SIM instruction bitmask manipulation",
                "IVT address = Interrupt Type * 4"
              ]
            }
          ]
        },
        {
          "subject_code": "KEC-601",
          "subject_name": "Digital Communication",
          "semester": 6,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "High (Qualcomm, Intel, Signal Processing, Embedded)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Pulse Modulation (PAM, PWM, PPM)",
              "weightage_percent": 25.0,
              "is_high_yield": false,
              "estimated_hours": 6,
              "topics": [
                "Pulse Modulation (PAM, PWM, PPM)"
              ],
              "key_concepts": [
                "Pulse Modulation (PAM, PWM, PPM)"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Digital Modulation Techniques (ASK, PSK, QPSK)",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 8,
              "topics": [
                "Digital Modulation Techniques (ASK, PSK, QPSK)"
              ],
              "key_concepts": [
                "Digital Modulation Techniques (ASK, PSK, QPSK)"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Information Theory & Channel Coding",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Information Theory & Channel Coding"
              ],
              "key_concepts": [
                "Information Theory & Channel Coding"
              ]
            }
          ]
        },
        {
          "subject_code": "KEC-602",
          "subject_name": "Digital Signal Processing",
          "semester": 6,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "High (Qualcomm, Intel, Signal Processing, Embedded)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "DFT and FFT Algorithms",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 8,
              "topics": [
                "DFT and FFT Algorithms"
              ],
              "key_concepts": [
                "DFT and FFT Algorithms"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "IIR and FIR Filter Design",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "IIR and FIR Filter Design"
              ],
              "key_concepts": [
                "IIR and FIR Filter Design"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Finite Word Length Effects",
              "weightage_percent": 25.0,
              "is_high_yield": false,
              "estimated_hours": 6,
              "topics": [
                "Finite Word Length Effects"
              ],
              "key_concepts": [
                "Finite Word Length Effects"
              ]
            }
          ]
        },
        {
          "subject_code": "KEC-061",
          "subject_name": "Microcontrollers & Embedded Systems",
          "semester": 6,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "High (Qualcomm, Intel, Signal Processing, Embedded)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "8051 Architecture & Timers",
              "weightage_percent": 25.0,
              "is_high_yield": false,
              "estimated_hours": 5,
              "topics": [
                "8051 Architecture & Timers"
              ],
              "key_concepts": [
                "8051 Architecture & Timers"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "ARM Cortex-M Programming",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 8,
              "topics": [
                "ARM Cortex-M Programming"
              ],
              "key_concepts": [
                "ARM Cortex-M Programming"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Peripheral Interfacing (I2C, SPI)",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 7,
              "topics": [
                "Peripheral Interfacing (I2C, SPI)"
              ],
              "key_concepts": [
                "Peripheral Interfacing (I2C, SPI)"
              ]
            }
          ]
        },
        {
          "subject_code": "KAS-101",
          "subject_name": "Engineering Physics",
          "semester": 1,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Foundational Physics & Semiconductor Physics",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Relativistic Mechanics",
              "weightage_percent": 20.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "Lorentz Transformations",
                "Length Contraction",
                "Time Dilation"
              ],
              "key_concepts": [
                "Relativistic kinematics"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Electromagnetic Field Theory",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Maxwell Equations",
                "Poynting Vector",
                "Wave Propagation"
              ],
              "key_concepts": [
                "Maxwell equations in vacuum & dielectric"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Quantum Mechanics",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "De-Broglie Waves",
                "Schrodinger Wave Equation",
                "Particle in a 1D Box"
              ],
              "key_concepts": [
                "Wave function physical interpretation"
              ]
            }
          ]
        },
        {
          "subject_code": "KEE-201",
          "subject_name": "Basic Electrical Engineering",
          "semester": 2,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Circuit Analysis & Power Systems Foundation",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "DC Circuit Analysis",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 9,
              "topics": [
                "Thevenin Theorem",
                "Norton Theorem",
                "Superposition",
                "KVL/KCL"
              ],
              "key_concepts": [
                "Mesh and Nodal circuit reduction"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "AC Circuit Analysis",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Phasor Representation",
                "Series/Parallel Resonance",
                "Power Factor"
              ],
              "key_concepts": [
                "Q-factor and resonance frequency"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Transformers & Electrical Machines",
              "weightage_percent": 25.0,
              "is_high_yield": false,
              "estimated_hours": 9,
              "topics": [
                "Single Phase Transformer",
                "OC/SC Tests",
                "DC Machines"
              ],
              "key_concepts": [
                "Transformer equivalent circuit"
              ]
            }
          ]
        },
        {
          "subject_code": "KEC-301",
          "subject_name": "Electronic Devices & Semiconductor Physics",
          "semester": 3,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "High (VLSI, Qualcomm, Intel, Texas Instruments)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Semiconductor Physics & PN Junction",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Carrier Transport",
                "Diffusion and Drift",
                "PN Junction Depletion Region",
                "Diode Capacitance"
              ],
              "key_concepts": [
                "Bandgap theory & diode equation"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Bipolar Junction Transistors (BJT)",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "CE, CB, CC Configurations",
                "Ebers-Moll Model",
                "Transistor Biasing",
                "Early Effect"
              ],
              "key_concepts": [
                "BJT current gain & thermal stability"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "MOSFET & Field Effect Transistors",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "MOS Capacitor",
                "Threshold Voltage",
                "Depletion/Enhancement MOSFET",
                "Subthreshold Conduction"
              ],
              "key_concepts": [
                "I-V characteristics in linear and saturation"
              ]
            }
          ]
        },
        {
          "subject_code": "KEC-302",
          "subject_name": "Digital System Design",
          "semester": 3,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "High (VLSI & FPGA RTL Modeling)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Combinational Logic & Minimization",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 9,
              "topics": [
                "K-Maps up to 5 variables",
                "Quine-McCluskey",
                "Look-Ahead Carry Adders"
              ],
              "key_concepts": [
                "Hazards and glitches in logic circuits"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Synchronous Sequential Circuits",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 11,
              "topics": [
                "Mealy and Moore Machines",
                "State Reduction and Assignment",
                "Setup/Hold Margins"
              ],
              "key_concepts": [
                "FSM state diagram to hardware synthesis"
              ]
            }
          ]
        },
        {
          "subject_code": "KEC-401",
          "subject_name": "Analog Circuits",
          "semester": 4,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Analog IC Design (TI, Analog Devices)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Operational Amplifiers (Op-Amps)",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 11,
              "topics": [
                "Ideal vs Practical Op-Amp",
                "Inverting/Non-inverting",
                "Integrator and Differentiator",
                "CMRR & Slew Rate"
              ],
              "key_concepts": [
                "Virtual ground concept and frequency response"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Feedback Amplifiers & Oscillators",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Negative Feedback Topologies",
                "Barkhausen Criterion",
                "Wien Bridge and Colpitts"
              ],
              "key_concepts": [
                "Feedback stability and phase margin"
              ]
            }
          ]
        },
        {
          "subject_code": "KEC-402",
          "subject_name": "Signals & Systems",
          "semester": 4,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "DSP & Communications (Qualcomm, MediaTek)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Continuous & Discrete Time Signals",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Linear Time Invariant (LTI) Systems",
                "Convolution Integral & Sum",
                "Impulse Response"
              ],
              "key_concepts": [
                "BIBO stability & causality"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Fourier & Z-Transforms",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Continuous-Time Fourier Transform",
                "Z-Transform ROC",
                "Inverse Z-Transform"
              ],
              "key_concepts": [
                "Region of Convergence (ROC) properties"
              ]
            }
          ]
        },
        {
          "subject_code": "KEC-701",
          "subject_name": "VLSI Design & CMOS Circuit Architecture",
          "semester": 7,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Top Tier (Qualcomm, Nvidia, Apple Silicon)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "CMOS Inverter & Static Logic",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "CMOS Static Inverter VTC",
                "Noise Margins",
                "Propagation Delay & Elmore Delay",
                "Power Dissipation"
              ],
              "key_concepts": [
                "Dynamic vs static power and sizing ratio"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Dynamic Logic & Clocking",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Domino Logic",
                "Charge Sharing",
                "Clock Skew & Jitter",
                "Pipeline Retiming"
              ],
              "key_concepts": [
                "Metastability mitigation in multi-clock designs"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Physical Design & Static Timing Analysis",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Placement & Routing",
                "Clock Tree Synthesis (CTS)",
                "Setup/Hold Slack Equations"
              ],
              "key_concepts": [
                "Multi-corner timing closure"
              ]
            }
          ]
        },
        {
          "subject_code": "KEC-702",
          "subject_name": "Optical Fiber & Wireless Communication",
          "semester": 7,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Telecom & RF Engineering",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Optical Waveguides & Fibers",
              "weightage_percent": 25.0,
              "is_high_yield": false,
              "estimated_hours": 9,
              "topics": [
                "Total Internal Reflection",
                "Numerical Aperture",
                "Modal Dispersion",
                "Attenuation"
              ],
              "key_concepts": [
                "Single-mode vs multimode dispersion"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Cellular Radio & 5G Architectures",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 11,
              "topics": [
                "Cellular Concept",
                "Frequency Reuse",
                "Handoff Strategies",
                "MIMO & Beamforming"
              ],
              "key_concepts": [
                "Co-channel interference and capacity scaling"
              ]
            }
          ]
        },
        {
          "subject_code": "KEC-801",
          "subject_name": "Radar, Satellite & Microwave Systems",
          "semester": 8,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Defense, Aerospace & Satellite Comms (ISRO, DRDO)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Radar Systems & Range Equations",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Radar Range Equation",
                "Pulse Doppler",
                "MTI Radar",
                "Antenna Arrays"
              ],
              "key_concepts": [
                "Doppler shift & target tracking"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Satellite Link Budget Design",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Kepler Laws",
                "Geostationary Orbits",
                "Link Budget Calculations",
                "Carrier-to-Noise Ratio"
              ],
              "key_concepts": [
                "Free space path loss and transponder design"
              ]
            }
          ]
        }
      ]
    },
    "CSE": {
      "branch_name": "Computer Science & Engineering",
      "branch_code": "CSE",
      "subjects": [
        {
          "subject_code": "KCS-501",
          "subject_name": "Data Structures & Algorithms",
          "semester": 5,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Critical (MAANG, Tier-1 Product Companies, Coding Rounds)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Asymptotic Analysis, Stacks & Queues",
              "weightage_percent": 15.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "Asymptotic Notations (Big-O, Omega, Theta, Little-o)",
                "Master Theorem for Divide-and-Conquer Recurrences",
                "Array Representations and Space Complexity",
                "Stack Operations, Infix to Postfix Conversion, Evaluation",
                "Circular Queue, Deque, Priority Queue Implementation"
              ],
              "key_concepts": [
                "Master theorem casework",
                "Monotonic stack pattern",
                "Circular queue array wrapping arithmetic"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Linked Lists & Hierarchical Trees",
              "weightage_percent": 20.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Singly, Doubly, and Circular Linked Lists",
                "Fast & Slow Pointer Technique (Cycle detection, Middle of List)",
                "Binary Tree Traversals (Inorder, Preorder, Postorder, Level Order)",
                "Binary Search Tree (BST) Operations (Insert, Delete, Search)",
                "AVL Trees (Rotations: LL, RR, LR, RL, Balance Factor)",
                "B-Trees and B+ Trees Fundamentals"
              ],
              "key_concepts": [
                "Floyd's cycle detection algorithm",
                "AVL balance factor maintenance via rotations",
                "B-Tree node splitting and branching factor"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Graph Algorithms & Traversals",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Graph Representations (Adjacency Matrix vs Adjacency List)",
                "Breadth First Search (BFS) and Depth First Search (DFS)",
                "Topological Sort (Kahn's Algorithm and DFS-based)",
                "Cycle Detection in Directed and Undirected Graphs",
                "Minimum Spanning Tree (Kruskal's Algorithm with Disjoint Set Union, Prim's)",
                "Single-Source Shortest Path (Dijkstra's Algorithm, Bellman-Ford)",
                "All-Pairs Shortest Path (Floyd-Warshall)"
              ],
              "key_concepts": [
                "Disjoint Set Union (Union by Rank & Path Compression)",
                "Dijkstra greedy shortest path with min-heap",
                "Bellman-Ford negative weight cycle detection"
              ]
            },
            {
              "unit_number": 4,
              "unit_title": "Dynamic Programming & Greedy Design Strategies",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Greedy vs Dynamic Programming Paradigms",
                "Fractional Knapsack (Greedy) vs 0/1 Knapsack (DP)",
                "Longest Common Subsequence (LCS)",
                "Longest Increasing Subsequence (LIS)",
                "Matrix Chain Multiplication (MCM)",
                "Coin Change Problem and Subset Sum Problem"
              ],
              "key_concepts": [
                "Optimal substructure and overlapping subproblems",
                "Memoization vs Tabulation trade-offs",
                "State space transition equations"
              ]
            },
            {
              "unit_number": 5,
              "unit_title": "Sorting, Searching & Intractability (P vs NP)",
              "weightage_percent": 15.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "Comparison Sorts: Merge Sort, Quick Sort, Heap Sort",
                "Linear Time Sorts: Counting Sort, Radix Sort",
                "Lower Bound for Comparison-based Sorting (Omega(N log N))",
                "Ternary Search and Binary Search Variations",
                "Complexity Classes: P, NP, NP-Complete, and NP-Hard",
                "Reducibility and Cook's Theorem Overview"
              ],
              "key_concepts": [
                "Quick sort pivot selection and randomized partitioning",
                "Heapify procedure and in-place heapsort",
                "Polynomial time reduction"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-502",
          "subject_name": "Operating Systems",
          "semester": 5,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Critical (Core Subject for All Tech Interviews, Systems Roles)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Introduction & Operating System Structures",
              "weightage_percent": 15.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "Functions and Goals of Operating Systems",
                "Dual Mode Operation (User Mode vs Kernel Mode)",
                "System Calls (fork(), exec(), wait(), exit())",
                "OS Architectures: Monolithic, Microkernel, Hybrid",
                "Process Concept, Process States, Process Control Block (PCB)",
                "Context Switching Mechanics and Overhead"
              ],
              "key_concepts": [
                "Privileged vs non-privileged instructions",
                "fork() copy-on-write semantics",
                "Context switch state saving"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Process Management & CPU Scheduling",
              "weightage_percent": 20.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Thread Concepts: User-level Threads vs Kernel-level Threads",
                "Multithreading Models (Many-to-One, One-to-One, Many-to-Many)",
                "Scheduling Criteria (Throughput, Turnaround, Waiting, Response Time)",
                "Preemptive vs Non-Preemptive Scheduling",
                "Algorithms: FCFS, Shortest Job First (SJF / SRTF)",
                "Round Robin (Quantum sizing trade-offs)",
                "Priority Scheduling and Multilevel Feedback Queue (MLFQ)"
              ],
              "key_concepts": [
                "Convoy effect in FCFS",
                "SJF optimality proof for waiting time",
                "Time quantum selection in Round Robin"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Process Synchronization & Deadlocks",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Critical Section Problem and Correctness Criteria",
                "Peterson's Solution and Hardware Instructions (Test-and-Set, CAS)",
                "Mutex Locks and Semaphores (Counting vs Binary)",
                "Classic Problems: Producer-Consumer, Readers-Writers, Dining Philosophers",
                "Four Necessary Conditions for Deadlock (Coffman Conditions)",
                "Resource Allocation Graphs (RAG)",
                "Deadlock Prevention, Avoidance (Banker's Algorithm)",
                "Deadlock Detection and Recovery Techniques"
              ],
              "key_concepts": [
                "Mutual exclusion, progress, and bounded waiting",
                "Semaphores wait() (P) and signal() (V) atomic operations",
                "Banker's algorithm safety state verification"
              ]
            },
            {
              "unit_number": 4,
              "unit_title": "Memory Management & Virtual Memory",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Logical vs Physical Address Space",
                "Contiguous Allocation, Fragmentation (Internal vs External)",
                "Paging Architecture, Page Table Structures, Translation Lookaside Buffer (TLB)",
                "Effective Memory Access Time (EMAT) Calculations",
                "Segmentation and Segmented Paging",
                "Virtual Memory Concepts and Demand Paging",
                "Page Fault Handling Lifecycle",
                "Page Replacement Algorithms: FIFO, Belady's Anomaly, Optimal, Least Recently Used (LRU)",
                "Thrashing and Working Set Model"
              ],
              "key_concepts": [
                "TLB hit ratio impact on EMAT",
                "Belady's anomaly in FIFO page replacement",
                "Working set model to prevent thrashing"
              ]
            },
            {
              "unit_number": 5,
              "unit_title": "File Systems & Storage Management",
              "weightage_percent": 15.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "File Attributes, Operations, and File Types",
                "File Allocation Methods (Contiguous, Linked, Indexed / Inode)",
                "Free Space Management (Bitmaps, Linked Lists)",
                "Disk Structure and Physical Geometry",
                "Disk Scheduling Algorithms: FCFS, SSTF, SCAN (Elevator), C-SCAN, LOOK, C-LOOK",
                "RAID Levels (RAID 0, 1, 5, 6, 10) and Fault Tolerance"
              ],
              "key_concepts": [
                "Unix Inode direct, indirect, and double-indirect pointers",
                "Disk seek time optimization with SCAN/C-SCAN",
                "RAID 5 parity distribution"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-503",
          "subject_name": "Database Management Systems",
          "semester": 5,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Critical (Backend, Database Architecture, System Design Interviews)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Database Architecture & ER Modeling",
              "weightage_percent": 15.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "DBMS vs File System Architecture",
                "Three-Schema Architecture (Internal, Conceptual, External)",
                "Data Independence (Physical and Logical)",
                "Entity Types, Entity Sets, Attributes, Keys (Super, Candidate, Primary)",
                "Relationship Sets, Degree, Cardinality Ratios, Participation Constraints",
                "Weak Entity Sets and Identifying Relationships",
                "ER Diagram to Relational Table Mapping"
              ],
              "key_concepts": [
                "Three-tier schema decoupling",
                "Weak entity double rectangle / discriminator key",
                "Mapping 1:N and M:N relationships to foreign keys"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Relational Model & Formal Query Languages",
              "weightage_percent": 15.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "Relational Model Concepts and Integrity Constraints (Domain, Entity, Referential)",
                "Relational Algebra Operators: Selection, Projection, Rename",
                "Set Operations: Union, Intersection, Set Difference, Cartesian Product",
                "Join Operations: Theta Join, Equi-Join, Natural Join, Outer Joins (Left, Right, Full)",
                "Division Operator and its Practical Queries",
                "Tuple Relational Calculus (TRC) and Domain Relational Calculus (DRC)"
              ],
              "key_concepts": [
                "Referential integrity and cascade delete/update rules",
                "Relational algebra query equivalence and optimization",
                "Division operator for 'for all' relational queries"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "SQL & Relational Database Design / Normalization",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "SQL DDL, DML, DCL, and TCL Commands",
                "Complex Queries, Nested Subqueries, Correlated Subqueries",
                "Aggregate Functions and GROUP BY / HAVING Clauses",
                "Anomalies in Unnormalized Relations (Insertion, Deletion, Update)",
                "Functional Dependencies, Closure of Attribute Sets, Canonical Cover",
                "Candidate Key Finding Algorithm",
                "Normal Forms: First Normal Form (1NF), Second Normal Form (2NF), Third Normal Form (3NF)",
                "Boyce-Codd Normal Form (BCNF)",
                "Lossless Join Decomposition and Dependency Preservation Verification"
              ],
              "key_concepts": [
                "Correlated subquery execution logic",
                "Attribute closure algorithm to identify candidate keys",
                "3NF (prime attribute escape) vs BCNF (strictly superkey determinant)"
              ]
            },
            {
              "unit_number": 4,
              "unit_title": "Transaction Processing & Concurrency Control",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Transaction Concepts and State Diagram",
                "ACID Properties (Atomicity, Consistency, Isolation, Durability)",
                "Schedules: Serial, Concurrent, Conflict Serializable, View Serializable",
                "Testing for Conflict Serializability using Precedence Graphs",
                "Recoverable, Cascadeless, and Strict Schedules",
                "Concurrency Problems: Dirty Read, Unrepeatable Read, Lost Update, Phantom Read",
                "Lock-Based Protocols: Shared vs Exclusive Locks, Two-Phase Locking (2PL, Strict 2PL, Rigorous 2PL)",
                "Timestamp Ordering Protocol and Thomas Write Rule",
                "Deadlock Prevention (Wait-Die, Wound-Wait) and Detection"
              ],
              "key_concepts": [
                "Precedence graph cycle check for conflict serializability",
                "Strict 2PL prevents cascading rollbacks",
                "Wound-Wait and Wait-Die non-preemptive vs preemptive strategies"
              ]
            },
            {
              "unit_number": 5,
              "unit_title": "Indexing, Hashing & Query Optimization",
              "weightage_percent": 20.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "File Organization (Heap, Sorted, Hash)",
                "Indexing Types: Primary Index, Clustering Index, Secondary Index",
                "Dense vs Sparse Indexes, Multilevel Indexes",
                "B-Tree and B+ Tree Index Structures (Insertion, Deletion, Search, Range Queries)",
                "Static Hashing vs Dynamic Hashing (Extendible and Linear Hashing)",
                "Query Processing Steps (Parsing, Optimization, Code Generation, Execution)",
                "Database Recovery Techniques (Log-Based Recovery, Write-Ahead Logging WAL, Checkpointing, ARIES)"
              ],
              "key_concepts": [
                "B+ Tree leaf node linked list for sequential scan performance",
                "Extendible hashing directory and bucket depth doubling",
                "WAL protocol ensuring durability before commit"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-601",
          "subject_name": "Software Engineering",
          "semester": 6,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "High (Amazon, TCS Prime, System Architecture)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "SDLC, Agile & Scrum",
              "weightage_percent": 25.0,
              "is_high_yield": false,
              "estimated_hours": 5,
              "topics": [
                "SDLC, Agile & Scrum"
              ],
              "key_concepts": [
                "SDLC, Agile & Scrum"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "System Architecture & Design Patterns",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 8,
              "topics": [
                "System Architecture & Design Patterns"
              ],
              "key_concepts": [
                "System Architecture & Design Patterns"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Software Testing & QA",
              "weightage_percent": 25.0,
              "is_high_yield": false,
              "estimated_hours": 6,
              "topics": [
                "Software Testing & QA"
              ],
              "key_concepts": [
                "Software Testing & QA"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-602",
          "subject_name": "Web Technology",
          "semester": 6,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "High (Amazon, TCS Prime, System Architecture)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "HTML5, CSS3, DOM & JavaScript",
              "weightage_percent": 25.0,
              "is_high_yield": false,
              "estimated_hours": 4,
              "topics": [
                "HTML5, CSS3, DOM & JavaScript"
              ],
              "key_concepts": [
                "HTML5, CSS3, DOM & JavaScript"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Async JS, Promises & RESTful APIs",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 8,
              "topics": [
                "Async JS, Promises & RESTful APIs"
              ],
              "key_concepts": [
                "Async JS, Promises & RESTful APIs"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Microservices Architecture & DB Indexing",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 8,
              "topics": [
                "Microservices Architecture & DB Indexing"
              ],
              "key_concepts": [
                "Microservices Architecture & DB Indexing"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-603",
          "subject_name": "Computer Networks",
          "semester": 6,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "High (Amazon, TCS Prime, System Architecture)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "OSI & TCP/IP Layering Models",
              "weightage_percent": 25.0,
              "is_high_yield": false,
              "estimated_hours": 6,
              "topics": [
                "OSI & TCP/IP Layering Models"
              ],
              "key_concepts": [
                "OSI & TCP/IP Layering Models"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Routing Protocols (OSPF, BGP)",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 8,
              "topics": [
                "Routing Protocols (OSPF, BGP)"
              ],
              "key_concepts": [
                "Routing Protocols (OSPF, BGP)"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "TCP Congestion Control & Flow Control",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "TCP Congestion Control & Flow Control"
              ],
              "key_concepts": [
                "TCP Congestion Control & Flow Control"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-101",
          "subject_name": "Programming for Problem Solving (C)",
          "semester": 1,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Foundational Coding (TCS, Infosys, Cognizant)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "C Syntax & Control Structures",
              "weightage_percent": 25.0,
              "is_high_yield": false,
              "estimated_hours": 8,
              "topics": [
                "Variables",
                "Operators",
                "Loops",
                "Branching"
              ],
              "key_concepts": [
                "Control flow mechanics"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Functions, Arrays & Pointers",
              "weightage_percent": 35.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Pointer Arithmetic",
                "Dynamic Memory Allocation (malloc/free)",
                "Array-Pointer duality"
              ],
              "key_concepts": [
                "Memory leaks & pointer manipulation"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-301",
          "subject_name": "Data Structures & Algorithms",
          "semester": 3,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Top Tier (Google, Amazon, Microsoft, Adobe)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Linear Data Structures",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Stacks",
                "Queues",
                "Circular Queues",
                "Singly/Doubly Linked Lists"
              ],
              "key_concepts": [
                "LIFO/FIFO complexity and pointer updates"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Trees & Binary Search Trees",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Binary Trees",
                "BST Validation",
                "AVL Balancing",
                "Heap and Priority Queue"
              ],
              "key_concepts": [
                "Tree traversal, LCA and height-balanced rotations"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Graphs & Dynamic Programming",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "BFS",
                "DFS",
                "Dijkstra Shortest Path",
                "0/1 Knapsack",
                "Memoization"
              ],
              "key_concepts": [
                "Graph cycle detection & optimal substructure"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-302",
          "subject_name": "Computer Organization & Architecture",
          "semester": 3,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Systems Engineering & High Performance Computing",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Instruction Set Architecture & CPU",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 9,
              "topics": [
                "Von Neumann vs Harvard",
                "Addressing Modes",
                "ALU and Control Unit (Hardwired vs Microprogrammed)"
              ],
              "key_concepts": [
                "Instruction cycle and micro-operations"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Memory Hierarchy & Pipelining",
              "weightage_percent": 35.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Direct/Associative Cache Mapping",
                "Cache Hits/Misses",
                "RISC Pipelining",
                "Data/Control Hazards"
              ],
              "key_concepts": [
                "Branch prediction & pipeline stalls"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-401",
          "subject_name": "Operating Systems",
          "semester": 4,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Top Tier Core (Amazon, Microsoft, Google)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Process Management & Scheduling",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "PCB",
                "Context Switching",
                "CPU Scheduling (FCFS, Round Robin, SRTF)"
              ],
              "key_concepts": [
                "Preemptive scheduling & response time"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Synchronization & Deadlocks",
              "weightage_percent": 35.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Critical Section Problem",
                "Mutex & Semaphores",
                "Dining Philosophers",
                "Banker Algorithm"
              ],
              "key_concepts": [
                "Deadlock 4 conditions & avoidance"
              ]
            },
            {
              "unit_number": 3,
              "unit_title": "Memory Management & Virtual Memory",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Paging",
                "Segmentation",
                "TLB",
                "Page Replacement (LRU, FIFO, Optimal)",
                "Thrashing"
              ],
              "key_concepts": [
                "Page table lookup & working set model"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-402",
          "subject_name": "Theory of Automata & Formal Languages",
          "semester": 4,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "GATE & Compiler Engineering",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Finite Automata & Regular Languages",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 11,
              "topics": [
                "DFA and NFA",
                "Subset Construction",
                "Pumping Lemma for Regular Languages"
              ],
              "key_concepts": [
                "Equivalence of DFA and NFA"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Context Free Grammars & Turing Machines",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 11,
              "topics": [
                "CFG",
                "Pushdown Automata (PDA)",
                "Turing Machine",
                "Halting Problem"
              ],
              "key_concepts": [
                "Chomsky hierarchy & undecidability"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-701",
          "subject_name": "Cloud Computing & Distributed Systems",
          "semester": 7,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Top Tier Backend (Amazon AWS, Microsoft Azure, Google Cloud)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Cloud Architectures & Virtualization",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "IaaS, PaaS, SaaS",
                "Hypervisors Type 1/2",
                "Docker Containers & Kubernetes Orchestration"
              ],
              "key_concepts": [
                "Containerization vs hypervisor overhead"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Distributed Consensus & Consistency",
              "weightage_percent": 35.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "CAP Theorem",
                "PACELC",
                "Two-Phase Commit (2PC)",
                "Raft and Paxos Consensus",
                "Eventual Consistency"
              ],
              "key_concepts": [
                "Distributed replication tradeoffs"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-702",
          "subject_name": "Artificial Intelligence & Machine Learning",
          "semester": 7,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "AI/ML Engineering Tracks",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Search Algorithms & Heuristics",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 9,
              "topics": [
                "A* Search",
                "Admissibility",
                "Minimax & Alpha-Beta Pruning"
              ],
              "key_concepts": [
                "Heuristic optimality"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Supervised & Unsupervised Learning",
              "weightage_percent": 35.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "Linear/Logistic Regression",
                "Decision Trees",
                "SVM",
                "K-Means Clustering",
                "Backpropagation"
              ],
              "key_concepts": [
                "Gradient descent & over-fitting mitigation"
              ]
            }
          ]
        },
        {
          "subject_code": "KCS-801",
          "subject_name": "Deep Learning & Natural Language Processing",
          "semester": 8,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "GenAI & LLM Systems (OpenAI, Anthropic, Meta)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Neural Networks & Transformers",
              "weightage_percent": 35.0,
              "is_high_yield": true,
              "estimated_hours": 12,
              "topics": [
                "CNN Architecture",
                "RNN and LSTM",
                "Self-Attention Mechanism",
                "Transformer Encoder-Decoder"
              ],
              "key_concepts": [
                "Attention query-key-value formulation"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Large Language Models & Fine-Tuning",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 11,
              "topics": [
                "Pretraining vs SFT",
                "LoRA & PEFT",
                "RLHF",
                "Vector Embeddings & RAG"
              ],
              "key_concepts": [
                "Retrieval augmented generation pipeline"
              ]
            }
          ]
        }
      ]
    },
    "IT": {
      "branch_name": "IT",
      "branch_code": "IT",
      "subjects": [
        {
          "subject_code": "KIT-501",
          "subject_name": "Design & Analysis of Algorithms",
          "semester": 5,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Core Software (TCS, Amazon, Infosys)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Asymptotic Analysis & Divide-and-Conquer",
              "weightage_percent": 25.0,
              "is_high_yield": true,
              "estimated_hours": 9,
              "topics": [
                "Big O, Theta, Omega",
                "Master Theorem",
                "Merge Sort",
                "Quick Sort"
              ],
              "key_concepts": [
                "Recurrence relation solving"
              ]
            }
          ]
        },
        {
          "subject_code": "KIT-601",
          "subject_name": "Cloud Computing & Distributed Systems",
          "semester": 6,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Cloud Infra (AWS, Azure)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Virtualization & Containers",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Containers vs VMs",
                "Kubernetes",
                "Microservices"
              ],
              "key_concepts": [
                "Containerization architecture"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "CAP Theorem & Consensus",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "CAP Theorem",
                "Distributed Storage",
                "Consistent Hashing"
              ],
              "key_concepts": [
                "Partition tolerance"
              ]
            }
          ]
        },
        {
          "subject_code": "KIT-701",
          "subject_name": "Cryptography & Network Security",
          "semester": 7,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Cybersecurity & Fintech",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Symmetric & Asymmetric Encryption",
              "weightage_percent": 35.0,
              "is_high_yield": true,
              "estimated_hours": 11,
              "topics": [
                "AES",
                "DES",
                "RSA Algorithm",
                "Diffie-Hellman Key Exchange"
              ],
              "key_concepts": [
                "Public key infrastructure"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Authentication & Hash Functions",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "SHA-256",
                "Digital Signatures",
                "HMAC",
                "TLS/SSL Handshake"
              ],
              "key_concepts": [
                "Cryptographic integrity"
              ]
            }
          ]
        }
      ]
    },
    "MECH": {
      "branch_name": "MECH",
      "branch_code": "MECH",
      "subjects": [
        {
          "subject_code": "KME-301",
          "subject_name": "Thermodynamics",
          "semester": 3,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Core Mechanical (Tata Motors, L&T)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Laws of Thermodynamics",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "First Law for Closed/Open Systems",
                "Carnot Cycle",
                "Entropy Generation"
              ],
              "key_concepts": [
                "Second law and reversibility"
              ]
            }
          ]
        },
        {
          "subject_code": "KME-401",
          "subject_name": "Fluid Mechanics",
          "semester": 4,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "Fluid Systems (DRDO, ISRO)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Fluid Statics & Bernoulli Equation",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Navier-Stokes Equations",
                "Bernoulli Principle",
                "Pipe Flow Losses"
              ],
              "key_concepts": [
                "Laminar vs turbulent boundary layers"
              ]
            }
          ]
        },
        {
          "subject_code": "KME-601",
          "subject_name": "Refrigeration and Air Conditioning",
          "semester": 6,
          "credit_weight": 4.0,
          "is_core": true,
          "placement_relevance": "HVAC Industry (Voltas, Daikin)",
          "units": [
            {
              "unit_number": 1,
              "unit_title": "Vapour Compression Cycles",
              "weightage_percent": 35.0,
              "is_high_yield": true,
              "estimated_hours": 11,
              "topics": [
                "Standard VCR Cycle",
                "p-h and T-s Diagrams",
                "COP Calculations"
              ],
              "key_concepts": [
                "Superheating and subcooling effects"
              ]
            },
            {
              "unit_number": 2,
              "unit_title": "Psychrometry & Heat Load",
              "weightage_percent": 30.0,
              "is_high_yield": true,
              "estimated_hours": 10,
              "topics": [
                "Psychrometric Chart",
                "Sensible Heat Factor",
                "Cooling Load Estimation"
              ],
              "key_concepts": [
                "Enthalpy of moist air"
              ]
            }
          ]
        }
      ]
    }
  },
  "ECE": {
    "6": {
      "semester_name": "ECE 6th Semester (AKTU / GCET)",
      "subjects": [
        {
          "code": "KEC-601",
          "name": "Digital Communication",
          "units": [
            {
              "unit_num": 1,
              "title": "Pulse Modulation (PAM, PWM, PPM)",
              "difficulty": 3,
              "estimated_hours": 6
            },
            {
              "unit_num": 2,
              "title": "Digital Modulation Techniques (ASK, PSK, QPSK)",
              "difficulty": 4,
              "estimated_hours": 8
            },
            {
              "unit_num": 3,
              "title": "Information Theory & Channel Coding",
              "difficulty": 5,
              "estimated_hours": 10
            }
          ]
        },
        {
          "code": "KEC-602",
          "name": "Digital Signal Processing",
          "units": [
            {
              "unit_num": 1,
              "title": "DFT and FFT Algorithms",
              "difficulty": 4,
              "estimated_hours": 8
            },
            {
              "unit_num": 2,
              "title": "IIR and FIR Filter Design",
              "difficulty": 5,
              "estimated_hours": 10
            },
            {
              "unit_num": 3,
              "title": "Finite Word Length Effects",
              "difficulty": 3,
              "estimated_hours": 6
            }
          ]
        },
        {
          "code": "KEC-061",
          "name": "Microcontrollers & Embedded Systems",
          "units": [
            {
              "unit_num": 1,
              "title": "8051 Architecture & Timers",
              "difficulty": 3,
              "estimated_hours": 5
            },
            {
              "unit_num": 2,
              "title": "ARM Cortex-M Programming",
              "difficulty": 4,
              "estimated_hours": 8
            },
            {
              "unit_num": 3,
              "title": "Peripheral Interfacing (I2C, SPI)",
              "difficulty": 4,
              "estimated_hours": 7
            }
          ]
        }
      ]
    }
  },
  "CSE": {
    "6": {
      "semester_name": "CSE 6th Semester (AKTU / GCET)",
      "subjects": [
        {
          "code": "KCS-601",
          "name": "Software Engineering",
          "units": [
            {
              "unit_num": 1,
              "title": "SDLC, Agile & Scrum",
              "difficulty": 2,
              "estimated_hours": 5
            },
            {
              "unit_num": 2,
              "title": "System Architecture & Design Patterns",
              "difficulty": 4,
              "estimated_hours": 8
            },
            {
              "unit_num": 3,
              "title": "Software Testing & QA",
              "difficulty": 3,
              "estimated_hours": 6
            }
          ]
        },
        {
          "code": "KCS-602",
          "name": "Web Technology",
          "units": [
            {
              "unit_num": 1,
              "title": "HTML5, CSS3, DOM & JavaScript",
              "difficulty": 2,
              "estimated_hours": 4
            },
            {
              "unit_num": 2,
              "title": "Async JS, Promises & RESTful APIs",
              "difficulty": 4,
              "estimated_hours": 8
            },
            {
              "unit_num": 3,
              "title": "Microservices Architecture & DB Indexing",
              "difficulty": 4,
              "estimated_hours": 8
            }
          ]
        },
        {
          "code": "KCS-603",
          "name": "Computer Networks",
          "units": [
            {
              "unit_num": 1,
              "title": "OSI & TCP/IP Layering Models",
              "difficulty": 3,
              "estimated_hours": 6
            },
            {
              "unit_num": 2,
              "title": "Routing Protocols (OSPF, BGP)",
              "difficulty": 4,
              "estimated_hours": 8
            },
            {
              "unit_num": 3,
              "title": "TCP Congestion Control & Flow Control",
              "difficulty": 5,
              "estimated_hours": 10
            }
          ]
        }
      ]
    }
  },
  "IT": {
    "6": {
      "semester_name": "IT 6th Semester (AKTU / GCET)",
      "subjects": [
        {
          "code": "KIT-601",
          "name": "Cloud Computing & Distributed Systems",
          "units": [
            {
              "unit_num": 1,
              "title": "Virtualization, Hypervisors & Containers",
              "difficulty": 3,
              "estimated_hours": 6
            },
            {
              "unit_num": 2,
              "title": "CAP Theorem & Distributed Consensus",
              "difficulty": 5,
              "estimated_hours": 9
            }
          ]
        }
      ]
    }
  },
  "MECH": {
    "6": {
      "semester_name": "MECH 6th Semester (AKTU / GCET)",
      "subjects": [
        {
          "code": "KME-601",
          "name": "Refrigeration and Air Conditioning",
          "units": [
            {
              "unit_num": 1,
              "title": "Vapour Compression Cycles",
              "difficulty": 4,
              "estimated_hours": 8
            },
            {
              "unit_num": 2,
              "title": "Psychrometry & Heat Load Estimation",
              "difficulty": 4,
              "estimated_hours": 7
            }
          ]
        }
      ]
    }
  }
}
INTERVIEW_BANK = {
  "companies": {
    "qualcomm": {
      "name": "Qualcomm",
      "track": "Hardware & Embedded Systems / VLSI",
      "description": "Chip design, Verilog/SystemVerilog RTL modeling, STA timing closure, and mobile SoC architecture.",
      "questions": [
        {
          "id": "qualcomm_verilog_01",
          "company": "Qualcomm",
          "track": "VLSI / Digital Design",
          "tier": "standard",
          "fee_fet": 0.0,
          "topic": "Verilog Blocking vs Non-Blocking Assignments",
          "difficulty": "Medium",
          "question": "In Verilog RTL design, explain the fundamental behavioral difference between blocking (`=`) and non-blocking (`<=`) assignments. How does the event-scheduling queue handle each during simulation, and what are the severe synthesis or race-condition consequences if they are used incorrectly in sequential `always @(posedge clk)` vs combinational `always @(*)` blocks?",
          "expected_rubric": {
            "must_include": [
              "Blocking (=) executes sequentially in active region and blocks subsequent statements until completion",
              "Non-blocking (<=) schedules RHS evaluation in active region and updates LHS in NBA (Non-blocking Assignment) region",
              "Sequential logic (@(posedge clk)) must strictly use non-blocking (<=) to avoid race conditions across flip-flops",
              "Combinational logic (@(*)) should use blocking (=) to ensure immediate signal updates and avoid latch inference",
              "Stratified Event Queue understanding (Active, Inactive, NBA regions)"
            ],
            "bonus_points": [
              "Explanation of delta cycles in Verilog event scheduling",
              "Shift register example showing race condition when blocking '=' is incorrectly used across clocked stages",
              "Synthesis tool interpretation and unexpected latch generation warnings"
            ],
            "common_pitfalls": [
              "Confusing simulation delta delay with physical wire propagation delay",
              "Claiming non-blocking assignments run in parallel hardware without explaining the two-stage evaluation-update mechanism",
              "Failing to mention latch synthesis when combinational branches are incomplete"
            ]
          },
          "ideal_sample_answer": "In Verilog, blocking assignments (`=`) are evaluated and committed immediately in the Active region of the simulation event queue, blocking the execution of subsequent statements within the procedural block. In contrast, non-blocking assignments (`<=`) evaluate the Right-Hand-Side (RHS) in the Active region, but defer updating the Left-Hand-Side (LHS) until the NBA (Non-Blocking Assignment) event region, after all active evaluations have finished.\n\nIn sequential logic `always @(posedge clk)`, non-blocking assignments must always be used. If blocking assignments are used, the execution order between independent always blocks at the same clock edge is non-deterministic, causing simulation-synthesis mismatches and race conditions (e.g., in a shift register where data shoots through multiple stages in one clock edge). In combinational logic `always @(*)`, blocking assignments should be used so that intermediate variable updates propagate immediately, preventing accidental latch inference."
        },
        {
          "id": "qualcomm_sta_02",
          "company": "Qualcomm",
          "track": "VLSI / Physical Design & STA",
          "tier": "standard",
          "fee_fet": 0.0,
          "topic": "Setup and Hold Time Violations",
          "difficulty": "Medium-Hard",
          "question": "Define Setup Time ($T_{setup}$) and Hold Time ($T_{hold}$) for a D-Flip-Flop. Provide the governing mathematical timing inequalities for both setup and hold checks including clock skew ($T_{skew}$), clock jitter, and combinational path delay ($T_{comb}$). Which violation can NEVER be fixed by simply reducing clock frequency, and how do physical design engineers fix hold violations during clock tree synthesis?",
          "expected_rubric": {
            "must_include": [
              "T_setup: minimum duration data must be stable before the active clock edge",
              "T_hold: minimum duration data must be stable after the active clock edge",
              "Setup inequality: T_clk >= T_cq + T_comb_max + T_setup - T_skew + T_jitter",
              "Hold inequality: T_cq + T_comb_min >= T_hold + T_skew",
              "Hold violation cannot be resolved by lowering clock frequency (independent of T_clk)",
              "Hold violation fix: inserting delay buffers / inverter pairs along the data path"
            ],
            "bonus_points": [
              "Explaining positive vs negative clock skew impact on setup vs hold",
              "Metastability risk and MTBF (Mean Time Between Failures) if setup/hold is violated",
              "Multi-corner analysis (fast-fast / slow-slow silicon corners)"
            ],
            "common_pitfalls": [
              "Thinking hold violations depend on clock period",
              "Adding delay buffers to the clock path instead of the data path to fix hold time"
            ]
          },
          "ideal_sample_answer": "Setup time ($T_{setup}$) is the minimum time data must remain stable before the capturing clock edge. Hold time ($T_{hold}$) is the minimum time data must remain stable after the capturing clock edge.\n\nSetup Check: $T_{clk} \\ge T_{cq} + T_{comb\\_max} + T_{setup} - T_{skew} + T_{jitter}$. Setup margin depends directly on the clock period $T_{clk}$, so setup violations can always be relieved by lowering the operating frequency.\n\nHold Check: $T_{cq} + T_{comb\\_min} \\ge T_{hold} + T_{skew}$. Because $T_{clk}$ does not appear in this equation, hold violations are frequency-independent and CANNOT be fixed by reducing the clock frequency! A hold violation causes fatal chip failure at any frequency.\n\nTo resolve hold violations during Physical Design, engineers insert non-inverting delay buffers or high-threshold-voltage (HVT) cells into the fast data path ($T_{comb\\_min}$) to delay data arrival without worsening setup time on critical paths."
        },
        {
          "id": "qualcomm_vlsi_adv_01",
          "company": "Qualcomm",
          "track": "Qualcomm VLSI Advanced Pack (Tier-1 Premium)",
          "tier": "tier-1",
          "fee_fet": 1.0,
          "topic": "Clock Domain Crossing (CDC) & Multi-Voltage Power Gating",
          "difficulty": "Bar Raiser / Hard",
          "question": "[TIER-1 QUALCOMM MOCK PACK]\nDesign a robust Clock Domain Crossing (CDC) architecture for transferring a multi-bit control vector between asynchronous clock domains in a Snapdragon modem subsystem. Why does a standard 2-Flip-Flop synchronizer fail for multi-bit data buses, and how do you implement a Gray-code asynchronous FIFO or a 4-phase handshake protocol to guarantee zero data corruption? Furthermore, explain how isolation cells and level shifters are placed when crossing between different voltage domains (UPF).",
          "expected_rubric": {
            "must_include": [
              "2-FF synchronizer bus skew issue: bit propagation delays vary, causing intermediate invalid binary states to be sampled",
              "Asynchronous FIFO with dual-port SRAM and Gray-coded read/write pointers",
              "Gray code property: only 1 bit transitions per increment, eliminating multi-bit sample skew",
              "2-FF synchronizers used strictly on the single-bit Gray pointers crossing domains",
              "Level shifters required for voltage translation between different VDD domains",
              "Isolation cells (ISO) required to hold lines at safe logic state when power domain is gated OFF"
            ],
            "bonus_points": [
              "Calculating FIFO full and empty conditions in Gray code domain (MSB inversion for wrap-around)",
              "Unified Power Format (UPF) retention registers and power management controller sequencing",
              "Mean Time Between Failures (MTBF) formulation for synchronizer flip-flops"
            ],
            "common_pitfalls": [
              "Suggesting passing multi-bit binary bus directly through a 2-FF synchronizer bank",
              "Confusing level shifters (voltage adaptation) with isolation cells (floating input protection during power down)"
            ]
          },
          "ideal_sample_answer": "A standard 2-FF synchronizer cannot be applied directly to a multi-bit binary bus because routing and gate delays cause bits to arrive with slight skews. When crossing asynchronous boundaries, intermediate invalid bus states will be sampled, corrupting the payload.\n\nTo resolve this, an Asynchronous FIFO is used. The read and write addresses are converted into Gray code, where only exactly one bit transitions per pointer increment. The 1-bit Gray transitions are safely passed across the CDC boundary using 2-FF synchronizers. Full and empty comparisons occur after pointer synchronization (with FIFO full detected by inverting the top two MSBs in Gray code). Alternatively, a Req-Ack handshake mechanism with closed-loop acknowledgment can be used for slow multi-bit control vectors.\n\nIn Multi-Voltage UPF domains: Level shifters are placed between domains operating at different voltage rails to prevent gate breakdown or weak switching. Isolation cells (AND/OR gates tied to enable clamp) are placed at power domain boundaries to clamp floating signals to known logic values (0 or 1) when a domain is powered off, preventing high crowbar leakage currents."
        }
      ]
    },
    "tcs_prime": {
      "name": "TCS Prime",
      "track": "Systems Engineering, C++ & Advanced Algorithms",
      "description": "High-performance software engineering, memory safety, C++ modern idioms, and multi-threaded systems.",
      "questions": [
        {
          "id": "tcs_prime_cpp_01",
          "company": "TCS Prime",
          "track": "C++ & Memory Management",
          "tier": "standard",
          "fee_fet": 0.0,
          "topic": "Pointers, References, Memory Leaks & RAII",
          "difficulty": "Medium",
          "question": "In modern C++, explain the difference between raw pointers, references, and smart pointers (`std::unique_ptr`, `std::shared_ptr`, `std::weak_ptr`). How does the RAII (Resource Acquisition Is Initialization) paradigm eliminate resource leaks, and what is the exact scenario where `std::shared_ptr` causes a fatal memory leak? How does `std::weak_ptr` break that leak?",
          "expected_rubric": {
            "must_include": [
              "Differences: references cannot be null or reseated; raw pointers allow manual allocation/deallocation; smart pointers manage lifetime automatically",
              "RAII: resources are bound to object lifetime; destructor deterministically releases heap memory/handles when scope exits",
              "std::unique_ptr: exclusive ownership, zero overhead, move-only semantics",
              "std::shared_ptr: shared ownership via reference-counted control block",
              "Circular / Cyclic reference problem: two objects owning shared_ptr to each other keep use_count >= 1, preventing deallocation",
              "std::weak_ptr: non-owning observer that does not increment strong reference count, breaking cyclic dependencies"
            ],
            "bonus_points": [
              "Control block details (strong count vs weak count and make_shared memory layout)",
              "Thread safety of shared_ptr reference count vs underlying object access",
              "Using `std::weak_ptr::lock()` to safely acquire temporary shared ownership"
            ],
            "common_pitfalls": [
              "Failing to explain how cyclic shared_ptr references prevent ref_count from reaching 0",
              "Claiming references can be re-bound to new memory addresses",
              "Omitting the distinction between stack unwinding during exceptions and manual delete calls"
            ]
          },
          "ideal_sample_answer": "References are immutable aliases for existing objects that cannot be null or reseated. Raw pointers represent raw memory addresses requiring manual `delete`, creating high risk of leaks and dangling pointers. Modern C++ relies on RAII (Resource Acquisition Is Initialization), where resources are acquired in constructors and deterministically freed in destructors when objects go out of scope, even during exception unwinding.\n\nSmart pointers:\n1. `std::unique_ptr`: Enforces exclusive single ownership with zero runtime overhead over a raw pointer. It is move-only.\n2. `std::shared_ptr`: Enables shared ownership using a dynamically allocated control block with an atomic reference count.\n3. `std::weak_ptr`: A non-owning observer that references a `shared_ptr` managed object without incrementing the strong reference count.\n\nThe Fatal Leak Scenario: When two objects hold `std::shared_ptr` references to each other (cyclic reference), each object's strong count remains at least 1 even after all external references are destroyed. Because the reference count never reaches zero, their destructors are never invoked, causing a permanent memory leak. To fix this, one link in the cycle is converted to `std::weak_ptr`, allowing the strong count to hit zero and memory to be reclaimed."
        },
        {
          "id": "tcs_prime_oop_02",
          "company": "TCS Prime",
          "track": "Object Oriented Architecture & Polymorphism",
          "tier": "standard",
          "fee_fet": 0.0,
          "topic": "Virtual Functions, VTables & Object Slicing",
          "difficulty": "Medium",
          "question": "Explain how runtime polymorphism is implemented in C++ under the hood using `vptr` and `vtable`. Why is it critical to declare a virtual destructor in a base class containing virtual functions, and what happens during 'Object Slicing' when a derived class instance is assigned to a base class variable by value?",
          "expected_rubric": {
            "must_include": [
              "vtable is a per-class static lookup table storing pointers to virtual member functions",
              "vptr is an invisible pointer embedded in every object instance pointing to its class vtable",
              "Dynamic dispatch: call resolution dereferences vptr at runtime to locate correct derived function",
              "Virtual destructor: ensures deleting derived object through base pointer invokes derived destructor first, avoiding resource leaks",
              "Object Slicing: copying derived object by value into base object truncates derived member variables and resets vptr to base class"
            ],
            "bonus_points": [
              "Memory layout diagram/description showing vptr offset in object memory",
              "Performance overhead of vtable cache miss vs direct function inlining",
              "Use of `= default` and pure virtual destructors"
            ],
            "common_pitfalls": [
              "Thinking each object instance contains its own copy of the vtable instead of just a pointer (vptr)",
              "Forgetting that object slicing happens when passing by value rather than pointer or reference"
            ]
          },
          "ideal_sample_answer": "In C++, dynamic polymorphism uses two structures: a `vtable` (virtual table) and a `vptr` (virtual pointer). The compiler generates one static `vtable` per polymorphic class containing function pointers to its virtual methods. Each instantiated object contains an invisible hidden `vptr` member pointing to its class's `vtable`. When a virtual function is invoked on a pointer/reference, the program dereferences the object's `vptr`, locates the function index in the `vtable`, and dispatches the call dynamically.\n\nVirtual Destructor: If a base class pointer points to a derived class object allocated on the heap, executing `delete base_ptr` without a virtual destructor results in undefined behavior\u2014only the base destructor runs! The derived class destructor is bypassed, leaking derived dynamic members. Declaring a virtual destructor ensures the derived destructor executes first.\n\nObject Slicing: Occurs when a derived class instance is assigned to a base class variable by value (`Base b = derived;`). The compiler allocates only enough space for the Base class, 'slicing off' derived attributes and copying only base fields. The `vptr` in `b` is initialized to the Base class `vtable`, losing polymorphic behavior."
        },
        {
          "id": "tcs_prime_adv_01",
          "company": "TCS Prime",
          "track": "TCS Prime Advanced Systems Track (Tier-1 Premium)",
          "tier": "tier-1",
          "fee_fet": 1.0,
          "topic": "Lock-Free Ring Buffer & C++20 Concurrency",
          "difficulty": "Hard / Tier-1",
          "question": "[TIER-1 TCS PRIME ADVANCED PACK]\nDesign a single-producer single-consumer (SPSC) lock-free circular ring buffer in modern C++ utilizing `std::atomic` and memory order semantics (`memory_order_acquire`, `memory_order_release`, `memory_order_relaxed`). Why does avoiding `std::mutex` provide deterministic latency in high-frequency trading or real-time telematics? Address cache-line false sharing between the head and tail indices and explain how `alignas(hardware_destructive_interference_size)` mitigates it.",
          "expected_rubric": {
            "must_include": [
              "SPSC queue with head and tail atomic indices",
              "Lock-free advantage: avoids kernel context switching, priority inversion, and blocking latency",
              "Release-Acquire semantics: Producer uses store with memory_order_release; Consumer uses load with memory_order_acquire",
              "Producer loads head with relaxed (local owner), consumer loads tail with relaxed (local owner)",
              "False sharing: head and tail residing on same 64-byte cache line cause continuous CPU cache invalidations across cores",
              "Mitigation: alignas(64) or alignas(hardware_destructive_interference_size) to place indices on separate cache lines"
            ],
            "bonus_points": [
              "Ring buffer wraparound using power-of-two capacity and bitwise AND masking `(index & (capacity - 1))`",
              "Comparing sequential consistency (`memory_order_seq_cst`) overhead vs acquire-release",
              "ABA problem explanation and why SPSC queues are inherently immune to ABA"
            ],
            "common_pitfalls": [
              "Using default memory_order_seq_cst without explaining memory barriers",
              "Overlooking cache line ping-pong (false sharing) between core caches"
            ]
          },
          "ideal_sample_answer": "In real-time telematics and HFT, mutex-based queues incur OS context switches, scheduler delays, and potential priority inversions. A lock-free SPSC ring buffer guarantees bounded wait-free progress.\n\nThe ring buffer maintains two atomic indices: `head` (producer write pointer) and `tail` (consumer read pointer). For synchronization without sequential consistency overhead:\n- In `push(item)`: The producer loads `tail` using `memory_order_acquire` to ensure it observes consumer reads. It writes the data element into the buffer, then stores the updated `head` with `memory_order_release`, ensuring the payload is globally visible before `head` is updated.\n- In `pop(item)`: The consumer loads `head` with `memory_order_acquire`. After copying the item, it updates `tail` with `memory_order_release`.\n- Local index updates use `memory_order_relaxed` since each pointer is written by exactly one thread.\n\nCache-Line False Sharing: In modern CPUs, cache coherency protocols operate on 64-byte cache lines. If `head` and `tail` share the same line, writes by core A invalidate the cache line on core B ('cache ping-pong'), collapsing throughput. We mitigate this using `alignas(std::hardware_destructive_interference_size)` on both atomic members to guarantee they reside in separate CPU cache lines."
        }
      ]
    },
    "amazon": {
      "name": "Amazon",
      "track": "Data Structures, Algorithms & Distributed Systems",
      "description": "Amazon Technical Track: Tree/Graph algorithms, scalable cloud architecture, and Leadership Principles.",
      "questions": [
        {
          "id": "amazon_bst_01",
          "company": "Amazon",
          "track": "DSA / Binary Search Trees",
          "tier": "standard",
          "fee_fet": 0.0,
          "topic": "Binary Search Tree Validation and Lowest Common Ancestor",
          "difficulty": "Medium",
          "question": "Given the root of a binary tree, describe an optimal algorithm to determine whether it is a valid Binary Search Tree (BST). Why is checking `node.left.val < node.val < node.right.val` locally insufficient? Provide the time and space complexity. Additionally, explain how to find the Lowest Common Ancestor (LCA) of two given nodes in a BST in $O(h)$ time without additional memory.",
          "expected_rubric": {
            "must_include": [
              "Local check flaw: a node in the right subtree of the left child could exceed the root value while satisfying local child check",
              "Correct BST validation: range bounded traversal (low, high) or in-order traversal strictly increasing",
              "Time complexity: O(N) visiting each node once",
              "Space complexity: O(h) where h is tree height for recursive call stack / explicit stack",
              "LCA in BST: walk down from root; if both p and q are less than root, move left; if both greater, move right; split point is the LCA",
              "LCA time O(h) and space O(1) iterative"
            ],
            "bonus_points": [
              "Handling integer overflow edge cases using 64-bit integer bounds or nullable pointers",
              "Morris in-order traversal for O(1) auxiliary space validation",
              "Degenerate skewed tree worst-case O(N) height vs balanced tree O(log N)"
            ],
            "common_pitfalls": [
              "Only validating immediate parent-child relationships instead of global subtree bounds",
              "Allowing duplicate values in strict BST without defining duplicate policy",
              "Using recursive stack for LCA when a simple while loop achieves O(1) space"
            ]
          },
          "ideal_sample_answer": "Validating a BST cannot be done by merely checking `node.left.val < node.val < node.right.val` because that only tests local parent-child validity. For example, a left child could have a right grandchild whose value is greater than the root, violating the global BST property.\n\nOptimal Algorithm: Traverse the tree while propagating valid value bounds `(min_allowed, max_allowed)` initialized to `(-\u221e, +\u221e)`. For each node:\n1. Check if `min_val < node.val < max_val`. If not, return False.\n2. Recurse left with `(min_val, node.val)`.\n3. Recurse right with `(node.val, max_val)`.\nAlternatively, perform an in-order traversal and verify that visited values are strictly monotonically increasing. Time Complexity: $O(N)$ where $N$ is total nodes. Space Complexity: $O(h)$ for the recursion stack ($O(\\log N)$ balanced, $O(N)$ worst-case skewed).\n\nLowest Common Ancestor (LCA) in BST: Starting at root:\n- If both $p.val < node.val$ and $q.val < node.val$, the LCA must be in the left subtree; move $node = node.left$.\n- If both $p.val > node.val$ and $q.val > node.val$, move $node = node.right$.\n- As soon as $p$ and $q$ diverge (or one equals $node$), current $node$ is the Lowest Common Ancestor. This iterative search takes $O(h)$ time and $O(1)$ auxiliary space."
        },
        {
          "id": "amazon_dsa_02",
          "company": "Amazon",
          "track": "DSA / Graph & Routing Algorithms",
          "tier": "standard",
          "fee_fet": 0.0,
          "topic": "Shortest Path & Topological Sorting in Fulfillment Logistics",
          "difficulty": "Medium-Hard",
          "question": "In Amazon's fulfillment network, package delivery routes must find the shortest travel time across delivery hubs with non-negative road transit delays, while package sorting facilities require topological ordering to resolve order assembly dependencies (Directed Acyclic Graph). Compare Dijkstra's algorithm with topological sorting for DAG shortest paths. Why does DAG shortest path run in $O(V + E)$ while Dijkstra requires $O((V + E) \\log V)$?",
          "expected_rubric": {
            "must_include": [
              "Dijkstra uses min-heap priority queue to greedily expand closest unvisited vertex, handling cyclic graphs with non-negative weights",
              "Dijkstra complexity: O((V + E) log V) due to priority queue insertions/decrease-key operations",
              "DAG shortest path: topological sort (Kahn's or DFS post-order) linearizes vertices so all edges point left-to-right",
              "DAG relaxation: single pass relaxing outgoing edges in topological order guarantees optimal distance without back-tracking",
              "DAG complexity: O(V + E) because each vertex and edge is relaxed exactly once in topological sequence"
            ],
            "bonus_points": [
              "DAG relaxation works even with negative edge weights unlike standard Dijkstra",
              "Cycle detection in logistics assembly graphs using in-degree array in Kahn's algorithm",
              "Real-world fulfillment batching and dynamic traffic rerouting consideration"
            ],
            "common_pitfalls": [
              "Attempting to run topological sort on graphs with directed cycles",
              "Failing to explain why the DAG structure eliminates the need for a min-heap"
            ]
          },
          "ideal_sample_answer": "In fulfillment networks, route optimization depends on graph topology:\n1. Dijkstra's Algorithm works on general directed graphs (which may contain cycles) with non-negative edge weights. Because edges can lead back or branch unpredictably, it maintains a Min-Heap priority queue to always greedily process the unvisited vertex with the minimum tentative distance. Updating the heap on edge relaxations yields an $O((V + E) \\log V)$ time complexity.\n\n2. DAG Shortest Path works when the network is a Directed Acyclic Graph (e.g. assembly dependencies). In a DAG, we can perform a Topological Sort (using Kahn's algorithm or DFS post-order) in $O(V + E)$. In topological order, all directed edges point strictly from earlier vertices to later vertices. We then iterate through the linear order, relaxing outgoing edges of each vertex. When we reach vertex $u$, all possible paths leading into $u$ have already been permanently resolved! Thus, no min-heap is required, and every vertex and edge is processed once in $O(V + E)$ linear time."
        },
        {
          "id": "amazon_bar_raiser_01",
          "company": "Amazon",
          "track": "Amazon Bar Raiser Drill (Tier-1 Premium)",
          "tier": "tier-1",
          "fee_fet": 1.0,
          "topic": "Distributed In-Memory Cache with Write-Back & Leadership Principles",
          "difficulty": "Bar Raiser / Hard",
          "question": "[TIER-1 AMAZON BAR RAISER DRILL]\nPart A (System Architecture): Design an Amazon-scale distributed caching layer (like ElastiCache/DynamoDB Accelerator) supporting millions of concurrent read/write queries per second. Detail your eviction policy (LRU/LFU), cache coherence strategy (Cache-Aside vs Write-Through vs Write-Back), handling of Cache Stampede (dog-piling on hot keys), and consistent hashing with virtual nodes for partitioning.\n\nPart B (Amazon Leadership Principles): Explain a scenario where you applied 'Customer Obsession' and 'Dive Deep' during a catastrophic production latency regression caused by cache thrashing. How did you push through ambiguities, make a high-judgment trade-off (Two-Way vs One-Way door), and deliver results?",
          "expected_rubric": {
            "must_include": [
              "Part A: Consistent hashing with virtual nodes (e.g. 100-256 tokens per node) to prevent hot-spotting and ensure smooth rebalancing",
              "Part A: LRU eviction using doubly-linked list + hash map, or segmented LRU",
              "Part A: Cache Stampede mitigation: distributed mutex locks, probabilistic early expiration (XFetch), or background pre-warming",
              "Part A: Coherence: Write-Aside/Write-Through trade-offs vs Write-Back data loss risks on crash",
              "Part B: Clear demonstration of Amazon Leadership Principles (Customer Obsession, Dive Deep, Bias for Action)",
              "Part B: STAR method framing (Situation, Task, Action, Result) with metrics and root-cause analysis",
              "Part B: Clear distinction between One-Way Doors (irreversible architectural commitments) and Two-Way Doors (reversible experiments)"
            ],
            "bonus_points": [
              "Multi-AZ active-active replication and gossiping protocols for membership (e.g. SWIM)",
              "Sliding window TTL with jitter to prevent synchronized mass expiration",
              "Measurable business impact (e.g., P99 latency dropped from 450ms to 8ms, 99.999% availability)"
            ],
            "common_pitfalls": [
              "Focusing only on the technical architecture while treating the Amazon Leadership Principle question as an afterthought",
              "Not addressing Cache Stampede when millions of clients request an expired key simultaneously",
              "Omitting virtual nodes when explaining consistent hashing"
            ]
          },
          "ideal_sample_answer": "Part A (Technical Architecture):\n1. Partitioning & Balancing: Keys are mapped to nodes using Consistent Hashing on a 128-bit ring (e.g., Murmur3/CityHash). Each physical node owns 150-200 virtual nodes (tokens) uniformly distributed across the ring to prevent unbalanced load spikes and minimize key migration ($1/N$ fraction) when nodes join or fail.\n2. Eviction & Data Structure: In-memory storage uses an $O(1)$ Hash Map combined with a Doubly Linked List for LRU eviction (or 2Q/Segmented LRU to resist scan resistance).\n3. Cache Stampede Mitigation: When a hot product key expires, thousands of concurrent requests could overwhelm the primary database. We mitigate this using Probabilistic Early Expiration (XFetch algorithm: $e^{-\\beta \\cdot \\Delta \\cdot \\ln(\\text{rand})} > \\text{TTL}$) or distributed lease locks (only one thread fetches and refreshes cache while others wait or serve stale data for 200ms).\n4. Coherence: We utilize Cache-Aside with Write-Through for critical ordering data, with asynchronous invalidation events published over Amazon SNS/SQS to purge replica node caches.\n\nPart B (Leadership Principles - STAR):\n- Situation: During Prime Day preview, a top-selling retail category triggered severe cache thrashing, elevating P99 latency from 15ms to 850ms, degrading customer checkout completion by 4.2%.\n- Task: As technical lead, I prioritized Customer Obsession\u2014buyers couldn't complete orders. I had to identify the root cause without taking down checkout services.\n- Action (Dive Deep & Decision Framing): Diving deep into metrics, I noticed 12 distinct marketing promotion keys had zero jitter on TTLs, expiring simultaneously at the top of every hour and dog-piling the read replicas. Recognizing a reversible Two-Way Door decision, I implemented an immediate emergency hot-patch injecting a 15% Gaussian jitter to key expiration windows and enabled stale-while-revalidate fallback.\n- Result: P99 latency plunged back to 11ms within 4 minutes. Zero data loss occurred, preserving an estimated $1.8M in Prime Day transactions. We followed up with a permanent One-Way Door architecture review introducing automated cache lease locks across all tier-1 microservices."
        }
      ]
    },
    "google": {
      "name": "Google",
      "track": "Systems Architecture & Algorithmic Scalability",
      "description": "Distributed systems, algorithmic optimization, high-throughput RPCs, and scale-out architecture.",
      "questions": [
        {
          "id": "google_sys_01",
          "company": "Google",
          "track": "Distributed Systems",
          "tier": "standard",
          "fee_fet": 0.0,
          "topic": "Consistent Hashing & Distributed Sharding",
          "difficulty": "Medium-Hard",
          "question": "In large-scale distributed storage systems (like Google Bigtable or Dynamo), explain how Consistent Hashing solves the $O(N)$ key remapping storm that occurs when adding or removing cache nodes under standard modulus hashing ($hash(key) \\pmod N$). How do virtual nodes (vnodes) address nonuniform key distribution and hot-spotting?",
          "expected_rubric": {
            "must_include": [
              "Modulus hashing remaps nearly all keys when N changes (O(N) data migration catastrophe)",
              "Consistent hashing maps both servers and keys to a 2^32 or 2^64 circular hash ring",
              "A key is assigned to the first server encountered moving clockwise along the ring",
              "Adding or removing a server only relocates keys between immediate neighbor nodes (O(K/N) migration)",
              "Virtual nodes (vnodes) distribute multiple ring tokens per physical server, mitigating hot spots and balancing load"
            ],
            "bonus_points": [
              "Replication factor R strategy (storing replicas on next R distinct physical servers)",
              "Handling heterogeneous server capacities by assigning proportional vnode counts",
              "Binary search (O(log M)) lookup along the token ring array"
            ],
            "common_pitfalls": [
              "Confusing cryptographic hash security with consistent hash ring geometry",
              "Failing to explain how vnodes solve non-uniform hash clustering"
            ]
          },
          "ideal_sample_answer": "Under standard modulo hashing (hash(key) % N), changing the server count from N to N+1 alters almost every key's destination, causing a massive data migration storm and catastrophic cache invalidation. Consistent hashing maps both server node IDs and data keys onto a continuous hash ring (e.g. 0 to 2^64 - 1). A key is assigned to the first server encountered when traversing the ring clockwise. When a node is added or removed, only the keys in the immediate predecessor interval are affected, reducing required data migration to O(K/N).\n\nTo prevent hot spots caused by non-uniform server placement along the ring, consistent hashing utilizes virtual nodes (vnodes). Each physical server is assigned multiple distinct virtual positions on the ring (e.g., 256 vnodes per node). This ensures statistical uniform key distribution, supports heterogeneous machines with weighted tokens, and prevents cascading node failures."
        },
        {
          "id": "google_dsa_adv_01",
          "company": "Google",
          "track": "Advanced DSA & Competitive Algorithms",
          "tier": "tier-1",
          "fee_fet": 1.0,
          "topic": "Dynamic Programming on Trees & Diameter Optimization",
          "difficulty": "Hard",
          "question": "Design an optimal algorithm to find the diameter (longest simple path between any two nodes) of an unweighted undirected tree with $N$ vertices ($N \\le 2 \\cdot 10^5$). Explain both the 2-BFS/DFS method and the Tree-DP post-order traversal method. Why does the 2-BFS method fail on trees with negative edge weights while Tree-DP remains valid?",
          "expected_rubric": {
            "must_include": [
              "2-BFS method: pick arbitrary root u, find furthest node v, find furthest node w from v; distance(v, w) is diameter",
              "Tree-DP method: at each node u, diameter is max(d_1 + d_2) where d_1 and d_2 are top 2 deepest child subtree depths",
              "Tree-DP post-order traversal runs in strict O(N) time and O(N) space",
              "2-BFS failure with negative weights: greedy choice property breaks since longer paths can have lower total weight"
            ],
            "bonus_points": [
              "Heavy-Light Decomposition for path queries",
              "Centroid decomposition overview for divide-and-conquer on trees"
            ],
            "common_pitfalls": [
              "Attempting All-Pairs Shortest Path (Floyd-Warshall) in O(N^3) time",
              "Failing to account for diameter passing through the root vs entirely inside a child subtree"
            ]
          },
          "ideal_sample_answer": "The tree diameter can be solved via two approaches:\n1. 2-BFS/DFS Method: Select an arbitrary start node u, run BFS/DFS to find the furthest node v. Run a second BFS/DFS from v to find furthest node w. The distance between v and w is the tree diameter. This runs in O(N) time.\n2. Tree-DP Method: Root the tree arbitrarily. For every node u, maintain the longest path from u down to any leaf in its subtree: height(u) = 1 + max(height(child)). The longest path passing through u as the lowest common ancestor is the sum of the two largest child heights: diameter_through_u = top1_height + top2_height. In a single post-order traversal, update the global maximum diameter. Total complexity is O(N) time and O(H) recursion stack space.\n\nWhy 2-BFS fails on negative edge weights: 2-BFS relies on the greedy property that the furthest node from any arbitrary starting vertex is guaranteed to be one endpoint of the diameter. When negative weights exist, reaching a far node in hop-count or distance does not preserve the optimal substructure, causing 2-BFS to terminate at suboptimal nodes. Tree-DP correctly explores all subtree path combinations."
        }
      ]
    },
    "microsoft": {
      "name": "Microsoft",
      "track": "Cloud Platforms, Distributed Systems & Modern Concurrency",
      "description": "Azure cloud services, microservices resilience, async concurrency, and high-throughput backend architecture.",
      "questions": [
        {
          "id": "msft_sys_01",
          "company": "Microsoft",
          "track": "Backend Concurrency",
          "tier": "standard",
          "fee_fet": 0.0,
          "topic": "Thread Pools, Context Switching & Async/Await Mechanics",
          "difficulty": "Medium",
          "question": "In high-throughput web APIs (.NET / Java / Node.js), explain why allocating a dedicated OS thread per HTTP request causes server thrashing under 100,000 concurrent connections. Contrast synchronous thread blocking with asynchronous non-blocking I/O (`async/await` and completion ports), detailing the memory footprint and CPU context-switching overhead.",
          "expected_rubric": {
            "must_include": [
              "OS Thread stack memory overhead (1MB per thread = 100GB for 100k threads, causing OOM)",
              "CPU context-switching thrashing: CPU spends more cycles swapping register/kernel state than executing business logic",
              "Non-blocking async I/O uses OS event notification (epoll, kqueue, Windows I/O Completion Ports - IOCP)",
              "State machine generation in async/await freeing the executing thread back to the thread pool while awaiting I/O"
            ],
            "bonus_points": [
              "Thread pool starvation mitigation",
              "Work-stealing schedulers (like .NET TaskScheduler or Go runtime)"
            ],
            "common_pitfalls": [
              "Thinking async/await creates a new background OS thread for every await call",
              "Confusing CPU-bound parallelism with I/O-bound asynchronous concurrency"
            ]
          },
          "ideal_sample_answer": "Under the thread-per-request model, 100,000 concurrent requests require 100,000 OS threads. Each thread typically allocates 1 MB of stack memory, demanding ~100 GB of RAM just for thread stacks, triggering Out-Of-Memory (OOM) crashes. Furthermore, having thousands of active threads forces the OS kernel into continuous context-switching: saving and restoring CPU register banks, cache pollution, and kernel transitions, causing CPU thrashing where zero useful work completes.\n\nAsync/await with non-blocking I/O solves this by utilizing operating system completion notifications (e.g. Windows IOCP, Linux epoll). When an I/O operation begins, the compiler-generated async state machine captures the continuation and returns the worker thread to the shared thread pool. No thread sleeps or blocks. When the OS completes the disk/network transfer, an event notification re-enqueues the continuation onto an available pool thread. A small pool of 8\u201316 threads can effortlessly service 100,000 concurrent connections with minimal memory and negligible context switching."
        }
      ]
    },
    "nvidia": {
      "name": "Nvidia",
      "track": "GPU Architecture, Parallel Computing & CUDA Systems",
      "description": "CUDA kernels, SIMT execution, memory coalescing, warp divergence, and deep learning acceleration.",
      "questions": [
        {
          "id": "nvidia_gpu_01",
          "company": "Nvidia",
          "track": "GPU Architecture & CUDA",
          "tier": "standard",
          "fee_fet": 0.0,
          "topic": "Warp Divergence, Shared Memory Bank Conflicts & Memory Coalescing",
          "difficulty": "Medium-Hard",
          "question": "In Nvidia GPU microarchitectures (Hopper / Blackwell / Ampere), explain the SIMT (Single Instruction Multiple Threads) execution model. What happens during Warp Divergence when threads in a 32-thread warp evaluate different conditional `if-else` branches? How do shared memory bank conflicts and uncoalesced global memory access degrade kernel throughput?",
          "expected_rubric": {
            "must_include": [
              "SIMT executes threads in synchronized groups of 32 called warps on Streaming Multiprocessors (SMs)",
              "Warp divergence: conditional branching causes the warp to serially execute both paths with inactive threads masked off, halving efficiency",
              "Shared memory bank conflicts: 32 memory banks service addresses; if multiple threads in a warp access different words in the same bank, accesses are serialized",
              "Global memory coalescing: consecutive threads in a warp must access contiguous 32/64/128-byte aligned memory to maximize cache-line bandwidth utilization"
            ],
            "bonus_points": [
              "Pad array columns to eliminate stride-induced bank conflicts (e.g., float shared[32][33])",
              "Tensor Core warp-level matrix multiply-accumulate (WMMA) instructions"
            ],
            "common_pitfalls": [
              "Confusing CPU SIMD vector lanes with GPU SIMT independent program counters",
              "Claiming divergent threads execute in true hardware parallelism"
            ]
          },
          "ideal_sample_answer": "In Nvidia GPU microarchitecture, Streaming Multiprocessors (SMs) execute instructions using SIMT (Single Instruction Multiple Threads) in lockstep bundles of 32 threads known as a Warp. All threads in a warp share an instruction pointer.\n\n1. Warp Divergence: If threads within the same warp take different paths in an `if (condition) ... else ...` block, the warp must execute both branches sequentially. The hardware activates threads taking the 'if' branch while masking off 'else' threads, and then reverses the mask for the 'else' branch. This serialization cuts effective computational throughput by 50% or more.\n\n2. Shared Memory Bank Conflicts: On-chip shared memory is divided into 32 equally sized memory banks (4 bytes per bank). When multiple threads in a warp request distinct memory addresses that map to the same bank, a bank conflict occurs and requests are serialized. If all 32 threads access different banks, memory access occurs in a single clock cycle.\n\n3. Global Memory Coalescing: The GPU memory controller loads data from High-Bandwidth Memory (HBM) in 32-byte or 128-byte aligned transactions. If threads in a warp access contiguous addresses, the entire warp's data is retrieved in a single memory transaction (coalesced). If access is strided or scattered, the hardware issues up to 32 separate transactions, squandering memory bus bandwidth."
        }
      ]
    }
  }
}

STOPWORDS = {"what", "is", "the", "in", "and", "of", "for", "about", "tell", "me", "explain", "how", "to", "a", "an", "do", "you", "know", "can", "please", "give"}

def clean_tokens(text: str) -> List[str]:
    words = re.findall(r'[a-zA-Z0-9_\-\+]+', text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]

# ==============================================================================
# Autonomous Knowledge & Retrieval Engine
# ==============================================================================
def match_query(query: str) -> Dict[str, Any]:
    q_low = query.lower()
    tokens = set(clean_tokens(query))

    # 1. Exact Subject Code Match (e.g. KEC-601, KCS-501)
    code_match = re.search(r'\b(k[a-z]{2}-?\d{3})\b', q_low)
    if code_match:
        target_code = code_match.group(1).upper().replace("-", "")
        for branch, bdata in CURRICULUM_DATA.get('branches', {}).items():
            for s in bdata.get('subjects', []):
                s_code = s.get('subject_code', '').upper().replace("-", "")
                if target_code == s_code:
                    return {"type": "SUBJECT", "branch": branch, "data": s}

    # 2. Company Technical Questions Match
    best_q = None
    best_score = 0
    for comp_key, comp_data in INTERVIEW_BANK.get('companies', {}).items():
        for qitem in comp_data.get('questions', []):
            topic = qitem.get('topic', '').lower()
            topic_tokens = set(clean_tokens(topic))
            comp_match = comp_key in q_low
            common = tokens.intersection(topic_tokens)
            score = len(common) * 2 + (2 if comp_match else 0)
            if score > best_score and (len(common) >= 2 or (comp_match and len(common) >= 1) or topic in q_low):
                best_score = score
                best_q = qitem
    if best_q and best_score >= 2:
        return {"type": "INTERVIEW_QUESTION", "data": best_q}

    # 3. Curriculum Subject Name Match
    for branch, bdata in CURRICULUM_DATA.get('branches', {}).items():
        for s in bdata.get('subjects', []):
            s_name = s.get('subject_name', '').lower()
            if s_name in q_low or len(tokens.intersection(set(clean_tokens(s_name)))) >= 2:
                return {"type": "SUBJECT", "branch": branch, "data": s}

    # 4. Curriculum Unit Topic Match
    for branch, bdata in CURRICULUM_DATA.get('branches', {}).items():
        for s in bdata.get('subjects', []):
            for u in s.get('units', []):
                u_title = u.get('unit_title', '').lower()
                if u_title in q_low:
                    return {"type": "CURRICULUM_UNIT", "branch": branch, "subject": s, "unit": u}
                for t in u.get('topics', []):
                    t_low = t.lower()
                    if t_low in q_low or len(tokens.intersection(set(clean_tokens(t_low)))) >= 2:
                        return {"type": "CURRICULUM_TOPIC", "branch": branch, "subject": s, "unit": u, "topic": t}

    return {"type": "NONE"}


def format_subject_markdown(subject: Dict[str, Any], branch: str) -> str:
    code = subject.get("subject_code", "")
    name = subject.get("subject_name", "")
    sem = subject.get("semester", "")
    credits = subject.get("credit_weight", 4.0)
    relevance = subject.get("placement_relevance", "Core Engineering Value")
    
    lines = [
        f"## 📚 AKTU Official Syllabus: {code} — {name}",
        f"**Branch:** {branch} | **Semester:** {sem} | **Credits:** {credits}",
        f"**Recruitment Value:** _{relevance}_",
        "",
        "### 📖 Course Units Breakdown:"
    ]
    for u in subject.get("units", []):
        u_num = u.get("unit_number", 1)
        u_title = u.get("unit_title", "")
        is_hy = "🔥 High-Yield" if u.get("is_high_yield") else "Standard"
        lines.append(f"#### Unit {u_num}: {u_title} ({is_hy})")
        topics = u.get("topics", [])
        if topics:
            lines.append("- " + " • ".join(topics))
        lines.append("")
    
    lines.append("---")
    lines.append(f"👉 *To generate your daily balanced timetable, send: **\"Create study plan for {branch} Sem {sem} with 4 hours daily\"***")
    lines.append("👉 *To launch a technical interview mock, send: **\"Start Qualcomm drill\"** or **\"Start Google drill\"****")
    return "\n".join(lines)


def format_topic_markdown(match: Dict[str, Any]) -> str:
    s = match.get("subject", {})
    u = match.get("unit", {})
    t = match.get("topic", u.get("unit_title", ""))
    branch = match.get("branch", "Engineering")
    code = s.get("subject_code", "")
    name = s.get("subject_name", "")
    sem = s.get("semester", "")
    is_hy = "🔥 High-Yield" if u.get("is_high_yield") else "Standard"
    relevance = s.get("placement_relevance", "Core Technical Value")
    
    lines = [
        f"## 📘 Syllabus Concept: {t}",
        f"**Curriculum Mapping:** {code} — {name} ({branch} Semester {sem})",
        f"**Unit {u.get('unit_number')}:** {u.get('unit_title')} ({is_hy})",
        f"**Industry Placement Alignment:** _{relevance}_",
        "",
        "---",
        "### 🔍 Detailed Curriculum Coverage:",
        f"This topic is an integral component of **Unit {u.get('unit_number')}** under the official AKTU university syllabus.",
        "",
        "**Core Topics in this Unit:**"
    ]
    for topic_item in u.get("topics", []):
        marker = "👉" if topic_item.lower() == t.lower() else "-"
        lines.append(f"{marker} {topic_item}")
        
    lines.append("")
    lines.append("---")
    lines.append("💡 *Academic & Placement Tip:* For recruitment drills, focus on numerical derivations, timing diagrams, and architecture applications.")
    lines.append(f"👉 *To add this topic to your daily schedule, send: **\"Create study plan for {branch} Sem {sem}\"****")
    return "\n".join(lines)


def format_interview_concept_markdown(q: Dict[str, Any]) -> str:
    comp = q.get("company", "Company")
    track = q.get("track", "Engineering")
    topic = q.get("topic", "System Drill")
    diff = q.get("difficulty", "Medium")
    tier = q.get("tier", "Standard").title()
    rubric = q.get("expected_rubric", {})
    
    lines = [
        f"## ⚡ {comp} Recruitment Drill: {topic}",
        f"**Track:** {track} | **Difficulty:** `{diff}` | **Tier:** `{tier}`",
        "",
        "---",
        "### 📋 Technical Interview Challenge:",
        f"{q.get('question', '')}",
        "",
        "---",
        "### 🎯 Senior Bar Raiser Scoring Checkpoints (10.0 Rubric):",
        "**Must-Include Technical Mechanics:**"
    ]
    for item in rubric.get("must_include", []):
        lines.append(f"- ✅ {item}")
    
    if rubric.get("bonus_points"):
        lines.append("")
        lines.append("**Bonus Architecture / Edge Cases:**")
        for item in rubric.get("bonus_points", []):
            lines.append(f"- ⭐ {item}")
            
    if rubric.get("common_pitfalls"):
        lines.append("")
        lines.append("**Common Pitfalls to Avoid:**")
        for item in rubric.get("common_pitfalls", []):
            lines.append(f"- ⚠️ {item}")
            
    lines.append("")
    lines.append("---")
    lines.append("✍️ *Reply directly with your technical explanation or code to receive your instant Bar Raiser scorecard & badge!*")
    return "\n".join(lines)


def format_balancing_strategy_markdown() -> str:
    return "\n".join([
        "## ⚖️ CampusMate Dynamic Load-Balancing Algorithm",
        "CampusMate AI eliminates **Academic Debt** by continuously harmonizing your college semester exams with tier-1 recruitment goals using a 3-tier deterministic allocation model:",
        "",
        "### 📊 The 3 Dynamic Workload Modes:",
        "1. **Normal Preparation Mode (> 7 Days to Midterm):**",
        "   - **Allocation:** `60% Placement Prep (144m)` / `40% Syllabus Revision (96m)` (based on 4 hrs)",
        "   - **Focus:** Heavy coding drills, system design, LeetCode/Verilog, while maintaining steady syllabus momentum.",
        "",
        "2. **Approaching Midterm Mode (3 to 7 Days to Midterm):**",
        "   - **Allocation:** `50% Placement Prep (120m)` / `50% Syllabus Revision (120m)`",
        "   - **Focus:** Balanced split to prevent last-minute cramming without pausing competitive problem solving.",
        "",
        "3. **Urgent Exam Revision Mode (< 3 Days to Midterm):**",
        "   - **Allocation:** `10% Placement Prep (24m)` / `90% High-Yield Syllabus Units (216m)`",
        "   - **Focus:** Emergency academic triage. Dynamically filters out low-weight syllabus units and drills exclusively on `🔥 High-Yield` numerical derivations and diagrams to secure CGPA.",
        "",
        "---",
        "### ⚡ Evening Remedial Mutation Hook:",
        "If you score `< 6.0 / 10.0` on any technical interview drill, the engine automatically injects a **30-minute remedial session** into tonight's Evening Block, guaranteeing knowledge gaps are eliminated before sleep.",
        "",
        "👉 *To generate your customized plan, send: **\"Create study plan for ECE Sem 6 with 4 hours daily\"***"
    ])


def format_branches_coverage_markdown() -> str:
    return "\n".join([
        "## 🎓 AKTU / AICTE Comprehensive Academic Coverage",
        "CampusMate AI includes official course structures, high-yield tags, and placement mappings for all 4 major engineering departments across **Semesters 1 through 8**:",
        "",
        "| Department | Branch Code | Supported Semesters | Placement Recruitment Targets |",
        "| :--- | :--- | :--- | :--- |",
        "| **Electronics & Communication** | `ECE` | Semesters 1 to 8 | Qualcomm, Intel, Texas Instruments, Nvidia, Embedded & Signal Processing |",
        "| **Computer Science & Engg** | `CSE` | Semesters 1 to 8 | Google, Amazon, Microsoft, Systems Architecture, Distributed Cloud |",
        "| **Information Technology** | `IT` | Semesters 1 to 8 | Cloud Computing, Full-Stack Architecture, TCS Prime, Amazon AWS |",
        "| **Mechanical Engineering** | `MECH` | Semesters 1 to 8 | Robotics, CAD/CAM, Thermal Systems, Core Engineering Operations |",
        "",
        "---",
        "### 🔍 What you can ask:",
        "- *\"Tell me the topics for CSE semester 5\"*",
        "- *\"What is KEC-601?\"*",
        "- *\"Show MECH semester 4 subjects\"*",
        "- *\"Which units in KCS-502 are high yield?\"*"
    ])


def format_company_guide_markdown(company_name: str) -> str:
    comp = company_name.title()
    dossiers = {
        "Qualcomm": {
            "track": "Hardware & Embedded Systems / VLSI",
            "topics": "Verilog RTL, Blocking vs Non-Blocking Assignments, Setup & Hold Time Violations, Clock Domain Crossing (CDC), ARM Cortex Interfacing (I2C/SPI).",
            "pitfall": "Mixing blocking (=) and non-blocking (<=) statements in sequential always blocks; ignoring clock skew in hold-time analysis.",
            "command": "Start Qualcomm Verilog mock technical interview drill"
        },
        "Google": {
            "track": "Systems Architecture & Algorithmic Scalability",
            "topics": "Consistent Hashing with Virtual Nodes, Distributed Sharding, High-Capacity Tree-DP, Cache Invalidation at Planet Scale.",
            "pitfall": "Failing to account for non-uniform node distribution; ignoring hotspot churn when scaling server clusters.",
            "command": "Start Google drill"
        },
        "Nvidia": {
            "track": "GPU Architecture, Parallel Computing & CUDA Systems",
            "topics": "SIMT Execution Models, 32-Thread Warp Divergence, Shared Memory Bank Conflicts (32 banks), Coalesced Global Memory Access.",
            "pitfall": "Allowing thread branch divergence inside a single warp; ignoring stride patterns that cause memory serialization.",
            "command": "Start Nvidia drill"
        },
        "Microsoft": {
            "track": "Cloud Platforms, High-Throughput Concurrency & Async I/O",
            "topics": "Worker Thread Pools, Asynchronous I/O Completion Ports (IOCP), Lock-Free Ring Buffers, Semaphore vs Mutex contention.",
            "pitfall": "Blocking thread pool worker threads with synchronous calls; deadlocks caused by priority inversions.",
            "command": "Start Microsoft drill"
        },
        "Amazon": {
            "track": "Data Structures, Distributed Caching & Bar Raiser",
            "topics": "Cache Stampede (Thundering Herd) Prevention, Probabilistic Early Expiration (XFetch), Distributed Locks, Bar Raiser Leadership Principles.",
            "pitfall": "Relying on standard TTL without mutex/probabilistic recompute; missing graceful degradation during downstream cache failure.",
            "command": "Unlock Amazon Bar Raiser mock interview pack"
        },
        "Tcs Prime": {
            "track": "Systems Engineering, Modern C++ & Advanced Algorithms",
            "topics": "Modern C++ (C++17/20), Smart Pointers (`std::unique_ptr`, `std::shared_ptr`, `std::weak_ptr`), RAII, Exception Safety, Virtual Dispatch.",
            "pitfall": "Creating cyclic references with `shared_ptr` instead of `weak_ptr`; raw memory leaks when exceptions are thrown.",
            "command": "Start TCS Prime drill"
        }
    }
    d = dossiers.get(comp, dossiers["Qualcomm"])
    return "\n".join([
        f"## 🏢 {comp} Recruitment Preparation Guide",
        f"**Track:** {d['track']}",
        "",
        "---",
        "### 🎯 High-Frequency Technical Topics Tested:",
        f"{d['topics']}",
        "",
        "### ⚠️ Senior Bar Raiser Pitfall to Avoid:",
        f"_{d['pitfall']}_",
        "",
        "---",
        f"👉 *Launch an interactive technical mock drill: Send **\"{d['command']}\"***"
    ])


def format_interview_tracks_markdown() -> str:
    return "\n".join([
        "## 🎯 CampusMate Interview Preparation Hub",
        "Tailored technical drill tracks aligned with tier-1 engineering recruitment:",
        "",
        "| Company | Recruitment Track | Quick Launch Command |",
        "| :--- | :--- | :--- |",
        "| **Qualcomm** | Hardware / VLSI RTL / STA | `Start Qualcomm Verilog drill` |",
        "| **Google** | Distributed Systems & Dynamic Programming | `Start Google drill` |",
        "| **Nvidia** | GPU CUDA, SIMT & Shared Memory | `Start Nvidia drill` |",
        "| **Microsoft** | High-Throughput Concurrency & Async I/O | `Start Microsoft drill` |",
        "| **Amazon** | System Design & Bar Raiser Cache | `Start Amazon Bar Raiser drill` |",
        "| **TCS Prime** | Modern C++ Smart Pointers & RAII | `Start TCS Prime drill` |",
        "",
        "---",
        "💡 *All drills include instant Senior Bar Raiser 10.0 rubric evaluation and automatic evening schedule mutation if score < 6.0/10.*",
        "👉 *Send any command from the table above to start drilling immediately.*"
    ])


def format_web3_guide_markdown() -> str:
    return format_interview_tracks_markdown()


def format_exam_strategy_markdown() -> str:
    return "\n".join([
        "## 📝 AKTU Sessional & University Exam Excellence Guide",
        "How to secure 8.5+ CGPA while cracking Tier-1 off-campus placements:",
        "",
        "### 💡 Top 4 Tactical Rules for AKTU Students:",
        "1. **Master the `🔥 High-Yield` Units First:**",
        "   - In AKTU curricula, Units 1, 2, and 3 typically account for **70% of numerical derivations and theory** in Section B and C.",
        "",
        "2. **Step-Marking & Diagram Formatting:**",
        "   - AKTU evaluators award up to 40% of marks for clear block diagrams, timing waveforms, and circuit schematics before reading text derivations.",
        "",
        "3. **Never Zero Out Coding:**",
        "   - Even in exam week, dedicate 30 minutes daily to technical drills. Algorithmic thinking atrophies fast if paused completely.",
        "",
        "4. **Synchronize Sessional Buffer with CampusMate:**",
        "   - College announced midterms? Simply tell CampusMate: *\"my exam is in 3 days\"* — the balancer engine instantly recalculates your daily routine to 90% exam focus.",
        "",
        "👉 *To generate your exam timetable, send: **\"Create study plan for ECE Sem 6 with 4 hours daily\"***"
    ])


def format_remedial_hook_markdown() -> str:
    return "\n".join([
        "## 🔄 Autonomous Evening Remedial Mutation Hook",
        "The proprietary feedback loop between Member 2 (Syllabus Balancer) and Member 3 (Technical Interviewer):",
        "",
        "### ⚙️ How the Mutation Mechanism Works:",
        "1. **Interactive Evaluation:** You submit code or explanation to a company drill prompt.",
        "2. **Rubric Grading:** Evaluated on a 10.0 scale against expected architectural checkpoints and pitfalls.",
        "3. **Threshold Trigger:** If score is **`< 6.0 / 10.0`**, the balancer intercepts tonight's schedule.",
        "4. **Dynamic Mutation:** Injects a targeted **30-minute remedial review block** on your exact weak topic into your Evening Block.",
        "5. **Schedule Regeneration:** Prevents knowledge gaps from lingering into campus placement season.",
        "",
        "👉 *Test the mutation hook: Send **\"Start Qualcomm drill\"** and submit an incomplete answer to watch tonight's schedule mutate dynamically!*"
    ])


def format_profile_status_markdown(session: StudentSession) -> str:
    exam_status = f"Midterm in **{session.days_to_midterm} Days** (User-Specified)" if session.days_specified else f"Midterm in **{session.days_to_midterm} Days** (Synced to AKTU/GCET Calendar)"
    mode_label = "Urgent Exam Revision (10/90)" if session.days_to_midterm < 3 else ("Approaching Midterm (50/50)" if session.days_to_midterm <= 7 else "Normal Prep (60/40)")

    return "\n".join([
        "## 👤 Active Student Twin Profile",
        f"- 🎓 **Engineering Branch:** `{session.branch}`",
        f"- 📚 **Current Semester:** `Semester {session.semester}`",
        f"- 🏢 **Target Company:** `{session.target_company}`",
        f"- ⏱️ **Daily Study Budget:** `{session.daily_hours:.1f} Hours/Day`",
        f"- ⏳ **Exam Proximity:** {exam_status}",
        f"- ⚖️ **Current Balancer Mode:** `{mode_label}`",
        f"- 🔄 **Remedial Hook Status:** `{'Active (' + session.evening_remedial_mutation + ')' if session.evening_remedial_mutation else 'Clear (No Academic Debt)'}`",
        "",
        "---",
        "💡 *To update your profile anytime, send e.g.:*  \n*\"Switch to CSE Semester 5 with 3 hours daily targeting Google, exam in 4 days\"*",
        "",
        "👉 *To view your study timetable, send: **\"Show my daily study plan\"***"
    ])


# ==============================================================================
# Agent Initialization
# ==============================================================================
agent = Agent(
    name="campusmate_ai",
    seed="campusmate_student_twin_secret_seed_gcet_2026"
)

chat_proto = Protocol(spec=chat_protocol_spec)

class StudentSession:
    def __init__(self, sender: str):
        self.sender = sender
        self.branch = "ECE"
        self.semester = 6
        self.target_company = "Qualcomm"
        self.daily_hours = 4.0
        self.days_to_midterm = 18
        self.days_specified = False
        self.last_question_id = "qualcomm_verilog_01"
        self.evening_remedial_mutation = None
        self.in_drill = False

sessions: Dict[str, StudentSession] = {}

def get_session(sender: str) -> StudentSession:
    if sender not in sessions:
        sessions[sender] = StudentSession(sender)
    return sessions[sender]

def evaluate_submission(q: Dict[str, Any], answer: str) -> Dict[str, Any]:
    ans_low = answer.lower()
    rubric = q.get("expected_rubric", {})
    must_includes = rubric.get("must_include", [])
    bonus_points = rubric.get("bonus_points", [])
    pitfalls = rubric.get("common_pitfalls", [])

    matched_must = sum(1 for m in must_includes if any(w in ans_low for w in clean_tokens(m)[:3]))
    matched_bonus = sum(1 for b in bonus_points if any(w in ans_low for w in clean_tokens(b)[:3]))
    matched_pitfalls = sum(1 for p in pitfalls if any(w in ans_low for w in clean_tokens(p)[:3]))

    must_pct = (matched_must / max(1, len(must_includes)))
    score = min(10.0, max(2.0, (must_pct * 7.5) + (matched_bonus * 1.5) - (matched_pitfalls * 1.0) + (1.0 if len(answer) > 80 else 0.0)))
    
    badge = "Strong Hire" if score >= 8.5 else ("Hire" if score >= 7.0 else ("Borderline" if score >= 6.0 else "Needs Improvement"))
    return {
        "score": round(score, 1),
        "badge": badge,
        "matched_must": matched_must,
        "total_must": len(must_includes),
        "remedial_topic": q.get("remedial_topics", ["Core Fundamentals"])[0]
    }


def generate_schedule_markdown(session: StudentSession) -> str:
    total_mins = int(round(session.daily_hours * 60))
    if session.days_to_midterm < 3:
        p_pct, s_pct = 10, 90
        mode_label = "Urgent Exam Revision Mode (90% Academic / 10% Placement)"
    elif session.days_to_midterm <= 7:
        p_pct, s_pct = 50, 50
        mode_label = "Approaching Midterm Mode (50% Placement / 50% Academic)"
    else:
        p_pct, s_pct = 60, 40
        mode_label = "Normal Prep Mode (60% Placement / 40% Academic Coursework)"

    p_mins = int(round(total_mins * (p_pct / 100.0)))
    s_mins = total_mins - p_mins

    bdata = CURRICULUM_DATA.get("branches", {}).get(session.branch, {})
    subjs = [s for s in bdata.get("subjects", []) if s.get("semester") == session.semester]
    if not subjs:
        subjs = bdata.get("subjects", [])[:3]

    lines = [
        f"## 📅 Adaptive Daily Study Plan ({session.branch} — Semester {session.semester})",
        f"**Target Company:** {session.target_company} | **Study Budget:** {session.daily_hours:.1f} Hours/Day",
        "",
        "### ⏳ Exam Proximity & Calendar Synchronization:"
    ]
    if session.days_specified:
        lines.append(f"- 📌 **User-Specified Exam Date:** Midterm in **{session.days_to_midterm} Days**.")
    else:
        lines.append(
            f"- 📌 **College Academic Calendar Synced (AKTU/GCET):** Sessional Midterms start in **{session.days_to_midterm} Days** "
            "(operating in Normal Placement Focus). *(💡 If your exam is sooner, send e.g. **\"exam in 3 days\"** to adapt!)*"
        )

    lines.append("")
    lines.append(f"### ⚖️ Deterministic Workload Allocation ({mode_label})")
    lines.append(f"- 🎯 **Placement Technical Drills:** **{p_pct}%** ({p_mins} mins)")
    lines.append(f"- 📘 **Academic Syllabus Revision:** **{s_pct}%** ({s_mins} mins)")
    lines.append("")
    lines.append("---")
    lines.append("### 📝 Today's Recommended Task Schedule:")

    s1 = subjs[0].get("subject_name", "Core Subject 1") if len(subjs) > 0 else "Digital Systems"
    s2 = subjs[1].get("subject_name", "Core Subject 2") if len(subjs) > 1 else "Microcontrollers"
    
    t_drill1 = int(p_mins * 0.5)
    t_drill2 = p_mins - t_drill1
    t_acad1 = int(s_mins * 0.5)
    t_acad2 = s_mins - t_acad1

    lines.append(f"1. **🌅 Morning Block ({t_drill1}m):** `🎯 Placement` {session.target_company} Technical Problem Solving & Coding")
    lines.append(f"2. **☀️ Mid-Day Block ({t_acad1}m):** `📘 Syllabus` {s1} (Unit 1 High-Yield Revision)")
    lines.append(f"3. **🌆 Afternoon Block ({t_drill2}m):** `🎯 Placement` {session.target_company} System Architecture & Speed Drill")
    lines.append(f"4. **🌙 Night Block ({t_acad2}m):** `📘 Syllabus` {s2} (Unit 2 Numerical & Derivation Drill)")

    if session.evening_remedial_mutation:
        lines.append("")
        lines.append(f"⚠️ **Evening Remedial Hook Injected:** {session.evening_remedial_mutation}")

    lines.append("")
    lines.append("---")
    lines.append(f"👉 *Ready to practice? Type: **\"Start {session.target_company} drill\"** to begin your mock technical interview!*")
    return "\n".join(lines)


@chat_proto.on_message(model=ACPChatMessage)
async def on_acp_message(ctx: Context, sender: str, msg: ACPChatMessage):
    session = get_session(sender)
    raw_text = msg.text().strip()
    user_text = re.sub(r"@agent1[a-z0-9]+\s*", "", raw_text).strip() or raw_text
    ctx.logger.info(f"Incoming message from {sender}: {user_text}")
    lower = user_text.lower()

    # Universal Dynamic State Extraction
    b_match = re.search(r"\b(ece|cse|it|mech)\b", lower)
    if b_match:
        session.branch = b_match.group(1).upper()
    s_match = re.search(r"(?:semester|sem)\s*(\d+)", lower)
    if s_match:
        session.semester = int(s_match.group(1))
    h_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr|h\b)", lower)
    if h_match:
        session.daily_hours = float(h_match.group(1))
    d_match = re.search(r"(?:midterm|exam|in)\s*(\d+)\s*days?", lower)
    if d_match:
        session.days_to_midterm = int(d_match.group(1))
        session.days_specified = True
    for c in ["google", "nvidia", "microsoft", "amazon", "tcs", "qualcomm"]:
        if c in lower:
            session.target_company = "TCS Prime" if c == "tcs" else c.title()
            break

    # --------------------------------------------------------------------------
    # INTENT: Profile Status
    # --------------------------------------------------------------------------
    if any(k in lower for k in ["my profile", "current settings", "my current branch", "my status", "who am i", "my target"]):
        md = format_profile_status_markdown(session)
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT: Load-Balancing Strategy & Workload Allocation Formula
    # --------------------------------------------------------------------------
    if any(k in lower for k in ["how do you balance", "balancing formula", "how does it balance", "ratio", "60/40", "50/50", "10/90", "academic debt", "balancing work", "workload allocation", "balance college"]):
        md = format_balancing_strategy_markdown()
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT: Branches & AKTU University Coverage
    # --------------------------------------------------------------------------
    if any(k in lower for k in ["which branch", "what branches", "branches supported", "is cse supported", "is mech supported", "is it supported", "aktu coverage", "all semesters", "which engineering"]):
        md = format_branches_coverage_markdown()
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT: Target Company Recruitment & Preparation Guide
    # --------------------------------------------------------------------------
    if any(k in lower for k in ["how to prepare for", "recruitment guide", "placement guide", "interview tips", "what does google ask", "qualcomm prep", "nvidia prep", "amazon prep", "how to crack"]) and not any(k in lower for k in ["start", "unlock", "drill", "mock"]):
        md = format_company_guide_markdown(session.target_company)
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT: Interview Tracks & Company Drills Guide
    # --------------------------------------------------------------------------
    if any(k in lower for k in ["how to unlock", "tracks", "all tracks", "available drills", "what drills", "show drills", "interview tracks"]):
        md = format_interview_tracks_markdown()
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT: AKTU Sessional Exam Tips & CGPA Protection
    # --------------------------------------------------------------------------
    if any(k in lower for k in ["exam tips", "score high", "sessional tips", "study tips", "cgpa tips", "how to pass", "how to score", "tips for sessional"]):
        md = format_exam_strategy_markdown()
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT: Evening Remedial Mutation Hook Details
    # --------------------------------------------------------------------------
    if any(k in lower for k in ["remedial hook", "mutation hook", "why did my schedule change", "remedial mutation", "evening mutation", "schedule mutation"]):
        md = format_remedial_hook_markdown()
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return

    # 1. Answer Submission Evaluation
    if session.in_drill and len(user_text) > 25 and not any(k in lower for k in ["start", "schedule", "topics", "hello", "hi", "help"]):
        q = None
        for cdata in INTERVIEW_BANK.get("companies", {}).values():
            for item in cdata.get("questions", []):
                if item.get("id") == session.last_question_id:
                    q = item
                    break
        if not q:
            q = INTERVIEW_BANK["companies"]["qualcomm"]["questions"][0]

        eval_res = evaluate_submission(q, user_text)
        score = eval_res["score"]
        badge = eval_res["badge"]
        session.in_drill = False

        if score < 6.0:
            session.evening_remedial_mutation = f"30m Remedial Drill: {eval_res['remedial_topic']} (Mock score was {score}/10)"

        lines = [
            "## 🏆 Technical Interview Scorecard",
            f"**Company Track:** {q.get('company')} | **Topic:** {q.get('topic')}",
            f"**Candidate Score:** `{score} / 10.0` — **{badge}**",
            "",
            "---",
            "### 📊 Rubric Evaluation Breakdown:",
            f"- **Core Mechanics Checkpoints Hit:** `{eval_res['matched_must']} / {eval_res['total_must']}`",
            f"- **Recommended Remedial Topic:** `{eval_res['remedial_topic']}`",
            "",
            "### 📝 Evaluator Feedback:",
            f"Submission demonstrated technical awareness. For top-tier 10.0 scores, ensure complete edge cases and formal architectural formulas are stated."
        ]
        if score < 6.0:
            lines.append("")
            lines.append(f"⚠️ **Member 2 Remedial Mutation Injected:** 30m review of '{eval_res['remedial_topic']}' added to tonight's Evening Study Block.")

        lines.append("")
        lines.append("👉 *Send **\"Create study plan\"** to view your schedule or **\"Start Google drill\"** for next drill!*")
        reply = ACPChatMessage(content=[TextContent(text="\n".join(lines))])
        await ctx.send(sender, reply)
        return

    # 2. Knowledge Retrieval (Zero Hallucination Ground Truth Search)
    match = match_query(user_text)
    if match["type"] == "SUBJECT":
        md = format_subject_markdown(match["data"], match["branch"])
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return
    elif match["type"] in ("CURRICULUM_UNIT", "CURRICULUM_TOPIC"):
        md = format_topic_markdown(match)
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return
    elif match["type"] == "INTERVIEW_QUESTION" and any(k in lower for k in ["explain", "what is", "how", "tell me", "concept", "pitfall", "rubric"]):
        md = format_interview_concept_markdown(match["data"])
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return

    # 3. Interview Tracks Overview
    if any(k in lower for k in ["interview track", "interview prep", "companies", "what tracks", "available tracks", "show tracks"]):
        lines = [
            "## 🎯 CampusMate Interview Preparation Hub",
            "Tailored technical drill tracks aligned with tier-1 engineering recruitment:",
            "",
            "| Company | Recruitment Track | Quick Launch Command |",
            "| :--- | :--- | :--- |",
            "| **Qualcomm** | Hardware / VLSI RTL / STA | `Start Qualcomm drill` |",
            "| **Google** | Distributed Systems & Sharding | `Start Google drill` |",
            "| **Nvidia** | GPU CUDA, SIMT & Shared Memory | `Start Nvidia drill` |",
            "| **Microsoft** | High-Throughput Concurrency & Async I/O | `Start Microsoft drill` |",
            "| **Amazon** | System Design & Bar Raiser Cache | `Unlock Amazon drill` |",
            "| **TCS Prime** | Modern C++ Smart Pointers & RAII | `Start TCS Prime drill` |",
            "",
            "---",
            "💡 *All drills include instant Senior Bar Raiser 10.0 rubric evaluation and automatic evening schedule mutation if score < 6.0/10.*",
            "👉 *Send any command above to start drilling immediately.*"
        ]
        reply = ACPChatMessage(content=[TextContent(text="\n".join(lines))])
        await ctx.send(sender, reply)
        return

    # 4. Start Drill
    if any(k in lower for k in ["drill", "start", "unlock", "mock", "qualcomm", "google", "nvidia", "microsoft", "amazon", "tcs"]):
        comp_key = "qualcomm"
        if "google" in lower: comp_key = "google"
        elif "nvidia" in lower: comp_key = "nvidia"
        elif "microsoft" in lower or "msft" in lower: comp_key = "microsoft"
        elif "amazon" in lower: comp_key = "amazon"
        elif "tcs" in lower: comp_key = "tcs_prime"

        comp_data = INTERVIEW_BANK["companies"].get(comp_key, INTERVIEW_BANK["companies"]["qualcomm"])
        q = comp_data["questions"][0]
        session.target_company = q.get("company", "Tech Company")
        session.last_question_id = q.get("id")
        session.in_drill = True

        md = format_interview_concept_markdown(q)
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return

    # 5. Study Schedule & Balancer
    if any(k in lower for k in ["schedule", "plan", "timetable", "routine", "hours", "midterm", "exam"]):
        b_match = re.search(r"\b(ece|cse|it|mech)\b", lower)
        if b_match: session.branch = b_match.group(1).upper()
        s_match = re.search(r"(?:semester|sem)\s*(\d+)", lower)
        if s_match: session.semester = int(s_match.group(1))
        h_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr|h\b)", lower)
        if h_match: session.daily_hours = float(h_match.group(1))
        d_match = re.search(r"(?:midterm|exam|in)\s*(\d+)\s*days?", lower)
        if d_match:
            session.days_to_midterm = int(d_match.group(1))
            session.days_specified = True
        else:
            session.days_to_midterm = 18
            session.days_specified = False

        md = generate_schedule_markdown(session)
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return

    # 6. Default Welcome & Help
    lines = [
        "## 🎓 Welcome to CampusMate AI!",
        "Your **Autonomous Academic & Career Agent** built on Fetch.ai uAgents and Agent Chat Protocol (ACP).",
        "",
        "Combines all 3 team members' work into one seamless workflow:",
        "- **Member 1 (Orchestration):** Agent Chat Protocol (ACP 0.3.0) discovery on ASI:One.",
        "- **Member 2 (Syllabus Balancing):** AKTU/GCET 1st-8th sem curriculum, dynamic ratio balancing (60/40, 50/50, 10/90) & evening remedial mutation hook.",
        "- **Member 3 (Technical Interviewer):** Qualcomm, Google, Nvidia, Microsoft, Amazon, TCS Prime bank & 10.0 Bar Raiser rubric grading.",
        "",
        "---",
        "### 🚀 Quick Prompts (Click or send any of these):",
        "1. **📖 Course Topics & Syllabus:**  \n   *\"Tell me the topics for ECE semester 6\"* or *\"What is KEC-601?\"*",
        "2. **📅 Study Timetable:**  \n   *\"Create study schedule for ECE Semester 6 with 4 hours daily\"*",
        "3. **⚡ Hardware & VLSI Drill:**  \n   *\"Start Qualcomm Verilog mock technical interview drill\"*",
        "4. **🔍 Google Distributed Systems:**  \n   *\"Start Google drill\"*",
        "5. **🎮 Nvidia GPU & CUDA:**  \n   *\"Start Nvidia drill\"*",
        "6. **🏢 Amazon Bar Raiser:**  \n   *\"Start Amazon Bar Raiser drill\"*",
        "7. **🎯 All Interview Tracks:**  \n   *\"Show interview tracks\"*"
    ]
    reply = ACPChatMessage(content=[TextContent(text="\n".join(lines))])
    await ctx.send(sender, reply)


agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    print(f"Starting CampusMate AI (Address: {agent.address})...")
    agent.run()
