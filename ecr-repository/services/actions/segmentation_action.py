import gc
import cv2
import argparse
import skimage.io
import numpy as np
import keras.backend as K
from pixellib.instance import instance_segmentation
K.set_image_data_format('channels_last')


ap = argparse.ArgumentParser()
ap.add_argument("-sm", "--segmentation_model", required=True, help='segmentation model path')
ap.add_argument("-f", "--file", required=True, help='file path')
args = vars(ap.parse_args())

def get_silhouette(mask, file_path):
    image = skimage.io.imread(file_path)
    for i in range(mask.shape[2]):
        for j in range(image.shape[2]):
            image[:,:,j] = image[:,:,j] * mask[:,:,i]
    _, _segmented_img = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY)
    return _segmented_img

# get the local file path
file_path = args['file']

# load segmentation model
instance_segmentation = instance_segmentation()
instance_segmentation.load_model(args['segmentation_model'])

# creates the segmentation target
target_classes = instance_segmentation.select_target_classes(person=True)

# target person in the image
mask, _ = instance_segmentation.segmentImage(
    file_path, 
    segment_target_classes=target_classes, 
    extract_segmented_objects=True
)

# convert targeting values ​​to integer
mask = mask['masks'].astype(int)

# get silhouette of the person in the image and
# save the new image in the local folder
cv2.imwrite(file_path, get_silhouette(mask, file_path))

# clear session
K.clear_session()
del instance_segmentation
gc.collect()