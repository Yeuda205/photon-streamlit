import streamlit as st
import time
import requests
from lumaai import LumaAI
from PIL import Image
from io import BytesIO
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Must be the first Streamlit command
st.set_page_config(
    page_title="מכונת החלומות של פוטון",
    page_icon="✨",
    layout="wide"
)

# Initialize Luma client
try:
    client = LumaAI(auth_token=st.secrets["LUMA_API_KEY"])
    logger.info("Successfully initialized Luma AI client")
except Exception as e:
    logger.error(f"Failed to initialize Luma AI client: {str(e)}")
    st.error("שגיאה באתחול המערכת. אנא נסה שוב מאוחר יותר.")

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
    
    /* File uploader - only keep LTR */
    .stUploadedFile {
        direction: ltr !important;
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
    try:
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        logger.error(f"Failed to convert image to data URL: {str(e)}")
        return None

def generate_image(prompt, aspect_ratio="16:9", model="photon-1", style_ref=None, character_ref=None, modify_image=None):
    """Generate image using Luma AI"""
    try:
        with st.spinner("🎨 יוצר את התמונה שלך... (זה יכול לקחת כמה שניות)"):
            logger.info(f"Starting image generation with prompt: {prompt[:50]}...")
            
            params = {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "model": model
            }
            
            if style_ref:
                params["style_ref"] = [{"url": style_ref, "weight": 0.8}]
                logger.info("Adding style reference to generation")
            if character_ref:
                params["character_ref"] = {"identity0": {"images": [character_ref]}}
                logger.info("Adding character reference to generation")
            if modify_image:
                params["modify_image_ref"] = {"url": modify_image, "weight": 1.0}
                logger.info("Adding image modification reference to generation")
            
            generation = client.generations.image.create(**params)
            logger.info(f"Generation started with ID: {generation.id}")
            
            while True:
                generation = client.generations.get(id=generation.id)
                if generation.state == "completed":
                    logger.info("Generation completed successfully")
                    break
                elif generation.state == "failed":
                    error_msg = generation.failure_reason
                    logger.error(f"Generation failed: {error_msg}")
                    
                    if "moderate" in error_msg.lower():
                        raise RuntimeError("""
                        התמונה לא עברה את בדיקת המודרציה. 
                        אנא וודאו שהתמונה עומדת בהנחיות הבאות:
                        - לא מכילה תוכן למבוגרים
                        - לא מכילה אלימות
                        - לא מכילה סמלים פוליטיים/דתיים שנויים במחלוקת
                        - לא מכילה טקסט או לוגואים מוגנים
                        """)
                    else:
                        raise RuntimeError(f"Generation failed: {error_msg}")
                time.sleep(2)
            
            return generation.assets.image
    except Exception as e:
        logger.error(f"Error during image generation: {str(e)}")
        st.error(f"אופס! משהו השתבש: {str(e)}")
        return None

def display_uploaded_image(uploaded_file, caption=""):
    """Display uploaded image with preview"""
    try:
        image = Image.open(uploaded_file)
        # Create a thumbnail for preview
        max_size = (300, 300)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        with st.container():
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                st.image(image, caption=caption, use_column_width=True)
        return image
    except Exception as e:
        logger.error(f"Error displaying uploaded image: {str(e)}")
        st.error("שגיאה בטעינת התמונה")
        return None

def display_upload_guidelines():
    """Display guidelines for image upload"""
    with st.expander("📋 הנחיות להעלאת תמונות"):
        st.markdown("""
        - התמונה צריכה להיות בפורמט PNG, JPG או JPEG
        - התמונה צריכה להיות נקייה מתוכן למבוגרים או אלימות
        - אין להעלות תמונות עם סמלים פוליטיים או דתיים שנויים במחלוקת
        - אין להעלות תמונות עם טקסט או לוגואים מוגנים בזכויות יוצרים
        - מומלץ להעלות תמונות באיכות טובה אך לא גדולות מדי
        """)

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
                    try:
                        response = requests.get(image_url)
                        img = Image.open(BytesIO(response.content))
                        st.image(img, caption="התמונה שנוצרה 🎨")
                        st.markdown(f"**הפרומפט ששימש ליצירה:**\n```{prompt}```")
                    except Exception as e:
                        logger.error(f"Error displaying generated image: {str(e)}")
                        st.error("שגיאה בטעינת התמונה שנוצרה")
            else:
                st.warning("אנא הכנס פרומפט לפני היצירה!")
        st.markdown('</div>', unsafe_allow_html=True)

    # Style Transfer Tab
    with tabs[1]:
        st.markdown('<div class="rtl">', unsafe_allow_html=True)
        st.markdown("### העברת סגנון")
        display_upload_guidelines()
        uploaded_style = st.file_uploader("העלה תמונת סגנון", type=["png", "jpg", "jpeg"], key="style")
        
        if uploaded_style:
            st.markdown("##### תצוגה מקדימה של תמונת הסגנון:")
            style_image = display_uploaded_image(uploaded_style)
            
        prompt = st.text_area("תאר את התמונה באנגלית:", 
                            placeholder="Example: A vibrant cityscape of Tel Aviv in the style of the reference image, detailed architecture, 8k quality", 
                            key="style_prompt")
        
        if uploaded_style and prompt and st.button("✨ צור בסגנון"):
            if style_image:
                style_url = image_to_data_url(style_image)
                image_url = generate_image(prompt, style_ref=style_url)
                if image_url:
                    try:
                        response = requests.get(image_url)
                        img = Image.open(BytesIO(response.content))
                        st.image(img, caption="התמונה החדשה בסגנון שבחרת")
                    except Exception as e:
                        logger.error(f"Error displaying style transfer result: {str(e)}")
                        st.error("שגיאה בטעינת התמונה שנוצרה")
        st.markdown('</div>', unsafe_allow_html=True)

    # Character Creation Tab
    with tabs[2]:
        st.markdown('<div class="rtl">', unsafe_allow_html=True)
        st.markdown("### יצירת דמויות")
        display_upload_guidelines()
        uploaded_char = st.file_uploader("העלה תמונת דמות", type=["png", "jpg", "jpeg"], key="char")
        
        if uploaded_char:
            st.markdown("##### תצוגה מקדימה של תמונת הדמות:")
            char_image = display_uploaded_image(uploaded_char)
            
        prompt = st.text_area("תאר את הסיטואציה החדשה באנגלית:", 
                            placeholder="Example: The character as a samurai warrior in a traditional Japanese garden, dramatic pose, detailed armor, 8k quality", 
                            key="char_prompt")
        
        if uploaded_char and prompt and st.button("✨ צור וריאציה"):
            if char_image:
                char_url = image_to_data_url(char_image)
                image_url = generate_image(prompt, character_ref=char_url)
                if image_url:
                    try:
                        response = requests.get(image_url)
                        img = Image.open(BytesIO(response.content))
                        st.image(img, caption="הדמות בסיטואציה החדשה")
                    except Exception as e:
                        logger.error(f"Error displaying character variation: {str(e)}")
                        st.error("שגיאה בטעינת התמונה שנוצרה")
        st.markdown('</div>', unsafe_allow_html=True)

    # Image Editing Tab
    with tabs[3]:
        st.markdown('<div class="rtl">', unsafe_allow_html=True)
        st.markdown("### עריכת תמונה קיימת")
        display_upload_guidelines()
        uploaded_edit = st.file_uploader("העלה תמונה לעריכה", type=["png", "jpg", "jpeg"], key="edit")
        
        if uploaded_edit:
            st.markdown("##### תצוגה מקדימה של התמונה לעריכה:")
            edit_image = display_uploaded_image(uploaded_edit)
            
        prompt = st.text_area("תאר את השינויים הרצויים באנגלית:", 
                            placeholder="Example: Change all flowers to pink and add magical sparkles around them, maintain original composition, 8k quality", 
                            key="edit_prompt")
        
        if uploaded_edit and prompt and st.button("✨ ערוך תמונה"):
            if edit_image:
                edit_url = image_to_data_url(edit_image)
                image_url = generate_image(prompt, modify_image=edit_url)
                if image_url:
                    try:
                        response = requests.get(image_url)
                        img = Image.open(BytesIO(response.content))
                        st.image(img, caption="התמונה לאחר העריכה")
                    except Exception as e:
                        logger.error(f"Error displaying edited image: {str(e)}")
                        st.error("שגיאה בטעינת התמונה שנוצרה")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 