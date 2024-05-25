import glob
import json
import traceback

import numpy as np
import torch
from torch import nn
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
from PIL import Image
from skimage.util.shape import view_as_windows
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

import scipy.ndimage as ndimage
import os
from flask import Flask, flash, request, redirect, send_file, Response
from threading import Lock

mutex = Lock()

UPLOAD_FOLDER = './uploaded'
PROCESSED_FOLDER = './processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


@app.route("/hello", methods=['GET', 'POST'])
def hello():
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], "lol")
    print(upload_path)
    return "hello"


@app.route("/process", methods=['POST'])
def process():
    print("Start processing image")

    if 'image' not in request.files:
        return Response("no image", status=400)

    file = request.files.get('image')
    print(f"Processing file: {file.filename}")

    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    process_path = os.path.join(app.config['PROCESSED_FOLDER'], file.filename)

    with mutex:
        file.save(upload_path)
        image = Image.open(upload_path)

    print("Image opened")
    try:
        res_image, res_mask, cl_coefs = predict_full(image)
    except Exception as e:
        print(traceback.format_exc())

    im = Image.fromarray(res_image)
    print("Image processed")

    with mutex:
        im.save(process_path)
        # os.remove(upload_path)
        response = send_file(
            os.path.join(app.config['PROCESSED_FOLDER'], file.filename),
            mimetype='image/jpg'
        )
        response.set_cookie("cl_coefs", json.dumps(cl_coefs, cls=NpEncoder))
        return response


MODEL_CHECKPOINT = 'nvidia/mit-b2'
model_path = "model.pt"

h = 512
w = 512
stride = 512

id2label = {
    0: "background",
    1: "iron",
    2: "fishing gear",
    3: "plastic",
    4: "tree",
    5: "concrete",
    6: "rubber"
}

cl_to_name = {
    1: "железо",
    2: "рыболовные снасти",
    3: "пластик",
    4: "дерево",
    5: "бетон",
    6: "резина"
}

palette = {1: [255, 255, 255], 2: [0, 255, 255], 3: [0, 255, 0], 4: [255, 0, 0], 5: [255, 0, 255], 6: [255, 255, 0]}

label2id = {v: k for k, v in id2label.items()}
id2color = {x: y for x, y in palette.items()}

image_processor = SegformerImageProcessor.from_pretrained(MODEL_CHECKPOINT)
image_processor.do_reduce_labels = False
image_processor.reduce_labels = False

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

loaded_model = SegformerForSemanticSegmentation.from_pretrained(MODEL_CHECKPOINT,
                                                                num_labels=len(id2label),
                                                                id2label=id2label,
                                                                label2id=label2id)

loaded_model.load_state_dict(torch.load(model_path, map_location=device))
loaded_model = loaded_model.to(device)


# Параллельное предсказание, работает только на больших GPU
# def predict(batch):
#     images = []
#     for image in batch:
#         images.append(Image.fromarray(image))
#
#     encoding = image_processor(images, return_tensors="pt")
#     pixel_values = encoding.pixel_values.to(device)
#     outputs = loaded_model(pixel_values=pixel_values)
#
#     logits = outputs.logits.cpu()
#
#     # First, rescale logits to original image size
#     upsampled_logits = nn.functional.interpolate(logits,
#                                                  size=images[0].size[::-1],  # (height, width)
#                                                  mode='bilinear',
#                                                  align_corners=False)
#     batch_seg = upsampled_logits.argmax(dim=1)
#     batch_images = []
#
#     for i, seg in enumerate(batch_seg):
#         color_seg = np.zeros((seg.shape[0], seg.shape[1], 3), dtype=np.uint8)  # height, width, 3
#         for label, color in id2color.items():
#             color_seg[seg == label, :] = color
#
#         img = batch[i] * 0.8 + color_seg * 0.2
#         img = img.astype(np.uint8)
#         batch_images.append(img)
#
#     return batch_seg, batch_images


def predict(batch):
    images = []
    for image in batch:
        images.append(Image.fromarray(image))

    batch_seg = []
    batch_images = []

    for i, image in enumerate(images):
        encoding = image_processor(image, return_tensors="pt")
        pixel_values = encoding.pixel_values.to(device)
        outputs = loaded_model(pixel_values=pixel_values)
        logits = outputs.logits.cpu()

        # First, rescale logits to original image size
        upsampled_logits = nn.functional.interpolate(logits,
                                                     size=image.size[::-1],  # (height, width)
                                                     mode='bilinear',
                                                     align_corners=False)

        seg = upsampled_logits.argmax(dim=1)[0]
        batch_seg.append(seg)

        color_seg = np.zeros((seg.shape[0], seg.shape[1], 3), dtype=np.uint8)  # height, width, 3
        for label, color in id2color.items():
            color_seg[seg == label, :] = color

        img = batch[i] * 0.7 + color_seg * 0.3
        img = img.astype(np.uint8)
        batch_images.append(img)

    return batch_seg, batch_images


def predict_full(image):
    arr = np.array(image)
    img = arr
    # img = arr[:define_nearest_crop(arr.shape[0]), :define_nearest_crop(arr.shape[1]), ...]

    height = img.shape[0]
    width = img.shape[1]

    n = 1
    if height % stride == 0:
        n = height // stride
    else:
        n = height // stride + 1

    m = 1
    if width % stride == 0:
        m = width // stride
    else:
        m = width // stride + 1

    n_m = n * m

    res_image = np.zeros((height, width, 3))
    res_mask = np.zeros((height, width))

    crops = []

    for index in range(n_m):
        row_num = index // n
        col_num = index % n

        x_min = stride * col_num
        x_max = min(stride * col_num + h, height)

        y_min = stride * row_num
        y_max = min(stride * row_num + w, width)

        img_crop = arr[x_min:x_max, y_min:y_max, ...]
        crops.append(img_crop)

    predicted_seg, predicted_images = predict(crops)

    for index in range(n_m):
        row_num = index // n
        col_num = index % n

        x_min = stride * col_num
        x_max = min(stride * col_num + h, height)

        y_min = stride * row_num
        y_max = min(stride * row_num + w, width)

        res_image[x_min:x_max, y_min:y_max, ...] = predicted_images[index]
        res_mask[x_min:x_max, y_min:y_max] = predicted_seg[index]

    res_image = np.uint8(res_image)
    cl_coefs = {}

    for cl, _ in cl_to_name.items():
        cl_coefs[cl] = calc_coefs(res_mask, cl=cl)

    return res_image, res_mask, cl_coefs


cl_to_max_window = {
    1: 2,
    2: 2,
    3: 2,
    4: 4,
    5: 6,
    6: 3,
}

cl_to_density = {
    1: 8000,
    2: 800,
    3: 400,  # может быть и легче, но мне кажется, что он обычно моркый и тяжелый
    4: 900,  # так как чаще всего мокрое
    5: 2600,
    6: 2000,
}


def strided4D_v2(arr, arr2, s):
    return view_as_windows(arr, arr2.shape, step=s)


def stride_conv_strided(arr, arr2, s):
    arr4D = strided4D_v2(arr, arr2, s=s)
    return np.tensordot(arr4D, arr2, axes=((2, 3), (0, 1)))


def separate_objects_masks(mask):
    """
    mask: должна содержать только значиния 0 и 255,
    h x w x 3, все 3 канала одинаково заполнены
    """
    res = []

    label_im, nb_labels = ndimage.label(mask)

    for i in range(nb_labels):
        mask = label_im == i + 1
        if np.sum(mask) < 80:  # filter small objects
            continue
        res.append(mask)
    return res


def calc_coefs(mask, cl):
    coefs = []
    cl_mask = mask == cl

    masks = separate_objects_masks(cl_mask)
    for v in masks:
        mass_y, mass_x = np.where(v)
        cent_y = np.average(mass_y)
        cent_x = np.average(mass_x)

        square_in_pixels = np.sum(v)

        size = 4
        kernel = np.ones((size, size))
        denom = size * size

        squares = stride_conv_strided(v, kernel, s=size) / denom

        max_window = cl_to_max_window[cl]
        k = max_window - 1

        padded = np.pad(squares, [(k, k), (k, k)], mode='constant', constant_values=0)

        kernel_hor = np.array([[1.0] * max_window])
        kernel_vert = np.array([[1.0]] * max_window)

        hor = stride_conv_strided(padded, kernel_hor, s=1)
        vert = stride_conv_strided(padded, kernel_vert, s=1)

        l = hor[k:-k, :-k]
        r = hor[k:-k, k:]
        up = vert[:-k, k:-k]
        down = vert[k:, k:-k]

        res = np.stack([l, r, up, down]).min(axis=0)

        volume_coef = np.sum(res) / np.sum(squares)
        mass_coef = cl_to_density[cl] * volume_coef
        coefs.append([int(cent_y), int(cent_x), square_in_pixels, volume_coef, mass_coef])

    return coefs


def delete_files_in_dir(path):
    try:
        files = glob.glob(os.path.join(path, '*'))
        for file in files:
            if os.path.isfile(file):
                os.remove(file)
        print(f"All files deleted successfully in {path}")
    except OSError:
        print(f"Error occurred while deleting files in {path}")


def clear_dirs():
    with mutex:
        delete_files_in_dir(app.config['PROCESSED_FOLDER'])


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=clear_dirs, trigger="interval", seconds=60 * 60)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    print("DEVICE: ", device)
    app.run(host='0.0.0.0', port=8000)
