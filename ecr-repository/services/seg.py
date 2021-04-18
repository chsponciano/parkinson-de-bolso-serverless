import gc
import cv2
import argparse
import skimage.io
import numpy as np
import keras.backend as K
from pixellib.instance import instance_segmentation
K.set_image_data_format('channels_last')


def _get_silhouette(self, mask, file_path):
    image = skimage.io.imread(file_path)
    for i in range(mask.shape[2]):
        for j in range(image.shape[2]):
            image[:,:,j] = image[:,:,j] * mask[:,:,i]
    _, _segmented_img = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY)
    return _segmented_img

ap = argparse.ArgumentParser()
ap.add_argument("-sm", "--segmentation_model", required=True, help='segmentation model path')
ap.add_argument("-f", "--file", required=True, help='file path')
args = vars(ap.parse_args())

instance_segmentation = instance_segmentation()
instance_segmentation.load_model(args['segmentation_model'])
target_classes = instance_segmentation.select_target_classes(person=True)
file_path = args['file']

mask, _ = instance_segmentation.segmentImage(
    file_path, 
    segment_target_classes=_target_classes, 
    extract_segmented_objects=True
)

mask = mask['masks'].astype(int)
cv2.imwrite(file_path, self._get_silhouette(mask, file_path))
K.clear_session()
del instance_segmentation
gc.collect()