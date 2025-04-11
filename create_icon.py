from PIL import Image, ImageDraw
import os

# Create a simple crosshair icon
icon_size = 256
icon = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
draw = ImageDraw.Draw(icon)

# Background circle
circle_radius = icon_size // 2.5
center = icon_size // 2
draw.ellipse(
    [(center - circle_radius, center - circle_radius), 
     (center + circle_radius, center + circle_radius)], 
    fill=(93, 95, 239, 180)  # Semi-transparent primary color
)

# Crosshair lines
line_width = icon_size // 20
line_length = circle_radius * 1.5
gap = icon_size // 10

# Horizontal lines
draw.rectangle(
    [(center - line_length, center - line_width//2), 
     (center - gap, center + line_width//2)], 
    fill=(255, 255, 255, 230)
)
draw.rectangle(
    [(center + gap, center - line_width//2), 
     (center + line_length, center + line_width//2)], 
    fill=(255, 255, 255, 230)
)

# Vertical lines
draw.rectangle(
    [(center - line_width//2, center - line_length), 
     (center + line_width//2, center - gap)], 
    fill=(255, 255, 255, 230)
)
draw.rectangle(
    [(center - line_width//2, center + gap), 
     (center + line_width//2, center + line_length)], 
    fill=(255, 255, 255, 230)
)

# Center dot
dot_radius = icon_size // 15
draw.ellipse(
    [(center - dot_radius, center - dot_radius), 
     (center + dot_radius, center + dot_radius)], 
    fill=(255, 20, 20, 230)  # Semi-transparent red
)

# Create resources directory if it doesn't exist
os.makedirs('src/resources', exist_ok=True)

# Save as PNG first (for ICO conversion)
png_path = 'src/resources/crosshair_icon.png'
icon.save(png_path)
print(f"Created PNG icon at {png_path}")

# Try to create ICO if PIL supports it
try:
    ico_path = 'src/resources/crosshair_icon.ico'
    icon.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Created ICO file at {ico_path}")
except Exception as e:
    print(f"Could not create ICO file: {e}")
    print("You may need to convert the PNG to ICO using an online converter.")

# Create a copy in static for the spec file
static_icon_path = 'static/crosshair_icon.ico'
try:
    icon.save(static_icon_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Created ICO file at {static_icon_path}")
except Exception as e:
    print(f"Could not create static ICO file: {e}") 