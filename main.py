from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import re

app = FastAPI()

# Allow all origins (for your frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostRequest(BaseModel):
    topic: str
    platform: str
    tone: str
    include_image: bool = True

@app.post("/generate")
async def generate_post(request: PostRequest):
    """Generate social media post"""
    
    # Simple caption templates
    captions = {
        "professional": f"🚀 Master {request.topic} with these proven strategies!\n\n#{request.topic.replace(' ', '')} #Business #Growth",
        "casual": f"Hey friends! 🌟 Check out this {request.topic} tip!\n\n#{request.topic.replace(' ', '')} #Tips #Daily",
        "funny": f"Me trying {request.topic}: 🤡\n\n#{request.topic.replace(' ', '')} #Funny #Relatable",
        "inspirational": f"✨ Your {request.topic} journey starts today!\n\n#{request.topic.replace(' ', '')} #Motivation #Success"
    }
    
    caption = captions.get(request.tone, captions["professional"])
    hashtags = " ".join(re.findall(r'#\w+', caption))
    
    # Generate image URL
    image_url = None
    if request.include_image:
        prompt = f"{request.topic} social media post {request.tone}"
        sizes = {"instagram": "1080x1080", "linkedin": "1200x627", "twitter": "1200x675", "facebook": "1200x630"}
        size = sizes.get(request.platform, "1024x1024")
        image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width={size.split('x')[0]}&height={size.split('x')[1]}"
    
    return {
        "success": True,
        "caption": caption,
        "hashtags": hashtags,
        "image_url": image_url,
        "platform": request.platform,
        "topic": request.topic,
        "tone": request.tone
    }

@app.get("/")
async def root():
    return {"status": "Social Media AI Manager is running!", "version": "1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
