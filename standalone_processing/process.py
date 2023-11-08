from collections import defaultdict
import torch

import numpy as np
from skimage.io import imread, imsave
from skimage.transform import resize
from skimage.exposure import rescale_intensity
import os

from glob import glob

from tqdm.auto import tqdm

import hydra
from omegaconf import DictConfig, OmegaConf
import re
import yaml

import cv2

import imgviz

define_nearest_crop = lambda x: int((x//32)*32)
is_img = re.compile('^.*.(jpg|jpeg|png|tif|tiff)', flags=re.IGNORECASE)

class Processor:
    def _process_one_image(self, img):
        raise NotImplementedError('processing one image is not implemented somehow!')
    
    def _load_one_image(self, img_addr):
        img = imread(img_addr)
        img = np.moveaxis(img, -1, 0)
        img = img[..., :define_nearest_crop(img.shape[-2]), :define_nearest_crop(img.shape[-1])]
        img = torch.FloatTensor(img/255)[None, ...]
        return img
    
    def _process_one_folder(self, folder_addr, target_folder_masks, target_folder_imres):
        for img_addr in tqdm([i for i in glob(os.path.join(folder_addr, '*')) if re.match(is_img, i)], desc='images', leave=False):
            if img_addr.split('.')[-2].endswith('_R'):
                continue
            if os.path.basename(img_addr).startswith('WS_'):
                continue
            try:
                img = self._load_one_image(img_addr)
                mask, imres = self._process_one_image(img)
                
                np.save(os.path.join(target_folder_masks, self.prefix+os.path.basename(img_addr.split('.')[0])), mask)
                imsave(os.path.join(target_folder_imres, self.prefix+os.path.basename(img_addr.split('.')[0])), imres)
            except Exception as e:
                print(f'Image {img_addr} will not be processed: {e}.')

import pytorch_lightning as pl
from segmentation_models_pytorch import Unet
import torch

class Segmenter(Processor):
    def __init__(self, checkpoint_addr, classes_names, prefix, **kwargs):
        self.model = Unet('resnet18', in_channels=3, classes=len(classes_names)+1)
        self.model.load_state_dict(torch.load(checkpoint_addr))
        self.model.eval()
        if torch.cuda.is_available():
            self.model = self.model.to('cuda:0')
        self.classes_names = classes_names
        self.prefix = prefix
    
    def _process_one_image(self, img):
        if torch.cuda.is_available():
            img = img.to('cuda:0')
        pred = self.model.model.forward(img)[0].detach().cpu().numpy().argmax(0)

        imres = imgviz.label2rgb(pred, np.moveaxis((img[0].detach().cpu().numpy()*255).astype(np.uint8), 0, -1), 
                                        label_names=['background']+self.classes_names)
        return pred, imres

import pandas as pd

@hydra.main(config_path='./config', config_name="config")
def main(cfg : DictConfig) -> None:
    folder_to_process= cfg['photo_collection']
    folder_to_save_masks = cfg['masks_folder']
    folder_to_save_overlays = cfg['overlay_folder']

    processors_configs = cfg['processors']

    for proc_conf in tqdm(OmegaConf.to_container(processors_configs, resolve=True), desc='processors'):
        procerssor_class = proc_conf.pop('processor_class')
        processor = globals()[procerssor_class](**proc_conf)
        processor._process_one_folder(folder_to_process, folder_to_save_masks, folder_to_save_overlays)
    
if __name__ == "__main__":
    main()
