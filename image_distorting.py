import random
from PIL import Image, ImageEnhance  # , ImageFilter


MAX_SCAN_ROTATION = 1.8
MAX_PHOTO_ROTATION = None

PAPER_PATH = "Data/sources/paper_textures/"


class ImageDistorting:
    def __init__(self):
        self.paper_textures = []

        for texture_num in range(1, 7):
            path_to_img = f"{PAPER_PATH}paper_texture_{texture_num}.jpg"
            try:
                with Image.open(path_to_img) as texture:
                    self.paper_textures.append(texture)

            except FileNotFoundError:
                print(f"File Not Found Error: Missing {path_to_img}")
                exit(1)
            except PermissionError:
                print(f"Permission Error: Can't access {path_to_img}")
                exit(1)
            except Exception as e:
                print(f"An error occurred while handling {path_to_img}: {str(e)}")
                exit(1)

    def _apply_paper_texture(self, image):
        if random.randint(1, 10) == 10:
            # choose crumpled paper
            choice = random.randint(4, 5)
        else:
            choice = random.randint(0, 3)

        paper_texture = self.paper_textures[choice]

        texture_image = paper_texture.resize(image.size)
        image = Image.blend(image, texture_image, 0.5)

        return image

    @staticmethod
    def _rotate_img(pil_image, max_rotation):
        rotation = random.uniform(-max_rotation, max_rotation)
        pil_image = pil_image.rotate(rotation, fillcolor=(255, 255, 255), resample=Image.BICUBIC)

        return pil_image

    @staticmethod
    def photo_distortion(pil_image):
        # Adjust brightness and contrast
        enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = enhancer.enhance(1)

        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1)

        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(1)

        return pil_image
        #
        # # Add drop shadow using image convolution
        # shadow_mask = Image.new("L", image.size)
        # shadow_mask.paste(100, offset=(shadow_offset_x, shadow_offset_y))
        # image = Image.composite(image, Image.new("RGBA", image.size), shadow_mask)

        # pil_image.save("Testing.jpg")
        # pil_image.show()

    @staticmethod
    def scan_distortion(pil_image):
        enhancer = ImageEnhance.Brightness(pil_image)
        brightness = random.uniform(1.1, 1.3)
        pil_image = enhancer.enhance(brightness)

        return pil_image
