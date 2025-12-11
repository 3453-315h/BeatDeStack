from PIL import Image

def remove_checkerboard(path):
    print(f"Opening {path}...")
    img = Image.open(path).convert("RGBA")
    data = img.getdata()
    
    new_data = []
    
    # Target: The specific gray values found in the analysis
    # Range identified: 105-113 for R, G, B
    
    for item in data:
        r, g, b, a = item
        
        # Check if gray (r,g,b are close) and within the "checkerboard" range
        if 100 <= r <= 120 and 100 <= g <= 120 and 100 <= b <= 120:
             # Additional check: typical grays have r~=g~=b
             if abs(r-g) < 10 and abs(r-b) < 10:
                 new_data.append((0, 0, 0, 0)) # Transparent
             else:
                 new_data.append(item)
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    img.save(path)
    print("Checkerboard transparency applied.")

if __name__ == "__main__":
    remove_checkerboard(r"c:\projects\0.ongoing\StemLab\resources\nyan.png")
