import pickle
from scipy.spatial.distance import hamming
import numpy as np
from tqdm import tqdm
import os


def extract_columns(image):
    matrix = np.transpose(image).tolist()
    tuple_list = [tuple(lst) for lst in matrix]
    unique_tuples = set(tuple_list)
    unique_lists = [list(tup) for tup in unique_tuples]

    unique_columns = np.transpose(np.array(unique_lists))
    unique_columns = np.delete(unique_columns, np.where(np.sum(unique_columns, axis=0) == 0)[0][0], axis=1)

    filtered_unique_columns = []
    counts = []
    for column in tqdm(unique_columns.T, desc='Extraction columns'):
        mirrored_column = column[::-1]

        representative = column if np.sum(np.all(image == column.reshape(-1, 1), axis=0)) >= np.sum(
            np.all(image == mirrored_column.reshape(-1, 1), axis=0)) else mirrored_column
        matches = np.sum(np.all(image == column.reshape(-1, 1), axis=0)) + np.sum(
            np.all(image == mirrored_column.reshape(-1, 1), axis=0))

        if list(column) not in filtered_unique_columns and list(mirrored_column) not in filtered_unique_columns:
            filtered_unique_columns.append(list(representative))
            counts.append(matches)

    filtered_unique_columns = np.transpose(np.array(filtered_unique_columns))
    counts = np.array(counts) / np.sum(counts)
    return filtered_unique_columns, counts


def encode_base62(num):
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = "0123456789"

    idx_char = num // 100
    idx_character = (num - idx_char * 100) // 10
    idx_num = num % 10

    encoding = characters[idx_char] + characters[idx_character] + numbers[idx_num]
    return encoding


def OMP(unique_columns, counts, encodingDir, design, node_tech, increment=1):
    counts = counts.reshape(-1, 1)
    corr_matrix = np.zeros((unique_columns.shape[1], unique_columns.shape[1]))
    for x in range(unique_columns.shape[1]):
        for y in range(unique_columns.shape[1]):
            similarity = 1 - hamming(unique_columns[:, x], unique_columns[:, y])
            corr_matrix[x, y] = similarity

    corr_matrix = (corr_matrix - np.min(corr_matrix)) / (np.max(corr_matrix) - np.min(corr_matrix))
    # corr_matrix_copy = corr_matrix.copy()

    residual = counts
    indices = []

    info_coverage = {'n_components': [], 'info_capture': []}
    while len(indices) <= unique_columns.shape[1]:
        indices.append(np.argmax(residual))
        residual = counts.reshape(-1, 1) - np.multiply(counts.reshape(-1, 1),
                                                       np.max(corr_matrix[:, indices], axis=1).reshape(-1, 1))
        information_capture = 1 - np.sum(residual)
        info_coverage['n_components'].append(len(indices))
        info_coverage['info_capture'].append(information_capture)

        column_dict = {}
        for i in range(len(indices)):
            column_dict[tuple(unique_columns[:, indices[i]])] = encode_base62(i)

        if len(indices) % increment == 0:
            filename = os.path.join(*[encodingDir, 'column_dictionary',
                                      f'{design}_{node_tech}nm_column_dict_{len(indices)}.pkl'])
            with open(filename, 'wb') as f:
                pickle.dump(column_dict, f)
            f.close()
    return info_coverage


def encode_image(image, column_dict):
    image_encoding = ''
    for j in range(1, image.shape[1]):
        if tuple(image[:, j - 1]) != tuple(image[:, j]) and np.sum(image[:, j]) != 0:
            if tuple(image[:, j]) in column_dict.keys():
                image_encoding += column_dict[tuple(image[:, j])]
            elif tuple(image[:, j])[::-1] in column_dict.keys():
                image_encoding += column_dict[tuple(image[:, j])[::-1]]
            else:
                similarity_score = [1 - hamming(list(image[:, j]), list(k)) for k in column_dict.keys()]
                ss_reversed = [1 - hamming(list(image[:, j])[::-1], list(k)) for k in column_dict.keys()]
                if np.max(similarity_score) < np.max(ss_reversed):
                    key = list(column_dict.keys())[np.argmax(ss_reversed)]
                else:
                    key = list(column_dict.keys())[np.argmax(similarity_score)]
                image_encoding += column_dict[key]
    return image_encoding
