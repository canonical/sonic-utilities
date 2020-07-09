"""
Abstract Bootloader class
"""

import sys
from os import path

from ..common import (
   HOST_PATH,
   IMAGE_DIR_PREFIX,
   IMAGE_PREFIX,
)

class Bootloader(object):

    NAME = None
    DEFAULT_IMAGE_PATH = None

    def get_current_image(self):
        """returns name of the current image"""
        raise NotImplementedError

    def get_next_image(self):
        """returns name of the next image"""
        raise NotImplementedError

    def get_installed_images(self):
        """returns list of installed images"""
        raise NotImplementedError

    def set_default_image(self, image):
        """set default image to boot from"""
        raise NotImplementedError

    def set_next_image(self, image):
        """set next image to boot from"""
        raise NotImplementedError

    def install_image(self, image_path):
        """install new image"""
        raise NotImplementedError

    def remove_image(self, image):
        """remove existing image"""
        raise NotImplementedError

    def get_binary_image_version(self, image_path):
        """returns the version of the image"""
        raise NotImplementedError

    def verify_binary_image(self, image_path):
        """verify that the image is supported by the bootloader"""
        raise NotImplementedError

    def verify_reboot(self):
        """verify the image for reboot"""
        image = self.get_next_image()
        image_path = self.get_image_path(image)
        if not path.exists(image_path):
            sys.stderr.write('Next image {0} doesn\'t exist ...\n'.format(image))
            return False
        return True

    @classmethod
    def detect(cls):
        """returns True if the bootloader is in use"""
        return False

    @classmethod
    def get_image_path(cls, image):
        """returns the image path"""
        prefix = HOST_PATH + '/' + IMAGE_DIR_PREFIX
        return image.replace(IMAGE_PREFIX, prefix)

