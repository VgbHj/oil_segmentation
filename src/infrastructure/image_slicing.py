
from math import ceil
import numpy as np


def crop_image_by_edges(img):
    mask_y, mask_x = np.where(img.sum(axis=2) > 0)
    return img[
        mask_y.min(): mask_y.max(),
        mask_x.min(): mask_x.max()
    ]


def padding_before_sub(img, w_size):
    """Padding image to fit whole image in same slices."""

    # Calculate padding:
    source_shape = img.shape[:-1]
    target_shape = tuple([
        ceil(x / w_size) * w_size
        for x in img.shape[:-1]
    ])
    padding_shape = tuple([
        (0, ts - ss) for ss, ts in zip(source_shape, target_shape)
    ])
    # Padding:
    return np.stack([
        np.pad(img[:, :, ch], padding_shape)
        for ch in range(img.shape[-1])
    ]).transpose(1, 2, 0)


def extract_sub_frames(img, win_h, win_w):
    """Amount of windows by x example:

    window.shape ~ (win_h, win_w)
    x stride (dx) ~ win_w
    y stride (dy) ~ win_h

    (img.shape[-2] - windows.shape[-2]) // dx + 1  =>
    (img.shape[-2] - win_w) // win_w + 1           =>
    img.shape[-2] // win_w - 1 + 1                 =>
    img.shape[-2] // win_w
    """
    # calculate new shape:
    new_shape = (
            img.shape[:-2]  # amount of rows
            + (img.shape[-2] // win_h,)  # amount of windows by y
            + (img.shape[-1] // win_w,)  # amount of windows by x
            + (win_h, win_w)  # size of window
    )
    # calculate new strides:
    new_strides = (
            img.strides[:-2]
            + (img.strides[-2] * win_h,)
            + (img.strides[-1] * win_w,)
            + img.strides[-2:]
    )
    # rolling window:
    return np.lib.stride_tricks.as_strided(
        img,
        shape=new_shape,
        strides=new_strides
    )


def slice_image(img, w_size):
    """Returns (rows, cols, C, H, W)"""
    crop = crop_image_by_edges(img)
    crop_pad = padding_before_sub(crop, w_size)
    return np.stack([
        extract_sub_frames(crop_pad[:, :, ch], w_size, w_size)
        for ch in range(crop_pad.shape[-1])
    ]).transpose(1, 2, 0, 3, 4)


def batch2image(batch, rows, cols):
    _, channels, w_size, _ = batch.shape
    from_batch = batch.reshape(
        rows, cols, channels, w_size, w_size
    )
    return np.vstack([
        np.hstack([*(from_batch[row, :].transpose(0, 2, 3, 1))])
        for row in range(rows)
    ])
