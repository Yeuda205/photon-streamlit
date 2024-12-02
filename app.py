import streamlit as st
import time
import requests
from lumaai import LumaAI
from PIL import Image
from io import BytesIO
import base64

# Must be the first Streamlit command
st.set_page_config(
    page_title="מכונת החלומות של פוטון",
    page_icon="✨",
    layout="wide"
)

# Initialize Luma client
client = LumaAI(auth_token=st.secrets["LUMA_API_KEY"])

# CSS for RTL support
st.markdown("""
<style>
    /* Global RTL settings */
    .main > div {
        direction: rtl !important;
    }
    
    .stMarkdown, .stText, div:not(.stSlider) > label {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Headers and text alignment */
    h1, h2, h3, p {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Radio buttons and checkboxes */
    .stRadio > div {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Selectbox */
    .stSelectbox > div {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Text inputs and text areas */
    .stTextInput > div, .stTextArea > div {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Buttons */
    .stButton > button {
        float: right !important;
    }
    
    /* Keep sliders LTR */
    .stSlider > div {
        direction: ltr !important;
    }
    
    /* File uploader */
    .stUploadButton > div {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Tabs */
    .stTabs > div > div:first-child {
        direction: rtl !important;
    }
    
    /* Images and captions */
    .stImage {
        text-align: right !important;
    }
    
    /* Error and warning messages */
    .stAlert > div {
        direction: rtl !important;
        text-align: right !important;
    }
</style>
""", unsafe_allow_html=True)

# Prompt templates with Hebrew descriptions and English prompts
PROMPT_TEMPLATES = {
    "🎸 רוק סטאר": {
        "desc": "דובי רוק-סטאר על במה",
        "prompt": "A cool teddy bear rock star playing electric guitar on a neon-lit stage, epic lighting, dynamic pose, detailed fur texture, 8k quality"
    },
    "🧙‍♂️ קוסם": {
        "desc": "קוסם בספרייה עתיקה",
        "prompt": "A wise wizard casting magical spells in an ancient mystical library, floating ancient books, magical sparkles, detailed robe textures, ethereal lighting, 8k quality"
    },
    "🚀 חלל": {
        "desc": "חתול אסטרונאוט בחלל",
        "prompt": "An astronaut cat floating in deep space, Earth in background, detailed spacesuit, cosmic nebula colors, zero gravity effects, cinematic lighting, 8k quality"
    },
    "🎨 אמן": {
        "desc": "רובוט אמן בסטודיו",
        "prompt": "A creative robot artist creating a masterpiece in a modern art studio, paint splatters, dynamic brushstrokes, artistic lighting, detailed mechanical parts, 8k quality"
    },
    "🌺 טבע": {
        "desc": "גן פנטזיה קסום",
        "prompt": "A magical fantasy garden with bioluminescent flowers and ethereal butterflies at sunset, mystical fog, fairy lights, detailed flora, dreamy atmosphere, 8k quality"
    }
}

def image_to_data_url(image):
    """Convert PIL image to base64 data URL"""
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

def generate_image(prompt, aspect_ratio="16:9", model="photon-1", style_ref=None, character_ref=None, modify_image=None):
    """Generate image using Luma AI"""
    try:
        with st.spinner("🎨 יוצר את התמונה שלך... (זה יכול לקחת כמה שניות)"):
            params = {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "model": model
            }
            
            if style_ref:
                params["style_ref"] = [{"url": style_ref, "weight": 0.8}]
            if character_ref:
                params["character_ref"] = {"identity0": {"images": [character_ref]}}
            if modify_image:
                params["modify_image_ref"] = {"url": modify_image, "weight": 1.0}
            
            generation = client.generations.image.create(**params)
            
            while True:
                generation = client.generations.get(id=generation.id)
                if generation.state == "completed":
                    break
                elif generation.state == "failed":
                    raise RuntimeError(f"Generation failed: {generation.failure_reason}")
                time.sleep(2)
            
            return generation.assets.image
    except Exception as e:
        st.error(f"אופס! משהו השתבש: {str(e)}")
        return None

def main():
    st.markdown('<div class="rtl">', unsafe_allow_html=True)
    st.title("✨ מכונת החלומות של פוטון ✨")
    st.markdown("### בואו ניצור קסם עם AI! 🪄")
    
    tabs = st.tabs(["🎨 יצירה בסיסית", "🖼️ סגנון מותאם", "👤 דמויות", "✏️ עריכת תמונה"])
    
    # Basic Generation Tab
    with tabs[0]:
        st.markdown('<div class="rtl">', unsafe_allow_html=True)
        st.markdown("### יצירת תמונה חדשה")
        prompt_type = st.radio(
            "בחר סוג פרומפט:",
            ["✍️ כתיבה חופשית", "📝 השראה מהדוגמאות"]
        )
        
        if prompt_type == "📝 השראה מהדוגמאות":
            selected = st.selectbox("בחר פרומפט:", list(PROMPT_TEMPLATES.keys()))
            st.markdown(f"**תיאור:** {PROMPT_TEMPLATES[selected]['desc']}")
            prompt = PROMPT_TEMPLATES[selected]['prompt']
        else:
            prompt = st.text_area("תאר את התמונה באנגלית:", 
                                placeholder="Example: A magical sunset over Tel Aviv skyline with floating lanterns and modern architecture, cinematic lighting, 8k quality")
        
        col1, col2 = st.columns(2)
        with col1:
            aspect_ratio = st.select_slider(
                "יחס גובה-רוחב:",
                options=["1:1", "3:4", "4:3", "9:16", "16:9", "9:21", "21:9"],
                value="16:9"
            )
        with col2:
            model = st.radio("בחר מודל:", ["photon-1 (איכותי)", "photon-flash-1 (מהיר)"])
        
        if st.button("✨ צור תמונה"):
            if prompt:
                selected_model = model.split(" ")[0]
                image_url = generate_image(prompt, aspect_ratio, selected_model)
                if image_url:
                    response = requests.get(image_url)
                    img = Image.open(BytesIO(response.content))
                    st.image(img, caption="התמונה שנוצרה 🎨")
                    st.markdown(f"**הפרומפט ששימש ליצירה:**\n```{prompt}```")
            else:
                st.warning("אנא הכנס פרומפט לפני היצירה!")
        st.markdown('</div>', unsafe_allow_html=True)

    # Style Transfer Tab
    with tabs[1]:
        st.markdown('<div class="rtl">', unsafe_allow_html=True)
        st.markdown("### העברת סגנון")
        uploaded_style = st.file_uploader("העלה תמונת סגנון", type=["png", "jpg", "jpeg"], key="style")
        prompt = st.text_area("תאר את התמונה שאנגלית:", 
                            placeholder="Example: A vibrant cityscape of Tel Aviv in the style of the reference image, detailed architecture, 8k quality", 
                            key="style_prompt")
        
        if uploaded_style and prompt and st.button("✨ צור בסגנון"):
            style_image = Image.open(uploaded_style)
            style_url = image_to_data_url(style_image)
            
            image_url = generate_image(prompt, style_ref=style_url)
            if image_url:
                response = requests.get(image_url)
                img = Image.open(BytesIO(response.content))
                col1, col2 = st.columns(2)
                with col1:
                    st.image(style_image, caption="תמונת הסגנון המקורית")
                with col2:
                    st.image(img, caption="התמונה החדשה בסגנון שבחרת")
        st.markdown('</div>', unsafe_allow_html=True)

    # Character Creation Tab
    with tabs[2]:
        st.markdown('<div class="rtl">', unsafe_allow_html=True)
        st.markdown("### יצירת דמויות")
        uploaded_char = st.file_uploader("העלה תמונת דמות", type=["png", "jpg", "jpeg"], key="char")
        prompt = st.text_area("תאר את הסיטואציה החדשה באנגלית:", 
                            placeholder="Example: The character as a samurai warrior in a traditional Japanese garden, dramatic pose, detailed armor, 8k quality", 
                            key="char_prompt")
        
        if uploaded_char and prompt and st.button("✨ צור וריאציה"):
            char_image = Image.open(uploaded_char)
            char_url = image_to_data_url(char_image)
            
            image_url = generate_image(prompt, character_ref=char_url)
            if image_url:
                response = requests.get(image_url)
                img = Image.open(BytesIO(response.content))
                col1, col2 = st.columns(2)
                with col1:
                    st.image(char_image, caption="תמונת הדמות המקורית")
                with col2:
                    st.image(img, caption="הדמות בסיטואציה החדשה")
        st.markdown('</div>', unsafe_allow_html=True)

    # Image Editing Tab
    with tabs[3]:
        st.markdown('<div class="rtl">', unsafe_allow_html=True)
        st.markdown("### עריכת תמונה קיימת")
        uploaded_edit = st.file_uploader("העלה תמונה לעריכה", type=["png", "jpg", "jpeg"], key="edit")
        prompt = st.text_area("תאר את השינויים הרצויים באנגלית:", 
                            placeholder="Example: Change all flowers to pink and add magical sparkles around them, maintain original composition, 8k quality", 
                            key="edit_prompt")
        
        if uploaded_edit and prompt and st.button("✨ ערוך תמונה"):
            edit_image = Image.open(uploaded_edit)
            edit_url = image_to_data_url(edit_image)
            
            image_url = generate_image(prompt, modify_image=edit_url)
            if image_url:
                response = requests.get(image_url)
                img = Image.open(BytesIO(response.content))
                col1, col2 = st.columns(2)
                with col1:
                    st.image(edit_image, caption="התמונה המקורית")
                with col2:
                    st.image(img, caption="התמונה לאחר העריכה")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 