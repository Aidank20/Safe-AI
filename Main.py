from io import BytesIO
import random
from urllib.parse import quote
from PIL import Image
import requests
import streamlit as st
FILTER_API_URL = "https://filters-zeta.vercel.app/api/filter"
POLLINATIONS_TEXT_URL = "https://text.pollinations.ai/"
POLLINATIONS_IMAGE_BASE = "https://image.pollinations.ai/prompt/"
ENHANCE_SYS = ( "Improve prompts for text-to-image generation. Return ONLY the enhanced prompt ""with no intro, quotes, or explanation. Add clear details for subject, artistic style, ""lighting, camera angle, background, and color palette. Keep the content completely safe." )
def check_prompt_with_filter_api(prompt:str)->dict:
    try:
        response = requests.post(FILTER_API_URL, json={"prompt": prompt},timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return {"ok": False, "error": "Invalid safety filter API response format."}
        return data
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Safety filter API request timed out. Please try again later."}
    except Exception as e:
        return {"ok": False, "error": f"Safety filter API error: {str(e)}"}
def enhance_prompt(raw_prompt: str)->str:
    headers = {"Content-Type": "application/json"}
    payload = {
        "messages":[
            {"role": "system", "content": ENHANCE_SYS},
            {"role": "user", "content":f"Raw_prompt: {raw_prompt}"},
        ],
        "model": "openai",
        "seed": random.randint(1, 99999),
        "private": True,
    }
    try:
        response = requests.post(
            POLLINATIONS_TEXT_URL,
            json=payload, 
            headers=headers, 
            timeout=20
        )
        response.raise_for_status()
        enhanced = response.text.strip()
        return enhanced if enhanced else raw_prompt
    except Exception:
        return raw_prompt
def gen_image(prompt: str, model:str = "flux", width:int = 512, height:int = 512,):
    filter_result = check_prompt_with_filter_api(prompt)
    if not filter_result.get("ok"):
        return None, f"Prompt bolcked by safety filter: {filter_result.get('reason', 'Unsafe prompt')}"
    header={}
    encoded_prompt = quote(prompt)
    seed = random.randint(1, 99999)
    url = (f"{POLLINATIONS_IMAGE_BASE}{encoded_prompt}"f"?model={model}&width={width}&height={height}&seed={seed}&nologo=true&safe=true")
    try:
        response = requests.get(url, headers=header, timeout=60)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return img, None
    except requests.exceptions.Timeout:
        return None, "Image generation request timed out. Please try again later."
    except Exception as e:
        return None, f"Image generation error: {str(e)}"
def main():
    st.set_page_config(page_title="AI Image Generator", page_icon=":art:", layout="wide")
    st.title("AI Image Generator")
    st.write("Describe the image you want to create")
    prompt = st.text_area("Image Prompt", height=140,placeholder="A peaceful mountain lake at sunrise,painted in a watercolor style...")
    enhance = st.checkbox("Enhance Prompt", value=True, help="use AI to add visual details before genrating your image")
    left, center, right = st.columns(3)
    with left:
        model = st.selectbox("Model",["flux", "turbo", "gptimage"])
    with center:
        width = st.number_input("Width",min_value=256, max_value=2048, value=1024, step=256)
    with right:
        height = st.number_input("Height",min_value=256, max_value=2048, value=1024, step=256)
    if st.button("Generate image", type="primary", use_container_width=True):
        raw_prompt = prompt.strip()
        if not raw_prompt:
            st.warning("Please enter a prompt to generate an image.")
            return  
        final_prompt = enhance_prompt(raw_prompt) if enhance else raw_prompt
        if enhance and final_prompt != raw_prompt:
            with st.expander("Enhanced Prompt"):
                st.write(final_prompt)
        with st.spinner("Generating image..."):
            image, error = gen_image(final_prompt, model=model, width=int(width), height=int(height))
        if error:
            st.error(error)
        else:
            st.image(image, caption=final_prompt, use_container_width=True)
if __name__ == "__main__":
    main()                                        