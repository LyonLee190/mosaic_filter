import cv2
import numpy as np

def create_blank(height, width, rgb_color=(0, 0, 0)):
    '''
    https://stackoverflow.com/questions/9710520/opencv-createimage-function-isnt-working
    '''
    # Create black blank image
    image = np.zeros((height, width, 3), np.uint8)

    # Since OpenCV uses BGR, convert the color first
    color = tuple(reversed(rgb_color))
    # Fill image with color
    image[:] = color

    return image

# main() function
def main():
    while True:
        color_code = input("Color code in hex (Q to quit): ")
        if color_code == "Q":
            break

        R = int(color_code[0:2], 16)
        print("Value of R: ", R)
        G = int(color_code[2:4], 16)
        print("Value of G: ", G)
        B = int(color_code[4:6], 16)
        print("Value of B: ", B)

        rgb_color = (int(R), int(G), int(B))
        img = create_blank(128, 128, rgb_color=rgb_color)
        cv2.imwrite("#" + color_code.upper() + ".jpg", img)

# call main
if __name__ == '__main__':
    main()
