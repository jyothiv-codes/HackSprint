# HackSprint
MemoryBrowse

## Inspiration - Everyone opens dozens of tabs while researching, learning, or coding, but information gets buried, lost, or forgotten. Re-finding pages breaks focus and wastes time. MemoryBrowse was created to solve this problem by giving users a persistent, intelligent memory of their browsing history.

## What it does 
MemoryBrowse is an AI-powered browsing companion that:
- Stores the full content of any webpage a user wants to remember
- Generates semantic embeddings to organize pages by meaning, not keywords
- Lets users ask natural questions like:
“Where was that page about Python functions?”
- Finds the most relevant past tab instantly
- Provides summaries and answers based on the recalled page
MemoryBrowse transforms browsing into a searchable, smart memory system.


## How I built it
- Browser Use :  automates page navigation and extracts visible content. The extracted pages + titles are stored in a structured memory file
- Daytona :  Provides isolated sandbox environments for secure AI code execution, ensuring each analysis runs in a fresh, containerized workspace that's automatically destroyed after completion.
- Galileo - Tracks all LLM interactions with detailed observability - logging prompts, responses, token usage, and performance metrics to enable debugging and optimization of the AI agent's behavior.

The result is a lightweight, intelligent recall system powered by partner tools

## Challenges I ran into
- Network Isolation: Browser Use couldn't run in Daytona sandboxes due to blocked external API calls - required building local execution fallback with session-based sandbox reuse optimization.
- Observability Gaps: Browser Use's abstraction layer hides actual LLM calls, forcing token count estimation for Galileo logging instead of exact metrics.
- Chrome Remote Debugging: Handling multiple browser instances across ports while managing connection lifecycles and avoiding memory leaks from orphaned browser contexts.

## Accomplishments that we're proud of

- Transformed Tab Chaos into Clarity: Created an experience where users go from "I have 100 tabs and I'm overwhelmed" to "Here's exactly what I'm researching, what's duplicate, and what matters" - in under 30 seconds with natural language queries.

- Flexible Query System: Instead of hardcoded analysis, users ask anything in natural language - "What am I researching?", "Find duplicates", "Create a reading list", or completely custom queries. The AI adapts to what users actually need, not what we thought they'd want.

- Production-grade architecture: MemoryBrowse is built with enterprise-level thinking - Daytona sandboxes for security, Galileo for observability, and graceful fallbacks. It is made ready for real users with proper monitoring, error handling, and resource optimization.


## What I learnt

- Users Want Flexibility Over Features: Our preset tasks ("Analyze & Categorize", "Find Duplicates") are useful, but the "Custom" option gets the most creative use. Users know their problems better than we do - our job is giving them tools, not prescribing solutions.

- Security and Privacy Are Features, Not Afterthoughts: Designing with Daytona sandboxes from the start forced us to think about data isolation, user privacy, and secure execution. These aren't nice-to-haves for AI products - they're fundamental requirements that shape the entire architecture.

## What's next for MemoryBrowse
- Smart Tab Sessions: Automatically save and restore different browsing contexts (work, research, shopping) with one click. Users could switch between "ML Research Mode" and "Trip Planning Mode" instantly, with AI remembering the context and purpose of each session.
- Proactive Recommendations: Instead of waiting for user queries, MemoryBrowse could notify you: "You have 5 duplicate tabs," "These 10 tabs haven't been viewed in 2 weeks," or "These 3 articles relate to your current research - read them next."
- Cross-Browser Support: Expand beyond Chrome to Firefox, Edge, and Safari. Make MemoryBrowse the universal tab intelligence layer that works regardless of browser choice.

## Demo - https://youtu.be/OtLjGa5CdfE
