import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os

st.set_page_config(page_title="ArtRestorer AI", page_icon="🎨", layout="wide")

# Custom CSS - COMPLETELY FIXED COLOR SCHEME
st.markdown("""
<style>
    .stApp {
        background: #F5F1E8;
    }
    h1 {
        font-family: Georgia, serif;
        color: #4A5D3F;
        text-align: center;
    }
    .tagline {
        text-align: center;
        color: #6B7A5E;
        font-style: italic;
        margin-bottom: 2rem;
    }
    
    /* FIX ALL TEXT INPUTS - WHITE BACKGROUND, DARK TEXT */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        color: #2C3E50 !important;
        background-color: white !important;
    }
    
    /* FIX ALL LABELS - VISIBLE GREEN COLOR */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stNumberInput > label,
    .stSlider > label {
        color: #4A5D3F !important;
    }
    
    /* FIX SLIDER */
    .stSlider > div > div > div > div {
        background-color: #4A5D3F !important;
    }
    
    /* FIX ALL PARAGRAPH TEXT */
    p, span, div {
        color: #2C3E50 !important;
    }
    
    /* FIX SELECTBOX DROPDOWN OPTIONS */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: white !important;
        color: #2C3E50 !important;
    }
    
    /* FIX DROPDOWN MENU POPUP */
    [data-baseweb="popover"] {
        background-color: white !important;
    }
    
    [data-baseweb="menu"] {
        background-color: white !important;
    }
    
    [role="option"] {
        background-color: white !important;
        color: #2C3E50 !important;
    }
    
    [role="option"]:hover {
        background-color: #F0F0F0 !important;
        color: #2C3E50 !important;
    }
    
    /* FIX DROPDOWN LIST ITEMS */
    ul[role="listbox"] {
        background-color: white !important;
    }
    
    ul[role="listbox"] li {
        background-color: white !important;
        color: #2C3E50 !important;
    }
    
    ul[role="listbox"] li:hover {
        background-color: #E8F5E9 !important;
        color: #2C3E50 !important;
    }
    
    /* FIX FORM SUBMIT BUTTON TEXT */
    .stButton > button {
        color: white !important;
        background-color: #4A5D3F !important;
    }
    
    /* FIX SIDEBAR TEXT */
    .css-1d391kg, .css-1v0mbdj {
        color: white !important;
    }
    
    /* FIX EXPANDER HEADERS */
    .streamlit-expanderHeader {
        color: #2C3E50 !important;
    }
    
    /* FIX CHAT MESSAGES */
    .stChatMessage {
        background-color: white !important;
    }
    
    /* FIX ALL TEXT IN FORMS */
    [data-testid="stForm"] {
        background-color: transparent !important;
    }
    
    [data-testid="stForm"] p,
    [data-testid="stForm"] span,
    [data-testid="stForm"] label {
        color: #2C3E50 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'welcome'
if 'user' not in st.session_state:
    st.session_state.user = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# Configure Gemini - DYNAMICALLY FIND AVAILABLE MODEL
model = None
api_error = None
api_key = None
available_models = []

try:
    # Method 1: Try Streamlit secrets (standard location)
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        pass
    
    # Method 2: Try reading from .secrets/secrets.toml (your teacher's structure)
    if not api_key:
        secrets_path = ".secrets/secrets.toml"
        if os.path.exists(secrets_path):
            try:
                with open(secrets_path, 'r') as f:
                    content = f.read()
                    # Parse the TOML file manually
                    for line in content.split('\n'):
                        if 'GEMINI_API_KEY' in line and '=' in line:
                            # Extract the key from line like: GEMINI_API_KEY = "key_here"
                            api_key = line.split('=')[1].strip().strip('"').strip("'")
                            break
            except Exception as e:
                api_error = f"Found .secrets/secrets.toml but couldn't read it: {str(e)}"
    
    # Method 3: Try reading from .streamlit/secrets.toml
    if not api_key:
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            try:
                with open(secrets_path, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if 'GEMINI_API_KEY' in line and '=' in line:
                            api_key = line.split('=')[1].strip().strip('"').strip("'")
                            break
            except Exception as e:
                api_error = f"Found .streamlit/secrets.toml but couldn't read it: {str(e)}"
    
    # Method 4: Try environment variable
    if not api_key:
        api_key = os.getenv('GEMINI_API_KEY')
    
    # Configure the API if we found a key
    if api_key:
        genai.configure(api_key=api_key)
        
        # DYNAMICALLY LIST AND SELECT AVAILABLE MODELS
        try:
            # Get list of all available models that support generateContent
            all_models = genai.list_models()
            for m in all_models:
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            
            # Prefer gemini models in this order
            preferred_models = [
                'models/gemini-1.5-flash',
                'models/gemini-1.5-pro',
                'models/gemini-pro',
                'models/gemini-1.0-pro',
            ]
            
            # Find the first available preferred model
            model_name = None
            for pref in preferred_models:
                if pref in available_models:
                    model_name = pref
                    break
            
            # If no preferred model found, use the first available one
            if not model_name and available_models:
                model_name = available_models[0]
            
            if model_name:
                model = genai.GenerativeModel(model_name)
            else:
                api_error = "No models supporting generateContent found for your API key"
                
        except Exception as e:
            api_error = f"Error listing models: {str(e)}"
    else:
        api_error = "No API key found. Please add GEMINI_API_KEY to .secrets/secrets.toml or .streamlit/secrets.toml"
        
except Exception as e:
    api_error = f"Error configuring API: {str(e)}"

def generate_response(prompt, user_profile):
    if not model:
        error_msg = f"⚠️ API Configuration Error: {api_error}\n\n"
        
        if available_models:
            error_msg += f"Available models found: {', '.join(available_models)}\n\n"
        
        error_msg += """Please check:
1. Your API key is valid (get from: https://aistudio.google.com/app/apikey)
2. You have enabled the Gemini API
3. Add to .secrets/secrets.toml:
   GEMINI_API_KEY = "your-key-here"
"""
        return error_msg
    
    try:
        system_prompt = f"""You are an art restoration expert.
User profile: {user_profile.get('experience', 'intermediate')} level
Tone: {user_profile.get('tone', 'academic')}
Creativity: {user_profile.get('creativity', 5)}/10
Detail: {user_profile.get('length', 5)}/10

{prompt}"""
        
        response = model.generate_content(system_prompt)
        return response.text
        
    except Exception as e:
        return f"Error generating response: {str(e)}"

# WELCOME PAGE
if st.session_state.page == 'welcome':
    st.markdown("<h1>🎨 ArtRestorer AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='tagline'>Reviving Cultural Heritage Through Ethical Generative AI</p>", unsafe_allow_html=True)
    
    st.markdown("<p style='color: #2C3E50;'>Many historical artworks are damaged or partially lost. This application provides AI-assisted, text-based restoration guidance for museums, students, and cultural researchers.</p>", unsafe_allow_html=True)
    
    # Show API status with detailed info
    if api_error:
        st.error(f"⚠️ API Configuration Issue: {api_error}")
        
        if available_models:
            st.warning(f"📋 Found {len(available_models)} available models, but couldn't initialize")
            with st.expander("Available Models"):
                for m in available_models:
                    st.write(f"- {m}")
        
        st.info("""💡 **How to fix:**

**Step 1: Get a NEW API key from Google AI Studio**
- Go to: https://aistudio.google.com/app/apikey
- Click "Get API Key"
- Click "Create API key in new project"
- Copy the ENTIRE key (starts with AIza)

**Step 2: Add to your secrets file**
Open `.secrets/secrets.toml` and make sure it has:
```
GEMINI_API_KEY = "paste-your-full-key-here"
```

**Step 3: Restart the app**
Press Ctrl+C in terminal, then run:
```
streamlit run app.py
```
""")
        
        # Debug info
        with st.expander("🔍 Debug Information"):
            st.write("API Key found:", "Yes" if api_key else "No")
            if api_key:
                st.write(f"API Key starts with: {api_key[:10]}...")
                st.write(f"API Key length: {len(api_key)} characters")
            st.write(f"Available models: {len(available_models)}")
            st.write(f".secrets/secrets.toml exists: {os.path.exists('.secrets/secrets.toml')}")
            st.write(f".streamlit/secrets.toml exists: {os.path.exists('.streamlit/secrets.toml')}")
    else:
        st.success("✅ API Configured Successfully")
        if model:
            st.info(f"Using model: {model.model_name}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info("📜\n\nText-Based Guidance")
    with col2:
        st.info("🎨\n\nCultural Interpretation")
    with col3:
        st.info("✨\n\nEthical AI Principles")
    with col4:
        st.info("🏛️\n\nMuseum-Quality Insights")
    
    if st.button("Login / Get Started", use_container_width=True):
        st.session_state.page = 'login'
        st.rerun()

# LOGIN PAGE
elif st.session_state.page == 'login':
    st.markdown("<h1 style='color: #4A5D3F;'>Create Your Profile</h1>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", key="name_input")
            email = st.text_input("Email", key="email_input")
        with col2:
            age = st.number_input("Age", 1, 120, 25, key="age_input")
            experience = st.selectbox("Experience", ["beginner", "intermediate", "advanced"], key="exp_input")
        
        password = st.text_input("Password", type="password", key="pass_input")
        creativity = st.slider("Creativity Level", 1, 10, 5, key="creativity_input")
        length = st.slider("Output Length", 1, 10, 5, key="length_input")
        tone = st.selectbox("Tone", ["academic", "simplified"], key="tone_input")
        
        submit_col1, submit_col2 = st.columns([3, 1])
        with submit_col1:
            if st.form_submit_button("Create Profile", use_container_width=True):
                if name and email:
                    st.session_state.user = {
                        'name': name, 'email': email, 'age': age,
                        'experience': experience, 'creativity': creativity,
                        'length': length, 'tone': tone
                    }
                    st.session_state.page = 'dashboard'
                    st.rerun()
                else:
                    st.error("Please fill in Name and Email")
    
    if st.button("← Back"):
        st.session_state.page = 'welcome'
        st.rerun()

# DASHBOARD
elif st.session_state.page == 'dashboard' and st.session_state.user:
    
    with st.sidebar:
        st.markdown("## 🎨 ArtRestorer AI")
        st.markdown(f"**{st.session_state.user['name']}**")
        st.markdown(f"{st.session_state.user['email']}")
        st.divider()
        
        menu = st.radio("Menu", [
            "🎨 Restoration Workspace",
            "💬 AI Chatbot",
            "📚 Art Guide",
            "📋 History",
            "⚙️ Settings",
            "⚖️ Ethics"
        ])
        
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.session_state.page = 'welcome'
            st.rerun()
    
    # RESTORATION WORKSPACE
    if menu == "🎨 Restoration Workspace":
        st.markdown("<h1 style='color: #4A5D3F;'>Restoration Workspace</h1>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            with st.form("restoration_form"):
                artwork_type = st.selectbox("Artwork Type", ["", "Painting", "Sculpture", "Manuscript", "Textile", "Mural"], key="artwork_input")
                art_period = st.text_input("Art Period/Style", key="period_input")
                artist = st.text_input("Artist Name (Optional)", key="artist_input")
                region = st.text_input("Cultural Region (Optional)", key="region_input")
                damage = st.text_area("Damage Description", height=150, key="damage_input")
                output_type = st.selectbox("Output Type", ["", "Restoration Technique", "Stylistic Reconstruction", "Symbol Interpretation", "Visitor Summary", "Conservation Advice"], key="output_input")
                
                if st.form_submit_button("Generate Guidance", use_container_width=True):
                    if artwork_type and damage and output_type:
                        prompt = f"""Artwork: {artwork_type}
Period: {art_period}
Artist: {artist}
Region: {region}
Damage: {damage}
Output: {output_type}

Provide detailed restoration guidance."""
                        
                        with st.spinner("Generating..."):
                            response = generate_response(prompt, st.session_state.user)
                            st.session_state.current_output = {
                                'artwork': artwork_type, 'period': art_period,
                                'damage': damage, 'output': output_type,
                                'response': response, 'time': datetime.now()
                            }
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields")
        
        with col2:
            st.markdown("<h2 style='color: #4A5D3F;'>AI-Generated Guidance</h2>", unsafe_allow_html=True)
            
            if 'current_output' in st.session_state:
                st.markdown(f"<p style='color: #2C3E50;'><strong>Time:</strong> {st.session_state.current_output['time'].strftime('%Y-%m-%d %H:%M')}</p>", unsafe_allow_html=True)
                st.divider()
                st.markdown(f"<div style='color: #2C3E50; background-color: white; padding: 20px; border-radius: 10px;'>{st.session_state.current_output['response']}</div>", unsafe_allow_html=True)
                
                st.write("")  # spacing
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("💾 Save", use_container_width=True):
                        st.session_state.history.append(st.session_state.current_output)
                        st.success("Saved!")
                
                with col_b:
                    text = f"""ArtRestorer AI Report
Time: {st.session_state.current_output['time']}
Artwork: {st.session_state.current_output['artwork']}
Period: {st.session_state.current_output['period']}
Damage: {st.session_state.current_output['damage']}

{st.session_state.current_output['response']}"""
                    st.download_button("📥 Export", text, f"restoration_{datetime.now().strftime('%Y%m%d')}.txt", use_container_width=True)
            else:
                st.info("Fill the form and generate guidance")
    
    # AI CHATBOT
    elif menu == "💬 AI Chatbot":
        st.markdown("<h1 style='color: #4A5D3F;'>AI Chatbot</h1>", unsafe_allow_html=True)
        
        if not st.session_state.chat_messages:
            st.session_state.chat_messages = [{
                "role": "assistant",
                "content": f"Hello {st.session_state.user['name']}! I'm your AI assistant for art restoration. How can I help?"
            }]
        
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(f"<p style='color: #2C3E50;'>{msg['content']}</p>", unsafe_allow_html=True)
        
        if prompt := st.chat_input("Ask about art restoration..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(f"<p style='color: #2C3E50;'>{prompt}</p>", unsafe_allow_html=True)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = generate_response(f"Art restoration question: {prompt}", st.session_state.user)
                    st.markdown(f"<p style='color: #2C3E50;'>{response}</p>", unsafe_allow_html=True)
            
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    # ART GUIDE
    elif menu == "📚 Art Guide":
        st.markdown("<h1 style='color: #4A5D3F;'>Art Guide</h1>", unsafe_allow_html=True)
        
        with st.expander("🎨 Major Art Periods", expanded=True):
            st.markdown("""
            <div style='color: #2C3E50;'>
            <strong>Ancient (3000 BCE - 400 CE):</strong> Egyptian, Greek, Roman<br><br>
            <strong>Medieval (400 - 1400):</strong> Byzantine, Romanesque, Gothic<br><br>
            <strong>Renaissance (1400 - 1600):</strong> Linear perspective, naturalism, humanism<br><br>
            <strong>Baroque (1600 - 1750):</strong> Drama, movement, rich color<br><br>
            <strong>Modern (1850 - 1970):</strong> Impressionism, Expressionism, Cubism, Abstract<br><br>
            <strong>Contemporary (1970 - Present):</strong> Diverse movements, new media
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("🔧 Common Damage Types"):
            st.markdown("""
            <div style='color: #2C3E50;'>
            • <strong>Paint Layer Damage:</strong> Cracking, flaking, blistering<br>
            • <strong>Canvas Issues:</strong> Tears, punctures, sagging<br>
            • <strong>Environmental:</strong> Water stains, mold growth<br>
            • <strong>Chemical:</strong> Darkened varnish, oxidation<br>
            • <strong>Physical:</strong> Scratches, broken fragments
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("⚖️ Ethical Principles"):
            st.markdown("""
            <div style='color: #2C3E50;'>
            • Respect for Authenticity<br>
            • Minimal Intervention<br>
            • Reversibility<br>
            • Documentation<br>
            • Cultural Sensitivity<br>
            • Professional Competence
            </div>
            """, unsafe_allow_html=True)
    
    # HISTORY
    elif menu == "📋 History":
        st.markdown("<h1 style='color: #4A5D3F;'>Saved History</h1>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Saved Records", len(st.session_state.history))
        with col2:
            st.metric("Chat Messages", len(st.session_state.chat_messages))
        with col3:
            st.metric("Total", len(st.session_state.history) + len(st.session_state.chat_messages))
        
        st.divider()
        
        if st.session_state.history:
            for i, record in enumerate(reversed(st.session_state.history)):
                with st.expander(f"{record['artwork']} - {record['time'].strftime('%Y-%m-%d %H:%M')}"):
                    st.markdown(f"<p style='color: #2C3E50;'><strong>Period:</strong> {record['period']}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color: #2C3E50;'><strong>Damage:</strong> {record['damage'][:100]}...</p>", unsafe_allow_html=True)
                    if st.button("Delete", key=f"del_{i}"):
                        st.session_state.history.pop(-(i+1))
                        st.rerun()
        else:
            st.info("No saved records yet")
    
    # SETTINGS
    elif menu == "⚙️ Settings":
        st.markdown("<h1 style='color: #4A5D3F;'>Settings</h1>", unsafe_allow_html=True)
        
        with st.form("settings_form"):
            name = st.text_input("Name", st.session_state.user['name'], key="settings_name")
            age = st.number_input("Age", 1, 120, st.session_state.user['age'], key="settings_age")
            experience = st.selectbox("Experience", ["beginner", "intermediate", "advanced"], 
                                     index=["beginner", "intermediate", "advanced"].index(st.session_state.user['experience']), key="settings_exp")
            creativity = st.slider("Creativity", 1, 10, st.session_state.user['creativity'], key="settings_creativity")
            length = st.slider("Output Length", 1, 10, st.session_state.user['length'], key="settings_length")
            tone = st.selectbox("Tone", ["academic", "simplified"],
                               index=["academic", "simplified"].index(st.session_state.user['tone']), key="settings_tone")
            
            if st.form_submit_button("Save Settings", use_container_width=True):
                st.session_state.user.update({
                    'name': name, 'age': age, 'experience': experience,
                    'creativity': creativity, 'length': length, 'tone': tone
                })
                st.success("Settings saved!")
    
    # ETHICS
    elif menu == "⚖️ Ethics":
        st.markdown("<h1 style='color: #4A5D3F;'>Ethics & About</h1>", unsafe_allow_html=True)
        
        with st.expander("📚 Educational Purpose", expanded=True):
            st.markdown("<p style='color: #2C3E50;'>This is an educational tool for museums, students, and researchers. NOT for direct physical restoration.</p>", unsafe_allow_html=True)
        
        with st.expander("⚠️ AI Limitations"):
            st.markdown("<p style='color: #2C3E50;'>AI cannot assess actual materials, perform scientific analysis, or replace trained conservators.</p>", unsafe_allow_html=True)
        
        with st.expander("🌍 Cultural Respect"):
            st.markdown("<p style='color: #2C3E50;'>We respect cultural contexts and encourage community consultation.</p>", unsafe_allow_html=True)
        
        with st.expander("🤖 Responsible AI"):
            st.markdown("<p style='color: #2C3E50;'>AI assists but humans make final decisions. Always consult professional conservators.</p>", unsafe_allow_html=True)