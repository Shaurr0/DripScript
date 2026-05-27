from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

# Load model
processor = BlipProcessor.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)

model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)

# Load image
image = Image.open("shirt.jpg").convert("RGB")

# Process image
inputs = processor(images=image, return_tensors="pt")

# Generate caption
out = model.generate(**inputs)

caption = processor.decode(out[0], skip_special_tokens=True)

print("\nDetected Description:")
print(caption)