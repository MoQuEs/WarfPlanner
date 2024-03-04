from random import randint, choices
from math import floor

from cv2 import IMWRITE_PNG_COMPRESSION, imwrite, resize, imread, IMREAD_UNCHANGED
from dotenv import load_dotenv

from App.Init import arknights
from App.Utils import (
    materials_dir,
    auto_labels_in_dir,
    generate_random_string as grs,
    get_mats_to_generate_auto_labels,
    clear_auto_labels_in_dir,
)
from App.Image import get_random_image, overlay_image


def main() -> None:
    load_dotenv()
    clear_auto_labels_in_dir()

    mats_data = get_mats_to_generate_auto_labels(
        arknights, lambda data: data["count"] < 50 or data["represented"] != "Over Represented"
    )
    names, ids, counts, represented = zip(*mats_data)
    weights = [1 / count for count in counts]
    total_weight = sum(weights)
    normalized_weights = [weight / total_weight for weight in weights]

    def get_random_mat_id():
        return choices(ids, normalized_weights)[0]

    resolutions = [
        [1920, 1080],
        [1600, 900],
        [1440, 900],
        [1366, 768],
        [1280, 1024],
        [1280, 800],
    ]

    for _ in range(0, 50):
        wh_space = randint(10, 30)
        size = randint(100, 200)
        [width, height] = resolutions[randint(0, len(resolutions) - 1)]
        [max_cols, max_rows] = [
            min(floor(width / (size + (wh_space * 2))), 9),
            min(floor(height / (size + (wh_space * 2))), 6),
        ]

        while True:
            [cols, rows] = [randint(floor(max_cols / 2), max_cols), randint(floor(max_rows / 2), max_rows)]
            [fw_size, fh_size] = [floor(width / cols), floor(height / rows)]
            [pw_size, ph_size] = [floor((fw_size - size) / 2), floor((fh_size - size) / 2)]
            [sp_width, sp_height] = [floor((width - (fw_size * cols)) / 2), floor((height - (fh_size * rows)) / 2)]
            if ((pw_size * 2) < size or cols == 9) and ((ph_size * 2) < size or rows == 6):
                break

        base_image = get_random_image(width, height)

        for col in range(0, cols):
            for row in range(0, rows):
                mat_id = get_random_mat_id()
                material_image = imread(materials_dir("%s.png" % mat_id), IMREAD_UNCHANGED)
                material_image = resize(material_image, (size, size))

                overlay_image(
                    base_image,
                    material_image,
                    (sp_width + (fw_size * col) + pw_size, sp_height + (fh_size * row) + ph_size),
                )

        imwrite(auto_labels_in_dir("%s-%s.%s" % (grs(), grs(), "png")), base_image, [int(IMWRITE_PNG_COMPRESSION), 0])


if __name__ == "__main__":
    main()
