import streamlit as st
import subprocess
import os
import tempfile
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from langchain.memory import ConversationBufferMemory

st.set_page_config(layout="wide")

if 'output' not in st.session_state:
    st.session_state.output = None
if 'carbon_emission' not in st.session_state:
    st.session_state.carbon_emission = 0.0 
if 'compare_output' not in st.session_state:
    st.session_state.compare_output = None
if 'compare_carbon_emission' not in st.session_state:
    st.session_state.compare_carbon_emission = 0.0  
if 'optimized_code' not in st.session_state:
    st.session_state.optimized_code = None
if 'show_results' not in st.session_state:
    st.session_state.show_results = False

carbon_intensity_values = {
    "France": 56,
    "Germany": 475,
    "United States": 405,
    "India": 715,
    "China": 679,
    "Brazil": 84,
    "Canada": 150,
    "United Kingdom": 230,
    "Australia": 720,
}

st.markdown("""
    <style>
        .block-container { padding: 1rem; width: 90%; max-width: 1200px; margin: auto; }
        .navbar { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 0.5rem 1rem; border-bottom: 1px solid #eee; margin-bottom: 1rem; }
        .navbar h1 { font-size: 24px; margin: 0; }
        .output-container { display: flex; flex-direction: column; align-items: center; width: 100%; }

        /* Loader CSS */
        .terminal-loader {
          position: fixed; /* Floating window */
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          border: 0.1em solid #333;
          background-color: #1a1a1a;
          color: #0f0;
          font-family: "Courier New", Courier, monospace;
          font-size: 1em;
          padding: 1.5em 1em;
          width: 12em;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
          border-radius: 4px;
          z-index: 9999;
          overflow: hidden;
          box-sizing: border-box;
          display: none; /* Hidden by default */
        }

        .terminal-loader.active {
          display: block; /* Show when active */
        }

        .terminal-header {
          position: relative;
          height: 1.5em;
          background-color: #333;
          border-top-left-radius: 4px;
          border-top-right-radius: 4px;
          padding: 0 0.4em;
          box-sizing: border-box;
        }

        .control { width: 0.6em; height: 0.6em; border-radius: 50%; background-color: #777; margin-left: 0.4em; }
        .control.close { background-color: #e33; }
        .control.minimize { background-color: #ee0; }
        .control.maximize { background-color: #0b0; }

        .text {
          white-space: nowrap;
          overflow: hidden;
          border-right: 0.2em solid green; /* Cursor */
          animation: typeAndDelete 4s steps(11) infinite, blinkCursor 0.5s step-end infinite alternate;
          margin-top: 1.5em;
        }

        @keyframes blinkCursor {
          50% { border-right-color: transparent; }
        }

        @keyframes typeAndDelete {
          0%, 10% { width: 0; }
          45%, 55% { width: 6.2em; }
          90%, 100% { width: 0; }
        }
    </style>
""", unsafe_allow_html=True)

def navbar():
    st.markdown('<div class="navbar">', unsafe_allow_html=True)
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("<h1 style='font-size: 24px; margin: 0;'>CoTrue Analysis</h1>", unsafe_allow_html=True)
    with col2:
        country = st.selectbox("Select Country", list(carbon_intensity_values.keys()), index=0)
    st.markdown('</div>', unsafe_allow_html=True)
    return country

country = navbar()
CARBON_INTENSITY = carbon_intensity_values[country]

template = '''
You are an AI assistant named Alex. Optimize this code to be more efficient while maintaining functionality:
{code}
Optimized code:
'''
prompt_template = ChatPromptTemplate.from_template(template)
memory = ConversationBufferMemory(return_messages=True)
model = OllamaLLM(model="llama3.2:1b")

def chat_bot(prompt):
    memory.chat_memory.add_user_message(prompt)
    prompt = prompt_template.format(history=memory.load_memory_variables({})["history"], code=prompt)
    result = model(prompt)
    memory.chat_memory.add_ai_message(str(result))
    return str(result)

def run_code(code, language):
    temp_dir = tempfile.mkdtemp()
    source_file = os.path.join(temp_dir, f'code.{language}')
    with open(source_file, 'w') as f:
        f.write(code)

    try:
        start_time = time.time()
        if language == 'python':
            result = subprocess.run(['python', source_file], capture_output=True, text=True)
        elif language == 'c':
            executable = os.path.join(temp_dir, 'a.out')
            compile_result = subprocess.run(['gcc', source_file, '-o', executable], capture_output=True, text=True)
            if compile_result.returncode != 0:
                return f'Compilation failed: {compile_result.stderr}', None
            result = subprocess.run([executable], capture_output=True, text=True)
        else:
            return 'Unsupported language', None
        duration = time.time() - start_time
        carbon_emission = (duration / 3600) * 0.2 * CARBON_INTENSITY / 1000
        output = result.stdout or result.stderr
        return output, carbon_emission
    finally:
        os.remove(source_file)
        if language == 'c' and os.path.exists(executable):
            os.remove(executable)
        os.rmdir(temp_dir)

code = st.text_area("Enter your code here", height=200)
language = st.selectbox("Select the programming language", ("python", "c"))

loader_placeholder = st.empty()

if st.button("Run Code"):
    if code:
        loader_placeholder.markdown("""
            <div class="terminal-loader active">
                <div class="terminal-header">
                    <div class="terminal-title">Status</div>
                    <div class="terminal-controls">
                        <div class="control close"></div>
                        <div class="control minimize"></div>
                        <div class="control maximize"></div>
                    </div>
                </div>
                <div class="text">Running code...</div>
            </div>
        """, unsafe_allow_html=True)
        
        output, carbon_emission = run_code(code, language)
        st.session_state.output = output
        st.session_state.carbon_emission = carbon_emission
        loader_placeholder.empty()

if st.button("Optimize Code"):
    if code:
        loader_placeholder.markdown("""
            <div class="terminal-loader active">
                <div class="terminal-header">
                    <div class="terminal-title">Status</div>
                    <div class="terminal-controls">
                        <div class="control close"></div>
                        <div class="control minimize"></div>
                        <div class="control maximize"></div>
                    </div>
                </div>
                <div class="text">Optimizing code...</div>
            </div>
        """, unsafe_allow_html=True)
        
        optimized_code = chat_bot(code)
        st.session_state.optimized_code = optimized_code
        loader_placeholder.empty()

if st.session_state.output:
    st.subheader("Code Output")
    st.markdown(f"{language}\n{st.session_state.output}\n")
    st.markdown(f"*Carbon Emission (kg CO₂):* {st.session_state.carbon_emission:.15f}")

if st.session_state.optimized_code:
    st.subheader("Optimized Code")
    st.markdown(f"{language}\n{st.session_state.optimized_code}\n")