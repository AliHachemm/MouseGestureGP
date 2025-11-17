# Laser-Guided Touchless Gesture Interface

## Overview
The COVID-19 pandemic fundamentally reshaped how humans interact with public devices. Shared touchscreens on vending machines, ATMs, ticket kiosks, and information terminals became potential vectors for disease transmission, highlighting the need for **touchless human-computer interaction (HCI)** systems. This project presents a **laser-guided, webcam-based finger-tracking system** that allows users to interact with digital interfaces without physical contact, using natural pointing and gesture-based selection.

---

## Background
Touchless interaction systems leverage computer vision, hand tracking, and gesture recognition to interpret human movement as digital input. Key developments in this field include:

- **PalmSpace** (Nath, 2024) – transforming a user's palm into an interactive surface for contact-free control.
- **Hand-based interaction design guidelines** (Sun et al., 2024) – providing insights for effective public-use systems.
- **Gesture recognition using deep learning** (Babu, Rustamov, & Turaev, 2023) – applied in real-world food-ordering systems.
- **Gaze tracking for vending machines** (Zeng et al., 2022) – demonstrating low-cost optical input can replace touch.

Open-source contributions have accelerated practical implementations:

- **Gesture-Based Touchless ATM** – replicates an ATM interface using hand gestures.
- **Touchless-UI** and **Hand Gesture Recognition for HCI** – map real-time hand landmarks to interface commands using Google MediaPipe.
- **Gesture-Controlled Virtual Mouse** – full cursor control via finger tracking.
- **touchless** – integrates gestures, gaze, and voice into a unified spatial interface library.

Despite these advances, existing systems often lack **precision, low latency, spatial feedback**, and advanced interaction metaphors like drag-and-drop or multi-finger selection.

---

## Project Goals
This project aims to develop a **next-generation touchless interaction prototype** that:

1. Tracks user finger movements in real-time using a standard webcam.
2. Provides **laser-guided spatial feedback** to mirror the user’s finger position.
3. Supports **sharp-motion gestures** for selection and natural pointing.
4. Demonstrates a hygienic, low-cost, and deployable solution for public interfaces such as vending machines or interactive maps.

By integrating academic insights and practical open-source techniques, this project showcases a **hygienic, intuitive, and accessible alternative to traditional touchscreens**.

---

## Features
- Real-time hand and finger tracking using computer vision.
- Laser-guided feedback for accurate spatial interaction.
- Multi-gesture support (point, select, and custom gestures).
- Low-cost, deployable on standard hardware.
- Open-source, easy to extend for new public interface applications.

---

## References
- Iqbal, 2021 – Touchless human-computer interaction trends.
- Nath, 2024 – PalmSpace: contact-free palm interaction.
- Babu, Rustamov, & Turaev, 2023 – EfficientNet-Lite for gesture recognition.
- Sun et al., 2024 – Hand-based interaction design guidelines.
- Zeng et al., 2022 – Vending machine gaze tracking.
- Open-source repositories: Gesture-Based Touchless ATM; Touchless-UI; Hand Gesture Recognition for HCI; Gesture-Controlled Virtual Mouse; touchless.

---

## Getting Started
1. Clone the repository:

```bash
git clone https://github.com/AliHachemm/MouseGestureGP.git
