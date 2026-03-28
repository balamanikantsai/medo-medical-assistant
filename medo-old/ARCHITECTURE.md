# Medo Assistant: Broad Architectural Overview

## 1. The Big Picture: What is Medo?
At its core, the **Medo Medical Assistant** is an **intelligent orchestration engine** designed to bridge the gap between patients and complex medical information. It is not simply a chatbot; it is a **multilingual, safety-gated, and context-aware system** that acts as a translator, a researcher, and a personal secretary for health-related tasks.

The architecture is built around the philosophy of **"Local Reasoning, Global Knowledge."** It uses a private, local Artificial Intelligence (AI) to understand and process requests, but intelligently reaches out to the internet or external tools only when necessary. This ensures a balance of privacy, speed, and accuracy.

## 2. The Three Pillars of the System
The system architecture rests on three main conceptual pillars:

### A. The Interaction Pillar (The "Senses")
This layer handles how the system communicates with the world. Its primary goal is **Accessibility**.
- **Universal Translator:** The system employs a "Translation Sandwich" approach. No matter what language the user speaks (e.g., Hindi, Spanish), the system translates it to English for processing and then translates the answer back. This allows the core AI to operate at peak performance (in English) while the user remains in their native tongue.
- **Voice-First Design:** Recognizing that typing is difficult for many patients (especially the elderly), the architecture treats **Voice** as a first-class citizen. It has "Ears" (Speech-to-Text) to listen and a "Mouth" (Text-to-Speech) to speak, making the interaction feel like a natural conversation.

### B. The Intelligence Pillar (The "Brain")
This is the decision-making core of the system.
- **Hybrid Intelligence:** Unlike simple bots that just look up keywords, Medo uses a **Large Language Model (LLM)** running locally. This gives it "common sense" and the ability to understand nuance.
- **The Decision Gate:** Before answering, the "Brain" pauses to ask: *"Do I know this, or do I need to check?"*
  - If the user asks *"How do I stay healthy?"*, the Brain answers from its internal wisdom.
  - If the user asks *"What is the latest flu strain?"*, the Brain triggers a **Search Tool (Firecrawl)** to fetch real-time data from the web.
- **Safety Filter:** The architecture includes a rigid safety layer. The Brain is instructed to never provide a medical diagnosis. It is architected to be an **educator**, not a doctor.

### C. The Operational Pillar (The "Hands")
This layer allows the system to take action in the real world.
- **Structured Data Extraction:** The system can look at a messy text file (like a prescription) and "read" it like a human would, extracting the Drug Name, Dosage, and Frequency into a structured format.
- **Calendar Agent:** It connects to the user's digital life (Google Calendar) to turn that structured data into actionable reminders (e.g., *"Take pill at 9 AM"*).

---

## 3. The Narrative Flow: Life of a User Request
To understand the architecture, let's follow a single request through the system:

**Scenario:** A user asks, *"What are the side effects of this new medicine?"*

1.  **Reception (The Entry):** The Web Interface captures the user's voice.
2.  **Transduction (The Ears):** The audio is sent to the **Speech Service**, which converts sound waves into text.
3.  **Normalization (The Translator):** If the text is in Hindi, the **Translation Service** converts it to English.
4.  **Triage (The Decision):** The **Local LLM** analyzes the intent. It tags this request as `[SEARCH_NEEDED]` because "new medicine" implies specific, up-to-date knowledge is required.
5.  **Retrieval (The Research):** The system activates the **Search Agent**, which scours trusted medical websites for the specific medicine and retrieves a summary.
6.  **Synthesis (The Reasoning):** The Local LLM combines the user's question + the search results + safety guidelines to draft a comprehensive, easy-to-understand answer.
7.  **Delivery (The Response):** The English answer is translated back to Hindi.
8.  **Vocalization (The Mouth):** The **Text-to-Speech** engine reads the Hindi response aloud to the user.

---

## 4. Why This Architecture?
This specific architectural design was chosen to solve three critical problems:

1.  **Privacy & Data Sovereignty:**
    By running the "Brain" (LLM) locally on the machine, we minimize the amount of sensitive reasoning data sent to third-party clouds. Only the necessary bits (like audio for transcription or search queries) leave the secure environment.

2.  **Resilience:**
    The modular design means the system is robust. If the Internet goes down, the "Search" module fails, but the "Brain" and "Interaction" layers can still function for general advice and chatting.

3.  **Scalability:**
    The system is **loosely coupled**. We can swap out the Translation engine (e.g., from Google to Azure) or the LLM (e.g., from Llama 3 to Mistral) without rewriting the entire application. This makes the system future-proof.

## 5. Technical Mapping (For Developers)
*   **The Interface:** Flask Web Server (HTML/JS)
*   **The Brain:** Ollama (running Llama 3 / Mistral)
*   **The Ears/Mouth:** Google Speech-to-Text / Text-to-Speech
*   **The Translator:** Google Translate API
*   **The Researcher:** Firecrawl API
*   **The Memory:** SQLite Database & Excel (Legacy)
*   **The Hands:** Google Calendar API

---

## 6. Deep Dive: Understanding the Architectural Philosophy

### 6.1 The Modular Monolith Approach
The Medo Assistant is built as a **Modular Monolith**—a single application that is internally organized into distinct, loosely-coupled modules. This architectural choice represents a middle ground between traditional monolithic applications and fully distributed microservices.

**Why Not Pure Microservices?**
For a healthcare assistant that must guarantee transactional consistency (e.g., logging a user's question and response atomically), splitting every component into separate services would introduce unnecessary complexity, network latency, and failure points. However, we've designed each module (Translation, Speech, LLM, Search) with well-defined interfaces so that they *can* be extracted into microservices in the future if scale demands it.

**Why Not a Traditional Monolith?**
A tightly-coupled monolith would make it impossible to swap components. By maintaining clear boundaries (e.g., the Translation module exposes only `translate_text()`), we can replace Google Translate with Azure Translator without touching the LLM or Speech code.

### 6.2 The Data Flow Architecture: Understanding the "Pipeline"

Think of the system as a **multi-stage data transformation pipeline**, where raw user input undergoes a series of enrichments before becoming a useful response:

```
Raw Input → Normalization → Understanding → Enrichment → Synthesis → Denormalization → Output
```

Let's break down what happens at each stage:

**Stage 1: Normalization (Making Inputs Uniform)**
- **Problem:** Users speak different languages, use different input modalities (text vs voice), and phrase questions in countless ways.
- **Solution:** All inputs are converted to a canonical form: English text.
  - Voice → Text (via STT)
  - Foreign Language → English (via Translation)
  - This creates a single, predictable format for the "Brain" to process.

**Stage 2: Understanding (Intent Recognition)**
- **Problem:** Not all questions require the same treatment. "What is diabetes?" can be answered from the LLM's training data, but "What are the latest COVID statistics?" requires real-time data.
- **Solution:** The LLM performs a **meta-reasoning step** where it classifies the query:
  - Does this need current information? → `[SEARCH_NEEDED]`
  - Can I answer this from my knowledge? → `[NO_SEARCH_NEEDED]`
  - This classification is done via a carefully crafted decision prompt that instructs the LLM to output a tag.

**Stage 3: Enrichment (Knowledge Augmentation)**
- **Problem:** LLMs have a knowledge cutoff date and can hallucinate facts.
- **Solution:** If tagged as `[SEARCH_NEEDED]`, the system:
  - Activates the Firecrawl agent
  - Retrieves 2-4 relevant web snippets from trusted medical sources
  - Injects these as "context" into the next stage
  - This is a simplified implementation of **Retrieval-Augmented Generation (RAG)**.

**Stage 4: Synthesis (Answer Generation)**
- **Problem:** The LLM needs to generate a response that is accurate, safe, and contextually appropriate.
- **Solution:** The system constructs a **composite prompt**:
  ```
  System Instructions: "You are a medical educator. Never diagnose. Always suggest consulting professionals."
  Context: [Search results if any]
  User Question: [The normalized question]
  ```
  - The LLM generates a response constrained by these instructions.
  - **Temperature control** is used here: low temperature (0.2-0.3) for factual responses, slightly higher for conversational warmth.

**Stage 5: Denormalization (Making Outputs Accessible)**
- **Problem:** The LLM's English response needs to be accessible to the user in their original language and preferred modality.
- **Solution:** 
  - Translate English → User's language
  - Convert text → Speech (via TTS)
  - Sanitize text (remove markdown, special characters) to prevent TTS errors.

**Stage 6: Output (Delivery & Logging)**
- The response is sent to the user interface
- **Simultaneously**, the interaction is logged to the database for audit trails and future analysis.

### 6.3 The Security Architecture: Defense in Depth

The system employs multiple layers of security, following the principle of **Defense in Depth**:

**Layer 1: Authentication & Session Management**
- **Password Security:** Passwords are never stored in plaintext. We use the Werkzeug library's `generate_password_hash()` which implements PBKDF2 with SHA-256 hashing and automatic salting.
- **Session Security:** Flask sessions are cryptographically signed using a secret key. Even if an attacker intercepts a session cookie, they cannot modify it without invalidating the signature.
- **Session Timeout:** (Future enhancement) Sessions should expire after inactivity to limit exposure.

**Layer 2: Input Validation**
- **File Upload Security:** 
  - Only `.txt` files are accepted for prescriptions
  - Filenames are sanitized using `secure_filename()` to prevent path traversal attacks (e.g., `../../etc/passwd`)
  - Files are stored in a dedicated `uploads/` directory with restricted permissions
  - Files are deleted after processing to minimize data retention
- **Query Sanitization:** User inputs are passed to the LLM as string data, not executable code, preventing injection attacks.

**Layer 3: API Key Management**
- **Current State:** API keys are stored in JSON files (`translate.json`, `speech-credentials.json`)
- **Improvement Path:** Keys should be moved to environment variables or a secrets management service (e.g., AWS Secrets Manager, Azure Key Vault)
- **Principle of Least Privilege:** Each API key has only the permissions it needs (e.g., the Translation key cannot access Calendar data)

**Layer 4: Data Privacy**
- **Local LLM:** By running the LLM locally (Ollama), sensitive medical queries never leave the server for inference
- **Minimal External Calls:** Only the translation text and search queries are sent to external APIs—the full conversation context stays local
- **HTTPS:** (Production requirement) All web traffic should be encrypted in transit

**Layer 5: Audit Logging**
- Every conversation is logged with:
  - Username
  - Timestamp
  - Prompt
  - Response
  - Inference time
- This creates an immutable audit trail for accountability and debugging

### 6.4 The Scalability Architecture: Designed for Growth

While currently deployed as a single-server application, the architecture has been designed with several scalability patterns in mind:

**Horizontal Scalability (Serving More Users)**
- **Stateless Sessions:** Flask sessions are client-side, meaning any server instance can handle any request. This enables load balancing.
- **Database Bottleneck:** The current SQLite database is a scalability limit. Migration path:
  - **Phase 1:** PostgreSQL on the same server (handles more concurrent connections)
  - **Phase 2:** Managed database service (AWS RDS, Azure SQL) with read replicas
  - **Phase 3:** Database sharding by user ID if needed

**Vertical Scalability (More Powerful Responses)**
- **LLM Optimization:**
  - **Quantization:** The current LLM can be quantized (8-bit or 4-bit) to use less memory while maintaining quality
  - **GPU Acceleration:** Adding a GPU can increase inference speed by 5-10x
  - **Model Distillation:** Create a smaller, faster model trained on the larger model's outputs

**Async Processing (Reducing Wait Times)**
- **Current:** All operations are synchronous (the user waits for each step)
- **Future:** Implement async patterns:
  - Translation and Search can happen in parallel (not sequential)
  - Use WebSockets or Server-Sent Events to stream responses to the user as they're generated
  - Background job queues (Celery) for prescription parsing

### 6.5 The Resilience Architecture: Graceful Degradation

The system is designed to **fail gracefully**—when a component fails, the system continues operating in a reduced capacity rather than crashing completely.

**Fallback Hierarchy:**

1. **Translation Failure:**
   - If Google Translate is unavailable, the system:
     - Continues in English-only mode
     - Displays a warning: "Translation unavailable—responses will be in English"
     - Logs the error for admin review

2. **Speech Service Failure:**
   - If STT/TTS fail:
     - The text interface remains fully functional
     - Voice input buttons are disabled with a message
     - System continues serving text-based users

3. **Search API Failure:**
   - If Firecrawl is down:
     - The LLM still answers from its internal knowledge
     - A disclaimer is added: "Could not verify current information—answer based on training data"

4. **LLM Failure:**
   - If Ollama crashes (critical failure):
     - The system returns a user-friendly error: "The AI is temporarily unavailable"
     - Logs the error with full stack trace
     - Auto-restart mechanisms should be in place (systemd, Docker restart policies)

5. **Database Failure:**
   - If SQLite locks or corrupts:
     - The system can still serve responses (stateless operation)
     - Conversation logging fails silently with error logs
     - Admin is alerted to restore from backup

**Circuit Breaker Pattern (Future Enhancement):**
If an external service fails repeatedly, the system should "open the circuit" and stop calling it for a cooldown period, preventing cascading failures.

### 6.6 The Extensibility Architecture: Plugin Points

The system has several well-defined extension points where new capabilities can be added without modifying core logic:

**Extension Point 1: New Languages**
- Add a new language code to the translation mapping
- Update the UI language selector
- No changes to LLM or core logic needed

**Extension Point 2: New LLM Models**
- Ollama's API is model-agnostic
- To switch from Llama 3 to GPT-4 or Claude:
  - Change the model name in the Ollama call
  - Potentially adjust the system prompt for the new model's personality

**Extension Point 3: New External Knowledge Sources**
- The search module is abstracted behind a simple interface
- To add Wikipedia or PubMed search:
  - Create a new function following the same input/output contract
  - The LLM doesn't need to know where context came from

**Extension Point 4: New Output Modalities**
- The current flow is: Text → TTS → Audio
- Future modalities could include:
  - Braille output (text → Braille translation library)
  - Sign language animation (text → 3D avatar gestures)
  - Visual diagrams (text → diagram generation)

**Extension Point 5: Safety Classifiers**
- Currently, safety is prompt-based
- Future: Insert a classifier module between input and LLM:
  ```
  Input → [Emergency Classifier] → Route to {LLM, Emergency Escalation}
  ```
  - This can be added without touching existing code

### 6.7 The Observability Architecture: Understanding System Behavior

The system includes several mechanisms for monitoring and understanding its behavior:

**Logging Hierarchy:**
- **Info:** Successful operations (user login, response generated)
- **Warning:** Degraded functionality (translation unavailable)
- **Error:** Failures (API timeout, file upload error)

**Metrics to Track (Future):**
- **Latency:** p50, p95, p99 response times
- **Throughput:** Requests per second
- **Error Rates:** Percentage of failed requests
- **LLM Performance:** Average tokens/second
- **User Engagement:** Session duration, messages per session

**Distributed Tracing (Future):**
When a request touches multiple services (Translation → LLM → TTS), trace IDs can follow the request through the entire pipeline, making debugging easier.

### 6.8 The Ethical Architecture: Responsible AI by Design

The architecture embeds ethical considerations into its core design:

**Non-Diagnostic Constraint:**
- The system prompt explicitly forbids diagnosis
- Future: Add a classifier to detect and block diagnostic-sounding responses

**Transparency:**
- When search is used, sources are (or should be) cited
- When translation is used, the user is informed
- When confidence is low, the system should say "I'm not certain..."

**Privacy by Default:**
- Minimal data retention (uploads deleted after processing)
- Local LLM (sensitive reasoning doesn't leave the server)
- No user tracking or analytics without explicit consent

**Accessibility:**
- Voice-first design for users who can't type
- Multilingual support for non-English speakers
- Simple language (future: reading level adjustment)

**Auditability:**
- Every interaction is logged
- Enables review of system decisions
- Supports accountability in case of errors

---

## 7. Conclusion: A Living Architecture

This architecture is not static—it's designed to evolve. The modular structure, clear interfaces, and extensibility points mean that Medo can grow from a prototype to a production-grade system without requiring a complete rewrite.

The key architectural principles that guide this evolution are:
1. **Privacy First:** Keep sensitive processing local
2. **Fail Gracefully:** Never crash completely
3. **Stay Modular:** Make components replaceable
4. **Log Everything:** Create audit trails
5. **Optimize for Users:** Accessibility and simplicity trump technical purity

As the system matures, we anticipate migrations in several areas:
- Excel → PostgreSQL (persistence)
- Prompt-based safety → Classifier-based safety (reliability)
- Synchronous → Asynchronous (performance)
- Single server → Distributed deployment (scale)

But the core architecture—the three pillars of Interaction, Intelligence, and Operation—will remain stable.

