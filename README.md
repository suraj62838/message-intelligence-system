# Message Intelligence System

A privacy-first AI-powered system that analyzes messages, classifies them into meaningful categories, extracts tasks and events, and detects and masks sensitive information.

The system is built using **Next.js, Tailwind CSS, FastAPI, Python, and Groq API**.

---

## Overview

The Message Intelligence System processes a chronological collection of messages and converts unstructured message content into structured information.

The system can:

- Classify messages into six categories
- Calculate classification confidence
- Provide a reason for each classification
- Extract tasks and reminders
- Extract meetings and events
- Identify dates, deadlines, times, and people when explicitly available
- Detect sensitive information
- Mask sensitive values
- Assign sensitivity risk levels
- Recommend privacy actions
- Display results through a web dashboard

The project was developed for an individual message-processing assignment using a dataset containing **900 fictional messages**.

> **Privacy Note:** The original assignment dataset is not included in this public repository.

---

## Features

- CSV dataset upload
- Chronological message processing
- AI-assisted message classification
- Six message categories
- Confidence scores
- Classification explanations
- Task extraction
- Meeting and event extraction
- Deadline and date extraction
- Person extraction
- Sensitive information detection
- Sensitive value masking
- Risk-level classification
- Privacy recommendations
- Dashboard statistics
- Tasks & Events page
- Sensitive Information page
- Processing progress indicator
- Cloud deployment support

---

## Technology Stack

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend

- Python
- FastAPI
- Pandas

### AI

- Groq API
- LLM-based classification and analysis
- Local rule-based processing for sensitive information

### Deployment

- Vercel — Frontend
- Render — Backend

---

## System Architecture

```text
                     CSV Dataset
                         |
                         v
                +------------------+
                |  FastAPI Backend |
                +--------+---------+
                         |
             +-----------+-----------+
             |                       |
             v                       v
     Sensitive Detection       Message Analysis
       & Masking                    |
             |              +--------+--------+
             |              |                 |
             |              v                 v
             |        Classification    Task/Event
             |                           Extraction
             |              |                 |
             +--------------+-----------------+
                            |
                            v
                    Structured Results
                            |
                            v
                  +-------------------+
                  |   Next.js UI      |
                  |     Dashboard     |
                  +-------------------+