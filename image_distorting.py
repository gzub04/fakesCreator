import random
from PIL import Image, ImageEnhance  # , ImageFilter


MAX_SCAN_ROTATION = 1.8
MAX_PHOTO_ROTATION = None

PAPER_PATH = "data/sources/textures"
BACKGROUND_PATH = 'data/sources/textures/img_background.jpg'


class ImageDistorting:
    def __init__(self):
        self.paper_textures = []
        self.background = None

        # paper textures
        for texture_num in range(1, 7):
            path_to_img = f"{PAPER_PATH}/paper_texture_{texture_num}.jpg"
            try:
                texture = Image.open(path_to_img)
                self.paper_textures.append(texture)

            except FileNotFoundError:
                print(f"File Not Found Error: Missing {path_to_img}")
                exit(1)
            except PermissionError:
                print(f"Permission Error: Can't access {path_to_img}")
                exit(1)

        # background texture
        try:
            background_texture = Image.open(BACKGROUND_PATH)
            self.background = background_texture
        except FileNotFoundError:
            print(f"File Not Found Error: Missing {BACKGROUND_PATH}")
            exit(1)
        except PermissionError:
            print(f"Permission Error: Can't access {BACKGROUND_PATH}")
            exit(1)

    def _apply_paper_texture(self, image):
        if random.randint(1, 10) == 10:
            # choose crumpled paper
            choice = random.randint(4, 5)
        else:
            choice = random.randint(0, 3)

        paper_texture = self.paper_textures[choice]

        texture_image = paper_texture.resize(image.size)
        image_w_texture = Image.blend(image, texture_image, 0.5)

        return image_w_texture

    def rotate_img(self, pil_image, img_type):
        """
        rotates image by a random amount and adds background based on image type
        :param pil_image: image in PIL format
        :param img_type: string 'scan' or 'photo'
        :return: returns rotated image in PIL format
        """

        if img_type == 'scan':
            rotation = random.uniform(-MAX_SCAN_ROTATION, MAX_SCAN_ROTATION)
            output_image = pil_image.rotate(
                rotation, expand=True, fillcolor=(255, 255, 255, 255), resample=Image.BICUBIC
            )
        elif img_type == 'photo':
            rotation = random.uniform(-MAX_PHOTO_ROTATION, MAX_PHOTO_ROTATION)
            # Rotate and expand the image, filling empty space with black
            rotated_pil_image = pil_image.rotate(
                rotation, expand=True, fillcolor=(0, 0, 0, 0), resample=Image.BICUBIC
            )
            # Create a mask
            mask = rotated_pil_image.convert('L').point(lambda x: 255 if x > 0 else 0)
            # resize the background and paste
            width, height = rotated_pil_image.size
            extend_image = 64
            width += extend_image
            height += extend_image
            output_image = self.background.resize((width, height))
            output_image.paste(rotated_pil_image, (32, 32), mask)

            rotated_pil_image.close()
        else:
            print(f"Error: unknown img_type \"{img_type}\" in rotate_img function")
            exit(1)

        # note changes in image
        in_width, in_height = pil_image.size
        out_width, out_height = output_image.size
        changes = {
            'rotation': rotation,
            'width_increase': out_width - in_width,
            'height_increase': out_height - in_height
        }

        return output_image, changes

    def photo_distortion(self, pil_image):
        output_image = self._apply_paper_texture(pil_image)

        # Adjust brightness and blur
        enhancer = ImageEnhance.Brightness(output_image)
        brightness = random.uniform(0.75, 1)
        output_image = enhancer.enhance(brightness)

        enhancer = ImageEnhance.Sharpness(output_image)
        sharpness = random.uniform(-1, 3)
        output_image = enhancer.enhance(-sharpness)

        return output_image

    @staticmethod
    def scan_distortion(pil_image):
        enhancer = ImageEnhance.Brightness(pil_image)
        brightness = random.uniform(1.1, 1.3)
        pil_image = enhancer.enhance(brightness)

        return pil_image
