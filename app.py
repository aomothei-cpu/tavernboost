import streamlit as st
from google import genai
from google.genai import types
from datetime import datetime

# Page config
st.set_page_config(
    page_title="TavernBoost – Content Generator",
    page_icon="🍻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling, colors, and branded platform tags
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.15rem;
    }
    .sub-header {
        color: #666;
        font-size: 1.05rem;
        margin-bottom: 1.8rem;
    }
    
    /* Professional Light/Royal Blue Button */
    .stButton>button {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 0.65rem 1.3rem !important;
        border: none !important;
        box-shadow: 0 2px 5px rgba(2, 132, 199, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover, .stButton>button:focus {
        background-color: #0369a1 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 8px rgba(3, 105, 161, 0.4) !important;
    }

    /* Wipe out default Streamlit red tag backgrounds */
    .stMultiSelect [data-baseweb="tag"],
    div[data-baseweb="tag"], 
    span[data-baseweb="tag"] {
        background-color: #0284c7 !important;
        border-radius: 6px !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] *,
    div[data-baseweb="tag"] *, 
    span[data-baseweb="tag"] * {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    div[data-testid="stMarkdownContainer"] h3 {
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🍻 TavernBoost")
    st.caption("Specialised content generator for taverns")
    
    st.markdown("---")
    api_key_input = st.text_input(
        "Gemini API Key",
        type="password",
        help="Get a free key at https://aistudio.google.com/apikey"
    )
    
    # Fallback to secrets if sidebar is empty
    api_key = api_key_input.strip() or st.secrets.get("GEMINI_API_KEY", "")
    
    if api_key:
        st.success("API key loaded", icon="✅")
    else:
        st.info("Enter your free Gemini API key to generate content")
    
    st.markdown("---")
    st.markdown("**Platforms covered**")
    st.markdown("- Facebook\n- Instagram\n- WhatsApp Status\n- TikTok / Reels\n- X (Twitter)")
    
    st.markdown("---")
    st.markdown("**Default language:** English")
    st.caption("Setswana option available below")

# System prompt specialised for taverns + all platforms
SYSTEM_PROMPT = """You are an expert local marketing copywriter specialising in South African taverns, shebeens and pubs.
You write short, energetic, authentic social media content that feels local and natural.

Rules:
- Default language is English. Only use Setswana when the user specifically requests it.
- When Setswana is requested, write natural everyday Setswana (or a natural mix of Setswana + English as people actually speak in South Africa).
- Keep every piece of content short and punchy – perfect for social media.
- Always include a clear call-to-action (visit, WhatsApp us, bring your crew, mention the promo, etc.).
- Use relevant emojis sparingly but effectively (🍻 🍗 🎵 🔥 📍 👀 🍻).
- Sound like a real local person talking, not a corporate agency or AI.
- Never invent prices, times or details the user did not provide.
- Offer multiple strong variations.
- Always include a tracking-friendly CTA idea when useful (e.g. “Mention WhatsApp”, “Show this Status”, “Comment FACEBOOK”).

Platform-specific guidance:
- Facebook / Instagram: Good captions, can be a bit longer, use line breaks, strong first line.
- WhatsApp Status: Extremely short (1–2 lines max), very punchy.
- TikTok / Reels: Short hook + caption + suggested on-screen text / first 3 seconds idea.
- X (Twitter): Keep under 280 characters, sharp and shareable.
"""

def generate_content(tavern_name, location, special, platforms, tone, language, extra_notes, api_key):
    client = genai.Client(api_key=api_key.strip())
    
    platforms_text = ", ".join(platforms) if platforms else "All platforms"
    
    user_prompt = f"""
Create ready-to-post content for this tavern:

Tavern name: {tavern_name}
Location: {location or "not specified"}
Today’s special / event / offer: {special}
Platforms needed: {platforms_text}
Desired tone: {tone}
Language: {language}
Extra notes: {extra_notes or "none"}

Please generate the following, clearly separated with headings:

### Facebook / Instagram Posts
Give 3 strong caption options (ready to copy-paste). Use line breaks for readability.

### WhatsApp Status
Give 2–3 very short Status options (1–2 lines maximum each).

### TikTok / Reels
Give:
- 2 short video hooks (what to say or show in the first 3 seconds)
- Matching caption for each
- Suggested on-screen text

### X (Twitter)
Give 2 short posts (under 280 characters each).

### Hashtags
Suggest 6–8 relevant hashtags.

### Tracking CTA ideas
Give 2 simple tracking phrases the tavern can use (e.g. “Mention WhatsApp for R10 off”, “Show this Status”, “Comment FACEBOOK”).

Make everything feel local, energetic and ready to post immediately.
"""
    
    # Try current active models to prevent 404 NOT_FOUND error
    candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-002", "gemini-1.5-flash"]
    
    last_exception = None
    for model_id in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.85,
                )
            )
            return response.text
        except Exception as e:
            last_exception = e
            continue
            
    if last_exception:
        raise last_exception


# ====================== MAIN INTERFACE ======================
st.markdown('<p class="main-header">Tavern Content Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Create ready-to-post content for Facebook, Instagram, WhatsApp, TikTok & X</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    tavern_name = st.text_input("Tavern Name *", placeholder="e.g. Golden Barrel Tavern")
    location = st.text_input("Location / Area", placeholder="e.g. Dinokana, Zeerust")
    special = st.text_area(
        "Special / Event / Offer *",
        placeholder="e.g. Friday Special: Castle Lite R25 + DJ from 8pm\nor Big screen soccer this Saturday + wings special",
        height=110
    )

with col2:
    platforms = st.multiselect(
        "Platforms to generate for *",
        options=["Facebook / Instagram", "WhatsApp Status", "TikTok / Reels", "X (Twitter)"],
        default=["Facebook / Instagram", "WhatsApp Status", "TikTok / Reels", "X (Twitter)"]
    )
    tone = st.selectbox(
        "Tone",
        ["Hype / Party", "Chill / Relaxed", "Food-focused", "Sports / Game day", "Event / DJ night"]
    )
    language = st.selectbox(
        "Language",
        ["English (default)", "Setswana", "Both (English + Setswana versions)"]
    )
    extra_notes = st.text_input(
        "Extra notes (optional)",
        placeholder="e.g. Mention pool tables, target weekend crowd, no alcohol discount"
    )

st.markdown("")
generate_btn = st.button("Generate Content ✨", use_container_width=True, type="primary")

if generate_btn:
    if not api_key:
        st.error("Please enter your Gemini API key in the sidebar first.")
    elif not tavern_name or not special:
        st.warning("Please fill in at least the Tavern Name and the Special/Event.")
    elif not platforms:
        st.warning("Please select at least one platform.")
    else:
        with st.spinner("Creating your content..."):
            try:
                result = generate_content(
                    tavern_name=tavern_name,
                    location=location,
                    special=special,
                    platforms=platforms,
                    tone=tone,
                    language=language,
                    extra_notes=extra_notes,
                    api_key=api_key
                )
                
                st.markdown("---")
                st.markdown("### Your Content")
                st.markdown(result)
                
                # Download
                filename = f"{tavern_name.replace(' ', '_')}_content_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                st.download_button(
                    label="Download as text file",
                    data=result,
                    file_name=filename,
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Error generating content: {str(e)}")
                st.info("Check that your API key is valid and you still have free quota.")

st.markdown("---")
st.caption("TavernBoost • Built by Techmo Innovations")
