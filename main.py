from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from transformers import pipeline
import requests
import uuid
import os
from PIL import Image, ImageDraw, ImageFont
import io

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load AI model for text
model_name = "meta-llama/Llama-3.2-3B-Instruct"
text_generator = pipeline(
    "text-generation",
    model=model_name,
    device_map="auto"
)

class PostRequest(BaseModel):
    topic: str
    platform: str
    tone: str
    include_image: bool = True

# ============================================
# GENERATE TEXT (Caption + Hashtags)
# ============================================

def generate_caption(topic: str, platform: str, tone: str) -> dict:
    """Generate social media caption"""
    
    platform_style = {
        "instagram": "Use emojis, short lines, engaging question, 10-20 hashtags",
        "linkedin": "Professional, value-driven, industry insight, 3-5 hashtags",
        "twitter": "Concise, under 280 chars, witty, 1-3 hashtags",
        "facebook": "Conversational, community-focused, 3-5 hashtags"
    }
    
    prompt = f"""Create a {platform} post about {topic} with {tone} tone.

Style: {platform_style.get(platform, 'Engaging')}

Return format:
CAPTION: [main post text]
HASHTAGS: [comma separated]"""

    response = text_generator(
        f"<|system|>You are a social media expert\n<|user|>{prompt}\n<|assistant|>",
        max_new_tokens=300,
        temperature=0.8
    )
    
    output = response[0]['generated_text']
    
    caption = ""
    hashtags = ""
    
    for line in output.split('\n'):
        if 'CAPTION:' in line:
            caption = line.replace('CAPTION:', '').strip()
        elif 'HASHTAGS:' in line:
            hashtags = line.replace('HASHTAGS:', '').strip()
    
    return {
        "caption": caption if caption else f"Check out these amazing {topic} tips! 🚀",
        "hashtags": hashtags if hashtags else f"#{topic.replace(' ', '')} #socialmedia #viral"
    }

# ============================================
# GENERATE IMAGE (Free using Pollinations.ai)
# ============================================

def generate_image(prompt: str, platform: str) -> str:
    """Generate image using free API"""
    
    # Platform-specific sizes
    sizes = {
        "instagram": "1080x1080",
        "linkedin": "1200x627",
        "twitter": "1200x675",
        "facebook": "1200x630"
    }
    
    size = sizes.get(platform, "1024x1024")
    width, height = map(int, size.split('x'))
    
    # Enhance prompt for better images
    image_prompt = f"{prompt}, social media post, vibrant, professional, clean design"
    
    # Free image generation API (Pollinations.ai)
    image_url = f"https://pollinations.ai/p/{image_prompt.replace(' ', '%20')}?width={width}&height={height}"
    
    return image_url

# ============================================
# ADD TEXT TO IMAGE (Optional)
# ============================================

def add_text_to_image(image_url: str, caption: str) -> str:
    """Add caption text to image"""
    try:
        # Download image
        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content))
        
        # Add text overlay
        draw = ImageDraw.Draw(img)
        
        # Simple text overlay (you can customize)
        draw.rectangle([(0, img.height-100), (img.width, img.height)], fill=(0,0,0,128))
        
        return image_url  # Return original URL if text overlay fails
    except:
        return image_url

# ============================================
# MAIN API ENDPOINT
# ============================================

@app.post("/generate")
async def generate_post(request: PostRequest):
    """Generate complete social media post with text + image"""
    
    # Generate text
    text = generate_caption(request.topic, request.platform, request.tone)
    
    # Prepare response
    response = {
        "success": True,
        "platform": request.platform,
        "topic": request.topic,
        "tone": request.tone,
        "caption": text["caption"],
        "hashtags": text["hashtags"],
        "image_url": None
    }
    
    # Generate image if requested
    if request.include_image:
        image_prompt = f"{request.topic} social media post {request.tone} style"
        response["image_url"] = generate_image(image_prompt, request.platform)
    
    return response

@app.post("/generate-batch")
async def generate_batch(request: PostRequest):
    """Generate multiple posts at once"""
    posts = []
    topics = [request.topic, f"{request.topic} tips", f"{request.topic} inspiration"]
    
    for topic in topics[:3]:  # Max 3 posts
        post = await generate_post(PostRequest(
            topic=topic,
            platform=request.platform,
            tone=request.tone,
            include_image=request.include_image
        ))
        posts.append(post)
    
    return {"success": True, "posts": posts}

@app.get("/")
async def root():
    return {"message": "Social Media AI Manager with Images", "status": "online"}

# Run: uvicorn main:app --reload
