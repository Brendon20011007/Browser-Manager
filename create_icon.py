from PIL import Image, ImageDraw

# Create a new image with a white background
size = (256, 256)
image = Image.new('RGBA', size, (255, 255, 255, 0))
draw = ImageDraw.Draw(image)

# Draw a blue circle
circle_color = (0, 120, 212, 255)  # Microsoft blue
circle_radius = 100
circle_center = (size[0]//2, size[1]//2)
draw.ellipse(
    [
        circle_center[0] - circle_radius,
        circle_center[1] - circle_radius,
        circle_center[0] + circle_radius,
        circle_center[1] + circle_radius
    ],
    fill=circle_color
)

# Save as ICO
image.save('browser_icon.ico', format='ICO', sizes=[(256, 256)]) 