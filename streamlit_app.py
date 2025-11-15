import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Try to find and load .env file
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)
else:
    load_dotenv()

# Debug: Check if API key is loaded
api_key = os.getenv('BROWSER_USE_API_KEY')
if not api_key:
    print("❌ WARNING: BROWSER_USE_API_KEY not found!")
    print(f"Current directory: {Path.cwd()}")
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith('BROWSER_USE_API_KEY'):
                    key = line.split('=', 1)[1].strip()
                    os.environ['BROWSER_USE_API_KEY'] = key
                    print(f"✅ Manually loaded API key from .env")
                    break

# Set headless mode
os.environ['HEADLESS'] = 'true'
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '0'

import asyncio
import json
import streamlit as st
from datetime import datetime
from playwright.async_api import async_playwright
from browser_use import Agent, ChatBrowserUse
from collections import defaultdict

# Galileo integration (Official SDK)
try:
    from galileo import galileo_context
    from galileo.config import GalileoPythonConfig
    GALILEO_AVAILABLE = True
    print("✅ Galileo SDK is available")
except ImportError:
    GALILEO_AVAILABLE = False
    print("⚠️  Galileo not installed")

# ============================================================
# CHROME CONNECTION
# ============================================================

async def fetch_all_chrome_urls():
    """Fetch all URLs from all tabs in Chrome across multiple instances."""
    playwright = await async_playwright().start()
    
    ports_to_check = [9222, 9223, 9224, 9225, 9226]
    all_urls = []
    connected_ports = []
    
    try:
        for port in ports_to_check:
            try:
                print(f"🔍 Checking port {port}...")
                browser = await playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                
                print(f"✅ Connected to Chrome on port {port}")
                print(f"🔍 Found {len(browser.contexts)} browser context(s)")
                connected_ports.append(port)
                
                for ctx_idx, context in enumerate(browser.contexts):
                    pages = context.pages
                    print(f"🪟 Context {ctx_idx + 1}: {len(pages)} page(s)")
                    
                    for page_idx, page in enumerate(pages):
                        try:
                            url = page.url
                            title = await page.title()
                            
                            if url in ['about:blank', 'chrome://newtab/', ''] or url.startswith('chrome://'):
                                continue
                            
                            tab_info = {
                                'port': port,
                                'window': ctx_idx + 1,
                                'tab': page_idx + 1,
                                'url': url,
                                'title': title
                            }
                            
                            all_urls.append(tab_info)
                            
                        except Exception as e:
                            continue
                
                await browser.close()
                
            except Exception as e:
                continue
        
        if connected_ports:
            print(f"\n{'='*70}")
            print(f"✅ Connected to Chrome on ports: {connected_ports}")
            print(f"✅ Found {len(all_urls)} tabs total across all instances")
            print(f"{'='*70}\n")
        else:
            print(f"\n❌ No Chrome instances found")
        
        return all_urls
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return []
        
    finally:
        await playwright.stop()


# ============================================================
# AI ANALYSIS
# ============================================================

async def analyze_urls(tabs, custom_task):
    """Analyze tabs using Browser Use with Galileo tracking."""
    
    if not tabs:
        return None
    
    # Initialize Galileo if available
    logger = None
    galileo_session_started = False
    
    if GALILEO_AVAILABLE:
        try:
            project_name = os.getenv('GALILEO_PROJECT_NAME', 'chrome-tab-analyzer')
            log_stream = os.getenv('GALILEO_LOG_STREAM', 'tab-analysis')
            
            galileo_context.init(project=project_name, log_stream=log_stream)
            logger = galileo_context.get_logger_instance()
            logger.start_session()
            galileo_session_started = True
            print(f"✅ Galileo session started for project: {project_name}")
        except Exception as e:
            print(f"⚠️  Galileo initialization failed: {e}")
            logger = None
    
    # Format URLs
    urls_text = "\n".join([f"{i+1}. {tab['title']} - {tab['url']}" for i, tab in enumerate(tabs)])
    
    # Create task
    task = f"""
    I have {len(tabs)} browser tabs saved. Here's the list:
    
    {urls_text}
    
    {custom_task}
    """
    
    # Start Galileo trace
    if logger and galileo_session_started:
        try:
            logger.start_trace(name="Browser Tab Analysis", input=task)
            start_time_ns = datetime.now().timestamp() * 1_000_000_000
        except Exception as e:
            print(f"⚠️  Galileo trace failed: {e}")
    
    # Run Browser Use analysis
    llm = ChatBrowserUse()
    agent = Agent(task=task, llm=llm)
    
    result = await agent.run()
    
    # Get analysis
    analysis = result.final_result()
    clean_analysis = analysis.replace('\\n', '\n') if analysis else "Analysis failed"
    
    # Log to Galileo
    if logger and galileo_session_started:
        try:
            duration_ns = (datetime.now().timestamp() * 1_000_000_000) - start_time_ns
            
            logger.add_llm_span(
                input=task,
                output=clean_analysis,
                model="browser-use-agent",
                num_input_tokens=len(task) // 4,
                num_output_tokens=len(clean_analysis) // 4,
                total_tokens=(len(task) + len(clean_analysis)) // 4,
                duration_ns=int(duration_ns),
            )
            
            logger.conclude(output=clean_analysis)
            logger.flush()
            
            print("✅ Logged to Galileo")
            
            config = GalileoPythonConfig.get()
            project_url = f"{config.console_url}project/{logger.project_id}"
            log_stream_url = f"{project_url}/log-streams/{logger.log_stream_id}"
            print(f"🔗 Galileo Project: {project_url}")
            print(f"📊 Log Stream: {log_stream_url}")
            
        except Exception as e:
            print(f"⚠️  Galileo logging failed: {e}")
    
    return clean_analysis


# ============================================================
# STREAMLIT APP
# ============================================================

def main():
    st.set_page_config(
        page_title="Chrome Tab Analyzer",
        page_icon="🌐",
        layout="wide"
    )
    
    st.title("🌐 Chrome Tab Analyzer")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        **Step 1:** Launch Chrome with remote debugging:
        
        **macOS:**
        ```bash
        /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-debug" &
        ```
        
        **Step 2:** Open your tabs in Chrome
        
        **Step 3:** Click "Fetch Tabs"
        
        **Step 4:** Analyze!
        """)
        
        st.markdown("---")
        
        # Galileo status
        if GALILEO_AVAILABLE:
            st.success("✅ Galileo SDK enabled")
            st.caption(f"Project: {os.getenv('GALILEO_PROJECT_NAME', 'chrome-tab-analyzer')}")
        else:
            st.info("💡 Galileo not configured")
        
        st.markdown("---")
        st.markdown("**💡 Example Tasks:**")
        st.markdown("""
        - Summarize what I'm researching
        - Find duplicate tabs
        - Organize by category
        - Create reading list
        """)
    
    # Main content
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔄 Fetch Tabs", use_container_width=True, type="primary"):
            with st.spinner("Fetching tabs..."):
                tabs = asyncio.run(fetch_all_chrome_urls())
                
                if tabs:
                    st.session_state['tabs'] = tabs
                    st.session_state['timestamp'] = datetime.now().isoformat()
                    st.success(f"✅ Found {len(tabs)} tabs!")
                else:
                    st.error("❌ No tabs found")
    
    with col2:
        if 'tabs' in st.session_state:
            st.info(f"📊 **{len(st.session_state['tabs'])} tabs** loaded")
    
    st.markdown("---")
    
    # Display tabs if available
    if 'tabs' in st.session_state and st.session_state['tabs']:
        tabs = st.session_state['tabs']
        
        # Tabs preview
        with st.expander(f"👀 View All {len(tabs)} Tabs", expanded=False):
            tabs_by_port = defaultdict(list)
            for tab in tabs:
                tabs_by_port[tab.get('port', 'Unknown')].append(tab)
            
            for port in sorted(tabs_by_port.keys()):
                port_tabs = tabs_by_port[port]
                st.markdown(f"### 🌐 Chrome Instance (Port {port}) - {len(port_tabs)} tabs")
                
                for i, tab in enumerate(port_tabs):
                    st.markdown(f"**{i+1}.** {tab['title']}")
                    st.caption(f"🔗 {tab['url']}")
                    if i < len(port_tabs) - 1:
                        st.markdown("---")
        
        st.markdown("---")
        
        # Task input
        st.subheader("🎯 What would you like me to do with these tabs?")
        
        quick_tasks = {
            "Analyze & Categorize": "Please analyze these tabs and tell me:\n1. What categories/topics do they fall into?\n2. Which domains appear most?\n3. What am I probably working on or researching?\n4. Any duplicate or similar tabs I should close?",
            "Find Duplicates": "Find any duplicate or very similar tabs that I should close. List them clearly.",
            "Create Reading List": "Organize these tabs into a prioritized reading list. Group by topic and suggest an order.",
            "Summarize Research": "Summarize what I'm researching based on these tabs. What are the main themes and connections?",
            "Time Management": "Which of these tabs are time-wasters vs. productive? Help me focus.",
            "Custom": ""
        }
        
        task_type = st.radio(
            "Choose a task type:",
            options=list(quick_tasks.keys()),
            horizontal=True
        )
        
        if task_type == "Custom":
            custom_task = st.text_area(
                "Enter your custom task:",
                height=150,
                placeholder="Example: Find all tabs related to Python..."
            )
        else:
            custom_task = st.text_area(
                "Task (you can edit this):",
                value=quick_tasks[task_type],
                height=150
            )
        
        # Analyze button
        if st.button("🤖 Analyze Tabs", use_container_width=True, type="primary"):
            if not custom_task.strip():
                st.error("❌ Please enter a task!")
            else:
                with st.spinner("🧠 AI is analyzing your tabs..."):
                    analysis = asyncio.run(analyze_urls(tabs, custom_task))
                    
                    if analysis:
                        st.session_state['analysis'] = analysis
                        st.success("✅ Analysis complete!")
                    else:
                        st.error("❌ Analysis failed.")
        
        # Display analysis
        if 'analysis' in st.session_state:
            st.markdown("---")
            st.subheader("📊 Analysis Results")
            st.markdown(st.session_state['analysis'])
            
            # Download options
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "💾 Download as Text",
                    st.session_state['analysis'],
                    file_name=f"tab_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            with col2:
                export_data = {
                    'timestamp': st.session_state.get('timestamp'),
                    'total_tabs': len(tabs),
                    'task': custom_task,
                    'analysis': st.session_state['analysis'],
                    'tabs': tabs
                }
                st.download_button(
                    "📋 Download as JSON",
                    json.dumps(export_data, indent=2),
                    file_name=f"tab_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    else:
        st.info("👆 Click 'Fetch Tabs' to get started!")


if __name__ == "__main__":
    main()