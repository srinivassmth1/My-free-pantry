import streamlit as st
import json
import httpx

# 1. Setup Page Configuration
st.set_page_config(page_title="Free Smart Pantry", page_icon="🥦", layout="centered")
st.title("🥦 Free Smart Pantry & Inventory Agent")

# 2. Free API Key Input
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key = st.text_input("Enter your free Gemini API Key:", value=st.session_state.api_key, type="password")
if api_key:
    st.session_state.api_key = api_key
else:
    st.warning("Please enter your Gemini API key to activate the app.")
    st.stop()

# Initialize global session variables to hold persistent inventory
if "inventory" not in st.session_state:
    st.session_state.inventory = ["Paneer", "Tomatoes", "Cilantro", "Butter"]

# 3. Photo & Bill Capture Interface
st.subheader("📸 Scan Kitchen / Add Bill")
upload_method = st.radio("Choose upload method:", ["Take a Live Photo", "Upload Receipt / Image File"])

image_file = None
if upload_method == "Take a Live Photo":
    image_file = st.camera_input("Snap a photo of your fridge or shopping bill")
else:
    image_file = st.file_uploader("Upload an image asset...", type=["jpg", "jpeg", "png"])

# Helper function to send images directly over a secure API call without local heavy packages
def call_gemini_vision(api_key, image_bytes, mime_type):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    import base64
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Analyze this image (refrigerator, pantry, or grocery bill receipt). List all unique food ingredient items clearly. Return only a simple comma-separated list of lowercase items (e.g., milk, eggs, chicken). Do not write any sentences, notes, or descriptions."},
                {
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": base64_image
                    }
                }
            ]
        }]
    }
    
    response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
    if response.status_code == 200:
        res_json = response.json()
        try:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return ""
    return ""

def call_gemini_text(api_key, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = httpx.post(url, headers=headers, json=payload, timeout=20.0)
    if response.status_code == 200:
        try:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "Could not generate recipe options."
    return "Connection error."

# 4. Trigger AI Scanning Agent
if image_file is not None:
    if st.button("🤖 Process Photo & Sync Data"):
        with st.spinner("AI is scanning image pixels directly..."):
            img_bytes = image_file.getvalue()
            m_type = image_file.type if image_file.type else "image/jpeg"
            
            scanned_text = call_gemini_vision(st.session_state.api_key, img_bytes, m_type)
            
            if scanned_text:
                new_items = [item.strip().capitalize() for item in scanned_text.split(",") if item.strip()]
                st.session_state.inventory = list(set(st.session_state.inventory + new_items))
                st.success("Data synchronization complete! Inventory updated.")
            else:
                st.error("Failed to parse the image. Verify your API key is correct.")

# 5. Core Inventory Dashboard
st.subheader("📋 Current Kitchen Inventory")
st.write("Uncheck items you have fully consumed or are running low on:")

current_items = list(st.session_state.inventory)
available_items = []
empty_items = []

for item in current_items:
    is_stocked = st.checkbox(f"🍏 {item}", value=True, key=f"inv_{item}")
    if is_stocked:
        available_items.append(item)
    else:
        empty_items.append(item)

# 6. Automate Your Missing / Pending Shopping List
st.subheader("🛒 Out of Stock / Pending Purchase List")
if len(empty_items) > 0:
    st.error("The following items are getting empty in your fridge:")
    for empty_item in empty_items:
        st.write(f"❌ **{empty_item}** needs to be bought!")
        
    if st.button("💡 Suggest Recipes based only on remaining Stock"):
        with st.spinner("Calculating custom recipes..."):
            recipe_prompt = f"Suggest 2 quick meals using only: {', '.join(available_items)}. Keep it brief."
            recipe_text = call_gemini_text(st.session_state.api_key, recipe_prompt)
            st.info(recipe_text)
else:
    st.success("Your fridge is completely full! Nothing is pending purchase.")
