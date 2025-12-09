from PIL import Image, ImageDraw

def create_nyan():
    # Canvas size (small pixel art)
    w, h = 34, 24
    scale = 4 # Scale up for visibility
    
    # Create empty transparent image
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pixels = img.load()
    
    # Accurate Nyan Colors
    tart_edge = (255, 153, 0, 255) # Orange-ish edge
    tart_fill = (255, 153, 255, 255) # Pink #ff99ff
    tart_spot = (255, 51, 153, 255) # Dark Pink spots #ff3399
    head_grey = (153, 153, 153, 255)
    
    # Rainbow Colors (Red, Orange, Yellow, Green, Blue, Violet)
    rainbow = [
        (255, 0, 0, 255),    
        (255, 153, 0, 255),  
        (255, 255, 0, 255),  
        (51, 255, 0, 255),   
        (0, 153, 255, 255),  
        (102, 51, 255, 255)  
    ]
    
    # 1. Draw Rainbow Trail
    for i, color in enumerate(rainbow):
        for x in range(0, 18):
            # Wavy effect: up down up down
            # Patterns: x%4 == 0 or 1 -> offset 0
            #           x%4 == 2 or 3 -> offset 1
            y_offset = 0 if (x % 4) < 2 else 1
            
            # Each color band is 2 pixels high
            base_y = 5 + (i * 2)
            
            pixels[x, base_y + y_offset] = color
            pixels[x, base_y + 1 + y_offset] = color

    # 2. Draw Pop Tart Body
    # Main box
    for x in range(12, 29):
        for y in range(4, 18):
            pixels[x, y] = tart_edge
            
    # Filling (inset by 1)
    for x in range(13, 28):
        for y in range(5, 17):
            pixels[x, y] = tart_fill
            
    # Sprinkles (Spots)
    dots = [(15,7), (20,6), (25,9), (17,12), (23,13), (15,15)]
    for dx, dy in dots:
        pixels[dx, dy] = tart_spot

    # 3. Draw Head (Grey block)
    head_x = 24
    head_y = 7
    # 8x7 rectangle
    for x in range(head_x, head_x + 8):
        for y in range(head_y, head_y + 7):
            pixels[x, y] = head_grey
            
    # Face details (Eyes, Mouth etc - simplified)
    # Eyes (Black)
    pixels[head_x + 2, head_y + 2] = (0, 0, 0, 255)
    pixels[head_x + 6, head_y + 2] = (0, 0, 0, 255)
    # Nose/Mouth
    pixels[head_x + 4, head_y + 4] = (0, 0, 0, 255) 
    
    # 4. Draw Feet
    feet_positions = [(14, 18), (15, 18), (26, 18), (27, 18)]
    for fx, fy in feet_positions:
        pixels[fx, fy] = head_grey

    # 5. Draw Tail
    tail_pixels = [(11, 10), (10, 10), (9, 11)]
    for tx, ty in tail_pixels:
        pixels[tx, ty] = head_grey
    
    # Ears
    pixels[head_x, head_y-1] = head_grey
    pixels[head_x+7, head_y-1] = head_grey


    # Resize (Nearest Neighbor to keep pixel look)
    # Native 34x24 -> 4x Scale -> 136x96
    final_img = img.resize((w * scale, h * scale), Image.Resampling.NEAREST)
    
    output_path = r"c:\projects\0.ongoing\StemLab\resources\nyan_v2.png"
    final_img.save(output_path)
    print(f"Created pixel-perfect Nyan Cat at {output_path}")

if __name__ == "__main__":
    create_nyan()
