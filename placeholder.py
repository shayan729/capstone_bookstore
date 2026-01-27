# create_placeholder.py
from PIL import Image, ImageDraw, ImageFont

# Create a 300x450 image (book cover aspect ratio)
img = Image.new('RGB', (300, 450), color='#E8E8E8')
draw = ImageDraw.Draw(img)

# Draw a book icon representation
draw.rectangle([50, 75, 250, 375], outline='#CCCCCC', width=3)
draw.line([150, 75, 150, 375], fill='#CCCCCC', width=2)

# Add text
try:
    # Try to use a nice font
    font = ImageFont.truetype("arial.ttf", 24)
except:
    # Fallback to default font
    font = ImageFont.load_default()

text = "No Image\nAvailable"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
draw.text(((300 - text_width) / 2, (450 - text_height) / 2), 
          text, fill='#999999', font=font, align='center')

# Save
img.save('static/images/book-placeholder.jpg')
print("✅ Placeholder image created at static/images/book-placeholder.jpg")
