import cv2
from PIL import Image, ImageEnhance  # , ImageFilter


def apply_texture(image):
    paper_texture = Image.open("Data/sources/paper_textures/paper_texture_2.jpg")
    texture_image = paper_texture.resize(image.size)
    image = Image.blend(image, texture_image, 0.5)

    return image


def apply_shadows(image):
    # Adjust brightness and contrast
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1)

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.6)

    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(0)

    return image
    #
    # # Add drop shadow using image convolution
    # shadow_mask = Image.new("L", image.size)
    # shadow_mask.paste(100, offset=(shadow_offset_x, shadow_offset_y))
    # image = Image.composite(image, Image.new("RGBA", image.size), shadow_mask)


def modify_image(image_path):
    image = Image.open(image_path)
    image = apply_texture(image)
    image = apply_shadows(image)

    image.save("Testing.jpg")
    image.show()


if __name__ == '__main__':
    modify_image("Data/sources/hospitalInformationSheet.jpg")
