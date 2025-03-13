import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
from collections import defaultdict
from utils import count_frequency
import re
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parent_string_checker(list_of_strings, test_string):
    for string in list_of_strings:
        if test_string in string and len(string) > len(test_string):
            return True
    return False


def group_substrings(strings):
    # Sort the strings by length, longest first
    strings.sort(key=len, reverse=False)

    # Dictionary to store grouped substrings
    groups = defaultdict(list)

    # Set to track which strings have been grouped
    grouped = set()

    for i, string in enumerate(strings):
        # If the string is already grouped, skip it
        if string in grouped:
            continue

        # Create a new group for this string
        group = [string]
        grouped.add(string)

        # Check for substrings in the remaining strings
        for other_string in strings[i + 1:]:
            if other_string not in grouped and string in other_string:
                group.append(other_string)
                grouped.add(other_string)

        # Add the group to the result
        group.sort(key=len, reverse=True)
        groups[string] = group

    return list(groups.values())


def createPathGraph(s, nodes):
    path = []
    i = 0
    s_copy = s[:]
    while i < len(s):
        for node in nodes:
            if s.startswith(node, i):
                path.append(node)
                i += len(node)
                s_copy = s_copy[len(node):]
                break
        else:
            i += 1  # Increment i if no node is found to avoid infinite loop

    # Create path graph using NetworkX
    G = nx.path_graph(path, create_using=nx.DiGraph())
    # Add edges to graph and count occurrences
    edges = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
    edge_counts = Counter(edges)

    # Add edges with weights (degree)
    for edge, count in edge_counts.items():
        G.add_edge(edge[0], edge[1], weight=count)

    # Map nodes to numbers for labeling
    node_map = dict(zip(nodes, range(len(nodes))))

    # Find edges with degree greater than 1
    high_degree_edges = [(edge, count) for edge, count in edge_counts.items() if count > 0 and '\t' not in edge]
    high_degree_edges = sorted(high_degree_edges, key=lambda x: x[1], reverse=True)
    return path, G, high_degree_edges, edge_counts


def get_nodes(image_encodings, final_words):
    encodings = image_encodings.split('\t')[:-1]
    final_words = sorted(final_words, key=len, reverse=True)
    encoding_copy = image_encodings[:]

    potentials = []
    for word in final_words:
        reversed_word = ''.join(re.findall('...', word)[::-1])
        if word in image_encodings:
            potentials.append(word)
        if reversed_word in image_encodings:
            potentials.append(word)

    # potentials = [word for word in final_words if word in image_encodings]

    groups = group_substrings(potentials)
    filtered = []
    for group in groups:
        frequency = count_frequency(group, image_encodings)
        filtered.append((group[frequency.index(max(frequency))], max(frequency)))

    filtered_words = []
    for f in filtered:
        if f[0] in image_encodings:
            filtered_words.append(f[0])
        image_encodings = image_encodings.replace(f[0], '\t')

    potential_nodes = [x for x in image_encodings.split('\t') if x]
    c = Counter(potential_nodes)
    filtered_words += [k for k, v in c.items() if v > 1]
    filtered_words = sorted(filtered_words, key=len, reverse=True)

    for word in filtered_words:
        image_encodings = image_encodings.replace(word, '\t')

    filtered_words += re.findall('...', image_encodings.replace('\t', ''))
    nodes = sorted(list(set(filtered_words)), key=len, reverse=True)
    nodes.extend(['\t'])

    for encoding in encodings:
        path, G, high_edge, edge_counts = createPathGraph(encoding, nodes)
        a = ''.join(path)

        if a != encoding:
            missed_node = list(set(re.findall('...', a)) ^ set(re.findall('...', encoding)))
            nodes.extend(missed_node)

    nodes = sorted(nodes, key=len, reverse=True)
    return nodes


def merge_nodes(image_encodings, nodes):
    encoding_copy = image_encodings[:]
    new_path = []
    path, _, high_edge, _ = createPathGraph(encoding_copy, nodes)

    while set(new_path) != set(path):
        # logger.info('========================')
        final_results = []
        path, _, high_edge, _ = createPathGraph(encoding_copy, nodes)
        for edge in high_edge:
            in_node, out_node = edge[0][0], edge[0][1]
            in_node_freq, out_node_freq = path.count(in_node), path.count(out_node)
            merged_nodes = ''.join([in_node, out_node])
            merged_nodes_freq = image_encodings.count(merged_nodes)

            if in_node == out_node and parent_string_checker(nodes, in_node):
                if merged_nodes not in nodes:
                    logger.info(f'Merging repeated nodes - {in_node} and {out_node}')
                    nodes.append(merged_nodes)

                    nodes = sorted(nodes, key=len, reverse=True)
                    new_path, G, high_edge, edge_counts = createPathGraph(encoding_copy, nodes)
                    break

            elif in_node == out_node and not parent_string_checker(nodes, in_node):
                if in_node not in final_results:
                    final_results.append(in_node)
                continue

            elif in_node != out_node and in_node not in final_results and out_node not in final_results:
                if merged_nodes_freq >= in_node_freq or merged_nodes_freq >= out_node_freq:
                    logger.info(f'Merging node - {in_node} and {out_node}')
                    nodes.append(merged_nodes)

                    nodes = sorted(nodes, key=len, reverse=True)
                    new_path, G, high_edge, edge_counts = createPathGraph(encoding_copy, nodes)
                    break

        if set(new_path) == set(path):
            break
    return nodes

