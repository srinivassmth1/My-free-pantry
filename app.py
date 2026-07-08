import streamlit as st
import json
import httpx
import base64

# 1. Setup Page Layout
st.set_page_config(page_title="Free Smart Pantry", page_icon="🥦", layout="centered")
st.title("🥦 Free Smart Pantry & Inventory Agent (OpenRouter)")

# 2. Key Validation Matrix
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "inventory" not in st.session_state:
    st.session_state.inventory = ["Paneer", "Tomatoes", "Cilantro", "Butter"]

api_key = st.text_input("Enter your free OpenRouter API Key (starts with sk-or-):", value=st.session_state.api_key, type="password")
if api_key:
    st.session_state.api_key = api_key
else:
    st.warning("Please enter your OpenRouter API key to activate the app.")
    st.stop()

# 3. Media Upload Interface
st.subheader("📸 Scan Kitchen / Add Bill")
upload_method = st.radio("Choose upload method:", ["Take a Live Photo", "Upload Receipt / Image File"])

image_file = None
if upload_method == "Take a Live Photo":
    image_file = st.camera_input("Snap a photo of your fridge or shopping bill")
else:
    image_file = st.file_uploader("Upload an image asset...", type=["jpg", "jpeg", "png"])

# 4. Global Action Engine
if image_file is not None:
    if st.button("🤖 Process Photo & Sync Data"):
        with st.spinner("AI is scanning high-res image pixels via OpenRouter..."):
            img_bytes = image_file.getvalue()
            b64_img = base64.b64encode(img_bytes).decode("utf-8")
            data_url = f"data:image/jpeg;base64,{b64_img}"
            
            # Direct connection to OpenRouter's global API routing layer
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {st.session_state.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "google/gemini-2.5-flash",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this image. List all unique food items or grocery names clearly as a simple comma-separated list of items. Do not write text sentences or conversational descriptions."},
                            {"type": "image_url", "image_url": {"url": data_url}}
                        ]
                    }
                ]
            }
            
            try:
                res = httpx.post(url, headers=headers, json=payload, timeout=45.0)
                if res.status_code == 200:
                    scanned_text = res.json()["choices"][0]["message"]["content"].strip()
                    new_items = [item.strip().capitalize() for item in scanned_text.split(",") if item.strip()]
                    st.session_state.inventory = list(set(st.session_state.inventory + new_items))
                    st.success("Data synchronization complete! Inventory updated.")
                else:
                    st.error(f"Server Error: Status Code {res.status_code}. Verify your sk-or- key structure.")
            except Exception as e:
                st.error("Network timeout processing large data asset. Try again.")

# 5. Core Live Dashboard
st.subheader("📋 Current Kitchen Inventory")
st.write("Uncheck items you have fully consumed or are running low on:")

available_items = []
empty_items = []

for item in list(st.session_state.inventory):
    if st.checkbox(f"🍏 {item}", value=True, key=f"inv_{item}"):
        available_items.append(item)
    else:
        empty_items.append(item)

# 6. Automatic Purchase Engine
st.subheader("🛒 Out of Stock / Pending Purchase List")
if len(empty_items) > 0:
    st.error("The following items are getting empty in your fridge:")
    for empty_item in empty_items:
        st.write(f"❌ **{empty_item}** needs to be bought!")
        
    if st.button("💡 Suggest Recipes based only on remaining Stock"):
        with st.spinner("Calculating custom recipes..."):
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {st.session_state.api_key}",
                "Content-Type": "application/json"
            }
            p_text = f"Suggest 2 quick meals using only: {', '.join(available_items)}. Keep it brief."
            t_payload = {
                "model": "google/gemini-2.5-flash",
                "messages": [{"role": "user", "content": p_text}]
            }
            try:
                t_res = httpx.post(url, headers=headers, json=t_payload, timeout=20.0)
                st.info(t_res.json()["choices"][0]["message"]["content"])
            except Exception:
                st.warning("Could not reach recipe engine. Try again.")
else:
    st.success("Your fridge is completely full! Nothing is pending purchase.")
