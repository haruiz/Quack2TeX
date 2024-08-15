from PIL.Image import Image as PILImage
import base64
from io import BytesIO


class ImageUtils:
    """
    Utility functions for images.
    """

    @staticmethod
    def image_to_base64(image: PILImage) -> str:
        """
        Convert an image to a base64 string.
        :param image:
        :return:
        """
        buffered = BytesIO()
        image.save(
            buffered, format=image.format or "PNG"
        )  # Default to 'PNG' if format is None
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    @staticmethod
    def image_to_base64_url(image: PILImage) -> str:
        """Convert an image to a base64 data URL."""
        return f"data:image/{image.format.lower()};base64,{ImageUtils.image_to_base64(image)}"
