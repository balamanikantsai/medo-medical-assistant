# Figure Prompts and Detailed Descriptions

This document provides generation prompts and guidance for each figure referenced in the report. Use with your preferred image generation tool (e.g., Illustrator, draw.io, Mermaid → SVG, or text-to-image models). Where applicable, prefer clean SVG for diagrams and PNG for charts.

## 1. System Architecture Diagram
- Prompt: "Create a professional block diagram that depicts a multilingual medical assistant architecture. Include the following labeled components as rounded rectangles: (1) Web UI (Chat, Settings, Upload), (2) Flask API (Routing, Auth, Controllers), (3) Local LLM (Decision + Synthesis), (4) Firecrawl Search (External Web Context), (5) Google Translate (Input/Output normalization), (6) Speech Services (STT/TTS), (7) Persistence (SQLite/Excel user prefs, Chat logs), (8) Google Calendar (Event creation). Arrange left-to-right: UI → Flask → Services/LLM on the right. Draw solid arrows for synchronous calls (UI→Flask, Flask→LLM), dashed arrows for optional paths (Flask→Firecrawl when search_needed), and dotted arrows for background/fallback flows (e.g., TTS synthesis failure fallback to text). Add a semi-transparent red overlay labeled 'Safety & Disclaimers Layer' near the LLM block. Use minimalist flat colors, high-contrast labels (12–14pt), consistent spacing, and 16:9 landscape. Export as clean SVG without raster artifacts."
- Description: Depict the UI at left, Flask API central, downstream services on the right. Use solid arrows for synchronous calls; dashed arrows for optional paths (search). Add a red-bordered "Safety & Disclaimers" overlay near the LLM.

## 2. Conversation Pipeline Flowchart
- Prompt: "Design a flowchart with the following nodes in sequence: Start → User Input → Language Normalization (Translate to English) → Decision Diamond: 'Search Needed?' with outputs YES/NO → If YES: Firecrawl Context Retrieval → Answer Synthesis (LLM) with a subnote 'Conservative tone + disclaimers' → Output Translation (to user’s language) → Text-to-Speech (TTS) → End. Include small shield icons at 'Answer Synthesis' and 'Output Translation' to indicate safety checkpoints. Use clear rectangular nodes, one diamond decision, horizontal flow, arrowheads on connectors, node titles 14pt, body 12pt. Maintain generous padding, flat colors with sufficient contrast. Export as SVG."
- Description: Show the decision diamond branching to Firecrawl or directly to answer synthesis. Mark safety checkpoints before synthesis and after translation.

## 3. Prescription Upload Sequence Diagram
- Prompt: "Draw a sequence diagram with lifelines: User, Flask Server, Local LLM, Schema Validator, Google Calendar API. Messages: (1) User → Flask: Upload prescription.txt, (2) Flask → Flask: Validate extension (.txt) + secure filename, (3) Flask → Local LLM: Parse with low temperature + required JSON schema, (4) Local LLM → Flask: JSON result or parse error, (5) Flask → Schema Validator: Validate fields (diagnosis, medications[]), (6) Validator → Flask: Valid/Invalid, (7) Flask → Google Calendar API: Create event(s) for medication reminders (conditional), (8) Calendar API → Flask: Success/Failure, (9) Flask → User: Success message or structured error JSON. Use monochrome or subtle color, clear arrow labels, activation boxes where relevant. Export as SVG."
- Description: Lifelines: User, Flask, LLM, Validator, Calendar API. Messages include file validation, parse request, parse response, validation outcome, event creation.

## 4. Prescription JSON Schema Visual
- Prompt: "Create a UML-style data schema diagram representing a 'Prescription' JSON object. Top-level fields: diagnosis:string, doctor?:string, date?:string (ISO 8601). Field 'medications' is an array of objects with fields: name:string, dosage:string, frequency:string, timing:string, notes?:string. Use class-like boxes with field names and types, mark optional fields with '?'. Include a small example instance snippet next to the diagram showing one medication (e.g., name:'Amoxicillin', dosage:'500mg', frequency:'3x/day', timing:'after meals'). Keep lines crisp, align fields neatly, export as SVG."
- Description: Present class-like boxes with fields and type annotations. Include one example medication object.

## 5. UI Mockups (Login, Chat, Settings, Upload)
- Prompt: "Produce four clean UI mockups (1920x1080 PNG each) using Material-inspired components: (A) Login screen with 'Username', 'Password', 'Login' button and link to 'Register'; (B) Chat screen with left message pane, input box, send button, and a language indicator chip (e.g., 'es'); (C) Settings screen with language dropdown (English/Hindi/Spanish), save button, and accessibility toggles; (D) Prescription Upload with file picker, 'Parse' button, and result panel. Include a high-contrast accessibility variant for each (dark text on light background, WCAG-friendly color palette)."
- Description: Capture layout and key controls; do not include real user data.

## 6. Latency Distribution Chart
- Prompt: "Generate a side-by-side latency comparison chart (1600x900 PNG): left panel 'Non-search' and right panel 'Search-enabled'. Use boxplots with whiskers plus overlayed markers for p50 and p95. X-axis: Category, Y-axis: Latency (ms). Include legend noting p50/p95 markers, subtle gridlines, and annotations pointing to 'LLM generation' and 'Network call' as bottlenecks. Keep colors flat, high contrast, font legible at print size."
- Description: Two series side-by-side; annotate bottlenecks near LLM generation and network calls.

## 7. Feature Availability Heatmap
- Prompt: "Create a 1600x900 PNG heatmap showing feature availability across credential scenarios. Rows: Features (Translate, STT, TTS, Search). Columns: Scenarios (All present, Missing Translate, Missing Speech, Missing Search, All missing). Color code: Green=Available, Gray=Degraded (fallback to English or text-only), Red=Unavailable. Add legend and footnote: 'Graceful degradation messaging surfaced to users.' Use clear axis labels and consistent cell sizes."
- Description: Rows: features; Columns: credential scenarios. Add footnote: graceful degradation messaging.

## 8. Safety Escalation Model (Planned)
- Prompt: "Illustrate a conceptual model of safety escalation using an SVG diagram. Inputs: Normalized text (post-translation). Stage 1: Classifier layer (intent, emergency risk) producing confidence scores. Stage 2: Decision aggregator with adjustable thresholds and hysteresis, yielding risk levels (Low/Medium/High) color-coded (green/amber/red). Stage 3: Routing—Low → advisory response; Medium → advisory + recommendation to consult professional; High → immediate escalation to human-in-loop review queue. Include icons for human review and logs."
- Description: Show inputs from normalized text, outputs to advisory or escalation path.

## 9. Multilingual Coverage Map
- Prompt: "Render a 2000x1100 PNG world map highlighting current coverage: English, Hindi, Spanish. Use soft region shading for primary language areas, and pin icons for planned expansions. Add callout boxes describing 'Glossary locking priority' and 'Quality estimation checks'. Keep labels minimal, colors soft but distinct, and include a legend for language codes."
- Description: Shade countries where languages are primary; add callouts for planned expansion.

## 10. Test Cases Overview Grid
- Prompt: "Produce a 1600x1000 PNG grid/table summarizing representative test cases. Columns: ID, Category, Input Example, Expected Output, Outcome Status (Pass/Fail). Categories: Auth, Language, Search Decision, Response, Prescription Parsing, Translation, Speech (STT/TTS), Safety, Performance. Use alternating row shading, clear header typography, and ensure text is readable at print scale."
- Description: Include categories: Auth, Language, Search, Response, Prescription, Translation, Speech, Safety, Performance.

## 11. Roadmap Phases Timeline
- Prompt: "Create an SVG horizontal timeline with four phases: (1) Stabilization, (2) Safety Foundation, (3) Clinical Validation, (4) Scale & Research. Under each phase, list 3–4 milestones (e.g., DB migration, test harness; classifier integration, PHI redaction; pilot studies, RLHF cycles; ontology enrichment, provenance). Use simple icons per phase, arrows indicating progression, and consistent typography."
- Description: Short bullets under each phase with dependencies.

## 12. Privacy/PHI Redaction Infographic
- Prompt: "Design a 1600x900 PNG infographic showing the PHI redaction pipeline. Stages: Detection (regex patterns + NER), Redaction (replace PHI spans), Placeholder tokens (e.g., <DATE>, <NAME>), Downstream reasoning (LLM consumes placeholders). Add lock and shield icons, an 'Audit trail' arrow to a logging box, and a small note on data minimization and retention policy."
- Description: Emphasize data minimization and auditability.

## 13. Knowledge Provenance Sankey (Planned)
- Prompt: "Generate an SVG Sankey diagram illustrating knowledge provenance. Left: Sources (web pages with URLs). Middle: Extraction (Firecrawl snippets), Synthesis (LLM merging). Right: User Answer box with citation markers. Thicker flows for heavier contribution weights. Include clean labels, minimal style, and ensure paths are smooth without overlaps."
- Description: Demonstrate traceability for external information.

## 14. Architecture with Failure Isolation Boundaries
- Prompt: "Produce an SVG architecture variant emphasizing failure isolation. Show each external dependency (Translate, STT, TTS, Firecrawl, Calendar) wrapped in dashed red boxes labeled 'Isolation Boundary'. Add arrows from Flask to each with small 'try/except' tags. Include a callout that reads 'Fallback messaging surfaced to user; no cascade failures'. Maintain clean layout and legible labels."
- Description: Clarify how failures do not cascade.

## 15. Accessibility Features Mockup
- Prompt: "Render a 1920x1080 PNG UI mockup highlighting accessibility features: high-contrast theme (dark text on light background), larger base font sizes, a 'Simplified language' toggle, and screen-reader-friendly labels (ARIA-like hints). Include an Accessibility settings panel with checkboxes/toggles, and demonstrate how the Chat screen adapts when simplified mode is on (shorter sentences, clearer headings)."
- Description: Show settings panel enabling accessibility features.

---

Tip: Prefer SVG for diagrams to keep text sharp in the report. Save generated assets under `images/` and reference them in `report.txt` with captions and figure numbers.