import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="TavernBoost", page_icon="🍻", layout="centered")

# Tried in order. If Google retires one, the next is used automatically.
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]

PLATFORM_SPECS = {
    "Facebook / Instagram": "{n} caption variations (max 90 words each), emojis in moderation, a clear call to action.",
    "WhatsApp Status": "{n} WhatsApp Status lines, each under 150 characters, punchy and easy to screenshot.",
    "TikTok / Reels": "{n} video ideas. For each: a first-3-seconds hook, a 15-second shot list, and on-screen text.",
    "X (Twitter)": "{n} tweets, each under 270 characters, with at most 2 hashtags.",
}

SYSTEM_PROMPT = """You are a South African social media marketer who specialises in taverns, shisanyamas and local pubs.
You write ready-to-post content that sounds like real Mzansi people, not a corporate brochure.

Rules:
- Use light local flavour (township slang, Friday vibes, month-end/payday energy) but keep it clear and readable.
- Never target or appeal to minors. Never encourage excessive drinking or drunk driving.
- Every Facebook/Instagram post and every Status must end with: "Drink responsibly. 18+"
- Never invent prices, dates or phone numbers. Use only the details provided.
- Use plain text with simple headings. No markdown tables.
"""


def get_api_key() -> str:
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""
    if not key:
        key = st.sidebar.text_input("Gemini API key", type="password")
    return key


def language_rule(choice: str) -> str:
    if choice == "English":
        return "Write in English with light South African flavour."
    if choice == "Setswana":
        return "Write in Setswana (natural, conversational, not textbook). Keep brand names in English."
    return "Write each item twice: first in English, then in Setswana (natural, conversational)."


def build_post_prompt(d: dict) -> str:
    specs = "\n".join(
        f"- {p}: " + PLATFORM_SPECS[p].format(n=d["variations"]) for p in d["platforms"]
    )
    contact = d["contact"] or "no contact number given (do not invent one)"
    return f"""Create social media content for this tavern.

Tavern: {d['name']}
Location: {d['location']}
Special / event: {d['special']}
Tone: {d['tone']}
Contact / booking: {contact}
Language: {language_rule(d['language'])}

Produce, for each selected platform:
{specs}

Then add:
HASHTAGS: 12 hashtags mixing local (town/area), tavern-life and event tags.
TRACKING CTAs: 3 calls to action that let the owner measure results, for example
"Show this post at the bar for a free shot", "WhatsApp us the word BOOST to reserve a table",
"Tell the bartender you saw us on Facebook". Make them specific to the special above.
BEST TIMES TO POST: one line per platform.
"""


def build_calendar_prompt(d: dict) -> str:
    contact = d["contact"] or "no contact number given (do not invent one)"
    return f"""Create a 7-day content calendar for this tavern, one post idea per day.

Tavern: {d['name']}
Location: {d['location']}
Main special / event this week: {d['special']}
Tone: {d['tone']}
Contact / booking: {contact}
Language: {language_rule(d['language'])}
Platforms to use: {', '.join(d['platforms'])}

For each day (Monday to Sunday) give:
- Theme (e.g. Monday teaser, Wednesday throwback, Friday main event, month-end payday push)
- Platform
- Ready-to-post caption
- A simple visual idea the owner can shoot on a phone
- A tracking CTA

Finish with 12 hashtags. Every caption ends with: "Drink responsibly. 18+"
"""


def generate(api_key: str, prompt: str, temperature: float) -> str:
    client = genai.Client(api_key=api_key)
    last_error = None
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=temperature,
                ),
            )
            if response.text:
                return response.text
        except Exception as e:  # try the next model
            last_error = e
    raise last_error or RuntimeError("No response from model.")


# ---------- UI ----------
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; max-width: 700px;}
    .stButton>button {width: 100%; font-weight: 600; padding: 0.7rem 0;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🍻 TavernBoost")
st.caption("Ready-to-post content for South African taverns")

api_key = get_api_key()

mode = st.radio("What do you need?", ["Post pack", "7-day calendar"], horizontal=True)

with st.form("inputs"):
    name = st.text_input("Tavern name", placeholder="e.g. Mama T's Place")
    location = st.text_input("Location", placeholder="e.g. Zeerust, North West")
    special = st.text_area(
        "Special / event", placeholder="e.g. Friday DJ night, R20 beers till 9pm", height=90
    )
    contact = st.text_input("WhatsApp / contact number (optional)", placeholder="e.g. 082 123 4567")

    col1, col2 = st.columns(2)
    tone = col1.selectbox("Tone", ["Hype", "Chilled", "Classy", "Funny", "Family-friendly daytime"])
    language = col2.selectbox("Language", ["English", "Setswana", "Both"])

    platforms = st.multiselect(
        "Platforms",
        list(PLATFORM_SPECS.keys()),
        default=["Facebook / Instagram", "WhatsApp Status"],
    )
    variations = st.slider("Variations per platform", 1, 5, 3) if mode == "Post pack" else 3
    submitted = st.form_submit_button("🚀 Generate")

if submitted:
    if not api_key:
        st.warning("Add your Gemini API key in the sidebar (or Streamlit secrets) to continue.")
    elif not (name and location and special and platforms):
        st.warning("Please fill in the tavern name, location, special and at least one platform.")
    else:
        data = dict(
            name=name, location=location, special=special, contact=contact,
            tone=tone, language=language, platforms=platforms, variations=variations,
        )
        prompt = build_post_prompt(data) if mode == "Post pack" else build_calendar_prompt(data)
        with st.spinner("Cooking up your content..."):
            try:
                st.session_state["result"] = generate(api_key, prompt, 0.9)
                st.session_state["fname"] = f"{name.strip().replace(' ', '_')}_content.txt"
            except Exception as e:
                msg = str(e)
                if "429" in msg or "quota" in msg.lower():
                    st.error("Too many requests right now. Please try again in a minute.")
                elif "API key" in msg or "403" in msg or "401" in msg:
                    st.error("Your API key was rejected. Check it and try again.")
                else:
                    st.error("Something went wrong. Please try again.")
                    with st.expander("Technical details"):
                        st.code(msg)

if "result" in st.session_state:
    st.divider()
    st.subheader("Your content")
    st.markdown(st.session_state["result"])
    with st.expander("Copy as plain text"):
        st.code(st.session_state["result"], language=None)
    st.download_button(
        "⬇️ Download as .txt",
        st.session_state["result"],
        file_name=st.session_state.get("fname", "tavernboost.txt"),
    )

st.divider()
st.caption("TavernBoost • Built by Techmo Innovations")
