import os
import cv2
import random
import pickle
from pathlib import Path
import tensorflow as tf
from models.config import TABLE_PATH, NUM_CLASSES,OUTPUT_SHAPE, WORK_PATH

#字典查询器
table = tf.lookup.StaticHashTable(
            tf.lookup.TextFileInitializer(
                TABLE_PATH, 
                tf.string, 
                tf.lookup.TextFileIndex.WHOLE_LINE, 
                tf.int64, tf.lookup.TextFileIndex.LINE_NUMBER
            ), 
        NUM_CLASSES-2)

#数据预处理方法
def preprocess_image(image, mode = 'train'):
    image = tf.image.decode_jpeg(image, channels=3)
    image = image / 255
    image -= 0.5
    image /= 0.5
    if mode == 'train':
        image_shape = (32, 320, 3)
        # 饱和度
        image = tf.image.random_saturation(image, 0.1, 5)
        # 色调
        image = tf.image.random_hue(image, 0.2)
        # 对比度
        image = tf.image.random_contrast(image, 0.2, 3)
        # 亮度
        image = tf.image.random_brightness(image, max_delta=0.5)
        # 随机噪声
        image = tf.image.random_jpeg_quality(image,0,100)
    else:
        image_shape = (32, 720, 3)
    imgH, imgW, imgC = image_shape
    resized_image = tf.image.resize(image, [imgH, imgW],preserve_aspect_ratio=True)
    padding_im = tf.image.pad_to_bounding_box(resized_image,0,0,imgH, imgW)
    return padding_im

def load_and_preprocess_image(path,label):
    image = tf.io.read_file(path)
    return preprocess_image(image),label

def load_and_preprocess_image_pridict(path, mode = 'predict'):
    image = tf.io.read_file(path)
    return preprocess_image(image, mode)

def load_and_preprocess_image_draw(path):
    image = tf.io.read_file(path)
    img = tf.image.decode_jpeg(image, channels=3)
    return img

def decode_label(img,label):
    chars = tf.strings.unicode_split(label, "UTF-8")
    tokens = tf.ragged.map_flat_values(table.lookup, chars)
    tokens = tokens.to_sparse()
    return img,tokens


def get_image_path(dir_path):
    '''
    获取图片路径列表,及其标签列表
    '''
    if os.path.exists(WORK_PATH+'dataset/dataset.data'):
        with open(WORK_PATH+'dataset/dataset.data', 'rb') as f:
            train_all_image_paths, train_all_image_labels,val_all_image_paths,val_all_image_labels = pickle.load(f)
        print('数据集加载完毕！')
        return train_all_image_paths, train_all_image_labels,val_all_image_paths,val_all_image_labels
    else:
        print('开始获取数据集，请耐心等待...')
        images  = []
        train_all_image_paths = []
        train_all_image_labels = []
        val_all_image_paths = []
        val_all_image_labels = []
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if '.jpg' in file:
                    file_path = os.path.join(root, file)
                    label_path = file_path.replace('.jpg','.txt')
                    if Path(file_path.replace('.jpg','.txt')).exists():
                        with open(label_path) as f:
                            label = f.read().strip()
                        imgs= cv2.imread(file_path)
                        if imgs.shape[1]/imgs.shape[0] <= 10 and len(label)>0:
                            images.append((file_path, label))
        random.shuffle(images)
        for image,label in images:
            random_num = random.randint(1,80)
            if random_num == 5:
                val_all_image_paths.append(image)
                val_all_image_labels.append(label)
            else:
                train_all_image_paths.append(image)
                train_all_image_labels.append(label)
        with open(WORK_PATH+'dataset/dataset.data', 'wb') as f:
            pickle.dump((train_all_image_paths, train_all_image_labels,val_all_image_paths,val_all_image_labels), f)
        print('数据集加载完毕！')
        return train_all_image_paths, train_all_image_labels,val_all_image_paths,val_all_image_labels