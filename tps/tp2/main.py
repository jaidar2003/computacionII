import argparse
from PIL import Image
import os

def main():
    parser = argparse.ArgumentParser(description='Process an image.')
    parser.add_argument('--input', default='/home/juanma/PycharmProjects/compu2/tps/tp2/imagen.png', help='Path to the input image')
    args = parser.parse_args()

    input_path = args.input

    if not os.path.exists(input_path):
        print(f"Error: The file {input_path} does not exist.")
        return

    try:
        image = Image.open(input_path)
        print(f"Successfully loaded image: {input_path}")
        # Aquí se podría agregar código para enviar la imagen al servidor asincrónico.
    except Exception as e:
        print(f"Error loading image: {e}")

if __name__ == '__main__':
    main()
